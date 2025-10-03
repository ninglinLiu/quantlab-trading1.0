#!/bin/bash

# QuantLab 一键启动脚本 (Linux/Mac)

echo "================================================"
echo "🚀 QuantLab - 量化交易实验室"
echo "================================================"
echo "📊 一键启动完整流程"
echo "================================================"
echo

# 检查Python环境
echo "🔍 检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3未安装"
    echo "请先安装Python 3.8+"
    exit 1
fi

echo "✅ Python环境正常"

# 安装依赖
echo
echo "📦 安装依赖包..."
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ 依赖安装失败"
    exit 1
fi

echo "✅ 依赖安装完成"

# 运行快速启动
echo
echo "🚀 开始快速启动..."
python3 quickstart.py
if [ $? -ne 0 ]; then
    echo "❌ 快速启动失败"
    exit 1
fi

echo
echo "🎉 完成！"
