#!/usr/bin/env python3
"""
QuantLab 快速启动脚本

一键运行完整的量化交易流程：数据抓取 → 绘图 → 回测
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def print_banner():
    """打印欢迎横幅"""
    print("=" * 60)
    print("QuantLab - 量化交易实验室")
    print("=" * 60)
    print("自动化量化交易流程")
    print("均线簇 + MACD 策略回测")
    print("=" * 60)
    print()

def check_dependencies():
    """检查依赖是否安装"""
    print("检查依赖...")
    
    required_packages = [
        'pandas', 'numpy', 'matplotlib', 'ccxt', 
        'tqdm', 'pydantic', 'click', 'numba'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"  [OK] {package}")
        except ImportError:
            print(f"  [FAIL] {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n[ERROR] 缺少依赖包: {', '.join(missing_packages)}")
        print("请运行: pip install -r requirements.txt")
        return False
    
    print("[OK] 所有依赖已安装")
    return True

def create_directories():
    """创建必要的目录"""
    print("\n创建项目目录...")
    
    directories = [
        'data/raw',
        'plots', 
        'reports',
        'notebooks'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"  [OK] {directory}")
    
    print("[OK] 目录创建完成")

def run_data_fetch():
    """运行数据抓取"""
    print("\n开始数据抓取...")
    
    try:
        # 先尝试生成模拟数据
        result = subprocess.run([
            sys.executable, 'scripts/generate_mock_data.py',
            '--symbols', 'BTCUSDT',
            '--symbols', 'ETHUSDT',
            '--timeframes', '1h',
            '--timeframes', '4h', 
            '--timeframes', '1d',
            '--timeframes', '1w',
            '--since', '2023-01-01',
            '--until', '2025-10-01'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("[OK] 模拟数据生成成功")
            return True
        else:
            print(f"[ERROR] 模拟数据生成失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"[ERROR] 数据生成异常: {e}")
        return False

def run_plotting():
    """运行图表生成"""
    print("\n开始生成图表...")
    
    symbols = ['BTCUSDT', 'ETHUSDT']
    success_count = 0
    
    for symbol in symbols:
        try:
            result = subprocess.run([
                sys.executable, 'scripts/plot_kline.py',
                '--symbol', symbol,
                '--timeframe', '4h',
                '--window', '500'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"  [OK] {symbol} 图表生成成功")
                success_count += 1
            else:
                print(f"  [ERROR] {symbol} 图表生成失败")
                
        except Exception as e:
            print(f"  [ERROR] {symbol} 图表生成异常: {e}")
    
    if success_count == len(symbols):
        print("[OK] 图表生成完成")
        return True
    else:
        print(f"[WARNING] 部分图表生成失败 ({success_count}/{len(symbols)})")
        return False

def run_backtest():
    """运行回测"""
    print("\n开始策略回测...")
    
    try:
        result = subprocess.run([
            sys.executable, 'scripts/run_backtest.py',
            '--symbol', 'BTCUSDT',
            '--timeframe', '4h',
            '--equity', '5000',
            '--leverage', '10',
            '--fee', '0.0008',
            '--slippage', '0.0005',
            '--cluster-pct', '0.01'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("[OK] 回测完成")
            return True
        else:
            print(f"[ERROR] 回测失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"[ERROR] 回测异常: {e}")
        return False

def show_results():
    """显示结果摘要"""
    print("\n" + "=" * 60)
    print("QuantLab 快速启动完成!")
    print("=" * 60)
    
    # 检查生成的文件
    data_files = list(Path('data/raw').glob('*.csv'))
    plot_files = list(Path('plots').glob('*.png'))
    report_dirs = list(Path('reports').glob('*'))
    
    print(f"\n生成的文件:")
    print(f"  数据文件: {len(data_files)} 个")
    print(f"  图表文件: {len(plot_files)} 个")
    print(f"  报告目录: {len(report_dirs)} 个")
    
    if data_files:
        print(f"\n数据文件:")
        for file in data_files[:5]:  # 显示前5个
            print(f"  [FILE] {file.name}")
    
    if plot_files:
        print(f"\n图表文件:")
        for file in plot_files[:5]:  # 显示前5个
            print(f"  [IMAGE] {file.name}")
    
    if report_dirs:
        print(f"\n报告目录:")
        for dir in report_dirs[:3]:  # 显示前3个
            print(f"  [DIR] {dir.name}")
    
    print(f"\n下一步操作:")
    print(f"  1. 查看回测报告: reports/BTCUSDT_4h/")
    print(f"  2. 运行交互式演示: jupyter notebook notebooks/demo.ipynb")
    print(f"  3. 运行项目测试: python test_project.py")
    print(f"  4. 自定义参数: 编辑 config.yaml")
    
    print(f"\n文档:")
    print(f"  [DOC] README.md - 详细使用说明")
    print(f"  [DOC] PROJECT_SUMMARY.md - 项目总结")
    print(f"  [TEST] test_project.py - 功能测试")

def main():
    """主函数"""
    print_banner()
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 创建目录
    create_directories()
    
    # 运行流程
    steps = [
        ("数据抓取", run_data_fetch),
        ("图表生成", run_plotting), 
        ("策略回测", run_backtest)
    ]
    
    success_count = 0
    
    for step_name, step_func in steps:
        print(f"\n[STEP] 执行步骤: {step_name}")
        if step_func():
            success_count += 1
        else:
            print(f"[WARNING] {step_name} 执行失败，继续下一步...")
    
    # 显示结果
    show_results()
    
    if success_count == len(steps):
        print(f"\n[SUCCESS] 所有步骤执行成功! ({success_count}/{len(steps)})")
        sys.exit(0)
    else:
        print(f"\n[WARNING] 部分步骤执行失败 ({success_count}/{len(steps)})")
        print("请检查错误信息并重试")
        sys.exit(1)

if __name__ == "__main__":
    main()
