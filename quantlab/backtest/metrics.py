"""
绩效指标计算

计算各种回测绩效指标，包括胜率、收益率、夏普比率、最大回撤等。
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns

from ..utils.io import ensure_dir, safe_save_csv, save_json


class PerformanceMetrics:
    """绩效指标计算类"""
    
    def __init__(self, trades: List[Dict], equity_curve: List[Dict]):
        """
        初始化绩效指标计算器
        
        Args:
            trades: 交易记录列表
            equity_curve: 权益曲线数据
        """
        self.trades = trades
        self.equity_curve = equity_curve
        
        # 转换为 DataFrame
        self.trades_df = pd.DataFrame(trades) if trades else pd.DataFrame()
        self.equity_df = pd.DataFrame(equity_curve) if equity_curve else pd.DataFrame()
        
        if not self.equity_df.empty:
            self.equity_df['timestamp'] = pd.to_datetime(self.equity_df['timestamp'], utc=True)
            self.equity_df.set_index('timestamp', inplace=True)
            self.equity_df['equity'] = self.equity_df['equity'].astype(float)
    
    def calculate_basic_metrics(self) -> Dict:
        """计算基本绩效指标"""
        if self.trades_df.empty:
            return self._empty_metrics()
        
        # 基本统计
        total_trades = len(self.trades_df)
        winning_trades = len(self.trades_df[self.trades_df['pnl'] > 0])
        losing_trades = len(self.trades_df[self.trades_df['pnl'] < 0])
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # 盈亏比
        avg_win = self.trades_df[self.trades_df['pnl'] > 0]['pnl'].mean() if winning_trades > 0 else 0
        avg_loss = self.trades_df[self.trades_df['pnl'] < 0]['pnl'].mean() if losing_trades > 0 else 0
        profit_loss_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
        
        # 期望收益
        expected_return = self.trades_df['pnl'].mean()
        
        # 平均持仓时长
        avg_duration = self.trades_df['duration_hours'].mean()
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'profit_loss_ratio': profit_loss_ratio,
            'expected_return': expected_return,
            'avg_duration_hours': avg_duration,
            'avg_win': avg_win,
            'avg_loss': avg_loss
        }
    
    def calculate_return_metrics(self) -> Dict:
        """计算收益率相关指标"""
        if self.equity_df.empty:
            return {}
        
        # 总收益率
        initial_equity = self.equity_df['equity'].iloc[0]
        final_equity = self.equity_df['equity'].iloc[-1]
        total_return = (final_equity - initial_equity) / initial_equity
        
        # 年化收益率
        start_time = self.equity_df.index[0]
        end_time = self.equity_df.index[-1]
        duration_years = (end_time - start_time).total_seconds() / (365 * 24 * 3600)
        annualized_return = (1 + total_return) ** (1 / duration_years) - 1 if duration_years > 0 else 0
        
        # 日收益率
        daily_returns = self.equity_df['equity'].pct_change().dropna()
        
        # 夏普比率（假设无风险利率为0）
        sharpe_ratio = daily_returns.mean() / daily_returns.std() * np.sqrt(252) if daily_returns.std() > 0 else 0
        
        # 索提诺比率（只考虑下行风险）
        downside_returns = daily_returns[daily_returns < 0]
        downside_std = downside_returns.std() if len(downside_returns) > 0 else 0
        sortino_ratio = daily_returns.mean() / downside_std * np.sqrt(252) if downside_std > 0 else 0
        
        return {
            'total_return': total_return,
            'annualized_return': annualized_return,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'duration_years': duration_years,
            'initial_equity': initial_equity,
            'final_equity': final_equity
        }
    
    def calculate_risk_metrics(self) -> Dict:
        """计算风险相关指标"""
        if self.equity_df.empty:
            return {}
        
        # 最大回撤
        equity_series = self.equity_df['equity']
        cummax = equity_series.cummax()
        drawdown = (equity_series - cummax) / cummax
        max_drawdown = drawdown.min()
        
        # 最大回撤持续时间
        drawdown_periods = []
        current_period = 0
        max_period = 0
        
        for dd in drawdown:
            if dd < 0:
                current_period += 1
                max_period = max(max_period, current_period)
            else:
                current_period = 0
        
        # 卡玛比率
        return_metrics = self.calculate_return_metrics()
        calmar_ratio = return_metrics.get('annualized_return', 0) / abs(max_drawdown) if max_drawdown != 0 else 0
        
        # 波动率
        daily_returns = equity_series.pct_change().dropna()
        volatility = daily_returns.std() * np.sqrt(252)
        
        # VaR (Value at Risk) - 95% 置信度
        var_95 = np.percentile(daily_returns, 5)
        
        # CVaR (Conditional Value at Risk) - 95% 置信度
        cvar_95 = daily_returns[daily_returns <= var_95].mean()
        
        return {
            'max_drawdown': max_drawdown,
            'max_drawdown_duration': max_period,
            'calmar_ratio': calmar_ratio,
            'volatility': volatility,
            'var_95': var_95,
            'cvar_95': cvar_95
        }
    
    def calculate_trade_analysis(self) -> Dict:
        """计算交易分析指标"""
        if self.trades_df.empty:
            return {}
        
        # 连续盈亏
        pnl_series = self.trades_df['pnl']
        consecutive_wins = 0
        consecutive_losses = 0
        max_consecutive_wins = 0
        max_consecutive_losses = 0
        
        for pnl in pnl_series:
            if pnl > 0:
                consecutive_wins += 1
                consecutive_losses = 0
                max_consecutive_wins = max(max_consecutive_wins, consecutive_wins)
            elif pnl < 0:
                consecutive_losses += 1
                consecutive_wins = 0
                max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)
        
        # 月度收益分析
        trades_with_dates = self.trades_df.copy()
        trades_with_dates['entry_timestamp'] = pd.to_datetime(trades_with_dates['entry_timestamp'])
        trades_with_dates['month'] = trades_with_dates['entry_timestamp'].dt.to_period('M')
        monthly_pnl = trades_with_dates.groupby('month')['pnl'].sum()
        
        # 胜率分析
        monthly_wins = trades_with_dates.groupby('month').apply(
            lambda x: len(x[x['pnl'] > 0]) / len(x) if len(x) > 0 else 0
        )
        
        return {
            'max_consecutive_wins': max_consecutive_wins,
            'max_consecutive_losses': max_consecutive_losses,
            'monthly_pnl_mean': monthly_pnl.mean(),
            'monthly_pnl_std': monthly_pnl.std(),
            'monthly_win_rate_mean': monthly_wins.mean(),
            'monthly_win_rate_std': monthly_wins.std()
        }
    
    def calculate_all_metrics(self) -> Dict:
        """计算所有绩效指标"""
        metrics = {}
        
        # 基本指标
        metrics.update(self.calculate_basic_metrics())
        
        # 收益率指标
        metrics.update(self.calculate_return_metrics())
        
        # 风险指标
        metrics.update(self.calculate_risk_metrics())
        
        # 交易分析
        metrics.update(self.calculate_trade_analysis())
        
        return metrics
    
    def _empty_metrics(self) -> Dict:
        """返回空指标"""
        return {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0,
            'profit_loss_ratio': 0,
            'expected_return': 0,
            'avg_duration_hours': 0,
            'avg_win': 0,
            'avg_loss': 0
        }
    
    def plot_equity_curve(self, save_path: Optional[str] = None) -> None:
        """绘制权益曲线"""
        if self.equity_df.empty:
            print("No equity data to plot")
            return
        
        plt.figure(figsize=(12, 8))
        
        # 权益曲线
        plt.subplot(2, 1, 1)
        plt.plot(self.equity_df.index, self.equity_df['equity'], linewidth=2, label='Equity')
        plt.title('Equity Curve', fontsize=14, fontweight='bold')
        plt.ylabel('Equity (USDT)', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        # 回撤曲线
        plt.subplot(2, 1, 2)
        equity_series = self.equity_df['equity']
        cummax = equity_series.cummax()
        drawdown = (equity_series - cummax) / cummax * 100
        
        plt.fill_between(self.equity_df.index, drawdown, 0, alpha=0.3, color='red')
        plt.plot(self.equity_df.index, drawdown, color='red', linewidth=1)
        plt.title('Drawdown', fontsize=14, fontweight='bold')
        plt.ylabel('Drawdown (%)', fontsize=12)
        plt.xlabel('Date', fontsize=12)
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            ensure_dir(save_path)
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Equity curve saved to {save_path}")
        
        plt.show()
    
    def plot_trade_analysis(self, save_path: Optional[str] = None) -> None:
        """绘制交易分析图表"""
        if self.trades_df.empty:
            print("No trade data to plot")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # 盈亏分布
        axes[0, 0].hist(self.trades_df['pnl'], bins=30, alpha=0.7, edgecolor='black')
        axes[0, 0].axvline(0, color='red', linestyle='--', alpha=0.7)
        axes[0, 0].set_title('PnL Distribution', fontweight='bold')
        axes[0, 0].set_xlabel('PnL (USDT)')
        axes[0, 0].set_ylabel('Frequency')
        axes[0, 0].grid(True, alpha=0.3)
        
        # 持仓时长分布
        axes[0, 1].hist(self.trades_df['duration_hours'], bins=30, alpha=0.7, edgecolor='black')
        axes[0, 1].set_title('Duration Distribution', fontweight='bold')
        axes[0, 1].set_xlabel('Duration (Hours)')
        axes[0, 1].set_ylabel('Frequency')
        axes[0, 1].grid(True, alpha=0.3)
        
        # 累计盈亏
        cumulative_pnl = self.trades_df['pnl'].cumsum()
        axes[1, 0].plot(range(len(cumulative_pnl)), cumulative_pnl, linewidth=2)
        axes[1, 0].set_title('Cumulative PnL', fontweight='bold')
        axes[1, 0].set_xlabel('Trade Number')
        axes[1, 0].set_ylabel('Cumulative PnL (USDT)')
        axes[1, 0].grid(True, alpha=0.3)
        
        # 月度收益
        trades_with_dates = self.trades_df.copy()
        trades_with_dates['entry_timestamp'] = pd.to_datetime(trades_with_dates['entry_timestamp'])
        trades_with_dates['month'] = trades_with_dates['entry_timestamp'].dt.to_period('M')
        monthly_pnl = trades_with_dates.groupby('month')['pnl'].sum()
        
        axes[1, 1].bar(range(len(monthly_pnl)), monthly_pnl.values, alpha=0.7)
        axes[1, 1].set_title('Monthly PnL', fontweight='bold')
        axes[1, 1].set_xlabel('Month')
        axes[1, 1].set_ylabel('PnL (USDT)')
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            ensure_dir(save_path)
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Trade analysis saved to {save_path}")
        
        plt.show()
    
    def save_metrics(self, file_path: str) -> None:
        """保存绩效指标到文件"""
        metrics = self.calculate_all_metrics()
        
        # 保存为 JSON
        save_json(metrics, file_path)
        print(f"Metrics saved to {file_path}")
    
    def save_trades(self, file_path: str) -> None:
        """保存交易记录到 CSV"""
        if not self.trades_df.empty:
            safe_save_csv(self.trades_df, file_path)
            print(f"Trades saved to {file_path}")
        else:
            print("No trades to save")


if __name__ == "__main__":
    # 测试绩效指标
    import numpy as np
    
    # 创建测试数据
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    
    # 模拟交易记录
    trades = []
    equity = 5000
    for i in range(20):
        pnl = np.random.normal(50, 200)
        equity += pnl
        
        trades.append({
            'entry_timestamp': dates[i*5],
            'exit_timestamp': dates[i*5+1],
            'side': 'long' if pnl > 0 else 'short',
            'entry_price': 50000 + i*100,
            'exit_price': 50000 + i*100 + pnl/0.1,
            'quantity': 0.1,
            'notional': 5000,
            'leverage': 10,
            'pnl': pnl,
            'fees': 10,
            'slippage': 5,
            'duration_hours': 24
        })
    
    # 模拟权益曲线
    equity_curve = []
    for i, date in enumerate(dates):
        equity_curve.append({
            'timestamp': date,
            'equity': 5000 + i*10 + np.random.normal(0, 50)
        })
    
    # 创建绩效指标计算器
    metrics_calc = PerformanceMetrics(trades, equity_curve)
    
    # 计算所有指标
    all_metrics = metrics_calc.calculate_all_metrics()
    print("Performance Metrics:")
    for key, value in all_metrics.items():
        print(f"{key}: {value}")
    
    # 绘制图表
    metrics_calc.plot_equity_curve()
    metrics_calc.plot_trade_analysis()
