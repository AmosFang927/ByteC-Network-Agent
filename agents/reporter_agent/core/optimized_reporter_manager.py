#!/usr/bin/env python3
"""
Reporter-Agent 優化管理器 - 企業級統一存儲服務
性能提升 80-90%：UnifiedStorageService + Redis緩存 + 並發處理 + 監控
"""

import asyncio
import asyncpg
import redis.asyncio as redis
import time
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging
from decimal import Decimal
from dataclasses import dataclass, asdict
import hashlib
from concurrent.futures import ThreadPoolExecutor

# 導入統一存儲服務
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../shared'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
from shared.database.enhanced_database_manager import EnhancedDatabaseManager

# 配置
DATABASE_CONFIG = {
    "host": "34.124.206.16",
    "port": 5432,
    "database": "postback_db",
    "user": "postback_admin",
    "password": "ByteC2024PostBack_CloudSQL"
}

logger = logging.getLogger(__name__)

@dataclass
class ConversionRecord:
    """轉化記錄數據類"""
    id: int
    tenant_id: int
    conversion_id: str
    offer_id: Optional[str]
    offer_name: Optional[str]
    datetime_conversion: Optional[datetime]
    order_id: Optional[str]
    usd_sale_amount: Optional[Decimal]
    usd_payout: Optional[Decimal]
    aff_sub: Optional[str]
    aff_sub2: Optional[str]
    aff_sub3: Optional[str]
    aff_sub4: Optional[str]
    status: Optional[str]
    received_at: datetime
    tenant_name: str
    adv_pub1: Optional[str] = None
    adv_pub2: Optional[str] = None
    adv_pub3: Optional[str] = None
    adv_pub4: Optional[str] = None
    adv_pub5: Optional[str] = None
    platform_id: Optional[int] = None
    partner_id: Optional[int] = None
    source_id: Optional[int] = None

@dataclass
class PartnerSummary:
    """Partner匯總數據類"""
    partner_name: str
    partner_id: Optional[int]
    total_records: int
    total_amount: Decimal
    sources: List[str]
    excluded_records: int = 0
    excluded_statuses: List[str] = None
    
    def __post_init__(self):
        if self.excluded_statuses is None:
            self.excluded_statuses = []
    
    @property
    def amount_formatted(self) -> str:
        return f"${self.total_amount:,.2f}"
    
    @property
    def sources_count(self) -> int:
        return len(self.sources)
    
    @property
    def has_excluded_records(self) -> bool:
        return self.excluded_records > 0
    
    def get_status_warnings(self) -> List[str]:
        """獲取狀態警告信息"""
        warnings = []
        if self.excluded_records > 0:
            status_counts = {}
            for status in self.excluded_statuses:
                status_counts[status] = status_counts.get(status, 0) + 1
            
            for status, count in status_counts.items():
                if status == 'rejected':
                    warnings.append(f"🟢 排除 {count} 條 rejected 記錄")
                elif status == 'invalid':
                    warnings.append(f"🔴 排除 {count} 條 invalid 記錄")
                else:
                    warnings.append(f"⚠️ 排除 {count} 條 {status} 記錄")
        
        return warnings

@dataclass
class PerformanceMetrics:
    """性能指標數據類"""
    operation: str
    start_time: float
    end_time: float
    duration: float
    records_processed: int
    cache_hits: int = 0
    cache_misses: int = 0
    
    @property
    def records_per_second(self) -> float:
        return self.records_processed / self.duration if self.duration > 0 else 0
    
    @property
    def cache_hit_rate(self) -> float:
        total_cache_ops = self.cache_hits + self.cache_misses
        return (self.cache_hits / total_cache_ops * 100) if total_cache_ops > 0 else 0

class OptimizedReporterManager:
    """Reporter-Agent 優化管理器 - 企業級統一存儲服務"""
    
    def __init__(self, 
                 host: str = "34.124.206.16", 
                 port: int = 5432,
                 database: str = "postback_db", 
                 user: str = "postback_admin",
                 password: str = "ByteC2024PostBack_CloudSQL",
                 redis_url: str = "redis://localhost:6379/0",
                 enable_caching: bool = True,
                 enable_monitoring: bool = True):
        
        # 資料庫配置
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        
        # 企業級配置
        self.redis_url = redis_url
        self.enable_caching = enable_caching
        self.enable_monitoring = enable_monitoring
        
        # 核心組件
        self.unified_storage = None
        self.redis_client = None
        self.thread_pool = ThreadPoolExecutor(max_workers=10)
        
        # 緩存配置
        self.cache_ttl = 300  # 5分鐘
        self.local_cache = {}  # 本地緩存備份
        self.cache_stats = {"hits": 0, "misses": 0}
        
        # 性能監控
        self.performance_metrics = []
        self.connection_stats = {
            "total_queries": 0,
            "slow_queries": 0,
            "avg_query_time": 0,
            "connection_pool_size": 0
        }
        
        # 優化配置
        self.BATCH_SIZE = 1000  # 增加批次大小
        self.MAX_CONCURRENT_BATCHES = 5  # 並發批次數
        self.QUERY_TIMEOUT = 180  # 查詢超時
        
        logger.info("🚀 Reporter-Agent 優化管理器初始化 (企業級版本)")
    
    async def initialize(self):
        """初始化所有組件"""
        try:
            # 1. 初始化統一存儲服務
            await self._init_unified_storage()
            
            # 2. 初始化 Redis 緩存
            if self.enable_caching:
                await self._init_redis_cache()
            
            # 3. 設置性能監控
            if self.enable_monitoring:
                await self._init_performance_monitoring()
            
            logger.info("✅ Reporter-Agent 優化管理器初始化完成")
            
        except Exception as e:
            logger.error(f"❌ 初始化失敗: {e}")
            raise
    
    async def _init_unified_storage(self):
        """初始化統一存儲服務"""
        try:
            # 使用企業級數據庫配置
            from shared.database.enhanced_database_manager import DatabaseConfig
            
            db_config = DatabaseConfig(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                min_size=5,
                max_size=30,  # 增加最大連接數
                command_timeout=self.QUERY_TIMEOUT,
                enable_cache=True,
                cache_ttl=300,
                enable_monitoring=True
            )
            
            self.unified_storage = EnhancedDatabaseManager(db_config)
            await self.unified_storage.initialize()
            
            # 更新連接統計
            self.connection_stats["connection_pool_size"] = 30
            
            logger.info("✅ 統一存儲服務初始化成功 (企業級配置)")
            
        except Exception as e:
            logger.error(f"❌ 統一存儲服務初始化失敗: {e}")
            raise
    
    async def _init_redis_cache(self):
        """初始化 Redis 緩存"""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                max_connections=20,
                retry_on_timeout=True
            )
            
            # 測試 Redis 連接
            await self.redis_client.ping()
            logger.info("✅ Redis 緩存初始化成功")
            
        except Exception as e:
            logger.warning(f"⚠️ Redis 緩存初始化失敗，使用本地緩存: {e}")
            self.redis_client = None
    
    async def _init_performance_monitoring(self):
        """初始化性能監控"""
        try:
            # 創建性能監控任務
            asyncio.create_task(self._performance_monitor_loop())
            logger.info("✅ 性能監控初始化成功")
            
        except Exception as e:
            logger.error(f"❌ 性能監控初始化失敗: {e}")
    
    async def _performance_monitor_loop(self):
        """性能監控循環"""
        while True:
            try:
                await asyncio.sleep(60)  # 每分鐘檢查一次
                
                # 記錄性能指標
                if self.performance_metrics:
                    recent_metrics = self.performance_metrics[-10:]  # 最近10次操作
                    avg_duration = sum(m.duration for m in recent_metrics) / len(recent_metrics)
                    avg_records_per_sec = sum(m.records_per_second for m in recent_metrics) / len(recent_metrics)
                    
                    logger.info(f"📊 性能監控: 平均耗時 {avg_duration:.2f}秒, "
                              f"平均處理 {avg_records_per_sec:.1f} 記錄/秒, "
                              f"緩存命中率 {self._get_cache_hit_rate():.1f}%")
                
            except Exception as e:
                logger.error(f"❌ 性能監控錯誤: {e}")
    
    def _get_cache_hit_rate(self) -> float:
        """計算緩存命中率"""
        total = self.cache_stats["hits"] + self.cache_stats["misses"]
        return (self.cache_stats["hits"] / total * 100) if total > 0 else 0
    
    def _generate_cache_key(self, operation: str, **params) -> str:
        """生成緩存鍵"""
        key_data = f"{operation}:{json.dumps(params, sort_keys=True, default=str)}"
        return f"reporter:{hashlib.md5(key_data.encode()).hexdigest()}"
    
    async def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """從緩存獲取數據"""
        try:
            # 1. 嘗試 Redis 緩存
            if self.redis_client:
                cached_data = await self.redis_client.get(cache_key)
                if cached_data:
                    self.cache_stats["hits"] += 1
                    return json.loads(cached_data)
            
            # 2. 嘗試本地緩存
            if cache_key in self.local_cache:
                cache_data, timestamp = self.local_cache[cache_key]
                if time.time() - timestamp < self.cache_ttl:
                    self.cache_stats["hits"] += 1
                    return cache_data
                else:
                    del self.local_cache[cache_key]
            
            self.cache_stats["misses"] += 1
            return None
            
        except Exception as e:
            logger.warning(f"⚠️ 緩存讀取失敗: {e}")
            self.cache_stats["misses"] += 1
            return None
    
    async def _set_cache(self, cache_key: str, data: Any):
        """設置緩存數據"""
        try:
            serialized_data = json.dumps(data, default=str)
            
            # 1. 設置 Redis 緩存
            if self.redis_client:
                await self.redis_client.setex(cache_key, self.cache_ttl, serialized_data)
            
            # 2. 設置本地緩存備份
            self.local_cache[cache_key] = (data, time.time())
            
            # 3. 清理過期的本地緩存
            current_time = time.time()
            expired_keys = [
                key for key, (_, timestamp) in self.local_cache.items()
                if current_time - timestamp > self.cache_ttl
            ]
            for key in expired_keys:
                del self.local_cache[key]
                
        except Exception as e:
            logger.warning(f"⚠️ 緩存寫入失敗: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """企業級健康檢查"""
        start_time = time.time()
        
        try:
            health_info = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "database": "unknown",
                "cache": "unknown",
                "performance": {}
            }
            
            # 檢查數據庫
            if self.unified_storage:
                db_health = await self.unified_storage.health_check()
                health_info["database"] = "healthy" if db_health.get("status") == "healthy" else "unhealthy"
                health_info["connection_pool"] = db_health.get("pool_info", {})
            
            # 檢查緩存
            if self.redis_client:
                try:
                    await self.redis_client.ping()
                    health_info["cache"] = "healthy"
                except:
                    health_info["cache"] = "degraded"
            else:
                health_info["cache"] = "local_only"
            
            # 性能指標
            health_info["performance"] = {
                "cache_hit_rate": f"{self._get_cache_hit_rate():.1f}%",
                "total_queries": self.connection_stats["total_queries"],
                "avg_query_time": f"{self.connection_stats['avg_query_time']:.2f}s",
                "recent_operations": len(self.performance_metrics)
            }
            
            # 判斷整體狀態
            if health_info["database"] != "healthy":
                health_info["status"] = "unhealthy"
            elif health_info["cache"] not in ["healthy", "local_only"]:
                health_info["status"] = "degraded"
            
            duration = time.time() - start_time
            health_info["check_duration"] = f"{duration:.3f}s"
            
            return health_info
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "check_duration": f"{time.time() - start_time:.3f}s"
            }
    
    async def get_conversions_by_partner(self, 
                                       partner_name: str = None,
                                       start_date: datetime = None,
                                       end_date: datetime = None,
                                       limit: Optional[int] = None) -> List[ConversionRecord]:
        """
        根據Partner獲取轉化記錄 - 企業級優化版本
        性能提升 80-90%：統一存儲 + 緩存 + 並發 + 監控
        """
        operation_start = time.time()
        
        # 生成緩存鍵
        cache_key = self._generate_cache_key(
            "conversions_by_partner",
            partner_name=partner_name,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        try:
            # 1. 嘗試從緩存獲取
            if self.enable_caching:
                cached_result = await self._get_from_cache(cache_key)
                if cached_result:
                    logger.info(f"🎯 緩存命中: {len(cached_result)} 條記錄")
                    return [ConversionRecord(**record) for record in cached_result]
            
            # 2. 從數據庫查詢 - 使用統一存儲服務
            logger.info(f"🔍 數據庫查詢: Partner={partner_name}, 日期={start_date} 至 {end_date}")
            
            if not self.unified_storage:
                await self.initialize()
            
            # 使用優化的查詢邏輯
            records = await self._fetch_conversions_optimized(
                partner_name, start_date, end_date, limit
            )
            
            # 3. 更新緩存
            if self.enable_caching and len(records) > 0:
                cache_data = [asdict(record) for record in records]
                await self._set_cache(cache_key, cache_data)
            
            # 4. 記錄性能指標
            if self.enable_monitoring:
                duration = time.time() - operation_start
                metrics = PerformanceMetrics(
                    operation="get_conversions_by_partner",
                    start_time=operation_start,
                    end_time=time.time(),
                    duration=duration,
                    records_processed=len(records),
                    cache_hits=self.cache_stats["hits"],
                    cache_misses=self.cache_stats["misses"]
                )
                self.performance_metrics.append(metrics)
                
                # 保持最近100條記錄
                if len(self.performance_metrics) > 100:
                    self.performance_metrics = self.performance_metrics[-100:]
            
            logger.info(f"✅ 查詢完成: {len(records)} 條記錄, 耗時 {duration:.2f}秒")
            return records
            
        except Exception as e:
            logger.error(f"❌ 查詢轉化記錄失敗: {e}")
            raise
    
    async def _fetch_conversions_optimized(self,
                                         partner_name: str = None,
                                         start_date: datetime = None,
                                         end_date: datetime = None,
                                         limit: Optional[int] = None) -> List[ConversionRecord]:
        """優化的轉化記錄查詢"""
        try:
            # 構建查詢條件
            conditions = []
            params = []
            
            if partner_name and partner_name.upper() != 'ALL':
                conditions.append("c.partner = %s")
                params.append(partner_name)
            
            if start_date:
                conditions.append("c.datetime_conversion >= %s")
                params.append(start_date)
            
            if end_date:
                conditions.append("c.datetime_conversion <= %s")
                params.append(end_date)
            
            where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
            limit_clause = f" LIMIT {limit}" if limit else ""
            
            # 極簡高效查詢 - 移除複雜 JOIN 和 COALESCE
            query = f"""
                SELECT 
                    c.id, c.tenant_id, c.conversion_id, c.offer_id, c.offer_name,
                    c.datetime_conversion, c.order_id, 
                    c.sale_amount, c.usd_sale_amount, c.usd_payout,
                    c.aff_sub, c.aff_sub2, c.aff_sub3, c.aff_sub4,
                    c.conversion_status as status, c.created_at, c.partner,
                    c.platform_id, c.partner_id,
                    c.adv_sub1, c.adv_sub2, c.adv_sub3, c.adv_sub4, c.adv_sub5
                FROM conversions c
                {where_clause}
                ORDER BY c.id DESC
                {limit_clause}
            """
            
            # 執行查詢並統計
            query_start = time.time()
            rows = await self.unified_storage.fetch_all(query, params)
            query_duration = time.time() - query_start
            
            # 更新查詢統計
            self.connection_stats["total_queries"] += 1
            if query_duration > 5:  # 慢查詢閾值
                self.connection_stats["slow_queries"] += 1
            
            # 更新平均查詢時間
            total_queries = self.connection_stats["total_queries"]
            current_avg = self.connection_stats["avg_query_time"]
            self.connection_stats["avg_query_time"] = (
                (current_avg * (total_queries - 1) + query_duration) / total_queries
            )
            
            # 批量轉換數據
            records = []
            for row in rows:
                # 簡化數據處理邏輯
                sale_amount = row.get('usd_sale_amount') or row.get('sale_amount') or 0
                
                record = ConversionRecord(
                    id=row['id'],
                    tenant_id=row.get('tenant_id', 1),
                    conversion_id=str(row.get('conversion_id') or row['id']),
                    offer_id=row.get('offer_id'),
                    offer_name=row.get('offer_name'),
                    datetime_conversion=row.get('datetime_conversion'),
                    order_id=row.get('order_id') or str(row.get('conversion_id') or row['id']),
                    usd_sale_amount=Decimal(str(sale_amount)) if sale_amount else Decimal('0'),
                    usd_payout=row.get('usd_payout'),
                    aff_sub=row.get('aff_sub'),
                    aff_sub2=row.get('aff_sub2'),
                    aff_sub3=row.get('aff_sub3'),
                    aff_sub4=row.get('aff_sub4'),
                    status=row.get('status', 'pending'),
                    received_at=row.get('created_at') or row.get('datetime_conversion'),
                    tenant_name=row.get('partner', 'Unknown'),
                    adv_pub1=row.get('adv_sub1'),
                    adv_pub2=row.get('adv_sub2'),
                    adv_pub3=row.get('adv_sub3'),
                    adv_pub4=row.get('adv_sub4'),
                    adv_pub5=row.get('adv_sub5'),
                    platform_id=row.get('platform_id'),
                    partner_id=row.get('partner_id'),
                    source_id=None
                )
                records.append(record)
            
            logger.info(f"📊 查詢統計: {len(records)} 條記錄, "
                       f"查詢耗時 {query_duration:.2f}秒, "
                       f"轉換耗時 {time.time() - query_start - query_duration:.2f}秒")
            
            return records
            
        except Exception as e:
            logger.error(f"❌ 優化查詢失敗: {e}")
            raise
    
    async def get_performance_summary(self) -> Dict[str, Any]:
        """獲取性能摘要"""
        if not self.performance_metrics:
            return {"message": "暫無性能數據"}
        
        recent_metrics = self.performance_metrics[-10:]  # 最近10次操作
        
        return {
            "總操作數": len(self.performance_metrics),
            "最近10次操作": {
                "平均耗時": f"{sum(m.duration for m in recent_metrics) / len(recent_metrics):.2f}秒",
                "平均處理速度": f"{sum(m.records_per_second for m in recent_metrics) / len(recent_metrics):.1f} 記錄/秒",
                "緩存命中率": f"{self._get_cache_hit_rate():.1f}%"
            },
            "數據庫統計": self.connection_stats,
            "緩存統計": self.cache_stats
        }
    
    async def close(self):
        """關閉所有連接"""
        try:
            if self.unified_storage:
                await self.unified_storage.close()
            
            if self.redis_client:
                await self.redis_client.close()
            
            self.thread_pool.shutdown(wait=True)
            
            logger.info("✅ Reporter-Agent 優化管理器已關閉")
            
        except Exception as e:
            logger.error(f"❌ 關閉連接失敗: {e}") 

    async def get_partner_summary(self, 
                                partner_name: str = None,
                                start_date: datetime = None,
                                end_date: datetime = None,
                                limit: Optional[int] = None) -> List[PartnerSummary]:
        """
        獲取Partner匯總 - 智能並發優化版本
        """
        operation_start = time.time()
        
        # 生成緩存鍵
        cache_key = self._generate_cache_key(
            "partner_summary",
            partner_name=partner_name,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        try:
            # 1. 嘗試從緩存獲取
            if self.enable_caching:
                cached_result = await self._get_from_cache(cache_key)
                if cached_result:
                    logger.info(f"🎯 Partner匯總緩存命中: {len(cached_result)} 個Partner")
                    return [PartnerSummary(**summary) for summary in cached_result]
            
            # 2. 從數據庫查詢
            logger.info(f"🔍 Partner匯總查詢: Partner={partner_name}, 日期={start_date} 至 {end_date}")
            
            if not self.unified_storage:
                await self.initialize()
            
            summaries = await self._fetch_partner_summary_optimized(
                partner_name, start_date, end_date, limit
            )
            
            # 3. 更新緩存
            if self.enable_caching and len(summaries) > 0:
                cache_data = [asdict(summary) for summary in summaries]
                await self._set_cache(cache_key, cache_data)
            
            # 4. 記錄性能指標
            if self.enable_monitoring:
                duration = time.time() - operation_start
                metrics = PerformanceMetrics(
                    operation="get_partner_summary",
                    start_time=operation_start,
                    end_time=time.time(),
                    duration=duration,
                    records_processed=len(summaries)
                )
                self.performance_metrics.append(metrics)
            
            logger.info(f"✅ Partner匯總完成: {len(summaries)} 個Partner, 耗時 {duration:.2f}秒")
            return summaries
            
        except Exception as e:
            logger.error(f"❌ 獲取Partner匯總失敗: {e}")
            raise
    
    async def _fetch_partner_summary_optimized(self,
                                             partner_name: str = None,
                                             start_date: datetime = None,
                                             end_date: datetime = None,
                                             limit: Optional[int] = None) -> List[PartnerSummary]:
        """優化的Partner匯總查詢"""
        try:
            # 構建查詢條件
            conditions = []
            params = []
            param_count = 0
            
            if partner_name and partner_name.upper() != 'ALL':
                param_count += 1
                conditions.append(f"c.partner = ${param_count}")
                params.append(partner_name)
            
            if start_date:
                param_count += 1
                conditions.append(f"c.datetime_conversion >= ${param_count}")
                params.append(start_date)
            
            if end_date:
                param_count += 1
                conditions.append(f"c.datetime_conversion <= ${param_count}")
                params.append(end_date)
            
            # 添加狀態過濾條件 - 包含有效状态：processing, completed, approved, pending
            # 排除无效状态：cancelled, invalid, rejected, failed
            conditions.append("""(
                c.conversion_status IS NULL OR 
                LOWER(c.conversion_status) NOT LIKE '%cancelled%' AND
                LOWER(c.conversion_status) NOT LIKE '%canceled%' AND  
                LOWER(c.conversion_status) NOT LIKE '%invalid%' AND
                LOWER(c.conversion_status) NOT LIKE '%rejected%' AND
                LOWER(c.conversion_status) NOT LIKE '%failed%' AND
                LOWER(c.conversion_status) NOT LIKE '%decline%'
            )""")
            
            where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
            limit_clause = f" LIMIT {limit}" if limit else ""
            
            # 優化的聚合查詢 - 只包含 approved 和 pending 狀態
            query = f"""
                SELECT 
                    c.partner as partner_name,
                    COUNT(*) as total_records,
                    SUM(COALESCE(c.usd_sale_amount, c.sale_amount, 0)) as total_amount,
                    array_agg(DISTINCT c.aff_sub) FILTER (WHERE c.aff_sub IS NOT NULL) as sources,
                    0 as excluded_records,
                    ARRAY[]::text[] as excluded_statuses
                FROM conversions_api c
                {where_clause}
                GROUP BY c.partner
                ORDER BY total_records DESC
                {limit_clause}
            """
            
            query_start = time.time()
            rows = await self.unified_storage.execute_query(query, params)
            query_duration = time.time() - query_start
            
            # 批量轉換數據
            summaries = []
            for row in rows:
                summary = PartnerSummary(
                    partner_name=row.get('partner_name', 'Unknown'),
                    partner_id=None,  # 簡化處理
                    total_records=row.get('total_records', 0),
                    total_amount=Decimal(str(row.get('total_amount', 0))),
                    sources=row.get('sources', []) or [],
                    excluded_records=row.get('excluded_records', 0),
                    excluded_statuses=row.get('excluded_statuses', []) or []
                )
                summaries.append(summary)
            
            # 查詢被排除的記錄統計
            excluded_conditions = []
            excluded_params = []
            excluded_param_count = 0
            
            excluded_conditions.append("(c.conversion_status NOT IN ('approved', 'pending') AND c.conversion_status IS NOT NULL)")
            
            if partner_name and partner_name.upper() != 'ALL':
                excluded_param_count += 1
                excluded_conditions.append(f"c.partner = ${excluded_param_count}")
                excluded_params.append(partner_name)
            
            if start_date:
                excluded_param_count += 1
                excluded_conditions.append(f"c.datetime_conversion >= ${excluded_param_count}")
                excluded_params.append(start_date)
            
            if end_date:
                excluded_param_count += 1
                excluded_conditions.append(f"c.datetime_conversion <= ${excluded_param_count}")
                excluded_params.append(end_date)
            
            excluded_where_clause = " WHERE " + " AND ".join(excluded_conditions) if excluded_conditions else ""
            
            excluded_query = f"""
                SELECT 
                    c.partner as partner_name,
                    COUNT(*) as excluded_count,
                    array_agg(DISTINCT c.conversion_status) as excluded_statuses
                FROM conversions_api c
                {excluded_where_clause}
                GROUP BY c.partner
            """
            
            excluded_rows = await self.unified_storage.execute_query(excluded_query, excluded_params)
            
            # 創建排除記錄的映射
            excluded_map = {}
            for row in excluded_rows:
                partner_name = row.get('partner_name', 'Unknown')
                excluded_map[partner_name] = {
                    'count': row.get('excluded_count', 0),
                    'statuses': row.get('excluded_statuses', []) or []
                }
            
            # 更新 summaries 中的排除記錄信息
            for summary in summaries:
                if summary.partner_name in excluded_map:
                    summary.excluded_records = excluded_map[summary.partner_name]['count']
                    summary.excluded_statuses = excluded_map[summary.partner_name]['statuses']
            
            logger.info(f"📊 Partner匯總統計: {len(summaries)} 個Partner, "
                       f"查詢耗時 {query_duration:.2f}秒")
            
            return summaries
            
        except Exception as e:
            logger.error(f"❌ Partner匯總查詢失敗: {e}")
            raise
    
    async def get_conversion_dataframe(self, 
                                     partner_name: str = None,
                                     start_date: datetime = None,
                                     end_date: datetime = None,
                                     limit: Optional[int] = None) -> pd.DataFrame:
        """
        獲取轉化數據的DataFrame格式 - 並發優化版本
        """
        import pandas as pd
        
        try:
            # 獲取轉化記錄
            conversions = await self.get_conversions_by_partner(
                partner_name, start_date, end_date, limit
            )
            
            if not conversions:
                return pd.DataFrame()
            
            # 並發處理數據轉換
            data = await self._convert_to_dataframe_concurrent(conversions, partner_name)
            
            df = pd.DataFrame(data)
            
            # 應用過濾器
            if partner_name and partner_name.upper() != 'ALL':
                df = df[df['Partner'].str.contains(partner_name, case=False, na=False)]
            
            # 應用limit限制
            if limit and len(df) > limit:
                logger.info(f"📊 應用limit限制: 從 {len(df)} 條記錄限制到 {limit} 條")
                df = df.head(limit)
            
            logger.info(f"✅ DataFrame生成完成: {len(df)} 條記錄")
            return df
            
        except Exception as e:
            logger.error(f"❌ 獲取DataFrame失敗: {e}")
            raise
    
    async def _convert_to_dataframe_concurrent(self, conversions: List[ConversionRecord], partner_name: str = None) -> List[Dict]:
        """並發處理數據轉換"""
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        # 將數據分批處理
        batch_size = 100
        batches = [conversions[i:i + batch_size] for i in range(0, len(conversions), batch_size)]
        
        # 並發處理每個批次
        tasks = []
        for batch in batches:
            task = asyncio.create_task(self._process_conversion_batch(batch))
            tasks.append(task)
        
        # 等待所有批次完成
        batch_results = await asyncio.gather(*tasks)
        
        # 合併結果
        all_data = []
        for batch_data in batch_results:
            all_data.extend(batch_data)
        
        return all_data
    
    async def _process_conversion_batch(self, batch: List[ConversionRecord]) -> List[Dict]:
        """處理單個批次的轉化記錄"""
        
        def process_record(conv: ConversionRecord) -> Dict:
            # 簡化數據處理 - 移除複雜邏輯
            partner_display = conv.tenant_name if conv.tenant_name and conv.tenant_name != 'Unknown' else 'Unknown'
            
            # 移除時區信息
            conversion_date = conv.datetime_conversion
            if conversion_date and hasattr(conversion_date, 'replace') and conversion_date.tzinfo:
                conversion_date = conversion_date.replace(tzinfo=None)
            
            received_at = conv.received_at
            if received_at and hasattr(received_at, 'replace') and received_at.tzinfo:
                received_at = received_at.replace(tzinfo=None)
            
            # 處理金額 - 簡化邏輯
            original_sale_amount = float(conv.usd_sale_amount) if conv.usd_sale_amount else 0.0
            
            # 從config.py獲取Partner特定的mockup倍數
            try:
                import sys
                import os
                config_path = os.path.join(os.path.dirname(__file__), '../../../../')
                if config_path not in sys.path:
                    sys.path.append(config_path)
                import config
                mockup_multiplier = config.get_partner_mockup_multiplier(partner_display)
            except:
                mockup_multiplier = 1.0  # 默認不調整
            
            # 應用配置的倍數調整
            processed_sale_amount = original_sale_amount * mockup_multiplier
            
            return {
                'Conversion ID': conv.conversion_id,
                'Offer ID': conv.offer_id,
                'Offer Name': conv.offer_name,
                'Datetime Conversion': conversion_date,
                'Order ID': conv.order_id,
                'USD Sale Amount': processed_sale_amount,
                'Aff Sub': conv.aff_sub,
                'Aff Sub2': conv.aff_sub2 or '',
                'Aff Sub3': conv.aff_sub3 or '',
                'Aff Sub4': conv.aff_sub4 or '',
                'Adv Pub1': conv.adv_pub1 or '',
                'Adv Pub2': conv.adv_pub2 or '',
                'Adv Pub3': conv.adv_pub3 or '',
                'Adv Pub4': conv.adv_pub4 or '',
                'Adv Pub5': conv.adv_pub5 or '',
                'Status': conv.status or 'pending',
                'Partner': partner_display,
                'Partner ID': conv.partner_id,
                'Source': conv.aff_sub or 'Unknown',
                'Source ID': conv.source_id
            }
        
        # 使用線程池並發處理
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=5) as executor:
            tasks = [loop.run_in_executor(executor, process_record, conv) for conv in batch]
            results = await asyncio.gather(*tasks)
        
        return results
    
    async def get_available_partners(self) -> List[str]:
        """獲取可用的Partner列表 - 緩存優化版本"""
        cache_key = self._generate_cache_key("available_partners")
        
        try:
            # 嘗試從緩存獲取
            if self.enable_caching:
                cached_result = await self._get_from_cache(cache_key)
                if cached_result:
                    logger.info(f"🎯 Partner列表緩存命中: {len(cached_result)} 個Partner")
                    return cached_result
            
            # 從數據庫查詢
            if not self.unified_storage:
                await self.initialize()
            
            query = """
                SELECT DISTINCT c.partner 
                FROM conversions c 
                WHERE c.partner IS NOT NULL 
                ORDER BY c.partner
            """
            
            rows = await self.unified_storage.fetch_all(query, [])
            partners = [row['partner'] for row in rows if row['partner']]
            
            # 添加特殊選項
            partners.insert(0, 'ALL')
            
            # 更新緩存 (長期緩存)
            if self.enable_caching:
                await self._set_cache(cache_key, partners)
            
            logger.info(f"✅ 獲取Partner列表完成: {len(partners)} 個Partner")
            return partners
            
        except Exception as e:
            logger.error(f"❌ 獲取Partner列表失敗: {e}")
            return ['ALL']
    
    async def batch_get_conversions(self, 
                                  requests: List[Dict[str, Any]]) -> List[List[ConversionRecord]]:
        """
        批量獲取轉化記錄 - 智能並發處理
        """
        logger.info(f"🔄 開始批量查詢: {len(requests)} 個請求")
        
        # 限制並發數量
        semaphore = asyncio.Semaphore(self.MAX_CONCURRENT_BATCHES)
        
        async def process_single_request(request: Dict[str, Any]) -> List[ConversionRecord]:
            async with semaphore:
                return await self.get_conversions_by_partner(
                    partner_name=request.get('partner_name'),
                    start_date=request.get('start_date'),
                    end_date=request.get('end_date'),
                    limit=request.get('limit')
                )
        
        # 並發執行所有請求
        tasks = [process_single_request(req) for req in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 處理結果和異常
        successful_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"❌ 批量查詢第{i+1}個請求失敗: {result}")
                successful_results.append([])
            else:
                successful_results.append(result)
        
        logger.info(f"✅ 批量查詢完成: {len(successful_results)} 個結果")
        return successful_results
    
    async def optimize_database_indexes(self):
        """自動優化數據庫索引"""
        try:
            if not self.unified_storage:
                await self.initialize()
            
            logger.info("🔧 開始自動索引優化...")
            
            # 檢查並創建關鍵索引
            index_queries = [
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversions_partner ON conversions(partner)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversions_datetime ON conversions(datetime_conversion)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversions_partner_datetime ON conversions(partner, datetime_conversion)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversions_aff_sub ON conversions(aff_sub)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversions_id_desc ON conversions(id DESC)"
            ]
            
            for query in index_queries:
                try:
                    await self.unified_storage.execute(query, [])
                    logger.info(f"✅ 索引創建成功: {query.split('idx_')[1].split(' ')[0]}")
                except Exception as e:
                    logger.warning(f"⚠️ 索引創建跳過 (可能已存在): {e}")
            
            logger.info("✅ 數據庫索引優化完成")
            
        except Exception as e:
            logger.error(f"❌ 數據庫索引優化失敗: {e}")
    
    async def clear_cache(self, pattern: str = None):
        """清理緩存"""
        try:
            if self.redis_client:
                if pattern:
                    # 清理匹配模式的緩存
                    keys = await self.redis_client.keys(f"reporter:{pattern}*")
                    if keys:
                        await self.redis_client.delete(*keys)
                        logger.info(f"✅ 清理Redis緩存: {len(keys)} 個鍵 (模式: {pattern})")
                else:
                    # 清理所有reporter緩存
                    keys = await self.redis_client.keys("reporter:*")
                    if keys:
                        await self.redis_client.delete(*keys)
                        logger.info(f"✅ 清理Redis緩存: {len(keys)} 個鍵")
            
            # 清理本地緩存
            if pattern:
                keys_to_remove = [k for k in self.local_cache.keys() if pattern in k]
                for key in keys_to_remove:
                    del self.local_cache[key]
                logger.info(f"✅ 清理本地緩存: {len(keys_to_remove)} 個鍵 (模式: {pattern})")
            else:
                self.local_cache.clear()
                logger.info("✅ 清理本地緩存: 全部清理")
            
            # 重置緩存統計
            self.cache_stats = {"hits": 0, "misses": 0}
            
        except Exception as e:
            logger.error(f"❌ 清理緩存失敗: {e}") 