"""
均线簇 + MACD 确认策略

实现基于均线簇突破和MACD确认的交易策略。
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, List, Tuple
from datetime import datetime
import logging

from ..indicators.cluster import (
    detect_cluster, 
    cluster_breakout_signals, 
    cluster_retest_signals,
    get_cluster_boundaries
)
from ..indicators.macd import macd_signals
from ..indicators.ma_ema import calculate_multiple_mas
from ..config import get_config

logger = logging.getLogger(__name__)


class ClusterMacdStrategy:
    """均线簇 + MACD 确认策略"""
    
    def __init__(
        self,
        ma_periods: List[int] = [20, 60, 120],
        cluster_threshold: float = 0.01,
        macd_fast: int = 12,
        macd_slow: int = 26,
        macd_signal: int = 9,
        retest_confirmation: bool = False,
        retest_periods: int = 3
    ):
        """
        初始化策略
        
        Args:
            ma_periods: 均线周期列表
            cluster_threshold: 均线簇密集阈值
            macd_fast: MACD快线周期
            macd_slow: MACD慢线周期
            macd_signal: MACD信号线周期
            retest_confirmation: 是否启用回踩确认
            retest_periods: 回踩确认周期数
        """
        self.ma_periods = ma_periods
        self.cluster_threshold = cluster_threshold
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.macd_signal = macd_signal
        self.retest_confirmation = retest_confirmation
        self.retest_periods = retest_periods
        
        # 策略状态
        self.current_position = None
        self.entry_price = None
        self.entry_timestamp = None
        self.stop_loss_price = None
        self.take_profit_price = None
        
        # 信号历史
        self.signals_history = []
        self.cluster_history = []
        self.macd_history = []
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        计算技术指标
        
        Args:
            data: OHLCV 数据
            
        Returns:
            pd.DataFrame: 包含指标的数据
        """
        result = data.copy()
        
        # 计算移动平均线
        mas = calculate_multiple_mas(data['close'], self.ma_periods)
        result = pd.concat([result, mas], axis=1)
        
        # 计算均线簇信号
        cluster_signal = detect_cluster(
            data['close'], 
            self.ma_periods, 
            self.cluster_threshold
        )
        result['cluster'] = cluster_signal
        
        # 计算均线簇突破信号
        breakout_signal = cluster_breakout_signals(
            data['close'],
            self.ma_periods,
            self.cluster_threshold
        )
        result['cluster_breakout'] = breakout_signal
        
        # 计算回踩确认信号
        if self.retest_confirmation:
            retest_signal = cluster_retest_signals(
                data['close'],
                self.ma_periods,
                self.cluster_threshold,
                retest_periods=self.retest_periods
            )
            result['cluster_retest'] = retest_signal
        
        # 计算MACD信号
        macd_signal = macd_signals(
            data['close'],
            self.macd_fast,
            self.macd_slow,
            self.macd_signal
        )
        result['macd_signal'] = macd_signal
        
        # 计算MACD指标
        from ..indicators.macd import macd
        macd_data = macd(data['close'], self.macd_fast, self.macd_slow, self.macd_signal)
        result = pd.concat([result, macd_data], axis=1)
        
        return result
    
    def generate_signal(self, data: pd.DataFrame, index: int) -> Optional[Dict]:
        """
        生成交易信号
        
        Args:
            data: 包含指标的数据
            index: 当前数据索引
            
        Returns:
            Optional[Dict]: 交易信号
        """
        if index < max(self.ma_periods):
            return None
        
        current_data = data.iloc[:index + 1]
        current_row = current_data.iloc[-1]
        
        # 检查均线簇
        if not current_row['cluster']:
            return None
        
        # 检查突破信号
        breakout_signal = current_row['cluster_breakout']
        if breakout_signal == 0:
            return None
        
        # 检查回踩确认
        if self.retest_confirmation:
            if 'cluster_retest' in current_row and current_row['cluster_retest'] == 0:
                return None
        
        # 检查MACD确认
        macd_signal = current_row['macd_signal']
        
        # 生成信号
        if breakout_signal == 1 and macd_signal == 1:  # 向上突破 + MACD 金叉
            signal = {
                'side': 'long',
                'strength': 1.0,
                'reason': 'cluster_breakout_up_macd_bullish',
                'price': current_row['close'],
                'timestamp': current_data.index[-1]
            }
            
            # 记录信号历史
            self.signals_history.append(signal)
            return signal
            
        elif breakout_signal == -1 and macd_signal == -1:  # 向下突破 + MACD 死叉
            signal = {
                'side': 'short',
                'strength': 1.0,
                'reason': 'cluster_breakout_down_macd_bearish',
                'price': current_row['close'],
                'timestamp': current_data.index[-1]
            }
            
            # 记录信号历史
            self.signals_history.append(signal)
            return signal
        
        return None
    
    def calculate_position_size(
        self, 
        signal: Dict, 
        current_equity: float, 
        leverage: int = 10
    ) -> float:
        """
        计算仓位大小
        
        Args:
            signal: 交易信号
            current_equity: 当前权益
            leverage: 杠杆倍数
            
        Returns:
            float: 名义价值
        """
        # 使用全仓杠杆
        notional = current_equity * leverage * signal['strength']
        return notional
    
    def calculate_stop_loss_take_profit(
        self, 
        entry_price: float, 
        side: str,
        take_profit_rate: float = 0.25,
        stop_loss_rate: float = 0.05
    ) -> Tuple[float, float]:
        """
        计算止盈止损价格
        
        Args:
            entry_price: 入场价格
            side: 订单方向
            take_profit_rate: 止盈比例（杠杆后）
            stop_loss_rate: 止损比例（杠杆后）
            
        Returns:
            Tuple[float, float]: (止盈价格, 止损价格)
        """
        if side == 'long':
            # 多单：价格上涨对应杠杆后收益
            take_profit_price = entry_price * (1 + take_profit_rate / 10)  # 假设10倍杠杆
            stop_loss_price = entry_price * (1 - stop_loss_rate / 10)
        else:
            # 空单：价格下跌对应杠杆后收益
            take_profit_price = entry_price * (1 - take_profit_rate / 10)
            stop_loss_price = entry_price * (1 + stop_loss_rate / 10)
        
        return take_profit_price, stop_loss_price
    
    def update_position(
        self, 
        current_price: float, 
        timestamp: datetime
    ) -> Optional[Dict]:
        """
        更新持仓状态
        
        Args:
            current_price: 当前价格
            timestamp: 当前时间
            
        Returns:
            Optional[Dict]: 平仓信号
        """
        if self.current_position is None:
            return None
        
        # 检查止盈止损
        if self.current_position['side'] == 'long':
            if current_price >= self.take_profit_price or current_price <= self.stop_loss_price:
                return {
                    'action': 'close',
                    'reason': 'take_profit' if current_price >= self.take_profit_price else 'stop_loss',
                    'price': current_price,
                    'timestamp': timestamp
                }
        else:
            if current_price <= self.take_profit_price or current_price >= self.stop_loss_price:
                return {
                    'action': 'close',
                    'reason': 'take_profit' if current_price <= self.take_profit_price else 'stop_loss',
                    'price': current_price,
                    'timestamp': timestamp
                }
        
        return None
    
    def open_position(self, signal: Dict, current_equity: float) -> Dict:
        """
        开仓
        
        Args:
            signal: 交易信号
            current_equity: 当前权益
            
        Returns:
            Dict: 持仓信息
        """
        # 计算仓位大小
        notional = self.calculate_position_size(signal, current_equity)
        
        # 计算止盈止损
        take_profit_price, stop_loss_price = self.calculate_stop_loss_take_profit(
            signal['price'], signal['side']
        )
        
        # 创建持仓
        self.current_position = {
            'side': signal['side'],
            'entry_price': signal['price'],
            'notional': notional,
            'entry_timestamp': signal['timestamp'],
            'take_profit_price': take_profit_price,
            'stop_loss_price': stop_loss_price
        }
        
        self.entry_price = signal['price']
        self.entry_timestamp = signal['timestamp']
        self.take_profit_price = take_profit_price
        self.stop_loss_price = stop_loss_price
        
        logger.info(f"Opened {signal['side']} position at {signal['price']:.2f}")
        
        return self.current_position
    
    def close_position(self, close_signal: Dict) -> Dict:
        """
        平仓
        
        Args:
            close_signal: 平仓信号
            
        Returns:
            Dict: 交易记录
        """
        if self.current_position is None:
            return None
        
        # 计算盈亏
        entry_price = self.current_position['entry_price']
        exit_price = close_signal['price']
        
        if self.current_position['side'] == 'long':
            pnl = (exit_price - entry_price) / entry_price
        else:
            pnl = (entry_price - exit_price) / entry_price
        
        # 创建交易记录
        trade_record = {
            'entry_timestamp': self.current_position['entry_timestamp'],
            'exit_timestamp': close_signal['timestamp'],
            'side': self.current_position['side'],
            'entry_price': entry_price,
            'exit_price': exit_price,
            'notional': self.current_position['notional'],
            'pnl': pnl,
            'exit_reason': close_signal['reason']
        }
        
        logger.info(f"Closed {self.current_position['side']} position at {exit_price:.2f}, PnL: {pnl:.4f}")
        
        # 清空持仓
        self.current_position = None
        self.entry_price = None
        self.entry_timestamp = None
        self.take_profit_price = None
        self.stop_loss_price = None
        
        return trade_record
    
    def get_strategy_summary(self) -> Dict:
        """获取策略摘要"""
        total_signals = len(self.signals_history)
        
        long_signals = len([s for s in self.signals_history if s['side'] == 'long'])
        short_signals = len([s for s in self.signals_history if s['side'] == 'short'])
        
        return {
            'total_signals': total_signals,
            'long_signals': long_signals,
            'short_signals': short_signals,
            'has_position': self.current_position is not None,
            'current_position': self.current_position,
            'ma_periods': self.ma_periods,
            'cluster_threshold': self.cluster_threshold,
            'macd_params': {
                'fast': self.macd_fast,
                'slow': self.macd_slow,
                'signal': self.macd_signal
            },
            'retest_confirmation': self.retest_confirmation
        }
    
    def backtest_strategy(
        self, 
        data: pd.DataFrame,
        initial_equity: float = 5000.0,
        leverage: int = 10
    ) -> Dict:
        """
        回测策略
        
        Args:
            data: OHLCV 数据
            initial_equity: 初始资金
            leverage: 杠杆倍数
            
        Returns:
            Dict: 回测结果
        """
        # 计算指标
        data_with_indicators = self.calculate_indicators(data)
        
        # 初始化回测状态
        current_equity = initial_equity
        trades = []
        equity_curve = [(data.index[0], initial_equity)]
        
        # 遍历数据
        for i in range(max(self.ma_periods), len(data_with_indicators)):
            current_timestamp = data_with_indicators.index[i]
            current_price = data_with_indicators.iloc[i]['close']
            
            # 更新持仓
            if self.current_position is not None:
                close_signal = self.update_position(current_price, current_timestamp)
                if close_signal is not None:
                    trade_record = self.close_position(close_signal)
                    if trade_record:
                        trades.append(trade_record)
                        # 更新权益（简化计算）
                        current_equity *= (1 + trade_record['pnl'] * leverage)
            
            # 生成新信号
            if self.current_position is None:
                signal = self.generate_signal(data_with_indicators, i)
                if signal is not None:
                    self.open_position(signal, current_equity)
            
            # 记录权益曲线
            equity_curve.append((current_timestamp, current_equity))
        
        # 最终平仓
        if self.current_position is not None:
            final_price = data_with_indicators.iloc[-1]['close']
            final_timestamp = data_with_indicators.index[-1]
            close_signal = {
                'action': 'close',
                'reason': 'end_of_data',
                'price': final_price,
                'timestamp': final_timestamp
            }
            trade_record = self.close_position(close_signal)
            if trade_record:
                trades.append(trade_record)
        
        return {
            'trades': trades,
            'equity_curve': equity_curve,
            'final_equity': current_equity,
            'total_return': (current_equity - initial_equity) / initial_equity,
            'total_trades': len(trades)
        }


if __name__ == "__main__":
    # 测试策略
    import numpy as np
    
    # 创建测试数据
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=1000, freq='4H')
    prices = 100 + np.cumsum(np.random.randn(1000) * 0.5)
    
    data = pd.DataFrame({
        'open': prices,
        'high': prices * 1.01,
        'low': prices * 0.99,
        'close': prices,
        'volume': np.random.randint(1000, 10000, 1000)
    }, index=dates)
    
    # 创建策略
    strategy = ClusterMacdStrategy(
        ma_periods=[20, 60, 120],
        cluster_threshold=0.01,
        retest_confirmation=False
    )
    
    # 运行回测
    results = strategy.backtest_strategy(data)
    
    print(f"Backtest Results:")
    print(f"Total trades: {results['total_trades']}")
    print(f"Total return: {results['total_return']:.4f}")
    print(f"Final equity: {results['final_equity']:.2f}")
    
    # 获取策略摘要
    summary = strategy.get_strategy_summary()
    print(f"\nStrategy Summary:")
    for key, value in summary.items():
        print(f"{key}: {value}")
