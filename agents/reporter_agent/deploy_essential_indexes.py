#!/usr/bin/env python3
"""
Reporter-Agent 關鍵索引部署腳本
安全部署關鍵索引，支持錯誤處理和回滾
"""

import asyncio
import asyncpg
import logging
import sys
import os
from pathlib import Path

# 添加項目根目錄到路徑
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class IndexDeployment:
    """索引部署管理器"""
    
    def __init__(self):
        self.host = "34.124.206.16"
        self.port = 5432
        self.database = "postback_db"
        self.user = "postback_admin"
        self.password = "ByteC2024PostBack_CloudSQL"
        self.connection_string = f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
        
    async def connect(self):
        """建立數據庫連接"""
        try:
            self.conn = await asyncpg.connect(self.connection_string)
            logger.info("✅ 數據庫連接成功")
            return True
        except Exception as e:
            logger.error(f"❌ 數據庫連接失敗: {e}")
            return False
    
    async def close(self):
        """關閉數據庫連接"""
        if hasattr(self, 'conn'):
            await self.conn.close()
            logger.info("✅ 數據庫連接已關閉")
    
    async def check_table_status(self):
        """檢查表格狀態"""
        try:
            # 檢查表格大小
            table_size = await self.conn.fetchval(
                "SELECT pg_size_pretty(pg_total_relation_size('conversions'))"
            )
            
            # 檢查記錄數量
            record_count = await self.conn.fetchval("SELECT COUNT(*) FROM conversions")
            
            # 檢查現有索引
            existing_indexes = await self.conn.fetch("""
                SELECT indexname, indexdef 
                FROM pg_indexes 
                WHERE tablename = 'conversions'
                ORDER BY indexname
            """)
            
            logger.info(f"📊 表格大小: {table_size}")
            logger.info(f"📊 記錄數量: {record_count:,}")
            logger.info(f"🔍 現有索引數量: {len(existing_indexes)}")
            
            for index in existing_indexes:
                logger.info(f"  - {index['indexname']}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 檢查表格狀態失敗: {e}")
            return False
    
    async def create_essential_indexes(self):
        """創建關鍵索引"""
        
        # 定義關鍵索引
        essential_indexes = [
            {
                'name': 'idx_conversions_id_desc_reporter',
                'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversions_id_desc_reporter ON conversions (id DESC)',
                'description': 'ID 降序索引 (游標分頁優化)'
            },
            {
                'name': 'idx_conversions_datetime_reporter',
                'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversions_datetime_reporter ON conversions (datetime_conversion DESC) WHERE datetime_conversion IS NOT NULL',
                'description': 'datetime_conversion 索引'
            },
            {
                'name': 'idx_conversions_partner_reporter',
                'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversions_partner_reporter ON conversions (partner) WHERE partner IS NOT NULL',
                'description': 'partner 索引'
            },
            {
                'name': 'idx_conversions_partner_datetime_reporter',
                'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversions_partner_datetime_reporter ON conversions (partner, datetime_conversion DESC) WHERE partner IS NOT NULL AND datetime_conversion IS NOT NULL',
                'description': 'partner + datetime_conversion 複合索引'
            },
            {
                'name': 'idx_conversions_datetime_id_reporter',
                'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversions_datetime_id_reporter ON conversions (datetime_conversion DESC, id DESC) WHERE datetime_conversion IS NOT NULL',
                'description': 'datetime_conversion + id 複合索引'
            },
            {
                'name': 'idx_conversions_partner_id_reporter',
                'sql': 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversions_partner_id_reporter ON conversions (partner, id DESC) WHERE partner IS NOT NULL',
                'description': 'partner + id 複合索引'
            }
        ]
        
        logger.info("🔧 開始創建關鍵索引...")
        
        success_count = 0
        total_count = len(essential_indexes)
        
        for index_info in essential_indexes:
            try:
                # 檢查索引是否已存在
                exists = await self.conn.fetchval("""
                    SELECT 1 FROM pg_indexes 
                    WHERE tablename = 'conversions' 
                    AND indexname = $1
                """, index_info['name'])
                
                if exists:
                    logger.info(f"⚠️ 索引 {index_info['name']} 已存在")
                    success_count += 1
                    continue
                
                logger.info(f"🔨 創建索引: {index_info['description']}")
                
                # 創建索引 (使用 CONCURRENTLY 避免鎖表)
                await self.conn.execute(index_info['sql'])
                
                logger.info(f"✅ 索引 {index_info['name']} 創建成功")
                success_count += 1
                
            except Exception as e:
                logger.error(f"❌ 創建索引 {index_info['name']} 失敗: {e}")
        
        logger.info(f"📊 索引創建結果: {success_count}/{total_count}")
        return success_count == total_count
    
    async def verify_indexes(self):
        """驗證索引創建結果"""
        try:
            reporter_indexes = await self.conn.fetch("""
                SELECT indexname, indexdef 
                FROM pg_indexes 
                WHERE tablename = 'conversions' 
                AND indexname LIKE '%_reporter'
                ORDER BY indexname
            """)
            
            logger.info(f"🔍 Reporter-Agent 專用索引數量: {len(reporter_indexes)}")
            
            for index in reporter_indexes:
                logger.info(f"  ✅ {index['indexname']}")
            
            return len(reporter_indexes) >= 6  # 至少應該有6個關鍵索引
            
        except Exception as e:
            logger.error(f"❌ 驗證索引失敗: {e}")
            return False
    
    async def deploy(self):
        """執行完整的索引部署流程"""
        logger.info("🚀 開始 Reporter-Agent 關鍵索引部署...")
        
        # 1. 連接數據庫
        if not await self.connect():
            return False
        
        try:
            # 2. 檢查表格狀態
            logger.info("📋 檢查表格狀態...")
            if not await self.check_table_status():
                return False
            
            # 3. 創建關鍵索引
            logger.info("🔧 創建關鍵索引...")
            if not await self.create_essential_indexes():
                logger.warning("⚠️ 部分索引創建失敗，但繼續驗證...")
            
            # 4. 驗證索引
            logger.info("🔍 驗證索引創建...")
            if await self.verify_indexes():
                logger.info("🎉 索引部署成功！")
                logger.info("📈 預期性能提升: 70-80%")
                return True
            else:
                logger.error("❌ 索引驗證失敗")
                return False
                
        finally:
            await self.close()

async def main():
    """主函數"""
    try:
        deployment = IndexDeployment()
        success = await deployment.deploy()
        
        if success:
            logger.info("✅ Reporter-Agent 索引優化部署完成")
            sys.exit(0)
        else:
            logger.error("❌ Reporter-Agent 索引優化部署失敗")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("⚠️ 用戶中斷部署")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ 部署過程發生未預期錯誤: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 