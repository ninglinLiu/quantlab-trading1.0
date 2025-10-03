"""
移动平均线指标

实现简单移动平均线(MA)和指数移动平均线(EMA)。
"""

import pandas as pd
import numpy as np
from typing import Union, List
from numba import jit


@jit(nopython=True)
def _ema_calc(prices: np.ndarray, period: int) -> np.ndarray:
    """
    计算 EMA 的核心函数（使用 numba 加速）
    
    Args:
        prices: 价格数组
        period: 周期
        
    Returns:
        np.ndarray: EMA 值
    """
    n = len(prices)
    ema = np.full(n, np.nan)
    
    if n < period:
        return ema
    
    # 计算平滑因子
    alpha = 2.0 / (period + 1)
    
    # 第一个 EMA 值使用 SMA
    ema[period - 1] = np.mean(prices[:period])
    
    # 计算后续 EMA 值
    for i in range(period, n):
        ema[i] = alpha * prices[i] + (1 - alpha) * ema[i - 1]
    
    return ema


@jit(nopython=True)
def _sma_calc(prices: np.ndarray, period: int) -> np.ndarray:
    """
    计算 SMA 的核心函数（使用 numba 加速）
    
    Args:
        prices: 价格数组
        period: 周期
        
    Returns:
        np.ndarray: SMA 值
    """
    n = len(prices)
    sma = np.full(n, np.nan)
    
    if n < period:
        return sma
    
    # 计算 SMA
    for i in range(period - 1, n):
        sma[i] = np.mean(prices[i - period + 1:i + 1])
    
    return sma


def ema(series: Union[pd.Series, np.ndarray], period: int) -> Union[pd.Series, np.ndarray]:
    """
    计算指数移动平均线 (EMA)
    
    Args:
        series: 价格序列
        period: 周期
        
    Returns:
        与输入相同类型的 EMA 序列
    """
    if isinstance(series, pd.Series):
        values = series.values
        result = _ema_calc(values, period)
        return pd.Series(result, index=series.index, name=f'EMA_{period}')
    else:
        return _ema_calc(series, period)


def ma(series: Union[pd.Series, np.ndarray], period: int) -> Union[pd.Series, np.ndarray]:
    """
    计算简单移动平均线 (MA/SMA)
    
    Args:
        series: 价格序列
        period: 周期
        
    Returns:
        与输入相同类型的 MA 序列
    """
    if isinstance(series, pd.Series):
        values = series.values
        result = _sma_calc(values, period)
        return pd.Series(result, index=series.index, name=f'MA_{period}')
    else:
        return _sma_calc(series, period)


def calculate_multiple_mas(
    series: pd.Series, 
    periods: List[int]
) -> pd.DataFrame:
    """
    计算多条移动平均线
    
    Args:
        series: 价格序列
        periods: 周期列表
        
    Returns:
        pd.DataFrame: 包含多条 MA 的 DataFrame
    """
    result = pd.DataFrame(index=series.index)
    
    for period in periods:
        result[f'MA_{period}'] = ma(series, period)
        result[f'EMA_{period}'] = ema(series, period)
    
    return result


def calculate_multiple_emas(
    series: pd.Series, 
    periods: List[int]
) -> pd.DataFrame:
    """
    计算多条指数移动平均线
    
    Args:
        series: 价格序列
        periods: 周期列表
        
    Returns:
        pd.DataFrame: 包含多条 EMA 的 DataFrame
    """
    result = pd.DataFrame(index=series.index)
    
    for period in periods:
        result[f'EMA_{period}'] = ema(series, period)
    
    return result


def ma_crossover(short_ma: pd.Series, long_ma: pd.Series) -> pd.Series:
    """
    计算移动平均线交叉信号
    
    Args:
        short_ma: 短期均线
        long_ma: 长期均线
        
    Returns:
        pd.Series: 交叉信号 (1: 金叉, -1: 死叉, 0: 无交叉)
    """
    # 计算交叉点
    cross_up = (short_ma > long_ma) & (short_ma.shift(1) <= long_ma.shift(1))
    cross_down = (short_ma < long_ma) & (short_ma.shift(1) >= long_ma.shift(1))
    
    signals = pd.Series(0, index=short_ma.index)
    signals[cross_up] = 1
    signals[cross_down] = -1
    
    return signals


def ma_slope(ma_series: pd.Series, periods: int = 5) -> pd.Series:
    """
    计算移动平均线的斜率
    
    Args:
        ma_series: 移动平均线序列
        periods: 计算斜率的周期
        
    Returns:
        pd.Series: 斜率值
    """
    return ma_series.diff(periods) / periods


if __name__ == "__main__":
    # 测试移动平均线
    import numpy as np
    
    # 创建测试数据
    np.random.seed(42)
    prices = 100 + np.cumsum(np.random.randn(100) * 0.5)
    series = pd.Series(prices, name='price')
    
    # 计算 MA 和 EMA
    ma_20 = ma(series, 20)
    ema_20 = ema(series, 20)
    
    print("MA 20:", ma_20.tail())
    print("EMA 20:", ema_20.tail())
    
    # 计算多条均线
    periods = [20, 60, 120]
    mas = calculate_multiple_mas(series, periods)
    print("\nMultiple MAs:")
    print(mas.tail())
    
    # 测试交叉信号
    signals = ma_crossover(ma(series, 10), ma(series, 20))
    print(f"\nCrossover signals: {signals.sum()} total signals")
