#!/usr/bin/env python3
"""
ByteC 智能轉換數據查詢路由器
根據查詢類型和場景自動選擇最優表格 (conversions vs conversions_enhanced)
"""

import logging
from typing import List, Dict, Any, Optional, Union
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class QueryType(Enum):
    """查詢類型枚舉"""
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    AGGREGATE = "AGGREGATE"
    JOIN = "JOIN"
    ANALYTICAL = "ANALYTICAL"

class TableType(Enum):
    """表格類型枚舉"""
    BASE_TABLE = "conversions"  # 基礎表格
    ENHANCED_VIEW = "conversions_enhanced"  # 增強視圖
    MATERIALIZED_VIEW = "conversions_enhanced_mat"  # 實體化視圖 (待創建)

@dataclass
class QueryContext:
    """查詢上下文"""
    query_type: QueryType
    fields: List[str]
    filters: Dict[str, Any]
    expected_rows: Optional[int] = None
    performance_critical: bool = False
    use_cache: bool = True
    
class ConversionsQueryRouter:
    """智能轉換數據查詢路由器"""
    
    # 原始表格專有欄位 (只存在於conversions表)
    BASE_TABLE_ONLY_FIELDS = {
        'datetime_conversion', 'datetime_conversion_updated', 
        'partner_id', 'payout', 'platform_id', 'sale_amount', 'sub_id'
    }
    
    # 視圖特有欄位 (經過處理的欄位)
    ENHANCED_VIEW_FIELDS = {
        'conversion_datetime', 'status'
    }
    
    # 大量數據查詢閾值
    LARGE_QUERY_THRESHOLD = 10000
    
    def __init__(self, enable_materialized_view: bool = False):
        """
        初始化查詢路由器
        
        Args:
            enable_materialized_view: 是否啟用實體化視圖
        """
        self.enable_materialized_view = enable_materialized_view
        self.performance_stats = {
            'base_table_queries': 0,
            'enhanced_view_queries': 0,
            'materialized_view_queries': 0,
            'routing_decisions': []
        }
        
    def route_query(self, context: QueryContext) -> TableType:
        """
        智能路由查詢到最優表格
        
        Args:
            context: 查詢上下文
            
        Returns:
            推薦的表格類型
        """
        decision_factors = []
        
        # 1. 寫入操作必須使用基礎表
        if context.query_type in [QueryType.INSERT, QueryType.UPDATE, QueryType.DELETE]:
            decision_factors.append("寫入操作")
            return self._log_decision(TableType.BASE_TABLE, context, decision_factors)
        
        # 2. 需要原始表格專有欄位
        if any(field in self.BASE_TABLE_ONLY_FIELDS for field in context.fields):
            decision_factors.append("需要原始專有欄位")
            return self._log_decision(TableType.BASE_TABLE, context, decision_factors)
        
        # 3. 性能關鍵查詢優先使用有索引的基礎表
        if context.performance_critical:
            decision_factors.append("性能關鍵查詢")
            return self._log_decision(TableType.BASE_TABLE, context, decision_factors)
        
        # 4. 大量數據聚合查詢使用基礎表 (有索引優勢)
        if (context.query_type == QueryType.AGGREGATE and 
            context.expected_rows and context.expected_rows > self.LARGE_QUERY_THRESHOLD):
            decision_factors.append(f"大量數據聚合 (>{self.LARGE_QUERY_THRESHOLD} 筆)")
            return self._log_decision(TableType.BASE_TABLE, context, decision_factors)
        
        # 5. 複雜JOIN查詢使用基礎表 (避免視圖開銷)
        if context.query_type == QueryType.JOIN:
            decision_factors.append("複雜JOIN查詢")
            return self._log_decision(TableType.BASE_TABLE, context, decision_factors)
        
        # 6. 時間範圍查詢優化
        if self._is_time_range_query(context.filters):
            if self._is_recent_data_query(context.filters):
                decision_factors.append("近期數據查詢 (有分區索引)")
                return self._log_decision(TableType.BASE_TABLE, context, decision_factors)
        
        # 7. 實體化視圖優先 (如果啟用且適合)
        if (self.enable_materialized_view and 
            context.query_type in [QueryType.SELECT, QueryType.ANALYTICAL]):
            decision_factors.append("使用實體化視圖")
            return self._log_decision(TableType.MATERIALIZED_VIEW, context, decision_factors)
        
        # 8. 默認使用增強視圖 (業務展示友好)
        decision_factors.append("默認業務展示")
        return self._log_decision(TableType.ENHANCED_VIEW, context, decision_factors)
    
    def get_optimized_query(self, 
                          base_query: str, 
                          context: QueryContext) -> tuple[str, TableType]:
        """
        獲取優化後的查詢語句
        
        Args:
            base_query: 原始查詢語句
            context: 查詢上下文
            
        Returns:
            優化後的查詢語句和使用的表格類型
        """
        optimal_table = self.route_query(context)
        
        # 替換表格名稱
        if "conversions_enhanced" in base_query:
            optimized_query = base_query.replace("conversions_enhanced", optimal_table.value)
        elif "conversions" in base_query:
            if optimal_table != TableType.BASE_TABLE:
                optimized_query = base_query.replace("conversions", optimal_table.value)
            else:
                optimized_query = base_query
        else:
            optimized_query = base_query
        
        return optimized_query, optimal_table
    
    def _log_decision(self, 
                     table_type: TableType, 
                     context: QueryContext, 
                     factors: List[str]) -> TableType:
        """記錄路由決策"""
        decision = {
            'timestamp': datetime.now(),
            'table_type': table_type.value,
            'query_type': context.query_type.value,
            'factors': factors,
            'fields_count': len(context.fields),
            'performance_critical': context.performance_critical
        }
        
        self.performance_stats['routing_decisions'].append(decision)
        
        # 更新統計
        if table_type == TableType.BASE_TABLE:
            self.performance_stats['base_table_queries'] += 1
        elif table_type == TableType.ENHANCED_VIEW:
            self.performance_stats['enhanced_view_queries'] += 1
        elif table_type == TableType.MATERIALIZED_VIEW:
            self.performance_stats['materialized_view_queries'] += 1
        
        logger.info(f"查詢路由: {table_type.value} | 原因: {', '.join(factors)}")
        return table_type
    
    def _is_time_range_query(self, filters: Dict[str, Any]) -> bool:
        """檢查是否為時間範圍查詢"""
        time_fields = {'created_at', 'datetime_conversion', 'conversion_datetime', 'event_time'}
        return any(field in filters for field in time_fields)
    
    def _is_recent_data_query(self, filters: Dict[str, Any]) -> bool:
        """檢查是否為近期數據查詢 (30天內)"""
        recent_threshold = datetime.now() - timedelta(days=30)
        
        for field, value in filters.items():
            if field in {'created_at', 'datetime_conversion', 'event_time'}:
                if isinstance(value, datetime) and value >= recent_threshold:
                    return True
                # 檢查範圍查詢
                if isinstance(value, dict):
                    if 'gte' in value and isinstance(value['gte'], datetime):
                        return value['gte'] >= recent_threshold
        
        return False
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """獲取性能統計"""
        total_queries = (
            self.performance_stats['base_table_queries'] +
            self.performance_stats['enhanced_view_queries'] +
            self.performance_stats['materialized_view_queries']
        )
        
        if total_queries == 0:
            return self.performance_stats
        
        return {
            **self.performance_stats,
            'total_queries': total_queries,
            'base_table_percentage': (self.performance_stats['base_table_queries'] / total_queries) * 100,
            'enhanced_view_percentage': (self.performance_stats['enhanced_view_queries'] / total_queries) * 100,
            'materialized_view_percentage': (self.performance_stats['materialized_view_queries'] / total_queries) * 100,
        }
    
    def reset_stats(self):
        """重置統計"""
        self.performance_stats = {
            'base_table_queries': 0,
            'enhanced_view_queries': 0,
            'materialized_view_queries': 0,
            'routing_decisions': []
        }

class ConversionsService:
    """統一轉換數據服務 (示例用法)"""
    
    def __init__(self, database_manager, enable_materialized_view: bool = False):
        self.db = database_manager
        self.router = ConversionsQueryRouter(enable_materialized_view)
    
    async def get_conversions(self, 
                            filters: Dict[str, Any],
                            fields: List[str] = None,
                            performance_critical: bool = False) -> List[Dict[str, Any]]:
        """
        智能獲取轉換數據
        
        Args:
            filters: 過濾條件
            fields: 需要的欄位列表
            performance_critical: 是否為性能關鍵查詢
            
        Returns:
            轉換數據列表
        """
        if fields is None:
            fields = ['*']
        
        # 創建查詢上下文
        context = QueryContext(
            query_type=QueryType.SELECT,
            fields=fields,
            filters=filters,
            performance_critical=performance_critical
        )
        
        # 獲取最優表格
        optimal_table = self.router.route_query(context)
        
        # 構建查詢
        base_query = f"SELECT {', '.join(fields)} FROM {optimal_table.value}"
        
        # 添加過濾條件
        where_conditions = []
        params = []
        
        for field, value in filters.items():
            where_conditions.append(f"{field} = ${len(params) + 1}")
            params.append(value)
        
        if where_conditions:
            base_query += f" WHERE {' AND '.join(where_conditions)}"
        
        # 執行查詢
        results = await self.db.fetch(base_query, *params)
        
        logger.info(f"查詢執行: {optimal_table.value} | 結果: {len(results)} 筆")
        return [dict(row) for row in results]
    
    async def create_conversion(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """創建轉換記錄 (自動路由到基礎表)"""
        context = QueryContext(
            query_type=QueryType.INSERT,
            fields=list(data.keys()),
            filters={}
        )
        
        # 插入操作自動路由到基礎表
        table_type = self.router.route_query(context)
        
        # 構建插入語句
        fields = list(data.keys())
        placeholders = [f"${i+1}" for i in range(len(fields))]
        
        query = f"""
            INSERT INTO {table_type.value} ({', '.join(fields)})
            VALUES ({', '.join(placeholders)})
            RETURNING *
        """
        
        result = await self.db.fetchrow(query, *data.values())
        return dict(result)
    
    def get_router_stats(self) -> Dict[str, Any]:
        """獲取路由器統計"""
        return self.router.get_performance_stats()

# 使用示例
async def example_usage():
    """使用示例"""
    # 初始化服務
    # service = ConversionsService(database_manager)
    
    # 示例1: 業務報表查詢 (自動使用增強視圖)
    business_filters = {
        'aff_sub1': 'RAMPUP',
        'created_at': datetime.now() - timedelta(days=7)
    }
    # results = await service.get_conversions(business_filters)
    
    # 示例2: 性能關鍵查詢 (自動使用基礎表)
    performance_filters = {
        'partner': 'DeepLeaper'
    }
    # results = await service.get_conversions(
    #     performance_filters, 
    #     performance_critical=True
    # )
    
    # 示例3: 創建新記錄 (自動路由到基礎表)
    new_conversion = {
        'conversion_id': '123456',
        'tenant_id': 1,
        'offer_name': 'Test Offer'
    }
    # result = await service.create_conversion(new_conversion)
    
    # 查看路由統計
    # stats = service.get_router_stats()
    # print(f"路由統計: {stats}")

if __name__ == "__main__":
    # 測試查詢路由邏輯
    router = ConversionsQueryRouter()
    
    # 測試不同場景
    test_cases = [
        # 寫入操作
        QueryContext(QueryType.INSERT, ['conversion_id'], {}),
        
        # 需要原始欄位
        QueryContext(QueryType.SELECT, ['datetime_conversion'], {}),
        
        # 性能關鍵查詢
        QueryContext(QueryType.SELECT, ['*'], {}, performance_critical=True),
        
        # 大量聚合查詢
        QueryContext(QueryType.AGGREGATE, ['COUNT(*)'], {}, expected_rows=50000),
        
        # 業務展示查詢
        QueryContext(QueryType.SELECT, ['conversion_datetime', 'usd_payout'], {}),
    ]
    
    print("🔍 查詢路由測試:")
    print("=" * 60)
    
    for i, context in enumerate(test_cases, 1):
        result = router.route_query(context)
        print(f"{i}. {context.query_type.value} -> {result.value}")
    
    print("\n📊 路由統計:")
    stats = router.get_performance_stats()
    for key, value in stats.items():
        if not key.endswith('_decisions'):
            print(f"  {key}: {value}") 