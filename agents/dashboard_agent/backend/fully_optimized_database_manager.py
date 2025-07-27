#!/usr/bin/env python3
"""
完全優化的數據庫管理器
Fully Optimized Database Manager

結合企業級連接池、反N+1查詢管理、智能緩存的完整解決方案
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from .enhanced_connection_pool import EnhancedConnectionPool, ConnectionPoolConfig
from .anti_n_plus_one_manager import AntiNPlusOneManager
from ..cache.intelligent_cache_manager import IntelligentCacheManager

logger = logging.getLogger(__name__)

class FullyOptimizedDatabaseManager:
    """完全優化的數據庫管理器"""
    
    def __init__(self):
        # 企業級連接池配置
        pool_config = ConnectionPoolConfig(
            min_size=10,      # 增加到10個最小連接
            max_size=50,      # 增加到50個最大連接
            max_queries=50000, # 每個連接最大查詢數
            max_inactive_time=300,  # 5分鐘空閒超時
            command_timeout=60      # 60秒命令超時
        )
        
        # 初始化組件
        self.connection_pool = EnhancedConnectionPool(pool_config)
        self.anti_n_plus_one = AntiNPlusOneManager()
        self.cache_manager = IntelligentCacheManager()
        
        # 性能統計
        self._query_stats = {
            'total_queries': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'optimized_queries': 0,
            'avg_response_time': 0.0
        }
        
        self._response_times: List[float] = []
        self.is_initialized = False
    
    async def initialize(self):
        """初始化所有組件"""
        if self.is_initialized:
            return
        
        logger.info("🚀 初始化完全優化數據庫管理器...")
        
        try:
            # 並行初始化所有組件
            await asyncio.gather(
                self.connection_pool.initialize(),
                self.anti_n_plus_one.initialize(),
                self.cache_manager.initialize()
            )
            
            self.is_initialized = True
            logger.info("✅ 完全優化數據庫管理器初始化完成")
            
        except Exception as e:
            logger.error(f"❌ 數據庫管理器初始化失敗: {e}")
            raise
    
    # =================== 優化的查詢方法 ===================
    
    async def get_summary_data(self, start_date: str, end_date: str, 
                             partner_id: Optional[int] = None) -> Dict[str, Any]:
        """獲取總覽數據（完全優化版本）"""
        if not self.is_initialized:
            await self.initialize()
        
        start_time = time.time()
        cache_key = f"summary_data:{start_date}:{end_date}:{partner_id}"
        
        try:
            # 1. 嘗試從緩存獲取
            cached_result = await self.cache_manager.get(cache_key)
            if cached_result:
                self._update_stats('cache_hit', time.time() - start_time)
                return cached_result
            
            # 2. 使用反N+1查詢管理器執行優化查詢
            result = await self.anti_n_plus_one.get_summary_data_optimized(
                start_date, end_date, partner_id
            )
            
            # 3. 緩存結果
            if result:
                await self.cache_manager.set(cache_key, result, ttl=300)  # 5分鐘TTL
            
            execution_time = time.time() - start_time
            self._update_stats('cache_miss', execution_time)
            
            logger.info(f"✅ 總覽數據查詢完成: {execution_time:.3f}s (優化版)")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ 總覽數據查詢失敗: {execution_time:.3f}s - {e}")
            return {}
    
    async def get_daily_trend(self, start_date: str, end_date: str,
                            partner_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """獲取日趨勢數據（優化版本）"""
        if not self.is_initialized:
            await self.initialize()
        
        start_time = time.time()
        cache_key = f"daily_trend:{start_date}:{end_date}:{partner_id}"
        
        try:
            # 嘗試從緩存獲取
            cached_result = await self.cache_manager.get(cache_key)
            if cached_result:
                self._update_stats('cache_hit', time.time() - start_time)
                return cached_result
            
            # 從總覽數據中提取（已包含日趨勢）
            summary_data = await self.get_summary_data(start_date, end_date, partner_id)
            result = summary_data.get('daily_trend', [])
            
            # 獨立緩存日趨勢數據
            if result:
                await self.cache_manager.set(cache_key, result, ttl=600)  # 10分鐘TTL
            
            execution_time = time.time() - start_time
            self._update_stats('optimized_query', execution_time)
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ 日趨勢查詢失敗: {execution_time:.3f}s - {e}")
            return []
    
    async def get_hourly_trend(self, start_date: str, end_date: str,
                             partner_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """獲取小時趨勢數據（優化版本）"""
        if not self.is_initialized:
            await self.initialize()
        
        start_time = time.time()
        cache_key = f"hourly_trend:{start_date}:{end_date}:{partner_id}"
        
        try:
            # 嘗試從緩存獲取
            cached_result = await self.cache_manager.get(cache_key)
            if cached_result:
                self._update_stats('cache_hit', time.time() - start_time)
                return cached_result
            
            # 從總覽數據中提取（已包含小時趨勢）
            summary_data = await self.get_summary_data(start_date, end_date, partner_id)
            result = summary_data.get('hourly_trend', [])
            
            # 獨立緩存小時趨勢數據
            if result:
                await self.cache_manager.set(cache_key, result, ttl=1800)  # 30分鐘TTL
            
            execution_time = time.time() - start_time
            self._update_stats('optimized_query', execution_time)
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ 小時趨勢查詢失敗: {execution_time:.3f}s - {e}")
            return []
    
    async def get_conversion_details_optimized(self, start_date: str, end_date: str,
                                             partner_name: Optional[str] = None,
                                             page: int = 1, limit: int = 100) -> Dict[str, Any]:
        """獲取轉化詳情（完全優化版本）"""
        if not self.is_initialized:
            await self.initialize()
        
        start_time = time.time()
        cache_key = f"conversion_details:{start_date}:{end_date}:{partner_name}:{page}:{limit}"
        
        try:
            # 嘗試從緩存獲取
            cached_result = await self.cache_manager.get(cache_key)
            if cached_result:
                self._update_stats('cache_hit', time.time() - start_time)
                return cached_result
            
            # 使用反N+1查詢管理器執行優化查詢
            result = await self.anti_n_plus_one.get_conversion_details_optimized(
                start_date, end_date, partner_name, page, limit
            )
            
            # 緩存結果
            if result and result.get('records'):
                # 根據數據量動態調整TTL
                ttl = 300 if limit <= 100 else 180  # 小批量5分鐘，大批量3分鐘
                await self.cache_manager.set(cache_key, result, ttl=ttl)
            
            execution_time = time.time() - start_time
            self._update_stats('cache_miss', execution_time)
            
            logger.info(f"✅ 轉化詳情查詢完成: {execution_time:.3f}s, {len(result.get('records', []))} 條記錄")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ 轉化詳情查詢失敗: {execution_time:.3f}s - {e}")
            return {
                "records": [],
                "total": 0,
                "page": page,
                "limit": limit,
                "pages": 0
            }
    
    async def get_partner_performance(self, start_date: str, end_date: str,
                                    limit: int = 50) -> List[Dict[str, Any]]:
        """獲取合作夥伴表現（優化版本）"""
        if not self.is_initialized:
            await self.initialize()
        
        start_time = time.time()
        cache_key = f"partner_performance:{start_date}:{end_date}:{limit}"
        
        try:
            # 嘗試從緩存獲取
            cached_result = await self.cache_manager.get(cache_key)
            if cached_result:
                self._update_stats('cache_hit', time.time() - start_time)
                return cached_result
            
            # 使用批量查詢獲取表現數據
            performance_data = await self.anti_n_plus_one.get_performance_data_batch(
                start_date, end_date, None, limit
            )
            
            result = performance_data.get('partner_performance', [])
            
            # 緩存結果
            if result:
                await self.cache_manager.set(cache_key, result, ttl=600)  # 10分鐘TTL
            
            execution_time = time.time() - start_time
            self._update_stats('optimized_query', execution_time)
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ 合作夥伴表現查詢失敗: {execution_time:.3f}s - {e}")
            return []
    
    async def get_offer_performance(self, start_date: str, end_date: str,
                                  partner_id: Optional[int] = None,
                                  limit: int = 50) -> List[Dict[str, Any]]:
        """獲取 Offer 表現（優化版本）"""
        if not self.is_initialized:
            await self.initialize()
        
        start_time = time.time()
        cache_key = f"offer_performance:{start_date}:{end_date}:{partner_id}:{limit}"
        
        try:
            # 嘗試從緩存獲取
            cached_result = await self.cache_manager.get(cache_key)
            if cached_result:
                self._update_stats('cache_hit', time.time() - start_time)
                return cached_result
            
            # 使用批量查詢獲取表現數據
            performance_data = await self.anti_n_plus_one.get_performance_data_batch(
                start_date, end_date, partner_id, limit
            )
            
            result = performance_data.get('offer_performance', [])
            
            # 緩存結果
            if result:
                await self.cache_manager.set(cache_key, result, ttl=600)  # 10分鐘TTL
            
            execution_time = time.time() - start_time
            self._update_stats('optimized_query', execution_time)
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ Offer 表現查詢失敗: {execution_time:.3f}s - {e}")
            return []
    
    # =================== 批量操作 ===================
    
    async def get_dashboard_data_batch(self, start_date: str, end_date: str,
                                     partner_id: Optional[int] = None) -> Dict[str, Any]:
        """批量獲取 Dashboard 所有數據（超級優化版本）"""
        if not self.is_initialized:
            await self.initialize()
        
        start_time = time.time()
        cache_key = f"dashboard_batch:{start_date}:{end_date}:{partner_id}"
        
        try:
            # 嘗試從緩存獲取完整數據
            cached_result = await self.cache_manager.get(cache_key)
            if cached_result:
                self._update_stats('cache_hit', time.time() - start_time)
                return cached_result
            
            # 並行獲取所有數據
            tasks = [
                self.get_summary_data(start_date, end_date, partner_id),
                self.get_partner_performance(start_date, end_date, 20),
                self.get_offer_performance(start_date, end_date, partner_id, 20),
                self.get_conversion_details_optimized(start_date, end_date, None, 1, 10)
            ]
            
            summary_data, partner_performance, offer_performance, sample_conversions = await asyncio.gather(*tasks)
            
            # 組合結果
            result = {
                'summary': summary_data,
                'partner_performance': partner_performance,
                'offer_performance': offer_performance,
                'sample_conversions': sample_conversions,
                'generated_at': datetime.now().isoformat()
            }
            
            # 緩存完整結果
            await self.cache_manager.set(cache_key, result, ttl=600)  # 10分鐘TTL
            
            execution_time = time.time() - start_time
            self._update_stats('batch_query', execution_time)
            
            logger.info(f"✅ Dashboard 批量數據獲取完成: {execution_time:.3f}s")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ Dashboard 批量數據獲取失敗: {execution_time:.3f}s - {e}")
            return {}
    
    # =================== 緩存管理 ===================
    
    async def invalidate_cache(self, pattern: str = None):
        """失效緩存"""
        try:
            if pattern:
                await self.cache_manager.delete_pattern(pattern)
                logger.info(f"✅ 緩存模式失效: {pattern}")
            else:
                await self.cache_manager.clear()
                logger.info("✅ 所有緩存已清除")
        except Exception as e:
            logger.error(f"❌ 緩存失效失敗: {e}")
    
    async def warm_up_cache(self, start_date: str, end_date: str):
        """預熱緩存"""
        logger.info("🔥 開始緩存預熱...")
        
        try:
            # 預熱關鍵數據
            tasks = [
                self.get_summary_data(start_date, end_date),
                self.get_partner_performance(start_date, end_date),
                self.get_offer_performance(start_date, end_date),
            ]
            
            await asyncio.gather(*tasks, return_exceptions=True)
            
            logger.info("✅ 緩存預熱完成")
            
        except Exception as e:
            logger.error(f"❌ 緩存預熱失敗: {e}")
    
    # =================== 兼容性方法 ===================
    
    async def get_partners(self) -> List[Dict[str, Any]]:
        """獲取合作夥伴列表（簡化版本）"""
        cache_key = "active_partners"
        
        try:
            cached_result = await self.cache_manager.get(cache_key)
            if cached_result:
                return cached_result
            
            async with self.connection_pool.get_connection() as conn:
                query = """
                    SELECT DISTINCT partner as partner_name, partner as partner_code, true as is_active
                    FROM conversions
                    WHERE partner IS NOT NULL
                    ORDER BY partner
                """
                rows = await conn.fetch(query)
                result = [dict(row) for row in rows]
                
                # 緩存1小時
                await self.cache_manager.set(cache_key, result, ttl=3600)
                
                return result
                
        except Exception as e:
            logger.error(f"獲取合作夥伴失敗: {e}")
            return []
    
    # =================== 性能監控 ===================
    
    def _update_stats(self, query_type: str, execution_time: float):
        """更新統計數據"""
        self._query_stats['total_queries'] += 1
        self._response_times.append(execution_time)
        
        if query_type == 'cache_hit':
            self._query_stats['cache_hits'] += 1
        elif query_type == 'cache_miss':
            self._query_stats['cache_misses'] += 1
        elif query_type in ['optimized_query', 'batch_query']:
            self._query_stats['optimized_queries'] += 1
        
        # 保持最近1000次查詢記錄
        if len(self._response_times) > 1000:
            self._response_times = self._response_times[-1000:]
        
        # 計算平均響應時間
        self._query_stats['avg_response_time'] = sum(self._response_times) / len(self._response_times)
    
    async def get_performance_summary(self) -> Dict[str, Any]:
        """獲取性能摘要"""
        try:
            # 獲取各組件性能統計
            pool_stats = self.connection_pool.get_metrics()
            cache_stats = await self.cache_manager.get_stats()
            n_plus_one_stats = self.anti_n_plus_one.get_optimization_stats()
            
            # 計算緩存命中率
            total_cache_requests = self._query_stats['cache_hits'] + self._query_stats['cache_misses']
            cache_hit_rate = (self._query_stats['cache_hits'] / max(1, total_cache_requests)) * 100
            
            return {
                'overall_performance': {
                    'total_queries': self._query_stats['total_queries'],
                    'avg_response_time': f"{self._query_stats['avg_response_time']:.3f}s",
                    'cache_hit_rate': f"{cache_hit_rate:.1f}%",
                    'optimized_queries_ratio': f"{(self._query_stats['optimized_queries'] / max(1, self._query_stats['total_queries'])) * 100:.1f}%"
                },
                'connection_pool': pool_stats,
                'cache_performance': cache_stats,
                'query_optimization': n_plus_one_stats,
                'response_time_distribution': {
                    'fast_queries_(<0.1s)': len([t for t in self._response_times if t < 0.1]),
                    'medium_queries_(0.1-1s)': len([t for t in self._response_times if 0.1 <= t < 1.0]),
                    'slow_queries_(>1s)': len([t for t in self._response_times if t >= 1.0])
                } if self._response_times else {}
            }
            
        except Exception as e:
            logger.error(f"獲取性能摘要失敗: {e}")
            return {}
    
    async def test_connection(self) -> bool:
        """測試數據庫連接"""
        try:
            async with self.connection_pool.get_connection() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"數據庫連接測試失敗: {e}")
            return False
    
    async def close(self):
        """關閉所有組件"""
        try:
            await asyncio.gather(
                self.connection_pool.close(),
                self.cache_manager.close(),
                return_exceptions=True
            )
            logger.info("✅ 完全優化數據庫管理器已關閉")
        except Exception as e:
            logger.error(f"關閉數據庫管理器時出錯: {e}") 