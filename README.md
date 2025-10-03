# QuantLab - 量化交易实验室

## 项目简介

QuantLab 是一个专为加密货币期货交易设计的量化交易实验室，提供数据抓取、技术分析、策略回测等完整功能。

## 主要功能

1. **数据抓取**：从 Binance 拉取 OHLCV 数据，支持缓存和增量更新
2. **技术分析**：绘制 K 线图，支持多种技术指标
3. **策略回测**：实现"均线簇 + MACD 确认"策略，支持杠杆交易和风险管理

## 🚀 一键启动

### 方法1：使用Makefile（推荐）
```bash
# 安装依赖
pip install -r requirements.txt

# 一键运行完整流程
make quickstart
```

### 方法2：使用Python脚本
```bash
# 安装依赖
pip install -r requirements.txt

# 运行快速启动
python quickstart.py
```

### 方法3：使用批处理文件（Windows）
```bash
# 双击运行
quickstart.bat
```

### 方法4：使用Shell脚本（Linux/Mac）
```bash
# 添加执行权限并运行
chmod +x quickstart.sh
./quickstart.sh
```

## 📦 安装步骤

### 1. 安装依赖

```bash
# 方法1：使用pip（推荐）
pip install -r requirements.txt

# 方法2：使用Poetry
pip install poetry
poetry install

# 方法3：使用安装脚本
python install.py
```

### 2. 设置环境变量（可选）

创建 `.env` 文件：
```bash
BINANCE_API_KEY=your_api_key
BINANCE_SECRET_KEY=your_secret_key
```

**注意**：公共数据抓取无需 API Key，只有私有数据或高频请求才需要。

## 快速开始

### 1. 抓取数据

```bash
make fetch
# 或
python scripts/fetch_to_csv.py --symbols BTCUSDT ETHUSDT --timeframes 1h 4h 1d 1w --since 2023-01-01 --until 2025-10-01
```

### 2. 绘制 K 线图

```bash
make plot
# 或
python scripts/plot_kline.py --symbol BTCUSDT --timeframe 4h --window 500
```

### 3. 运行回测

```bash
make backtest
# 或
python scripts/run_backtest.py --symbol BTCUSDT --timeframe 4h --equity 5000 --leverage 10 --fee 0.0008 --slippage 0.0005 --cluster_pct 0.01 --retest False
```

## 项目结构

```
quantlab/
├── config.py              # 配置管理
├── data/                  # 数据模块
│   ├── binance_client.py  # Binance API 客户端
│   └── loader.py          # 数据加载器
├── indicators/            # 技术指标
│   ├── ma_ema.py         # 移动平均线
│   ├── macd.py           # MACD 指标
│   └── cluster.py        # 均线簇
├── backtest/             # 回测引擎
│   ├── portfolio.py      # 投资组合管理
│   ├── engine.py         # 回测引擎
│   └── metrics.py        # 绩效指标
├── plotting/             # 绘图模块
│   └── kline.py          # K 线图
├── strategy/             # 交易策略
│   └── cluster_macd_4h.py # 均线簇+MACD策略
└── utils/                # 工具函数
    ├── timeframes.py     # 时间框架
    └── io.py             # 文件操作
```

## 配置参数

### 交易参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| fee | 0.0008 | 单边手续费率 (0.08%) |
| slippage | 0.0005 | 滑点率 (0.05%) |
| leverage | 10 | 杠杆倍数 |
| equity | 5000 | 起始资金 (USDT) |
| cluster_pct | 0.01 | 均线簇密集阈值 (1%) |
| mmr | 0.005 | 维持保证金率 (0.5%) |

### 策略参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| macd_fast | 12 | MACD 快线周期 |
| macd_slow | 26 | MACD 慢线周期 |
| macd_signal | 9 | MACD 信号线周期 |
| ma_periods | [20, 60, 120] | 均线周期 |
| take_profit | 0.25 | 止盈比例 (杠杆后 25%) |
| stop_loss | 0.05 | 止损比例 (杠杆后 5%) |
| retest_confirmation | False | 是否启用回踩确认 |

### 时间框架

支持的时间框架：1h, 4h, 1d, 1w

## 策略说明

### 均线簇 + MACD 确认策略

1. **均线簇识别**：当多条均线（20/60/120）的宽度小于价格的 1% 时，判定为均线簇
2. **突破信号**：价格突破均线簇上沿/下沿
3. **MACD 确认**：
   - 多单：DIF > DEA 且 hist > 0
   - 空单：DIF < DEA 且 hist < 0
4. **风险管理**：
   - 止盈：杠杆后收益率 +25%
   - 止损：杠杆后收益率 -5%
   - 爆仓：权益 <= 名义价值 × 维持保证金率

### 价格计算说明

- **入场价格**：收盘价 + 滑点
- **出场价格**：目标价格 + 滑点
- **爆仓价格**：基于收盘价近似计算

**注意**：本系统使用收盘价近似标记价格，与真实交易存在差异，仅用于策略验证。

## 输出文件

### 数据文件
- `data/raw/{symbol}_{timeframe}.csv`：原始 OHLCV 数据

### 图表文件
- `plots/{symbol}_{timeframe}.png`：K 线图

### 回测报告
- `reports/{symbol}_{timeframe}/metrics.csv`：绩效指标
- `reports/{symbol}_{timeframe}/equity_curve.png`：资金曲线
- `reports/{symbol}_{timeframe}/trades.csv`：交易记录

## 常见问题

### 1. 速率限制

Binance API 有速率限制，系统会自动处理：
- 公共数据：1200 请求/分钟
- 私有数据：600 请求/分钟

### 2. 数据时区

所有数据统一使用 UTC 时区，确保一致性。

### 3. 爆仓逻辑

当前实现为线性近似，实际交易中 Binance 使用分级维持保证金率，可根据需要扩展。

### 4. 滑点计算

滑点基于收盘价计算，实际交易中滑点与市场深度和订单大小相关。

## 开发说明

### 添加新策略

1. 在 `strategy/` 目录创建新策略文件
2. 实现 `generate_signals()` 方法
3. 在回测引擎中注册策略

### 添加新指标

1. 在 `indicators/` 目录添加指标文件
2. 实现指标计算函数
3. 在策略中调用

### 扩展交易所

1. 在 `data/` 目录添加新交易所客户端
2. 实现统一的接口方法
3. 更新配置和文档

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
