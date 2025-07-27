#!/usr/bin/env python3
"""
ByteC 轉換數據清理服務
在應用層提供智能數據標準化，避免視圖計算開銷
"""

import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)

@dataclass
class CleaningRules:
    """數據清理規則配置"""
    # 時間欄位優先級
    datetime_priority: List[str] = None
    
    # 金額欄位優先級  
    amount_priority: List[str] = None
    
    # 默認值設置
    default_currency: str = "USD"
    default_status: str = "completed"
    
    # 數據驗證規則
    validate_amounts: bool = True
    validate_dates: bool = True
    
    def __post_init__(self):
        if self.datetime_priority is None:
            self.datetime_priority = ['datetime_conversion', 'created_at', 'event_time']
        
        if self.amount_priority is None:
            self.amount_priority = ['sale_amount', 'usd_sale_amount']

class ConversionsDataCleaner:
    """轉換數據清理服務"""
    
    def __init__(self, rules: CleaningRules = None):
        """
        初始化數據清理器
        
        Args:
            rules: 清理規則配置
        """
        self.rules = rules or CleaningRules()
        self.cleaning_stats = {
            'processed_records': 0,
            'cleaned_fields': {},
            'validation_errors': 0,
            'performance_metrics': []
        }
    
    def clean_single_record(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        清理單條記錄
        
        Args:
            raw_data: 原始數據記錄
            
        Returns:
            清理後的數據記錄
        """
        start_time = datetime.now()
        cleaned_data = raw_data.copy()
        
        try:
            # 1. 時間欄位標準化
            cleaned_data['conversion_datetime'] = self._standardize_datetime(raw_data)
            
            # 2. 金額欄位標準化
            usd_sale, usd_payout = self._standardize_amounts(raw_data)
            cleaned_data['usd_sale_amount'] = usd_sale
            cleaned_data['usd_payout'] = usd_payout
            
            # 3. 貨幣標準化
            cleaned_data['currency'] = self._standardize_currency(raw_data)
            
            # 4. 狀態標準化
            cleaned_data['status'] = self._standardize_status(raw_data)
            
            # 5. 數據驗證
            self._validate_cleaned_data(cleaned_data)
            
            # 6. 記錄統計
            self.cleaning_stats['processed_records'] += 1
            processing_time = (datetime.now() - start_time).total_seconds()
            self.cleaning_stats['performance_metrics'].append(processing_time)
            
            return cleaned_data
            
        except Exception as e:
            logger.warning(f"數據清理失敗: {e}")
            self.cleaning_stats['validation_errors'] += 1
            return raw_data
    
    def clean_batch_records(self, raw_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        批量清理記錄
        
        Args:
            raw_records: 原始數據記錄列表
            
        Returns:
            清理後的數據記錄列表
        """
        start_time = datetime.now()
        cleaned_records = []
        
        for record in raw_records:
            cleaned_record = self.clean_single_record(record)
            cleaned_records.append(cleaned_record)
        
        batch_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"批量清理完成: {len(raw_records)} 筆記錄，耗時 {batch_time:.3f}s")
        
        return cleaned_records
    
    def _standardize_datetime(self, data: Dict[str, Any]) -> Optional[datetime]:
        """標準化時間欄位"""
        for field in self.rules.datetime_priority:
            value = data.get(field)
            if value:
                if isinstance(value, datetime):
                    return value
                elif isinstance(value, str):
                    try:
                        return datetime.fromisoformat(value.replace('Z', '+00:00'))
                    except ValueError:
                        continue
        
        # 更新統計
        self._update_field_stats('conversion_datetime')
        return None
    
    def _standardize_amounts(self, data: Dict[str, Any]) -> tuple[Optional[Decimal], Optional[Decimal]]:
        """標準化金額欄位"""
        # 銷售金額
        usd_sale_amount = None
        for field in ['sale_amount', 'usd_sale_amount']:
            value = data.get(field)
            if value is not None:
                usd_sale_amount = self._convert_to_decimal(value)
                if usd_sale_amount is not None:
                    break
        
        # 支付金額  
        usd_payout = None
        for field in ['payout', 'usd_payout']:
            value = data.get(field)
            if value is not None:
                usd_payout = self._convert_to_decimal(value)
                if usd_payout is not None:
                    break
        
        # 更新統計
        if usd_sale_amount is not None:
            self._update_field_stats('usd_sale_amount')
        if usd_payout is not None:
            self._update_field_stats('usd_payout')
        
        return usd_sale_amount, usd_payout
    
    def _standardize_currency(self, data: Dict[str, Any]) -> str:
        """標準化貨幣欄位"""
        # 優先級: conversion_currency > currency > 默認USD
        currency = (
            data.get('conversion_currency') or 
            data.get('currency') or 
            self.rules.default_currency
        )
        
        # 確保是字符串且非空
        if not currency or not isinstance(currency, str):
            currency = self.rules.default_currency
        
        self._update_field_stats('currency')
        return currency.upper()
    
    def _standardize_status(self, data: Dict[str, Any]) -> str:
        """標準化狀態欄位"""
        status = (
            data.get('conversion_status') or 
            self.rules.default_status
        )
        
        # 確保是字符串且非空
        if not status or not isinstance(status, str):
            status = self.rules.default_status
        
        self._update_field_stats('status')
        return status.lower()
    
    def _convert_to_decimal(self, value: Any) -> Optional[Decimal]:
        """轉換為Decimal類型"""
        if value is None:
            return None
        
        try:
            if isinstance(value, Decimal):
                return value
            elif isinstance(value, (int, float)):
                return Decimal(str(value))
            elif isinstance(value, str):
                # 清理字符串格式
                cleaned_value = value.strip().replace(',', '')
                if cleaned_value:
                    return Decimal(cleaned_value)
            return None
        except (InvalidOperation, ValueError):
            return None
    
    def _validate_cleaned_data(self, data: Dict[str, Any]):
        """驗證清理後的數據"""
        if not self.rules.validate_amounts and not self.rules.validate_dates:
            return
        
        # 驗證金額
        if self.rules.validate_amounts:
            usd_sale = data.get('usd_sale_amount')
            usd_payout = data.get('usd_payout')
            
            if usd_sale and usd_sale < 0:
                logger.warning(f"負數銷售金額: {usd_sale}")
            
            if usd_payout and usd_payout < 0:
                logger.warning(f"負數支付金額: {usd_payout}")
        
        # 驗證時間
        if self.rules.validate_dates:
            conversion_datetime = data.get('conversion_datetime')
            if conversion_datetime and conversion_datetime > datetime.now(timezone.utc):
                logger.warning(f"未來時間: {conversion_datetime}")
    
    def _update_field_stats(self, field_name: str):
        """更新欄位統計"""
        if field_name not in self.cleaning_stats['cleaned_fields']:
            self.cleaning_stats['cleaned_fields'][field_name] = 0
        self.cleaning_stats['cleaned_fields'][field_name] += 1
    
    def get_cleaning_stats(self) -> Dict[str, Any]:
        """獲取清理統計"""
        stats = self.cleaning_stats.copy()
        
        if stats['performance_metrics']:
            stats['avg_processing_time'] = sum(stats['performance_metrics']) / len(stats['performance_metrics'])
            stats['max_processing_time'] = max(stats['performance_metrics'])
            stats['min_processing_time'] = min(stats['performance_metrics'])
        
        if stats['processed_records'] > 0:
            stats['error_rate'] = (stats['validation_errors'] / stats['processed_records']) * 100
        
        return stats
    
    def reset_stats(self):
        """重置統計"""
        self.cleaning_stats = {
            'processed_records': 0,
            'cleaned_fields': {},
            'validation_errors': 0,
            'performance_metrics': []
        }

class ConversionsServiceWithCleaning:
    """帶數據清理的轉換服務"""
    
    def __init__(self, database_manager, query_router, enable_cleaning: bool = True):
        """
        初始化服務
        
        Args:
            database_manager: 數據庫管理器
            query_router: 查詢路由器
            enable_cleaning: 是否啟用數據清理
        """
        self.db = database_manager
        self.router = query_router
        self.enable_cleaning = enable_cleaning
        self.cleaner = ConversionsDataCleaner() if enable_cleaning else None
    
    async def get_conversions_with_cleaning(self, 
                                          filters: Dict[str, Any],
                                          fields: List[str] = None,
                                          performance_critical: bool = False,
                                          use_app_cleaning: bool = True) -> List[Dict[str, Any]]:
        """
        獲取帶清理的轉換數據
        
        Args:
            filters: 過濾條件
            fields: 需要的欄位
            performance_critical: 是否為性能關鍵查詢
            use_app_cleaning: 是否使用應用層清理
            
        Returns:
            清理後的轉換數據
        """
        from .conversions_query_router import QueryContext, QueryType
        
        if fields is None:
            fields = ['*']
        
        # 創建查詢上下文
        context = QueryContext(
            query_type=QueryType.SELECT,
            fields=fields,
            filters=filters,
            performance_critical=performance_critical
        )
        
        # 如果使用應用層清理，直接查詢基礎表
        if use_app_cleaning and self.enable_cleaning:
            # 強制使用基礎表避免視圖計算開銷
            query = f"SELECT {', '.join(fields)} FROM conversions"
            where_conditions = []
            params = []
            
            for field, value in filters.items():
                where_conditions.append(f"{field} = ${len(params) + 1}")
                params.append(value)
            
            if where_conditions:
                query += f" WHERE {' AND '.join(where_conditions)}"
            
            # 執行查詢
            raw_results = await self.db.fetch(query, *params)
            raw_data = [dict(row) for row in raw_results]
            
            # 應用層清理
            cleaned_data = self.cleaner.clean_batch_records(raw_data)
            
            logger.info(f"應用層清理: {len(raw_data)} 筆記錄，使用基礎表查詢")
            return cleaned_data
        
        else:
            # 使用路由器決定最優表格
            optimal_table = self.router.route_query(context)
            
            query = f"SELECT {', '.join(fields)} FROM {optimal_table.value}"
            where_conditions = []
            params = []
            
            for field, value in filters.items():
                where_conditions.append(f"{field} = ${len(params) + 1}")
                params.append(value)
            
            if where_conditions:
                query += f" WHERE {' AND '.join(where_conditions)}"
            
            results = await self.db.fetch(query, *params)
            
            logger.info(f"視圖查詢: {len(results)} 筆記錄，使用 {optimal_table.value}")
            return [dict(row) for row in results]
    
    def get_cleaning_performance(self) -> Dict[str, Any]:
        """獲取清理性能統計"""
        if not self.cleaner:
            return {"cleaning_enabled": False}
        
        stats = self.cleaner.get_cleaning_stats()
        router_stats = self.router.get_performance_stats()
        
        return {
            "cleaning_enabled": True,
            "cleaning_stats": stats,
            "routing_stats": router_stats
        }

# 使用示例和測試
async def example_usage():
    """使用示例"""
    # 初始化清理規則
    rules = CleaningRules(
        default_currency="USD",
        default_status="pending",
        validate_amounts=True,
        validate_dates=True
    )
    
    # 初始化清理器
    cleaner = ConversionsDataCleaner(rules)
    
    # 測試數據
    test_data = {
        'id': 1,
        'conversion_id': '123456',
        'datetime_conversion': None,
        'created_at': '2025-07-17T10:00:00Z',
        'sale_amount': '100.50',
        'payout': None,
        'usd_payout': '5.25',
        'conversion_currency': None,
        'currency': 'usd',
        'conversion_status': None
    }
    
    # 清理數據
    cleaned = cleaner.clean_single_record(test_data)
    
    print("🔧 數據清理示例:")
    print(f"原始數據: {test_data}")
    print(f"清理後: {cleaned}")
    print(f"統計信息: {cleaner.get_cleaning_stats()}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage()) 