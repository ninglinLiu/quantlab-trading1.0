# QuantLab 项目结构说明

## 📁 完整项目结构

```
量化交易1.0/
├── 📦 核心包
│   ├── quantlab/                    # 主包目录
│   │   ├── __init__.py             # 包初始化
│   │   ├── config.py               # 配置管理
│   │   ├── data/                   # 数据模块
│   │   │   ├── __init__.py
│   │   │   ├── binance_client.py   # Binance API客户端
│   │   │   └── loader.py           # 数据加载器
│   │   ├── indicators/              # 技术指标模块
│   │   │   ├── __init__.py
│   │   │   ├── ma_ema.py           # 移动平均线
│   │   │   ├── macd.py             # MACD指标
│   │   │   └── cluster.py           # 均线簇
│   │   ├── backtest/               # 回测模块
│   │   │   ├── __init__.py
│   │   │   ├── portfolio.py        # 投资组合管理
│   │   │   ├── engine.py           # 回测引擎
│   │   │   └── metrics.py          # 绩效指标
│   │   ├── plotting/               # 绘图模块
│   │   │   ├── __init__.py
│   │   │   └── kline.py            # K线图
│   │   ├── strategy/               # 策略模块
│   │   │   ├── __init__.py
│   │   │   └── cluster_macd_4h.py  # 均线簇+MACD策略
│   │   └── utils/                  # 工具模块
│   │       ├── __init__.py
│   │       ├── timeframes.py       # 时间框架工具
│   │       └── io.py               # 文件操作工具
│   │
│   ├── scripts/                    # 命令行脚本
│   │   ├── fetch_to_csv.py         # 数据抓取脚本
│   │   ├── plot_kline.py           # K线绘图脚本
│   │   └── run_backtest.py         # 回测脚本
│   │
│   └── notebooks/                  # Jupyter笔记本
│       └── demo.ipynb              # 演示笔记本
│
├── 📋 配置文件
│   ├── requirements.txt            # Python依赖包
│   ├── pyproject.toml              # Poetry配置
│   ├── config.yaml                # 项目配置
│   └── Makefile                   # 构建脚本
│
├── 🚀 启动脚本
│   ├── quickstart.py               # Python快速启动
│   ├── quickstart.bat              # Windows批处理
│   ├── quickstart.sh               # Linux/Mac脚本
│   └── install.py                  # 安装脚本
│
├── 🧪 测试文件
│   └── test_project.py             # 项目测试
│
├── 📚 文档
│   ├── README.md                   # 项目说明
│   └── PROJECT_SUMMARY.md          # 项目总结
│
└── 📊 输出目录（运行后生成）
    ├── data/                       # 数据目录
    │   └── raw/                    # 原始数据
    │       ├── BTCUSDT_1h.csv
    │       ├── BTCUSDT_4h.csv
    │       ├── BTCUSDT_1d.csv
    │       ├── BTCUSDT_1w.csv
    │       ├── ETHUSDT_1h.csv
    │       ├── ETHUSDT_4h.csv
    │       ├── ETHUSDT_1d.csv
    │       └── ETHUSDT_1w.csv
    │
    ├── plots/                      # 图表目录
    │   ├── BTCUSDT_4h_kline.png
    │   ├── ETHUSDT_4h_kline.png
    │   └── BTCUSDT_4h_backtest.png
    │
    └── reports/                    # 报告目录
        └── BTCUSDT_4h/             # 回测报告
            ├── metrics.json       # 绩效指标
            ├── trades.csv          # 交易记录
            ├── equity_curve.png    # 资金曲线
            └── trade_analysis.png  # 交易分析
```

## 🎯 一键启动流程

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 运行完整流程
```bash
make quickstart
```

### 3. 查看结果
- 📊 数据：`data/raw/` 目录
- 📈 图表：`plots/` 目录  
- 📋 报告：`reports/` 目录

## 🔧 核心功能模块

### 数据模块 (`quantlab/data/`)
- **binance_client.py**：Binance API客户端，支持速率限制
- **loader.py**：数据加载器，支持增量更新和缓存

### 指标模块 (`quantlab/indicators/`)
- **ma_ema.py**：移动平均线计算，支持numba加速
- **macd.py**：MACD指标计算
- **cluster.py**：均线簇检测和突破信号

### 回测模块 (`quantlab/backtest/`)
- **portfolio.py**：投资组合管理，包含保证金、杠杆、手续费、滑点
- **engine.py**：回测引擎，事件驱动架构
- **metrics.py**：绩效指标计算，包含夏普比率、最大回撤等

### 绘图模块 (`quantlab/plotting/`)
- **kline.py**：K线图绘制，支持技术指标叠加

### 策略模块 (`quantlab/strategy/`)
- **cluster_macd_4h.py**：均线簇+MACD确认策略

## 📝 使用说明

### 命令行工具
```bash
# 数据抓取
python scripts/fetch_to_csv.py --symbols BTCUSDT ETHUSDT --timeframes 1h 4h 1d 1w

# 图表绘制
python scripts/plot_kline.py --symbol BTCUSDT --timeframe 4h --window 500

# 策略回测
python scripts/run_backtest.py --symbol BTCUSDT --timeframe 4h --equity 5000 --leverage 10
```

### Makefile命令
```bash
make install      # 安装依赖
make fetch        # 抓取数据
make plot         # 生成图表
make backtest     # 运行回测
make quickstart   # 一键启动
make test         # 运行测试
make clean        # 清理文件
make help         # 查看帮助
```

### 配置参数
- **手续费**：0.08% (0.0008)
- **滑点**：0.05% (0.0005)
- **杠杆**：10倍
- **起始资金**：5000 USDT
- **均线簇阈值**：1% (0.01)
- **维持保证金率**：0.5% (0.005)

## 🚀 快速开始

1. **克隆项目**
2. **安装依赖**：`pip install -r requirements.txt`
3. **一键启动**：`make quickstart`
4. **查看结果**：检查 `data/`、`plots/`、`reports/` 目录

就这么简单！🎉
