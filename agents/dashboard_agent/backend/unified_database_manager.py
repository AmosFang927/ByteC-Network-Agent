#!/usr/bin/env python3
"""
ByteC 統一數據庫管理器 v2.0
ByteC Unified Database Manager v2.0

整合企業級連接池、反N+1查詢引擎、智能三層緩存的統一解決方案
"""

import asyncio
import logging
import time
import json
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager

import asyncpg

logger = logging.getLogger(__name__)

@dataclass
class UnifiedConfig:
    """統一配置類"""
    # 數據庫配置
    database_url: str = "postgresql://username:password@localhost/postback_db"
    
    # 連接池配置
    pool_min_size: int = 10
    pool_max_size: int = 50
    pool_overflow_size: int = 20
    pool_max_queries: int = 50000
    pool_max_inactive_time: int = 300
    pool_command_timeout: int = 60
    pool_health_check_interval: int = 30
    
    # 緩存配置
    l1_memory_size: int = 100  # MB
    l1_ttl: int = 50          # 毫秒
    l2_redis_size: int = 1024  # MB
    l2_ttl: int = 300         # 秒
    l3_disk_size: int = 10240  # MB
    l3_ttl: int = 1800        # 秒
    
    # 查詢優化配置
    enable_query_optimization: bool = True
    enable_batch_processing: bool = True
    batch_size: int = 1000
    parallel_workers: int = 4
    
    # 監控配置
    enable_performance_monitoring: bool = True
    metrics_retention_days: int = 30
    alert_thresholds: Dict[str, float] = None
    
    def __post_init__(self):
        if self.alert_thresholds is None:
            self.alert_thresholds = {
                'response_time': 1.0,      # 秒
                'cache_hit_rate': 0.5,     # 50%
                'connection_usage': 0.9,   # 90%
                'error_rate': 0.05         # 5%
            }

@dataclass
class PerformanceMetrics:
    """性能指標"""
    # 響應時間指標
    avg_response_time: float = 0.0
    p95_response_time: float = 0.0
    p99_response_time: float = 0.0
    
    # 吞吐量指標
    current_qps: int = 0
    peak_qps: int = 0
    total_queries: int = 0
    
    # 緩存指標
    cache_hit_rate: float = 0.0
    cache_miss_rate: float = 0.0
    cache_response_time: float = 0.0
    
    # 連接池指標
    active_connections: int = 0
    idle_connections: int = 0
    connection_pool_usage: float = 0.0
    
    # 系統指標
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    error_rate: float = 0.0
    
    # 優化指標
    optimized_queries: int = 0
    query_optimization_ratio: float = 0.0
    n_plus_one_eliminated: int = 0

class IntelligentCache:
    """智能三層緩存系統"""
    
    def __init__(self, config: UnifiedConfig):
        self.config = config
        self.l1_cache: Dict[str, Any] = {}  # 記憶體緩存
        self.l2_cache: Optional[Any] = None  # Redis緩存 (稍後實現)
        self.l3_cache: Dict[str, Any] = {}   # 磁盤緩存 (簡化實現)
        
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'total_requests': 0
        }
    
    async def get(self, key: str) -> Optional[Any]:
        """智能獲取緩存數據"""
        self.cache_stats['total_requests'] += 1
        
        # L1 記憶體緩存
        if key in self.l1_cache:
            entry = self.l1_cache[key]
            if time.time() - entry['timestamp'] < self.config.l1_ttl / 1000:
                self.cache_stats['hits'] += 1
                return entry['data']
            else:
                del self.l1_cache[key]
        
        # L2 Redis緩存 (簡化)
        # 此處可以集成Redis
        
        # L3 磁盤緩存
        if key in self.l3_cache:
            entry = self.l3_cache[key]
            if time.time() - entry['timestamp'] < self.config.l3_ttl:
                # 升級到L1緩存
                self.l1_cache[key] = {
                    'data': entry['data'],
                    'timestamp': time.time()
                }
                self.cache_stats['hits'] += 1
                return entry['data']
            else:
                del self.l3_cache[key]
        
        self.cache_stats['misses'] += 1
        return None
    
    async def set(self, key: str, value: Any, ttl_level: str = 'l1') -> None:
        """智能設置緩存數據"""
        current_time = time.time()
        
        if ttl_level == 'l1':
            self.l1_cache[key] = {
                'data': value,
                'timestamp': current_time
            }
        elif ttl_level == 'l3':
            self.l3_cache[key] = {
                'data': value,
                'timestamp': current_time
            }
    
    def get_hit_rate(self) -> float:
        """獲取緩存命中率"""
        total = self.cache_stats['total_requests']
        if total == 0:
            return 0.0
        return self.cache_stats['hits'] / total
    
    async def clear_expired(self) -> int:
        """清理過期緩存"""
        current_time = time.time()
        cleared = 0
        
        # 清理L1緩存
        expired_l1 = [
            key for key, entry in self.l1_cache.items()
            if current_time - entry['timestamp'] >= self.config.l1_ttl / 1000
        ]
        for key in expired_l1:
            del self.l1_cache[key]
            cleared += 1
        
        # 清理L3緩存
        expired_l3 = [
            key for key, entry in self.l3_cache.items()
            if current_time - entry['timestamp'] >= self.config.l3_ttl
        ]
        for key in expired_l3:
            del self.l3_cache[key]
            cleared += 1
        
        return cleared

class QueryOptimizer:
    """查詢優化引擎"""
    
    def __init__(self, config: UnifiedConfig):
        self.config = config
        self.optimized_patterns = {}
        self.query_stats = {
            'total_queries': 0,
            'optimized_queries': 0,
            'n_plus_one_eliminated': 0
        }
    
    def register_pattern(self, name: str, optimized_query: str, original_queries: List[str]):
        """註冊優化查詢模式"""
        self.optimized_patterns[name] = {
            'optimized_query': optimized_query,
            'original_queries': original_queries,
            'usage_count': 0
        }
    
    async def execute_optimized(self, pool: asyncpg.Pool, pattern_name: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """執行優化查詢"""
        if pattern_name not in self.optimized_patterns:
            raise ValueError(f"Unknown optimization pattern: {pattern_name}")
        
        pattern = self.optimized_patterns[pattern_name]
        query = pattern['optimized_query']
        
        self.query_stats['total_queries'] += 1
        self.query_stats['optimized_queries'] += 1
        self.query_stats['n_plus_one_eliminated'] += len(pattern['original_queries']) - 1
        pattern['usage_count'] += 1
        
        async with pool.acquire() as conn:
            results = await conn.fetch(query, **params)
            return [dict(row) for row in results]
    
    def get_optimization_ratio(self) -> float:
        """獲取查詢優化比例"""
        total = self.query_stats['total_queries']
        if total == 0:
            return 0.0
        return self.query_stats['optimized_queries'] / total

class PerformanceMonitor:
    """性能監控系統"""
    
    def __init__(self, config: UnifiedConfig):
        self.config = config
        self.metrics = PerformanceMetrics()
        self.response_times: List[float] = []
        self.start_time = time.time()
        self.last_qps_calculation = time.time()
        self.query_count_last_period = 0
    
    def record_query(self, response_time: float, optimized: bool = False, cached: bool = False):
        """記錄查詢性能"""
        self.response_times.append(response_time)
        self.metrics.total_queries += 1
        
        if optimized:
            self.metrics.optimized_queries += 1
        
        # 保持最近1000次查詢的記錄
        if len(self.response_times) > 1000:
            self.response_times = self.response_times[-1000:]
        
        # 更新響應時間指標
        if self.response_times:
            self.metrics.avg_response_time = sum(self.response_times) / len(self.response_times)
            sorted_times = sorted(self.response_times)
            n = len(sorted_times)
            self.metrics.p95_response_time = sorted_times[int(n * 0.95)]
            self.metrics.p99_response_time = sorted_times[int(n * 0.99)]
        
        # 計算QPS
        current_time = time.time()
        if current_time - self.last_qps_calculation >= 1.0:  # 每秒計算一次
            time_diff = current_time - self.last_qps_calculation
            queries_diff = self.metrics.total_queries - self.query_count_last_period
            self.metrics.current_qps = int(queries_diff / time_diff)
            self.metrics.peak_qps = max(self.metrics.peak_qps, self.metrics.current_qps)
            
            self.last_qps_calculation = current_time
            self.query_count_last_period = self.metrics.total_queries
    
    def update_cache_metrics(self, hit_rate: float, response_time: float):
        """更新緩存指標"""
        self.metrics.cache_hit_rate = hit_rate
        self.metrics.cache_miss_rate = 1.0 - hit_rate
        self.metrics.cache_response_time = response_time
    
    def update_connection_metrics(self, active: int, idle: int, max_connections: int):
        """更新連接池指標"""
        self.metrics.active_connections = active
        self.metrics.idle_connections = idle
        total = active + idle
        self.metrics.connection_pool_usage = total / max_connections if max_connections > 0 else 0.0
    
    def check_alerts(self) -> List[Dict[str, Any]]:
        """檢查告警條件"""
        alerts = []
        thresholds = self.config.alert_thresholds
        
        if self.metrics.avg_response_time > thresholds['response_time']:
            alerts.append({
                'type': 'high_response_time',
                'value': self.metrics.avg_response_time,
                'threshold': thresholds['response_time'],
                'severity': 'warning'
            })
        
        if self.metrics.cache_hit_rate < thresholds['cache_hit_rate']:
            alerts.append({
                'type': 'low_cache_hit_rate',
                'value': self.metrics.cache_hit_rate,
                'threshold': thresholds['cache_hit_rate'],
                'severity': 'warning'
            })
        
        if self.metrics.connection_pool_usage > thresholds['connection_usage']:
            alerts.append({
                'type': 'high_connection_usage',
                'value': self.metrics.connection_pool_usage,
                'threshold': thresholds['connection_usage'],
                'severity': 'critical'
            })
        
        return alerts

class UnifiedDatabaseManager:
    """統一數據庫管理器"""
    
    def __init__(self, config: Optional[UnifiedConfig] = None):
        """初始化統一數據庫管理器"""
        self.config = config or UnifiedConfig()
        self.pool: Optional[asyncpg.Pool] = None
        self.cache = IntelligentCache(self.config)
        self.query_optimizer = QueryOptimizer(self.config)
        self.performance_monitor = PerformanceMonitor(self.config)
        self.is_initialized = False
        
        logger.info("統一數據庫管理器初始化完成")
    
    async def initialize(self) -> None:
        """初始化所有組件"""
        if self.is_initialized:
            return
        
        # 創建連接池
        self.pool = await asyncpg.create_pool(
            self.config.database_url,
            min_size=self.config.pool_min_size,
            max_size=self.config.pool_max_size,
            max_queries=self.config.pool_max_queries,
            max_inactive_connection_lifetime=self.config.pool_max_inactive_time,
            command_timeout=self.config.pool_command_timeout
        )
        
        # 註冊優化查詢模式
        await self._register_optimization_patterns()
        
        # 啟動後台監控任務
        if self.config.enable_performance_monitoring:
            asyncio.create_task(self._background_monitoring())
        
        self.is_initialized = True
        logger.info("統一數據庫管理器初始化成功")
    
    async def _register_optimization_patterns(self):
        """註冊預定義的查詢優化模式"""
        
        # 統一總覽查詢
        self.query_optimizer.register_pattern(
            'summary_metrics_unified',
            """
            WITH conversion_stats AS (
                SELECT 
                    COUNT(*) as total_conversions,
                    SUM(revenue) as total_revenue,
                    COUNT(DISTINCT partner_id) as active_partners,
                    AVG(revenue) as avg_revenue
                FROM conversions 
                WHERE datetime_conversion >= $1 AND datetime_conversion < $2
            ),
            daily_trend AS (
                SELECT 
                    DATE(datetime_conversion) as date,
                    COUNT(*) as daily_conversions,
                    SUM(revenue) as daily_revenue
                FROM conversions 
                WHERE datetime_conversion >= $1 AND datetime_conversion < $2
                GROUP BY DATE(datetime_conversion)
                ORDER BY date DESC
                LIMIT 7
            )
            SELECT 
                cs.*,
                json_agg(dt.*) as daily_trends
            FROM conversion_stats cs
            CROSS JOIN daily_trend dt
            GROUP BY cs.total_conversions, cs.total_revenue, cs.active_partners, cs.avg_revenue
            """,
            [
                "SELECT COUNT(*) FROM conversions WHERE datetime_conversion >= $1 AND datetime_conversion < $2",
                "SELECT SUM(revenue) FROM conversions WHERE datetime_conversion >= $1 AND datetime_conversion < $2",
                "SELECT COUNT(DISTINCT partner_id) FROM conversions WHERE datetime_conversion >= $1 AND datetime_conversion < $2",
                "SELECT DATE(datetime_conversion) as date, COUNT(*) FROM conversions WHERE datetime_conversion >= $1 AND datetime_conversion < $2 GROUP BY DATE(datetime_conversion)"
            ]
        )
        
        # 批量轉化詳情查詢
        self.query_optimizer.register_pattern(
            'conversion_details_batch',
            """
            WITH paginated_conversions AS (
                SELECT 
                    c.*,
                    p.partner_name,
                    o.offer_name
                FROM conversions c
                LEFT JOIN partners p ON c.partner_id = p.partner_id
                LEFT JOIN offers o ON c.offer_id = o.offer_id
                WHERE c.datetime_conversion >= $1 AND c.datetime_conversion < $2
                ORDER BY c.datetime_conversion DESC
                LIMIT $3 OFFSET $4
            ),
            total_count AS (
                SELECT COUNT(*) as total
                FROM conversions
                WHERE datetime_conversion >= $1 AND datetime_conversion < $2
            )
            SELECT 
                pc.*,
                tc.total as total_count
            FROM paginated_conversions pc
            CROSS JOIN total_count tc
            """,
            [
                "SELECT COUNT(*) FROM conversions WHERE datetime_conversion >= $1 AND datetime_conversion < $2",
                "SELECT c.*, p.partner_name, o.offer_name FROM conversions c LEFT JOIN partners p ON c.partner_id = p.partner_id LEFT JOIN offers o ON c.offer_id = o.offer_id WHERE c.datetime_conversion >= $1 AND c.datetime_conversion < $2 ORDER BY c.datetime_conversion DESC LIMIT $3 OFFSET $4"
            ]
        )
    
    @asynccontextmanager
    async def get_connection(self):
        """獲取數據庫連接"""
        if not self.is_initialized:
            await self.initialize()
        
        async with self.pool.acquire() as conn:
            yield conn
    
    async def execute_cached_query(self, 
                                 query: str, 
                                 params: Optional[Dict[str, Any]] = None,
                                 cache_key: Optional[str] = None,
                                 cache_ttl: str = 'l1') -> List[Dict[str, Any]]:
        """執行帶緩存的查詢"""
        start_time = time.time()
        params = params or {}
        
        # 生成緩存鍵
        if cache_key is None:
            param_str = json.dumps(params, sort_keys=True, default=str)
            cache_key = f"query:{hash(query + param_str)}"
        
        # 嘗試從緩存獲取
        cached_result = await self.cache.get(cache_key)
        if cached_result is not None:
            response_time = time.time() - start_time
            self.performance_monitor.record_query(response_time, cached=True)
            return cached_result
        
        # 執行查詢
        async with self.get_connection() as conn:
            results = await conn.fetch(query, **params)
            result_dicts = [dict(row) for row in results]
        
        # 設置緩存
        await self.cache.set(cache_key, result_dicts, cache_ttl)
        
        # 記錄性能
        response_time = time.time() - start_time
        self.performance_monitor.record_query(response_time)
        
        return result_dicts
    
    async def execute_optimized_query(self, 
                                    pattern_name: str, 
                                    params: Dict[str, Any],
                                    cache_key: Optional[str] = None) -> List[Dict[str, Any]]:
        """執行優化查詢"""
        start_time = time.time()
        
        # 生成緩存鍵
        if cache_key is None:
            param_str = json.dumps(params, sort_keys=True, default=str)
            cache_key = f"optimized:{pattern_name}:{hash(param_str)}"
        
        # 嘗試從緩存獲取
        cached_result = await self.cache.get(cache_key)
        if cached_result is not None:
            response_time = time.time() - start_time
            self.performance_monitor.record_query(response_time, optimized=True, cached=True)
            return cached_result
        
        # 執行優化查詢
        results = await self.query_optimizer.execute_optimized(self.pool, pattern_name, params)
        
        # 設置緩存
        await self.cache.set(cache_key, results, 'l3')  # 優化查詢使用L3緩存
        
        # 記錄性能
        response_time = time.time() - start_time
        self.performance_monitor.record_query(response_time, optimized=True)
        
        return results
    
    async def get_summary_data(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """獲取總覽數據 - 優化版本"""
        results = await self.execute_optimized_query(
            'summary_metrics_unified',
            {'start_date': start_date, 'end_date': end_date}
        )
        
        if results:
            return results[0]
        return {}
    
    async def get_conversion_details(self, 
                                   start_date: str, 
                                   end_date: str, 
                                   page: int = 1, 
                                   limit: int = 100) -> Dict[str, Any]:
        """獲取轉化詳情 - 優化版本"""
        offset = (page - 1) * limit
        
        results = await self.execute_optimized_query(
            'conversion_details_batch',
            {
                'start_date': start_date,
                'end_date': end_date,
                'limit': limit,
                'offset': offset
            }
        )
        
        total_count = results[0]['total_count'] if results else 0
        
        return {
            'data': results,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total_count,
                'pages': (total_count + limit - 1) // limit
            }
        }
    
    async def get_performance_metrics(self) -> PerformanceMetrics:
        """獲取性能指標"""
        # 更新緩存指標
        self.performance_monitor.update_cache_metrics(
            self.cache.get_hit_rate(),
            0.001  # 假設緩存響應時間為1ms
        )
        
        # 更新連接池指標
        if self.pool:
            pool_stats = self.pool.get_stats()
            self.performance_monitor.update_connection_metrics(
                pool_stats.active_connections,
                pool_stats.idle_connections,
                self.config.pool_max_size
            )
        
        # 更新查詢優化指標
        self.performance_monitor.metrics.query_optimization_ratio = self.query_optimizer.get_optimization_ratio()
        self.performance_monitor.metrics.n_plus_one_eliminated = self.query_optimizer.query_stats['n_plus_one_eliminated']
        
        return self.performance_monitor.metrics
    
    async def get_system_health(self) -> Dict[str, Any]:
        """獲取系統健康狀態"""
        metrics = await self.get_performance_metrics()
        alerts = self.performance_monitor.check_alerts()
        
        # 計算健康評分
        health_score = 100
        if metrics.avg_response_time > 0.5:
            health_score -= 20
        if metrics.cache_hit_rate < 0.7:
            health_score -= 15
        if metrics.connection_pool_usage > 0.8:
            health_score -= 15
        if len(alerts) > 0:
            health_score -= len(alerts) * 10
        
        health_score = max(0, health_score)
        
        return {
            'health_score': health_score,
            'status': 'healthy' if health_score >= 80 else 'warning' if health_score >= 60 else 'critical',
            'metrics': asdict(metrics),
            'alerts': alerts,
            'uptime': time.time() - self.performance_monitor.start_time,
            'cache_stats': {
                'hit_rate': self.cache.get_hit_rate(),
                'l1_size': len(self.cache.l1_cache),
                'l3_size': len(self.cache.l3_cache)
            }
        }
    
    async def warm_up_cache(self, start_date: str, end_date: str) -> Dict[str, int]:
        """預熱緩存"""
        logger.info(f"開始預熱緩存: {start_date} 至 {end_date}")
        
        warmed_queries = 0
        
        # 預熱總覽數據
        await self.get_summary_data(start_date, end_date)
        warmed_queries += 1
        
        # 預熱前幾頁的轉化詳情
        for page in range(1, 6):  # 前5頁
            await self.get_conversion_details(start_date, end_date, page, 100)
            warmed_queries += 1
        
        logger.info(f"緩存預熱完成，共預熱 {warmed_queries} 個查詢")
        
        return {
            'warmed_queries': warmed_queries,
            'cache_hit_rate': self.cache.get_hit_rate()
        }
    
    async def _background_monitoring(self):
        """後台監控任務"""
        while True:
            try:
                # 清理過期緩存
                cleared = await self.cache.clear_expired()
                if cleared > 0:
                    logger.debug(f"清理過期緩存: {cleared} 個條目")
                
                # 檢查告警
                alerts = self.performance_monitor.check_alerts()
                for alert in alerts:
                    logger.warning(f"性能告警: {alert}")
                
                # 每30秒執行一次
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"後台監控任務錯誤: {e}")
                await asyncio.sleep(60)  # 錯誤時等待更長時間
    
    async def close(self):
        """關閉數據庫管理器"""
        if self.pool:
            await self.pool.close()
        self.is_initialized = False
        logger.info("統一數據庫管理器已關閉")
    
    async def __aenter__(self):
        """異步上下文管理器入口"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器出口"""
        await self.close()

# 全局實例
_global_db_manager: Optional[UnifiedDatabaseManager] = None

async def get_unified_db() -> UnifiedDatabaseManager:
    """獲取全局統一數據庫管理器實例"""
    global _global_db_manager
    
    if _global_db_manager is None:
        _global_db_manager = UnifiedDatabaseManager()
        await _global_db_manager.initialize()
    
    return _global_db_manager

async def initialize_global_db(config: Optional[UnifiedConfig] = None) -> UnifiedDatabaseManager:
    """初始化全局數據庫管理器"""
    global _global_db_manager
    
    if _global_db_manager is not None:
        await _global_db_manager.close()
    
    _global_db_manager = UnifiedDatabaseManager(config)
    await _global_db_manager.initialize()
    
    return _global_db_manager

async def close_global_db():
    """關閉全局數據庫管理器"""
    global _global_db_manager
    
    if _global_db_manager is not None:
        await _global_db_manager.close()
        _global_db_manager = None

# 使用示例
"""
# 基本使用
async def example_usage():
    # 方式1: 使用全局實例
    db = await get_unified_db()
    
    # 獲取總覽數據
    summary = await db.get_summary_data("2024-01-01", "2024-01-31")
    print(f"總轉化數: {summary.get('total_conversions', 0)}")
    
    # 獲取轉化詳情
    details = await db.get_conversion_details("2024-01-01", "2024-01-31", page=1)
    print(f"第一頁數據: {len(details['data'])} 條")
    
    # 檢查系統健康狀態
    health = await db.get_system_health()
    print(f"系統健康評分: {health['health_score']}")
    
    # 方式2: 使用上下文管理器
    async with UnifiedDatabaseManager() as db:
        # 預熱緩存
        await db.warm_up_cache("2024-01-01", "2024-01-31")
        
        # 執行查詢
        summary = await db.get_summary_data("2024-01-01", "2024-01-31")

# 配置使用
async def example_with_config():
    config = UnifiedConfig(
        database_url="postgresql://user:pass@localhost/db",
        pool_max_size=100,
        l1_ttl=100,
        enable_performance_monitoring=True
    )
    
    db = await initialize_global_db(config)
    
    # 使用配置後的數據庫管理器
    summary = await db.get_summary_data("2024-01-01", "2024-01-31")
""" 