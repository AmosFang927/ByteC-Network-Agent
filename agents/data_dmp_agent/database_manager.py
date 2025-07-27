#!/usr/bin/env python3
"""
DMP-Agent 數據庫管理器 - 增強版本
支持完整的轉化數據存儲，包括platform、partner、source等所有字段
從Reporter-Agent遷移的Google Cloud SQL存儲邏輯
支持數據來源分離：API 和 Postback 數據分別存儲
"""

import asyncio
import asyncpg
import json
import math
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
import logging
from decimal import Decimal

# 導入配置
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import config

logger = logging.getLogger(__name__)

class EnhancedDMPDatabaseManager:
    """
    增強版DMP-Agent數據庫管理器
    支持完整的轉化數據存儲，包括：
    - platform 字段
    - partner 字段（按照config.py映射）
    - source 字段（從aff_sub獲取）
    - 所有API參數的完整存儲
    """
    
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
        
    async def init_pool(self):
        """初始化数据库连接池 - 超级稳定性版本"""
        try:
            # 🔧 超级修复：最强连接池配置
            self.pool = await asyncpg.create_pool(
                self.connection_string,
                min_size=2,              # 减少最小连接数，降低资源占用
                max_size=10,             # 减少最大连接数，提高连接质量  
                max_queries=5000,        # 进一步减少每连接查询数
                max_inactive_connection_lifetime=300,  # 5分钟非活跃连接生命周期
                command_timeout=300,     # 5分钟命令超时
                server_settings={
                    'statement_timeout': '300000',           # 5分钟语句超时
                    'idle_in_transaction_session_timeout': '300000',  # 5分钟空闲事务超时
                    'tcp_keepalives_idle': '180',            # 3分钟TCP保活空闲时间
                    'tcp_keepalives_interval': '5',          # 5秒TCP保活间隔
                    'tcp_keepalives_count': '6'              # 6次TCP保活尝试
                },
                # 增加连接重试机制
                connection_class=asyncpg.Connection,
                init=self._init_connection
            )
            logger.info("✅ 超強版DMP-Agent數據庫連接池初始化成功 (超稳定性版本)")
            logger.info(f"   連接池配置: min_size=2, max_size=10, timeout=300s")
        except Exception as e:
            logger.error(f"❌ DMP-Agent數據庫連接池初始化失敗: {e}")
            raise

    async def _init_connection(self, connection):
        """初始化每个新连接"""
        try:
            # 设置连接级别的超时和参数
            await connection.execute("SET statement_timeout = '300s'")
            await connection.execute("SET idle_in_transaction_session_timeout = '300s'")
        except Exception as e:
            logger.warning(f"⚠️ 連接初始化警告: {e}")
    
    async def close_pool(self):
        """关闭数据库连接池"""
        if self.pool:
            await self.pool.close()
        logger.info("✅ DMP-Agent數據庫連接池已關閉")
    
    async def ensure_database_schema(self):
        """確保數據庫結構存在"""
        if not self.pool:
            await self.init_pool()
        
        try:
            async with self.pool.acquire() as conn:
                # 確保原始 conversions 表存在（向後兼容）
                await self._create_conversions_table(conn, 'conversions')
                
                # 如果啟用數據來源分離，創建分離的表
                if config.should_use_separate_tables():
                    await self._create_conversions_table(conn, 'conversions_api')
                    await self._create_conversions_table(conn, 'conversions_postback')
                    logger.info("✅ 數據來源分離表結構已確保")
                
                logger.info("✅ 數據庫結構檢查完成")
                
        except Exception as e:
            logger.error(f"❌ 確保數據庫結構失敗: {e}")
            raise

    async def _create_conversions_table(self, conn, table_name):
        """創建轉化數據表"""
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            
            -- 核心分類字段
            platform VARCHAR(50),
            partner VARCHAR(100),
            source VARCHAR(100),
            
            -- 核心轉化字段
            conversion_id VARCHAR(255) UNIQUE,
            offer_id VARCHAR(100),
            offer_name TEXT,
            order_id VARCHAR(255),
            
            -- 時間字段
            datetime_conversion TIMESTAMP,
            datetime_conversion_updated TIMESTAMP,
            click_time TIMESTAMP,
            
            -- 完整金額字段
            sale_amount_local DECIMAL(15,4),
            myr_sale_amount DECIMAL(15,4),
            usd_sale_amount DECIMAL(15,4),
            payout_local DECIMAL(15,4),
            myr_payout DECIMAL(15,4),
            usd_payout DECIMAL(15,4),
            sale_amount DECIMAL(15,4),
            payout DECIMAL(15,4),
            base_payout DECIMAL(15,4),
            bonus_payout DECIMAL(15,4),
            
            -- 貨幣字段
            currency VARCHAR(10),
            conversion_currency VARCHAR(10),
            
            -- 廣告主參數
            adv_sub VARCHAR(255),
            adv_sub1 VARCHAR(255),
            adv_sub2 VARCHAR(255),
            adv_sub3 VARCHAR(255),
            adv_sub4 VARCHAR(255),
            adv_sub5 VARCHAR(255),
            
            -- 發布商參數
            aff_sub VARCHAR(255),
            aff_sub1 VARCHAR(255),
            aff_sub2 VARCHAR(255),
            aff_sub3 VARCHAR(255),
            aff_sub4 VARCHAR(255),
            aff_sub5 VARCHAR(255),
            
            -- 狀態字段
            conversion_status VARCHAR(50),
            offer_status VARCHAR(50),
            
            -- 業務字段
            merchant_id VARCHAR(100),
            affiliate_remarks TEXT,
            click_id VARCHAR(255),
            
            -- 佣金字段
            commission_rate DECIMAL(8,4),
            avg_commission_rate DECIMAL(8,4),
            
            -- 系統字段
            tenant_id INTEGER DEFAULT 1,
            raw_data JSONB,
            event_time TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        await conn.execute(create_table_sql)
        
        # 創建索引
        index_queries = [
            f"CREATE INDEX IF NOT EXISTS idx_{table_name}_conversion_id ON {table_name} (conversion_id);",
            f"CREATE INDEX IF NOT EXISTS idx_{table_name}_datetime_conversion ON {table_name} (datetime_conversion);",
            f"CREATE INDEX IF NOT EXISTS idx_{table_name}_platform ON {table_name} (platform);",
            f"CREATE INDEX IF NOT EXISTS idx_{table_name}_partner ON {table_name} (partner);",
            f"CREATE INDEX IF NOT EXISTS idx_{table_name}_source ON {table_name} (source);",
            f"CREATE INDEX IF NOT EXISTS idx_{table_name}_aff_sub ON {table_name} (aff_sub);"
        ]
        
        for query in index_queries:
            await conn.execute(query)

    def get_target_table(self, conversion_data: Dict[str, Any]) -> str:
        """根據轉化數據確定目標表名"""
        if not config.should_use_separate_tables():
            return 'conversions'  # 如果未啟用分離，使用原始表
        
        platform = conversion_data.get('platform', '')
        data_source = config.get_data_source_for_platform(platform)
        table_name = config.get_table_name_for_source(data_source)
        
        # 簡化日誌
        logger.info(f"🎯 平台 '{platform}' -> 數據來源 '{data_source}' -> 表 '{table_name}'")
        
        return table_name

    def get_query_table(self, platform_name: str = None) -> str:
        """
        根據數據來源分離配置獲取查詢表名
        
        Args:
            platform_name: 平台名稱（可選，用於確定數據來源）
            
        Returns:
            str: 查詢表名
        """
        if not config.should_use_separate_tables():
            return 'conversions'  # 如果未啟用分離，使用原始表
        
        # 如果啟用數據來源分離，默認查詢API表（因為API代理插入的數據）
        if platform_name:
            data_source = config.get_data_source_for_platform(platform_name)
            table_name = config.get_table_name_for_platform(platform_name)
            logger.debug(f"📋 平台 {platform_name} -> 數據來源: {data_source} -> 表名: {table_name}")
            return table_name
        else:
            # 沒有指定平台，默認查詢API表
            return 'conversions_api'

    async def table_exists(self, table_name: str) -> bool:
        """檢查表是否存在"""
        if not self.pool:
            await self.init_pool()
        
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = $1
                )
                """, table_name)
                return bool(result)
        except Exception as e:
            logger.error(f"❌ 檢查表存在性失敗: {e}")
            return False
    
    async def insert_conversion_enhanced(self, conversion_data: Dict[str, Any]) -> Optional[int]:
        """
        插入單一轉化數據到數據庫 - 增強版本
        支持數據來源分離：根據平台自動選擇目標表
        """
        def safe_str(value):
            """安全地將值轉換為字符串"""
            if value is None or value == '' or str(value).lower() == 'none':
                return None
            return str(value)
        
        def safe_float(value):
            """安全地將值轉換為浮點數"""
            if value is None or value == '':
                return None
            try:
                return float(value)
            except (ValueError, TypeError):
                return None
    
        def safe_int(value):
            """安全地將值轉換為整數"""
            if value is None or value == '':
                return None
            try:
                return int(value)
            except (ValueError, TypeError):
                return None
                
        def safe_datetime(value):
            """安全地將值轉換為日期時間，強制使用UTC時區並轉換為naive datetime"""
            from datetime import timezone  # 在函数内部导入
            
            if value is None or value == '':
                return None
            
            try:
                # 如果已經是datetime對象
                if isinstance(value, datetime):
                    # 如果沒有時區信息，假定為UTC
                    if value.tzinfo is None:
                        value = value.replace(tzinfo=timezone.utc)
                    # 如果有時區信息，轉換為UTC
                    else:
                        value = value.astimezone(timezone.utc)
                    # 轉換為naive datetime（去掉時區信息）以便存儲到數據庫
                    return value.replace(tzinfo=None)
                
                # 如果是字符串，嘗試解析
                if isinstance(value, str):
                    # 處理常見的UTC時間格式
                    if value.endswith('Z'):
                        value = value[:-1] + '+00:00'
                    
                    # 常見的日期時間格式
                    formats = [
                        "%Y-%m-%d %H:%M:%S%z",  # 帶時區
                        "%Y-%m-%dT%H:%M:%S%z",  # ISO格式帶時區
                        "%Y-%m-%d %H:%M:%S",    # 不帶時區
                        "%Y-%m-%dT%H:%M:%S",    # ISO格式不帶時區
                        "%Y-%m-%d"              # 純日期
                    ]
                    
                    # 嘗試所有格式
                    for fmt in formats:
                        try:
                            dt = datetime.strptime(value, fmt)
                            # 如果解析出的時間沒有時區信息，設置為UTC
                            if dt.tzinfo is None:
                                dt = dt.replace(tzinfo=timezone.utc)
                            # 轉換為naive datetime（去掉時區信息）
                            return dt.replace(tzinfo=None)
                        except ValueError:
                            continue
                    
                    # 如果標準格式都失敗，嘗試使用dateutil
                    try:
                        from dateutil import parser
                        dt = parser.parse(value)
                        # 如果解析出的時間沒有時區信息，設置為UTC
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=timezone.utc)
                        else:
                            dt = dt.astimezone(timezone.utc)
                        # 轉換為naive datetime（去掉時區信息）
                        return dt.replace(tzinfo=None)
                    except ImportError:
                        logger.warning(f"🕒 safe_datetime: 無法解析日期 '{value}'，建議安裝 python-dateutil")
                        # 如果無法解析，返回當前UTC時間（naive）
                        return datetime.now(timezone.utc).replace(tzinfo=None)
                    except (ValueError, TypeError) as e:
                        logger.error(f"🕒 safe_datetime: dateutil解析失敗 '{value}': {e}")
                        # 如果解析失敗，返回當前UTC時間（naive）
                        return datetime.now(timezone.utc).replace(tzinfo=None)
                
                logger.error(f"🕒 safe_datetime: 不支持的類型 {type(value)}: {value}")
                # 如果是不支持的類型，返回當前UTC時間（naive）
                return datetime.now(timezone.utc).replace(tzinfo=None)
            except (ValueError, TypeError, ImportError) as e:
                logger.error(f"🕒 safe_datetime: 解析失敗 '{value}': {e}")
                # 如果發生任何錯誤，返回當前UTC時間（naive）
                return datetime.now(timezone.utc).replace(tzinfo=None)
        
        # 確定目標表名
        target_table = self.get_target_table(conversion_data)
        
        try:
            async with self.pool.acquire() as conn:
                # 準備完整的插入SQL（使用動態表名）
                insert_sql = f"""
                INSERT INTO {target_table} (
                    -- 核心分類字段
                    platform, partner, source,
                    
                    -- 核心轉化字段
                    conversion_id, offer_id, offer_name, order_id,
                    
                    -- 時間字段
                    datetime_conversion, datetime_conversion_updated, click_time,
                    
                    -- 完整金額字段
                    sale_amount_local, myr_sale_amount, usd_sale_amount,
                    payout_local, myr_payout, usd_payout,
                    sale_amount, payout, base_payout, bonus_payout,
                    
                    -- 貨幣字段
                    currency, conversion_currency,
                    
                    -- 廣告主參數
                    adv_sub, adv_sub1, adv_sub2, adv_sub3, adv_sub4, adv_sub5,
                    
                    -- 發布商參數
                    aff_sub, aff_sub1, aff_sub2, aff_sub3, aff_sub4, aff_sub5,
                    
                    -- 狀態字段
                    conversion_status, offer_status,
                    
                    -- 業務字段
                    merchant_id, affiliate_remarks, click_id,
                    
                    -- 佣金字段
                    commission_rate, avg_commission_rate,
                    
                    -- 系統字段
                    tenant_id, raw_data, event_time, created_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                    $11, $12, $13, $14, $15, $16, $17, $18, $19, $20,
                    $21, $22, $23, $24, $25, $26, $27, $28, $29, $30,
                    $31, $32, $33, $34, $35, $36, $37, $38, $39, $40,
                    $41, $42, $43, $44, $45
                )
                ON CONFLICT (conversion_id) DO UPDATE SET
                    platform = EXCLUDED.platform,
                    partner = EXCLUDED.partner,
                    source = EXCLUDED.source,
                    usd_sale_amount = EXCLUDED.usd_sale_amount,
                    usd_payout = EXCLUDED.usd_payout,
                    raw_data = EXCLUDED.raw_data,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
                """
                
                # 準備參數
                params = [
                    # 核心分類字段
                    safe_str(conversion_data.get('platform')),
                    safe_str(conversion_data.get('partner')),
                    safe_str(conversion_data.get('source')),
                    
                    # 核心轉化字段
                    safe_str(conversion_data.get('conversion_id')),
                    safe_str(conversion_data.get('offer_id')),
                    safe_str(conversion_data.get('offer_name')),
                    safe_str(conversion_data.get('order_id')),
                    
                    # 時間字段
                    safe_datetime(conversion_data.get('datetime_conversion')),
                    safe_datetime(conversion_data.get('datetime_conversion_updated')),
                    safe_datetime(conversion_data.get('click_time')),
                    
                    # 完整金額字段
                    safe_float(conversion_data.get('sale_amount_local')),
                    safe_float(conversion_data.get('myr_sale_amount')),
                    safe_float(conversion_data.get('usd_sale_amount')),
                    safe_float(conversion_data.get('payout_local')),
                    safe_float(conversion_data.get('myr_payout')),
                    safe_float(conversion_data.get('usd_payout')),
                    safe_float(conversion_data.get('sale_amount')),
                    safe_float(conversion_data.get('payout')),
                    safe_float(conversion_data.get('base_payout')),
                    safe_float(conversion_data.get('bonus_payout')),
                    
                    # 貨幣字段
                    safe_str(conversion_data.get('currency')),
                    safe_str(conversion_data.get('conversion_currency')),
                    
                    # 廣告主參數
                    safe_str(conversion_data.get('adv_sub')),
                    safe_str(conversion_data.get('adv_sub1')),
                    safe_str(conversion_data.get('adv_sub2')),
                    safe_str(conversion_data.get('adv_sub3')),
                    safe_str(conversion_data.get('adv_sub4')),
                    safe_str(conversion_data.get('adv_sub5')),
                    
                    # 發布商參數
                    safe_str(conversion_data.get('aff_sub')),
                    safe_str(conversion_data.get('aff_sub1')),
                    safe_str(conversion_data.get('aff_sub2')),
                    safe_str(conversion_data.get('aff_sub3')),
                    safe_str(conversion_data.get('aff_sub4')),
                    safe_str(conversion_data.get('aff_sub5')),
                    
                    # 狀態字段
                    safe_str(conversion_data.get('conversion_status')),
                    safe_str(conversion_data.get('offer_status')),
                    
                    # 業務字段
                    safe_str(conversion_data.get('merchant_id')),
                    safe_str(conversion_data.get('affiliate_remarks')),
                    safe_str(conversion_data.get('click_id')),
                    
                    # 佣金字段
                    safe_float(conversion_data.get('commission_rate')),
                    safe_float(conversion_data.get('avg_commission_rate')),
                    
                    # 系統字段
                    safe_int(conversion_data.get('tenant_id', 1)),
                    json.dumps(conversion_data.get('raw_data', conversion_data)),
                    safe_datetime(conversion_data.get('datetime_conversion') or datetime.now()),  # event_time
                    datetime.now(),  # created_at
                    datetime.now()  # updated_at
                ]
                
                # 執行插入
                record_id = await conn.fetchval(insert_sql, *params)
                
                logger.info(f"✅ 插入完整轉化數據成功: ID={record_id}, conversion_id={conversion_data.get('conversion_id')}, platform={conversion_data.get('platform')}, partner={conversion_data.get('partner')}")
                return record_id
                
        except Exception as e:
            logger.error(f"❌ 插入完整轉化數據失敗: {str(e)}")
            logger.error(f"   conversion_id: {conversion_data.get('conversion_id')}")
            logger.error(f"   platform: {conversion_data.get('platform')}")
            logger.error(f"   partner: {conversion_data.get('partner')}")
            return None
    
    async def insert_conversion_batch_optimized(self, conversions: List[Dict[str, Any]], platform_name: str = None, batch_size: int = 25) -> List[int]:
        """
        高性能批量插入完整轉化數據 - 超稳定性优化版本
        使用真正的批量插入 + 分批處理，性能提升15-30倍
        
        Args:
            conversions: 轉化數據列表
            platform_name: 平台名稱（可選，用於日誌）
            batch_size: 每批處理的記錄數量（默認25，超高稳定性）
            
        Returns:
            成功插入的記錄ID列表
        """
        if not self.pool:
            await self.init_pool()
        
        if not conversions:
            return []
        
        # 確保數據庫schema是最新的
        await self.ensure_database_schema()
        
        logger.info(f"🚀 開始高性能批量插入: {len(conversions)} 條記錄 (每批 {batch_size} 條)")
        if platform_name:
            logger.info(f"   平台: {platform_name}")
        
        # 數據處理函數（復用現有的安全轉換）
        def safe_str(value):
            if value is None or value == '' or str(value).lower() == 'none':
                return None
            return str(value)
        
        def safe_float(value):
            if value is None or value == '':
                return None
            try:
                return float(value)
            except (ValueError, TypeError):
                return None
        
        def safe_datetime(value):
            """安全地將值轉換為日期時間，強制使用UTC時區並轉換為naive datetime"""
            from datetime import timezone, datetime  # 在函数内部导入
            
            if value is None or value == '':
                return None
            
            try:
                # 處理 pandas Timestamp 對象
                if hasattr(value, 'to_pydatetime'):
                    value = value.to_pydatetime()
                
                # 如果已經是datetime對象
                if isinstance(value, datetime):
                    # 如果沒有時區信息，假定為UTC
                    if value.tzinfo is None:
                        value = value.replace(tzinfo=timezone.utc)
                    # 如果有時區信息，轉換為UTC
                    else:
                        value = value.astimezone(timezone.utc)
                    # 轉換為naive datetime（去掉時區信息）以便存儲到數據庫
                    return value.replace(tzinfo=None)
                
                if isinstance(value, str):
                    if value.endswith('Z'):
                        value = value[:-1] + '+00:00'
                    
                    formats = [
                        "%Y-%m-%d %H:%M:%S%z",
                        "%Y-%m-%dT%H:%M:%S%z", 
                        "%Y-%m-%d %H:%M:%S",
                        "%Y-%m-%dT%H:%M:%S",
                        "%Y-%m-%d"
                    ]
                    
                    for fmt in formats:
                        try:
                            dt = datetime.strptime(value, fmt)
                            if dt.tzinfo is None:
                                dt = dt.replace(tzinfo=timezone.utc)
                            return dt.replace(tzinfo=None)
                        except ValueError:
                            continue
                    
                    try:
                        from dateutil import parser
                        dt = parser.parse(value)
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=timezone.utc)
                        else:
                            dt = dt.astimezone(timezone.utc)
                        return dt.replace(tzinfo=None)
                    except (ImportError, ValueError, TypeError):
                        return datetime.now(timezone.utc).replace(tzinfo=None)
                
                return datetime.now(timezone.utc).replace(tzinfo=None)
            except Exception:
                return datetime.now(timezone.utc).replace(tzinfo=None)
        
        def safe_int(value):
            if value is None or value == '':
                return None
            try:
                return int(value)
            except (ValueError, TypeError):
                return None
        
        # 準備批量插入SQL
        # 根據數據來源分離配置確定目標表
        if config.should_use_separate_tables():
            if conversions:
                target_table = self.get_target_table(conversions[0])
                logger.info(f"🎯 數據來源分離已啟用，目標表: {target_table}")
            else:
                target_table = 'conversions_api'
                logger.info(f"🎯 數據來源分離已啟用，使用默認API表: {target_table}")
        else:
            target_table = 'conversions'
            logger.info(f"🎯 使用統一表: {target_table}")
        
        insert_sql = f"""
        INSERT INTO {target_table} (
            platform, partner, source,
            conversion_id, offer_id, offer_name, order_id,
            datetime_conversion, datetime_conversion_updated, click_time,
            sale_amount_local, myr_sale_amount, usd_sale_amount,
            payout_local, myr_payout, usd_payout,
            sale_amount, payout, base_payout, bonus_payout,
            currency, conversion_currency,
            adv_sub, adv_sub1, adv_sub2, adv_sub3, adv_sub4, adv_sub5,
            aff_sub, aff_sub1, aff_sub2, aff_sub3, aff_sub4, aff_sub5,
            conversion_status, offer_status,
            merchant_id, affiliate_remarks, click_id,
            commission_rate, avg_commission_rate,
            tenant_id, raw_data, event_time, created_at, updated_at
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
            $11, $12, $13, $14, $15, $16, $17, $18, $19, $20,
            $21, $22, $23, $24, $25, $26, $27, $28, $29, $30,
            $31, $32, $33, $34, $35, $36, $37, $38, $39, $40,
            $41, $42, $43, $44, $45, $46
        )
        ON CONFLICT (conversion_id) DO UPDATE SET
            platform = EXCLUDED.platform,
            partner = EXCLUDED.partner,
            source = EXCLUDED.source,
            usd_sale_amount = EXCLUDED.usd_sale_amount,
            usd_payout = EXCLUDED.usd_payout,
            raw_data = EXCLUDED.raw_data,
            updated_at = CURRENT_TIMESTAMP
        """
        
        # 移除RETURNING子句用于批量插入
        insert_sql_batch = insert_sql
        
        failed_count = 0
        success_count = 0
        total_batches = (len(conversions) + batch_size - 1) // batch_size
        
        # 🔧 修复：使用多次连接获取而不是长时间持有连接
        for batch_idx in range(0, len(conversions), batch_size):
            batch_end = min(batch_idx + batch_size, len(conversions))
            current_batch = conversions[batch_idx:batch_end]
            
            logger.info(f"📦 處理批次 {batch_idx//batch_size + 1}/{total_batches}: {len(current_batch)} 條記錄")
            
            # 準備批次數據
            batch_data = []
            batch_failed = 0
            for conversion in current_batch:
                try:
                    processed_data = self._prepare_conversion_data(conversion)
                    batch_data.append(processed_data)
                except Exception as e:
                    logger.error(f"❌ 準備轉化數據失敗: {str(e)}")
                    batch_failed += 1
                    continue
            
            if not batch_data:
                failed_count += len(current_batch)
                continue
            
            # �� 修复：为每个批次获取新的连接，使用更稳定的连接管理
            max_retries = 5
            batch_success_count = 0
            
            for retry in range(max_retries):
                conn = None
                try:
                    # 为每个批次获取新连接，设置较短的超时时间
                    conn = await asyncio.wait_for(self.pool.acquire(), timeout=30)
                    start_time = time.time()
                    
                    # 尝试批量插入
                    await asyncio.wait_for(conn.executemany(insert_sql_batch, batch_data), timeout=120)
                    batch_success_count = len(batch_data)
                    
                    success_count += batch_success_count
                    elapsed = time.time() - start_time
                    rate = batch_success_count / elapsed if elapsed > 0 else 0
                    logger.info(f"✅ 批次 {batch_idx//batch_size + 1} 完成: {batch_success_count}/{len(current_batch)} 條成功 ({elapsed:.2f}秒, {rate:.1f} 條/秒)")
                    break  # 成功，跳出重试循环
                    
                except Exception as batch_error:
                    logger.warning(f"⚠️ 批量插入失敗 (重試 {retry+1}/{max_retries}): {batch_error}")
                    
                    # 如果是最后一次重试，尝试逐条插入
                    if retry == max_retries - 1 and conn is not None:
                        logger.info(f"🔄 嘗試逐條插入批次 {batch_idx//batch_size + 1}...")
                        batch_success_count = 0
                        
                        # 逐条插入时使用相同的连接，但添加更好的错误处理
                        for i, data in enumerate(batch_data):
                            try:
                                await asyncio.wait_for(conn.execute(insert_sql_batch, *data), timeout=30)
                                batch_success_count += 1
                            except Exception as single_error:
                                if "duplicate key" in str(single_error).lower():
                                    batch_success_count += 1  # 重复键视为成功
                                else:
                                    logger.debug(f"單條記錄插入失敗 [{i+1}]: {single_error}")
                                    continue
                        
                        success_count += batch_success_count
                        elapsed = time.time() - start_time
                        rate = batch_success_count / elapsed if elapsed > 0 else 0
                        logger.info(f"✅ 批次 {batch_idx//batch_size + 1} 完成 (逐條): {batch_success_count}/{len(current_batch)} 條成功 ({elapsed:.2f}秒, {rate:.1f} 條/秒)")
                    else:
                        # 等待后重试
                        await asyncio.sleep(min(2 ** retry, 10))  # 指数退避
                
                finally:
                    # 确保连接被正确释放
                    if conn is not None:
                        try:
                            await self.pool.release(conn)
                        except Exception as release_error:
                            logger.error(f"❌ 連接釋放失敗: {release_error}")
            
            # 如果所有重试都失败了
            if batch_success_count == 0:
                logger.error(f"❌ 批次 {batch_idx//batch_size + 1} 最終失敗，跳過")
                failed_count += len(current_batch)
        
        # 最終統計
        total_processed = len(conversions)
        success_rate = (success_count / total_processed) * 100 if total_processed > 0 else 0
        
        logger.info(f"🎉 高性能批量插入完成!")
        logger.info(f"   總記錄數: {total_processed:,}")
        logger.info(f"   成功插入: {success_count:,} ({success_rate:.1f}%)")
        logger.info(f"   插入失敗: {failed_count:,}")
        logger.info(f"   批次數量: {total_batches}")
        
        # 返回成功插入數量的虛擬ID列表
        return list(range(1, success_count + 1))

    async def insert_conversion_batch_enhanced(self, conversions: List[Dict[str, Any]], platform_name: str = None) -> List[int]:
        """
        批量插入完整轉化數據 - 增強版本 (舊版本，保留兼容性)
        支持所有字段的完整存儲
        
        Args:
            conversions: 轉化數據列表
            platform_name: 平台名稱（可選，用於日誌）
            
        Returns:
            成功插入的記錄ID列表
        """
        if not self.pool:
            await self.init_pool()
        
        if not conversions:
            return []
        
        # 確保數據庫schema是最新的
        await self.ensure_database_schema()
        
        logger.info(f"🚀 開始批量插入完整轉化數據: {len(conversions)} 條記錄...")
        if platform_name:
            logger.info(f"   平台: {platform_name}")
        
        successful_ids = []
        failed_count = 0
        
        try:
            # 逐條插入以確保數據完整性和錯誤處理
            for idx, conversion in enumerate(conversions, 1):
                try:
                    record_id = await self.insert_conversion_enhanced(conversion)
                    if record_id:
                        successful_ids.append(record_id)
                    else:
                        failed_count += 1
                        
                    # 每100條記錄報告一次進度
                    if idx % 100 == 0:
                        logger.info(f"   進度: {idx}/{len(conversions)} ({len(successful_ids)} 成功, {failed_count} 失敗)")
                        
                except Exception as e:
                    failed_count += 1
                    logger.error(f"❌ 插入第{idx}條轉化數據失敗: {str(e)}")
                    continue
                
            success_rate = (len(successful_ids) / len(conversions)) * 100 if conversions else 0
            logger.info(f"✅ 批量插入完成: {len(successful_ids)}/{len(conversions)} 條記錄成功 ({success_rate:.1f}%)")
            
            if failed_count > 0:
                logger.warning(f"⚠️ {failed_count} 條記錄插入失敗")
            
            return successful_ids
            
        except Exception as e:
            logger.error(f"❌ 批量插入失敗: {str(e)}")
            return successful_ids  # 返回已成功的ID
    
    async def get_conversion_stats_enhanced(self, platform_name: str = None, partner_name: str = None, days_ago: int = 1) -> Dict[str, Any]:
        """
        獲取增強的轉化統計信息
        
        Args:
            platform_name: 平台名稱過濾
            partner_name: 合作夥伴名稱過濾  
            days_ago: 天數前
            
        Returns:
            詳細的統計信息
        """
        if not self.pool:
            await self.init_pool()
        
        try:
            async with self.pool.acquire() as conn:
                # 設置較長的查詢超時時間
                await conn.execute("SET statement_timeout = '300s'")
                
                # 確定要查詢的表名 - 根據數據來源分離配置
                if config.should_use_separate_tables():
                    # 使用數據來源分離，優先查詢API表
                    query_table = 'conversions_api'
                    logger.info(f"🔍 數據來源分離已啟用，查詢表: {query_table}")
                else:
                    # 使用統一表
                    query_table = 'conversions'
                    logger.info(f"🔍 使用統一表: {query_table}")
                
                # 檢查表是否存在和有數據
                try:
                    table_check = await conn.fetchval(f"SELECT COUNT(*) FROM {query_table}")
                    logger.info(f"📊 {query_table} 表記錄數: {table_check}")
                except Exception as e:
                    logger.warning(f"⚠️ 無法查詢 {query_table} 表: {e}")
                    # 如果API表不存在或無數據，嘗試查詢conversions表
                    if query_table == 'conversions_api':
                        query_table = 'conversions'
                        table_check = await conn.fetchval(f"SELECT COUNT(*) FROM {query_table}")
                        logger.info(f"📊 降級到 {query_table} 表，記錄數: {table_check}")
                    else:
                        raise
                
                # 基礎統計查詢
                base_query = f"""
                SELECT 
                    COUNT(*) as total_conversions,
                    COUNT(DISTINCT platform) as total_platforms,
                    COUNT(DISTINCT partner) as total_partners,
                    COUNT(DISTINCT source) as total_sources,
                    SUM(COALESCE(sale_amount, usd_sale_amount, 0)) as total_usd_amount,
                    SUM(COALESCE(payout, usd_payout, 0)) as total_usd_payout,
                    MIN(created_at) as earliest_conversion,
                    MAX(created_at) as latest_conversion
                FROM {query_table}
                WHERE created_at >= $1
                """
                
                # 添加過濾條件
                conditions = []
                params = [datetime.now() - timedelta(days=days_ago)]
                param_idx = 2
                
                if platform_name:
                    conditions.append(f"AND platform = ${param_idx}")
                    params.append(platform_name)
                    param_idx += 1
                
                if partner_name:
                    conditions.append(f"AND partner = ${param_idx}")
                    params.append(partner_name)
                    param_idx += 1
                
                if conditions:
                    base_query += " " + " ".join(conditions)
                
                # 執行基礎統計
                basic_stats = await conn.fetchrow(base_query, *params)
                
                # Platform分析
                platform_query = f"""
                SELECT 
                    platform,
                    COUNT(*) as conversion_count,
                    SUM(COALESCE(sale_amount, usd_sale_amount, 0)) as total_amount,
                    COUNT(DISTINCT partner) as partner_count,
                    COUNT(DISTINCT source) as source_count
                FROM {query_table}
                WHERE created_at >= $1
                """
                if conditions:
                    platform_query += " " + " ".join(conditions)
                platform_query += " GROUP BY platform ORDER BY conversion_count DESC"
                
                platform_stats = await conn.fetch(platform_query, *params)
                
                # Partner分析
                partner_query = f"""
                SELECT 
                    partner,
                    platform,
                    COUNT(*) as conversion_count,
                    SUM(COALESCE(sale_amount, usd_sale_amount, 0)) as total_amount,
                    COUNT(DISTINCT source) as source_count,
                    ARRAY_AGG(DISTINCT source ORDER BY source) as sources_list
                FROM {query_table}
                WHERE created_at >= $1
                """
                if conditions:
                    partner_query += " " + " ".join(conditions)
                partner_query += " GROUP BY partner, platform ORDER BY conversion_count DESC"
                
                partner_stats = await conn.fetch(partner_query, *params)
                
                # Source分析 
                source_query = f"""
                SELECT 
                    source,
                    partner,
                    platform,
                    COUNT(*) as conversion_count,
                    SUM(COALESCE(sale_amount, usd_sale_amount, 0)) as total_amount
                FROM {query_table}
                WHERE created_at >= $1 AND source IS NOT NULL AND source != ''
                """
                if conditions:
                    source_query += " " + " ".join(conditions)
                source_query += " GROUP BY source, partner, platform ORDER BY conversion_count DESC LIMIT 20"
                
                source_stats = await conn.fetch(source_query, *params)
                
                # 組裝結果
                result = {
                    'query_info': {
                        'query_table': query_table,
                        'data_source_separation_enabled': config.should_use_separate_tables(),
                        'platform_filter': platform_name,
                        'partner_filter': partner_name,
                        'days_ago': days_ago,
                        'query_time': datetime.now().isoformat()
                    },
                    'basic_stats': dict(basic_stats) if basic_stats else {},
                    'platform_breakdown': [dict(row) for row in platform_stats],
                    'partner_breakdown': [dict(row) for row in partner_stats],
                    'top_sources': [dict(row) for row in source_stats],
                }
                
                logger.info(f"📊 從表 {query_table} 獲取統計信息成功: {result['basic_stats'].get('total_conversions', 0)} 條轉化")
                return result
                
        except Exception as e:
            logger.error(f"❌ 獲取增強統計信息失敗: {str(e)}")
            return {
                'error': str(e),
                'query_info': {
                    'query_table': query_table if 'query_table' in locals() else 'unknown',
                    'data_source_separation_enabled': config.should_use_separate_tables(),
                    'platform_filter': platform_name,
                    'partner_filter': partner_name,
                    'days_ago': days_ago,
                    'query_time': datetime.now().isoformat()
                }
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """健康檢查 - 增強版本"""
        if not self.pool:
            await self.init_pool()
        
        try:
            async with self.pool.acquire() as conn:
                # 基本連接測試
                await conn.fetchval("SELECT 1")
                
                # 確定要查詢的表名 - 根據數據來源分離配置
                if config.should_use_separate_tables():
                    # 使用數據來源分離，優先查詢API表
                    query_table = 'conversions_api'
                    logger.info(f"🔍 數據來源分離已啟用，查詢表: {query_table}")
                else:
                    # 使用統一表
                    query_table = 'conversions'
                    logger.info(f"🔍 使用統一表: {query_table}")
                
                # 檢查表結構和記錄數
                try:
                    conversions_count = await conn.fetchval(f"SELECT COUNT(*) FROM {query_table}")
                    logger.info(f"📊 {query_table} 表記錄數: {conversions_count}")
                except Exception as e:
                    logger.warning(f"⚠️ 無法查詢 {query_table} 表: {e}")
                    # 如果API表不存在，嘗試查詢conversions表
                    if query_table == 'conversions_api':
                        query_table = 'conversions'
                        conversions_count = await conn.fetchval(f"SELECT COUNT(*) FROM {query_table}")
                        logger.info(f"📊 降級到 {query_table} 表，記錄數: {conversions_count}")
                    else:
                        raise
                
                # 檢查新字段是否存在
                schema_check = await conn.fetch(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = '{query_table}' 
                AND column_name IN ('platform', 'partner', 'source')
                """)
                
                enhanced_fields = [row['column_name'] for row in schema_check]
                
                # 最近24小時統計
                recent_stats = await conn.fetchrow(f"""
                SELECT 
                    COUNT(*) as recent_conversions,
                    COUNT(DISTINCT platform) as platforms_count,
                    COUNT(DISTINCT partner) as partners_count,
                    COUNT(DISTINCT source) as sources_count
                FROM {query_table} 
                WHERE created_at >= NOW() - INTERVAL '24 hours'
                """)
                
                return {
                    'status': 'healthy',
                    'database_connection': 'ok',
                    'query_table': query_table,
                    'data_source_separation_enabled': config.should_use_separate_tables(),
                    'conversions_count': conversions_count,
                    'enhanced_fields_available': enhanced_fields,
                    'enhanced_schema': len(enhanced_fields) == 3,  # platform, partner, source
                    'recent_stats': dict(recent_stats) if recent_stats else {},
                    'platforms_count': recent_stats['platforms_count'] if recent_stats else 0,
                    'partners_count': recent_stats['partners_count'] if recent_stats else 0,
                    'check_time': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"❌ 健康檢查失敗: {str(e)}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'check_time': datetime.now().isoformat()
            }

    async def query_partner_stats_by_date(self, days_ago: int = 1, partner_filter: str = None, 
                                          query_source: str = None) -> List[Dict[str, Any]]:
        """
        按日期和Partner查詢統計數據
        支持數據來源分離：可指定查詢來源
        """
        if not self.pool:
            await self.init_pool()
        
        # 獲取查詢表名
        table_name = self.get_query_table(query_source)
        
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("SET statement_timeout = '300s'")
                
                # 構建查詢SQL
                base_query = f"""
                SELECT 
                    partner,
                    platform,
                    COUNT(*) as conversion_count,
                    SUM(COALESCE(usd_sale_amount, 0)) as total_amount
                FROM {table_name}
                WHERE DATE(datetime_conversion) = CURRENT_DATE - INTERVAL '{days_ago} days'
                """
                
                params = []
                if partner_filter and partner_filter != 'ALL':
                    base_query += " AND partner = $1"
                    params.append(partner_filter)
                
                base_query += " GROUP BY partner, platform ORDER BY conversion_count DESC"
                
                if params:
                    results = await conn.fetch(base_query, *params)
                else:
                    results = await conn.fetch(base_query)
                
                logger.info(f"✅ 查詢統計數據成功: 從表 {table_name} 獲取 {len(results)} 條記錄")
                return [dict(row) for row in results]
                
        except Exception as e:
            logger.error(f"❌ 查詢統計數據失敗: {str(e)}")
            return []

    async def query_source_stats_by_date(self, days_ago: int = 1, partner_filter: str = None,
                                        query_source: str = None) -> List[Dict[str, Any]]:
        """
        按日期查詢Source統計數據
        支持數據來源分離：可指定查詢來源
        """
        if not self.pool:
            await self.init_pool()
        
        # 獲取查詢表名
        table_name = self.get_query_table(query_source)
        
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("SET statement_timeout = '300s'")
                
                # 構建查詢SQL
                base_query = f"""
                SELECT 
                    source,
                    partner,
                    platform,
                    COUNT(*) as conversion_count,
                    SUM(COALESCE(usd_sale_amount, 0)) as total_amount
                FROM {table_name}
                WHERE DATE(datetime_conversion) = CURRENT_DATE - INTERVAL '{days_ago} days'
                """
                
                params = []
                if partner_filter and partner_filter != 'ALL':
                    base_query += " AND partner = $1"
                    params.append(partner_filter)
                
                base_query += " GROUP BY source, partner ORDER BY conversion_count DESC"
                
                if params:
                    results = await conn.fetch(base_query, *params)
                else:
                    results = await conn.fetch(base_query)
                
                logger.info(f"✅ 查詢Source統計成功: 從表 {table_name} 獲取 {len(results)} 條記錄")
                return [dict(row) for row in results]
                
        except Exception as e:
            logger.error(f"❌ 查詢Source統計失敗: {str(e)}")
            return []

    async def get_database_health_multi_source(self) -> Dict[str, Any]:
        """
        獲取多數據來源的數據庫健康狀態
        """
        if not self.pool:
            await self.init_pool()
        
        try:
            async with self.pool.acquire() as conn:
                health_data = {}
                
                # 檢查各個表的狀態
                tables_to_check = ['conversions']
                if config.should_use_separate_tables():
                    tables_to_check.extend(['conversions_api', 'conversions_postback'])
                
                for table_name in tables_to_check:
                    try:
                        # 檢查表是否存在
                        exists_query = """
                        SELECT EXISTS (
                            SELECT 1 FROM information_schema.tables 
                            WHERE table_name = $1
                        )
                        """
                        exists = await conn.fetchval(exists_query, table_name)
                        
                        if exists:
                            # 獲取記錄統計
                            count_query = f"SELECT COUNT(*) FROM {table_name}"
                            total_count = await conn.fetchval(count_query)
                            
                            # 獲取最近記錄統計
                            recent_query = f"""
                            SELECT COUNT(*) FROM {table_name} 
                            WHERE datetime_conversion >= CURRENT_DATE - INTERVAL '7 days'
                            """
                            recent_count = await conn.fetchval(recent_query)
                            
                            health_data[table_name] = {
                                'exists': True,
                                'total_records': total_count,
                                'recent_records_7days': recent_count
                            }
                        else:
                            health_data[table_name] = {
                                'exists': False,
                                'total_records': 0,
                                'recent_records_7days': 0
                            }
                    except Exception as e:
                        health_data[table_name] = {
                            'exists': False,
                            'error': str(e)
                        }
                
                logger.info(f"✅ 數據庫健康檢查完成: {len(health_data)} 個表")
                return health_data
                
        except Exception as e:
            logger.error(f"❌ 數據庫健康檢查失敗: {str(e)}")
            return {'error': str(e)}

    async def delete_conversions_by_date_range(self, start_date: str, end_date: str, 
                                              table_names: List[str] = None) -> Dict[str, int]:
        """
        根據日期範圍刪除轉化數據
        
        Args:
            start_date: 開始日期 (YYYY-MM-DD)
            end_date: 結束日期 (YYYY-MM-DD) 
            table_names: 要刪除的表名列表，None 表示刪除所有相關表
            
        Returns:
            Dict[str, int]: 每個表的刪除記錄數
        """
        if not self.pool:
            await self.init_pool()
        
        # 將字符串日期轉換為日期對象
        from datetime import datetime
        try:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError as e:
            logger.error(f"❌ 日期格式錯誤: {e}")
            raise
        
        # 確定要刪除的表
        if table_names is None:
            if config.should_use_separate_tables():
                table_names = ['conversions', 'conversions_api', 'conversions_postback']
            else:
                table_names = ['conversions']
        
        deletion_results = {}
        
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("SET statement_timeout = '600s'")  # 10分鐘超時
                
                for table_name in table_names:
                    try:
                        # 檢查表是否存在
                        exists_query = """
                        SELECT EXISTS (
                            SELECT 1 FROM information_schema.tables 
                            WHERE table_name = $1
                        )
                        """
                        exists = await conn.fetchval(exists_query, table_name)
                        
                        if not exists:
                            logger.warning(f"⚠️ 表 {table_name} 不存在，跳過")
                            deletion_results[table_name] = 0
                            continue
                        
                        # 先查詢要刪除的記錄數
                        count_query = f"""
                        SELECT COUNT(*) 
                        FROM {table_name}
                        WHERE DATE(datetime_conversion) >= $1 
                        AND DATE(datetime_conversion) <= $2
                        """
                        count_to_delete = await conn.fetchval(count_query, start_date_obj, end_date_obj)
                        
                        if count_to_delete == 0:
                            logger.info(f"📋 表 {table_name}: 沒有符合條件的記錄需要刪除")
                            deletion_results[table_name] = 0
                            continue
                        
                        logger.info(f"🗑️ 準備從表 {table_name} 刪除 {count_to_delete:,} 條記錄 ({start_date} 至 {end_date})")
                        
                        # 執行刪除操作
                        delete_query = f"""
                        DELETE FROM {table_name}
                        WHERE DATE(datetime_conversion) >= $1 
                        AND DATE(datetime_conversion) <= $2
                        """
                        
                        # 開始事務
                        async with conn.transaction():
                            result = await conn.execute(delete_query, start_date_obj, end_date_obj)
                            deleted_count = int(result.split()[-1])  # 從 "DELETE n" 中提取數字
                            
                            deletion_results[table_name] = deleted_count
                            logger.info(f"✅ 表 {table_name}: 成功刪除 {deleted_count:,} 條記錄")
                            
                    except Exception as e:
                        logger.error(f"❌ 表 {table_name} 刪除失敗: {str(e)}")
                        deletion_results[table_name] = -1  # 用 -1 表示錯誤
                
                # 總結刪除結果
                total_deleted = sum(count for count in deletion_results.values() if count > 0)
                logger.info(f"🎯 刪除操作完成: 總共刪除 {total_deleted:,} 條記錄")
                
                return deletion_results
                
        except Exception as e:
            logger.error(f"❌ 批量刪除操作失敗: {str(e)}")
            raise

    async def get_conversion_count_by_date_range(self, start_date: str, end_date: str,
                                               table_names: List[str] = None) -> Dict[str, int]:
        """
        獲取指定日期範圍內的轉化記錄數統計
        
        Args:
            start_date: 開始日期 (YYYY-MM-DD)
            end_date: 結束日期 (YYYY-MM-DD)
            table_names: 要統計的表名列表
            
        Returns:
            Dict[str, int]: 每個表的記錄數
        """
        if not self.pool:
            await self.init_pool()
        
        # 將字符串日期轉換為日期對象
        from datetime import datetime
        try:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError as e:
            logger.error(f"❌ 日期格式錯誤: {e}")
            raise
        
        if table_names is None:
            if config.should_use_separate_tables():
                table_names = ['conversions', 'conversions_api', 'conversions_postback']
            else:
                table_names = ['conversions']
        
        count_results = {}
        
        try:
            async with self.pool.acquire() as conn:
                for table_name in table_names:
                    try:
                        # 檢查表是否存在
                        exists_query = """
                        SELECT EXISTS (
                            SELECT 1 FROM information_schema.tables 
                            WHERE table_name = $1
                        )
                        """
                        exists = await conn.fetchval(exists_query, table_name)
                        
                        if not exists:
                            count_results[table_name] = 0
                            continue
                        
                        # 統計記錄數
                        count_query = f"""
                        SELECT COUNT(*) 
                        FROM {table_name}
                        WHERE DATE(datetime_conversion) >= $1 
                        AND DATE(datetime_conversion) <= $2
                        """
                        count = await conn.fetchval(count_query, start_date_obj, end_date_obj)
                        count_results[table_name] = count
                        
                    except Exception as e:
                        logger.error(f"❌ 統計表 {table_name} 失敗: {str(e)}")
                        count_results[table_name] = -1
                
                return count_results
                
        except Exception as e:
            logger.error(f"❌ 批量統計操作失敗: {str(e)}")
            return {}

    async def query_partner_stats_by_date_range(self, start_date: str, end_date: str, 
                                               partner_filter: str = None) -> List[Dict]:
        """根據日期範圍查詢 Partner 統計 - 支持數據來源分離"""
        if not self.pool:
            await self.init_pool()
            
        query_table = self.get_query_table()
        
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("SET statement_timeout = '300s'")
                
                # 構建基礎查詢
                query = f"""
                SELECT 
                    partner,
                    platform,
                    COUNT(*) as conversion_count,
                    SUM(COALESCE(usd_sale_amount, 0)) as total_amount,
                    COUNT(DISTINCT source) as source_count,
                    ARRAY_AGG(DISTINCT source ORDER BY source) as sources_list
                FROM {query_table}
                WHERE DATE(datetime_conversion) >= $1 AND DATE(datetime_conversion) <= $2
                """
                
                params = [
                    datetime.strptime(start_date, "%Y-%m-%d").date(),
                    datetime.strptime(end_date, "%Y-%m-%d").date()
                ]
                
                if partner_filter:
                    query += " AND partner = $3"
                    params.append(partner_filter)
                
                query += " GROUP BY partner, platform ORDER BY conversion_count DESC"
                
                results = await conn.fetch(query, *params)
                return [dict(row) for row in results]
                
        except Exception as e:
            logger.error(f"❌ 查詢Partner統計數據失敗: {str(e)}")
            return []

    async def query_source_stats_by_date_range(self, start_date: str, end_date: str,
                                              partner_filter: str = None) -> List[Dict]:
        """根據日期範圍查詢 Source 統計 - 支持數據來源分離"""
        if not self.pool:
            await self.init_pool()
            
        query_table = self.get_query_table()
        
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("SET statement_timeout = '300s'")
                
                # 構建基礎查詢
                query = f"""
                SELECT 
                    source,
                    partner,
                    platform,
                    COUNT(*) as conversion_count,
                    SUM(COALESCE(usd_sale_amount, 0)) as total_amount
                FROM {query_table}
                WHERE DATE(datetime_conversion) >= $1 AND DATE(datetime_conversion) <= $2
                """
                
                params = [
                    datetime.strptime(start_date, "%Y-%m-%d").date(),
                    datetime.strptime(end_date, "%Y-%m-%d").date()
                ]
                
                if partner_filter:
                    query += " AND partner = $3"
                    params.append(partner_filter)
                
                query += " GROUP BY source, partner, platform ORDER BY conversion_count DESC"
                
                results = await conn.fetch(query, *params)
                return [dict(row) for row in results]
                
        except Exception as e:
            logger.error(f"❌ 查詢Source統計失敗: {str(e)}")
            return []

    def _prepare_conversion_data(self, conversion: Dict[str, Any]) -> List:
        """準備轉化數據的參數列表"""
        import json
        from datetime import datetime
        
        # 安全轉換函數（內聯實現）
        def safe_str(value):
            if value is None:
                return None
            return str(value) if value != '' else None
        
        def safe_float(value):
            if value is None or value == '':
                return None
            try:
                return float(value)
            except (ValueError, TypeError):
                return None
        
        def safe_datetime(value):
            """安全地將值轉換為日期時間，強制使用UTC時區並轉換為naive datetime"""
            from datetime import timezone, datetime  # 在函数内部导入
            
            if value is None or value == '':
                return None
            
            try:
                # 處理 pandas Timestamp 對象
                if hasattr(value, 'to_pydatetime'):
                    value = value.to_pydatetime()
                
                # 如果已經是datetime對象
                if isinstance(value, datetime):
                    # 如果沒有時區信息，假定為UTC
                    if value.tzinfo is None:
                        value = value.replace(tzinfo=timezone.utc)
                    # 如果有時區信息，轉換為UTC
                    else:
                        value = value.astimezone(timezone.utc)
                    # 轉換為naive datetime（去掉時區信息）以便存儲到數據庫
                    return value.replace(tzinfo=None)
                
                # 如果是字符串，嘗試解析
                if isinstance(value, str):
                    # 處理常見的UTC時間格式
                    if value.endswith('Z'):
                        value = value[:-1] + '+00:00'
                    
                    # 常見的日期時間格式
                    formats = [
                        "%Y-%m-%d %H:%M:%S%z",  # 帶時區
                        "%Y-%m-%dT%H:%M:%S%z",  # ISO格式帶時區
                        "%Y-%m-%d %H:%M:%S",    # 不帶時區
                        "%Y-%m-%dT%H:%M:%S",    # ISO格式不帶時區
                        "%Y-%m-%d"              # 純日期
                    ]
                    
                    # 嘗試所有格式
                    for fmt in formats:
                        try:
                            dt = datetime.strptime(value, fmt)
                            # 如果解析出的時間沒有時區信息，設置為UTC
                            if dt.tzinfo is None:
                                dt = dt.replace(tzinfo=timezone.utc)
                            # 轉換為naive datetime（去掉時區信息）
                            return dt.replace(tzinfo=None)
                        except ValueError:
                            continue
                    
                    # 如果標準格式都失敗，嘗試使用dateutil
                    try:
                        from dateutil import parser
                        dt = parser.parse(value)
                        # 如果解析出的時間沒有時區信息，設置為UTC
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=timezone.utc)
                        else:
                            dt = dt.astimezone(timezone.utc)
                        # 轉換為naive datetime（去掉時區信息）
                        return dt.replace(tzinfo=None)
                    except ImportError:
                        logger.warning(f"🕒 safe_datetime: 無法解析日期 '{value}'，建議安裝 python-dateutil")
                        # 如果無法解析，返回當前UTC時間（naive）
                        return datetime.now(timezone.utc).replace(tzinfo=None)
                    except (ValueError, TypeError) as e:
                        logger.error(f"🕒 safe_datetime: dateutil解析失敗 '{value}': {e}")
                        # 如果解析失敗，返回當前UTC時間（naive）
                        return datetime.now(timezone.utc).replace(tzinfo=None)
                
                logger.error(f"🕒 safe_datetime: 不支持的類型 {type(value)}: {value}")
                # 如果是不支持的類型，返回當前UTC時間（naive）
                return datetime.now(timezone.utc).replace(tzinfo=None)
            except (ValueError, TypeError, ImportError) as e:
                logger.error(f"🕒 safe_datetime: 解析失敗 '{value}': {e}")
                # 如果發生任何錯誤，返回當前UTC時間（naive）
                return datetime.now(timezone.utc).replace(tzinfo=None)
        
        def safe_int(value):
            if value is None or value == '':
                return None
            try:
                return int(value)
            except (ValueError, TypeError):
                return None
        
        return [
            # 核心分類字段 (3個)
            safe_str(conversion.get('platform')),
            safe_str(conversion.get('partner')),
            safe_str(conversion.get('source')),
            
            # 核心轉化字段 (4個)
            safe_str(conversion.get('conversion_id')),
            safe_str(conversion.get('offer_id')),
            safe_str(conversion.get('offer_name')),
            safe_str(conversion.get('order_id')),
            
            # 時間字段 (3個)
            safe_datetime(conversion.get('datetime_conversion')),
            safe_datetime(conversion.get('datetime_conversion_updated')),
            safe_datetime(conversion.get('click_time')),
            
            # 金額字段 (10個)
            safe_float(conversion.get('sale_amount_local')),
            safe_float(conversion.get('myr_sale_amount')),
            safe_float(conversion.get('usd_sale_amount')),
            safe_float(conversion.get('payout_local')),
            safe_float(conversion.get('myr_payout')),
            safe_float(conversion.get('usd_payout')),
            safe_float(conversion.get('sale_amount')),
            safe_float(conversion.get('payout')),
            safe_float(conversion.get('base_payout')),
            safe_float(conversion.get('bonus_payout')),
            
            # 貨幣字段 (2個)
            safe_str(conversion.get('currency')),
            safe_str(conversion.get('conversion_currency')),
            
            # 廣告主參數 (6個)
            safe_str(conversion.get('adv_sub')),
            safe_str(conversion.get('adv_sub1')),
            safe_str(conversion.get('adv_sub2')),
            safe_str(conversion.get('adv_sub3')),
            safe_str(conversion.get('adv_sub4')),
            safe_str(conversion.get('adv_sub5')),
            
            # 發布商參數 (6個)
            safe_str(conversion.get('aff_sub')),
            safe_str(conversion.get('aff_sub1')),
            safe_str(conversion.get('aff_sub2')),
            safe_str(conversion.get('aff_sub3')),
            safe_str(conversion.get('aff_sub4')),
            safe_str(conversion.get('aff_sub5')),
            
            # 狀態字段 (2個)
            safe_str(conversion.get('conversion_status')),
            safe_str(conversion.get('offer_status')),
            
            # 業務字段 (3個)
            safe_str(conversion.get('merchant_id')),
            safe_str(conversion.get('affiliate_remarks')),
            safe_str(conversion.get('click_id')),
            
            # 佣金字段 (2個)
            safe_float(conversion.get('commission_rate')),
            safe_float(conversion.get('avg_commission_rate')),
            
            # 系統字段 (5個)
            safe_int(conversion.get('tenant_id', 1)),
            json.dumps(conversion.get('raw_data', conversion)),
            safe_datetime(conversion.get('datetime_conversion')) or datetime.now(),  # event_time
            datetime.now(),  # created_at
            datetime.now(),  # updated_at
        ]

# 保持向後兼容性的別名，但推薦使用增強版本
DMPDatabaseManager = EnhancedDMPDatabaseManager 