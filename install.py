#!/usr/bin/env python3
"""
QuantLab 安装脚本

自动安装依赖并设置项目环境
"""

import subprocess
import sys
import os
from pathlib import Path

def print_banner():
    """打印安装横幅"""
    print("=" * 50)
    print("🚀 QuantLab 安装程序")
    print("=" * 50)
    print("📦 自动安装依赖和设置环境")
    print("=" * 50)
    print()

def check_python_version():
    """检查Python版本"""
    print("🐍 检查Python版本...")
    
    if sys.version_info < (3, 8):
        print(f"❌ Python版本过低: {sys.version}")
        print("需要Python 3.8或更高版本")
        return False
    
    print(f"✅ Python版本: {sys.version}")
    return True

def install_requirements():
    """安装依赖包"""
    print("\n📦 安装依赖包...")
    
    if not Path("requirements.txt").exists():
        print("❌ requirements.txt 文件不存在")
        return False
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 依赖包安装成功")
            return True
        else:
            print(f"❌ 依赖包安装失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 安装异常: {e}")
        return False

def create_directories():
    """创建项目目录"""
    print("\n📁 创建项目目录...")
    
    directories = [
        'data/raw',
        'plots',
        'reports', 
        'notebooks',
        'scripts'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"  ✅ {directory}")
    
    print("✅ 目录创建完成")

def verify_installation():
    """验证安装"""
    print("\n🔍 验证安装...")
    
    required_packages = [
        'pandas', 'numpy', 'matplotlib', 'ccxt',
        'tqdm', 'pydantic', 'click', 'numba'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n❌ 缺少包: {', '.join(missing_packages)}")
        return False
    
    print("✅ 所有依赖验证通过")
    return True

def show_next_steps():
    """显示下一步操作"""
    print("\n" + "=" * 50)
    print("🎉 安装完成!")
    print("=" * 50)
    
    print("\n🚀 快速开始:")
    print("  1. make quickstart    # 一键运行完整流程")
    print("  2. python quickstart.py  # 或使用Python脚本")
    
    print("\n📚 其他命令:")
    print("  make help           # 查看所有命令")
    print("  make test           # 运行测试")
    print("  make notebook       # 启动Jupyter")
    
    print("\n📖 文档:")
    print("  README.md           # 详细使用说明")
    print("  PROJECT_SUMMARY.md  # 项目总结")

def main():
    """主函数"""
    print_banner()
    
    # 检查Python版本
    if not check_python_version():
        sys.exit(1)
    
    # 安装依赖
    if not install_requirements():
        sys.exit(1)
    
    # 创建目录
    create_directories()
    
    # 验证安装
    if not verify_installation():
        print("\n⚠️ 安装验证失败，请检查错误信息")
        sys.exit(1)
    
    # 显示下一步
    show_next_steps()

if __name__ == "__main__":
    main()
