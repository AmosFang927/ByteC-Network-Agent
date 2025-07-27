#!/usr/bin/env python3
"""
增強版統一資料庫管理器
Enhanced Unified Database Manager

整合了所有性能優化策略：
- 統一連接池管理
- 智能緩存策略
- 查詢優化
- 批量處理
- 連接池監控
"""

import os
import asyncio
import asyncpg
import redis.asyncio as redis
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timedelta
import logging
import hashlib
import json
import time
from decimal import Decimal
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager
import weakref

logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    """資料庫配置"""
    host: str = "34.124.206.16"
    port: int = 5432
    database: str = "postback_db"
    user: str = "postback_admin"
    password: str = "ByteC2024PostBack_CloudSQL"
    
    # 連接池配置 - 優化後的設置
    min_size: int = 5  # 提高最小連接數
    max_size: int = 20  # 提高最大連接數
    command_timeout: int = 120
    connection_timeout: int = 10
    
    # 緩存配置
    enable_cache: bool = True
    cache_ttl: int = 300  # 5分鐘
    redis_url: str = "redis://localhost:6379/1"
    
    # 性能配置
    batch_size: int = 1000  # 批量處理大小
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # 監控配置
    enable_monitoring: bool = True
    slow_query_threshold: float = 1.0  # 慢查詢閾值（秒）

@dataclass 
class QueryMetrics:
    """查詢指標"""
    query_count: int = 0
    total_time: float = 0.0
    avg_time: float = 0.0
    slow_queries: int = 0
    cache_hits: int = 0
    cache_misses: int = 0

class ConnectionPoolMonitor:
    """連接池監控器"""
    
    def __init__(self):
        self.metrics = {
            'active_connections': 0,
            'total_queries': 0,
            'failed_queries': 0,
            'avg_query_time': 0.0,
            'pool_exhausted_count': 0
        }
        
    def record_query(self, duration: float, success: bool = True):
        """記錄查詢指標"""
        self.metrics['total_queries'] += 1
        if not success:
            self.metrics['failed_queries'] += 1
        
        # 更新平均查詢時間
        total_time = self.metrics['avg_query_time'] * (self.metrics['total_queries'] - 1)
        self.metrics['avg_query_time'] = (total_time + duration) / self.metrics['total_queries']
        
    def get_status(self) -> Dict[str, Any]:
        """獲取連接池狀態"""
        return self.metrics.copy()

class SmartCache:
    """智能緩存管理器"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None, ttl: int = 300):
        self.redis_client = redis_client
        self.ttl = ttl
        self.local_cache = {}  # 備用本地緩存
        self.cache_stats = {'hits': 0, 'misses': 0, 'sets': 0, 'errors': 0}
        
    def _generate_key(self, query: str, params: List[Any]) -> str:
        """生成緩存鍵"""
        content = f"{query}:{str(params)}"
        return f"db_cache:{hashlib.md5(content.encode()).hexdigest()}"
        
    async def get(self, query: str, params: List[Any]) -> Optional[List[Dict]]:
        """獲取緩存"""
        try:
            key = self._generate_key(query, params)
            
            if self.redis_client:
                cached = await self.redis_client.get(key)
                if cached:
                    self.cache_stats['hits'] += 1
                    return json.loads(cached)
            
            # 備用本地緩存
            if key in self.local_cache:
                data, timestamp = self.local_cache[key]
                if time.time() - timestamp < self.ttl:
                    self.cache_stats['hits'] += 1
                    return data
                else:
                    del self.local_cache[key]
                    
            self.cache_stats['misses'] += 1
            return None
            
        except Exception as e:
            logger.warning(f"緩存讀取失敗: {e}")
            self.cache_stats['errors'] += 1
            return None
    
    async def set(self, query: str, params: List[Any], data: List[Dict]):
        """設置緩存"""
        try:
            key = self._generate_key(query, params)
            serialized = json.dumps(data, default=str)
            
            if self.redis_client:
                await self.redis_client.setex(key, self.ttl, serialized)
            
            # 備用本地緩存（限制大小）
            if len(self.local_cache) < 1000:
                self.local_cache[key] = (data, time.time())
            
            self.cache_stats['sets'] += 1
            
        except Exception as e:
            logger.warning(f"緩存設置失敗: {e}")
            self.cache_stats['errors'] += 1
    
    def get_stats(self) -> Dict[str, int]:
        """獲取緩存統計"""
        total = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = (self.cache_stats['hits'] / total * 100) if total > 0 else 0
        return {**self.cache_stats, 'hit_rate': round(hit_rate, 2)}

class EnhancedDatabaseManager:
    """增強版資料庫管理器"""
    
    _instances = weakref.WeakValueDictionary()
    
    def __new__(cls, config: Optional[DatabaseConfig] = None):
        """單例模式確保同一配置只創建一個實例"""
        if config is None:
            config = DatabaseConfig()
        
        key = f"{config.host}:{config.port}:{config.database}"
        if key in cls._instances:
            return cls._instances[key]
            
        instance = super().__new__(cls)
        cls._instances[key] = instance
        return instance
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        if hasattr(self, '_initialized'):
            return
            
        self.config = config or DatabaseConfig()
        self.pool: Optional[asyncpg.Pool] = None
        self.redis_client: Optional[redis.Redis] = None
        self.cache: Optional[SmartCache] = None
        self.monitor = ConnectionPoolMonitor()
        self.query_metrics: Dict[str, QueryMetrics] = {}
        self._initialized = True
        
        # 準備語句緩存
        self.prepared_statements = {}
        
    async def initialize(self):
        """初始化資料庫管理器"""
        try:
            # 初始化連接池
            await self._init_connection_pool()
            
            # 初始化Redis緩存
            if self.config.enable_cache:
                await self._init_cache()
            
            # 創建必要的索引
            await self._ensure_indexes()
            
            logger.info("✅ 增強版資料庫管理器初始化完成")
            
        except Exception as e:
            logger.error(f"❌ 資料庫管理器初始化失敗: {e}")
            raise
    
    async def _init_connection_pool(self):
        """初始化連接池"""
        try:
            connection_string = (
                f"postgresql://{self.config.user}:{self.config.password}@"
                f"{self.config.host}:{self.config.port}/{self.config.database}"
            )
            
            self.pool = await asyncpg.create_pool(
                connection_string,
                min_size=self.config.min_size,
                max_size=self.config.max_size,
                command_timeout=self.config.command_timeout
                # 移除可能需要服務器重啟的設置以避免配置問題
            )
            
            logger.info(f"✅ 連接池初始化成功: min={self.config.min_size}, max={self.config.max_size}")
            
        except Exception as e:
            logger.error(f"❌ 連接池初始化失敗: {e}")
            raise
    
    async def _init_cache(self):
        """初始化緩存"""
        try:
            self.redis_client = redis.from_url(
                self.config.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # 測試連接
            await self.redis_client.ping()
            self.cache = SmartCache(self.redis_client, self.config.cache_ttl)
            
            logger.info("✅ Redis緩存初始化成功")
            
        except Exception as e:
            logger.warning(f"⚠️ Redis連接失敗，使用本地緩存: {e}")
            self.cache = SmartCache(None, self.config.cache_ttl)
    
    async def _ensure_indexes(self):
        """確保關鍵索引存在"""
        indexes = [
            # 基本索引 - 最常用的查詢
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversions_partner ON conversions(partner) WHERE partner IS NOT NULL",
            
            # 日期索引 - 用於時間範圍查詢
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversions_datetime ON conversions(datetime_conversion) WHERE datetime_conversion IS NOT NULL",
            
            # 複合索引 - 優化常見查詢組合  
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversions_partner_datetime ON conversions(partner, datetime_conversion) WHERE datetime_conversion IS NOT NULL AND partner IS NOT NULL",
            
            # 金額索引 - 用於收入統計
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversions_amount ON conversions(usd_sale_amount) WHERE usd_sale_amount IS NOT NULL",
            
            # ID 索引 - 用於快速查找
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversions_conversion_id ON conversions(conversion_id) WHERE conversion_id IS NOT NULL",
        ]
        
        try:
            async with self.pool.acquire() as conn:
                for index_sql in indexes:
                    try:
                        await conn.execute(index_sql)
                        logger.debug(f"✅ 索引創建成功: {index_sql[:50]}...")
                    except Exception as e:
                        if "already exists" not in str(e):
                            logger.warning(f"⚠️ 索引創建失敗: {index_sql[:50]}... - {e}")
                            
        except Exception as e:
            logger.error(f"❌ 索引創建過程失敗: {e}")
    
    @asynccontextmanager
    async def get_connection(self):
        """獲取資料庫連接的上下文管理器"""
        if not self.pool:
            await self.initialize()
            
        start_time = time.time()
        conn = None
        try:
            conn = await self.pool.acquire()
            self.monitor.metrics['active_connections'] += 1
            yield conn
            
        except Exception as e:
            duration = time.time() - start_time
            self.monitor.record_query(duration, False)
            logger.error(f"❌ 資料庫連接錯誤: {e}")
            raise
            
        finally:
            if conn:
                try:
                    await self.pool.release(conn)
                    self.monitor.metrics['active_connections'] -= 1
                except Exception as e:
                    logger.error(f"❌ 連接釋放失敗: {e}")
    
    async def execute_query(self, query: str, params: List[Any] = None, 
                          use_cache: bool = True, cache_ttl: Optional[int] = None) -> List[Dict]:
        """執行查詢 - 帶緩存和性能監控"""
        params = params or []
        query_hash = hashlib.md5(f"{query}:{str(params)}".encode()).hexdigest()[:8]
        
        start_time = time.time()
        
        try:
            # 嘗試從緩存獲取
            if use_cache and self.cache:
                cached_result = await self.cache.get(query, params)
                if cached_result is not None:
                    duration = time.time() - start_time
                    logger.debug(f"🎯 緩存命中 [{query_hash}]: {duration:.3f}s")
                    return cached_result
            
            # 執行查詢
            async with self.get_connection() as conn:
                rows = await conn.fetch(query, *params)
                result = [dict(row) for row in rows]
                
                duration = time.time() - start_time
                
                # 記錄指標
                self.monitor.record_query(duration, True)
                self._update_query_metrics(query_hash, duration)
                
                # 緩存結果
                if use_cache and self.cache and len(result) > 0:
                    ttl = cache_ttl or self.config.cache_ttl
                    await self.cache.set(query, params, result)
                
                # 慢查詢告警
                if duration > self.config.slow_query_threshold:
                    logger.warning(f"🐌 慢查詢 [{query_hash}]: {duration:.3f}s - {query[:100]}...")
                
                logger.debug(f"✅ 查詢完成 [{query_hash}]: {duration:.3f}s, {len(result)} 條記錄")
                return result
                
        except Exception as e:
            duration = time.time() - start_time
            self.monitor.record_query(duration, False)
            logger.error(f"❌ 查詢失敗 [{query_hash}]: {duration:.3f}s - {e}")
            raise
    
    async def execute_batch_query(self, queries: List[Tuple[str, List[Any]]], 
                                use_cache: bool = True) -> List[List[Dict]]:
        """批量執行查詢"""
        results = []
        
        async with self.get_connection() as conn:
            for query, params in queries:
                result = await self.execute_query(query, params, use_cache)
                results.append(result)
                
        return results
    
    def _update_query_metrics(self, query_hash: str, duration: float):
        """更新查詢指標"""
        if query_hash not in self.query_metrics:
            self.query_metrics[query_hash] = QueryMetrics()
            
        metrics = self.query_metrics[query_hash]
        metrics.query_count += 1
        metrics.total_time += duration
        metrics.avg_time = metrics.total_time / metrics.query_count
        
        if duration > self.config.slow_query_threshold:
            metrics.slow_queries += 1
    
    async def get_conversions_optimized(self, partner: Optional[str] = None,
                                      start_date: Optional[datetime] = None,
                                      end_date: Optional[datetime] = None,
                                      limit: Optional[int] = None,
                                      use_cache: bool = True) -> List[Dict]:
        """優化版轉化數據查詢"""
        
        # 構建優化查詢 - 使用覆蓋索引
        query = """
        SELECT 
            c.id,
            c.conversion_id,
            c.partner,
            c.datetime_conversion,
            c.usd_sale_amount,
            c.offer_id,
            c.offer_name,
            c.aff_sub
        FROM conversions c
        WHERE 1=1
        """
        
        params = []
        param_count = 0
        
        # 添加過濾條件
        if partner and partner.upper() != 'ALL':
            param_count += 1
            query += f" AND c.partner = ${param_count}"
            params.append(partner)
        
        if start_date:
            param_count += 1
            query += f" AND DATE(c.datetime_conversion) >= ${param_count}"
            params.append(start_date.date())
        
        if end_date:
            param_count += 1
            query += f" AND DATE(c.datetime_conversion) <= ${param_count}"
            params.append(end_date.date())
        
        # 添加排序和限制
        query += " ORDER BY c.datetime_conversion DESC"
        
        if limit:
            param_count += 1
            query += f" LIMIT ${param_count}"
            params.append(limit)
        
        return await self.execute_query(query, params, use_cache)
    
    async def get_partner_summary_optimized(self, partner: Optional[str] = None,
                                          start_date: Optional[datetime] = None,
                                          end_date: Optional[datetime] = None) -> List[Dict]:
        """優化版Partner汇总查詢"""
        
        # 使用聚合查詢和覆蓋索引
        query = """
        SELECT 
            c.partner,
            COUNT(*) as total_records,
            SUM(COALESCE(c.sale_amount, c.usd_sale_amount, 0)) as total_amount,
            AVG(COALESCE(c.sale_amount, c.usd_sale_amount, 0)) as avg_amount,
            COUNT(DISTINCT DATE(c.datetime_conversion)) as active_days
        FROM conversions c
        WHERE c.datetime_conversion IS NOT NULL
        """
        
        params = []
        param_count = 0
        
        if partner and partner.upper() != 'ALL':
            param_count += 1
            query += f" AND c.partner = ${param_count}"
            params.append(partner)
        
        if start_date:
            param_count += 1
            query += f" AND DATE(c.datetime_conversion) >= ${param_count}"
            params.append(start_date.date())
        
        if end_date:
            param_count += 1
            query += f" AND DATE(c.datetime_conversion) <= ${param_count}"
            params.append(end_date.date())
        
        query += " GROUP BY c.partner ORDER BY total_amount DESC"
        
        return await self.execute_query(query, params, True)
    
    async def health_check(self) -> Dict[str, Any]:
        """健康檢查"""
        try:
            start_time = time.time()
            
            async with self.get_connection() as conn:
                await conn.fetchval("SELECT 1")
                
            db_latency = (time.time() - start_time) * 1000
            
            cache_stats = self.cache.get_stats() if self.cache else {}
            pool_stats = self.monitor.get_status()
            
            return {
                'status': 'healthy',
                'database': {
                    'connected': True,
                    'latency_ms': round(db_latency, 2),
                    'pool_size': f"{self.config.min_size}-{self.config.max_size}",
                    'active_connections': pool_stats.get('active_connections', 0)
                },
                'cache': {
                    'enabled': self.config.enable_cache,
                    'type': 'redis' if self.redis_client else 'local',
                    **cache_stats
                },
                'performance': pool_stats
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'database': {'connected': False}
            }
    
    async def close(self):
        """關閉資料庫管理器"""
        if self.pool:
            await self.pool.close()
            logger.info("✅ 資料庫連接池已關閉")
            
        if self.redis_client:
            await self.redis_client.close()
            logger.info("✅ Redis連接已關閉")

# 全局實例
_global_db_manager: Optional[EnhancedDatabaseManager] = None

async def get_database_manager(config: Optional[DatabaseConfig] = None) -> EnhancedDatabaseManager:
    """獲取全局資料庫管理器實例"""
    global _global_db_manager
    
    if _global_db_manager is None:
        _global_db_manager = EnhancedDatabaseManager(config)
        await _global_db_manager.initialize()
    
    return _global_db_manager

# 便捷函數
async def execute_query(query: str, params: List[Any] = None, **kwargs) -> List[Dict]:
    """執行查詢的便捷函數"""
    db = await get_database_manager()
    return await db.execute_query(query, params, **kwargs)

async def get_conversions(partner: str = None, start_date: datetime = None, 
                         end_date: datetime = None, limit: int = None) -> List[Dict]:
    """獲取轉化數據的便捷函數"""
    db = await get_database_manager()
    return await db.get_conversions_optimized(partner, start_date, end_date, limit) 