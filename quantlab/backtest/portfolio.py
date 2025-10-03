"""
投资组合管理

处理保证金、杠杆、手续费、滑点、爆仓等交易逻辑。
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class OrderSide(Enum):
    """订单方向"""
    LONG = "long"
    SHORT = "short"


class OrderStatus(Enum):
    """订单状态"""
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"


@dataclass
class Order:
    """订单类"""
    timestamp: datetime
    side: OrderSide
    price: float
    quantity: float
    notional: float
    fee: float
    slippage: float
    status: OrderStatus = OrderStatus.PENDING
    filled_price: Optional[float] = None
    filled_quantity: Optional[float] = None
    filled_notional: Optional[float] = None
    total_fee: Optional[float] = None
    total_slippage: Optional[float] = None


@dataclass
class Position:
    """持仓类"""
    side: OrderSide
    entry_price: float
    quantity: float
    notional: float
    margin: float
    leverage: int
    entry_timestamp: datetime
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    total_fees: float = 0.0


@dataclass
class Trade:
    """交易记录类"""
    entry_timestamp: datetime
    exit_timestamp: datetime
    side: OrderSide
    entry_price: float
    exit_price: float
    quantity: float
    notional: float
    leverage: int
    pnl: float
    fees: float
    slippage: float
    mae: float = 0.0  # Maximum Adverse Excursion
    mfe: float = 0.0  # Maximum Favorable Excursion
    duration_hours: float = 0.0


class Portfolio:
    """投资组合管理类"""
    
    def __init__(
        self,
        initial_equity: float = 5000.0,
        leverage: int = 10,
        fee_rate: float = 0.0008,
        slippage_rate: float = 0.0005,
        mmr: float = 0.005,  # 维持保证金率
        take_profit_rate: float = 0.25,  # 杠杆后止盈比例
        stop_loss_rate: float = 0.05,    # 杠杆后止损比例
    ):
        """
        初始化投资组合
        
        Args:
            initial_equity: 初始资金
            leverage: 杠杆倍数
            fee_rate: 手续费率
            slippage_rate: 滑点率
            mmr: 维持保证金率
            take_profit_rate: 止盈比例（杠杆后）
            stop_loss_rate: 止损比例（杠杆后）
        """
        self.initial_equity = initial_equity
        self.current_equity = initial_equity
        self.leverage = leverage
        self.fee_rate = fee_rate
        self.slippage_rate = slippage_rate
        self.mmr = mmr
        self.take_profit_rate = take_profit_rate
        self.stop_loss_rate = stop_loss_rate
        
        # 持仓和订单
        self.position: Optional[Position] = None
        self.pending_orders: List[Order] = []
        self.trades: List[Trade] = []
        
        # 权益曲线
        self.equity_curve: List[Tuple[datetime, float]] = []
        self.equity_curve.append((datetime.now(), initial_equity))
        
        # 统计信息
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_fees = 0.0
        self.total_slippage = 0.0
        
    def get_available_margin(self) -> float:
        """获取可用保证金"""
        if self.position is None:
            return self.current_equity
        
        # 计算当前持仓的保证金占用
        position_margin = self.position.notional / self.leverage
        return self.current_equity - position_margin
    
    def get_max_notional(self) -> float:
        """获取最大可开仓名义价值"""
        return self.current_equity * self.leverage
    
    def can_open_position(self, notional: float) -> bool:
        """检查是否可以开仓"""
        required_margin = notional / self.leverage
        return required_margin <= self.current_equity
    
    def calculate_entry_price(self, market_price: float, side: OrderSide) -> float:
        """
        计算入场价格（包含滑点）
        
        Args:
            market_price: 市场价格
            side: 订单方向
            
        Returns:
            float: 入场价格
        """
        slippage_amount = market_price * self.slippage_rate
        
        if side == OrderSide.LONG:
            return market_price + slippage_amount
        else:
            return market_price - slippage_amount
    
    def calculate_exit_price(self, market_price: float, side: OrderSide) -> float:
        """
        计算出场价格（包含滑点）
        
        Args:
            market_price: 市场价格
            side: 订单方向
            
        Returns:
            float: 出场价格
        """
        slippage_amount = market_price * self.slippage_rate
        
        if side == OrderSide.LONG:
            return market_price - slippage_amount
        else:
            return market_price + slippage_amount
    
    def calculate_fee(self, notional: float) -> float:
        """计算手续费"""
        return notional * self.fee_rate
    
    def calculate_target_prices(self, entry_price: float, side: OrderSide) -> Tuple[float, float]:
        """
        计算止盈止损价格
        
        Args:
            entry_price: 入场价格
            side: 订单方向
            
        Returns:
            Tuple[float, float]: (止盈价格, 止损价格)
        """
        if side == OrderSide.LONG:
            # 多单：价格上涨对应杠杆后收益
            take_profit_price = entry_price * (1 + self.take_profit_rate / self.leverage)
            stop_loss_price = entry_price * (1 - self.stop_loss_rate / self.leverage)
        else:
            # 空单：价格下跌对应杠杆后收益
            take_profit_price = entry_price * (1 - self.take_profit_rate / self.leverage)
            stop_loss_price = entry_price * (1 + self.stop_loss_rate / self.leverage)
        
        return take_profit_price, stop_loss_price
    
    def open_position(
        self,
        timestamp: datetime,
        side: OrderSide,
        market_price: float,
        notional: float
    ) -> bool:
        """
        开仓
        
        Args:
            timestamp: 时间戳
            side: 订单方向
            market_price: 市场价格
            notional: 名义价值
            
        Returns:
            bool: 是否成功开仓
        """
        # 检查是否可以开仓
        if not self.can_open_position(notional):
            logger.warning(f"Insufficient margin to open position. Required: {notional/self.leverage}, Available: {self.current_equity}")
            return False
        
        # 如果已有持仓，先平仓
        if self.position is not None:
            self.close_position(timestamp, market_price)
        
        # 计算入场价格和手续费
        entry_price = self.calculate_entry_price(market_price, side)
        quantity = notional / entry_price
        fee = self.calculate_fee(notional)
        slippage_cost = abs(entry_price - market_price) * quantity
        
        # 创建持仓
        margin = notional / self.leverage
        self.position = Position(
            side=side,
            entry_price=entry_price,
            quantity=quantity,
            notional=notional,
            margin=margin,
            leverage=self.leverage,
            entry_timestamp=timestamp,
            total_fees=fee
        )
        
        # 更新权益
        self.current_equity -= fee + slippage_cost
        self.total_fees += fee
        self.total_slippage += slippage_cost
        
        logger.info(f"Opened {side.value} position: {quantity:.6f} @ {entry_price:.2f}, Notional: {notional:.2f}")
        return True
    
    def close_position(self, timestamp: datetime, market_price: float) -> Optional[Trade]:
        """
        平仓
        
        Args:
            timestamp: 时间戳
            market_price: 市场价格
            
        Returns:
            Optional[Trade]: 交易记录
        """
        if self.position is None:
            return None
        
        # 计算出场价格和手续费
        exit_price = self.calculate_exit_price(market_price, self.position.side)
        fee = self.calculate_fee(self.position.notional)
        slippage_cost = abs(exit_price - market_price) * self.position.quantity
        
        # 计算盈亏
        if self.position.side == OrderSide.LONG:
            pnl = (exit_price - self.position.entry_price) * self.position.quantity
        else:
            pnl = (self.position.entry_price - exit_price) * self.position.quantity
        
        # 计算杠杆后实际盈亏
        leverage_pnl = pnl * self.leverage
        
        # 创建交易记录
        duration = (timestamp - self.position.entry_timestamp).total_seconds() / 3600
        trade = Trade(
            entry_timestamp=self.position.entry_timestamp,
            exit_timestamp=timestamp,
            side=self.position.side,
            entry_price=self.position.entry_price,
            exit_price=exit_price,
            quantity=self.position.quantity,
            notional=self.position.notional,
            leverage=self.position.leverage,
            pnl=leverage_pnl,
            fees=self.position.total_fees + fee,
            slippage=slippage_cost,
            duration_hours=duration
        )
        
        # 更新权益
        self.current_equity += leverage_pnl - fee - slippage_cost
        self.total_fees += fee
        self.total_slippage += slippage_cost
        
        # 更新统计
        self.total_trades += 1
        if leverage_pnl > 0:
            self.winning_trades += 1
        else:
            self.losing_trades += 1
        
        # 记录交易
        self.trades.append(trade)
        
        logger.info(f"Closed {self.position.side.value} position: PnL: {leverage_pnl:.2f}, Fees: {fee:.2f}")
        
        # 清空持仓
        self.position = None
        
        return trade
    
    def update_position(self, timestamp: datetime, market_price: float) -> bool:
        """
        更新持仓（检查止盈止损和爆仓）
        
        Args:
            timestamp: 时间戳
            market_price: 市场价格
            
        Returns:
            bool: 是否触发平仓
        """
        if self.position is None:
            return False
        
        # 计算当前盈亏
        if self.position.side == OrderSide.LONG:
            unrealized_pnl = (market_price - self.position.entry_price) * self.position.quantity
        else:
            unrealized_pnl = (self.position.entry_price - market_price) * self.position.quantity
        
        self.position.unrealized_pnl = unrealized_pnl
        
        # 计算当前权益
        current_equity = self.current_equity + unrealized_pnl * self.leverage
        
        # 检查爆仓
        maintenance_margin = self.position.notional * self.mmr
        if current_equity <= maintenance_margin:
            logger.warning(f"Margin call triggered! Equity: {current_equity:.2f}, Required: {maintenance_margin:.2f}")
            self.close_position(timestamp, market_price)
            return True
        
        # 检查止盈止损
        take_profit_price, stop_loss_price = self.calculate_target_prices(
            self.position.entry_price, self.position.side
        )
        
        if self.position.side == OrderSide.LONG:
            if market_price >= take_profit_price or market_price <= stop_loss_price:
                self.close_position(timestamp, market_price)
                return True
        else:
            if market_price <= take_profit_price or market_price >= stop_loss_price:
                self.close_position(timestamp, market_price)
                return True
        
        return False
    
    def update_equity_curve(self, timestamp: datetime) -> None:
        """更新权益曲线"""
        current_equity = self.current_equity
        if self.position is not None:
            current_equity += self.position.unrealized_pnl * self.leverage
        
        self.equity_curve.append((timestamp, current_equity))
    
    def get_portfolio_summary(self) -> Dict:
        """获取投资组合摘要"""
        total_return = (self.current_equity - self.initial_equity) / self.initial_equity
        
        win_rate = self.winning_trades / self.total_trades if self.total_trades > 0 else 0
        
        avg_win = np.mean([t.pnl for t in self.trades if t.pnl > 0]) if self.winning_trades > 0 else 0
        avg_loss = np.mean([t.pnl for t in self.trades if t.pnl < 0]) if self.losing_trades > 0 else 0
        profit_loss_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
        
        return {
            'initial_equity': self.initial_equity,
            'current_equity': self.current_equity,
            'total_return': total_return,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': win_rate,
            'profit_loss_ratio': profit_loss_ratio,
            'total_fees': self.total_fees,
            'total_slippage': self.total_slippage,
            'leverage': self.leverage,
            'has_position': self.position is not None
        }


if __name__ == "__main__":
    # 测试投资组合
    portfolio = Portfolio(
        initial_equity=5000,
        leverage=10,
        fee_rate=0.0008,
        slippage_rate=0.0005
    )
    
    # 模拟交易
    timestamp = datetime.now()
    market_price = 50000
    
    # 开多单
    success = portfolio.open_position(timestamp, OrderSide.LONG, market_price, 10000)
    print(f"Open position: {success}")
    
    # 更新持仓
    portfolio.update_position(timestamp, 51000)
    portfolio.update_equity_curve(timestamp)
    
    # 平仓
    trade = portfolio.close_position(timestamp, 52000)
    print(f"Trade: {trade}")
    
    # 获取摘要
    summary = portfolio.get_portfolio_summary()
    print(f"Portfolio summary: {summary}")
