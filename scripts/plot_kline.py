#!/usr/bin/env python3
"""
K线绘图脚本

绘制K线图和技术指标。
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 确保可以导入 quantlab 模块
os.chdir(project_root)

import click
import logging
import pandas as pd

from quantlab.data.loader import DataLoader
from quantlab.plotting.kline import KlinePlotter
from quantlab.config import get_config

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@click.command()
@click.option('--symbol', '-s', default='BTCUSDT', 
              help='交易对符号')
@click.option('--timeframe', '-t', default='4h', 
              help='时间框架')
@click.option('--window', '-w', type=int, default=500, 
              help='显示窗口大小')
@click.option('--data-dir', default='data/raw', 
              help='数据目录')
@click.option('--plots-dir', default='plots', 
              help='图表保存目录')
@click.option('--show-ma', is_flag=True, default=True, 
              help='显示移动平均线')
@click.option('--show-ema', is_flag=True, default=True, 
              help='显示指数移动平均线')
@click.option('--show-macd', is_flag=True, default=True, 
              help='显示MACD')
@click.option('--style', default='default', 
              type=click.Choice(['default', 'dark']), 
              help='绘图样式')
def plot_kline(symbol, timeframe, window, data_dir, plots_dir, 
               show_ma, show_ema, show_macd, style):
    """
    绘制K线图和技术指标。
    
    示例:
        python scripts/plot_kline.py --symbol BTCUSDT --timeframe 4h --window 500
        python scripts/plot_kline.py --symbol ETHUSDT --timeframe 1d --style dark
    """
    try:
        logger.info(f"Starting K-line plot:")
        logger.info(f"  Symbol: {symbol}")
        logger.info(f"  Timeframe: {timeframe}")
        logger.info(f"  Window: {window}")
        logger.info(f"  Style: {style}")
        
        # 确保目录存在
        Path(plots_dir).mkdir(parents=True, exist_ok=True)
        
        # 加载数据
        loader = DataLoader(data_dir)
        data = loader.load_existing_data(symbol, timeframe)
        
        if data.empty:
            logger.error(f"No data found for {symbol} {timeframe}")
            logger.info("Please run fetch_to_csv.py first to download data")
            return
        
        logger.info(f"Loaded {len(data)} records for {symbol} {timeframe}")
        
        # 创建绘图器
        plotter = KlinePlotter(style=style)
        
        # 生成文件名
        filename = f"{symbol}_{timeframe}_kline.png"
        save_path = Path(plots_dir) / filename
        
        # 绘制K线图
        plotter.plot_with_indicators(
            data=data,
            title=f"{symbol} {timeframe} K线图",
            save_path=str(save_path),
            show_ma=show_ma,
            show_ema=show_ema,
            show_macd=show_macd,
            window=window
        )
        
        logger.info(f"K-line chart saved to {save_path}")
        
    except Exception as e:
        logger.error(f"Error during plotting: {e}")
        raise


if __name__ == '__main__':
    plot_kline()