#!/usr/bin/env python3
"""
數據庫清除腳本 - 執行完全清除操作
清除所有轉化記錄並重置ID序列
"""

import asyncio
import asyncpg
from datetime import datetime

# 數據庫配置
DB_CONFIG = {
    'host': '34.124.206.16',
    'port': 5432,
    'database': 'postback_db',
    'user': 'postback_admin',
    'password': 'ByteC2024PostBack_CloudSQL'
}

print("🗑️  開始執行數據庫完全清除操作")
print("=" * 60)
print(f"⏰ 執行時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)

async def clear_database_completely():
    """完全清除數據庫"""
    
    try:
        conn = await asyncpg.connect(**DB_CONFIG)
        print("✅ 數據庫連接成功")
        
        # 步驟1: 檢查清除前的數據量
        print("\n📊 清除前數據檢查:")
        tables_to_check = [
            'conversions', 'business_partners', 'partners', 
            'platforms', 'sources', 'aff_sub_partner_mapping'
        ]
        
        total_records_before = 0
        for table in tables_to_check:
            try:
                count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                print(f"   - {table}: {count:,} 條記錄")
                total_records_before += count
            except Exception as e:
                print(f"   - {table}: 表不存在或查詢失敗 ({e})")
        
        print(f"\n📋 清除前總記錄數: {total_records_before:,}")
        
        if total_records_before == 0:
            print("⚠️  數據庫已經是空的，無需清除")
            await conn.close()
            return
        
        # 步驟2: 開始清除操作
        print(f"\n🚀 開始清除 {total_records_before:,} 條記錄...")
        
        # 清除主要數據表（按依賴順序）
        tables_to_clear = [
            'conversions',
            'aff_sub_partner_mapping', 
            'sources',
            'business_partners',
            'partners',
            'platforms'
        ]
        
        total_deleted = 0
        
        for table in tables_to_clear:
            try:
                # 獲取刪除前的記錄數
                count_before = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                
                if count_before > 0:
                    print(f"   🗑️  清除 {table} 表...")
                    
                    # 刪除所有記錄
                    result = await conn.execute(f"DELETE FROM {table}")
                    deleted_count = int(result.split()[-1]) if result.split()[-1].isdigit() else count_before
                    
                    print(f"      ✅ 已刪除 {deleted_count:,} 條記錄")
                    total_deleted += deleted_count
                else:
                    print(f"   ⏭️  {table} 表已經是空的，跳過")
                    
            except Exception as e:
                print(f"   ❌ 清除 {table} 表失敗: {e}")
        
        # 步驟3: 重置ID序列
        print(f"\n🔄 重置ID序列...")
        
        sequence_reset_sqls = [
            "ALTER SEQUENCE conversions_id_seq RESTART WITH 1",
            "ALTER SEQUENCE business_partners_id_seq RESTART WITH 1", 
            "ALTER SEQUENCE partners_id_seq RESTART WITH 1",
            "ALTER SEQUENCE platforms_id_seq RESTART WITH 1",
            "ALTER SEQUENCE sources_id_seq RESTART WITH 1",
            "ALTER SEQUENCE aff_sub_partner_mapping_id_seq RESTART WITH 1"
        ]
        
        for sql in sequence_reset_sqls:
            try:
                await conn.execute(sql)
                table_name = sql.split('_')[0]
                print(f"   ✅ {table_name} ID序列已重置")
            except Exception as e:
                print(f"   ⚠️  ID序列重置失敗: {sql} ({e})")
        
        # 步驟4: 驗證清除結果
        print(f"\n🔍 清除後數據驗證:")
        
        total_records_after = 0
        for table in tables_to_check:
            try:
                count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                status = "✅" if count == 0 else "⚠️ "
                print(f"   {status} {table}: {count:,} 條記錄")
                total_records_after += count
            except Exception as e:
                print(f"   ❌ {table}: 驗證失敗 ({e})")
        
        # 步驟5: 清除總結
        print(f"\n" + "=" * 60)
        print(f"🎉 數據庫清除操作完成!")
        print(f"=" * 60)
        print(f"📊 清除統計:")
        print(f"   - 清除前總記錄數: {total_records_before:,}")
        print(f"   - 實際刪除記錄數: {total_deleted:,}")
        print(f"   - 清除後總記錄數: {total_records_after:,}")
        print(f"   - 清除成功率: {((total_records_before - total_records_after) / max(total_records_before, 1) * 100):.1f}%")
        
        if total_records_after == 0:
            print(f"✅ 數據庫已完全清空，所有ID序列已重置")
        else:
            print(f"⚠️  還有 {total_records_after} 條記錄未清除")
        
        print(f"⏰ 清除完成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        await conn.close()
        print("✅ 數據庫連接已關閉")
        
    except Exception as e:
        print(f"❌ 數據庫清除操作失敗: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """主函數"""
    await clear_database_completely()

if __name__ == "__main__":
    asyncio.run(main()) 