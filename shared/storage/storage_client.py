#!/usr/bin/env python3
"""
統一存儲客戶端
Unified Storage Client

供所有 agent 使用的統一數據存儲客戶端，連接到 DMP-Agent 的存儲服務
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from decimal import Decimal
import json

# 導入 DMP-Agent 的存儲服務
from agents.data_dmp_agent.unified_storage_service import (
    UnifiedStorageService, 
    QueryRequest, 
    ConversionData, 
    PartnerInfo,
    get_storage_service
)

logger = logging.getLogger(__name__)

class StorageClient:
    """統一存儲客戶端"""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.storage_service: Optional[UnifiedStorageService] = None
        self._initialized = False
    
    async def initialize(self):
        """初始化客戶端"""
        if self._initialized:
            return
            
        try:
            self.storage_service = await get_storage_service()
            self._initialized = True
            logger.info(f"✅ {self.agent_name} 存儲客戶端初始化完成")
            
        except Exception as e:
            logger.error(f"❌ {self.agent_name} 存儲客戶端初始化失敗: {e}")
            raise
    
    async def _make_request(self, operation: str, parameters: Dict[str, Any], 
                          use_cache: bool = True, cache_ttl: Optional[int] = None) -> Any:
        """發送請求到存儲服務"""
        if not self._initialized:
            await self.initialize()
        
        request = QueryRequest(
            agent_name=self.agent_name,
            query_type=operation,
            parameters=parameters,
            use_cache=use_cache,
            cache_ttl=cache_ttl
        )
        
        response = await self.storage_service.process_request(request)
        
        if not response.get('success', False):
            error_msg = response.get('error', '未知錯誤')
            logger.error(f"❌ {self.agent_name} 請求 {operation} 失敗: {error_msg}")
            raise Exception(f"存儲服務錯誤: {error_msg}")
        
        return response.get('data')
    
    # =================== 轉化數據操作 ===================
    
    async def get_conversions(self, partner: Optional[str] = None,
                            start_date: Optional[datetime] = None,
                            end_date: Optional[datetime] = None,
                            limit: Optional[int] = None,
                            use_cache: bool = True) -> List[Dict]:
        """獲取轉化數據"""
        parameters = {
            'partner': partner,
            'start_date': start_date.isoformat() if start_date else None,
            'end_date': end_date.isoformat() if end_date else None,
            'limit': limit
        }
        
        return await self._make_request('get_conversions', parameters, use_cache)
    
    async def insert_conversion(self, conversion_data: Union[Dict, ConversionData]) -> Dict:
        """插入單筆轉化數據"""
        if isinstance(conversion_data, ConversionData):
            conversion_data = {
                k: v.isoformat() if isinstance(v, datetime) else v
                for k, v in conversion_data.__dict__.items()
            }
        
        # 處理日期字段
        if 'datetime_conversion' in conversion_data and isinstance(conversion_data['datetime_conversion'], datetime):
            conversion_data['datetime_conversion'] = conversion_data['datetime_conversion'].isoformat()
        
        return await self._make_request('insert_conversion', conversion_data, use_cache=False)
    
    async def batch_insert_conversions(self, conversions: List[Union[Dict, ConversionData]]) -> Dict:
        """批量插入轉化數據"""
        processed_conversions = []
        
        for conv in conversions:
            if isinstance(conv, ConversionData):
                conv_dict = {
                    k: v.isoformat() if isinstance(v, datetime) else v
                    for k, v in conv.__dict__.items()
                }
            else:
                conv_dict = conv.copy()
                # 處理日期字段
                if 'datetime_conversion' in conv_dict and isinstance(conv_dict['datetime_conversion'], datetime):
                    conv_dict['datetime_conversion'] = conv_dict['datetime_conversion'].isoformat()
            
            processed_conversions.append(conv_dict)
        
        parameters = {'conversions': processed_conversions}
        return await self._make_request('batch_insert_conversions', parameters, use_cache=False)
    
    async def update_conversion(self, conversion_id: str, updates: Dict[str, Any]) -> Dict:
        """更新轉化數據"""
        # 處理日期字段
        processed_updates = updates.copy()
        for key, value in processed_updates.items():
            if isinstance(value, datetime):
                processed_updates[key] = value.isoformat()
        
        parameters = {
            'conversion_id': conversion_id,
            'updates': processed_updates
        }
        
        return await self._make_request('update_conversion', parameters, use_cache=False)
    
    # =================== 合作夥伴操作 ===================
    
    async def get_partners(self, is_active: Optional[bool] = True, use_cache: bool = True) -> List[Dict]:
        """獲取合作夥伴列表"""
        parameters = {'is_active': is_active}
        return await self._make_request('get_partners', parameters, use_cache)
    
    async def get_partner_summary(self, partner: Optional[str] = None,
                                start_date: Optional[datetime] = None,
                                end_date: Optional[datetime] = None,
                                use_cache: bool = True) -> List[Dict]:
        """獲取合作夥伴汇总"""
        parameters = {
            'partner': partner,
            'start_date': start_date.isoformat() if start_date else None,
            'end_date': end_date.isoformat() if end_date else None
        }
        
        return await self._make_request('get_partner_summary', parameters, use_cache)
    
    async def insert_partner(self, partner_info: Union[Dict, PartnerInfo]) -> Dict:
        """插入合作夥伴"""
        if isinstance(partner_info, PartnerInfo):
            partner_info = {
                k: v.isoformat() if isinstance(v, datetime) else v
                for k, v in partner_info.__dict__.items()
            }
        
        return await self._make_request('insert_partner', partner_info, use_cache=False)
    
    async def update_partner(self, partner_id: int, updates: Dict[str, Any]) -> Dict:
        """更新合作夥伴"""
        parameters = {
            'partner_id': partner_id,
            'updates': updates
        }
        
        return await self._make_request('update_partner', parameters, use_cache=False)
    
    # =================== 報表查詢 ===================
    
    async def get_daily_summary(self, start_date: Optional[datetime] = None,
                              end_date: Optional[datetime] = None,
                              partner: Optional[str] = None,
                              use_cache: bool = True) -> List[Dict]:
        """獲取日報表汇总"""
        parameters = {
            'start_date': start_date.isoformat() if start_date else None,
            'end_date': end_date.isoformat() if end_date else None,
            'partner': partner
        }
        
        return await self._make_request('get_daily_summary', parameters, use_cache)
    
    async def get_performance_metrics(self, days: int = 7, 
                                    partner: Optional[str] = None,
                                    use_cache: bool = True) -> Dict:
        """獲取性能指標"""
        parameters = {
            'days': days,
            'partner': partner
        }
        
        return await self._make_request('get_performance_metrics', parameters, use_cache)
    
    async def get_conversion_trends(self, days: int = 30,
                                  partner: Optional[str] = None,
                                  use_cache: bool = True) -> List[Dict]:
        """獲取轉化趨勢"""
        parameters = {
            'days': days,
            'partner': partner
        }
        
        return await self._make_request('get_conversion_trends', parameters, use_cache)
    
    # =================== 監控和工具 ===================
    
    async def health_check(self) -> Dict:
        """健康檢查"""
        return await self._make_request('health_check', {}, use_cache=False)
    
    async def get_metrics(self) -> Dict:
        """獲取系統指標"""
        return await self._make_request('get_metrics', {}, use_cache=False)
    
    async def execute_query(self, query: str, params: List[Any] = None, use_cache: bool = True) -> List[Dict]:
        """執行自定義查詢"""
        parameters = {
            'query': query,
            'params': params or []
        }
        
        return await self._make_request('execute_query', parameters, use_cache)

# =================== 便捷函數 ===================

# 全局客戶端實例緩存
_client_cache: Dict[str, StorageClient] = {}

async def get_storage_client(agent_name: str) -> StorageClient:
    """獲取存儲客戶端實例"""
    if agent_name not in _client_cache:
        client = StorageClient(agent_name)
        await client.initialize()
        _client_cache[agent_name] = client
    
    return _client_cache[agent_name]

# =================== Agent 專用的便捷類 ===================

class APIAgentStorage:
    """API-Agent 專用存儲客戶端"""
    
    def __init__(self):
        self.client: Optional[StorageClient] = None
    
    async def _get_client(self) -> StorageClient:
        if self.client is None:
            self.client = await get_storage_client('api-agent')
        return self.client
    
    async def store_postback_data(self, postback_data: Dict) -> Dict:
        """存儲 Postback 數據"""
        client = await self._get_client()
        
        # 轉換 Postback 數據為轉化數據格式
        conversion_data = {
            'conversion_id': postback_data.get('conversion_id'),
            'partner': postback_data.get('partner'),
            'platform': postback_data.get('platform'),
            'source': postback_data.get('aff_sub'),
            'offer_id': postback_data.get('offer_id'),
            'offer_name': postback_data.get('offer_name'),
            'datetime_conversion': postback_data.get('datetime_conversion'),
            'order_id': postback_data.get('order_id'),
            'usd_sale_amount': postback_data.get('usd_sale_amount'),
            'usd_payout': postback_data.get('usd_payout'),
            'aff_sub': postback_data.get('aff_sub'),
            'raw_data': postback_data
        }
        
        return await client.insert_conversion(conversion_data)

class DashboardAgentStorage:
    """Dashboard-Agent 專用存儲客戶端"""
    
    def __init__(self):
        self.client: Optional[StorageClient] = None
    
    async def _get_client(self) -> StorageClient:
        if self.client is None:
            self.client = await get_storage_client('dashboard-agent')
        return self.client
    
    async def get_dashboard_data(self, days: int = 7, partner: Optional[str] = None) -> Dict:
        """獲取儀表板數據"""
        client = await self._get_client()
        
        # 並行獲取多種數據
        tasks = [
            client.get_performance_metrics(days=days, partner=partner),
            client.get_conversion_trends(days=days, partner=partner),
            client.get_partner_summary(
                partner=partner,
                start_date=datetime.now() - timedelta(days=days),
                end_date=datetime.now()
            )
        ]
        
        metrics, trends, summary = await asyncio.gather(*tasks)
        
        return {
            'performance_metrics': metrics,
            'conversion_trends': trends,
            'partner_summary': summary,
            'generated_at': datetime.now().isoformat()
        }

class ReporterAgentStorage:
    """Reporter-Agent 專用存儲客戶端"""
    
    def __init__(self):
        self.client: Optional[StorageClient] = None
    
    async def _get_client(self) -> StorageClient:
        if self.client is None:
            self.client = await get_storage_client('reporter-agent')
        return self.client
    
    async def get_report_data(self, partner: Optional[str] = None,
                            start_date: Optional[datetime] = None,
                            end_date: Optional[datetime] = None,
                            limit: Optional[int] = None) -> Dict:
        """獲取報表數據"""
        client = await self._get_client()
        
        # 並行獲取轉化數據和汇总數據
        tasks = [
            client.get_conversions(partner=partner, start_date=start_date, end_date=end_date, limit=limit),
            client.get_partner_summary(partner=partner, start_date=start_date, end_date=end_date)
        ]
        
        conversions, summary = await asyncio.gather(*tasks)
        
        return {
            'conversions': conversions,
            'summary': summary,
            'total_records': len(conversions),
            'date_range': {
                'start': start_date.isoformat() if start_date else None,
                'end': end_date.isoformat() if end_date else None
            }
        }

# =================== 工廠函數 ===================

def create_api_agent_storage() -> APIAgentStorage:
    """創建 API-Agent 存儲客戶端"""
    return APIAgentStorage()

def create_dashboard_agent_storage() -> DashboardAgentStorage:
    """創建 Dashboard-Agent 存儲客戶端"""
    return DashboardAgentStorage()

def create_reporter_agent_storage() -> ReporterAgentStorage:
    """創建 Reporter-Agent 存儲客戶端"""
    return ReporterAgentStorage()

# =================== 裝飾器 ===================

def with_storage_client(agent_name: str):
    """裝飾器：為函數注入存儲客戶端"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            client = await get_storage_client(agent_name)
            return await func(client, *args, **kwargs)
        return wrapper
    return decorator

# 使用範例：
# @with_storage_client('my-agent')
# async def my_function(storage_client: StorageClient, other_params):
#     data = await storage_client.get_conversions(partner='RAMPUP')
#     return data 