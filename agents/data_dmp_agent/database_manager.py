#!/usr/bin/env python3
"""
DMP-Agent 數據庫管理器 - 增強版本
支持完整的轉化數據存儲，包括platform、partner、source等所有字段
從Reporter-Agent遷移的Google Cloud SQL存儲邏輯
"""

import asyncio
import asyncpg
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from decimal import Decimal

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
        """初始化数据库连接池"""
        try:
            self.pool = await asyncpg.create_pool(
                self.connection_string,
                min_size=2,
                max_size=10,
                command_timeout=30
            )
            logger.info("✅ 增強版DMP-Agent數據庫連接池初始化成功")
        except Exception as e:
            logger.error(f"❌ DMP-Agent數據庫連接池初始化失敗: {e}")
            raise
    
    async def close_pool(self):
        """关闭数据库连接池"""
        if self.pool:
            await self.pool.close()
        logger.info("✅ DMP-Agent數據庫連接池已關閉")
    
    async def ensure_database_schema(self):
        """
        確保數據庫schema包含所有新增字段
        為升級現有數據庫添加缺失字段
        """
        if not self.pool:
            await self.init_pool()
        
        logger.info("🔧 檢查並更新數據庫schema...")
        
        try:
            async with self.pool.acquire() as conn:
                # 檢查conversions表是否存在新字段
                schema_updates = [
                    # 核心分類字段
                    "ALTER TABLE conversions ADD COLUMN IF NOT EXISTS platform VARCHAR(100)",
                    "ALTER TABLE conversions ADD COLUMN IF NOT EXISTS partner VARCHAR(100)",
                    "ALTER TABLE conversions ADD COLUMN IF NOT EXISTS source VARCHAR(255)",
                    
                    # 完整的金額字段
                    "ALTER TABLE conversions ADD COLUMN IF NOT EXISTS sale_amount DECIMAL(15,2)",
                    "ALTER TABLE conversions ADD COLUMN IF NOT EXISTS payout DECIMAL(15,2)", 
                    "ALTER TABLE conversions ADD COLUMN IF NOT EXISTS base_payout DECIMAL(15,2)",
                    "ALTER TABLE conversions ADD COLUMN IF NOT EXISTS bonus_payout DECIMAL(15,2)",
                    "ALTER TABLE conversions ADD COLUMN IF NOT EXISTS sale_amount_local DECIMAL(15,2)",
                    "ALTER TABLE conversions ADD COLUMN IF NOT EXISTS myr_sale_amount DECIMAL(15,2)",
                    "ALTER TABLE conversions ADD COLUMN IF NOT EXISTS payout_local DECIMAL(15,2)",
                    "ALTER TABLE conversions ADD COLUMN IF NOT EXISTS myr_payout DECIMAL(15,2)",
                    
                    # 擴展的參數字段
                    "ALTER TABLE conversions ADD COLUMN IF NOT EXISTS aff_sub1 VARCHAR(255)",
                    "ALTER TABLE conversions ADD COLUMN IF NOT EXISTS aff_sub2 VARCHAR(255)",
                    "ALTER TABLE conversions ADD COLUMN IF NOT EXISTS aff_sub3 VARCHAR(255)",
                    "ALTER TABLE conversions ADD COLUMN IF NOT EXISTS aff_sub4 VARCHAR(255)",
                    "ALTER TABLE conversions ADD COLUMN IF NOT EXISTS aff_sub5 VARCHAR(255)",
                    
                    "ALTER TABLE conversions ADD COLUMN IF NOT EXISTS adv_sub VARCHAR(255)",
                    "ALTER TABLE conversions ADD COLUMN IF NOT EXISTS adv_sub1 VARCHAR(255)",
                    "ALTER TABLE conversions ADD COLUMN IF NOT EXISTS adv_sub2 VARCHAR(255)",
                    "ALTER TABLE conversions ADD COLUMN IF NOT EXISTS adv_sub3 VARCHAR(255)",
                    "ALTER TABLE conversions ADD COLUMN IF NOT EXISTS adv_sub4 VARCHAR(255)",
                    "ALTER TABLE conversions ADD COLUMN IF NOT EXISTS adv_sub5 VARCHAR(255)",
                    
                    # 狀態和業務字段
                    "ALTER TABLE conversions ADD COLUMN IF NOT EXISTS conversion_status VARCHAR(50)",
                    "ALTER TABLE conversions ADD COLUMN IF NOT EXISTS offer_status VARCHAR(50)",
                    "ALTER TABLE conversions ADD COLUMN IF NOT EXISTS merchant_id VARCHAR(100)",
                    "ALTER TABLE conversions ADD COLUMN IF NOT EXISTS affiliate_remarks TEXT",
                    "ALTER TABLE conversions ADD COLUMN IF NOT EXISTS click_id VARCHAR(255)",
                    "ALTER TABLE conversions ADD COLUMN IF NOT EXISTS click_time TIMESTAMP WITH TIME ZONE",
                    
                    # 時間字段
                    "ALTER TABLE conversions ADD COLUMN IF NOT EXISTS datetime_conversion TIMESTAMP WITH TIME ZONE",
                    "ALTER TABLE conversions ADD COLUMN IF NOT EXISTS datetime_conversion_updated TIMESTAMP WITH TIME ZONE",
                    
                    # 貨幣字段
                    "ALTER TABLE conversions ADD COLUMN IF NOT EXISTS currency VARCHAR(3)",
                    "ALTER TABLE conversions ADD COLUMN IF NOT EXISTS conversion_currency VARCHAR(3)",
                    
                    # 佣金字段
                    "ALTER TABLE conversions ADD COLUMN IF NOT EXISTS commission_rate DECIMAL(8,4)",
                    "ALTER TABLE conversions ADD COLUMN IF NOT EXISTS avg_commission_rate DECIMAL(8,4)",
                    
                    # 訂單信息
                    "ALTER TABLE conversions ADD COLUMN IF NOT EXISTS order_id VARCHAR(100)",
                    "ALTER TABLE conversions ADD COLUMN IF NOT EXISTS offer_id VARCHAR(50)",
                    "ALTER TABLE conversions ADD COLUMN IF NOT EXISTS offer_name TEXT",
                    
                    # 系統時間戳字段
                    "ALTER TABLE conversions ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP",
                ]
                
                # 執行schema更新
                for update_sql in schema_updates:
                    try:
                        await conn.execute(update_sql)
                    except Exception as e:
                        logger.warning(f"⚠️ Schema更新失敗: {update_sql[:50]}... - {str(e)}")
                
                # 創建索引
                index_updates = [
                    "CREATE INDEX IF NOT EXISTS idx_conversions_platform ON conversions(platform)",
                    "CREATE INDEX IF NOT EXISTS idx_conversions_partner ON conversions(partner)",
                    "CREATE INDEX IF NOT EXISTS idx_conversions_source ON conversions(source)",
                    "CREATE INDEX IF NOT EXISTS idx_conversions_platform_partner ON conversions(platform, partner)",
                    "CREATE INDEX IF NOT EXISTS idx_conversions_datetime ON conversions(datetime_conversion)",
                    "CREATE INDEX IF NOT EXISTS idx_conversions_status ON conversions(conversion_status)",
                ]
                
                for index_sql in index_updates:
                    try:
                        await conn.execute(index_sql)
                    except Exception as e:
                        logger.warning(f"⚠️ 索引創建失敗: {index_sql[:50]}... - {str(e)}")
                
                logger.info("✅ 數據庫schema更新完成")
                
        except Exception as e:
            logger.error(f"❌ 數據庫schema更新失敗: {str(e)}")
            raise
    
    async def insert_conversion_enhanced(self, conversion_data: Dict[str, Any]) -> Optional[int]:
        """
        插入單一轉化數據到數據庫 - 增強版本
        """
        def safe_str(value):
            """安全地將值轉換為字符串"""
            if value is None:
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
            """安全地將值轉換為datetime對象"""
            if value is None or value == '':
                logger.debug(f"🕒 safe_datetime: 空值輸入")
                return None
            if isinstance(value, datetime):
                logger.debug(f"🕒 safe_datetime: datetime對象輸入 = {value}")
                return value
            try:
                # 嘗試解析ISO格式的時間字符串
                if isinstance(value, str):
                    logger.debug(f"🕒 safe_datetime: 字符串輸入 = '{value}'")
                    # 處理多種時間格式
                    for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%S.%f']:
                        try:
                            parsed_dt = datetime.strptime(value, fmt)
                            logger.debug(f"🕒 safe_datetime: 成功解析 '{value}' → {parsed_dt} (格式: {fmt})")
                            
                            # 🔧 時區修復：API 返回的時間應該被解釋為 UTC 時間
                            if parsed_dt.tzinfo is None:
                                from datetime import timezone
                                parsed_dt = parsed_dt.replace(tzinfo=timezone.utc)
                                logger.info(f"🕒 safe_datetime: 將API時間解釋為UTC → 原始: '{value}' 結果: {parsed_dt}")
                            
                            return parsed_dt
                        except ValueError:
                            continue
                    # 如果上述格式都不匹配，嘗試使用dateutil parser
                    from dateutil import parser
                    parsed_dt = parser.parse(value)
                    logger.debug(f"🕒 safe_datetime: dateutil解析 '{value}' → {parsed_dt}")
                    
                    # 🔧 時區修復：dateutil 解析結果也需要檢查時區
                    if parsed_dt.tzinfo is None:
                        from datetime import timezone
                        parsed_dt = parsed_dt.replace(tzinfo=timezone.utc)
                        logger.info(f"🕒 safe_datetime: dateutil結果設置為UTC時區 → 原始: '{value}' 結果: {parsed_dt}")
                    
                    return parsed_dt
                logger.warning(f"🕒 safe_datetime: 不支持的類型 {type(value)}: {value}")
                return None
            except (ValueError, TypeError, ImportError) as e:
                logger.error(f"🕒 safe_datetime: 解析失敗 '{value}': {e}")
            return None
    
        if not self.pool:
            await self.init_pool()
        
        try:
            async with self.pool.acquire() as conn:
                # 準備完整的插入SQL
                insert_sql = """
                INSERT INTO conversions (
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
                    safe_datetime(conversion_data.get('datetime_conversion') or datetime.now()),
                    datetime.now()
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
    
    async def insert_conversion_batch_optimized(self, conversions: List[Dict[str, Any]], platform_name: str = None, batch_size: int = 500) -> List[int]:
        """
        高性能批量插入完整轉化數據 - 優化版本
        使用真正的批量插入 + 分批處理，性能提升15-30倍
        
        Args:
            conversions: 轉化數據列表
            platform_name: 平台名稱（可選，用於日誌）
            batch_size: 每批處理的記錄數量（默認500）
            
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
            if value is None:
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
            if value is None or value == '':
                return None
            try:
                return int(value)
            except (ValueError, TypeError):
                return None
        
        def safe_datetime(value):
            if value is None or value == '':
                logger.debug(f"🕒 safe_datetime: 空值輸入")
                return None
            if isinstance(value, datetime):
                logger.debug(f"🕒 safe_datetime: datetime對象輸入 = {value}")
                return value
            try:
                if isinstance(value, str):
                    logger.debug(f"🕒 safe_datetime: 字符串輸入 = '{value}'")
                    for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%S.%f']:
                        try:
                            parsed_dt = datetime.strptime(value, fmt)
                            logger.debug(f"🕒 safe_datetime: 成功解析 '{value}' → {parsed_dt} (格式: {fmt})")
                            
                            # 🔧 時區修復：API 返回的時間應該被解釋為 UTC 時間
                            # 這樣可以保持日期正確，避免時區轉換導致的日期偏移
                            if parsed_dt.tzinfo is None:
                                from datetime import timezone
                                parsed_dt = parsed_dt.replace(tzinfo=timezone.utc)
                                logger.info(f"🕒 safe_datetime: 將API時間解釋為UTC → 原始: '{value}' 結果: {parsed_dt}")
                            
                            return parsed_dt
                        except ValueError:
                            continue
                    from dateutil import parser
                    parsed_dt = parser.parse(value)
                    logger.debug(f"🕒 safe_datetime: dateutil解析 '{value}' → {parsed_dt}")
                    
                    # 🔧 時區修復：dateutil 解析結果也需要檢查時區
                    if parsed_dt.tzinfo is None:
                        from datetime import timezone
                        parsed_dt = parsed_dt.replace(tzinfo=timezone.utc)
                        logger.info(f"🕒 safe_datetime: dateutil結果設置為UTC時區 → 原始: '{value}' 結果: {parsed_dt}")
                    
                    return parsed_dt
                logger.warning(f"🕒 safe_datetime: 不支持的類型 {type(value)}: {value}")
                return None
            except (ValueError, TypeError, ImportError) as e:
                logger.error(f"🕒 safe_datetime: 解析失敗 '{value}': {e}")
                return None
        
        # 準備批量插入SQL
        insert_sql = """
        INSERT INTO conversions (
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
        
        successful_ids = []
        failed_count = 0
        total_batches = (len(conversions) + batch_size - 1) // batch_size
        
        try:
            async with self.pool.acquire() as conn:
                # 準備語句以提高性能
                prepared_stmt = await conn.prepare(insert_sql)
                
                # 分批處理
                for batch_idx in range(total_batches):
                    start_idx = batch_idx * batch_size
                    end_idx = min(start_idx + batch_size, len(conversions))
                    batch_data = conversions[start_idx:end_idx]
                    
                    logger.info(f"📦 處理批次 {batch_idx + 1}/{total_batches}: {len(batch_data)} 條記錄")
                    
                    # 準備批次數據
                    batch_params = []
                    for idx, conversion in enumerate(batch_data):
                        try:
                            # 詳細日誌：記錄第一條和最後一條記錄的 datetime_conversion
                            if idx == 0 or idx == len(batch_data) - 1:
                                logger.info(f"🔍 記錄 {start_idx + idx + 1}: conversion_id={conversion.get('conversion_id')}, datetime_conversion='{conversion.get('datetime_conversion')}'")
                            
                            params = [
                                # 核心分類字段
                                safe_str(conversion.get('platform')),
                                safe_str(conversion.get('partner')),
                                safe_str(conversion.get('source')),
                                
                                # 核心轉化字段
                                safe_str(conversion.get('conversion_id')),
                                safe_str(conversion.get('offer_id')),
                                safe_str(conversion.get('offer_name')),
                                safe_str(conversion.get('order_id')),
                                
                                # 時間字段
                                safe_datetime(conversion.get('datetime_conversion')),
                                safe_datetime(conversion.get('datetime_conversion_updated')),
                                safe_datetime(conversion.get('click_time')),
                                
                                # 完整金額字段
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
                                
                                # 貨幣字段
                                safe_str(conversion.get('currency')),
                                safe_str(conversion.get('conversion_currency')),
                                
                                # 廣告主參數
                                safe_str(conversion.get('adv_sub')),
                                safe_str(conversion.get('adv_sub1')),
                                safe_str(conversion.get('adv_sub2')),
                                safe_str(conversion.get('adv_sub3')),
                                safe_str(conversion.get('adv_sub4')),
                                safe_str(conversion.get('adv_sub5')),
                                
                                # 發布商參數
                                safe_str(conversion.get('aff_sub')),
                                safe_str(conversion.get('aff_sub1')),
                                safe_str(conversion.get('aff_sub2')),
                                safe_str(conversion.get('aff_sub3')),
                                safe_str(conversion.get('aff_sub4')),
                                safe_str(conversion.get('aff_sub5')),
                                
                                # 狀態字段
                                safe_str(conversion.get('conversion_status')),
                                safe_str(conversion.get('offer_status')),
                                
                                # 業務字段
                                safe_str(conversion.get('merchant_id')),
                                safe_str(conversion.get('affiliate_remarks')),
                                safe_str(conversion.get('click_id')),
                                
                                # 佣金字段
                                safe_float(conversion.get('commission_rate')),
                                safe_float(conversion.get('avg_commission_rate')),
                                
                                # 系統字段
                                safe_int(conversion.get('tenant_id', 1)),
                                json.dumps(conversion.get('raw_data', conversion)),
                                safe_datetime(conversion.get('datetime_conversion') or datetime.now()),
                                datetime.now()
                            ]
                            batch_params.append(params)
                        except Exception as e:
                            failed_count += 1
                            logger.error(f"❌ 準備第{start_idx + len(batch_params) + 1}條數據失敗: {e}")
                            continue
                    
                    if not batch_params:
                        logger.warning(f"⚠️ 批次 {batch_idx + 1} 無有效數據，跳過")
                        continue
                    
                    # 執行批量插入
                    try:
                        batch_start_time = datetime.now()
                    
                        # 使用executemany進行真正的批量插入
                        batch_results = await prepared_stmt.fetchmany(batch_params)
                        
                        batch_end_time = datetime.now()
                        batch_duration = (batch_end_time - batch_start_time).total_seconds()
                        
                        # 收集成功的ID
                        batch_ids = [result['id'] for result in batch_results if result and 'id' in result]
                        successful_ids.extend(batch_ids)
                        
                        records_per_second = len(batch_ids) / batch_duration if batch_duration > 0 else 0
                        
                        logger.info(f"✅ 批次 {batch_idx + 1} 完成: {len(batch_ids)}/{len(batch_params)} 條成功 "
                                  f"({batch_duration:.2f}秒, {records_per_second:.1f} 條/秒)")
                        
                    except Exception as e:
                        failed_count += len(batch_params)
                        logger.error(f"❌ 批次 {batch_idx + 1} 插入失敗: {e}")
                        continue
                
                # 最終統計
                total_processed = len(conversions)
                success_count = len(successful_ids)
                success_rate = (success_count / total_processed) * 100 if total_processed > 0 else 0
                
                logger.info(f"🎉 高性能批量插入完成!")
                logger.info(f"   總記錄數: {total_processed:,}")
                logger.info(f"   成功插入: {success_count:,} ({success_rate:.1f}%)")
                logger.info(f"   插入失敗: {failed_count:,}")
                logger.info(f"   批次數量: {total_batches}")
                
                return successful_ids
            
        except Exception as e:
            logger.error(f"❌ 高性能批量插入失敗: {str(e)}")
            return successful_ids  # 返回已成功的ID

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
                # 基礎統計查詢
                base_query = """
                SELECT 
                    COUNT(*) as total_conversions,
                    COUNT(DISTINCT platform) as total_platforms,
                    COUNT(DISTINCT partner) as total_partners,
                    COUNT(DISTINCT source) as total_sources,
                    SUM(COALESCE(usd_sale_amount, 0)) as total_usd_amount,
                    SUM(COALESCE(usd_payout, 0)) as total_usd_payout,
                    MIN(created_at) as earliest_conversion,
                    MAX(created_at) as latest_conversion
                FROM conversions
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
                platform_query = """
                SELECT 
                    platform,
                    COUNT(*) as conversion_count,
                    SUM(COALESCE(usd_sale_amount, 0)) as total_amount,
                    COUNT(DISTINCT partner) as partner_count,
                    COUNT(DISTINCT source) as source_count
                FROM conversions
                WHERE created_at >= $1
                """
                if conditions:
                    platform_query += " " + " ".join(conditions)
                platform_query += " GROUP BY platform ORDER BY conversion_count DESC"
                
                platform_stats = await conn.fetch(platform_query, *params)
                
                # Partner分析
                partner_query = """
                SELECT 
                    partner,
                    platform,
                    COUNT(*) as conversion_count,
                    SUM(COALESCE(usd_sale_amount, 0)) as total_amount,
                    COUNT(DISTINCT source) as source_count,
                    ARRAY_AGG(DISTINCT source ORDER BY source) as sources_list
                FROM conversions
                WHERE created_at >= $1
                """
                if conditions:
                    partner_query += " " + " ".join(conditions)
                partner_query += " GROUP BY partner, platform ORDER BY conversion_count DESC"
                
                partner_stats = await conn.fetch(partner_query, *params)
                
                # Source分析 
                source_query = """
                SELECT 
                    source,
                    partner,
                    platform,
                    COUNT(*) as conversion_count,
                    SUM(COALESCE(usd_sale_amount, 0)) as total_amount
                FROM conversions
                WHERE created_at >= $1 AND source IS NOT NULL AND source != ''
                """
                if conditions:
                    source_query += " " + " ".join(conditions)
                source_query += " GROUP BY source, partner, platform ORDER BY conversion_count DESC LIMIT 20"
                
                source_stats = await conn.fetch(source_query, *params)
                
                # 組裝結果
                result = {
                    'query_info': {
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
                
                logger.info(f"📊 獲取增強統計信息成功: {result['basic_stats'].get('total_conversions', 0)} 條轉化")
                return result
                
        except Exception as e:
            logger.error(f"❌ 獲取增強統計信息失敗: {str(e)}")
            return {
                'error': str(e),
                'query_info': {
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
                
                # 檢查表結構
                conversions_count = await conn.fetchval("SELECT COUNT(*) FROM conversions")
                
                # 檢查新字段是否存在
                schema_check = await conn.fetch("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'conversions' 
                AND column_name IN ('platform', 'partner', 'source')
                """)
                
                enhanced_fields = [row['column_name'] for row in schema_check]
                
                # 最近24小時統計
                recent_stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as recent_conversions,
                    COUNT(DISTINCT platform) as platforms_count,
                    COUNT(DISTINCT partner) as partners_count,
                    COUNT(DISTINCT source) as sources_count
                FROM conversions 
                WHERE created_at >= NOW() - INTERVAL '24 hours'
                """)
                
                return {
                    'status': 'healthy',
                    'database_connection': 'ok',
                    'conversions_count': conversions_count,
                    'enhanced_fields_available': enhanced_fields,
                    'enhanced_schema': len(enhanced_fields) == 3,  # platform, partner, source
                    'recent_stats': dict(recent_stats) if recent_stats else {},
                    'check_time': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"❌ 健康檢查失敗: {str(e)}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'check_time': datetime.now().isoformat()
            }

# 保持向後兼容性的別名，但推薦使用增強版本
DMPDatabaseManager = EnhancedDMPDatabaseManager 