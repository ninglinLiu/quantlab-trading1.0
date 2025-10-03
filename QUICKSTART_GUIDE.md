# 🚀 QuantLab 一键启动指南

## 📋 前置要求

- Python 3.8+ 
- pip 包管理器
- 网络连接（用于下载数据和依赖）

## ⚡ 超快速启动（30秒）

### Windows用户
```bash
# 1. 双击运行
quickstart.bat

# 2. 等待完成，查看结果
```

### Linux/Mac用户
```bash
# 1. 添加执行权限
chmod +x quickstart.sh

# 2. 运行脚本
./quickstart.sh

# 3. 等待完成，查看结果
```

### 通用方法（推荐）
```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 一键启动
make quickstart

# 3. 查看结果
```

## 🎯 启动后你会得到什么

### 📊 数据文件 (`data/raw/`)
- BTCUSDT_1h.csv - BTC 1小时K线数据
- BTCUSDT_4h.csv - BTC 4小时K线数据  
- BTCUSDT_1d.csv - BTC 日K线数据
- BTCUSDT_1w.csv - BTC 周K线数据
- ETHUSDT_1h.csv - ETH 1小时K线数据
- ETHUSDT_4h.csv - ETH 4小时K线数据
- ETHUSDT_1d.csv - ETH 日K线数据
- ETHUSDT_1w.csv - ETH 周K线数据

### 📈 图表文件 (`plots/`)
- BTCUSDT_4h_kline.png - BTC 4小时K线图+技术指标
- ETHUSDT_4h_kline.png - ETH 4小时K线图+技术指标
- BTCUSDT_4h_backtest.png - BTC 回测结果图

### 📋 回测报告 (`reports/BTCUSDT_4h/`)
- metrics.json - 详细绩效指标
- trades.csv - 完整交易记录
- equity_curve.png - 资金曲线图
- trade_analysis.png - 交易分析图

## 🔍 查看结果

### 1. 查看回测报告
```bash
# 打开报告目录
open reports/BTCUSDT_4h/  # Mac
explorer reports\BTCUSDT_4h\  # Windows
```

### 2. 运行交互式演示
```bash
# 启动Jupyter
make notebook
# 或
jupyter notebook notebooks/demo.ipynb
```

### 3. 运行项目测试
```bash
# 验证所有功能
make test
# 或
python test_project.py
```

## 🛠️ 自定义配置

### 修改交易参数
编辑 `config.yaml`：
```yaml
trading:
  fee: 0.0008        # 手续费率
  slippage: 0.0005   # 滑点率
  leverage: 10       # 杠杆倍数
  equity: 5000.0     # 起始资金
```

### 修改策略参数
```yaml
strategy:
  cluster_pct: 0.01      # 均线簇阈值
  retest_confirmation: false  # 回踩确认
  macd_fast: 12         # MACD快线
  macd_slow: 26         # MACD慢线
  macd_signal: 9        # MACD信号线
```

### 修改交易对
```yaml
data:
  symbols: [BTCUSDT, ETHUSDT, SOLUSDT]  # 添加更多币种
  timeframes: [1h, 4h, 1d, 1w]         # 时间框架
```

## 🎮 常用命令

```bash
# 完整流程
make quickstart

# 单独步骤
make fetch      # 只抓取数据
make plot       # 只生成图表
make backtest   # 只运行回测

# 维护命令
make clean      # 清理生成文件
make test       # 运行测试
make help       # 查看帮助

# 开发命令
make format     # 代码格式化
make lint       # 代码检查
make dev-install # 开发环境
```

## 🚨 故障排除

### 1. 依赖安装失败
```bash
# 升级pip
pip install --upgrade pip

# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

### 2. 网络连接问题
```bash
# 检查网络
ping binance.com

# 使用代理（如果需要）
pip install -r requirements.txt --proxy http://proxy:port
```

### 3. 权限问题（Linux/Mac）
```bash
# 添加执行权限
chmod +x quickstart.sh
chmod +x scripts/*.py
```

### 4. Python版本问题
```bash
# 检查版本
python --version

# 使用python3
python3 quickstart.py
```

## 📚 深入学习

### 1. 阅读文档
- `README.md` - 详细使用说明
- `PROJECT_SUMMARY.md` - 项目总结
- `PROJECT_STRUCTURE.md` - 项目结构

### 2. 运行示例
- `notebooks/demo.ipynb` - 交互式演示
- `test_project.py` - 功能测试

### 3. 修改代码
- 查看 `quantlab/` 目录下的源码
- 修改策略参数和逻辑
- 添加新的技术指标

## 🎉 恭喜！

你已经成功运行了 QuantLab 量化交易实验室！

现在你可以：
- 📊 分析回测结果
- 🎯 优化策略参数  
- 📈 添加新的技术指标
- 🚀 开发自己的交易策略

开始你的量化交易之旅吧！🚀

