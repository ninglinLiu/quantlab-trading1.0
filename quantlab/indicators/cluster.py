"""
均线簇指标

实现均线簇识别和相关信号生成。
"""

import pandas as pd
import numpy as np
from typing import List, Tuple, Union
from numba import jit

from .ma_ema import ma, ema


@jit(nopython=True)
def _cluster_width_calc(ma_values: np.ndarray) -> np.ndarray:
    """
    计算均线簇宽度（使用 numba 加速）
    
    Args:
        ma_values: 均线值数组 (n_samples, n_mas)
        
    Returns:
        np.ndarray: 每行的均线簇宽度
    """
    n_samples, n_mas = ma_values.shape
    widths = np.full(n_samples, np.nan)
    
    for i in range(n_samples):
        # 检查是否有有效值
        valid_mask = ~np.isnan(ma_values[i])
        if np.sum(valid_mask) >= 2:  # 至少需要2条均线
            valid_values = ma_values[i][valid_mask]
            widths[i] = np.max(valid_values) - np.min(valid_values)
    
    return widths


def calculate_cluster_width(
    price_series: pd.Series,
    ma_periods: List[int],
    ma_type: str = 'ma'
) -> pd.Series:
    """
    计算均线簇宽度
    
    Args:
        price_series: 价格序列
        ma_periods: 均线周期列表
        ma_type: 均线类型 ('ma' 或 'ema')
        
    Returns:
        pd.Series: 均线簇宽度序列
    """
    # 计算多条均线
    ma_data = pd.DataFrame(index=price_series.index)
    
    for period in ma_periods:
        if ma_type.lower() == 'ema':
            ma_data[f'MA_{period}'] = ema(price_series, period)
        else:
            ma_data[f'MA_{period}'] = ma(price_series, period)
    
    # 转换为 numpy 数组进行计算
    ma_values = ma_data.values
    widths = _cluster_width_calc(ma_values)
    
    return pd.Series(widths, index=price_series.index, name='cluster_width')


def detect_cluster(
    price_series: pd.Series,
    ma_periods: List[int],
    cluster_threshold: float = 0.01,
    ma_type: str = 'ma'
) -> pd.Series:
    """
    检测均线簇
    
    Args:
        price_series: 价格序列
        ma_periods: 均线周期列表
        cluster_threshold: 簇密集阈值（相对于价格的比例）
        ma_type: 均线类型 ('ma' 或 'ema')
        
    Returns:
        pd.Series: 均线簇信号 (True: 形成簇, False: 未形成簇)
    """
    # 计算均线簇宽度
    cluster_width = calculate_cluster_width(price_series, ma_periods, ma_type)
    
    # 计算相对宽度
    relative_width = cluster_width / price_series
    
    # 检测簇
    cluster_signal = relative_width <= cluster_threshold
    
    return cluster_signal


def get_cluster_boundaries(
    price_series: pd.Series,
    ma_periods: List[int],
    ma_type: str = 'ma'
) -> Tuple[pd.Series, pd.Series]:
    """
    获取均线簇的上下边界
    
    Args:
        price_series: 价格序列
        ma_periods: 均线周期列表
        ma_type: 均线类型 ('ma' 或 'ema')
        
    Returns:
        Tuple[pd.Series, pd.Series]: (上边界, 下边界)
    """
    # 计算多条均线
    ma_data = pd.DataFrame(index=price_series.index)
    
    for period in ma_periods:
        if ma_type.lower() == 'ema':
            ma_data[f'MA_{period}'] = ema(price_series, period)
        else:
            ma_data[f'MA_{period}'] = ma(price_series, period)
    
    # 计算上下边界
    upper_bound = ma_data.max(axis=1)
    lower_bound = ma_data.min(axis=1)
    
    return upper_bound, lower_bound


def cluster_breakout_signals(
    price_series: pd.Series,
    ma_periods: List[int],
    cluster_threshold: float = 0.01,
    ma_type: str = 'ma'
) -> pd.Series:
    """
    生成均线簇突破信号
    
    Args:
        price_series: 价格序列
        ma_periods: 均线周期列表
        cluster_threshold: 簇密集阈值
        ma_type: 均线类型
        
    Returns:
        pd.Series: 突破信号 (1: 向上突破, -1: 向下突破, 0: 无信号)
    """
    # 检测均线簇
    cluster_signal = detect_cluster(price_series, ma_periods, cluster_threshold, ma_type)
    
    # 获取簇边界
    upper_bound, lower_bound = get_cluster_boundaries(price_series, ma_periods, ma_type)
    
    # 初始化信号
    signals = pd.Series(0, index=price_series.index)
    
    # 检测突破
    for i in range(1, len(price_series)):
        # 检查是否在簇中
        if cluster_signal.iloc[i-1]:
            # 向上突破：价格突破上边界
            if (price_series.iloc[i] > upper_bound.iloc[i] and 
                price_series.iloc[i-1] <= upper_bound.iloc[i-1]):
                signals.iloc[i] = 1
            
            # 向下突破：价格突破下边界
            elif (price_series.iloc[i] < lower_bound.iloc[i] and 
                  price_series.iloc[i-1] >= lower_bound.iloc[i-1]):
                signals.iloc[i] = -1
    
    return signals


def cluster_retest_signals(
    price_series: pd.Series,
    ma_periods: List[int],
    cluster_threshold: float = 0.01,
    ma_type: str = 'ma',
    retest_periods: int = 3
) -> pd.Series:
    """
    生成均线簇回踩确认信号
    
    Args:
        price_series: 价格序列
        ma_periods: 均线周期列表
        cluster_threshold: 簇密集阈值
        ma_type: 均线类型
        retest_periods: 回踩确认周期数
        
    Returns:
        pd.Series: 回踩确认信号 (1: 向上突破后回踩确认, -1: 向下突破后回踩确认, 0: 无信号)
    """
    # 获取突破信号
    breakout_signals = cluster_breakout_signals(price_series, ma_periods, cluster_threshold, ma_type)
    
    # 获取簇边界
    upper_bound, lower_bound = get_cluster_boundaries(price_series, ma_periods, ma_type)
    
    # 初始化信号
    retest_signals = pd.Series(0, index=price_series.index)
    
    # 检测回踩确认
    for i in range(retest_periods, len(price_series)):
        # 检查是否有向上突破
        if breakout_signals.iloc[i-retest_periods] == 1:
            # 检查回踩：价格回踩到上边界附近但不跌破
            retest_window = price_series.iloc[i-retest_periods:i+1]
            bound_window = upper_bound.iloc[i-retest_periods:i+1]
            
            # 回踩确认：价格回踩到边界附近但未跌破
            if (retest_window.min() >= bound_window.min() * 0.995 and  # 允许0.5%的误差
                retest_window.iloc[-1] > bound_window.iloc[-1]):
                retest_signals.iloc[i] = 1
        
        # 检查是否有向下突破
        elif breakout_signals.iloc[i-retest_periods] == -1:
            # 检查回踩：价格回踩到下边界附近但不涨破
            retest_window = price_series.iloc[i-retest_periods:i+1]
            bound_window = lower_bound.iloc[i-retest_periods:i+1]
            
            # 回踩确认：价格回踩到边界附近但未涨破
            if (retest_window.max() <= bound_window.max() * 1.005 and  # 允许0.5%的误差
                retest_window.iloc[-1] < bound_window.iloc[-1]):
                retest_signals.iloc[i] = -1
    
    return retest_signals


def cluster_strength(
    price_series: pd.Series,
    ma_periods: List[int],
    ma_type: str = 'ma'
) -> pd.Series:
    """
    计算均线簇强度
    
    Args:
        price_series: 价格序列
        ma_periods: 均线周期列表
        ma_type: 均线类型
        
    Returns:
        pd.Series: 簇强度 (0-1, 1表示最强)
    """
    # 计算均线簇宽度
    cluster_width = calculate_cluster_width(price_series, ma_periods, ma_type)
    
    # 计算相对宽度
    relative_width = cluster_width / price_series
    
    # 计算强度（相对宽度越小，强度越高）
    strength = 1 - relative_width
    strength = strength.clip(0, 1)  # 限制在0-1之间
    
    return strength


if __name__ == "__main__":
    # 测试均线簇
    import numpy as np
    
    # 创建测试数据
    np.random.seed(42)
    prices = 100 + np.cumsum(np.random.randn(200) * 0.5)
    series = pd.Series(prices, name='price')
    
    # 测试参数
    ma_periods = [20, 60, 120]
    
    # 计算均线簇宽度
    cluster_width = calculate_cluster_width(series, ma_periods)
    print("Cluster Width (last 5):")
    print(cluster_width.tail())
    
    # 检测均线簇
    cluster_signal = detect_cluster(series, ma_periods, cluster_threshold=0.01)
    print(f"\nCluster signals: {cluster_signal.sum()} total clusters")
    
    # 生成突破信号
    breakout_signals = cluster_breakout_signals(series, ma_periods)
    print(f"\nBreakout signals: {breakout_signals.sum()} total breakouts")
    
    # 生成回踩确认信号
    retest_signals = cluster_retest_signals(series, ma_periods)
    print(f"\nRetest signals: {retest_signals.sum()} total retests")
    
    # 计算簇强度
    strength = cluster_strength(series, ma_periods)
    print(f"\nCluster strength (last 5): {strength.tail().values}")
