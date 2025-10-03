#!/usr/bin/env python3
"""
数据抓取脚本

从 Binance 抓取 OHLCV 数据并保存到 CSV 文件。
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
from datetime import datetime
from typing import List

from quantlab.data.loader import DataLoader
from quantlab.config import get_config, ensure_directories

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@click.command()
@click.option('--symbols', '-s', multiple=True, default=['BTCUSDT', 'ETHUSDT'], 
              help='交易对列表')
@click.option('--timeframes', '-t', multiple=True, default=['1h', '4h', '1d', '1w'], 
              help='时间框架列表')
@click.option('--since', default='2023-01-01', 
              help='开始日期 (YYYY-MM-DD)')
@click.option('--until', default='2025-10-01', 
              help='结束日期 (YYYY-MM-DD)')
@click.option('--force-refresh', is_flag=True, 
              help='强制刷新所有数据')
@click.option('--data-dir', default='data/raw', 
              help='数据存储目录')
def fetch_data(symbols, timeframes, since, until, force_refresh, data_dir):
    """
    从 Binance 抓取 OHLCV 数据并保存到 CSV 文件。
    
    示例:
        python scripts/fetch_to_csv.py --symbols BTCUSDT ETHUSDT --timeframes 1h 4h 1d 1w
        python scripts/fetch_to_csv.py --since 2024-01-01 --until 2024-12-31 --force-refresh
    """
    try:
        # 解析日期
        since_date = datetime.strptime(since, '%Y-%m-%d')
        until_date = datetime.strptime(until, '%Y-%m-%d')
        
        logger.info(f"Starting data fetch:")
        logger.info(f"  Symbols: {list(symbols)}")
        logger.info(f"  Timeframes: {list(timeframes)}")
        logger.info(f"  Period: {since_date} to {until_date}")
        logger.info(f"  Force refresh: {force_refresh}")
        
        # 确保目录存在
        Path(data_dir).mkdir(parents=True, exist_ok=True)
        
        # 创建数据加载器
        loader = DataLoader(data_dir)
        
        # 测试连接
        if not loader.client.test_connection():
            logger.error("Failed to connect to Binance API")
            return
        
        logger.info("Connected to Binance API successfully")
        
        # 批量抓取数据
        results = loader.fetch_multiple(
            symbols=list(symbols),
            timeframes=list(timeframes),
            since=since_date,
            until=until_date,
            force_refresh=force_refresh
        )
        
        # 显示结果摘要
        logger.info("\n" + "="*50)
        logger.info("FETCH SUMMARY")
        logger.info("="*50)
        
        for symbol in symbols:
            logger.info(f"\n{symbol}:")
            for timeframe in timeframes:
                if symbol in results and timeframe in results[symbol]:
                    data = results[symbol][timeframe]
                    if not data.empty:
                        logger.info(f"  {timeframe}: {len(data)} records, "
                                  f"{data.index[0]} to {data.index[-1]}")
                    else:
                        logger.warning(f"  {timeframe}: No data fetched")
        
        logger.info("\nData fetch completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during data fetch: {e}")
        raise


if __name__ == '__main__':
    fetch_data()