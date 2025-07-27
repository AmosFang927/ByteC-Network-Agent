#!/usr/bin/env python3
"""
統一存儲服務
Unified Storage Service

DMP-Agent 提供的統一數據存儲服務，供所有其他 agent 使用
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from decimal import Decimal
from dataclasses import dataclass, asdict
import json

# 導入增強版資料庫管理器
from shared.database import EnhancedDatabaseManager, DatabaseConfig, get_database_manager

logger = logging.getLogger(__name__)

@dataclass
class ConversionData:
    """轉化數據模型"""
    conversion_id: str
    tenant_id: int = 1
    partner: Optional[str] = None
    platform: Optional[str] = None
    source: Optional[str] = None
    offer_id: Optional[str] = None
    offer_name: Optional[str] = None
    datetime_conversion: Optional[datetime] = None
    order_id: Optional[str] = None
    usd_sale_amount: Optional[Decimal] = None
    usd_payout: Optional[Decimal] = None
    sale_amount_local: Optional[Decimal] = None
    payout_local: Optional[Decimal] = None
    aff_sub: Optional[str] = None
    aff_sub2: Optional[str] = None
    aff_sub3: Optional[str] = None
    aff_sub4: Optional[str] = None
    adv_sub1: Optional[str] = None
    adv_sub2: Optional[str] = None
    adv_sub3: Optional[str] = None
    adv_sub4: Optional[str] = None
    adv_sub5: Optional[str] = None
    conversion_status: str = 'pending'
    raw_data: Optional[Dict] = None

@dataclass
class PartnerInfo:
    """合作夥伴信息模型"""
    partner_id: int
    partner_name: str
    partner_code: Optional[str] = None
    commission_rate: Optional[Decimal] = None
    is_active: bool = True
    created_at: Optional[datetime] = None

@dataclass
class QueryRequest:
    """查詢請求模型"""
    agent_name: str
    query_type: str
    parameters: Dict[str, Any]
    use_cache: bool = True
    cache_ttl: Optional[int] = None

class UnifiedStorageService:
    """統一存儲服務"""
    
    def __init__(self, db_config: Optional[DatabaseConfig] = None):
        self.db_config = db_config or DatabaseConfig()
        self.db_manager: Optional[EnhancedDatabaseManager] = None
        self._initialized = False
        
        # 支援的查詢類型
        self.supported_operations = {
            # 轉化數據操作
            'get_conversions': self._get_conversions,
            'insert_conversion': self._insert_conversion,
            'batch_insert_conversions': self._batch_insert_conversions,
            'update_conversion': self._update_conversion,
            
            # 合作夥伴操作
            'get_partners': self._get_partners,
            'get_partner_summary': self._get_partner_summary,
            'insert_partner': self._insert_partner,
            'update_partner': self._update_partner,
            
            # 報表查詢
            'get_daily_summary': self._get_daily_summary,
            'get_performance_metrics': self._get_performance_metrics,
            'get_conversion_trends': self._get_conversion_trends,
            
            # 監控和健康檢查
            'health_check': self._health_check,
            'get_metrics': self._get_metrics,
            
            # 自定義查詢
            'execute_query': self._execute_custom_query,
        }
    
    async def initialize(self):
        """初始化存儲服務"""
        if self._initialized:
            return
            
        try:
            self.db_manager = await get_database_manager(self.db_config)
            self._initialized = True
            logger.info("✅ 統一存儲服務初始化完成")
            
        except Exception as e:
            logger.error(f"❌ 統一存儲服務初始化失敗: {e}")
            raise
    
    async def process_request(self, request: QueryRequest) -> Dict[str, Any]:
        """處理來自其他 agent 的請求"""
        if not self._initialized:
            await self.initialize()
        
        operation = request.query_type
        
        if operation not in self.supported_operations:
            raise ValueError(f"不支援的操作類型: {operation}")
        
        try:
            logger.info(f"🔄 處理 {request.agent_name} 的 {operation} 請求")
            
            # 執行操作
            handler = self.supported_operations[operation]
            result = await handler(request.parameters, request.use_cache, request.cache_ttl)
            
            return {
                'success': True,
                'data': result,
                'agent_name': request.agent_name,
                'operation': operation,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ 處理請求失敗 ({request.agent_name}/{operation}): {e}")
            return {
                'success': False,
                'error': str(e),
                'agent_name': request.agent_name,
                'operation': operation,
                'timestamp': datetime.now().isoformat()
            }
    
    # =================== 轉化數據操作 ===================
    
    async def _get_conversions(self, params: Dict, use_cache: bool = True, cache_ttl: Optional[int] = None) -> List[Dict]:
        """獲取轉化數據"""
        partner = params.get('partner')
        start_date = params.get('start_date')
        end_date = params.get('end_date') 
        limit = params.get('limit')
        
        # 處理日期參數
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date)
        if isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date)
        
        return await self.db_manager.get_conversions_optimized(
            partner=partner,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            use_cache=use_cache
        )
    
    async def _insert_conversion(self, params: Dict, use_cache: bool = True, cache_ttl: Optional[int] = None) -> Dict:
        """插入單筆轉化數據"""
        conversion_data = ConversionData(**params)
        
        query = """
        INSERT INTO conversions (
            conversion_id, tenant_id, partner, platform, source, offer_id, offer_name,
            datetime_conversion, order_id, usd_sale_amount, usd_payout, sale_amount_local,
            payout_local, aff_sub, aff_sub2, aff_sub3, aff_sub4, adv_sub1, adv_sub2,
            adv_sub3, adv_sub4, adv_sub5, conversion_status, raw_data, created_at
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17,
            $18, $19, $20, $21, $22, $23, $24, NOW()
        ) RETURNING id
        """
        
        query_params = [
            conversion_data.conversion_id,
            conversion_data.tenant_id,
            conversion_data.partner,
            conversion_data.platform,
            conversion_data.source,
            conversion_data.offer_id,
            conversion_data.offer_name,
            conversion_data.datetime_conversion,
            conversion_data.order_id,
            conversion_data.usd_sale_amount,
            conversion_data.usd_payout,
            conversion_data.sale_amount_local,
            conversion_data.payout_local,
            conversion_data.aff_sub,
            conversion_data.aff_sub2,
            conversion_data.aff_sub3,
            conversion_data.aff_sub4,
            conversion_data.adv_sub1,
            conversion_data.adv_sub2,
            conversion_data.adv_sub3,
            conversion_data.adv_sub4,
            conversion_data.adv_sub5,
            conversion_data.conversion_status,
            json.dumps(conversion_data.raw_data) if conversion_data.raw_data else None
        ]
        
        result = await self.db_manager.execute_query(query, query_params, use_cache=False)
        return {'inserted_id': result[0]['id'] if result else None}
    
    async def _batch_insert_conversions(self, params: Dict, use_cache: bool = True, cache_ttl: Optional[int] = None) -> Dict:
        """批量插入轉化數據"""
        conversions_list = params.get('conversions', [])
        
        if not conversions_list:
            return {'inserted_count': 0}
        
        query = """
        INSERT INTO conversions (
            conversion_id, tenant_id, partner, platform, source, offer_id, offer_name,
            datetime_conversion, order_id, usd_sale_amount, usd_payout, sale_amount_local,
            payout_local, aff_sub, aff_sub2, aff_sub3, aff_sub4, adv_sub1, adv_sub2,
            adv_sub3, adv_sub4, adv_sub5, conversion_status, raw_data, created_at
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17,
            $18, $19, $20, $21, $22, $23, $24, NOW()
        ) ON CONFLICT (conversion_id) DO NOTHING
        """
        
        inserted_count = 0
        
        async with self.db_manager.get_connection() as conn:
            for conversion_dict in conversions_list:
                try:
                    conversion_data = ConversionData(**conversion_dict)
                    
                    query_params = [
                        conversion_data.conversion_id,
                        conversion_data.tenant_id,
                        conversion_data.partner,
                        conversion_data.platform,
                        conversion_data.source,
                        conversion_data.offer_id,
                        conversion_data.offer_name,
                        conversion_data.datetime_conversion,
                        conversion_data.order_id,
                        conversion_data.usd_sale_amount,
                        conversion_data.usd_payout,
                        conversion_data.sale_amount_local,
                        conversion_data.payout_local,
                        conversion_data.aff_sub,
                        conversion_data.aff_sub2,
                        conversion_data.aff_sub3,
                        conversion_data.aff_sub4,
                        conversion_data.adv_sub1,
                        conversion_data.adv_sub2,
                        conversion_data.adv_sub3,
                        conversion_data.adv_sub4,
                        conversion_data.adv_sub5,
                        conversion_data.conversion_status,
                        json.dumps(conversion_data.raw_data) if conversion_data.raw_data else None
                    ]
                    
                    result = await conn.execute(query, *query_params)
                    if result == "INSERT 0 1":  # 成功插入
                        inserted_count += 1
                        
                except Exception as e:
                    logger.warning(f"⚠️ 批量插入失敗: {e}")
                    continue
        
        return {'inserted_count': inserted_count}
    
    async def _update_conversion(self, params: Dict, use_cache: bool = True, cache_ttl: Optional[int] = None) -> Dict:
        """更新轉化數據"""
        conversion_id = params.get('conversion_id')
        updates = params.get('updates', {})
        
        if not conversion_id or not updates:
            raise ValueError("conversion_id 和 updates 參數是必需的")
        
        # 構建動態更新查詢
        set_clauses = []
        query_params = []
        param_count = 0
        
        for field, value in updates.items():
            param_count += 1
            set_clauses.append(f"{field} = ${param_count}")
            query_params.append(value)
        
        param_count += 1
        query = f"""
        UPDATE conversions 
        SET {', '.join(set_clauses)}, updated_at = NOW()
        WHERE conversion_id = ${param_count}
        """
        query_params.append(conversion_id)
        
        await self.db_manager.execute_query(query, query_params, use_cache=False)
        return {'updated': True}
    
    # =================== 合作夥伴操作 ===================
    
    async def _get_partners(self, params: Dict, use_cache: bool = True, cache_ttl: Optional[int] = None) -> List[Dict]:
        """獲取合作夥伴列表"""
        is_active = params.get('is_active', True)
        
        query = """
        SELECT id, partner_name, partner_code, commission_rate, is_active, created_at
        FROM partners
        WHERE ($1::boolean IS NULL OR is_active = $1)
        ORDER BY partner_name
        """
        
        return await self.db_manager.execute_query(
            query, 
            [is_active if is_active is not None else None], 
            use_cache=use_cache
        )
    
    async def _get_partner_summary(self, params: Dict, use_cache: bool = True, cache_ttl: Optional[int] = None) -> List[Dict]:
        """獲取合作夥伴汇总"""
        partner = params.get('partner')
        start_date = params.get('start_date')
        end_date = params.get('end_date')
        
        # 處理日期參數
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date)
        if isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date)
        
        return await self.db_manager.get_partner_summary_optimized(
            partner=partner,
            start_date=start_date,
            end_date=end_date
        )
    
    async def _insert_partner(self, params: Dict, use_cache: bool = True, cache_ttl: Optional[int] = None) -> Dict:
        """插入合作夥伴"""
        partner_info = PartnerInfo(**params)
        
        query = """
        INSERT INTO partners (partner_name, partner_code, commission_rate, is_active, created_at)
        VALUES ($1, $2, $3, $4, NOW())
        RETURNING id
        """
        
        query_params = [
            partner_info.partner_name,
            partner_info.partner_code,
            partner_info.commission_rate,
            partner_info.is_active
        ]
        
        result = await self.db_manager.execute_query(query, query_params, use_cache=False)
        return {'partner_id': result[0]['id'] if result else None}
    
    async def _update_partner(self, params: Dict, use_cache: bool = True, cache_ttl: Optional[int] = None) -> Dict:
        """更新合作夥伴"""
        partner_id = params.get('partner_id')
        updates = params.get('updates', {})
        
        if not partner_id or not updates:
            raise ValueError("partner_id 和 updates 參數是必需的")
        
        # 構建動態更新查詢
        set_clauses = []
        query_params = []
        param_count = 0
        
        for field, value in updates.items():
            param_count += 1
            set_clauses.append(f"{field} = ${param_count}")
            query_params.append(value)
        
        param_count += 1
        query = f"""
        UPDATE partners 
        SET {', '.join(set_clauses)}, updated_at = NOW()
        WHERE id = ${param_count}
        """
        query_params.append(partner_id)
        
        await self.db_manager.execute_query(query, query_params, use_cache=False)
        return {'updated': True}
    
    # =================== 報表查詢 ===================
    
    async def _get_daily_summary(self, params: Dict, use_cache: bool = True, cache_ttl: Optional[int] = None) -> List[Dict]:
        """獲取日報表汇总"""
        start_date = params.get('start_date')
        end_date = params.get('end_date')
        partner = params.get('partner')
        
        # 處理日期參數
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date)
        if isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date)
        
        query = """
        SELECT 
            DATE(datetime_conversion) as date,
            partner,
            COUNT(*) as conversion_count,
            SUM(COALESCE(sale_amount, usd_sale_amount, 0)) as total_sales,
            SUM(COALESCE(payout, usd_payout, 0)) as total_payouts,
            AVG(COALESCE(sale_amount, usd_sale_amount, 0)) as avg_sale_amount,
            COUNT(DISTINCT aff_sub) as unique_sources
        FROM conversions
        WHERE datetime_conversion IS NOT NULL
        """
        
        query_params = []
        param_count = 0
        
        if start_date:
            param_count += 1
            query += f" AND DATE(datetime_conversion) >= ${param_count}"
            query_params.append(start_date.date())
        
        if end_date:
            param_count += 1
            query += f" AND DATE(datetime_conversion) <= ${param_count}"
            query_params.append(end_date.date())
        
        if partner and partner.upper() != 'ALL':
            param_count += 1
            query += f" AND partner = ${param_count}"
            query_params.append(partner)
        
        query += " GROUP BY DATE(datetime_conversion), partner ORDER BY date DESC, partner"
        
        return await self.db_manager.execute_query(query, query_params, use_cache=use_cache)
    
    async def _get_performance_metrics(self, params: Dict, use_cache: bool = True, cache_ttl: Optional[int] = None) -> Dict:
        """獲取性能指標"""
        days = params.get('days', 7)
        partner = params.get('partner')
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 總體統計
        base_query = """
        SELECT 
            COUNT(*) as total_conversions,
            SUM(COALESCE(sale_amount, usd_sale_amount, 0)) as total_sales,
            SUM(COALESCE(payout, usd_payout, 0)) as total_payouts,
            AVG(COALESCE(sale_amount, usd_sale_amount, 0)) as avg_sale_amount,
            COUNT(DISTINCT partner) as unique_partners,
            COUNT(DISTINCT aff_sub) as unique_sources
        FROM conversions
        WHERE datetime_conversion >= $1 AND datetime_conversion <= $2
        """
        
        query_params = [start_date, end_date]
        
        if partner and partner.upper() != 'ALL':
            base_query += " AND partner = $3"
            query_params.append(partner)
        
        metrics = await self.db_manager.execute_query(base_query, query_params, use_cache=use_cache)
        
        return metrics[0] if metrics else {}
    
    async def _get_conversion_trends(self, params: Dict, use_cache: bool = True, cache_ttl: Optional[int] = None) -> List[Dict]:
        """獲取轉化趨勢"""
        days = params.get('days', 30)
        partner = params.get('partner')
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        query = """
        SELECT 
            DATE(datetime_conversion) as date,
            COUNT(*) as conversions,
            SUM(COALESCE(sale_amount, usd_sale_amount, 0)) as sales,
            COUNT(DISTINCT aff_sub) as sources
        FROM conversions
        WHERE datetime_conversion >= $1 AND datetime_conversion <= $2
        """
        
        query_params = [start_date, end_date]
        
        if partner and partner.upper() != 'ALL':
            query += " AND partner = $3"
            query_params.append(partner)
        
        query += " GROUP BY DATE(datetime_conversion) ORDER BY date"
        
        return await self.db_manager.execute_query(query, query_params, use_cache=use_cache)
    
    # =================== 監控和工具 ===================
    
    async def _health_check(self, params: Dict, use_cache: bool = True, cache_ttl: Optional[int] = None) -> Dict:
        """健康檢查"""
        return await self.db_manager.health_check()
    
    async def _get_metrics(self, params: Dict, use_cache: bool = True, cache_ttl: Optional[int] = None) -> Dict:
        """獲取系統指標"""
        # 獲取資料庫健康狀態
        health = await self.db_manager.health_check()
        
        # 獲取緩存統計
        cache_stats = self.db_manager.cache.get_stats() if self.db_manager.cache else {}
        
        # 獲取連接池狀態
        pool_stats = self.db_manager.monitor.get_status()
        
        return {
            'service_status': 'healthy' if health.get('status') == 'healthy' else 'unhealthy',
            'database': health.get('database', {}),
            'cache': cache_stats,
            'pool': pool_stats,
            'supported_operations': list(self.supported_operations.keys()),
            'timestamp': datetime.now().isoformat()
        }
    
    async def _execute_custom_query(self, params: Dict, use_cache: bool = True, cache_ttl: Optional[int] = None) -> List[Dict]:
        """執行自定義查詢"""
        query = params.get('query')
        query_params = params.get('params', [])
        
        if not query:
            raise ValueError("query 參數是必需的")
        
        # 安全檢查：只允許 SELECT 查詢
        if not query.strip().upper().startswith('SELECT'):
            raise ValueError("只允許 SELECT 查詢")
        
        return await self.db_manager.execute_query(query, query_params, use_cache=use_cache)
    
    async def close(self):
        """關閉存儲服務"""
        if self.db_manager:
            await self.db_manager.close()
        logger.info("✅ 統一存儲服務已關閉")

# 全局實例
_storage_service: Optional[UnifiedStorageService] = None

async def get_storage_service(db_config: Optional[DatabaseConfig] = None) -> UnifiedStorageService:
    """獲取統一存儲服務實例"""
    global _storage_service
    
    if _storage_service is None:
        _storage_service = UnifiedStorageService(db_config)
        await _storage_service.initialize()
    
    return _storage_service 