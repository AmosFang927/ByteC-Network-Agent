#!/usr/bin/env python3
"""
企業級連接池管理器
Enhanced Connection Pool Manager

解決連接池設置偏保守問題，提供高性能數據庫連接管理
"""

import asyncio
import asyncpg
import logging
import time
import os
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class ConnectionPoolConfig:
    """連接池配置"""
    min_size: int = 10          # 最小連接數（從2增加到10）
    max_size: int = 50          # 最大連接數（從10增加到50）
    max_queries: int = 50000    # 每個連接最大查詢數
    max_inactive_time: int = 300  # 最大空閒時間（秒）
    command_timeout: int = 60   # 命令超時時間
    server_settings: Dict[str, str] = None  # 服務器設置

    def __post_init__(self):
        if self.server_settings is None:
            self.server_settings = {
                'application_name': 'ByteC-Dashboard-Agent',
                'search_path': 'public',
                'timezone': 'UTC',
                'statement_timeout': '60s',
                'idle_in_transaction_session_timeout': '300s',
                'tcp_keepalives_idle': '600',
                'tcp_keepalives_interval': '30', 
                'tcp_keepalives_count': '3'
            }

@dataclass
class PoolMetrics:
    """連接池指標"""
    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    total_queries: int = 0
    avg_query_time: float = 0.0
    connection_errors: int = 0
    pool_hits: int = 0
    pool_misses: int = 0
    last_reset: datetime = None

class EnhancedConnectionPool:
    """企業級連接池管理器"""
    
    def __init__(self, config: ConnectionPoolConfig = None):
        self.config = config or ConnectionPoolConfig()
        self.pool: Optional[asyncpg.Pool] = None
        self.metrics = PoolMetrics()
        self.is_initialized = False
        self._lock = asyncio.Lock()
        
        # 數據庫配置
        self.db_config = {
            "host": os.getenv("DB_HOST", "34.124.206.16"),
            "port": int(os.getenv("DB_PORT", "5432")),
            "database": os.getenv("DB_NAME", "postback_db"),
            "user": os.getenv("DB_USER", "postback_admin"),
            "password": os.getenv("DB_PASSWORD", "ByteC2024PostBack_CloudSQL")
        }
        
        # 性能監控
        self._query_times: List[float] = []
        self._connection_health_check_interval = 30  # 30秒檢查一次
        self._health_check_task: Optional[asyncio.Task] = None

    async def initialize(self) -> bool:
        """初始化連接池"""
        if self.is_initialized:
            return True
            
        async with self._lock:
            if self.is_initialized:
                return True
                
            try:
                logger.info("🚀 初始化企業級連接池...")
                
                # 創建連接池
                self.pool = await asyncpg.create_pool(
                    host=self.db_config["host"],
                    port=self.db_config["port"],
                    database=self.db_config["database"],
                    user=self.db_config["user"],
                    password=self.db_config["password"],
                    min_size=self.config.min_size,
                    max_size=self.config.max_size,
                    max_queries=self.config.max_queries,
                    max_inactive_connection_lifetime=self.config.max_inactive_time,
                    command_timeout=self.config.command_timeout,
                    server_settings=self.config.server_settings,
                    init=self._init_connection
                )
                
                # 測試連接池
                await self._test_pool()
                
                # 啟動健康檢查
                self._health_check_task = asyncio.create_task(self._health_check_loop())
                
                self.is_initialized = True
                self.metrics.last_reset = datetime.now()
                
                logger.info(f"✅ 連接池初始化成功: min={self.config.min_size}, max={self.config.max_size}")
                return True
                
            except Exception as e:
                logger.error(f"❌ 連接池初始化失敗: {e}")
                self.metrics.connection_errors += 1
                return False

    async def _init_connection(self, conn: asyncpg.Connection):
        """初始化新連接"""
        try:
            # 設置連接級配置
            await conn.execute("SET timezone = 'UTC'")
            await conn.execute("SET statement_timeout = '60s'")
            await conn.execute("SET idle_in_transaction_session_timeout = '300s'")
            
            # 預熱常用查詢
            await conn.fetchval("SELECT 1")
            
            logger.debug("✅ 連接初始化完成")
            
        except Exception as e:
            logger.warning(f"⚠️ 連接初始化警告: {e}")

    async def _test_pool(self):
        """測試連接池"""
        async with self.pool.acquire() as conn:
            result = await conn.fetchval("SELECT current_database()")
            logger.info(f"✅ 連接池測試成功，當前數據庫: {result}")

    async def _health_check_loop(self):
        """健康檢查循環"""
        while self.is_initialized:
            try:
                await asyncio.sleep(self._connection_health_check_interval)
                await self._perform_health_check()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"⚠️ 健康檢查失敗: {e}")

    async def _perform_health_check(self):
        """執行健康檢查"""
        try:
            start_time = time.time()
            
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            
            check_time = time.time() - start_time
            
            # 更新指標
            self.metrics.total_connections = self.pool.get_size()
            
            logger.debug(f"🔍 健康檢查完成: {check_time:.3f}s, 活躍連接: {self.pool.get_size()}")
            
        except Exception as e:
            logger.warning(f"⚠️ 健康檢查異常: {e}")
            self.metrics.connection_errors += 1

    @asynccontextmanager
    async def get_connection(self):
        """獲取連接（上下文管理器）"""
        if not self.is_initialized:
            await self.initialize()
        
        start_time = time.time()
        
        try:
            async with self.pool.acquire() as conn:
                self.metrics.pool_hits += 1
                self.metrics.active_connections += 1
                
                yield conn
                
        except Exception as e:
            self.metrics.connection_errors += 1
            self.metrics.pool_misses += 1
            logger.error(f"❌ 連接獲取失敗: {e}")
            raise
        finally:
            execution_time = time.time() - start_time
            self._update_query_metrics(execution_time)
            self.metrics.active_connections = max(0, self.metrics.active_connections - 1)

    async def execute_query(self, query: str, *args) -> List[asyncpg.Record]:
        """執行查詢"""
        start_time = time.time()
        
        try:
            async with self.get_connection() as conn:
                result = await conn.fetch(query, *args)
                
                self.metrics.total_queries += 1
                query_time = time.time() - start_time
                
                logger.debug(f"🔍 查詢執行: {query_time:.3f}s, 返回 {len(result)} 條記錄")
                
                return result
                
        except Exception as e:
            query_time = time.time() - start_time
            logger.error(f"❌ 查詢執行失敗: {query_time:.3f}s - {e}")
            raise

    async def execute_query_one(self, query: str, *args) -> Optional[asyncpg.Record]:
        """執行查詢（返回單條記錄）"""
        start_time = time.time()
        
        try:
            async with self.get_connection() as conn:
                result = await conn.fetchrow(query, *args)
                
                self.metrics.total_queries += 1
                query_time = time.time() - start_time
                
                logger.debug(f"🔍 單條查詢執行: {query_time:.3f}s")
                
                return result
                
        except Exception as e:
            query_time = time.time() - start_time
            logger.error(f"❌ 單條查詢執行失敗: {query_time:.3f}s - {e}")
            raise

    async def execute_query_value(self, query: str, *args) -> Any:
        """執行查詢（返回單個值）"""
        start_time = time.time()
        
        try:
            async with self.get_connection() as conn:
                result = await conn.fetchval(query, *args)
                
                self.metrics.total_queries += 1
                query_time = time.time() - start_time
                
                logger.debug(f"🔍 值查詢執行: {query_time:.3f}s")
                
                return result
                
        except Exception as e:
            query_time = time.time() - start_time
            logger.error(f"❌ 值查詢執行失敗: {query_time:.3f}s - {e}")
            raise

    def _update_query_metrics(self, execution_time: float):
        """更新查詢指標"""
        self._query_times.append(execution_time)
        
        # 保持最近1000次查詢的記錄
        if len(self._query_times) > 1000:
            self._query_times = self._query_times[-1000:]
        
        # 計算平均查詢時間
        if self._query_times:
            self.metrics.avg_query_time = sum(self._query_times) / len(self._query_times)

    def get_metrics(self) -> Dict[str, Any]:
        """獲取連接池指標"""
        pool_size = self.pool.get_size() if self.pool else 0
        idle_size = self.pool.get_idle_size() if self.pool else 0
        
        return {
            'pool_config': {
                'min_size': self.config.min_size,
                'max_size': self.config.max_size,
                'max_queries': self.config.max_queries,
                'max_inactive_time': self.config.max_inactive_time
            },
            'current_status': {
                'total_connections': pool_size,
                'idle_connections': idle_size,
                'active_connections': pool_size - idle_size,
                'is_initialized': self.is_initialized
            },
            'performance_metrics': {
                'total_queries': self.metrics.total_queries,
                'avg_query_time': f"{self.metrics.avg_query_time:.3f}s",
                'pool_hit_rate': f"{(self.metrics.pool_hits / max(1, self.metrics.pool_hits + self.metrics.pool_misses)) * 100:.1f}%",
                'connection_errors': self.metrics.connection_errors
            },
            'query_time_distribution': {
                'fast_queries_(<0.1s)': len([t for t in self._query_times if t < 0.1]),
                'medium_queries_(0.1-1s)': len([t for t in self._query_times if 0.1 <= t < 1.0]),
                'slow_queries_(>1s)': len([t for t in self._query_times if t >= 1.0])
            } if self._query_times else {},
            'uptime': str(datetime.now() - self.metrics.last_reset) if self.metrics.last_reset else "N/A"
        }

    async def close(self):
        """關閉連接池"""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        if self.pool:
            await self.pool.close()
            logger.info("✅ 連接池已關閉")
        
        self.is_initialized = False

# 全局連接池實例
_global_pool: Optional[EnhancedConnectionPool] = None

async def get_global_pool() -> EnhancedConnectionPool:
    """獲取全局連接池"""
    global _global_pool
    
    if _global_pool is None:
        _global_pool = EnhancedConnectionPool()
        await _global_pool.initialize()
    
    return _global_pool

async def close_global_pool():
    """關閉全局連接池"""
    global _global_pool
    
    if _global_pool:
        await _global_pool.close()
        _global_pool = None 