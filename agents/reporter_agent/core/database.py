#!/usr/bin/env python3
"""
PostBack数据库访问层
连接到现有的 bytec-network PostgreSQL 数据库
"""

import asyncio
import asyncpg
import pandas as pd
import json
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from dataclasses import dataclass
from decimal import Decimal

# 導入映射管理器
from agents.reporter_agent.core.mapping_manager import MappingManager

# 添加共享模块路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '../../../')
shared_path = os.path.join(project_root, 'shared')
if shared_path not in sys.path:
    sys.path.insert(0, shared_path)

# 添加项目根路径以获取config
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入统一的Source映射器
try:
    from shared.utils.source_mapper import SourceMapper
    SOURCE_MAPPER_AVAILABLE = True
except ImportError as e:
    print(f"警告: 无法导入统一映射器: {e}")
    SOURCE_MAPPER_AVAILABLE = False

from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class ConversionRecord:
    """转化记录数据类"""
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
    partner_name: str = 'Unknown'  # 添加partner_name字段
    adv_pub1: Optional[str] = None
    adv_pub2: Optional[str] = None
    adv_pub3: Optional[str] = None
    adv_pub4: Optional[str] = None
    adv_pub5: Optional[str] = None
    platform_id: Optional[str] = None  # 改為字符串類型以匹配實際表結構
    partner_id: Optional[int] = None
    source_id: Optional[int] = None

@dataclass
class PartnerSummary:
    """Partner汇总数据类"""
    partner_name: str
    partner_id: Optional[int]
    total_records: int
    total_amount: Decimal
    amount_formatted: str
    sources: List[str]
    sources_count: int
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'partner_name': self.partner_name,
            'partner_id': self.partner_id,
            'total_records': self.total_records,
            'total_amount': float(self.total_amount),
            'amount_formatted': self.amount_formatted,
            'sources': self.sources,
            'sources_count': self.sources_count
        }

# 數據庫配置 - 直接使用 ByteC-Network 配置
DB_CONFIG = {
    'host': '34.124.206.16',
    'port': 5432,
    'database': 'postback_db',
    'user': 'postback_admin',
    'password': 'ByteC2024PostBack_CloudSQL'
}

# 分批處理配置
BATCH_SIZE = 10000  # 每批處理的記錄數量

class PostbackDatabase:
    """PostBack数据库访问类 - 增強版本"""
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self.mapping_manager: Optional[MappingManager] = None
    
    def get_target_table(self) -> str:
        """根據數據來源分離配置確定目標表名 - 方案A：立即使用conversions_api"""
        try:
            # 添加項目根目錄到路徑
            import sys
            import os
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.join(current_dir, '../../../..')
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            
            import config
            if config.should_use_separate_tables():
                logger.info("🎯 數據來源分離已啟用，使用conversions_api表")
                return 'conversions_api'  # API數據專用表
            else:
                logger.info("🎯 數據來源分離未啟用，使用conversions統一表")
                return 'conversions'      # 統一表
        except Exception as e:
            logger.warning(f"⚠️ 無法讀取config，回退到conversions_api表: {e}")
            return 'conversions_api'  # 激進方案：默認使用API表

    async def init_pool(self):
        """初始化数据库连接池"""
        try:
            self.pool = await asyncpg.create_pool(**DB_CONFIG, min_size=5, max_size=20)
            logger.info("✅ Reporter-Agent數據庫連接池初始化成功")
        except Exception as e:
            logger.error(f"❌ Reporter-Agent數據庫連接池初始化失敗: {e}")
            raise

    async def init(self):
        """初始化數據庫和映射管理器"""
        if not self.pool:
            await self.init_pool()
        
        # 初始化映射管理器
        if self.mapping_manager is None:
            try:
                from .mapping_manager import MappingManager
                self.mapping_manager = MappingManager(self.pool)
                await self.mapping_manager.initialize()
                logger.info("✅ 映射管理器初始化成功")
            except Exception as e:
                logger.warning(f"⚠️ 映射管理器初始化失败: {e}, 使用基础查询模式")
                self.mapping_manager = None
    
    async def close_pool(self):
        """关闭连接池"""
        if self.pool:
            await self.pool.close()
            logger.info("✅ 数据库连接池已关闭")
    
    def _get_unified_partner_case_condition(self) -> str:
        """獲取統一的Partner CASE WHEN條件，與config.py中的match_source_to_partner函數保持一致"""
        return """
        CASE 
            WHEN (c.aff_sub1 LIKE 'OPPO%' OR c.aff_sub1 LIKE 'VIVO%' OR c.aff_sub1 LIKE 'OEM1%' OR c.aff_sub1 LIKE 'OEM2%' OR c.aff_sub1 LIKE 'OEM3%' OR c.aff_sub1 LIKE 'XIAOMI%') THEN 'DeepLeaper'
            WHEN (c.aff_sub1 LIKE 'RAMPUP%' OR c.aff_sub1 LIKE 'RPID%' OR c.aff_sub1 LIKE 'AF%') THEN 'RAMPUP'
            WHEN c.aff_sub1 = 'MP' THEN 'MP'
            WHEN c.aff_sub1 LIKE 'MKK%' THEN 'MKK'
            WHEN c.aff_sub1 LIKE 'TestPartner%' THEN 'TestPartner'
            WHEN c.aff_sub1 IS NOT NULL THEN 'ByteC'
            ELSE COALESCE(c.partner, 'Unknown')
        END
        """

    def _get_partner_filter_condition(self, partner_name: str) -> tuple:
        """根據 partner 名稱獲取對應的過濾條件，與config.py中的match_source_to_partner函數保持一致
        
        Returns:
            tuple: (condition_sql, param_value) 或者 None 如果是 ALL
        """
        if not partner_name or partner_name.upper() == 'ALL':
            return None
            
        partner_upper = partner_name.upper()
        
        # 統一的 Partner 到 aff_sub1 模式映射，與config.py中的match_source_to_partner函數保持一致
        partner_mapping = {
            'DEEPLEAPER': "(c.aff_sub1 LIKE 'OPPO%' OR c.aff_sub1 LIKE 'VIVO%' OR c.aff_sub1 LIKE 'OEM1%' OR c.aff_sub1 LIKE 'OEM2%' OR c.aff_sub1 LIKE 'OEM3%' OR c.aff_sub1 LIKE 'XIAOMI%')",
            'RAMPUP': "(c.aff_sub1 LIKE 'RAMPUP%' OR c.aff_sub1 LIKE 'RPID%' OR c.aff_sub1 LIKE 'AF%')",
            'MP': "c.aff_sub1 = 'MP'",
            'MKK': "c.aff_sub1 LIKE 'MKK%'",
            'TESTPARTNER': "c.aff_sub1 LIKE 'TestPartner%'",
            'FTK': "c.aff_sub1 LIKE 'FTK%'",
            'BYTEC': "c.aff_sub1 IS NOT NULL"
        }
        
        if partner_upper in partner_mapping:
            return (partner_mapping[partner_upper], None)  # 無需參數，直接使用條件
        else:
            # 如果沒有映射，回退到原有的 partner 欄位查詢
            return ("c.partner = $PARAM", partner_name)
    
    async def get_available_partners(self) -> List[str]:
        """获取可用的Partner列表 - 從目標表查詢"""
        if not self.pool:
            await self.init_pool()
        
        try:
            target_table = self.get_target_table()
            async with self.pool.acquire() as conn:
                # 從目標表獲取可用的Partner列表
                query = f"""
                SELECT DISTINCT c.partner
                FROM {target_table} c
                WHERE c.partner IS NOT NULL
                ORDER BY c.partner
                """
                rows = await conn.fetch(query)
                partners = [row['partner'] for row in rows]
                
                # 如果有數據，默認添加 "ALL" 選項
                if partners:
                    partners.insert(0, "ALL")
                
                logger.info(f"✅ 從{target_table}表獲取可用Partner列表: {partners}")
                return partners
        except Exception as e:
            logger.error(f"❌ 获取Partner列表失败: {e}")
            import traceback
            logger.error(f"詳細錯誤: {traceback.format_exc()}")
            raise
    
    async def get_conversions_by_partner(self, partner_name: str = None, 
                                       start_date: datetime = None,
                                       end_date: datetime = None,
                                       limit: Optional[int] = None,
                                       include_invalid: bool = False) -> List[ConversionRecord]:
        """獲取Partner轉化數據 - 使用統一字段邏輯和目標表"""
        if not self.pool:
            await self.init_pool()
        
        try:
            target_table = self.get_target_table()
            async with self.pool.acquire() as conn:
                # 獲取總記錄數進行分批處理判斷
                count_query = f"SELECT COUNT(*) as total_count FROM {target_table} c WHERE 1=1"
                count_params = []
                count_param_count = 0
                
                # 添加Partner過濾
                partner_filter = self._get_partner_filter_condition(partner_name)
                if partner_filter:
                    condition_sql, param_value = partner_filter
                    if param_value is not None:
                        # 需要參數的情況
                        count_param_count += 1
                        count_query += f" AND {condition_sql.replace('$PARAM', f'${count_param_count}')}"
                        count_params.append(param_value)
                    else:
                        # 直接條件，無需參數
                        count_query += f" AND {condition_sql}"
                
                # 添加時間範圍過濾 - 優化：使用範圍查詢而不是DATE函數以利用索引
                if start_date:
                    count_param_count += 1
                    # 使用範圍查詢替代DATE函數，這樣可以使用datetime_conversion索引
                    count_query += f" AND c.datetime_conversion >= ${count_param_count}::timestamp"
                    count_params.append(start_date)
                
                if end_date:
                    count_param_count += 1
                    # 結束日期加上23:59:59確保包含整天
                    end_datetime = end_date
                    if hasattr(end_date, 'replace'):
                        end_datetime = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                    count_query += f" AND c.datetime_conversion <= ${count_param_count}::timestamp"
                    count_params.append(end_datetime)
                
                # 添加狀態過濾條件
                if include_invalid:
                    # 包含所有狀態，包括 invalid
                    count_query += " AND (c.conversion_status IN ('approved', 'pending', 'invalid', 'rejected') OR c.conversion_status IS NULL)"
                else:
                    # 只包含 approved 和 pending
                    count_query += " AND (c.conversion_status IN ('approved', 'pending') OR c.conversion_status IS NULL)"
                
                # 獲取總記錄數
                total_count_row = await conn.fetchrow(count_query, *count_params)
                total_count = total_count_row['total_count'] if total_count_row else 0
                
                # 如果有limit限制，調整總數
                if limit and limit < total_count:
                    total_count = limit
                
                logger.info(f"🔍 執行查詢: Partner={partner_name}, 日期={start_date} 至 {end_date}, 總記錄數={total_count:,}, 目標表={target_table}, 包含無效={include_invalid}")
                
                # 如果記錄數較少，使用原有邏輯
                if total_count <= BATCH_SIZE:
                    return await self._fetch_single_batch(conn, partner_name, start_date, end_date, limit, include_invalid)
                
                # 大數據量使用分批處理
                logger.info(f"📊 數據量較大 ({total_count:,} 條)，啟用分批處理 (每批 {BATCH_SIZE:,} 條)")
                
                # 構建基礎查詢 - 方案A：激進統一字段邏輯，適配實際表結構
                base_query = f"""
                SELECT 
                    c.id,
                    COALESCE(c.tenant_id, 1) as tenant_id,
                    COALESCE(c.conversion_id::text, c.id::text) as conversion_id,
                    c.offer_id,
                    c.offer_name,
                    c.datetime_conversion,
                    COALESCE(c.order_id, c.conversion_id::text) as order_id,
                    c.usd_sale_amount,  -- 激進：只使用usd_sale_amount
                    c.usd_payout,       -- 激進：只使用usd_payout
                    c.aff_sub1 as aff_sub,
                    COALESCE(c.aff_sub2, '') as aff_sub2,
                    COALESCE(c.aff_sub3, '') as aff_sub3,
                    COALESCE(c.aff_sub4, '') as aff_sub4,
                    COALESCE(c.adv_sub1, '') as adv_pub1,
                    COALESCE(c.adv_sub2, '') as adv_pub2,
                    COALESCE(c.adv_sub3, '') as adv_pub3,
                    COALESCE(c.adv_sub4, '') as adv_pub4,
                    COALESCE(c.adv_sub5, '') as adv_pub5,
                    COALESCE(c.conversion_status, 'pending') as status,
                    COALESCE(c.created_at, c.datetime_conversion, NOW()) as received_at,
                    COALESCE(c.partner, 'Unknown') as partner_name,
                    c.platform,         -- 使用實際存在的platform欄位
                    c.partner           -- 使用實際存在的partner欄位
                FROM {target_table} c
                WHERE 1=1
                """
                
                params = []
                param_count = 0
                
                # 添加Partner過濾
                if partner_filter:
                    condition_sql, param_value = partner_filter
                    if param_value is not None:
                        param_count += 1
                        base_query += f" AND {condition_sql.replace('$PARAM', f'${param_count}')}"
                        params.append(param_value)
                    else:
                        base_query += f" AND {condition_sql}"
                
                # 添加時間範圍過濾 - 優化：使用範圍查詢而不是DATE函數以利用索引
                if start_date:
                    param_count += 1
                    # 使用範圍查詢替代DATE函數，這樣可以使用datetime_conversion索引
                    base_query += f" AND c.datetime_conversion >= ${param_count}::timestamp"
                    if hasattr(start_date, 'replace'):
                        start_date = start_date.replace(microsecond=0, tzinfo=None)
                    params.append(start_date)
                
                if end_date:
                    param_count += 1
                    # 結束日期加上23:59:59確保包含整天
                    end_datetime = end_date
                    if hasattr(end_date, 'replace'):
                        end_datetime = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                    base_query += f" AND c.datetime_conversion <= ${param_count}::timestamp"
                    params.append(end_datetime)
                
                # 添加狀態過濾條件
                if include_invalid:
                    # 包含所有狀態，包括 invalid
                    base_query += " AND (c.conversion_status IN ('approved', 'pending', 'invalid', 'rejected') OR c.conversion_status IS NULL)"
                else:
                    # 只包含 approved 和 pending
                    base_query += " AND (c.conversion_status IN ('approved', 'pending') OR c.conversion_status IS NULL)"
                
                # 添加排序 - 優先顯示有aff_sub1值的記錄
                base_query += " ORDER BY (CASE WHEN c.aff_sub1 IS NOT NULL AND c.aff_sub1 != '' THEN 0 ELSE 1 END), c.datetime_conversion DESC"
                
                # 分批處理
                all_conversions = []
                total_batches = (total_count + BATCH_SIZE - 1) // BATCH_SIZE
                
                for batch_idx in range(total_batches):
                    offset = batch_idx * BATCH_SIZE
                    batch_limit = min(BATCH_SIZE, total_count - offset)
                    
                    if limit and len(all_conversions) >= limit:
                        break
                    
                    batch_query = base_query + f" OFFSET {offset} LIMIT {batch_limit}"
                    batch_rows = await conn.fetch(batch_query, *params)
                    
                    logger.info(f"📦 處理批次 {batch_idx + 1}/{total_batches}: {len(batch_rows)} 條記錄")
                    
                    batch_conversions = []
                    for row in batch_rows:
                        # 處理 partner 和 platform 資訊
                        partner_str = row.get('partner') or 'Unknown'
                        platform_str = row.get('platform') or 'Unknown'
                        
                        # 獲取 partner_id 和 source_id（如果映射管理器可用）
                        partner_id = None
                        if self.mapping_manager and partner_str != 'Unknown':
                            partner_id = await self.mapping_manager.get_partner_id(partner_str)
                        
                        source_id = None
                        if row.get('aff_sub') and self.mapping_manager:
                            source_id = await self.mapping_manager.get_or_create_source_id(row['aff_sub'])
                        
                        batch_conversions.append(ConversionRecord(
                            id=row['id'],
                            tenant_id=row['tenant_id'],
                            conversion_id=row['conversion_id'],
                            offer_id=row['offer_id'],
                            offer_name=row['offer_name'],
                            datetime_conversion=row['datetime_conversion'],
                            order_id=row['order_id'],
                            usd_sale_amount=Decimal(str(row['usd_sale_amount'])) if row['usd_sale_amount'] else Decimal('0'),
                            usd_payout=Decimal(str(row['usd_payout'])) if row['usd_payout'] else Decimal('0'),
                            aff_sub=row['aff_sub'],
                            aff_sub2=row['aff_sub2'],
                            aff_sub3=row['aff_sub3'],
                            aff_sub4=row['aff_sub4'],
                            adv_pub1=row['adv_pub1'],
                            adv_pub2=row['adv_pub2'],
                            adv_pub3=row['adv_pub3'],
                            adv_pub4=row['adv_pub4'],
                            adv_pub5=row['adv_pub5'],
                            status=row['status'],
                            received_at=row['received_at'],
                            tenant_name=f"tenant_{row['tenant_id']}",
                            partner_name=partner_str,  # 確保partner_name被正確設置
                            platform_id=platform_str,  # 使用字符串而非ID
                            partner_id=partner_id,
                            source_id=source_id
                        ))
                    
                    all_conversions.extend(batch_conversions)
                    
                    # 如果達到limit限制，停止處理
                    if limit and len(all_conversions) >= limit:
                        all_conversions = all_conversions[:limit]
                        break
                
                logger.info(f"✅ 完成分批查詢: 總共獲取 {len(all_conversions):,} 條記錄")
                return all_conversions
                
        except Exception as e:
            logger.error(f"❌ 获取转化数据失败: {e}")
            import traceback
            logger.error(f"詳細錯誤: {traceback.format_exc()}")
            raise

    async def get_invalid_conversion_stats(self, partner_name: str = None,
                                         start_date: datetime = None,
                                         end_date: datetime = None,
                                         limit: Optional[int] = None) -> Dict[str, Any]:
        """獲取無效轉化統計信息"""
        if not self.pool:
            await self.init_pool()
        
        try:
            target_table = self.get_target_table()
            async with self.pool.acquire() as conn:
                # 構建查詢
                query = f"""
                SELECT 
                    COUNT(*) as invalid_count,
                    COALESCE(SUM(c.usd_sale_amount), 0) as invalid_amount
                FROM {target_table} c
                WHERE 1=1
                """
                
                params = []
                param_count = 0
                
                # 添加Partner過濾
                partner_filter = self._get_partner_filter_condition(partner_name)
                if partner_filter:
                    condition_sql, param_value = partner_filter
                    if param_value is not None:
                        param_count += 1
                        query += f" AND {condition_sql.replace('$PARAM', f'${param_count}')}"
                        params.append(param_value)
                    else:
                        query += f" AND {condition_sql}"
                
                # 添加時間範圍過濾 - 優化：使用範圍查詢而不是DATE函數以利用索引
                if start_date:
                    param_count += 1
                    # 使用範圍查詢替代DATE函數，這樣可以使用datetime_conversion索引
                    query += f" AND c.datetime_conversion >= ${param_count}::timestamp"
                    if hasattr(start_date, 'replace'):
                        start_date = start_date.replace(microsecond=0, tzinfo=None)
                    params.append(start_date)
                
                if end_date:
                    param_count += 1
                    # 結束日期加上23:59:59確保包含整天
                    end_datetime = end_date
                    if hasattr(end_date, 'replace'):
                        end_datetime = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                    query += f" AND c.datetime_conversion <= ${param_count}::timestamp"
                    params.append(end_datetime)
                
                # 查詢無效和拒絕狀態
                query += " AND c.conversion_status IN ('invalid', 'rejected')"
                
                # 如果有limit限制，需要先獲取符合條件的記錄ID，然後統計
                if limit is not None:
                    # 先獲取符合條件的記錄ID（按時間倒序）
                    id_query = f"""
                    SELECT c.id, c.usd_sale_amount
                    FROM {target_table} c
                    WHERE 1=1
                    """
                    
                    id_params = []
                    id_param_count = 0
                    
                    # 添加相同的過濾條件
                    if partner_filter:
                        condition_sql, param_value = partner_filter
                        if param_value is not None:
                            id_param_count += 1
                            id_query += f" AND {condition_sql.replace('$PARAM', f'${id_param_count}')}"
                            id_params.append(param_value)
                        else:
                            id_query += f" AND {condition_sql}"
                    
                    if start_date:
                        id_param_count += 1
                        id_query += f" AND c.datetime_conversion >= ${id_param_count}::timestamp"
                        id_params.append(start_date)
                    
                    if end_date:
                        id_param_count += 1
                        id_query += f" AND c.datetime_conversion <= ${id_param_count}::timestamp"
                        id_params.append(end_date)
                    
                    id_query += " AND c.conversion_status IN ('invalid', 'rejected')"
                    id_query += f" ORDER BY c.datetime_conversion DESC LIMIT ${id_param_count + 1}"
                    id_params.append(limit)
                    
                    # 獲取符合條件的記錄
                    rows = await conn.fetch(id_query, *id_params)
                    
                    # 統計無效轉化
                    invalid_count = len(rows)
                    invalid_amount = sum(float(row['usd_sale_amount']) if row['usd_sale_amount'] else 0.0 for row in rows)
                    
                else:
                    # 沒有limit限制，直接統計
                    result = await conn.fetchrow(query, *params)
                    invalid_count = result['invalid_count'] if result else 0
                    invalid_amount = float(result['invalid_amount']) if result and result['invalid_amount'] else 0.0
                
                logger.info(f"🔍 無效轉化統計: Partner={partner_name}, 無效數量={invalid_count}, 無效金額=${invalid_amount:,.2f}")
                
                return {
                    'invalid_count': invalid_count,
                    'invalid_amount': invalid_amount
                }
                
        except Exception as e:
            logger.error(f"❌ 獲取無效轉化統計失敗: {e}")
            return {
                'invalid_count': 0,
                'invalid_amount': 0.0
            }

    async def _fetch_single_batch(self, conn, partner_name: str = None, 
                                start_date: datetime = None,
                                end_date: datetime = None,
                                limit: Optional[int] = None,
                                include_invalid: bool = False) -> List[ConversionRecord]:
        """獲取單批轉化數據"""
        try:
            target_table = self.get_target_table()
            
            # 構建查詢 - 方案A：激進統一字段邏輯，適配實際表結構
            query = f"""
            SELECT 
                c.id,
                COALESCE(c.tenant_id, 1) as tenant_id,
                COALESCE(c.conversion_id::text, c.id::text) as conversion_id,
                c.offer_id,
                c.offer_name,
                c.datetime_conversion,
                COALESCE(c.order_id, c.conversion_id::text) as order_id,
                c.usd_sale_amount,  -- 激進：只使用usd_sale_amount
                c.usd_payout,       -- 激進：只使用usd_payout
                c.aff_sub1 as aff_sub,  -- 修復：使用aff_sub1字段
                COALESCE(c.aff_sub2, '') as aff_sub2,
                COALESCE(c.aff_sub3, '') as aff_sub3,
                COALESCE(c.aff_sub4, '') as aff_sub4,
                COALESCE(c.adv_sub1, '') as adv_pub1,
                COALESCE(c.adv_sub2, '') as adv_pub2,
                COALESCE(c.adv_sub3, '') as adv_pub3,
                COALESCE(c.adv_sub4, '') as adv_pub4,
                COALESCE(c.adv_sub5, '') as adv_pub5,
                COALESCE(c.conversion_status, 'pending') as status,
                COALESCE(c.created_at, c.datetime_conversion, NOW()) as received_at,
                COALESCE(c.partner, 'Unknown') as partner_name,
                c.platform,         -- 使用實際存在的platform欄位
                c.partner           -- 使用實際存在的partner欄位
            FROM {target_table} c
            WHERE 1=1
            """
            
            params = []
            param_count = 0
            
            # 添加Partner過濾
            partner_filter = self._get_partner_filter_condition(partner_name)
            if partner_filter:
                condition_sql, param_value = partner_filter
                if param_value is not None:
                    param_count += 1
                    query += f" AND {condition_sql.replace('$PARAM', f'${param_count}')}"
                    params.append(param_value)
                else:
                    query += f" AND {condition_sql}"
            
            # 添加時間範圍過濾 - 優化：使用範圍查詢而不是DATE函數以利用索引
            if start_date:
                param_count += 1
                # 使用範圍查詢替代DATE函數，這樣可以使用datetime_conversion索引
                query += f" AND c.datetime_conversion >= ${param_count}::timestamp"
                if hasattr(start_date, 'replace'):
                    start_date = start_date.replace(microsecond=0, tzinfo=None)
                params.append(start_date)
            
            if end_date:
                param_count += 1
                # 結束日期加上23:59:59確保包含整天
                end_datetime = end_date
                if hasattr(end_date, 'replace'):
                    end_datetime = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                query += f" AND c.datetime_conversion <= ${param_count}::timestamp"
                params.append(end_datetime)
            
            # 添加狀態過濾條件
            if include_invalid:
                # 包含所有狀態，包括 invalid
                query += " AND (c.conversion_status IN ('approved', 'pending', 'invalid', 'rejected') OR c.conversion_status IS NULL)"
            else:
                # 只包含 approved 和 pending
                query += " AND (c.conversion_status IN ('approved', 'pending') OR c.conversion_status IS NULL)"
            
            # 添加排序和限制 - 優先顯示有aff_sub1值的記錄
            query += " ORDER BY (CASE WHEN c.aff_sub1 IS NOT NULL AND c.aff_sub1 != '' THEN 0 ELSE 1 END), c.datetime_conversion DESC"
            if limit:
                query += f" LIMIT {limit}"
            
            # 執行查詢
            rows = await conn.fetch(query, *params)
            
            conversions = []
            for row in rows:
                # 處理 partner 和 platform 資訊
                partner_str = row.get('partner') or 'Unknown'
                platform_str = row.get('platform') or 'Unknown'
                
                # 獲取 partner_id 和 source_id（如果映射管理器可用）
                partner_id = None
                if self.mapping_manager and partner_str != 'Unknown':
                    partner_id = await self.mapping_manager.get_partner_id(partner_str)
                
                source_id = None
                if row.get('aff_sub') and self.mapping_manager:
                    source_id = await self.mapping_manager.get_or_create_source_id(row['aff_sub'])
                
                conversions.append(ConversionRecord(
                    id=row['id'],
                    tenant_id=row['tenant_id'],
                    conversion_id=row['conversion_id'],
                    offer_id=row['offer_id'],
                    offer_name=row['offer_name'],
                    datetime_conversion=row['datetime_conversion'],
                    order_id=row['order_id'],
                    usd_sale_amount=Decimal(str(row['usd_sale_amount'])) if row['usd_sale_amount'] else Decimal('0'),
                    usd_payout=Decimal(str(row['usd_payout'])) if row['usd_payout'] else Decimal('0'),
                    aff_sub=row['aff_sub'],
                    aff_sub2=row['aff_sub2'],
                    aff_sub3=row['aff_sub3'],
                    aff_sub4=row['aff_sub4'],
                    adv_pub1=row['adv_pub1'],
                    adv_pub2=row['adv_pub2'],
                    adv_pub3=row['adv_pub3'],
                    adv_pub4=row['adv_pub4'],
                    adv_pub5=row['adv_pub5'],
                    status=row['status'],
                    received_at=row['received_at'],
                    tenant_name=f"tenant_{row['tenant_id']}",
                    partner_name=partner_str,  # 確保partner_name被正確設置
                    platform_id=platform_str,  # 使用字符串而非ID
                    partner_id=partner_id,
                    source_id=source_id
                ))
            
            return conversions
            
        except Exception as e:
            logger.error(f"❌ 獲取單批轉化數據失敗: {e}")
            raise

    async def get_partner_summary(self, partner_name: str = None,
                                start_date: datetime = None,
                                end_date: datetime = None,
                                limit: Optional[int] = None) -> List[PartnerSummary]:
        """
        獲取Partner汇总数据 - 方案A：使用統一字段邏輯和目標表
        
        Args:
            partner_name: Partner名称，为None或"ALL"时获取所有Partner
            start_date: 开始日期
            end_date: 结束日期
            limit: 限制处理的记录数量
            
        Returns:
            List[PartnerSummary]: Partner汇总列表
        """
        if not self.pool:
            await self.init_pool()
        
        # 设置默认日期范围（过去7天）
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=7)
        
        try:
            target_table = self.get_target_table()
            async with self.pool.acquire() as conn:
                # 方案A：激進統一字段邏輯，使用目標表
                unified_case = self._get_unified_partner_case_condition()
                base_query = f"""
                SELECT 
                    {unified_case} as partner_name,
                    COUNT(*) as total_records,
                    SUM(c.usd_sale_amount) as total_amount,  -- 激進：只使用usd_sale_amount
                    array_agg(DISTINCT c.aff_sub1) FILTER (WHERE c.aff_sub1 IS NOT NULL) as sources
                FROM {target_table} c
                WHERE 1=1
                """
                
                params = []
                param_count = 0
                
                # 添加Partner過濾 - 使用統一邏輯
                if partner_name and partner_name.upper() != 'ALL':
                    partner_filter = self._get_partner_filter_condition(partner_name)
                    if partner_filter:
                        condition_sql, param_value = partner_filter
                        if param_value is not None:
                            param_count += 1
                            base_query += f" AND {condition_sql.replace('$PARAM', f'${param_count}')}"
                            params.append(param_value)
                        else:
                            base_query += f" AND {condition_sql}"
                
                # 添加時間範圍過濾 - 優化：使用範圍查詢而不是DATE函數以利用索引
                if start_date:
                    param_count += 1
                    # 使用範圍查詢替代DATE函數，這樣可以使用datetime_conversion索引
                    base_query += f" AND c.datetime_conversion >= ${param_count}::timestamp"
                    if hasattr(start_date, 'replace'):
                        start_date = start_date.replace(microsecond=0, tzinfo=None)
                    params.append(start_date)
                
                if end_date:
                    param_count += 1
                    # 結束日期加上23:59:59確保包含整天
                    end_datetime = end_date
                    if hasattr(end_date, 'replace'):
                        end_datetime = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                    base_query += f" AND c.datetime_conversion <= ${param_count}::timestamp"
                    params.append(end_datetime)
                
                # 添加狀態過濾條件 - 包含有效状态：processing, completed, approved, pending
                # 排除无效状态：cancelled, invalid, rejected, failed
                base_query += """ AND (
                    c.conversion_status IS NULL OR 
                    LOWER(c.conversion_status) NOT LIKE '%cancelled%' AND
                    LOWER(c.conversion_status) NOT LIKE '%canceled%' AND  
                    LOWER(c.conversion_status) NOT LIKE '%invalid%' AND
                    LOWER(c.conversion_status) NOT LIKE '%rejected%' AND
                    LOWER(c.conversion_status) NOT LIKE '%failed%' AND
                    LOWER(c.conversion_status) NOT LIKE '%decline%'
                )"""
                
                # 添加分組和排序
                base_query += " GROUP BY partner_name ORDER BY total_records DESC"
                
                # 添加limit限制
                if limit:
                    param_count += 1
                    base_query += f" LIMIT ${param_count}"
                    params.append(limit)
                
                logger.info(f"🔍 執行統一Partner汇总查詢: Partner={partner_name}, 日期={start_date} 至 {end_date}, 目標表={target_table}")
                
                rows = await conn.fetch(base_query, *params)
                
                summaries = []
                for row in rows:
                    partner_name_db = row['partner_name'] or 'Unknown'
                    total_records = row['total_records']
                    total_amount = Decimal(str(row['total_amount'])) if row['total_amount'] else Decimal('0')
                    sources = row['sources'] or []
                    
                    # 獲取 partner_id
                    partner_id = None
                    if self.mapping_manager:
                        partner_id = await self.mapping_manager.get_partner_id(partner_name_db)
                    
                    summary = PartnerSummary(
                        partner_name=partner_name_db,
                        partner_id=partner_id,
                        total_records=total_records,
                        total_amount=total_amount,
                        amount_formatted=f"${total_amount:,.2f}",
                        sources=sources,
                        sources_count=len(sources)
                    )
                    summaries.append(summary)
                
                logger.info(f"✅ 获取統一Partner汇总成功: {len(summaries)} 个Partner")
                for summary in summaries:
                    logger.info(f"   - {summary.partner_name}: {summary.total_records:,} 条记录, {summary.amount_formatted}")
                
                return summaries
                
        except Exception as e:
            logger.error(f"❌ 获取Partner汇总失败: {e}")
            import traceback
            logger.error(f"詳細錯誤: {traceback.format_exc()}")
            raise

    async def get_conversion_dataframe(self, partner_name: str = None,
                                     start_date: datetime = None,
                                     end_date: datetime = None,
                                     limit: Optional[int] = None) -> pd.DataFrame:
        """获取转化数据的 DataFrame - 使用統一字段邏輯"""
        try:
            logger.info(f"🔍 準備生成DataFrame: Partner={partner_name}, 日期={start_date} 至 {end_date}")
            
            # 獲取轉化數據（只包含有效狀態：pending/approved，與 partner_summary 保持一致）
            conversions = await self.get_conversions_by_partner(
                partner_name=partner_name,
                start_date=start_date,
                end_date=end_date,
                limit=limit,
                include_invalid=False  # 修復：只包含有效狀態（pending/approved），避免查詢所有記錄
            )
            
            # 獲取無效轉化統計
            invalid_stats = await self.get_invalid_conversion_stats(
                partner_name=partner_name,
                start_date=start_date,
                end_date=end_date,
                limit=limit  # 傳遞 limit 參數
            )
            
            if not conversions and invalid_stats['invalid_count'] == 0:
                logger.warning("⚠️ 沒有找到轉化數據")
                return pd.DataFrame()
            
            logger.info(f"✅ 獲取到 {len(conversions)} 條轉化數據（包含所有狀態），{invalid_stats['invalid_count']} 條無效轉化")
            
            data = []
            for conv in conversions:
                # 確定Partner名稱
                partner_display = conv.partner_name if hasattr(conv, 'partner_name') and conv.partner_name else 'Unknown'
                if not partner_display or partner_display == 'Unknown':
                    # 嘗試通過Source推斷Partner
                    if conv.aff_sub:
                        try:
                            import sys
                            import os
                            current_dir = os.path.dirname(os.path.abspath(__file__))
                            project_root = os.path.join(current_dir, '../../../..')
                            if project_root not in sys.path:
                                sys.path.insert(0, project_root)
                            from config import match_source_to_partner
                            partner_display = match_source_to_partner(conv.aff_sub)
                        except:
                            partner_display = 'Unknown'
                
                # 移除時區信息以支持Excel輸出
                conversion_date = conv.datetime_conversion
                if conversion_date and hasattr(conversion_date, 'replace') and conversion_date.tzinfo:
                    conversion_date = conversion_date.replace(tzinfo=None)
                
                received_at = conv.received_at
                if received_at and hasattr(received_at, 'replace') and received_at.tzinfo:
                    received_at = received_at.replace(tzinfo=None)
                
                # 方案A：激進統一字段邏輯 - 直接使用usd_sale_amount，無回退
                sale_amount = float(conv.usd_sale_amount) if conv.usd_sale_amount else 0.0
                payout_amount = float(conv.usd_payout) if conv.usd_payout else 0.0
                
                # 应用mockup调整（根据config.py设置）
                try:
                    import sys
                    import os
                    current_dir = os.path.dirname(os.path.abspath(__file__))
                    project_root = os.path.join(current_dir, '../../../..')
                    if project_root not in sys.path:
                        sys.path.insert(0, project_root)
                    
                    import config
                    is_bytec_partner = (
                        partner_display.upper() == 'BYTEC' or
                        partner_display.upper() == 'BYTEC-NETWORK' or
                        'BYTEC' in partner_display.upper()
                    )
                    
                    # 应用mockup调整 - 只有ByteC Partner才調整，其他Partner使用原始金額
                    if is_bytec_partner:
                        processed_sale_amount = sale_amount * config.BYTEC_MOCKUP_MULTIPLIER
                        logger.debug(f"ByteC Partner調整: {sale_amount} * {config.BYTEC_MOCKUP_MULTIPLIER} = {processed_sale_amount}")
                    else:
                        # 非ByteC Partner使用原始金額，不進行調整
                        processed_sale_amount = sale_amount
                        logger.debug(f"非ByteC Partner使用原始金額: {sale_amount}")
                except Exception as e:
                    # 如果無法讀取config，不應用調整
                    processed_sale_amount = sale_amount
                    logger.warning(f"無法讀取config，使用原始金額: {e}")
                
                # 生成正確的Source：直接使用aff_sub1的原始数值，不进行映射
                if conv.aff_sub and conv.aff_sub.strip():
                    source_name = conv.aff_sub.strip()  # 直接使用aff_sub1的原始值
                elif conv.aff_sub2 and conv.aff_sub2.strip():
                    source_name = conv.aff_sub2.strip()  # 备用：使用aff_sub2
                elif conv.aff_sub3 and conv.aff_sub3.strip():
                    source_name = conv.aff_sub3.strip()  # 备用：使用aff_sub3
                elif conv.aff_sub4 and conv.aff_sub4.strip():
                    source_name = conv.aff_sub4.strip()  # 备用：使用aff_sub4
                else:
                    source_name = 'Unknown'  # 如果所有aff_sub都为空

                # 包含所有數據庫欄位，使用統一的字段邏輯
                data.append({
                    'Conversion ID': conv.conversion_id,
                    'Offer ID': conv.offer_id,
                    'Offer Name': conv.offer_name,
                    'Datetime Conversion': conversion_date,
                    'Order ID': conv.order_id,
                    'USD Sale Amount': processed_sale_amount,  # 統一使用USD金額
                    'USD Payout': payout_amount,               # 統一使用USD佣金
                    'Aff Sub1': conv.aff_sub if conv.aff_sub else '',  # 改为Aff Sub1
                    'Aff Sub2': conv.aff_sub2 if conv.aff_sub2 else '',
                    'Aff Sub3': conv.aff_sub3 if conv.aff_sub3 else '',
                    'Aff Sub4': conv.aff_sub4 if conv.aff_sub4 else '',
                    'Adv Pub1': conv.adv_pub1 if conv.adv_pub1 else '',
                    'Adv Pub2': conv.adv_pub2 if conv.adv_pub2 else '',
                    'Adv Pub3': conv.adv_pub3 if conv.adv_pub3 else '',
                    'Adv Pub4': conv.adv_pub4 if conv.adv_pub4 else '',
                    'Adv Pub5': conv.adv_pub5 if conv.adv_pub5 else '',
                    'Status': conv.status if conv.status else 'pending',
                    'Partner': partner_display,
                    'Partner ID': conv.partner_id,
                    'Source': source_name,  # 使用新的Source生成邏輯
                    'Source ID': conv.source_id
                })
            
            df = pd.DataFrame(data)
            
            # 添加Partner过滤
            if partner_name and partner_name.upper() != 'ALL':
                df = df[df['Partner'].str.contains(partner_name, case=False, na=False)]
            
            # 应用limit限制
            if limit and len(df) > limit:
                logger.info(f"📊 应用limit限制: 从 {len(df)} 条记录限制到 {limit} 条")
                df = df.head(limit)
            
            # 應用 REMOVE_COLUMNS 配置移除指定欄位
            try:
                import config
                
                # 確定要移除的欄位列表
                if partner_name and 'BYTEC' in partner_name.upper():
                    # ByteC Partner 使用 BYTEC_REMOVE_COLUMNS（通常為空列表）
                    columns_to_remove = config.BYTEC_REMOVE_COLUMNS
                    logger.info(f"📋 ByteC Partner 模式：不移除欄位")
                else:
                    # 其他 Partner 使用 REMOVE_COLUMNS
                    columns_to_remove = config.REMOVE_COLUMNS
                    logger.info(f"📋 一般 Partner 模式：將移除欄位 {columns_to_remove}")
                
                # 移除存在於 DataFrame 中的指定欄位
                existing_columns_to_remove = [col for col in columns_to_remove if col in df.columns]
                missing_columns = [col for col in columns_to_remove if col not in df.columns]
                
                # 確保 Source ID 被移除（硬編碼修復）
                if 'Source ID' in df.columns:
                    existing_columns_to_remove.append('Source ID')
                    logger.info(f"🔧 強制添加移除字段: Source ID")
                
                if existing_columns_to_remove:
                    df = df.drop(columns=existing_columns_to_remove)
                    logger.info(f"✅ 已移除欄位: {existing_columns_to_remove}")
                
                if missing_columns:
                    logger.debug(f"📋 配置中的欄位不存在於DataFrame: {missing_columns}")
                    
            except Exception as e:
                logger.warning(f"⚠️ 應用REMOVE_COLUMNS配置時出錯: {e}")

            # 將無效轉化統計添加到DataFrame的屬性中
            df.attrs['invalid_stats'] = invalid_stats

            logger.info(f"✅ DataFrame生成完成: {len(df)} 條記錄（包含所有狀態），無效轉化: {invalid_stats['invalid_count']} 條")
            return df
            
        except Exception as e:
            logger.error(f"❌ 生成DataFrame失败: {e}")
            import traceback
            logger.error(f"詳細錯誤: {traceback.format_exc()}")
            raise

    async def health_check(self) -> Dict[str, Any]:
        """健康检查 - 檢查目標表"""
        try:
            if not self.pool:
                await self.init_pool()
            
            target_table = self.get_target_table()
            
            async with self.pool.acquire() as conn:
                # 检查数据库连接
                version = await conn.fetchval("SELECT version()")
                
                # 检查目標数据表
                target_count = await conn.fetchval(f"SELECT COUNT(*) FROM {target_table}")
                
                health_info = {
                    'status': 'healthy',
                    'database_version': version,
                    'target_table': target_table,
                    'target_table_count': target_count,
                    'mapping_manager': self.mapping_manager is not None
                }
                
                logger.info(f"✅ 健康檢查通過: {health_info}")
                return health_info
                
        except Exception as e:
            logger.error(f"❌ 健康检查失败: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            } 