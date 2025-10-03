#!/usr/bin/env python3
"""
模拟数据生成器

生成模拟的OHLCV数据用于演示项目功能
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 确保可以导入 quantlab 模块
os.chdir(project_root)

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import click

def generate_mock_data(symbol: str, timeframe: str, start_date: str, end_date: str) -> pd.DataFrame:
    """生成模拟OHLCV数据"""
    
    # 解析日期
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    # 根据时间框架确定频率
    freq_map = {
        '1h': '1H',
        '4h': '4H', 
        '1d': '1D',
        '1w': '1W'
    }
    
    freq = freq_map.get(timeframe, '4H')
    
    # 生成时间序列
    dates = pd.date_range(start=start, end=end, freq=freq)
    
    # 基础价格（根据币种设置）
    base_prices = {
        'BTCUSDT': 50000,
        'ETHUSDT': 3000,
        'SOLUSDT': 100,
        'ADAUSDT': 0.5
    }
    
    base_price = base_prices.get(symbol, 100)
    
    # 生成价格数据
    n = len(dates)
    
    # 使用随机游走生成价格
    returns = np.random.normal(0, 0.02, n)  # 2%的日波动率
    prices = [base_price]
    
    for i in range(1, n):
        new_price = prices[-1] * (1 + returns[i])
        prices.append(new_price)
    
    # 生成OHLCV数据
    data = []
    
    for i, (date, close) in enumerate(zip(dates, prices)):
        # 生成开盘价（接近前一个收盘价）
        if i == 0:
            open_price = close
        else:
            open_price = prices[i-1] * (1 + np.random.normal(0, 0.005))
        
        # 生成高低价
        high = max(open_price, close) * (1 + abs(np.random.normal(0, 0.01)))
        low = min(open_price, close) * (1 - abs(np.random.normal(0, 0.01)))
        
        # 确保价格逻辑正确
        high = max(high, open_price, close)
        low = min(low, open_price, close)
        
        # 生成成交量（随机）
        volume = np.random.uniform(1000, 10000)
        
        data.append({
            'timestamp': date,
            'open': round(open_price, 2),
            'high': round(high, 2),
            'low': round(low, 2),
            'close': round(close, 2),
            'volume': round(volume, 2)
        })
    
    df = pd.DataFrame(data)
    df.set_index('timestamp', inplace=True)
    
    return df

@click.command()
@click.option('--symbols', '-s', multiple=True, default=['BTCUSDT', 'ETHUSDT'], 
              help='交易对列表')
@click.option('--timeframes', '-t', multiple=True, default=['1h', '4h', '1d', '1w'], 
              help='时间框架列表')
@click.option('--since', default='2023-01-01', 
              help='开始日期 (YYYY-MM-DD)')
@click.option('--until', default='2025-10-01', 
              help='结束日期 (YYYY-MM-DD)')
@click.option('--data-dir', default='data/raw', 
              help='数据存储目录')
def generate_mock_data_cli(symbols, timeframes, since, until, data_dir):
    """生成模拟数据用于演示"""
    
    print("生成模拟数据...")
    print(f"交易对: {list(symbols)}")
    print(f"时间框架: {list(timeframes)}")
    print(f"时间范围: {since} 到 {until}")
    
    # 确保目录存在
    Path(data_dir).mkdir(parents=True, exist_ok=True)
    
    # 生成数据
    for symbol in symbols:
        print(f"\n生成 {symbol} 数据...")
        for timeframe in timeframes:
            print(f"  生成 {timeframe} 数据...")
            
            # 生成模拟数据
            data = generate_mock_data(symbol, timeframe, since, until)
            
            # 保存到CSV
            filename = f"{symbol}_{timeframe}.csv"
            filepath = Path(data_dir) / filename
            
            data.to_csv(filepath)
            print(f"    保存到: {filepath}")
            print(f"    数据量: {len(data)} 条记录")
            print(f"    时间范围: {data.index[0]} 到 {data.index[-1]}")
    
    print("\n模拟数据生成完成！")
    print("现在可以运行绘图和回测脚本了。")

if __name__ == '__main__':
    generate_mock_data_cli()
