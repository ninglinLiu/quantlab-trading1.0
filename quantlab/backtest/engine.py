"""
回测引擎

实现事件循环、信号生成、订单执行等回测核心逻辑。
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
import logging

from .portfolio import Portfolio, OrderSide
from ..indicators.cluster import cluster_breakout_signals, cluster_retest_signals
from ..indicators.macd import macd_signals
from ..indicators.ma_ema import calculate_multiple_mas
from ..config import get_config

logger = logging.getLogger(__name__)


class BacktestEngine:
    """回测引擎"""
    
    def __init__(
        self,
        data: pd.DataFrame,
        portfolio: Portfolio,
        strategy_func: Optional[Callable] = None
    ):
        """
        初始化回测引擎
        
        Args:
            data: OHLCV 数据
            portfolio: 投资组合
            strategy_func: 策略函数
        """
        self.data = data.copy()
        self.portfolio = portfolio
        self.strategy_func = strategy_func
        
        # 回测结果
        self.results = {
            'trades': [],
            'equity_curve': [],
            'signals': [],
            'positions': []
        }
        
        # 当前状态
        self.current_index = 0
        self.current_timestamp = None
        self.current_price = None
        
    def run_backtest(self) -> Dict:
        """
        运行回测
        
        Returns:
            Dict: 回测结果
        """
        logger.info(f"Starting backtest with {len(self.data)} bars")
        
        # 计算技术指标
        self._calculate_indicators()
        
        # 运行事件循环
        for i in range(len(self.data)):
            self.current_index = i
            self.current_timestamp = self.data.index[i]
            self.current_price = self.data.iloc[i]['close']
            
            # 更新持仓
            self.portfolio.update_position(self.current_timestamp, self.current_price)
            
            # 生成交易信号
            signal = self._generate_signal()
            
            # 执行交易
            if signal is not None:
                self._execute_trade(signal)
            
            # 更新权益曲线
            self.portfolio.update_equity_curve(self.current_timestamp)
        
        # 最终平仓
        if self.portfolio.position is not None:
            self.portfolio.close_position(self.current_timestamp, self.current_price)
        
        # 收集结果
        self._collect_results()
        
        logger.info(f"Backtest completed. Total trades: {len(self.portfolio.trades)}")
        return self.results
    
    def _calculate_indicators(self) -> None:
        """计算技术指标"""
        # 使用默认配置而不是全局配置
        ma_periods = [20, 60, 120]
        macd_fast = 12
        macd_slow = 26
        macd_signal = 9
        
        # 计算移动平均线
        mas = calculate_multiple_mas(self.data['close'], ma_periods)
        
        # 计算 MACD
        from ..indicators.macd import macd
        macd_data = macd(
            self.data['close'],
            macd_fast,
            macd_slow,
            macd_signal
        )
        
        # 合并指标数据
        self.data = pd.concat([self.data, mas, macd_data], axis=1)
        
        logger.info("Technical indicators calculated")
    
    def _generate_signal(self) -> Optional[Dict]:
        """
        生成交易信号
        
        Returns:
            Optional[Dict]: 交易信号
        """
        if self.current_index < max([20, 60, 120]):
            return None
        
        # 使用自定义策略函数
        if self.strategy_func is not None:
            return self.strategy_func(self.data.iloc[:self.current_index + 1], self.current_index)
        
        # 使用默认的均线簇+MACD策略
        return self._default_strategy()
    
    def _default_strategy(self) -> Optional[Dict]:
        """默认策略：均线簇+MACD确认"""
        # 使用默认配置
        ma_periods = [20, 60, 120]
        cluster_pct = 0.01
        
        # 获取当前数据
        current_data = self.data.iloc[:self.current_index + 1]
        
        # 检查均线簇
        from ..indicators.cluster import detect_cluster
        cluster_signal = detect_cluster(
            current_data['close'],
            ma_periods,
            cluster_pct
        )
        
        if not cluster_signal.iloc[-1]:
            return None
        
        # 检查突破信号
        breakout_signals = cluster_breakout_signals(
            current_data['close'],
            ma_periods,
            cluster_pct
        )
        
        current_signal = breakout_signals.iloc[-1]
        if current_signal == 0:
            return None
        
        # 检查回踩确认
        retest_confirmation = False  # 默认不启用回踩确认
        if retest_confirmation:
            retest_signals = cluster_retest_signals(
                current_data['close'],
                ma_periods,
                cluster_pct
            )
            
            if retest_signals.iloc[-1] == 0:
                return None
        
        # 检查 MACD 确认
        macd_fast = 12
        macd_slow = 26
        macd_signal = macd_signals(
            current_data['close'],
            macd_fast,
            macd_slow,
            9
        )
        
        current_macd = macd_signal.iloc[-1]
        
        # 确认信号
        if current_signal == 1 and current_macd == 1:  # 向上突破 + MACD 金叉
            return {
                'side': OrderSide.LONG,
                'strength': 1.0,
                'reason': 'cluster_breakout_up_macd_bullish'
            }
        elif current_signal == -1 and current_macd == -1:  # 向下突破 + MACD 死叉
            return {
                'side': OrderSide.SHORT,
                'strength': 1.0,
                'reason': 'cluster_breakout_down_macd_bearish'
            }
        
        return None
    
    def _execute_trade(self, signal: Dict) -> None:
        """
        执行交易
        
        Args:
            signal: 交易信号
        """
        side = signal['side']
        strength = signal.get('strength', 1.0)
        
        # 计算开仓名义价值
        max_notional = self.portfolio.get_max_notional()
        notional = max_notional * strength
        
        # 执行开仓
        success = self.portfolio.open_position(
            self.current_timestamp,
            side,
            self.current_price,
            notional
        )
        
        if success:
            logger.info(f"Trade executed: {side.value} @ {self.current_price:.2f}, Notional: {notional:.2f}")
            
            # 记录信号
            self.results['signals'].append({
                'timestamp': self.current_timestamp,
                'side': side.value,
                'price': self.current_price,
                'notional': notional,
                'reason': signal.get('reason', 'unknown')
            })
    
    def _collect_results(self) -> None:
        """收集回测结果"""
        # 交易记录
        self.results['trades'] = [
            {
                'entry_timestamp': trade.entry_timestamp,
                'exit_timestamp': trade.exit_timestamp,
                'side': trade.side.value,
                'entry_price': trade.entry_price,
                'exit_price': trade.exit_price,
                'quantity': trade.quantity,
                'notional': trade.notional,
                'leverage': trade.leverage,
                'pnl': trade.pnl,
                'fees': trade.fees,
                'slippage': trade.slippage,
                'duration_hours': trade.duration_hours
            }
            for trade in self.portfolio.trades
        ]
        
        # 权益曲线
        self.results['equity_curve'] = [
            {'timestamp': timestamp, 'equity': equity}
            for timestamp, equity in self.portfolio.equity_curve
        ]
        
        # 持仓记录
        self.results['positions'] = []
        for i, trade in enumerate(self.portfolio.trades):
            self.results['positions'].append({
                'trade_id': i,
                'entry_timestamp': trade.entry_timestamp,
                'exit_timestamp': trade.exit_timestamp,
                'side': trade.side.value,
                'entry_price': trade.entry_price,
                'exit_price': trade.exit_price,
                'duration_hours': trade.duration_hours,
                'pnl': trade.pnl
            })
    
    def get_performance_metrics(self) -> Dict:
        """获取绩效指标"""
        if not self.portfolio.trades:
            return {}
        
        trades_df = pd.DataFrame(self.results['trades'])
        equity_df = pd.DataFrame(self.results['equity_curve'])
        
        # 基本统计
        total_trades = len(trades_df)
        winning_trades = len(trades_df[trades_df['pnl'] > 0])
        losing_trades = len(trades_df[trades_df['pnl'] < 0])
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # 盈亏比
        avg_win = trades_df[trades_df['pnl'] > 0]['pnl'].mean() if winning_trades > 0 else 0
        avg_loss = trades_df[trades_df['pnl'] < 0]['pnl'].mean() if losing_trades > 0 else 0
        profit_loss_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
        
        # 收益率
        total_return = (self.portfolio.current_equity - self.portfolio.initial_equity) / self.portfolio.initial_equity
        
        # 年化收益率
        if len(equity_df) > 1:
            start_time = equity_df['timestamp'].iloc[0]
            end_time = equity_df['timestamp'].iloc[-1]
            duration_years = (end_time - start_time).total_seconds() / (365 * 24 * 3600)
            annualized_return = (1 + total_return) ** (1 / duration_years) - 1 if duration_years > 0 else 0
        else:
            annualized_return = 0
        
        # 夏普比率
        if len(equity_df) > 1:
            equity_df['timestamp'] = pd.to_datetime(equity_df['timestamp'])
            equity_df.set_index('timestamp', inplace=True)
            returns = equity_df['equity'].pct_change().dropna()
            sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
        else:
            sharpe_ratio = 0
        
        # 最大回撤
        equity_df['equity'] = equity_df['equity'].astype(float)
        equity_df['cummax'] = equity_df['equity'].cummax()
        equity_df['drawdown'] = (equity_df['equity'] - equity_df['cummax']) / equity_df['cummax']
        max_drawdown = equity_df['drawdown'].min()
        
        # 卡玛比率
        calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0
        
        # 平均持仓时长
        avg_duration = trades_df['duration_hours'].mean()
        
        # 期望收益
        expected_return = trades_df['pnl'].mean()
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'profit_loss_ratio': profit_loss_ratio,
            'total_return': total_return,
            'annualized_return': annualized_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'calmar_ratio': calmar_ratio,
            'avg_duration_hours': avg_duration,
            'expected_return': expected_return,
            'total_fees': self.portfolio.total_fees,
            'total_slippage': self.portfolio.total_slippage,
            'final_equity': self.portfolio.current_equity
        }


if __name__ == "__main__":
    # 测试回测引擎
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
    
    # 创建投资组合
    portfolio = Portfolio(initial_equity=5000, leverage=10)
    
    # 创建回测引擎
    engine = BacktestEngine(data, portfolio)
    
    # 运行回测
    results = engine.run_backtest()
    
    # 获取绩效指标
    metrics = engine.get_performance_metrics()
    print("Performance Metrics:")
    for key, value in metrics.items():
        print(f"{key}: {value}")
