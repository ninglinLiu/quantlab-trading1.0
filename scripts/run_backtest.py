#!/usr/bin/env python3
"""
回测脚本

运行均线簇+MACD策略回测。
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
from datetime import datetime

from quantlab.data.loader import DataLoader
from quantlab.backtest.engine import BacktestEngine
from quantlab.backtest.portfolio import Portfolio
from quantlab.backtest.metrics import PerformanceMetrics
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
@click.option('--equity', '-e', type=float, default=5000.0, 
              help='起始资金')
@click.option('--leverage', '-l', type=int, default=10, 
              help='杠杆倍数')
@click.option('--fee', '-f', type=float, default=0.0008, 
              help='手续费率')
@click.option('--slippage', type=float, default=0.0005, 
              help='滑点率')
@click.option('--cluster-pct', type=float, default=0.01, 
              help='均线簇密集阈值')
@click.option('--retest', is_flag=True, 
              help='启用回踩确认')
@click.option('--data-dir', default='data/raw', 
              help='数据目录')
@click.option('--reports-dir', default='reports', 
              help='报告保存目录')
@click.option('--plots-dir', default='plots', 
              help='图表保存目录')
def run_backtest(symbol, timeframe, equity, leverage, fee, slippage, 
                 cluster_pct, retest, data_dir, reports_dir, plots_dir):
    """
    运行均线簇+MACD策略回测。
    
    示例:
        python scripts/run_backtest.py --symbol BTCUSDT --timeframe 4h --equity 5000 --leverage 10
        python scripts/run_backtest.py --symbol ETHUSDT --cluster-pct 0.02 --retest
    """
    try:
        logger.info(f"Starting backtest:")
        logger.info(f"  Symbol: {symbol}")
        logger.info(f"  Timeframe: {timeframe}")
        logger.info(f"  Equity: {equity}")
        logger.info(f"  Leverage: {leverage}")
        logger.info(f"  Fee: {fee}")
        logger.info(f"  Slippage: {slippage}")
        logger.info(f"  Cluster threshold: {cluster_pct}")
        logger.info(f"  Retest confirmation: {retest}")
        
        # 确保目录存在
        Path(reports_dir).mkdir(parents=True, exist_ok=True)
        Path(plots_dir).mkdir(parents=True, exist_ok=True)
        
        # 创建报告子目录
        report_dir = Path(reports_dir) / f"{symbol}_{timeframe}"
        report_dir.mkdir(parents=True, exist_ok=True)
        
        # 加载数据
        loader = DataLoader(data_dir)
        data = loader.load_existing_data(symbol, timeframe)
        
        if data.empty:
            logger.error(f"No data found for {symbol} {timeframe}")
            logger.info("Please run fetch_to_csv.py first to download data")
            return
        
        logger.info(f"Loaded {len(data)} records for {symbol} {timeframe}")
        
        # 创建投资组合
        portfolio = Portfolio(
            initial_equity=equity,
            leverage=leverage,
            fee_rate=fee,
            slippage_rate=slippage
        )
        
        # 创建回测引擎
        engine = BacktestEngine(data, portfolio)
        
        # 运行回测
        logger.info("Running backtest...")
        results = engine.run_backtest()
        
        # 计算绩效指标
        logger.info("Calculating performance metrics...")
        metrics_calc = PerformanceMetrics(
            results['trades'], 
            results['equity_curve']
        )
        metrics = metrics_calc.calculate_all_metrics()
        
        # 保存结果
        logger.info("Saving results...")
        
        # 保存绩效指标
        metrics_file = report_dir / "metrics.json"
        metrics_calc.save_metrics(str(metrics_file))
        
        # 保存交易记录
        trades_file = report_dir / "trades.csv"
        metrics_calc.save_trades(str(trades_file))
        
        # 绘制权益曲线
        equity_curve_file = report_dir / "equity_curve.png"
        metrics_calc.plot_equity_curve(str(equity_curve_file))
        
        # 绘制交易分析
        trade_analysis_file = report_dir / "trade_analysis.png"
        metrics_calc.plot_trade_analysis(str(trade_analysis_file))
        
        # 绘制K线图
        kline_file = Path(plots_dir) / f"{symbol}_{timeframe}_backtest.png"
        plotter = KlinePlotter()
        plotter.create_summary_plot(
            data=data,
            title=f"{symbol} {timeframe} Backtest Results",
            save_path=str(kline_file),
            window=500
        )
        
        # 显示结果摘要
        logger.info("\n" + "="*60)
        logger.info("BACKTEST RESULTS")
        logger.info("="*60)
        
        logger.info(f"\nBasic Metrics:")
        logger.info(f"  Total trades: {metrics.get('total_trades', 0)}")
        logger.info(f"  Win rate: {metrics.get('win_rate', 0):.2%}")
        logger.info(f"  Profit/Loss ratio: {metrics.get('profit_loss_ratio', 0):.2f}")
        
        logger.info(f"\nReturn Metrics:")
        logger.info(f"  Total return: {metrics.get('total_return', 0):.2%}")
        logger.info(f"  Annualized return: {metrics.get('annualized_return', 0):.2%}")
        logger.info(f"  Sharpe ratio: {metrics.get('sharpe_ratio', 0):.2f}")
        
        logger.info(f"\nRisk Metrics:")
        logger.info(f"  Max drawdown: {metrics.get('max_drawdown', 0):.2%}")
        logger.info(f"  Calmar ratio: {metrics.get('calmar_ratio', 0):.2f}")
        logger.info(f"  Volatility: {metrics.get('volatility', 0):.2%}")
        
        logger.info(f"\nTrade Analysis:")
        logger.info(f"  Avg duration: {metrics.get('avg_duration_hours', 0):.1f} hours")
        logger.info(f"  Expected return: {metrics.get('expected_return', 0):.4f}")
        
        logger.info(f"\nFiles saved:")
        logger.info(f"  Metrics: {metrics_file}")
        logger.info(f"  Trades: {trades_file}")
        logger.info(f"  Equity curve: {equity_curve_file}")
        logger.info(f"  Trade analysis: {trade_analysis_file}")
        logger.info(f"  K-line chart: {kline_file}")
        
        logger.info("\nBacktest completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during backtest: {e}")
        raise


if __name__ == '__main__':
    run_backtest()