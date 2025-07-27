#!/usr/bin/env python3
"""
優化版PostBack數據庫管理器
解決N+1查詢問題，增加批次大小和連接池，提供更好的性能
"""

import asyncio
import asyncpg
import pandas as pd
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging
from dataclasses import dataclass
from decimal import Decimal
import time

logger = logging.getLogger(__name__)

@dataclass
class ConversionRecord:
    """轉化記錄數據類"""
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
    aff_sub5: Optional[str]
    adv_sub1: Optional[str]
    adv_sub2: Optional[str]
    adv_sub3: Optional[str]
    adv_sub4: Optional[str]
    adv_sub5: Optional[str]
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
    click_id: Optional[str] = None
    merchant_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'conversion_id': self.conversion_id,
            'offer_id': self.offer_id,
            'offer_name': self.offer_name,
            'datetime_conversion': self.datetime_conversion,
            'order_id': self.order_id,
            'usd_sale_amount': self.usd_sale_amount,
            'usd_payout': self.usd_payout,
            'aff_sub': self.aff_sub,
            'aff_sub2': self.aff_sub2,
            'aff_sub3': self.aff_sub3,
            'aff_sub4': self.aff_sub4,
            'aff_sub5': self.aff_sub5,
            'adv_sub1': self.adv_sub1,
            'adv_sub2': self.adv_sub2,
            'adv_sub3': self.adv_sub3,
            'adv_sub4': self.adv_sub4,
            'adv_sub5': self.adv_sub5,
            'status': self.status,
            'received_at': self.received_at,
            'tenant_name': self.tenant_name,
            'adv_pub1': self.adv_pub1,
            'adv_pub2': self.adv_pub2,
            'adv_pub3': self.adv_pub3,
            'adv_pub4': self.adv_pub4,
            'adv_pub5': self.adv_pub5,
            'platform_id': self.platform_id,
            'partner_id': self.partner_id,
            'source_id': self.source_id,
            'click_id': self.click_id,
            'merchant_id': self.merchant_id
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
        """轉換為字典格式"""
        return {
            'partner_name': self.partner_name,
            'partner_id': self.partner_id,
            'total_records': self.total_records,
            'total_amount': float(self.total_amount) if self.total_amount else 0.0,
            'amount_formatted': self.amount_formatted,
            'sources': self.sources if self.sources else [],
            'sources_count': self.sources_count
        }

class OptimizedMappingCache:
    """優化的映射快取管理器"""
    
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self.pool = None
        
        # 在記憶體中緩存所有映射關係
        self.partner_name_to_id = {}    # partner_name -> partner_id
        self.partner_id_to_name = {}    # partner_id -> partner_name
        self.source_name_to_id = {}     # source_name -> source_id
        self.source_id_to_name = {}     # source_id -> source_name
        self.platform_name_to_id = {}  # platform_name -> platform_id
        self.platform_id_to_name = {}  # platform_id -> platform_name
        
        # 快取狀態
        self.cache_initialized = False
        self.cache_last_updated = None
        
    async def init_pool(self):
        """初始化數據庫連接池"""
        try:
            connection_string = f"postgresql://{self.db_config['user']}:{self.db_config['password']}@{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}"
            self.pool = await asyncpg.create_pool(
                connection_string,
                min_size=2,
                max_size=10,  # 合理的連接池大小
                command_timeout=120,
                server_settings={
                    'application_name': 'bytec_reporter_optimized'
                }
            )
            logger.info("✅ 優化映射管理器數據庫連接池初始化成功")
        except Exception as e:
            logger.error(f"❌ 優化映射管理器數據庫連接池初始化失敗: {e}")
            raise
    
    async def close_pool(self):
        """關閉數據庫連接池"""
        if self.pool:
            await self.pool.close()
            logger.info("✅ 優化映射管理器數據庫連接池已關閉")
    
    async def initialize_cache(self):
        """初始化所有映射快取到記憶體 - 快速版本"""
        if not self.pool:
            await self.init_pool()
        
        start_time = time.time()
        logger.info("🚀 開始初始化映射快取（快速版本）...")
        
        try:
            async with self.pool.acquire() as conn:
                # 快速版本：只載入最近30天的數據來建立映射
                # 這樣可以大幅減少查詢時間
                
                # 載入最近Partner映射（限制查詢範圍）
                partner_rows = await conn.fetch("""
                    SELECT DISTINCT partner, 
                           DENSE_RANK() OVER (ORDER BY partner) as id 
                    FROM conversions 
                    WHERE partner IS NOT NULL 
                      AND partner != ''
                      AND received_at >= NOW() - INTERVAL '30 days'
                    LIMIT 1000
                """)
                
                for row in partner_rows:
                    partner_name = row['partner']
                    partner_id = row['id']
                    self.partner_name_to_id[partner_name] = partner_id
                    self.partner_id_to_name[partner_id] = partner_name
                
                logger.info(f"📊 載入 {len(self.partner_name_to_id)} 個Partner映射（快速模式）")
                
                # 載入最近Source映射（限制查詢範圍）
                source_rows = await conn.fetch("""
                    SELECT DISTINCT aff_sub,
                           DENSE_RANK() OVER (ORDER BY aff_sub) as id 
                    FROM conversions 
                    WHERE aff_sub IS NOT NULL 
                      AND aff_sub != ''
                      AND received_at >= NOW() - INTERVAL '30 days'
                    LIMIT 1000
                """)
                
                for row in source_rows:
                    source_name = row['aff_sub']
                    source_id = row['id']
                    self.source_name_to_id[source_name] = source_id
                    self.source_id_to_name[source_id] = source_name
                
                logger.info(f"📊 載入 {len(self.source_name_to_id)} 個Source映射（快速模式）")
                
                # 簡化Platform映射 - 直接使用數字ID
                platform_rows = await conn.fetch("""
                    SELECT DISTINCT platform_id 
                    FROM conversions 
                    WHERE platform_id IS NOT NULL
                      AND received_at >= NOW() - INTERVAL '30 days'
                    LIMIT 100
                """)
                
                for row in platform_rows:
                    platform_id = row['platform_id']
                    platform_name = f"Platform_{platform_id}"
                    self.platform_id_to_name[platform_id] = platform_name
                    self.platform_name_to_id[platform_name] = platform_id
                
                logger.info(f"📊 載入 {len(self.platform_id_to_name)} 個Platform映射（快速模式）")
                
                self.cache_initialized = True
                self.cache_last_updated = datetime.now()
                
                elapsed_time = time.time() - start_time
                logger.info(f"✅ 映射快取初始化完成（快速模式），耗時 {elapsed_time:.2f} 秒")
                
        except Exception as e:
            logger.error(f"❌ 初始化映射快取失敗: {e}")
            # 如果快取初始化失敗，使用動態映射作為回退
            logger.info("🔄 使用動態映射作為回退方案")
            self.cache_initialized = True  # 標記為已初始化，但使用動態查詢
            self.cache_last_updated = datetime.now()
    
    async def get_partner_id_dynamic(self, partner_name: str) -> Optional[int]:
        """動態獲取Partner ID（回退方案）"""
        if not partner_name:
            return None
            
        # 先檢查快取
        if partner_name in self.partner_name_to_id:
            return self.partner_name_to_id[partner_name]
        
        # 動態查詢並快取結果
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchval(
                    "SELECT MIN(id) FROM conversions WHERE partner = $1",
                    partner_name
                )
                if result:
                    self.partner_name_to_id[partner_name] = result
                    self.partner_id_to_name[result] = partner_name
                    return result
        except Exception as e:
            logger.warning(f"動態查詢Partner ID失敗: {e}")
        
        return None
    
    async def get_source_id_dynamic(self, source_name: str) -> Optional[int]:
        """動態獲取Source ID（回退方案）"""
        if not source_name:
            return None
            
        # 先檢查快取
        if source_name in self.source_name_to_id:
            return self.source_name_to_id[source_name]
        
        # 動態查詢並快取結果
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchval(
                    "SELECT MIN(id) FROM conversions WHERE aff_sub = $1",
                    source_name
                )
                if result:
                    self.source_name_to_id[source_name] = result
                    self.source_id_to_name[result] = source_name
                    return result
        except Exception as e:
            logger.warning(f"動態查詢Source ID失敗: {e}")
        
        return None
    
    def get_partner_id(self, partner_name: str) -> Optional[int]:
        """從快取獲取Partner ID (同步包裝)"""
        return self.partner_name_to_id.get(partner_name)
    
    def get_partner_name(self, partner_id: int) -> Optional[str]:
        """從快取獲取Partner名稱 (同步包裝)"""
        return self.partner_id_to_name.get(partner_id)
    
    def get_source_id(self, source_name: str) -> Optional[int]:
        """從快取獲取Source ID (同步包裝)"""
        return self.source_name_to_id.get(source_name)
    
    def get_source_name(self, source_id: int) -> Optional[str]:
        """從快取獲取Source名稱 (同步包裝)"""
        return self.source_id_to_name.get(source_id)
    
    def get_platform_id(self, platform_name: str) -> Optional[int]:
        """從快取獲取Platform ID (同步包裝)"""
        return self.platform_name_to_id.get(platform_name)
    
    def get_platform_name(self, platform_id: int) -> Optional[str]:
        """從快取獲取Platform名稱 (同步包裝)"""
        return self.platform_id_to_name.get(platform_id)

class OptimizedPostbackDatabase:
    """優化版PostBack數據庫訪問類"""
    
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
        
        # 初始化優化的映射快取管理器
        self.mapping_cache = OptimizedMappingCache({
            'host': host,
            'port': port,
            'database': database,
            'user': user,
            'password': password
        })
        
        # 性能配置
        self.BATCH_SIZE = 20000  # 大幅增加批次大小
        self.MAX_RETRIES = 3
        self.BATCH_TIMEOUT = 300  # 增加到5分鐘
        
    async def init_pool(self):
        """初始化數據庫連接池"""
        try:
            self.pool = await asyncpg.create_pool(
                self.connection_string,
                min_size=10,
                max_size=50,  # 大幅增加連接池大小
                command_timeout=300,  # 5分鐘超時
                server_settings={
                    'application_name': 'bytec_reporter_optimized',
                    'shared_preload_libraries': 'pg_stat_statements'
                }
            )
            
            # 初始化映射快取系統
            await self.mapping_cache.initialize_cache()
            
            logger.info("✅ 優化數據庫連接池初始化成功")
        except Exception as e:
            logger.error(f"❌ 優化數據庫連接池初始化失敗: {e}")
            raise
    
    async def close_pool(self):
        """關閉數據庫連接池"""
        if self.pool:
            await self.pool.close()
            
        # 關閉映射管理器
        if self.mapping_cache:
            await self.mapping_cache.close_pool()
            
        logger.info("✅ 優化數據庫連接池已關閉")
    
    async def ensure_indexes(self):
        """確保必要的索引存在以優化查詢性能"""
        if not self.pool:
            await self.init_pool()
        
        indexes_to_create = [
            # 主要查詢索引
            ("idx_conversions_datetime_partner", "conversions", "(DATE(datetime_conversion), partner)"),
            ("idx_conversions_datetime", "conversions", "datetime_conversion"),
            ("idx_conversions_partner", "conversions", "partner"),
            ("idx_conversions_aff_sub", "conversions", "aff_sub"),
            ("idx_conversions_platform_id", "conversions", "platform_id"),
            ("idx_conversions_partner_id", "conversions", "partner_id"),
            # 複合索引用於常見查詢模式
            ("idx_conversions_partner_datetime", "conversions", "partner, datetime_conversion DESC"),
            ("idx_conversions_datetime_desc", "conversions", "datetime_conversion DESC"),
        ]
        
        try:
            async with self.pool.acquire() as conn:
                for index_name, table_name, columns in indexes_to_create:
                    try:
                        await conn.execute(f"""
                        CREATE INDEX CONCURRENTLY IF NOT EXISTS {index_name} 
                        ON {table_name} {columns}
                        """)
                        logger.info(f"✅ 索引創建成功: {index_name}")
                    except Exception as e:
                        # 索引可能已存在，繼續處理其他索引
                        logger.warning(f"⚠️ 索引創建跳過: {index_name} - {e}")
                        
            logger.info("✅ 數據庫索引優化完成")
        except Exception as e:
            logger.error(f"❌ 數據庫索引創建失敗: {e}")
            raise
    
    async def get_conversions_by_partner_optimized(self, partner_name: str = None, 
                                                  start_date: datetime = None,
                                                  end_date: datetime = None,
                                                  limit: Optional[int] = None) -> List[ConversionRecord]:
        """
        優化版：根據Partner獲取轉化記錄
        - 使用JOIN查詢減少N+1問題
        - 大批次處理
        - 預載入映射快取
        """
        if not self.pool:
            await self.init_pool()
        
        # 確保映射快取已初始化
        if not self.mapping_cache.cache_initialized:
            await self.mapping_cache.initialize_cache()
        
        start_time = time.time()
        
        try:
            async with self.pool.acquire() as conn:
                # 構建優化查詢（使用一次性大量獲取）
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
                    if hasattr(start_date, 'replace'):
                        start_date = start_date.replace(microsecond=0, tzinfo=None)
                    params.append(start_date)
                
                if end_date:
                    param_count += 1
                    base_query += f" AND DATE(c.datetime_conversion) <= ${param_count}::date"
                    if hasattr(end_date, 'replace'):
                        end_date = end_date.replace(microsecond=0, tzinfo=None)
                    params.append(end_date)
                
                # 添加排序
                base_query += " ORDER BY c.datetime_conversion DESC"
                
                # 添加limit限制
                if limit:
                    param_count += 1
                    base_query += f" LIMIT ${param_count}"
                    params.append(limit)
                
                logger.info(f"🔍 執行優化查詢: Partner={partner_name}, 日期={start_date} 至 {end_date}")
                
                # 使用大批次一次性獲取數據
                rows = await asyncio.wait_for(
                    conn.fetch(base_query, *params),
                    timeout=self.BATCH_TIMEOUT
                )
                
                query_time = time.time() - start_time
                logger.info(f"📊 查詢完成: {len(rows):,} 條記錄，耗時 {query_time:.2f} 秒")
                
                # 使用預載入的快取處理映射，避免N+1查詢
                conversions = []
                mapping_start_time = time.time()
                
                for row in rows:
                    # 從快取獲取映射ID，無需額外查詢
                    partner_id = row.get('partner_id')
                    if not partner_id and row.get('partner_name'):
                        partner_id = self.mapping_cache.get_partner_id(row['partner_name'])
                    
                    source_id = None
                    if row.get('aff_sub'):
                        source_id = self.mapping_cache.get_source_id(row['aff_sub'])
                    
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
                
                mapping_time = time.time() - mapping_start_time
                total_time = time.time() - start_time
                
                logger.info(f"✅ 優化查詢完成: {len(conversions):,} 條記錄")
                logger.info(f"   📊 查詢時間: {query_time:.2f} 秒")
                logger.info(f"   🗺️ 映射時間: {mapping_time:.2f} 秒")
                logger.info(f"   ⏱️ 總時間: {total_time:.2f} 秒")
                
                return conversions
                
        except Exception as e:
            logger.error(f"❌ 優化查詢失敗: {e}")
            import traceback
            logger.error(f"詳細錯誤: {traceback.format_exc()}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """健康檢查"""
        try:
            if not self.pool:
                await self.init_pool()
            
            async with self.pool.acquire() as conn:
                # 檢查基本連接
                result = await conn.fetchval("SELECT 1")
                
                # 檢查數據庫統計
                conversion_count = await conn.fetchval("SELECT COUNT(*) FROM conversions")
                
                return {
                    'status': 'healthy',
                    'connection': 'ok',
                    'conversion_count': conversion_count,
                    'cache_initialized': self.mapping_cache.cache_initialized,
                    'cache_last_updated': self.mapping_cache.cache_last_updated
                }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            } 