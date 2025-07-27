#!/usr/bin/env python3
"""
反N+1查詢管理器
Anti N+1 Query Manager

解決N+1查詢問題，提供批量查詢和關聯查詢優化
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
from datetime import datetime, date
from collections import defaultdict

from .enhanced_connection_pool import get_global_pool

logger = logging.getLogger(__name__)

@dataclass
class QueryBatch:
    """查詢批次"""
    batch_id: str
    queries: List[str]
    params: List[List[Any]]
    expected_results: int
    created_at: datetime

@dataclass  
class BatchResult:
    """批次結果"""
    batch_id: str
    results: List[List[Dict]]
    execution_time: float
    total_records: int

class AntiNPlusOneManager:
    """反N+1查詢管理器"""
    
    def __init__(self):
        self.pool = None
        self._batch_cache: Dict[str, BatchResult] = {}
        self._query_patterns: Dict[str, str] = {}
        self._register_optimized_patterns()
    
    def _register_optimized_patterns(self):
        """註冊優化的查詢模式"""
        self._query_patterns = {
            # 總覽數據 - 合併為單一查詢
            'summary_metrics_and_trends': '''
                WITH summary_base AS (
                    SELECT 
                        COUNT(*) as total_conversions,
                        SUM(COALESCE(sale_amount, usd_sale_amount, 0)) as total_sales,
                        SUM(COALESCE(payout, usd_payout, 0)) as total_payout,
                        AVG(COALESCE(sale_amount, usd_sale_amount, 0)) as avg_sale_amount,
                        COUNT(DISTINCT partner_id) as unique_partners,
                        COUNT(DISTINCT offer_name) as unique_offers,
                        COUNT(DISTINCT aff_sub) as unique_sub_ids
                    FROM conversions
                    WHERE datetime_conversion >= $1 AND datetime_conversion < $2
                    AND ($3::int IS NULL OR partner_id = $3)
                ),
                daily_trend AS (
                    SELECT 
                        DATE(datetime_conversion) as date,
                        COUNT(*) as conversions,
                        SUM(COALESCE(sale_amount, usd_sale_amount, 0)) as total_sales,
                        SUM(COALESCE(payout, usd_payout, 0)) as total_payout
                    FROM conversions
                    WHERE datetime_conversion >= $1 AND datetime_conversion < $2
                    AND ($3::int IS NULL OR partner_id = $3)
                    GROUP BY DATE(datetime_conversion)
                    ORDER BY date
                ),
                hourly_trend AS (
                    SELECT 
                        EXTRACT(hour FROM datetime_conversion) as hour,
                        COUNT(*) as conversions,
                        SUM(COALESCE(sale_amount, usd_sale_amount, 0)) as total_sales
                    FROM conversions
                    WHERE datetime_conversion >= $1 AND datetime_conversion < $2
                    AND ($3::int IS NULL OR partner_id = $3)
                    GROUP BY EXTRACT(hour FROM datetime_conversion)
                    ORDER BY hour
                )
                SELECT 
                    'summary' as data_type,
                    json_build_object(
                        'total_conversions', s.total_conversions,
                        'total_sales', s.total_sales,
                        'total_payout', s.total_payout,
                        'avg_sale_amount', s.avg_sale_amount,
                        'unique_partners', s.unique_partners,
                        'unique_offers', s.unique_offers,
                        'unique_sub_ids', s.unique_sub_ids
                    ) as data
                FROM summary_base s
                UNION ALL
                SELECT 
                    'daily_trend' as data_type,
                    json_agg(
                        json_build_object(
                            'date', d.date,
                            'conversions', d.conversions,
                            'total_sales', d.total_sales,
                            'total_payout', d.total_payout
                        ) ORDER BY d.date
                    ) as data
                FROM daily_trend d
                UNION ALL
                SELECT 
                    'hourly_trend' as data_type,
                    json_agg(
                        json_build_object(
                            'hour', h.hour,
                            'conversions', h.conversions,
                            'total_sales', h.total_sales
                        ) ORDER BY h.hour
                    ) as data
                FROM hourly_trend h
            ''',
            
            # 轉化詳情 - 單查詢獲取總數和數據
            'conversion_details_optimized': '''
                WITH filtered_data AS (
                    SELECT c.*
                    FROM conversions c
                    WHERE datetime_conversion >= $1 AND datetime_conversion < $2
                    AND ($3::text IS NULL OR partner = $3)
                ),
                summary_stats AS (
                    SELECT 
                        COUNT(*) as total_conversions,
                        COALESCE(SUM(COALESCE(sale_amount, usd_sale_amount, 0)), 0) as total_sale_amount,
                        COALESCE(AVG(COALESCE(commission_rate, 0)), 0) as avg_commission_rate
                    FROM filtered_data
                )
                SELECT 
                    'stats' as data_type,
                    json_build_object(
                        'total', s.total_conversions,
                        'total_sale_amount', s.total_sale_amount,
                        'avg_commission_rate', s.avg_commission_rate
                    ) as data
                FROM summary_stats s
                UNION ALL
                SELECT 
                    'records' as data_type,
                    json_agg(
                        json_build_object(
                            'platform', COALESCE(c.platform, ''),
                            'partner', COALESCE(c.partner, ''),
                            'source', COALESCE(c.source, ''),
                            'conversion_id', COALESCE(c.conversion_id, ''),
                            'datetime_conversion', c.datetime_conversion,
                            'offer_name', COALESCE(c.offer_name, ''),
                            'usd_sale_amount', COALESCE(c.sale_amount, c.usd_sale_amount, 0),
                            'usd_payout', COALESCE(c.payout, c.usd_payout, 0),
                            'sub_id', COALESCE(c.aff_sub, ''),
                            'media_id', COALESCE(c.aff_sub, ''),
                            'click_id', COALESCE(c.click_id, '')
                        ) ORDER BY c.datetime_conversion DESC
                    ) as data
                FROM (
                    SELECT c.*
                    FROM filtered_data c
                    ORDER BY c.datetime_conversion DESC
                    LIMIT $4 OFFSET $5
                ) c
            ''',
            
            # 合作夥伴和Offer表現 - 批量查詢
            'performance_data_batch': '''
                SELECT 
                    'partner_performance' as data_type,
                    json_agg(
                        json_build_object(
                            'partner', partner,
                            'conversions', conversions,
                            'total_sales', total_sales,
                            'total_payout', total_payout,
                            'avg_sale_amount', avg_sale_amount,
                            'unique_offers', unique_offers,
                            'first_conversion', first_conversion,
                            'last_conversion', last_conversion
                        ) ORDER BY conversions DESC
                    ) as data
                FROM (
                    SELECT 
                        partner,
                        COUNT(*) as conversions,
                        SUM(COALESCE(sale_amount, usd_sale_amount, 0)) as total_sales,
                        SUM(COALESCE(payout, usd_payout, 0)) as total_payout,
                        AVG(COALESCE(sale_amount, usd_sale_amount, 0)) as avg_sale_amount,
                        COUNT(DISTINCT offer_name) as unique_offers,
                        MIN(datetime_conversion) as first_conversion,
                        MAX(datetime_conversion) as last_conversion
                    FROM conversions
                    WHERE datetime_conversion >= $1 AND datetime_conversion < $2
                    AND partner IS NOT NULL
                    GROUP BY partner
                    ORDER BY conversions DESC
                    LIMIT $3
                ) p
                UNION ALL
                SELECT 
                    'offer_performance' as data_type,
                    json_agg(
                        json_build_object(
                            'offer_name', offer_name,
                            'conversions', conversions,
                            'total_sales', total_sales,
                            'total_payout', total_payout,
                            'avg_sale_amount', avg_sale_amount,
                            'unique_sub_ids', unique_sub_ids,
                            'first_conversion', first_conversion,
                            'last_conversion', last_conversion
                        ) ORDER BY conversions DESC
                    ) as data
                FROM (
                    SELECT 
                        offer_name,
                        COUNT(*) as conversions,
                        SUM(COALESCE(sale_amount, usd_sale_amount, 0)) as total_sales,
                        SUM(COALESCE(payout, usd_payout, 0)) as total_payout,
                        AVG(COALESCE(sale_amount, usd_sale_amount, 0)) as avg_sale_amount,
                        COUNT(DISTINCT aff_sub) as unique_sub_ids,
                        MIN(datetime_conversion) as first_conversion,
                        MAX(datetime_conversion) as last_conversion
                    FROM conversions
                    WHERE datetime_conversion >= $1 AND datetime_conversion < $2
                    AND offer_name IS NOT NULL
                    AND ($4::int IS NULL OR partner_id = $4)
                    GROUP BY offer_name
                    ORDER BY conversions DESC
                    LIMIT $3
                ) o
            '''
        }
    
    async def initialize(self):
        """初始化管理器"""
        if self.pool is None:
            self.pool = await get_global_pool()
            logger.info("✅ 反N+1查詢管理器初始化完成")
    
    async def get_summary_data_optimized(self, start_date: str, end_date: str, 
                                       partner_id: Optional[int] = None) -> Dict[str, Any]:
        """獲取總覽數據（優化版，單查詢）"""
        if not self.pool:
            await self.initialize()
        
        start_time = time.time()
        
        try:
            start_date_obj = self._parse_date(start_date)
            end_date_obj = self._parse_date(end_date)
            
            query = self._query_patterns['summary_metrics_and_trends']
            params = [start_date_obj, end_date_obj, partner_id]
            
            rows = await self.pool.execute_query(query, *params)
            
            # 解析結果
            result = {
                "metrics": {},
                "daily_trend": [],
                "hourly_trend": []
            }
            
            for row in rows:
                data_type = row['data_type']
                data = row['data']
                
                if data_type == 'summary':
                    result['metrics'] = data
                elif data_type == 'daily_trend':
                    result['daily_trend'] = data or []
                elif data_type == 'hourly_trend':
                    result['hourly_trend'] = data or []
            
            # 計算衍生指標
            result['metrics'] = self._process_summary_metrics(result['metrics'])
            result['top_hours'] = self._get_top_hours(result['hourly_trend'])
            result['growth_rate'] = self._calculate_growth_rate(result['daily_trend'])
            
            execution_time = time.time() - start_time
            logger.info(f"✅ 總覽數據優化查詢完成: {execution_time:.3f}s")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ 總覽數據優化查詢失敗: {execution_time:.3f}s - {e}")
            return {}
    
    async def get_conversion_details_optimized(self, start_date: str, end_date: str,
                                             partner_name: Optional[str] = None,
                                             page: int = 1, limit: int = 100) -> Dict[str, Any]:
        """獲取轉化詳情（優化版，單查詢）"""
        if not self.pool:
            await self.initialize()
        
        start_time = time.time()
        
        try:
            start_date_obj = self._parse_date(start_date)
            end_date_obj = self._parse_date(end_date)
            offset = (page - 1) * limit
            
            query = self._query_patterns['conversion_details_optimized']
            params = [start_date_obj, end_date_obj, partner_name, limit, offset]
            
            rows = await self.pool.execute_query(query, *params)
            
            # 解析結果
            result = {
                "records": [],
                "total": 0,
                "total_sale_amount": 0,
                "avg_commission_rate": 0,
                "page": page,
                "limit": limit,
                "pages": 0
            }
            
            for row in rows:
                data_type = row['data_type']
                data = row['data']
                
                if data_type == 'stats':
                    result['total'] = data['total']
                    result['total_sale_amount'] = data['total_sale_amount']
                    result['avg_commission_rate'] = data['avg_commission_rate']
                    result['pages'] = (data['total'] + limit - 1) // limit if data['total'] > 0 else 0
                elif data_type == 'records':
                    result['records'] = data or []
            
            execution_time = time.time() - start_time
            logger.info(f"✅ 轉化詳情優化查詢完成: {execution_time:.3f}s, {len(result['records'])} 條記錄")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ 轉化詳情優化查詢失敗: {execution_time:.3f}s - {e}")
            return {
                "records": [],
                "total": 0,
                "page": page,
                "limit": limit,
                "pages": 0
            }
    
    async def get_performance_data_batch(self, start_date: str, end_date: str,
                                       partner_id: Optional[int] = None,
                                       limit: int = 50) -> Dict[str, Any]:
        """批量獲取表現數據（合作夥伴和Offer）"""
        if not self.pool:
            await self.initialize()
        
        start_time = time.time()
        
        try:
            start_date_obj = self._parse_date(start_date)
            end_date_obj = self._parse_date(end_date)
            
            query = self._query_patterns['performance_data_batch']
            params = [start_date_obj, end_date_obj, limit, partner_id]
            
            rows = await self.pool.execute_query(query, *params)
            
            # 解析結果
            result = {
                "partner_performance": [],
                "offer_performance": []
            }
            
            for row in rows:
                data_type = row['data_type']
                data = row['data']
                
                if data_type == 'partner_performance':
                    result['partner_performance'] = data or []
                elif data_type == 'offer_performance':
                    result['offer_performance'] = data or []
            
            execution_time = time.time() - start_time
            logger.info(f"✅ 表現數據批量查詢完成: {execution_time:.3f}s")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ 表現數據批量查詢失敗: {execution_time:.3f}s - {e}")
            return {
                "partner_performance": [],
                "offer_performance": []
            }
    
    async def execute_batched_queries(self, queries: List[Tuple[str, List[Any]]]) -> List[List[Dict]]:
        """執行批量查詢"""
        if not self.pool:
            await self.initialize()
        
        start_time = time.time()
        
        try:
            # 並行執行所有查詢
            tasks = []
            for query, params in queries:
                task = self.pool.execute_query(query, *params)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            
            # 轉換結果
            processed_results = []
            for result in results:
                processed_results.append([dict(row) for row in result])
            
            execution_time = time.time() - start_time
            logger.info(f"✅ 批量查詢完成: {len(queries)} 個查詢, {execution_time:.3f}s")
            
            return processed_results
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ 批量查詢失敗: {execution_time:.3f}s - {e}")
            return []
    
    def _parse_date(self, date_str: str) -> date:
        """解析日期字符串"""
        try:
            if isinstance(date_str, str):
                return datetime.strptime(date_str, '%Y-%m-%d').date()
            elif isinstance(date_str, date):
                return date_str
            elif isinstance(date_str, datetime):
                return date_str.date()
            else:
                raise ValueError(f"無法解析日期格式: {date_str}")
        except Exception as e:
            logger.error(f"日期解析失敗: {e}")
            raise ValueError(f"日期格式錯誤: {date_str}，期望格式: YYYY-MM-DD")
    
    def _process_summary_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """處理總覽指標"""
        if not metrics:
            return {}
        
        processed = dict(metrics)
        
        # 計算平均每個合作夥伴的轉化數
        if metrics.get('unique_partners', 0) > 0:
            processed['avg_conversions_per_partner'] = metrics['total_conversions'] / metrics['unique_partners']
        else:
            processed['avg_conversions_per_partner'] = 0
        
        # 計算每個offer的平均轉化數
        if metrics.get('unique_offers', 0) > 0:
            processed['avg_conversions_per_offer'] = metrics['total_conversions'] / metrics['unique_offers']
        else:
            processed['avg_conversions_per_offer'] = 0
        
        # 計算利潤率
        if metrics.get('total_sales', 0) > 0:
            processed['profit_margin'] = (metrics['total_payout'] / metrics['total_sales']) * 100
        else:
            processed['profit_margin'] = 0
        
        return processed
    
    def _get_top_hours(self, hourly_trend: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """獲取表現最好的小時"""
        if not hourly_trend:
            return []
        
        sorted_hours = sorted(hourly_trend, key=lambda x: x.get('conversions', 0), reverse=True)
        return sorted_hours[:5]
    
    def _calculate_growth_rate(self, daily_trend: List[Dict[str, Any]]) -> Dict[str, Any]:
        """計算增長率"""
        if len(daily_trend) < 2:
            return {"daily_growth": 0, "trend": "stable"}
        
        # 計算最近兩天的增長率
        latest_day = daily_trend[-1]['conversions']
        previous_day = daily_trend[-2]['conversions']
        
        if previous_day > 0:
            growth_rate = ((latest_day - previous_day) / previous_day) * 100
        else:
            growth_rate = 0
        
        trend = "up" if growth_rate > 5 else "down" if growth_rate < -5 else "stable"
        
        return {
            "daily_growth": round(growth_rate, 2),
            "trend": trend
        }
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """獲取優化統計"""
        return {
            "registered_patterns": len(self._query_patterns),
            "cache_size": len(self._batch_cache),
            "available_optimizations": list(self._query_patterns.keys())
        } 