"""
MACD 指标

实现 MACD (Moving Average Convergence Divergence) 技术指标。
"""

import pandas as pd
import numpy as np
from typing import Tuple, Union
from numba import jit

from .ma_ema import ema


@jit(nopython=True)
def _macd_calc(
    prices: np.ndarray, 
    fast_period: int, 
    slow_period: int, 
    signal_period: int
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    计算 MACD 的核心函数（使用 numba 加速）
    
    Args:
        prices: 价格数组
        fast_period: 快线周期
        slow_period: 慢线周期
        signal_period: 信号线周期
        
    Returns:
        Tuple[np.ndarray, np.ndarray, np.ndarray]: (DIF, DEA, HIST)
    """
    n = len(prices)
    
    # 计算 EMA
    fast_alpha = 2.0 / (fast_period + 1)
    slow_alpha = 2.0 / (slow_period + 1)
    signal_alpha = 2.0 / (signal_period + 1)
    
    # 初始化
    fast_ema = np.full(n, np.nan)
    slow_ema = np.full(n, np.nan)
    dif = np.full(n, np.nan)
    dea = np.full(n, np.nan)
    hist = np.full(n, np.nan)
    
    # 计算快线 EMA
    if n >= fast_period:
        fast_ema[fast_period - 1] = np.mean(prices[:fast_period])
        for i in range(fast_period, n):
            fast_ema[i] = fast_alpha * prices[i] + (1 - fast_alpha) * fast_ema[i - 1]
    
    # 计算慢线 EMA
    if n >= slow_period:
        slow_ema[slow_period - 1] = np.mean(prices[:slow_period])
        for i in range(slow_period, n):
            slow_ema[i] = slow_alpha * prices[i] + (1 - slow_alpha) * slow_ema[i - 1]
    
    # 计算 DIF
    for i in range(max(fast_period, slow_period) - 1, n):
        if not np.isnan(fast_ema[i]) and not np.isnan(slow_ema[i]):
            dif[i] = fast_ema[i] - slow_ema[i]
    
    # 计算 DEA (DIF 的 EMA)
    signal_start = max(fast_period, slow_period) + signal_period - 2
    if n > signal_start:
        dea[signal_start] = np.mean(dif[max(fast_period, slow_period):signal_start + 1])
        for i in range(signal_start + 1, n):
            if not np.isnan(dif[i]):
                dea[i] = signal_alpha * dif[i] + (1 - signal_alpha) * dea[i - 1]
    
    # 计算 HIST
    for i in range(signal_start, n):
        if not np.isnan(dif[i]) and not np.isnan(dea[i]):
            hist[i] = dif[i] - dea[i]
    
    return dif, dea, hist


def macd(
    series: Union[pd.Series, np.ndarray], 
    fast_period: int = 12, 
    slow_period: int = 26, 
    signal_period: int = 9
) -> Union[pd.DataFrame, Tuple[np.ndarray, np.ndarray, np.ndarray]]:
    """
    计算 MACD 指标
    
    Args:
        series: 价格序列
        fast_period: 快线周期
        slow_period: 慢线周期
        signal_period: 信号线周期
        
    Returns:
        如果输入是 pd.Series，返回 DataFrame；否则返回元组
    """
    if isinstance(series, pd.Series):
        values = series.values
        dif, dea, hist = _macd_calc(values, fast_period, slow_period, signal_period)
        
        result = pd.DataFrame(index=series.index)
        result['DIF'] = dif
        result['DEA'] = dea
        result['HIST'] = hist
        
        return result
    else:
        return _macd_calc(series, fast_period, slow_period, signal_period)


def macd_signals(
    series: pd.Series,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9
) -> pd.Series:
    """
    计算 MACD 交易信号
    
    Args:
        series: 价格序列
        fast_period: 快线周期
        slow_period: 慢线周期
        signal_period: 信号线周期
        
    Returns:
        pd.Series: 交易信号 (1: 买入, -1: 卖出, 0: 无信号)
    """
    macd_data = macd(series, fast_period, slow_period, signal_period)
    
    dif = macd_data['DIF']
    dea = macd_data['DEA']
    hist = macd_data['HIST']
    
    # 计算信号
    signals = pd.Series(0, index=series.index)
    
    # 金叉信号：DIF 上穿 DEA 且 HIST > 0
    golden_cross = (dif > dea) & (dif.shift(1) <= dea.shift(1)) & (hist > 0)
    
    # 死叉信号：DIF 下穿 DEA 且 HIST < 0
    death_cross = (dif < dea) & (dif.shift(1) >= dea.shift(1)) & (hist < 0)
    
    signals[golden_cross] = 1
    signals[death_cross] = -1
    
    return signals


def macd_divergence(
    price_series: pd.Series,
    macd_series: pd.Series,
    lookback: int = 20
) -> pd.Series:
    """
    检测 MACD 背离
    
    Args:
        price_series: 价格序列
        macd_series: MACD 序列（DIF 或 HIST）
        lookback: 回看周期
        
    Returns:
        pd.Series: 背离信号 (1: 看涨背离, -1: 看跌背离, 0: 无背离)
    """
    signals = pd.Series(0, index=price_series.index)
    
    for i in range(lookback, len(price_series)):
        # 获取回看期间的数据
        price_window = price_series.iloc[i-lookback:i+1]
        macd_window = macd_series.iloc[i-lookback:i+1]
        
        # 找到价格和 MACD 的极值点
        price_high_idx = price_window.idxmax()
        price_low_idx = price_window.idxmin()
        macd_high_idx = macd_window.idxmax()
        macd_low_idx = macd_window.idxmin()
        
        # 检测看涨背离：价格创新低，MACD 不创新低
        if (price_low_idx == price_window.index[-1] and 
            macd_low_idx != macd_window.index[-1] and
            macd_window.iloc[-1] > macd_window.iloc[macd_low_idx]):
            signals.iloc[i] = 1
        
        # 检测看跌背离：价格创新高，MACD 不创新高
        elif (price_high_idx == price_window.index[-1] and 
              macd_high_idx != macd_window.index[-1] and
              macd_window.iloc[-1] < macd_window.iloc[macd_high_idx]):
            signals.iloc[i] = -1
    
    return signals


def macd_momentum(
    series: pd.Series,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9
) -> pd.Series:
    """
    计算 MACD 动量
    
    Args:
        series: 价格序列
        fast_period: 快线周期
        slow_period: 慢线周期
        signal_period: 信号线周期
        
    Returns:
        pd.Series: MACD 动量值
    """
    macd_data = macd(series, fast_period, slow_period, signal_period)
    hist = macd_data['HIST']
    
    # 计算 HIST 的变化率
    momentum = hist.diff()
    
    return momentum


if __name__ == "__main__":
    # 测试 MACD
    import numpy as np
    
    # 创建测试数据
    np.random.seed(42)
    prices = 100 + np.cumsum(np.random.randn(200) * 0.5)
    series = pd.Series(prices, name='price')
    
    # 计算 MACD
    macd_data = macd(series)
    print("MACD Data:")
    print(macd_data.tail())
    
    # 计算交易信号
    signals = macd_signals(series)
    print(f"\nMACD Signals: {signals.sum()} total signals")
    
    # 计算动量
    momentum = macd_momentum(series)
    print(f"\nMACD Momentum (last 5): {momentum.tail().values}")
    
    # 测试背离检测
    divergence = macd_divergence(series, macd_data['DIF'])
    print(f"\nDivergence signals: {divergence.sum()} total divergences")
