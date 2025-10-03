@echo off
chcp 65001 >nul
echo ================================================
echo 🚀 QuantLab - 量化交易实验室
echo ================================================
echo 📊 一键启动完整流程
echo ================================================
echo.

echo 🔍 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python未安装或未添加到PATH
    echo 请先安装Python 3.8+
    pause
    exit /b 1
)

echo ✅ Python环境正常

echo.
echo 📦 安装依赖包...
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ 依赖安装失败
    pause
    exit /b 1
)

echo ✅ 依赖安装完成

echo.
echo 🚀 开始快速启动...
python quickstart.py
if errorlevel 1 (
    echo ❌ 快速启动失败
    pause
    exit /b 1
)

echo.
echo 🎉 完成！按任意键退出...
pause >nul
