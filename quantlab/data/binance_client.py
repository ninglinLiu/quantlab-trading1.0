"""
Binance API 客户端

提供与 Binance 期货交易所的接口，支持数据抓取和速率限制。
"""

import time
import ccxt
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class BinanceClient:
    """Binance 期货客户端"""
    
    def __init__(self, api_key: Optional[str] = None, secret_key: Optional[str] = None):
        """
        初始化 Binance 客户端
        
        Args:
            api_key: API 密钥（可选，公共数据不需要）
            secret_key: 密钥（可选，公共数据不需要）
        """
        self.exchange = ccxt.binanceusdm({
            'apiKey': api_key,
            'secret': secret_key,
            'sandbox': False,
            'enableRateLimit': True,
            'rateLimit': 100,  # 100ms between requests
        })
        
        # 速率限制配置
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms
        
    def _rate_limit(self) -> None:
        """速率限制"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def fetch_ohlcv(
        self, 
        symbol: str, 
        timeframe: str, 
        since: Optional[datetime] = None,
        limit: int = 1000
    ) -> pd.DataFrame:
        """
        获取 OHLCV 数据
        
        Args:
            symbol: 交易对符号
            timeframe: 时间框架
            since: 开始时间
            limit: 数据条数限制
            
        Returns:
            pd.DataFrame: OHLCV 数据
        """
        self._rate_limit()
        
        try:
            # 转换时间格式
            since_timestamp = None
            if since:
                since_timestamp = int(since.timestamp() * 1000)
            
            # 获取数据
            ohlcv = self.exchange.fetch_ohlcv(
                symbol=symbol,
                timeframe=timeframe,
                since=since_timestamp,
                limit=limit
            )
            
            # 转换为 DataFrame
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
            df.set_index('timestamp', inplace=True)
            
            # 确保数据类型
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
            
            logger.info(f"Fetched {len(df)} records for {symbol} {timeframe}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol} {timeframe}: {e}")
            raise
    
    def fetch_ohlcv_batch(
        self,
        symbol: str,
        timeframe: str,
        since: datetime,
        until: datetime,
        batch_size: int = 1000
    ) -> pd.DataFrame:
        """
        批量获取 OHLCV 数据
        
        Args:
            symbol: 交易对符号
            timeframe: 时间框架
            since: 开始时间
            until: 结束时间
            batch_size: 每批数据条数
            
        Returns:
            pd.DataFrame: 完整的 OHLCV 数据
        """
        all_data = []
        current_time = since
        
        # 计算时间间隔（毫秒）
        timeframe_ms = self._get_timeframe_ms(timeframe)
        batch_ms = batch_size * timeframe_ms
        
        while current_time < until:
            try:
                # 计算批次结束时间
                batch_end = min(
                    current_time + timedelta(milliseconds=batch_ms),
                    until
                )
                
                # 获取批次数据
                batch_data = self.fetch_ohlcv(
                    symbol=symbol,
                    timeframe=timeframe,
                    since=current_time,
                    limit=batch_size
                )
                
                if batch_data.empty:
                    break
                
                all_data.append(batch_data)
                
                # 更新当前时间
                current_time = batch_data.index[-1] + timedelta(milliseconds=timeframe_ms)
                
                # 避免重复数据
                if current_time >= until:
                    break
                    
            except Exception as e:
                logger.error(f"Error in batch fetch: {e}")
                break
        
        if not all_data:
            return pd.DataFrame()
        
        # 合并所有数据
        df = pd.concat(all_data, ignore_index=False)
        df = df.drop_duplicates()
        df = df.sort_index()
        
        logger.info(f"Batch fetch completed: {len(df)} records for {symbol} {timeframe}")
        return df
    
    def _get_timeframe_ms(self, timeframe: str) -> int:
        """获取时间框架对应的毫秒数"""
        timeframe_map = {
            '1m': 60 * 1000,
            '5m': 5 * 60 * 1000,
            '15m': 15 * 60 * 1000,
            '30m': 30 * 60 * 1000,
            '1h': 60 * 60 * 1000,
            '4h': 4 * 60 * 60 * 1000,
            '1d': 24 * 60 * 60 * 1000,
            '1w': 7 * 24 * 60 * 60 * 1000,
        }
        return timeframe_map.get(timeframe, 60 * 60 * 1000)  # 默认1小时
    
    def get_server_time(self) -> datetime:
        """获取服务器时间"""
        self._rate_limit()
        try:
            server_time = self.exchange.fetch_time()
            return datetime.fromtimestamp(server_time / 1000, tz=None)
        except Exception as e:
            logger.error(f"Error fetching server time: {e}")
            return datetime.now()
    
    def test_connection(self) -> bool:
        """测试连接"""
        try:
            self.get_server_time()
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False


if __name__ == "__main__":
    # 测试客户端
    client = BinanceClient()
    
    if client.test_connection():
        print("Connection test passed!")
        
        # 测试数据获取
        since = datetime(2024, 1, 1)
        until = datetime(2024, 1, 2)
        
        data = client.fetch_ohlcv_batch(
            symbol="BTCUSDT",
            timeframe="1h",
            since=since,
            until=until
        )
        
        print(f"Fetched {len(data)} records")
        print(data.head())
    else:
        print("Connection test failed!")
