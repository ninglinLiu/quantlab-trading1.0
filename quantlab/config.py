"""
配置管理模块

统一管理项目配置，支持 YAML 文件和环境变量。
"""

import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import yaml


class TradingConfig(BaseModel):
    """交易配置"""
    fee: float = Field(default=0.0008, description="单边手续费率")
    slippage: float = Field(default=0.0005, description="滑点率")
    leverage: int = Field(default=10, description="杠杆倍数")
    equity: float = Field(default=5000.0, description="起始资金(USDT)")
    mmr: float = Field(default=0.005, description="维持保证金率")
    take_profit: float = Field(default=0.25, description="止盈比例(杠杆后)")
    stop_loss: float = Field(default=0.05, description="止损比例(杠杆后)")


class StrategyConfig(BaseModel):
    """策略配置"""
    cluster_pct: float = Field(default=0.01, description="均线簇密集阈值")
    retest_confirmation: bool = Field(default=False, description="是否启用回踩确认")
    macd_fast: int = Field(default=12, description="MACD快线周期")
    macd_slow: int = Field(default=26, description="MACD慢线周期")
    macd_signal: int = Field(default=9, description="MACD信号线周期")
    ma_periods: List[int] = Field(default=[20, 60, 120], description="均线周期")


class DataConfig(BaseModel):
    """数据配置"""
    exchange: str = Field(default="binance", description="交易所")
    symbols: List[str] = Field(default=["BTCUSDT", "ETHUSDT"], description="交易对列表")
    timeframes: List[str] = Field(default=["1h", "4h", "1d", "1w"], description="时间框架")
    since: str = Field(default="2023-01-01", description="开始日期")
    until: str = Field(default="2025-10-01", description="结束日期")
    data_dir: str = Field(default="data/raw", description="数据目录")
    plots_dir: str = Field(default="plots", description="图表目录")
    reports_dir: str = Field(default="reports", description="报告目录")


class Config(BaseModel):
    """主配置类"""
    trading: TradingConfig = Field(default_factory=TradingConfig)
    strategy: StrategyConfig = Field(default_factory=StrategyConfig)
    data: DataConfig = Field(default_factory=DataConfig)
    
    # API 配置
    api_key: Optional[str] = Field(default=None, description="API密钥")
    secret_key: Optional[str] = Field(default=None, description="密钥")
    
    class Config:
        env_prefix = "QUANTLAB_"


def load_config(config_path: Optional[str] = None) -> Config:
    """
    加载配置
    
    Args:
        config_path: 配置文件路径，默认为 config.yaml
        
    Returns:
        Config: 配置对象
    """
    if config_path is None:
        config_path = "config.yaml"
    
    config_data = {}
    
    # 从 YAML 文件加载
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f) or {}
    
    # 从环境变量加载
    env_config = {}
    for key, value in os.environ.items():
        if key.startswith("QUANTLAB_"):
            config_key = key[9:].lower()  # 移除 QUANTLAB_ 前缀
            env_config[config_key] = value
    
    # 合并配置
    if env_config:
        config_data.update(env_config)
    
    return Config(**config_data)


def save_config(config: Config, config_path: str = "config.yaml") -> None:
    """
    保存配置到文件
    
    Args:
        config: 配置对象
        config_path: 配置文件路径
    """
    config_dict = config.dict()
    
    # 确保目录存在
    Path(config_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)


def create_default_config() -> Config:
    """创建默认配置"""
    return Config()


# 全局配置实例
_config: Optional[Config] = None


def get_config() -> Config:
    """获取全局配置实例"""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def set_config(config: Config) -> None:
    """设置全局配置实例"""
    global _config
    _config = config


# 创建必要的目录
def ensure_directories(config: Config) -> None:
    """确保必要的目录存在"""
    directories = [
        config.data.data_dir,
        config.data.plots_dir,
        config.data.reports_dir,
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    # 创建默认配置文件
    config = create_default_config()
    save_config(config)
    print("Default config.yaml created successfully!")
