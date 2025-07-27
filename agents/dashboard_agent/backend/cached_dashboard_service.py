#!/usr/bin/env python3
"""
帶緩存的 Dashboard Service
Cached Dashboard Service

集成智能緩存管理器的 Dashboard Service，大幅提升查詢性能
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from .dashboard_service import DashboardService
from .database_manager import DatabaseManager
from ..cache.intelligent_cache_manager import get_cache_manager, IntelligentCacheManager

logger = logging.getLogger(__name__)

class CachedDashboardService(DashboardService):
    """帶緩存的 Dashboard Service"""
    
    def __init__(self, db_manager: DatabaseManager, cache_config: Optional[Dict] = None):
        super().__init__(db_manager)
        self.cache_manager: Optional[IntelligentCacheManager] = None
        self.cache_config = cache_config or {
            'host': 'localhost',
            'port': 6379,
            'db': 1
        }
        self._initialized = False
    
    async def initialize_cache(self):
        """初始化緩存管理器"""
        if not self._initialized:
            self.cache_manager = await get_cache_manager(self.cache_config)
            self._initialized = True
            logger.info("✅ CachedDashboardService 初始化完成")
    
    # =================== 緩存版本的查詢方法 ===================
    
    async def get_summary_data(self, start_date: str, end_date: str, partner_id: Optional[int] = None) -> Dict[str, Any]:
        """獲取總覽數據（緩存版本）"""
        if not self._initialized:
            await self.initialize_cache()
        
        params = {
            'start_date': start_date,
            'end_date': end_date,
            'partner_id': partner_id
        }
        
        async def query_func():
            return await super().get_summary_data(start_date, end_date, partner_id)
        
        return await self.cache_manager.get_cached_result(
            'get_summary_data',
            params,
            query_func
        )
    
    async def get_company_level_data(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """獲取公司級別數據（緩存版本）"""
        if not self._initialized:
            await self.initialize_cache()
        
        params = {
            'start_date': start_date,
            'end_date': end_date
        }
        
        async def query_func():
            return await super().get_company_level_data(start_date, end_date)
        
        return await self.cache_manager.get_cached_result(
            'get_company_level_data',
            params,
            query_func
        )
    
    async def get_partner_level_data(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """獲取合作夥伴級別數據（緩存版本）"""
        if not self._initialized:
            await self.initialize_cache()
        
        params = {
            'start_date': start_date,
            'end_date': end_date
        }
        
        async def query_func():
            return await super().get_partner_level_data(start_date, end_date)
        
        return await self.cache_manager.get_cached_result(
            'get_partner_level_data',
            params,
            query_func
        )
    
    async def get_conversion_report_data(self, start_date: str, end_date: str, 
                                       partner_id: Optional[int] = None,
                                       page: int = 1, limit: int = 100) -> Dict[str, Any]:
        """獲取轉化報告數據（緩存版本）"""
        if not self._initialized:
            await self.initialize_cache()
        
        params = {
            'start_date': start_date,
            'end_date': end_date,
            'partner_id': partner_id,
            'page': page,
            'limit': limit
        }
        
        async def query_func():
            return await super().get_conversion_report_data(start_date, end_date, partner_id, page, limit)
        
        return await self.cache_manager.get_cached_result(
            'get_conversion_report_data',
            params,
            query_func
        )
    
    async def drill_data(self, data_type: str, filter_key: str, filter_value: str,
                        start_date: str, end_date: str) -> Dict[str, Any]:
        """數據鑽取服務（緩存版本）"""
        if not self._initialized:
            await self.initialize_cache()
        
        params = {
            'data_type': data_type,
            'filter_key': filter_key,
            'filter_value': filter_value,
            'start_date': start_date,
            'end_date': end_date
        }
        
        async def query_func():
            return await super().drill_data(data_type, filter_key, filter_value, start_date, end_date)
        
        return await self.cache_manager.get_cached_result(
            'drill_data',
            params,
            query_func
        )
    
    # =================== 緩存管理方法 ===================
    
    async def invalidate_cache(self, pattern: Optional[str] = None):
        """使緩存失效"""
        if self.cache_manager:
            await self.cache_manager.invalidate_cache(pattern)
            logger.info(f"✅ 緩存失效完成: {pattern or '全部'}")
    
    async def get_cache_statistics(self) -> Dict[str, Any]:
        """獲取緩存統計信息"""
        if not self.cache_manager:
            return {"error": "緩存管理器未初始化"}
        
        stats = self.cache_manager.get_cache_stats()
        
        # 添加業務相關的統計
        business_stats = {
            'dashboard_queries': {
                'summary_data': self._get_query_frequency('get_summary_data'),
                'company_level': self._get_query_frequency('get_company_level_data'),
                'partner_level': self._get_query_frequency('get_partner_level_data'),
                'conversion_report': self._get_query_frequency('get_conversion_report_data'),
                'drill_data': self._get_query_frequency('drill_data')
            },
            'performance_impact': {
                'queries_accelerated': stats['metrics']['hits'],
                'time_saved_total': f"{stats['metrics']['total_time_saved']:.2f}s",
                'estimated_cost_savings': self._calculate_cost_savings(stats['metrics'])
            }
        }
        
        return {
            'cache_stats': stats,
            'business_stats': business_stats,
            'recommendations': self._get_optimization_recommendations()
        }
    
    def _get_query_frequency(self, query_type: str) -> Dict[str, Any]:
        """獲取查詢頻率統計"""
        if not self.cache_manager or query_type not in self.cache_manager.query_patterns:
            return {'frequency': 0, 'last_access': None}
        
        pattern = self.cache_manager.query_patterns[query_type]
        return {
            'frequency': pattern['frequency'],
            'last_access': datetime.fromtimestamp(pattern['last_access']).isoformat(),
            'common_params': pattern.get('common_params', {})
        }
    
    def _calculate_cost_savings(self, metrics: Dict[str, Any]) -> str:
        """計算成本節省"""
        # 假設每秒查詢成本 $0.001（AWS RDS 概算）
        time_saved = metrics.get('total_time_saved', 0)
        cost_per_second = 0.001
        savings = time_saved * cost_per_second
        return f"${savings:.4f}"
    
    def _get_optimization_recommendations(self) -> List[str]:
        """獲取優化建議"""
        recommendations = []
        
        if not self.cache_manager:
            return ["請初始化緩存管理器"]
        
        stats = self.cache_manager.metrics
        
        if stats.hit_rate < 0.5:
            recommendations.append("緩存命中率較低，考慮調整 TTL 策略")
        
        if stats.total_queries > 100 and stats.avg_time_saved < 0.5:
            recommendations.append("平均時間節省較少，考慮優化查詢邏輯")
        
        if len(self.cache_manager.l1_cache) >= self.cache_manager.cache_config['l1_max_size'] * 0.9:
            recommendations.append("L1 緩存接近滿載，考慮增加容量")
        
        if not recommendations:
            recommendations.append("緩存系統運行良好，無需特別優化")
        
        return recommendations
    
    # =================== 批量優化方法 ===================
    
    async def batch_warm_cache(self, date_ranges: List[tuple], partner_ids: List[int] = None):
        """批量預熱緩存"""
        logger.info("🔥 開始批量預熱緩存...")
        
        if not self._initialized:
            await self.initialize_cache()
        
        tasks = []
        
        for start_date, end_date in date_ranges:
            # 為每個日期範圍預熱主要查詢
            tasks.extend([
                self.get_summary_data(start_date, end_date),
                self.get_company_level_data(start_date, end_date),
                self.get_partner_level_data(start_date, end_date)
            ])
            
            # 如果指定了合作夥伴，也預熱合作夥伴特定的查詢
            if partner_ids:
                for partner_id in partner_ids:
                    tasks.append(
                        self.get_summary_data(start_date, end_date, partner_id)
                    )
        
        # 並行執行預熱任務
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        success_count = sum(1 for r in results if not isinstance(r, Exception))
        logger.info(f"✅ 緩存預熱完成: {success_count}/{len(tasks)} 成功")
        
        return {
            'total_tasks': len(tasks),
            'successful': success_count,
            'failed': len(tasks) - success_count
        }
    
    async def refresh_today_cache(self):
        """刷新今日數據緩存"""
        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # 使相關緩存失效
        await self.invalidate_cache(today)
        await self.invalidate_cache(yesterday)
        
        # 重新載入今日數據
        return await self.batch_warm_cache([(today, today), (yesterday, yesterday)])

# =================== 工廠函數 ===================

async def create_cached_dashboard_service(db_manager: DatabaseManager, 
                                        cache_config: Optional[Dict] = None) -> CachedDashboardService:
    """創建帶緩存的 Dashboard Service"""
    service = CachedDashboardService(db_manager, cache_config)
    await service.initialize_cache()
    return service 