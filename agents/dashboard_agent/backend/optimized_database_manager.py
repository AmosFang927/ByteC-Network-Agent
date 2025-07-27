#!/usr/bin/env python3
"""
優化數據庫管理器
Optimized Database Manager

集成準備語句池和智能分批處理的數據庫管理器
"""

import os
import asyncio
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta, date

from .optimized_query_manager import OptimizedQueryManager, BatchConfig

logger = logging.getLogger(__name__)

class OptimizedDatabaseManager:
    """優化數據庫管理器"""
    
    def __init__(self):
        self.db_config = {
            "host": os.getenv("DB_HOST", "34.124.206.16"),
            "port": int(os.getenv("DB_PORT", "5432")),
            "database": os.getenv("DB_NAME", "postback_db"),
            "user": os.getenv("DB_USER", "postback_admin"),
            "password": os.getenv("DB_PASSWORD", "ByteC2024PostBack_CloudSQL")
        }
        
        self.query_manager = OptimizedQueryManager(self.db_config)
        self._initialized = False
    
    async def initialize(self):
        """初始化管理器"""
        if not self._initialized:
            self._initialized = True
            logger.info("✅ 優化數據庫管理器初始化完成")
    
    def _parse_date(self, date_str: str) -> date:
        """將字符串日期轉換為date對象"""
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
    
    # =================== 優化的查詢方法 ===================
    
    async def get_summary_metrics(self, start_date: str, end_date: str, 
                                partner_id: Optional[int] = None) -> Dict[str, Any]:
        """獲取總覽指標（優化版本）"""
        try:
            if not self._initialized:
                await self.initialize()
            
            start_date_obj = self._parse_date(start_date)
            end_date_obj = self._parse_date(end_date)
            
            params = [start_date_obj, end_date_obj, partner_id]
            
            result = await self.query_manager.execute_template_query(
                'summary_metrics', params
            )
            
            return dict(result[0]) if result else {}
            
        except Exception as e:
            logger.error(f"獲取總覽指標失敗: {e}")
            return {}
    
    async def get_daily_trend(self, start_date: str, end_date: str, 
                            partner_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """獲取日趨勢數據（優化版本）"""
        try:
            if not self._initialized:
                await self.initialize()
            
            start_date_obj = self._parse_date(start_date)
            end_date_obj = self._parse_date(end_date)
            
            params = [start_date_obj, end_date_obj, partner_id]
            
            return await self.query_manager.execute_template_query(
                'daily_trend', params
            )
            
        except Exception as e:
            logger.error(f"獲取日趨勢失敗: {e}")
            return []
    
    async def get_hourly_trend(self, start_date: str, end_date: str, 
                             partner_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """獲取小時趨勢數據（優化版本）"""
        try:
            if not self._initialized:
                await self.initialize()
            
            start_date_obj = self._parse_date(start_date)
            end_date_obj = self._parse_date(end_date)
            
            params = [start_date_obj, end_date_obj, partner_id]
            
            return await self.query_manager.execute_template_query(
                'hourly_trend', params
            )
            
        except Exception as e:
            logger.error(f"獲取小時趨勢失敗: {e}")
            return []
    
    async def get_partner_performance(self, start_date: str, end_date: str, 
                                    limit: int = 50) -> List[Dict[str, Any]]:
        """獲取合作夥伴表現（優化版本）"""
        try:
            if not self._initialized:
                await self.initialize()
            
            start_date_obj = self._parse_date(start_date)
            end_date_obj = self._parse_date(end_date)
            
            params = [start_date_obj, end_date_obj, limit]
            
            return await self.query_manager.execute_template_query(
                'partner_performance', params
            )
            
        except Exception as e:
            logger.error(f"獲取合作夥伴表現失敗: {e}")
            return []
    
    async def get_offer_performance(self, start_date: str, end_date: str, 
                                  partner_id: Optional[int] = None,
                                  limit: int = 50) -> List[Dict[str, Any]]:
        """獲取 Offer 表現（優化版本）"""
        try:
            if not self._initialized:
                await self.initialize()
            
            start_date_obj = self._parse_date(start_date)
            end_date_obj = self._parse_date(end_date)
            
            params = [start_date_obj, end_date_obj, partner_id, limit]
            
            return await self.query_manager.execute_template_query(
                'offer_performance', params
            )
            
        except Exception as e:
            logger.error(f"獲取 Offer 表現失敗: {e}")
            return []
    
    async def get_conversion_details_optimized(self, start_date: str, end_date: str,
                                             partner_name: Optional[str] = None,
                                             page: int = 1, limit: int = 100) -> Dict[str, Any]:
        """獲取轉化詳情（優化版本，分批處理）"""
        try:
            if not self._initialized:
                await self.initialize()
            
            start_date_obj = self._parse_date(start_date)
            end_date_obj = self._parse_date(end_date)
            
            # 計算偏移量
            offset = (page - 1) * limit
            
            # 先獲取總數
            count_params = [start_date_obj, end_date_obj, partner_name]
            total_result = await self.query_manager.execute_template_query(
                'conversion_details_count', count_params
            )
            total_conversions = total_result[0]['total'] if total_result else 0
            
            # 獲取數據
            data_params = [start_date_obj, end_date_obj, partner_name, limit, offset]
            records = await self.query_manager.execute_template_query(
                'conversion_details_data', data_params
            )
            
            return {
                "records": records,
                "total": total_conversions,
                "page": page,
                "limit": limit,
                "pages": (total_conversions + limit - 1) // limit if total_conversions > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"獲取轉化詳情失敗: {e}")
            return {
                "records": [],
                "total": 0,
                "page": page,
                "limit": limit,
                "pages": 0
            }
    
    async def get_large_dataset_batched(self, start_date: str, end_date: str,
                                      partner_name: Optional[str] = None,
                                      batch_size: int = 2000) -> List[Dict[str, Any]]:
        """獲取大數據集（智能分批處理）"""
        try:
            if not self._initialized:
                await self.initialize()
            
            start_date_obj = self._parse_date(start_date)
            end_date_obj = self._parse_date(end_date)
            
            params = [start_date_obj, end_date_obj, partner_name]
            
            # 使用分批處理獲取所有數據
            all_records = await self.query_manager.execute_large_query_batched(
                'conversion_details_data_unbounded',  # 需要新增無限制版本的模板
                'conversion_details_count',
                params,
                processor_func=self._process_conversion_record
            )
            
            return all_records
            
        except Exception as e:
            logger.error(f"分批獲取大數據集失敗: {e}")
            return []
    
    def _process_conversion_record(self, records: List[Dict]) -> List[Dict]:
        """處理轉化記錄"""
        processed = []
        
        for record in records:
            # 數據清理和轉換
            processed_record = {
                'platform': record.get('platform', ''),
                'partner': record.get('partner', ''),
                'source': record.get('source', ''),
                'conversion_id': record.get('conversion_id', ''),
                'datetime_conversion': record.get('datetime_conversion'),
                'offer_name': record.get('offer_name', ''),
                'usd_sale_amount': float(record.get('usd_sale_amount', 0)),
                'usd_payout': float(record.get('usd_payout', 0)),
                'sub_id': record.get('sub_id', ''),
                'media_id': record.get('media_id', ''),
                'click_id': record.get('click_id', '')
            }
            
            processed.append(processed_record)
        
        return processed
    
    # =================== 兼容性方法 ===================
    
    async def test_connection(self) -> bool:
        """測試數據庫連接"""
        try:
            conn = await self.query_manager.get_connection()
            # 簡單測試查詢
            await conn.fetchval("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"數據庫連接測試失敗: {e}")
            return False
    
    async def get_partners(self) -> List[Dict[str, Any]]:
        """獲取合作夥伴列表（簡化版本）"""
        try:
            conn = await self.query_manager.get_connection()
            query = """
                SELECT DISTINCT partner as partner_name, partner as partner_code, true as is_active
                FROM conversions
                WHERE partner IS NOT NULL
                ORDER BY partner
            """
            rows = await conn.fetch(query)
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"獲取合作夥伴失敗: {e}")
            return []
    
    # =================== 性能監控 ===================
    
    async def get_optimization_stats(self) -> Dict[str, Any]:
        """獲取優化統計數據"""
        return await self.query_manager.get_performance_summary()
    
    async def close(self):
        """關閉數據庫管理器"""
        await self.query_manager.close()
        logger.info("✅ 優化數據庫管理器已關閉") 