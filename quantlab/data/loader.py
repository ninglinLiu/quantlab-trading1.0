"""
数据加载器

负责从 Binance 抓取数据并保存到 CSV 文件，支持增量更新和缓存。
"""

import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict
import logging
from tqdm import tqdm

from .binance_client import BinanceClient
from ..config import get_config

logger = logging.getLogger(__name__)


class DataLoader:
    """数据加载器"""
    
    def __init__(self, data_dir: str = "data/raw"):
        """
        初始化数据加载器
        
        Args:
            data_dir: 数据存储目录
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化 Binance 客户端（不使用全局配置）
        self.client = BinanceClient()
    
    def get_file_path(self, symbol: str, timeframe: str) -> Path:
        """
        获取数据文件路径
        
        Args:
            symbol: 交易对符号
            timeframe: 时间框架
            
        Returns:
            Path: 文件路径
        """
        filename = f"{symbol}_{timeframe}.csv"
        return self.data_dir / filename
    
    def load_existing_data(self, symbol: str, timeframe: str) -> pd.DataFrame:
        """
        加载现有数据
        
        Args:
            symbol: 交易对符号
            timeframe: 时间框架
            
        Returns:
            pd.DataFrame: 现有数据
        """
        file_path = self.get_file_path(symbol, timeframe)
        
        if not file_path.exists():
            return pd.DataFrame()
        
        try:
            df = pd.read_csv(file_path, index_col=0, parse_dates=True)
            df.index = pd.to_datetime(df.index, utc=True)
            
            # 确保数据类型
            for col in ['open', 'high', 'low', 'close', 'volume']:
                if col in df.columns:
                    df[col] = df[col].astype(float)
            
            logger.info(f"Loaded {len(df)} existing records for {symbol} {timeframe}")
            return df
            
        except Exception as e:
            logger.error(f"Error loading existing data: {e}")
            return pd.DataFrame()
    
    def save_data(self, df: pd.DataFrame, symbol: str, timeframe: str) -> None:
        """
        保存数据到 CSV 文件
        
        Args:
            df: 数据 DataFrame
            symbol: 交易对符号
            timeframe: 时间框架
        """
        file_path = self.get_file_path(symbol, timeframe)
        
        try:
            # 确保索引为 UTC 时区
            if df.index.tz is None:
                df.index = df.index.tz_localize('UTC')
            elif df.index.tz != 'UTC':
                df.index = df.index.tz_convert('UTC')
            
            # 保存数据
            df.to_csv(file_path)
            logger.info(f"Saved {len(df)} records to {file_path}")
            
        except Exception as e:
            logger.error(f"Error saving data: {e}")
            raise
    
    def fetch_and_save(
        self,
        symbol: str,
        timeframe: str,
        since: datetime,
        until: datetime,
        force_refresh: bool = False
    ) -> pd.DataFrame:
        """
        抓取并保存数据
        
        Args:
            symbol: 交易对符号
            timeframe: 时间框架
            since: 开始时间
            until: 结束时间
            force_refresh: 是否强制刷新
            
        Returns:
            pd.DataFrame: 完整数据
        """
        logger.info(f"Fetching data for {symbol} {timeframe} from {since} to {until}")
        
        # 加载现有数据
        existing_data = self.load_existing_data(symbol, timeframe)
        
        if not force_refresh and not existing_data.empty:
            # 检查是否需要增量更新
            last_timestamp = existing_data.index[-1]
            
            if last_timestamp >= until:
                logger.info(f"Data already up to date for {symbol} {timeframe}")
                return existing_data
            
            # 从最后一个时间点开始增量更新
            since = last_timestamp + timedelta(milliseconds=1)
            logger.info(f"Incremental update from {since}")
        else:
            logger.info(f"Full refresh for {symbol} {timeframe}")
        
        # 抓取新数据
        try:
            new_data = self.client.fetch_ohlcv_batch(
                symbol=symbol,
                timeframe=timeframe,
                since=since,
                until=until
            )
            
            if new_data.empty:
                logger.warning(f"No new data fetched for {symbol} {timeframe}")
                return existing_data
            
            # 合并数据
            if not existing_data.empty:
                # 合并并去重
                combined_data = pd.concat([existing_data, new_data], ignore_index=False)
                combined_data = combined_data.drop_duplicates()
                combined_data = combined_data.sort_index()
            else:
                combined_data = new_data
            
            # 保存数据
            self.save_data(combined_data, symbol, timeframe)
            
            logger.info(f"Successfully updated {symbol} {timeframe}: {len(combined_data)} total records")
            return combined_data
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol} {timeframe}: {e}")
            raise
    
    def fetch_multiple(
        self,
        symbols: List[str],
        timeframes: List[str],
        since: datetime,
        until: datetime,
        force_refresh: bool = False
    ) -> Dict[str, Dict[str, pd.DataFrame]]:
        """
        批量抓取多个交易对和时间框架的数据
        
        Args:
            symbols: 交易对列表
            timeframes: 时间框架列表
            since: 开始时间
            until: 结束时间
            force_refresh: 是否强制刷新
            
        Returns:
            Dict: 嵌套字典 {symbol: {timeframe: DataFrame}}
        """
        results = {}
        
        # 创建进度条
        total_tasks = len(symbols) * len(timeframes)
        pbar = tqdm(total=total_tasks, desc="Fetching data")
        
        try:
            for symbol in symbols:
                results[symbol] = {}
                
                for timeframe in timeframes:
                    try:
                        data = self.fetch_and_save(
                            symbol=symbol,
                            timeframe=timeframe,
                            since=since,
                            until=until,
                            force_refresh=force_refresh
                        )
                        results[symbol][timeframe] = data
                        
                    except Exception as e:
                        logger.error(f"Failed to fetch {symbol} {timeframe}: {e}")
                        results[symbol][timeframe] = pd.DataFrame()
                    
                    pbar.update(1)
            
            pbar.close()
            logger.info("Batch fetch completed")
            return results
            
        except Exception as e:
            pbar.close()
            logger.error(f"Batch fetch failed: {e}")
            raise
    
    def get_data_info(self, symbol: str, timeframe: str) -> Dict:
        """
        获取数据信息
        
        Args:
            symbol: 交易对符号
            timeframe: 时间框架
            
        Returns:
            Dict: 数据信息
        """
        file_path = self.get_file_path(symbol, timeframe)
        
        if not file_path.exists():
            return {
                'exists': False,
                'file_path': str(file_path),
                'records': 0,
                'start_time': None,
                'end_time': None,
                'file_size': 0
            }
        
        try:
            df = self.load_existing_data(symbol, timeframe)
            
            return {
                'exists': True,
                'file_path': str(file_path),
                'records': len(df),
                'start_time': df.index[0] if not df.empty else None,
                'end_time': df.index[-1] if not df.empty else None,
                'file_size': file_path.stat().st_size
            }
            
        except Exception as e:
            logger.error(f"Error getting data info: {e}")
            return {
                'exists': False,
                'file_path': str(file_path),
                'records': 0,
                'start_time': None,
                'end_time': None,
                'file_size': 0,
                'error': str(e)
            }


if __name__ == "__main__":
    # 测试数据加载器
    loader = DataLoader()
    
    # 测试连接
    if loader.client.test_connection():
        print("Connection test passed!")
        
        # 测试数据抓取
        since = datetime(2024, 1, 1)
        until = datetime(2024, 1, 2)
        
        data = loader.fetch_and_save(
            symbol="BTCUSDT",
            timeframe="1h",
            since=since,
            until=until
        )
        
        print(f"Fetched {len(data)} records")
        print(data.head())
        
        # 测试数据信息
        info = loader.get_data_info("BTCUSDT", "1h")
        print(f"Data info: {info}")
    else:
        print("Connection test failed!")
