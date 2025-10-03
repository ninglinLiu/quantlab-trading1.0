# QuantLab - 量化交易实验室 Makefile

.PHONY: install fetch plot backtest quickstart clean test help

# 默认目标
all: install quickstart

# 安装依赖
install:
	@echo "🚀 Installing QuantLab dependencies..."
	pip install -r requirements.txt
	@echo "✅ Installation completed!"

# 抓取示例数据
fetch:
	@echo "📊 Fetching sample data from Binance..."
	python scripts/fetch_to_csv.py --symbols BTCUSDT ETHUSDT --timeframes 1h 4h 1d 1w --since 2023-01-01 --until 2025-10-01
	@echo "✅ Data fetch completed!"

# 绘制示例图表
plot:
	@echo "📈 Generating sample charts..."
	python scripts/plot_kline.py --symbol BTCUSDT --timeframe 4h --window 500
	python scripts/plot_kline.py --symbol ETHUSDT --timeframe 4h --window 500
	@echo "✅ Charts generated!"

# 运行示例回测
backtest:
	@echo "🎯 Running sample backtest..."
	python scripts/run_backtest.py --symbol BTCUSDT --timeframe 4h --equity 5000 --leverage 10 --fee 0.0008 --slippage 0.0005 --cluster_pct 0.01 --retest False
	@echo "✅ Backtest completed!"

# 快速启动 - 一键运行完整流程
quickstart: fetch plot backtest
	@echo ""
	@echo "🎉 QuantLab Quick Start Completed!"
	@echo "=================================="
	@echo "📁 Check the following directories:"
	@echo "   📊 Data:     data/raw/"
	@echo "   📈 Charts:   plots/"
	@echo "   📋 Reports:  reports/"
	@echo ""
	@echo "🚀 Next steps:"
	@echo "   1. Open notebooks/demo.ipynb for interactive demo"
	@echo "   2. Run 'make test' to verify all modules"
	@echo "   3. Modify config.yaml to customize parameters"
	@echo ""

# 运行项目测试
test:
	@echo "🧪 Running project tests..."
	python test_project.py
	@echo "✅ Tests completed!"

# 清理生成的文件
clean:
	@echo "🧹 Cleaning generated files..."
	rm -rf data/raw/*.csv
	rm -rf plots/*.png
	rm -rf reports/*/
	@echo "✅ Cleanup completed!"

# 创建必要的目录
setup-dirs:
	@echo "📁 Creating project directories..."
	mkdir -p data/raw
	mkdir -p plots
	mkdir -p reports
	mkdir -p notebooks
	@echo "✅ Directories created!"

# 完整安装和设置
setup: setup-dirs install
	@echo "🎯 QuantLab setup completed!"
	@echo "Run 'make quickstart' to start trading!"

# 开发模式安装
dev-install:
	@echo "🔧 Installing development dependencies..."
	pip install -r requirements.txt
	pip install pytest black flake8 mypy
	@echo "✅ Development environment ready!"

# 代码格式化
format:
	@echo "🎨 Formatting code..."
	black quantlab/ scripts/ --line-length 88
	@echo "✅ Code formatted!"

# 代码检查
lint:
	@echo "🔍 Running code checks..."
	flake8 quantlab/ scripts/ --max-line-length 88
	mypy quantlab/ --ignore-missing-imports
	@echo "✅ Code checks completed!"

# 运行 Jupyter notebook
notebook:
	@echo "📓 Starting Jupyter notebook..."
	jupyter notebook notebooks/demo.ipynb

# 帮助信息
help:
	@echo "QuantLab - 量化交易实验室"
	@echo "=========================="
	@echo ""
	@echo "Available commands:"
	@echo "  make install     - Install dependencies"
	@echo "  make fetch       - Fetch sample data from Binance"
	@echo "  make plot        - Generate sample charts"
	@echo "  make backtest    - Run sample strategy backtest"
	@echo "  make quickstart  - Run complete demo (fetch + plot + backtest)"
	@echo "  make test        - Run project tests"
	@echo "  make clean       - Clean generated files"
	@echo "  make setup       - Complete setup (dirs + install)"
	@echo "  make dev-install - Install development dependencies"
	@echo "  make format      - Format code with Black"
	@echo "  make lint        - Run code quality checks"
	@echo "  make notebook    - Start Jupyter notebook"
	@echo "  make help        - Show this help message"
	@echo ""
	@echo "Quick start:"
	@echo "  1. pip install -r requirements.txt"
	@echo "  2. make quickstart"
	@echo ""