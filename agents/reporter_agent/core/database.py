#!/usr/bin/env python3
"""
PostBack数据库访问层
连接到现有的 bytec-network PostgreSQL 数据库
"""

import asyncio
import asyncpg
import pandas as pd
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from dataclasses import dataclass
from decimal import Decimal

# 導入映射管理器
from .mapping_manager import MappingManager

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
    adv_pub1: Optional[str] = None
    adv_pub2: Optional[str] = None
    adv_pub3: Optional[str] = None
    adv_pub4: Optional[str] = None
    adv_pub5: Optional[str] = None
    platform_id: Optional[int] = None
    partner_id: Optional[int] = None
    source_id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'conversion_id': self.conversion_id,
            'offer_id': self.offer_id,
            'offer_name': self.offer_name,
            'datetime_conversion': self.datetime_conversion.isoformat() if self.datetime_conversion else None,
            'order_id': self.order_id,
            'usd_sale_amount': float(self.usd_sale_amount) if self.usd_sale_amount else 0.0,
            'usd_payout': float(self.usd_payout) if self.usd_payout else 0.0,
            'aff_sub': self.aff_sub,
            'aff_sub2': self.aff_sub2,
            'aff_sub3': self.aff_sub3,
            'aff_sub4': self.aff_sub4,
            'adv_pub1': self.adv_pub1,
            'adv_pub2': self.adv_pub2,
            'adv_pub3': self.adv_pub3,
            'adv_pub4': self.adv_pub4,
            'adv_pub5': self.adv_pub5,
            'status': self.status,
            'received_at': self.received_at.isoformat() if self.received_at else None,
            'tenant_name': self.tenant_name,
            'platform_id': self.platform_id,
            'partner_id': self.partner_id,
            'source_id': self.source_id
        }

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

class PostbackDatabase:
    """PostBack数据库访问类"""
    
    def __init__(self, host: str = "34.124.206.16", port: int = 5432, 
                 database: str = "postback_db", user: str = "postback_admin",
                 password: str = "ByteC2024PostBack_CloudSQL"):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.connection_string = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        self.pool = None
        
        # 初始化映射管理器
        self.mapping_manager = MappingManager({
            'host': host,
            'port': port,
            'database': database,
            'user': user,
            'password': password
        })
        
    async def init_pool(self):
        """初始化数据库连接池"""
        try:
            self.pool = await asyncpg.create_pool(
                self.connection_string,
                min_size=2,
                max_size=10,
                command_timeout=30
            )
            
            # 初始化映射系統
            await self.mapping_manager.initialize_all_mappings()
            
            logger.info("✅ 数据库连接池初始化成功")
        except Exception as e:
            logger.error(f"❌ 数据库连接池初始化失败: {e}")
            raise
    
    async def close_pool(self):
        """关闭数据库连接池"""
        if self.pool:
            await self.pool.close()
            
        # 關閉映射管理器
        if self.mapping_manager:
            await self.mapping_manager.close_pool()
            
        logger.info("✅ 数据库连接池已关闭")
    
    async def get_available_partners(self) -> List[str]:
        """获取可用的Partner列表 - 直接從 conversions 表查詢"""
        if not self.pool:
            await self.init_pool()
        
        try:
            async with self.pool.acquire() as conn:
                # 直接從 conversions 表獲取可用的Partner列表
                query = """
                SELECT DISTINCT c.partner
                FROM conversions c
                WHERE c.partner IS NOT NULL
                ORDER BY c.partner
                """
                rows = await conn.fetch(query)
                partners = [row['partner'] for row in rows]
                
                # 如果有數據，默認添加 "ALL" 選項
                if partners:
                    partners.insert(0, "ALL")
                
                logger.info(f"✅ 獲取可用Partner列表: {partners}")
                return partners
        except Exception as e:
            logger.error(f"❌ 获取Partner列表失败: {e}")
            import traceback
            logger.error(f"詳細錯誤: {traceback.format_exc()}")
            raise
    
    async def get_conversions_by_partner(self, partner_name: str = None, 
                                       start_date: datetime = None,
                                       end_date: datetime = None,
                                       limit: Optional[int] = None) -> List[ConversionRecord]:
        """
        根据Partner获取转化记录 - 使用分批查詢優化大數據量處理
        
        Args:
            partner_name: Partner名称，None表示获取所有
            start_date: 开始日期
            end_date: 结束日期
            limit: 限制返回的记录数量
            
        Returns:
            List[ConversionRecord]: 转化记录列表
        """
        if not self.pool:
            await self.init_pool()
        
        # 分批處理配置
        BATCH_SIZE = 5000
        MAX_RETRIES = 3
        BATCH_TIMEOUT = 30
        
        try:
            async with self.pool.acquire() as conn:
                # 首先獲取總記錄數用於進度顯示
                count_query = """
                SELECT COUNT(*) as total_count
                FROM conversions c
                WHERE 1=1
                """
                
                count_params = []
                count_param_count = 0
                
                # 添加Partner過濾
                if partner_name and partner_name.upper() != 'ALL':
                    count_param_count += 1
                    count_query += f" AND c.partner = ${count_param_count}"
                    count_params.append(partner_name)
                
                # 添加時間範圍過濾
                if start_date:
                    count_param_count += 1
                    count_query += f" AND DATE(c.datetime_conversion) >= ${count_param_count}::date"
                    if hasattr(start_date, 'replace'):
                        start_date = start_date.replace(microsecond=0, tzinfo=None)
                    count_params.append(start_date)
                
                if end_date:
                    count_param_count += 1
                    count_query += f" AND DATE(c.datetime_conversion) <= ${count_param_count}::date"
                    if hasattr(end_date, 'replace'):
                        end_date = end_date.replace(microsecond=0, tzinfo=None)
                    count_params.append(end_date)
                
                # 獲取總記錄數
                total_count_row = await conn.fetchrow(count_query, *count_params)
                total_count = total_count_row['total_count'] if total_count_row else 0
                
                # 如果有limit限制，調整總數
                if limit and limit < total_count:
                    total_count = limit
                
                logger.info(f"🔍 執行查詢: Partner={partner_name}, 日期={start_date} 至 {end_date}, 總記錄數={total_count:,}")
                
                # 如果記錄數較少，使用原有邏輯
                if total_count <= BATCH_SIZE:
                    return await self._fetch_single_batch(conn, partner_name, start_date, end_date, limit)
                
                # 大數據量使用分批處理
                logger.info(f"📊 數據量較大 ({total_count:,} 條)，啟用分批處理 (每批 {BATCH_SIZE:,} 條)")
                
                # 構建基礎查詢
                base_query = """
                SELECT 
                    c.id,
                    COALESCE(c.tenant_id, 1) as tenant_id,
                    COALESCE(c.conversion_id::text, c.id::text) as conversion_id,
                    c.offer_id,
                    c.offer_name,
                    c.datetime_conversion,
                    COALESCE(c.order_id, c.conversion_id::text) as order_id,
                    COALESCE(c.sale_amount, c.usd_sale_amount, 0) as usd_sale_amount,
                    COALESCE(c.payout, c.usd_payout, 0) as usd_payout,
                    c.aff_sub,
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
                    c.platform_id,
                    c.partner_id
                FROM conversions c
                WHERE 1=1
                """
                
                params = []
                param_count = 0
                
                # 添加Partner過濾
                if partner_name and partner_name.upper() != 'ALL':
                    param_count += 1
                    base_query += f" AND c.partner = ${param_count}"
                    params.append(partner_name)
                
                # 添加時間範圍過濾
                if start_date:
                    param_count += 1
                    base_query += f" AND DATE(c.datetime_conversion) >= ${param_count}::date"
                    params.append(start_date)
                
                if end_date:
                    param_count += 1
                    base_query += f" AND DATE(c.datetime_conversion) <= ${param_count}::date"
                    params.append(end_date)
                
                # 添加排序
                base_query += " ORDER BY c.datetime_conversion DESC"
                
                # 分批處理
                all_conversions = []
                offset = 0
                total_processed = 0
                batch_number = 1
                
                while total_processed < total_count:
                    # 計算當前批次大小
                    current_batch_size = min(BATCH_SIZE, total_count - total_processed)
                    if limit and total_processed + current_batch_size > limit:
                        current_batch_size = limit - total_processed
                    
                    # 構建批次查詢
                    batch_query = base_query + f" LIMIT {current_batch_size} OFFSET {offset}"
                    
                    # 執行批次查詢（帶重試機制）
                    batch_rows = await self._fetch_batch_with_retry(
                        conn, batch_query, params, batch_number, 
                        MAX_RETRIES, BATCH_TIMEOUT, partner_name
                    )
                    
                    if not batch_rows:
                        logger.warning(f"⚠️ 批次 {batch_number} 返回空結果，停止處理")
                        break
                    
                    # 處理當前批次
                    batch_conversions = []
                    for row in batch_rows:
                        # 獲取 partner_id 和 source_id
                        partner_id = row.get('partner_id')
                        if not partner_id and row.get('partner_name'):
                            partner_id = await self.mapping_manager.get_partner_id(row['partner_name'])
                        
                        source_id = None
                        if row.get('aff_sub'):
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
                            platform_id=row['platform_id'],
                            partner_id=partner_id,
                            source_id=source_id
                        ))
                    
                    all_conversions.extend(batch_conversions)
                    total_processed += len(batch_rows)
                    
                    # 顯示進度
                    percentage = (total_processed / total_count) * 100
                    logger.info(f"📈 批次 {batch_number} 完成: {total_processed:,}/{total_count:,} ({percentage:.1f}%)")
                    
                    offset += current_batch_size
                    batch_number += 1
                    
                    # 如果批次小於預期大小或達到limit，說明已經完成
                    if len(batch_rows) < current_batch_size or (limit and total_processed >= limit):
                        break
                
                logger.info(f"✅ 分批查詢完成: 總共處理 {total_processed:,} 條記錄，{batch_number-1} 個批次")
                return all_conversions
                
        except Exception as e:
            logger.error(f"❌ 获取转化记录失败: {e}")
            import traceback
            logger.error(f"詳細錯誤: {traceback.format_exc()}")
            raise

    async def _fetch_single_batch(self, conn, partner_name: str = None, 
                                start_date: datetime = None,
                                end_date: datetime = None,
                                limit: Optional[int] = None) -> List[ConversionRecord]:
        """處理小數據量的單批次查詢"""
        base_query = """
        SELECT 
            c.id,
            COALESCE(c.tenant_id, 1) as tenant_id,
            COALESCE(c.conversion_id::text, c.id::text) as conversion_id,
            c.offer_id,
            c.offer_name,
            c.datetime_conversion,
            COALESCE(c.order_id, c.conversion_id::text) as order_id,
            COALESCE(c.sale_amount, c.usd_sale_amount, 0) as usd_sale_amount,
            COALESCE(c.payout, c.usd_payout, 0) as usd_payout,
            c.aff_sub,
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
            c.platform_id,
            c.partner_id
        FROM conversions c
        WHERE 1=1
        """
        
        params = []
        param_count = 0
        
        # 添加Partner過濾
        if partner_name and partner_name.upper() != 'ALL':
            param_count += 1
            base_query += f" AND c.partner = ${param_count}"
            params.append(partner_name)
        
        # 添加時間範圍過濾
        if start_date:
            param_count += 1
            base_query += f" AND DATE(c.datetime_conversion) >= ${param_count}::date"
            params.append(start_date)
        
        if end_date:
            param_count += 1
            base_query += f" AND DATE(c.datetime_conversion) <= ${param_count}::date"
            params.append(end_date)
        
        # 添加排序
        base_query += " ORDER BY c.datetime_conversion DESC"
        
        # 添加limit限制
        if limit:
            param_count += 1
            base_query += f" LIMIT ${param_count}"
            params.append(limit)
        
        rows = await conn.fetch(base_query, *params)
        
        conversions = []
        for row in rows:
            # 獲取 partner_id 和 source_id
            partner_id = row.get('partner_id')
            if not partner_id and row.get('partner_name'):
                partner_id = await self.mapping_manager.get_partner_id(row['partner_name'])
            
            source_id = None
            if row.get('aff_sub'):
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
                platform_id=row['platform_id'],
                partner_id=partner_id,
                source_id=source_id
            ))
        
        return conversions

    async def _fetch_batch_with_retry(self, conn, query: str, params: list, 
                                    batch_number: int, max_retries: int, 
                                    timeout: int, partner_name: str):
        """帶重試機制的批次查詢"""
        import asyncio
        
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"🔄 執行批次 {batch_number} (第 {attempt} 次嘗試)")
                
                # 帶超時的查詢
                rows = await asyncio.wait_for(
                    conn.fetch(query, *params),
                    timeout=timeout
                )
                
                logger.info(f"✅ 批次 {batch_number} 查詢成功: {len(rows)} 條記錄")
                return rows
                
            except asyncio.TimeoutError:
                logger.warning(f"⚠️ 批次 {batch_number} 查詢超時 ({timeout}秒) - 第 {attempt} 次嘗試")
                if attempt == max_retries:
                    logger.error(f"❌ 批次 {batch_number} 在 {max_retries} 次重試後仍然超時，跳過此批次")
                    return []
                else:
                    logger.info(f"🔄 將在 2 秒後重試批次 {batch_number}")
                    await asyncio.sleep(2)
                    
            except Exception as e:
                logger.error(f"❌ 批次 {batch_number} 查詢失败 (第 {attempt} 次嘗試): {e}")
                if attempt == max_retries:
                    logger.error(f"❌ 批次 {batch_number} 在 {max_retries} 次重試後仍然失敗，跳過此批次")
                    return []
                else:
                    logger.info(f"🔄 將在 2 秒後重試批次 {batch_number}")
                    await asyncio.sleep(2)
        
        return []
    
    async def get_partner_summary(self, partner_name: str = None,
                                start_date: datetime = None,
                                end_date: datetime = None,
                                limit: Optional[int] = None) -> List[PartnerSummary]:
        """
        获取Partner汇总数据 - 使用簡化的直接欄位查詢
        
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
            async with self.pool.acquire() as conn:
                # 使用簡化的直接欄位查詢
                base_query = """
                SELECT 
                    c.partner,
                    COUNT(*) as total_records,
                    SUM(COALESCE(c.sale_amount, c.usd_sale_amount, 0)) as total_amount,
                    array_agg(DISTINCT c.aff_sub) FILTER (WHERE c.aff_sub IS NOT NULL) as sources
                FROM conversions c
                WHERE 1=1
                """
                
                params = []
                param_count = 0
                
                # 添加Partner過濾
                if partner_name and partner_name.upper() != 'ALL':
                    param_count += 1
                    base_query += f" AND c.partner = ${param_count}"
                    params.append(partner_name)
                
                # 添加時間範圍過濾
                if start_date:
                    param_count += 1
                    base_query += f" AND DATE(c.datetime_conversion) >= ${param_count}::date"
                    if hasattr(start_date, 'replace'):
                        start_date = start_date.replace(microsecond=0, tzinfo=None)
                    params.append(start_date)
                
                if end_date:
                    param_count += 1
                    base_query += f" AND DATE(c.datetime_conversion) <= ${param_count}::date"
                    if hasattr(end_date, 'replace'):
                        end_date = end_date.replace(microsecond=0, tzinfo=None)
                    params.append(end_date)
                
                # 添加分組和排序
                base_query += " GROUP BY c.partner ORDER BY total_records DESC"
                
                # 添加limit限制
                if limit:
                    param_count += 1
                    base_query += f" LIMIT ${param_count}"
                    params.append(limit)
                
                logger.info(f"🔍 執行Partner汇总查詢: Partner={partner_name}, 日期={start_date} 至 {end_date}")
                
                rows = await conn.fetch(base_query, *params)
                
                summaries = []
                for row in rows:
                    partner_name_db = row['partner'] or 'Unknown'
                    total_records = row['total_records']
                    total_amount = Decimal(str(row['total_amount'])) if row['total_amount'] else Decimal('0')
                    sources = row['sources'] or []
                    
                    # 獲取 partner_id
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
                
                logger.info(f"✅ 获取Partner汇总成功: {len(summaries)} 个Partner")
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
        """
        获取转化数据的DataFrame格式（增強版帶映射）
        
        Args:
            partner_name: Partner名称
            start_date: 开始日期
            end_date: 结束日期
            limit: 限制返回的记录数量
            
        Returns:
            pd.DataFrame: 转化数据框
        """
        try:
            conversions = await self.get_conversions_by_partner(
                partner_name=partner_name,
                start_date=start_date,
                end_date=end_date,
                limit=limit
            )
            
            if not conversions:
                logger.warning(f"⚠️ 没有找到转化数据: Partner={partner_name}")
                return pd.DataFrame()
            
            # 转换为DataFrame
            data = []
            for conv in conversions:
                # 確定Partner名稱
                partner_display = conv.partner_name if hasattr(conv, 'partner_name') and conv.partner_name else 'Unknown'
                if not partner_display or partner_display == 'Unknown':
                    # 嘗試通過Source推斷Partner
                    if conv.aff_sub:
                        from config import match_source_to_partner
                        partner_display = match_source_to_partner(conv.aff_sub)
                
                # 移除時區信息以支持Excel輸出
                conversion_date = conv.datetime_conversion
                if conversion_date and hasattr(conversion_date, 'replace') and conversion_date.tzinfo:
                    conversion_date = conversion_date.replace(tzinfo=None)
                
                received_at = conv.received_at
                if received_at and hasattr(received_at, 'replace') and received_at.tzinfo:
                    received_at = received_at.replace(tzinfo=None)
                
                # 处理Sale Amount - 根据config.py中的设置
                original_sale_amount = float(conv.usd_sale_amount) if conv.usd_sale_amount else 0.0
                
                # 检查是否为ByteC partner
                import sys
                import os
                config_path = os.path.join(os.path.dirname(__file__), '../../../../')
                if config_path not in sys.path:
                    sys.path.append(config_path)
                
                import config
                is_bytec_partner = (
                    partner_display.upper() == 'BYTEC' or
                    partner_display.upper() == 'BYTEC-NETWORK' or
                    'BYTEC' in partner_display.upper()
                )
                
                # 应用mockup调整（根据config.py设置）
                if is_bytec_partner:
                    processed_sale_amount = original_sale_amount * config.BYTEC_MOCKUP_MULTIPLIER  # ByteC使用BYTEC_MOCKUP_MULTIPLIER
                else:
                    processed_sale_amount = original_sale_amount * config.MOCKUP_MULTIPLIER  # 其他partner使用MOCKUP_MULTIPLIER
                
                # 包含所有數據庫欄位，按照數據庫格式輸出，隱藏指定欄位（ID, Tenant ID, Tenant, Received At, Status, Payout (USD), Platform ID）
                data.append({
                    'Conversion ID': conv.conversion_id,
                    'Offer ID': conv.offer_id,
                    'Offer Name': conv.offer_name,
                    'Datetime Conversion': conversion_date,
                    'Order ID': conv.order_id,
                    'USD Sale Amount': processed_sale_amount,  # 使用處理後的金額
                    'Aff Sub': conv.aff_sub,
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
                    'Source': conv.aff_sub if conv.aff_sub else 'Unknown',
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
            
            logger.info(f"✅ 获取转化数据成功: {len(df)} 条记录")
            return df
            
        except Exception as e:
            logger.error(f"❌ 获取转化数据DataFrame失败: {e}")
            raise
    
    async def insert_conversion_with_mapping(self, conversion_data: Dict[str, Any]) -> Optional[int]:
        """
        插入轉化數據並使用映射系統
        
        Args:
            conversion_data: 轉化數據字典
            
        Returns:
            Optional[int]: 插入的記錄ID，失敗時返回None
        """
        if not self.pool:
            await self.init_pool()
        
        try:
            # 提取映射信息
            api_secret = conversion_data.get('api_secret')
            aff_sub = conversion_data.get('aff_sub')
            
            # 獲取映射ID
            platform_id = None
            if api_secret:
                platform_id = await self.mapping_manager.get_platform_by_api_secret(api_secret)
            
            source_id = None
            partner_id = None
            if aff_sub:
                source_id = await self.mapping_manager.get_or_create_source_id(aff_sub)
                if source_id:
                    # 通過source_id獲取partner_id
                    async with self.pool.acquire() as conn:
                        partner_id = await conn.fetchval("""
                        SELECT partner_id FROM sources WHERE id = $1
                        """, source_id)
            
            async with self.pool.acquire() as conn:
                # 準備raw_data JSON
                raw_data = {
                    'offer_id': conversion_data.get('offer_id'),
                    'order_id': conversion_data.get('order_id'),
                    'aff_sub2': conversion_data.get('aff_sub2', ''),
                    'aff_sub3': conversion_data.get('aff_sub3', ''),
                    'aff_sub4': conversion_data.get('aff_sub4', ''),
                    'status': conversion_data.get('status', 'approved'),
                    'api_secret': api_secret,
                    'platform_id': platform_id,
                    'source_id': source_id,
                    'datetime_conversion': conversion_data.get('datetime_conversion'),
                    'original_data': conversion_data
                }
                
                # 插入到conversions表（僅使用實際存在的欄位）
                conversion_id = await conn.fetchval("""
                INSERT INTO conversions (
                    tenant_id, conversion_id, offer_name,
                    usd_sale_amount, usd_payout, aff_sub,
                    event_time, raw_data, partner_id, created_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10
                )
                RETURNING id
                """,
                conversion_data.get('tenant_id', 1),
                conversion_data.get('conversion_id'),
                conversion_data.get('offer_name'),
                conversion_data.get('usd_sale_amount'),
                conversion_data.get('usd_payout'),
                conversion_data.get('aff_sub'),
                conversion_data.get('datetime_conversion'),
                json.dumps(raw_data),
                partner_id,
                conversion_data.get('created_at', datetime.now())
                )
                
                logger.info(f"✅ 插入轉化數據成功: ID={conversion_id}, Platform={platform_id}, Partner={partner_id}, Source={source_id}")
                return conversion_id
                
        except Exception as e:
            logger.error(f"❌ 插入轉化數據失敗: {e}")
            return None
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查 - 簡化版本，只檢查實際存在的表"""
        try:
            if not self.pool:
                await self.init_pool()
            
            async with self.pool.acquire() as conn:
                # 检查数据库连接
                version = await conn.fetchval("SELECT version()")
                
                # 检查主要数据表
                conversions_count = await conn.fetchval("SELECT COUNT(*) FROM conversions")
                
                # 檢查可選表（如果不存在則跳過）
                partners_count = 0
                platforms_count = 0
                sources_count = 0
                
                try:
                    partners_count = await conn.fetchval("SELECT COUNT(*) FROM business_partners")
                except:
                    logger.warning("business_partners 表不存在，跳過檢查")
                
                try:
                    platforms_count = await conn.fetchval("SELECT COUNT(*) FROM platforms")
                except:
                    logger.warning("platforms 表不存在，跳過檢查")
                
                try:
                    sources_count = await conn.fetchval("SELECT COUNT(*) FROM sources")
                except:
                    logger.warning("sources 表不存在，跳過檢查")
                
                # 檢查映射系統（如果存在）
                mapping_summary = {}
                try:
                    mapping_summary = await self.mapping_manager.get_mapping_summary()
                except:
                    logger.warning("映射系統不可用，跳過檢查")
                
                # 檢查可用的partners
                available_partners = []
                try:
                    available_partners = await self.get_available_partners()
                except:
                    logger.warning("無法獲取可用partners列表")
                
                return {
                    'status': 'healthy',
                    'database_version': version,
                    'conversions_count': conversions_count,
                    'partners_count': partners_count,
                    'platforms_count': platforms_count,
                    'sources_count': sources_count,
                    'available_partners': available_partners,
                    'mapping_system': mapping_summary,
                    'connection_pool_size': self.pool.get_size() if self.pool else 0,
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"❌ 健康检查失败: {e}")
            import traceback
            logger.error(f"詳細錯誤: {traceback.format_exc()}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            } 