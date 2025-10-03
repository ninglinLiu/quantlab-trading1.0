"""
时间框架工具

处理不同时间框架的转换和计算。
"""

from datetime import datetime, timedelta
from typing import Dict, List, Union
import pandas as pd


# 时间框架映射（毫秒）
TIMEFRAME_MS = {
    '1m': 60 * 1000,
    '5m': 5 * 60 * 1000,
    '15m': 15 * 60 * 1000,
    '30m': 30 * 60 * 1000,
    '1h': 60 * 60 * 1000,
    '4h': 4 * 60 * 60 * 1000,
    '1d': 24 * 60 * 60 * 1000,
    '1w': 7 * 24 * 60 * 60 * 1000,
}

# 支持的时间框架
SUPPORTED_TIMEFRAMES = list(TIMEFRAME_MS.keys())

# 时间框架优先级（用于排序）
TIMEFRAME_PRIORITY = {
    '1m': 1,
    '5m': 2,
    '15m': 3,
    '30m': 4,
    '1h': 5,
    '4h': 6,
    '1d': 7,
    '1w': 8,
}


def get_timeframe_ms(timeframe: str) -> int:
    """
    获取时间框架对应的毫秒数
    
    Args:
        timeframe: 时间框架字符串
        
    Returns:
        int: 毫秒数
        
    Raises:
        ValueError: 不支持的时间框架
    """
    if timeframe not in TIMEFRAME_MS:
        raise ValueError(f"Unsupported timeframe: {timeframe}. Supported: {SUPPORTED_TIMEFRAMES}")
    
    return TIMEFRAME_MS[timeframe]


def get_timeframe_delta(timeframe: str) -> timedelta:
    """
    获取时间框架对应的 timedelta 对象
    
    Args:
        timeframe: 时间框架字符串
        
    Returns:
        timedelta: 时间间隔
    """
    ms = get_timeframe_ms(timeframe)
    return timedelta(milliseconds=ms)


def is_higher_timeframe(timeframe1: str, timeframe2: str) -> bool:
    """
    判断时间框架1是否比时间框架2更高（时间间隔更长）
    
    Args:
        timeframe1: 时间框架1
        timeframe2: 时间框架2
        
    Returns:
        bool: True 如果时间框架1更高
    """
    return TIMEFRAME_PRIORITY[timeframe1] > TIMEFRAME_PRIORITY[timeframe2]


def get_higher_timeframes(timeframe: str) -> List[str]:
    """
    获取比指定时间框架更高的所有时间框架
    
    Args:
        timeframe: 基准时间框架
        
    Returns:
        List[str]: 更高时间框架列表
    """
    current_priority = TIMEFRAME_PRIORITY[timeframe]
    return [tf for tf, priority in TIMEFRAME_PRIORITY.items() if priority > current_priority]


def get_lower_timeframes(timeframe: str) -> List[str]:
    """
    获取比指定时间框架更低的所有时间框架
    
    Args:
        timeframe: 基准时间框架
        
    Returns:
        List[str]: 更低时间框架列表
    """
    current_priority = TIMEFRAME_PRIORITY[timeframe]
    return [tf for tf, priority in TIMEFRAME_PRIORITY.items() if priority < current_priority]


def resample_data(
    data: pd.DataFrame,
    from_timeframe: str,
    to_timeframe: str,
    method: str = 'ohlc'
) -> pd.DataFrame:
    """
    重采样数据到不同时间框架
    
    Args:
        data: 原始数据 DataFrame
        from_timeframe: 源时间框架
        to_timeframe: 目标时间框架
        method: 重采样方法 ('ohlc', 'last', 'first', 'mean')
        
    Returns:
        pd.DataFrame: 重采样后的数据
    """
    if is_higher_timeframe(from_timeframe, to_timeframe):
        raise ValueError(f"Cannot resample from {from_timeframe} to {to_timeframe} (higher to lower)")
    
    if from_timeframe == to_timeframe:
        return data.copy()
    
    # 计算重采样频率
    delta = get_timeframe_delta(to_timeframe)
    freq = f"{delta.total_seconds():.0f}s"
    
    if method == 'ohlc':
        # OHLC 重采样
        resampled = data.resample(freq).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        })
    elif method == 'last':
        resampled = data.resample(freq).last()
    elif method == 'first':
        resampled = data.resample(freq).first()
    elif method == 'mean':
        resampled = data.resample(freq).mean()
    else:
        raise ValueError(f"Unsupported resample method: {method}")
    
    # 删除空值
    resampled = resampled.dropna()
    
    return resampled


def align_timeframe(timestamp: datetime, timeframe: str) -> datetime:
    """
    将时间戳对齐到指定时间框架的边界
    
    Args:
        timestamp: 原始时间戳
        timeframe: 目标时间框架
        
    Returns:
        datetime: 对齐后的时间戳
    """
    delta = get_timeframe_delta(timeframe)
    
    if timeframe == '1w':
        # 周对齐到周一
        days_since_monday = timestamp.weekday()
        aligned = timestamp - timedelta(days=days_since_monday)
        aligned = aligned.replace(hour=0, minute=0, second=0, microsecond=0)
    elif timeframe == '1d':
        # 日对齐到00:00
        aligned = timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
    elif timeframe in ['1h', '4h']:
        # 小时对齐
        hours = int(timestamp.hour / (delta.total_seconds() / 3600)) * (delta.total_seconds() / 3600)
        aligned = timestamp.replace(hour=int(hours), minute=0, second=0, microsecond=0)
    else:
        # 分钟对齐
        minutes = int(timestamp.minute / (delta.total_seconds() / 60)) * (delta.total_seconds() / 60)
        aligned = timestamp.replace(minute=int(minutes), second=0, microsecond=0)
    
    return aligned


def get_timeframe_bars_count(
    start_time: datetime,
    end_time: datetime,
    timeframe: str
) -> int:
    """
    计算指定时间范围内的时间框架K线数量
    
    Args:
        start_time: 开始时间
        end_time: 结束时间
        timeframe: 时间框架
        
    Returns:
        int: K线数量
    """
    delta = get_timeframe_delta(timeframe)
    duration = end_time - start_time
    return int(duration.total_seconds() / delta.total_seconds())


def validate_timeframe(timeframe: str) -> bool:
    """
    验证时间框架是否支持
    
    Args:
        timeframe: 时间框架字符串
        
    Returns:
        bool: 是否支持
    """
    return timeframe in SUPPORTED_TIMEFRAMES


def get_timeframe_info(timeframe: str) -> Dict:
    """
    获取时间框架信息
    
    Args:
        timeframe: 时间框架字符串
        
    Returns:
        Dict: 时间框架信息
    """
    if not validate_timeframe(timeframe):
        raise ValueError(f"Unsupported timeframe: {timeframe}")
    
    return {
        'timeframe': timeframe,
        'milliseconds': TIMEFRAME_MS[timeframe],
        'seconds': TIMEFRAME_MS[timeframe] / 1000,
        'minutes': TIMEFRAME_MS[timeframe] / (1000 * 60),
        'hours': TIMEFRAME_MS[timeframe] / (1000 * 60 * 60),
        'days': TIMEFRAME_MS[timeframe] / (1000 * 60 * 60 * 24),
        'priority': TIMEFRAME_PRIORITY[timeframe],
        'higher_timeframes': get_higher_timeframes(timeframe),
        'lower_timeframes': get_lower_timeframes(timeframe)
    }


if __name__ == "__main__":
    # 测试时间框架工具
    print("Supported timeframes:", SUPPORTED_TIMEFRAMES)
    
    # 测试时间框架信息
    for tf in ['1h', '4h', '1d']:
        info = get_timeframe_info(tf)
        print(f"\n{tf} info:", info)
    
    # 测试时间对齐
    now = datetime.now()
    aligned_1h = align_timeframe(now, '1h')
    aligned_4h = align_timeframe(now, '4h')
    print(f"\nTime alignment:")
    print(f"Original: {now}")
    print(f"1h aligned: {aligned_1h}")
    print(f"4h aligned: {aligned_4h}")
    
    # 测试K线数量计算
    start = datetime(2024, 1, 1)
    end = datetime(2024, 1, 2)
    bars_1h = get_timeframe_bars_count(start, end, '1h')
    bars_4h = get_timeframe_bars_count(start, end, '4h')
    print(f"\nBars count from {start} to {end}:")
    print(f"1h bars: {bars_1h}")
    print(f"4h bars: {bars_4h}")
