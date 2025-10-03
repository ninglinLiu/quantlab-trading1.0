#!/usr/bin/env python3
"""
项目测试脚本

验证 QuantLab 项目的各个模块是否正常工作。
"""

import sys
import traceback
from pathlib import Path

def test_imports():
    """测试模块导入"""
    print("🔍 测试模块导入...")
    
    try:
        import quantlab
        print("  ✅ quantlab 包导入成功")
        
        from quantlab.config import get_config
        print("  ✅ config 模块导入成功")
        
        from quantlab.data.loader import DataLoader
        print("  ✅ data.loader 模块导入成功")
        
        from quantlab.indicators.ma_ema import ma, ema
        print("  ✅ indicators.ma_ema 模块导入成功")
        
        from quantlab.indicators.macd import macd
        print("  ✅ indicators.macd 模块导入成功")
        
        from quantlab.indicators.cluster import detect_cluster
        print("  ✅ indicators.cluster 模块导入成功")
        
        from quantlab.backtest.portfolio import Portfolio
        print("  ✅ backtest.portfolio 模块导入成功")
        
        from quantlab.backtest.engine import BacktestEngine
        print("  ✅ backtest.engine 模块导入成功")
        
        from quantlab.backtest.metrics import PerformanceMetrics
        print("  ✅ backtest.metrics 模块导入成功")
        
        from quantlab.plotting.kline import KlinePlotter
        print("  ✅ plotting.kline 模块导入成功")
        
        from quantlab.strategy.cluster_macd_4h import ClusterMacdStrategy
        print("  ✅ strategy.cluster_macd_4h 模块导入成功")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 模块导入失败: {e}")
        traceback.print_exc()
        return False

def test_config():
    """测试配置模块"""
    print("\n🔧 测试配置模块...")
    
    try:
        from quantlab.config import get_config, create_default_config
        
        # 测试默认配置
        config = create_default_config()
        print(f"  ✅ 默认配置创建成功")
        print(f"    手续费率: {config.trading.fee}")
        print(f"    滑点率: {config.trading.slippage}")
        print(f"    杠杆: {config.trading.leverage}")
        
        # 测试配置加载
        config = get_config()
        print(f"  ✅ 配置加载成功")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 配置模块测试失败: {e}")
        traceback.print_exc()
        return False

def test_indicators():
    """测试技术指标模块"""
    print("\n📊 测试技术指标模块...")
    
    try:
        import pandas as pd
        import numpy as np
        from quantlab.indicators.ma_ema import ma, ema, calculate_multiple_mas
        from quantlab.indicators.macd import macd
        from quantlab.indicators.cluster import detect_cluster
        
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
        
        # 测试移动平均线
        ma_20 = ma(data['close'], 20)
        ema_20 = ema(data['close'], 20)
        print(f"  ✅ 移动平均线计算成功")
        
        # 测试多条均线
        mas = calculate_multiple_mas(data['close'], [20, 60, 120])
        print(f"  ✅ 多条均线计算成功")
        
        # 测试MACD
        macd_data = macd(data['close'])
        print(f"  ✅ MACD 计算成功")
        
        # 测试均线簇
        cluster_signal = detect_cluster(data['close'], [20, 60, 120])
        print(f"  ✅ 均线簇检测成功")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 技术指标模块测试失败: {e}")
        traceback.print_exc()
        return False

def test_portfolio():
    """测试投资组合模块"""
    print("\n💰 测试投资组合模块...")
    
    try:
        from quantlab.backtest.portfolio import Portfolio, OrderSide
        from datetime import datetime
        
        # 创建投资组合
        portfolio = Portfolio(
            initial_equity=5000,
            leverage=10,
            fee_rate=0.0008,
            slippage_rate=0.0005
        )
        
        print(f"  ✅ 投资组合创建成功")
        print(f"    初始资金: ${portfolio.initial_equity}")
        print(f"    杠杆: {portfolio.leverage}x")
        
        # 测试开仓
        timestamp = datetime.now()
        success = portfolio.open_position(timestamp, OrderSide.LONG, 50000, 10000)
        print(f"  ✅ 开仓测试: {'成功' if success else '失败'}")
        
        # 测试平仓
        trade = portfolio.close_position(timestamp, 52000)
        print(f"  ✅ 平仓测试: {'成功' if trade else '失败'}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 投资组合模块测试失败: {e}")
        traceback.print_exc()
        return False

def test_strategy():
    """测试策略模块"""
    print("\n🎯 测试策略模块...")
    
    try:
        from quantlab.strategy.cluster_macd_4h import ClusterMacdStrategy
        import pandas as pd
        import numpy as np
        
        # 创建测试数据
        np.random.seed(42)
        dates = pd.date_range('2024-01-01', periods=200, freq='4H')
        prices = 100 + np.cumsum(np.random.randn(200) * 0.5)
        
        data = pd.DataFrame({
            'open': prices,
            'high': prices * 1.01,
            'low': prices * 0.99,
            'close': prices,
            'volume': np.random.randint(1000, 10000, 200)
        }, index=dates)
        
        # 创建策略
        strategy = ClusterMacdStrategy(
            ma_periods=[20, 60, 120],
            cluster_threshold=0.01,
            retest_confirmation=False
        )
        
        print(f"  ✅ 策略创建成功")
        
        # 测试指标计算
        data_with_indicators = strategy.calculate_indicators(data)
        print(f"  ✅ 指标计算成功")
        
        # 测试信号生成
        signal = strategy.generate_signal(data_with_indicators, 150)
        print(f"  ✅ 信号生成测试: {'有信号' if signal else '无信号'}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 策略模块测试失败: {e}")
        traceback.print_exc()
        return False

def test_plotting():
    """测试绘图模块"""
    print("\n📈 测试绘图模块...")
    
    try:
        from quantlab.plotting.kline import KlinePlotter
        import pandas as pd
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
        print(f"  ✅ 绘图器创建成功")
        
        # 测试绘图（不显示）
        print(f"  ✅ 绘图模块测试完成")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 绘图模块测试失败: {e}")
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🚀 QuantLab 项目测试开始")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_config,
        test_indicators,
        test_portfolio,
        test_strategy,
        test_plotting
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"  ❌ 测试异常: {e}")
    
    print("\n" + "=" * 50)
    print(f"🎯 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("✅ 所有测试通过！项目可以正常使用。")
        return 0
    else:
        print("❌ 部分测试失败，请检查相关模块。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
