"""
K线绘图模块

使用 matplotlib 和 mplfinance 绘制K线图和技术指标。
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import mplfinance as mpf
from typing import Optional, List, Dict, Tuple
import logging

from ..indicators.ma_ema import calculate_multiple_mas
from ..indicators.macd import macd
from ..utils.io import ensure_dir

logger = logging.getLogger(__name__)

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


class KlinePlotter:
    """K线绘图器"""
    
    def __init__(self, style: str = 'default'):
        """
        初始化K线绘图器
        
        Args:
            style: 绘图样式
        """
        self.style = style
        self.setup_style()
    
    def setup_style(self) -> None:
        """设置绘图样式"""
        if self.style == 'dark':
            plt.style.use('dark_background')
            self.colors = {
                'bull': '#00ff88',
                'bear': '#ff4444',
                'ma': '#ffaa00',
                'ema': '#00aaff',
                'macd_line': '#ffffff',
                'macd_signal': '#ffaa00',
                'macd_hist': '#666666'
            }
        else:
            self.colors = {
                'bull': '#26a69a',
                'bear': '#ef5350',
                'ma': '#ff9800',
                'ema': '#2196f3',
                'macd_line': '#000000',
                'macd_signal': '#ff9800',
                'macd_hist': '#9e9e9e'
            }
    
    def plot_candlestick(
        self,
        data: pd.DataFrame,
        title: str = "K线图",
        save_path: Optional[str] = None,
        show_volume: bool = True,
        window: Optional[int] = None
    ) -> None:
        """
        绘制基础K线图
        
        Args:
            data: OHLCV 数据
            title: 图表标题
            save_path: 保存路径
            show_volume: 是否显示成交量
            window: 显示窗口大小
        """
        # 选择数据窗口
        plot_data = data.tail(window) if window else data
        
        # 设置样式
        style = mpf.make_mpf_style(
            base_mpf_style='charles',
            gridstyle='-',
            gridcolor='lightgray',
            y_on_right=False
        )
        
        # 绘制K线图
        fig, axes = mpf.plot(
            plot_data,
            type='candle',
            style=style,
            title=title,
            ylabel='Price',
            volume=show_volume,
            figsize=(15, 10),
            returnfig=True
        )
        
        if save_path:
            ensure_dir(save_path)
            fig.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"K-line chart saved to {save_path}")
        
        plt.show()
    
    def plot_with_indicators(
        self,
        data: pd.DataFrame,
        title: str = "K线图 + 技术指标",
        save_path: Optional[str] = None,
        show_ma: bool = True,
        show_ema: bool = True,
        show_macd: bool = True,
        ma_periods: List[int] = [20, 60, 120],
        window: Optional[int] = None
    ) -> None:
        """
        绘制带技术指标的K线图
        
        Args:
            data: OHLCV 数据
            title: 图表标题
            save_path: 保存路径
            show_ma: 是否显示移动平均线
            show_ema: 是否显示指数移动平均线
            show_macd: 是否显示MACD
            ma_periods: 均线周期
            window: 显示窗口大小
        """
        # 选择数据窗口
        plot_data = data.tail(window) if window else data
        
        # 计算技术指标
        indicators_data = plot_data.copy()
        
        if show_ma or show_ema:
            mas = calculate_multiple_mas(plot_data['close'], ma_periods)
            indicators_data = pd.concat([indicators_data, mas], axis=1)
        
        if show_macd:
            macd_data = macd(plot_data['close'])
            indicators_data = pd.concat([indicators_data, macd_data], axis=1)
        
        # 创建子图
        fig = plt.figure(figsize=(15, 12))
        
        # K线图
        ax1 = plt.subplot(3, 1, 1)
        self._plot_candlestick_subplot(ax1, plot_data)
        
        # 添加移动平均线
        if show_ma:
            for period in ma_periods:
                if f'MA_{period}' in indicators_data.columns:
                    ax1.plot(indicators_data.index, indicators_data[f'MA_{period}'], 
                            label=f'MA{period}', color=self.colors['ma'], alpha=0.8)
        
        if show_ema:
            for period in ma_periods:
                if f'EMA_{period}' in indicators_data.columns:
                    ax1.plot(indicators_data.index, indicators_data[f'EMA_{period}'], 
                            label=f'EMA{period}', color=self.colors['ema'], alpha=0.8)
        
        ax1.set_title(title, fontsize=16, fontweight='bold')
        ax1.set_ylabel('Price', fontsize=12)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 成交量
        ax2 = plt.subplot(3, 1, 2)
        colors = [self.colors['bull'] if close >= open else self.colors['bear'] 
                 for close, open in zip(plot_data['close'], plot_data['open'])]
        ax2.bar(plot_data.index, plot_data['volume'], color=colors, alpha=0.7)
        ax2.set_ylabel('Volume', fontsize=12)
        ax2.grid(True, alpha=0.3)
        
        # MACD
        if show_macd and 'DIF' in indicators_data.columns:
            ax3 = plt.subplot(3, 1, 3)
            
            # DIF 和 DEA 线
            ax3.plot(indicators_data.index, indicators_data['DIF'], 
                    label='DIF', color=self.colors['macd_line'], linewidth=1)
            ax3.plot(indicators_data.index, indicators_data['DEA'], 
                    label='DEA', color=self.colors['macd_signal'], linewidth=1)
            
            # 柱状图
            colors_hist = [self.colors['bull'] if hist >= 0 else self.colors['bear'] 
                          for hist in indicators_data['HIST']]
            ax3.bar(indicators_data.index, indicators_data['HIST'], 
                   color=colors_hist, alpha=0.7, width=0.8)
            
            ax3.axhline(y=0, color='black', linestyle='-', alpha=0.3)
            ax3.set_ylabel('MACD', fontsize=12)
            ax3.set_xlabel('Date', fontsize=12)
            ax3.legend()
            ax3.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            ensure_dir(save_path)
            fig.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"K-line chart with indicators saved to {save_path}")
        
        plt.show()
    
    def _plot_candlestick_subplot(self, ax, data: pd.DataFrame) -> None:
        """在子图中绘制K线"""
        for i, (timestamp, row) in enumerate(data.iterrows()):
            open_price = row['open']
            high_price = row['high']
            low_price = row['low']
            close_price = row['close']
            
            # 确定颜色
            color = self.colors['bull'] if close_price >= open_price else self.colors['bear']
            
            # 绘制影线
            ax.plot([i, i], [low_price, high_price], color='black', linewidth=1)
            
            # 绘制实体
            body_height = abs(close_price - open_price)
            body_bottom = min(open_price, close_price)
            
            rect = Rectangle((i - 0.4, body_bottom), 0.8, body_height, 
                           facecolor=color, edgecolor='black', linewidth=1)
            ax.add_patch(rect)
    
    def plot_trading_signals(
        self,
        data: pd.DataFrame,
        signals: pd.Series,
        title: str = "交易信号图",
        save_path: Optional[str] = None,
        window: Optional[int] = None
    ) -> None:
        """
        绘制交易信号
        
        Args:
            data: OHLCV 数据
            signals: 交易信号序列
            title: 图表标题
            save_path: 保存路径
            window: 显示窗口大小
        """
        # 选择数据窗口
        plot_data = data.tail(window) if window else data
        signal_data = signals.tail(window) if window else signals
        
        fig, ax = plt.subplots(figsize=(15, 8))
        
        # 绘制K线
        self._plot_candlestick_subplot(ax, plot_data)
        
        # 绘制交易信号
        for i, (timestamp, signal) in enumerate(signal_data.items()):
            if signal == 1:  # 买入信号
                ax.scatter(i, plot_data.iloc[i]['low'] * 0.995, 
                          marker='^', color=self.colors['bull'], s=100, alpha=0.8)
            elif signal == -1:  # 卖出信号
                ax.scatter(i, plot_data.iloc[i]['high'] * 1.005, 
                          marker='v', color=self.colors['bear'], s=100, alpha=0.8)
        
        ax.set_title(title, fontsize=16, fontweight='bold')
        ax.set_ylabel('Price', fontsize=12)
        ax.set_xlabel('Date', fontsize=12)
        ax.grid(True, alpha=0.3)
        
        # 设置x轴标签
        ax.set_xticks(range(0, len(plot_data), max(1, len(plot_data) // 10)))
        ax.set_xticklabels([plot_data.index[i].strftime('%Y-%m-%d') 
                           for i in range(0, len(plot_data), max(1, len(plot_data) // 10))])
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        if save_path:
            ensure_dir(save_path)
            fig.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Trading signals chart saved to {save_path}")
        
        plt.show()
    
    def plot_cluster_analysis(
        self,
        data: pd.DataFrame,
        cluster_signals: pd.Series,
        ma_periods: List[int] = [20, 60, 120],
        title: str = "均线簇分析",
        save_path: Optional[str] = None,
        window: Optional[int] = None
    ) -> None:
        """
        绘制均线簇分析图
        
        Args:
            data: OHLCV 数据
            cluster_signals: 均线簇信号
            ma_periods: 均线周期
            title: 图表标题
            save_path: 保存路径
            window: 显示窗口大小
        """
        # 选择数据窗口
        plot_data = data.tail(window) if window else data
        cluster_data = cluster_signals.tail(window) if window else cluster_signals
        
        # 计算移动平均线
        mas = calculate_multiple_mas(plot_data['close'], ma_periods)
        
        fig, ax = plt.subplots(figsize=(15, 8))
        
        # 绘制K线
        self._plot_candlestick_subplot(ax, plot_data)
        
        # 绘制移动平均线
        for period in ma_periods:
            if f'MA_{period}' in mas.columns:
                ax.plot(mas.index, mas[f'MA_{period}'], 
                       label=f'MA{period}', alpha=0.8, linewidth=2)
        
        # 高亮均线簇区域
        cluster_regions = []
        in_cluster = False
        start_idx = 0
        
        for i, (timestamp, is_cluster) in enumerate(cluster_data.items()):
            if is_cluster and not in_cluster:
                start_idx = i
                in_cluster = True
            elif not is_cluster and in_cluster:
                cluster_regions.append((start_idx, i))
                in_cluster = False
        
        # 绘制均线簇区域
        for start, end in cluster_regions:
            ax.axvspan(start, end, alpha=0.2, color='yellow', label='Cluster' if start == cluster_regions[0][0] else "")
        
        ax.set_title(title, fontsize=16, fontweight='bold')
        ax.set_ylabel('Price', fontsize=12)
        ax.set_xlabel('Date', fontsize=12)
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            ensure_dir(save_path)
            fig.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Cluster analysis chart saved to {save_path}")
        
        plt.show()
    
    def create_summary_plot(
        self,
        data: pd.DataFrame,
        signals: Optional[pd.Series] = None,
        cluster_signals: Optional[pd.Series] = None,
        title: str = "综合分析图",
        save_path: Optional[str] = None,
        window: Optional[int] = None
    ) -> None:
        """
        创建综合分析图
        
        Args:
            data: OHLCV 数据
            signals: 交易信号
            cluster_signals: 均线簇信号
            title: 图表标题
            save_path: 保存路径
            window: 显示窗口大小
        """
        # 选择数据窗口
        plot_data = data.tail(window) if window else data
        
        # 计算技术指标
        mas = calculate_multiple_mas(plot_data['close'], [20, 60, 120])
        macd_data = macd(plot_data['close'])
        
        fig, axes = plt.subplots(4, 1, figsize=(15, 16))
        
        # K线图
        ax1 = axes[0]
        self._plot_candlestick_subplot(ax1, plot_data)
        
        # 添加移动平均线
        for period in [20, 60, 120]:
            ax1.plot(mas.index, mas[f'MA_{period}'], 
                    label=f'MA{period}', alpha=0.8)
        
        # 添加交易信号
        if signals is not None:
            signal_data = signals.tail(window) if window else signals
            for i, (timestamp, signal) in enumerate(signal_data.items()):
                if signal == 1:
                    ax1.scatter(i, plot_data.iloc[i]['low'] * 0.995, 
                              marker='^', color=self.colors['bull'], s=100)
                elif signal == -1:
                    ax1.scatter(i, plot_data.iloc[i]['high'] * 1.005, 
                              marker='v', color=self.colors['bear'], s=100)
        
        ax1.set_title(title, fontsize=16, fontweight='bold')
        ax1.set_ylabel('Price', fontsize=12)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 成交量
        ax2 = axes[1]
        colors = [self.colors['bull'] if close >= open else self.colors['bear'] 
                 for close, open in zip(plot_data['close'], plot_data['open'])]
        ax2.bar(plot_data.index, plot_data['volume'], color=colors, alpha=0.7)
        ax2.set_ylabel('Volume', fontsize=12)
        ax2.grid(True, alpha=0.3)
        
        # MACD
        ax3 = axes[2]
        ax3.plot(macd_data.index, macd_data['DIF'], 
                label='DIF', color=self.colors['macd_line'])
        ax3.plot(macd_data.index, macd_data['DEA'], 
                label='DEA', color=self.colors['macd_signal'])
        
        colors_hist = [self.colors['bull'] if hist >= 0 else self.colors['bear'] 
                      for hist in macd_data['HIST']]
        ax3.bar(macd_data.index, macd_data['HIST'], 
               color=colors_hist, alpha=0.7, width=0.8)
        
        ax3.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        ax3.set_ylabel('MACD', fontsize=12)
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # 均线簇信号
        ax4 = axes[3]
        if cluster_signals is not None:
            cluster_data = cluster_signals.tail(window) if window else cluster_signals
            ax4.fill_between(cluster_data.index, 0, cluster_data.astype(int), 
                           alpha=0.3, color='yellow', label='Cluster')
        
        ax4.set_ylabel('Cluster Signal', fontsize=12)
        ax4.set_xlabel('Date', fontsize=12)
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            ensure_dir(save_path)
            fig.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Summary plot saved to {save_path}")
        
        plt.show()


if __name__ == "__main__":
    # 测试K线绘图
    import numpy as np
    
    # 创建测试数据
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=100, freq='4H')
    prices = 100 + np.cumsum(np.random.randn(100) * 0.5)
    
    data = pd.DataFrame({
        'open': prices,
        'high': prices * 1.01,
        'low': prices * 0.99,
        'close': prices,
        'volume': np.random.randint(1000, 10000, 100)
    }, index=dates)
    
    # 创建绘图器
    plotter = KlinePlotter()
    
    # 绘制基础K线图
    plotter.plot_candlestick(data, title="Test K-line Chart")
    
    # 绘制带指标的K线图
    plotter.plot_with_indicators(data, title="Test K-line with Indicators")
    
    # 创建模拟信号
    signals = pd.Series(np.random.choice([-1, 0, 1], 100), index=dates)
    plotter.plot_trading_signals(data, signals, title="Test Trading Signals")
