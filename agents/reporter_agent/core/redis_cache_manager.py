#!/usr/bin/env python3
"""
Redis快取管理器
為ByteC Network Agent Reporter提供高性能快取機制
"""

import redis
import json
import pickle
import hashlib
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import logging
from dataclasses import asdict
import os

logger = logging.getLogger(__name__)

class RedisCacheManager:
    """Redis快取管理器"""
    
    def __init__(self, 
                 host: str = "localhost", 
                 port: int = 6379,
                 db: int = 0,
                 password: Optional[str] = None,
                 decode_responses: bool = False):
        """
        初始化Redis快取管理器
        
        Args:
            host: Redis服務器地址
            port: Redis端口
            db: Redis數據庫編號
            password: Redis密碼
            decode_responses: 是否自動解碼響應
        """
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.decode_responses = decode_responses
        
        # Redis連接池
        self.redis_client = None
        self.connection_pool = None
        
        # 快取配置
        self.default_ttl = 3600  # 1小時默認過期時間
        self.prefix = "bytec:reporter:"
        
        # 快取統計
        self.cache_hits = 0
        self.cache_misses = 0
        
    def connect(self):
        """建立Redis連接"""
        try:
            # 嘗試從環境變量獲取Redis配置
            redis_host = os.getenv('REDIS_HOST', self.host)
            redis_port = int(os.getenv('REDIS_PORT', self.port))
            redis_password = os.getenv('REDIS_PASSWORD', self.password)
            redis_db = int(os.getenv('REDIS_DB', self.db))
            
            # 創建連接池
            self.connection_pool = redis.ConnectionPool(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                password=redis_password,
                decode_responses=self.decode_responses,
                max_connections=20,
                retry_on_timeout=True
            )
            
            # 創建Redis客戶端
            self.redis_client = redis.Redis(connection_pool=self.connection_pool)
            
            # 測試連接
            self.redis_client.ping()
            logger.info(f"✅ Redis快取連接成功: {redis_host}:{redis_port}/{redis_db}")
            return True
            
        except redis.ConnectionError:
            logger.warning("⚠️ Redis連接失敗，將使用記憶體快取作為備選方案")
            self.redis_client = None
            return False
        except Exception as e:
            logger.error(f"❌ Redis初始化失敗: {e}")
            self.redis_client = None
            return False
    
    def disconnect(self):
        """關閉Redis連接"""
        if self.connection_pool:
            self.connection_pool.disconnect()
            logger.info("✅ Redis連接已關閉")
    
    def _generate_cache_key(self, key_parts: List[str]) -> str:
        """生成快取鍵"""
        # 將所有部分連接並進行哈希以避免鍵過長
        key_string = ":".join(str(part) for part in key_parts)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        return f"{self.prefix}{key_hash}"
    
    def _serialize_data(self, data: Any) -> bytes:
        """序列化數據"""
        try:
            # 使用pickle進行序列化，支持複雜數據結構
            return pickle.dumps(data)
        except Exception as e:
            logger.error(f"❌ 數據序列化失敗: {e}")
            raise
    
    def _deserialize_data(self, data: bytes) -> Any:
        """反序列化數據"""
        try:
            return pickle.loads(data)
        except Exception as e:
            logger.error(f"❌ 數據反序列化失敗: {e}")
            raise
    
    def set_cache(self, key_parts: List[str], data: Any, ttl: Optional[int] = None) -> bool:
        """設置快取"""
        if not self.redis_client:
            return False
        
        try:
            cache_key = self._generate_cache_key(key_parts)
            serialized_data = self._serialize_data(data)
            cache_ttl = ttl or self.default_ttl
            
            # 設置快取數據和過期時間
            result = self.redis_client.setex(cache_key, cache_ttl, serialized_data)
            
            if result:
                logger.debug(f"📝 快取設置成功: {cache_key[:50]}... (TTL: {cache_ttl}s)")
                return True
            else:
                logger.warning(f"⚠️ 快取設置失敗: {cache_key[:50]}...")
                return False
                
        except Exception as e:
            logger.error(f"❌ 設置快取失敗: {e}")
            return False
    
    def get_cache(self, key_parts: List[str]) -> Optional[Any]:
        """獲取快取"""
        if not self.redis_client:
            self.cache_misses += 1
            return None
        
        try:
            cache_key = self._generate_cache_key(key_parts)
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                self.cache_hits += 1
                data = self._deserialize_data(cached_data)
                logger.debug(f"🎯 快取命中: {cache_key[:50]}...")
                return data
            else:
                self.cache_misses += 1
                logger.debug(f"❌ 快取未命中: {cache_key[:50]}...")
                return None
                
        except Exception as e:
            logger.error(f"❌ 獲取快取失敗: {e}")
            self.cache_misses += 1
            return None
    
    def delete_cache(self, key_parts: List[str]) -> bool:
        """刪除快取"""
        if not self.redis_client:
            return False
        
        try:
            cache_key = self._generate_cache_key(key_parts)
            result = self.redis_client.delete(cache_key)
            
            if result:
                logger.debug(f"🗑️ 快取刪除成功: {cache_key[:50]}...")
                return True
            else:
                logger.debug(f"⚠️ 快取不存在或刪除失敗: {cache_key[:50]}...")
                return False
                
        except Exception as e:
            logger.error(f"❌ 刪除快取失敗: {e}")
            return False
    
    def invalidate_pattern(self, pattern: str) -> int:
        """批量刪除匹配模式的快取"""
        if not self.redis_client:
            return 0
        
        try:
            full_pattern = f"{self.prefix}*{pattern}*"
            keys = self.redis_client.keys(full_pattern)
            
            if keys:
                deleted_count = self.redis_client.delete(*keys)
                logger.info(f"🗑️ 批量刪除快取: {deleted_count} 個鍵")
                return deleted_count
            else:
                logger.debug(f"⚠️ 沒有找到匹配模式的快取: {pattern}")
                return 0
                
        except Exception as e:
            logger.error(f"❌ 批量刪除快取失敗: {e}")
            return 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """獲取快取統計信息"""
        stats = {
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'hit_rate': 0.0,
            'redis_connected': self.redis_client is not None
        }
        
        total_requests = self.cache_hits + self.cache_misses
        if total_requests > 0:
            stats['hit_rate'] = (self.cache_hits / total_requests) * 100
        
        # 如果Redis連接可用，獲取Redis統計信息
        if self.redis_client:
            try:
                redis_info = self.redis_client.info()
                stats.update({
                    'redis_memory_used': redis_info.get('used_memory_human', 'N/A'),
                    'redis_total_commands': redis_info.get('total_commands_processed', 'N/A'),
                    'redis_connected_clients': redis_info.get('connected_clients', 'N/A'),
                    'redis_uptime_days': redis_info.get('uptime_in_days', 'N/A')
                })
            except Exception as e:
                logger.warning(f"⚠️ 獲取Redis統計信息失敗: {e}")
        
        return stats
    
    def clear_all_cache(self) -> bool:
        """清除所有快取"""
        if not self.redis_client:
            return False
        
        try:
            # 只清除帶有我們前綴的鍵
            pattern = f"{self.prefix}*"
            keys = self.redis_client.keys(pattern)
            
            if keys:
                deleted_count = self.redis_client.delete(*keys)
                logger.info(f"🗑️ 清除所有快取: {deleted_count} 個鍵")
                return True
            else:
                logger.info("⚠️ 沒有找到需要清除的快取")
                return True
                
        except Exception as e:
            logger.error(f"❌ 清除快取失敗: {e}")
            return False


class CachedQueryManager:
    """快取查詢管理器 - 專門處理數據庫查詢快取"""
    
    def __init__(self, cache_manager: RedisCacheManager):
        self.cache = cache_manager
        
        # 快取TTL配置（秒）
        self.ttl_config = {
            'conversions': 1800,      # 30分鐘
            'partner_summary': 3600,  # 1小時  
            'mapping': 7200,          # 2小時
            'health_check': 300,      # 5分鐘
            'statistics': 900         # 15分鐘
        }
    
    def cache_conversions_query(self, partner_name: str, start_date: datetime, 
                               end_date: datetime, limit: Optional[int], 
                               conversions: List[Any]) -> bool:
        """快取轉化記錄查詢結果"""
        key_parts = [
            'conversions',
            partner_name or 'ALL',
            start_date.isoformat() if start_date else 'None',
            end_date.isoformat() if end_date else 'None',
            str(limit) if limit else 'None'
        ]
        
        # 將數據對象轉換為可序列化的格式
        serializable_data = []
        for conv in conversions:
            if hasattr(conv, 'to_dict'):
                serializable_data.append(conv.to_dict())
            elif hasattr(conv, '__dict__'):
                serializable_data.append(asdict(conv))
            else:
                serializable_data.append(conv)
        
        return self.cache.set_cache(key_parts, serializable_data, self.ttl_config['conversions'])
    
    def get_cached_conversions_query(self, partner_name: str, start_date: datetime, 
                                    end_date: datetime, limit: Optional[int]) -> Optional[List[Any]]:
        """獲取快取的轉化記錄查詢結果"""
        key_parts = [
            'conversions',
            partner_name or 'ALL',
            start_date.isoformat() if start_date else 'None',
            end_date.isoformat() if end_date else 'None',
            str(limit) if limit else 'None'
        ]
        
        return self.cache.get_cache(key_parts)
    
    def cache_partner_summary(self, partner_name: str, start_date: datetime, 
                             end_date: datetime, summary: List[Any]) -> bool:
        """快取Partner汇总查詢結果"""
        key_parts = [
            'partner_summary',
            partner_name or 'ALL',
            start_date.isoformat() if start_date else 'None',
            end_date.isoformat() if end_date else 'None'
        ]
        
        serializable_data = []
        for item in summary:
            if hasattr(item, 'to_dict'):
                serializable_data.append(item.to_dict())
            elif hasattr(item, '__dict__'):
                serializable_data.append(asdict(item))
            else:
                serializable_data.append(item)
        
        return self.cache.set_cache(key_parts, serializable_data, self.ttl_config['partner_summary'])
    
    def get_cached_partner_summary(self, partner_name: str, start_date: datetime, 
                                  end_date: datetime) -> Optional[List[Any]]:
        """獲取快取的Partner汇总查詢結果"""
        key_parts = [
            'partner_summary',
            partner_name or 'ALL',
            start_date.isoformat() if start_date else 'None',
            end_date.isoformat() if end_date else 'None'
        ]
        
        return self.cache.get_cache(key_parts)
    
    def cache_mapping_data(self, mapping_type: str, mapping_data: Dict[str, Any]) -> bool:
        """快取映射數據"""
        key_parts = ['mapping', mapping_type]
        return self.cache.set_cache(key_parts, mapping_data, self.ttl_config['mapping'])
    
    def get_cached_mapping_data(self, mapping_type: str) -> Optional[Dict[str, Any]]:
        """獲取快取的映射數據"""
        key_parts = ['mapping', mapping_type]
        return self.cache.get_cache(key_parts)
    
    def invalidate_conversions_cache(self, partner_name: Optional[str] = None):
        """失效轉化記錄快取"""
        if partner_name:
            pattern = f"conversions:{partner_name}"
        else:
            pattern = "conversions"
        
        return self.cache.invalidate_pattern(pattern)
    
    def invalidate_partner_cache(self, partner_name: Optional[str] = None):
        """失效Partner快取"""
        if partner_name:
            pattern = f"partner_summary:{partner_name}"
        else:
            pattern = "partner_summary"
        
        return self.cache.invalidate_pattern(pattern)
    
    def invalidate_all_cache(self):
        """失效所有快取"""
        return self.cache.clear_all_cache()


# 單例模式的全局快取管理器
_global_cache_manager = None
_global_query_cache = None

def get_cache_manager() -> RedisCacheManager:
    """獲取全局快取管理器"""
    global _global_cache_manager
    if _global_cache_manager is None:
        _global_cache_manager = RedisCacheManager()
        _global_cache_manager.connect()
    return _global_cache_manager

def get_query_cache() -> CachedQueryManager:
    """獲取全局查詢快取管理器"""
    global _global_query_cache
    if _global_query_cache is None:
        cache_manager = get_cache_manager()
        _global_query_cache = CachedQueryManager(cache_manager)
    return _global_query_cache

def cleanup_cache():
    """清理快取連接"""
    global _global_cache_manager
    if _global_cache_manager:
        _global_cache_manager.disconnect()
        _global_cache_manager = None 