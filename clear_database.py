#!/usr/bin/env python3
"""
清除 Google Cloud SQL 資料庫所有資料
"""

import asyncio
import asyncpg
import logging
from datetime import datetime

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 資料庫配置
DB_CONFIG = {
    'host': '34.124.206.16',
    'port': 5432,
    'database': 'postback_db',
    'user': 'postback_admin',
    'password': 'ByteC2024PostBack_CloudSQL'
}

async def get_table_counts(conn):
    """獲取所有表的記錄數量"""
    tables_info = {}
    
    # 獲取所有表名
    tables_query = """
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_type = 'BASE TABLE'
    ORDER BY table_name;
    """
    
    tables = await conn.fetch(tables_query)
    
    for table in tables:
        table_name = table['table_name']
        try:
            count_query = f"SELECT COUNT(*) FROM {table_name};"
            result = await conn.fetchval(count_query)
            tables_info[table_name] = result
            logger.info(f"表 {table_name}: {result:,} 條記錄")
        except Exception as e:
            logger.warning(f"無法統計表 {table_name}: {e}")
            tables_info[table_name] = "錯誤"
    
    return tables_info

async def clear_database():
    """清除資料庫所有資料"""
    conn = None
    try:
        logger.info("🚀 開始清除資料庫操作")
        logger.info("=" * 60)
        
        # 連接資料庫
        logger.info("📡 正在連接資料庫...")
        conn = await asyncpg.connect(**DB_CONFIG)
        logger.info("✅ 資料庫連接成功")
        
        # 統計清除前的資料
        logger.info("\n📊 清除前的資料統計:")
        logger.info("-" * 40)
        before_counts = await get_table_counts(conn)
        total_before = sum(count for count in before_counts.values() if isinstance(count, int))
        logger.info(f"\n📈 清除前總記錄數: {total_before:,}")
        
        if total_before == 0:
            logger.info("ℹ️ 資料庫已經是空的，無需清除")
            return
        
        # 清除資料
        logger.info("\n🗑️ 開始清除資料...")
        logger.info("-" * 40)
        
        # 定義要清除的表（按依賴關係排序）
        tables_to_clear = [
            'aff_sub_partner_mapping',
            'conversions', 
            'sources',
            'business_partners',
            'partners',
            'platforms'
        ]
        
        cleared_counts = {}
        
        for table_name in tables_to_clear:
            if table_name in before_counts and before_counts[table_name] > 0:
                try:
                    # 刪除資料
                    delete_query = f"DELETE FROM {table_name};"
                    result = await conn.execute(delete_query)
                    
                    # 重置序列（如果存在）
                    try:
                        reset_seq_query = f"ALTER SEQUENCE {table_name}_id_seq RESTART WITH 1;"
                        await conn.execute(reset_seq_query)
                        logger.info(f"✅ 清除表 {table_name}: {before_counts[table_name]:,} 條記錄（已重置ID序列）")
                    except:
                        logger.info(f"✅ 清除表 {table_name}: {before_counts[table_name]:,} 條記錄")
                    
                    cleared_counts[table_name] = before_counts[table_name]
                    
                except Exception as e:
                    logger.error(f"❌ 清除表 {table_name} 失敗: {e}")
            else:
                logger.info(f"⏭️ 跳過表 {table_name}: 無記錄或不存在")
        
        # 確認清除結果
        logger.info("\n🔍 驗證清除結果...")
        logger.info("-" * 40)
        after_counts = await get_table_counts(conn)
        total_after = sum(count for count in after_counts.values() if isinstance(count, int))
        
        # 統計結果
        total_cleared = sum(cleared_counts.values())
        
        logger.info("\n📊 清除結果統計:")
        logger.info("=" * 60)
        logger.info(f"📉 清除前總記錄數: {total_before:,}")
        logger.info(f"📋 清除後總記錄數: {total_after:,}")
        logger.info(f"🗑️ 成功清除記錄數: {total_cleared:,}")
        
        if total_after == 0:
            logger.info("✅ 資料庫清除完成！所有資料已被刪除")
        else:
            logger.warning(f"⚠️ 注意：仍有 {total_after:,} 條記錄未被清除")
        
        # 顯示詳細的清除結果
        if cleared_counts:
            logger.info("\n📋 各表清除詳情:")
            logger.info("-" * 40)
            for table_name, count in cleared_counts.items():
                logger.info(f"  • {table_name}: {count:,} 條記錄")
        
        logger.info("\n🎉 資料庫清除操作完成！")
        
    except Exception as e:
        logger.error(f"❌ 清除資料庫失敗: {e}")
        raise
    finally:
        if conn:
            await conn.close()
            logger.info("🔐 資料庫連接已關閉")

if __name__ == "__main__":
    # 運行清除操作
    asyncio.run(clear_database()) 