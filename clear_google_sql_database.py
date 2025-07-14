#!/usr/bin/env python3
"""
Google Cloud SQL 資料庫清理腳本
⚠️ 警告：此腳本將完全清除資料庫中的所有數據！
"""

import asyncio
import asyncpg
import sys
import os
from datetime import datetime
from typing import Dict, List

# 資料庫配置
DB_CONFIG = {
    'host': '34.124.206.16',
    'port': 5432,
    'database': 'postback_db',
    'user': 'postback_admin',
    'password': 'ByteC2024PostBack_CloudSQL'
}

# 需要清理的表（按依賴順序排列）
TABLES_TO_CLEAR = [
    # 1. 首先清理有外鍵依賴的表
    'conversions',
    'postback_conversions', 
    'partner_conversions',
    'commission_calculations',
    'reports',
    
    # 2. 然後清理映射表
    'sources',
    
    # 3. 最後清理主表（保留基礎配置表）
    # 注意：不清理 tenants, partners, business_partners, platforms
    # 這些表包含重要的配置信息
]

# 可選：也清理配置表（需要額外確認）
CONFIG_TABLES = [
    'business_partners',
    'platforms', 
    'partners',
    'tenants'  # 最後清理，因為其他表可能依賴它
]

class DatabaseCleaner:
    """資料庫清理器"""
    
    def __init__(self):
        self.conn = None
        
    async def connect(self):
        """連接資料庫"""
        try:
            self.conn = await asyncpg.connect(**DB_CONFIG)
            print(f"✅ 成功連接到資料庫: {DB_CONFIG['host']}:{DB_CONFIG['database']}")
            return True
        except Exception as e:
            print(f"❌ 資料庫連接失敗: {e}")
            return False
            
    async def disconnect(self):
        """斷開資料庫連接"""
        if self.conn:
            await self.conn.close()
            print("✅ 資料庫連接已關閉")
    
    async def check_tables_exist(self, tables: List[str]) -> Dict[str, bool]:
        """檢查表是否存在"""
        existing_tables = {}
        
        for table in tables:
            try:
                result = await self.conn.fetch("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = $1
                );
                """, table)
                existing_tables[table] = result[0]['exists']
            except Exception as e:
                print(f"⚠️ 檢查表 {table} 時出錯: {e}")
                existing_tables[table] = False
                
        return existing_tables
    
    async def get_table_counts(self, tables: List[str]) -> Dict[str, int]:
        """獲取各表的記錄數量"""
        counts = {}
        
        for table in tables:
            try:
                result = await self.conn.fetch(f"SELECT COUNT(*) as count FROM {table};")
                counts[table] = result[0]['count']
            except Exception as e:
                print(f"⚠️ 無法獲取表 {table} 的記錄數: {e}")
                counts[table] = 0
                
        return counts
    
    async def backup_table_structure(self, output_dir: str = "backup"):
        """備份表結構"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{output_dir}/schema_backup_{timestamp}.sql"
        
        try:
            # 獲取所有表的創建語句
            tables = await self.conn.fetch("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            ORDER BY table_name;
            """)
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                f.write(f"-- Schema Backup Created: {datetime.now()}\n")
                f.write(f"-- Database: {DB_CONFIG['database']}\n\n")
                
                for table in tables:
                    table_name = table['table_name']
                    f.write(f"-- Table: {table_name}\n")
                    
                    # 獲取表結構
                    columns = await self.conn.fetch("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = $1
                    ORDER BY ordinal_position;
                    """, table_name)
                    
                    f.write(f"-- Columns for {table_name}:\n")
                    for col in columns:
                        f.write(f"--   {col['column_name']}: {col['data_type']}\n")
                    f.write("\n")
            
            print(f"✅ 表結構已備份到: {backup_file}")
            return backup_file
            
        except Exception as e:
            print(f"❌ 備份表結構失敗: {e}")
            return None
    
    async def clear_table(self, table_name: str) -> bool:
        """清理單個表"""
        try:
            # 先檢查表是否存在
            exists = await self.conn.fetch("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = $1
            );
            """, table_name)
            
            if not exists[0]['exists']:
                print(f"⚠️ 表 {table_name} 不存在，跳過")
                return True
            
            # 獲取清理前的記錄數
            count_before = await self.conn.fetch(f"SELECT COUNT(*) as count FROM {table_name};")
            before_count = count_before[0]['count']
            
            if before_count == 0:
                print(f"✅ 表 {table_name} 已經是空的")
                return True
            
            # 執行清理
            await self.conn.execute(f"TRUNCATE TABLE {table_name} CASCADE;")
            
            # 確認清理結果
            count_after = await self.conn.fetch(f"SELECT COUNT(*) as count FROM {table_name};")
            after_count = count_after[0]['count']
            
            if after_count == 0:
                print(f"✅ 表 {table_name} 清理成功 (刪除了 {before_count} 條記錄)")
                return True
            else:
                print(f"⚠️ 表 {table_name} 清理不完全 (還剩 {after_count} 條記錄)")
                return False
                
        except Exception as e:
            print(f"❌ 清理表 {table_name} 失敗: {e}")
            return False
    
    async def clear_all_data_tables(self):
        """清理所有數據表（保留配置表）"""
        print("\n🧹 開始清理數據表...")
        print("=" * 50)
        
        success_count = 0
        total_count = len(TABLES_TO_CLEAR)
        
        for table in TABLES_TO_CLEAR:
            print(f"\n📋 正在清理表: {table}")
            if await self.clear_table(table):
                success_count += 1
            else:
                print(f"❌ 表 {table} 清理失敗")
        
        print(f"\n📊 清理結果: {success_count}/{total_count} 個表清理成功")
        return success_count == total_count
    
    async def clear_config_tables(self):
        """清理配置表（需要額外確認）"""
        print("\n⚠️ 準備清理配置表...")
        print("這將刪除所有租戶、合作夥伴、平台等配置信息！")
        
        confirm = input("請輸入 'DELETE_CONFIG' 來確認清理配置表: ")
        if confirm != "DELETE_CONFIG":
            print("❌ 配置表清理已取消")
            return False
        
        print("\n🧹 開始清理配置表...")
        print("=" * 50)
        
        success_count = 0
        total_count = len(CONFIG_TABLES)
        
        for table in CONFIG_TABLES:
            print(f"\n📋 正在清理配置表: {table}")
            if await self.clear_table(table):
                success_count += 1
            else:
                print(f"❌ 配置表 {table} 清理失敗")
        
        print(f"\n📊 配置表清理結果: {success_count}/{total_count} 個表清理成功")
        return success_count == total_count

async def main():
    """主函數"""
    print("🚨 Google Cloud SQL 資料庫清理工具")
    print("=" * 50)
    print("⚠️ 警告：此操作將永久刪除資料庫中的數據！")
    print(f"📍 目標資料庫: {DB_CONFIG['host']}:{DB_CONFIG['database']}")
    print()
    
    # 第一次確認
    print("請選擇清理範圍:")
    print("1. 僅清理數據表 (保留配置表: tenants, partners, platforms 等)")
    print("2. 清理所有表 (包括配置表)")
    print("3. 取消操作")
    
    choice = input("請輸入選項 (1/2/3): ").strip()
    
    if choice == "3":
        print("❌ 操作已取消")
        return
    elif choice not in ["1", "2"]:
        print("❌ 無效選項，操作已取消")
        return
    
    # 第二次確認
    print(f"\n⚠️ 您選擇了選項 {choice}")
    if choice == "1":
        print("將清理數據表，保留配置表")
    else:
        print("將清理所有表，包括配置表")
    
    confirm = input("請輸入 'YES_DELETE_DATA' 來最終確認: ")
    if confirm != "YES_DELETE_DATA":
        print("❌ 操作已取消")
        return
    
    # 開始清理
    cleaner = DatabaseCleaner()
    
    try:
        # 連接資料庫
        if not await cleaner.connect():
            return
        
        # 檢查表存在性
        print("\n🔍 檢查資料庫表...")
        all_tables = TABLES_TO_CLEAR + CONFIG_TABLES
        existing_tables = await cleaner.check_tables_exist(all_tables)
        
        print("📋 表存在性檢查:")
        for table, exists in existing_tables.items():
            status = "✅ 存在" if exists else "❌ 不存在"
            print(f"   {table}: {status}")
        
        # 獲取記錄數量
        print("\n📊 獲取表記錄數量...")
        existing_table_names = [t for t, exists in existing_tables.items() if exists]
        table_counts = await cleaner.get_table_counts(existing_table_names)
        
        total_records = 0
        print("📋 各表記錄數量:")
        for table, count in table_counts.items():
            print(f"   {table}: {count:,} 條記錄")
            total_records += count
        
        print(f"\n📊 總記錄數: {total_records:,} 條")
        
        if total_records == 0:
            print("✅ 資料庫已經是空的，無需清理")
            return
        
        # 備份表結構
        print("\n💾 備份表結構...")
        backup_file = await cleaner.backup_table_structure()
        if backup_file:
            print(f"✅ 表結構備份完成: {backup_file}")
        
        # 執行清理
        if choice == "1":
            # 僅清理數據表
            success = await cleaner.clear_all_data_tables()
        else:
            # 清理所有表
            success1 = await cleaner.clear_all_data_tables()
            success2 = await cleaner.clear_config_tables()
            success = success1 and success2
        
        if success:
            print("\n🎉 資料庫清理完成！")
        else:
            print("\n⚠️ 資料庫清理部分完成，請檢查上述錯誤信息")
            
    except Exception as e:
        print(f"\n❌ 清理過程中發生錯誤: {e}")
    finally:
        await cleaner.disconnect()

if __name__ == "__main__":
    asyncio.run(main()) 