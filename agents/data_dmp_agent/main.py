#!/usr/bin/env python3
"""
DMP-Agent主程序
整合API數據獲取、數據處理和Google Cloud SQL存儲
支持 --days-ago 和 --platform 參數
"""

import sys
import os
import argparse
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# 添加父目錄到Python路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from .database_manager import EnhancedDMPDatabaseManager
from .api_data_fetcher import APIDataFetcher
from .api_config_manager import APIConfigManager

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('dmp_agent.log')
    ]
)
logger = logging.getLogger(__name__)

class DMPAgent:
    """DMP代理主類"""
    
    def __init__(self):
        self.db_manager = EnhancedDMPDatabaseManager()
        self.api_fetcher = APIDataFetcher()
        self.config_manager = APIConfigManager()
        self.stats = {
            'total_fetched': 0,
            'total_processed': 0,
            'total_stored': 0,
            'errors': []
        }
    
    async def initialize(self):
        """初始化DMP代理"""
        logger.info("🚀 正在初始化DMP-Agent...")
        
        try:
            # 初始化數據庫連接
            await self.db_manager.init_pool()
            
            # 檢查數據庫健康狀態
            health = await self.db_manager.health_check()
            if health.get('status') != 'healthy':
                raise Exception(f"數據庫不健康: {health.get('error', 'Unknown')}")
            
            logger.info("✅ DMP-Agent初始化成功")
            logger.info(f"   - 數據庫連接: {health.get('conversions_count', 0)} 條轉化記錄")
            logger.info(f"   - 合作夥伴: {health.get('partners_count', 0)} 個")
            logger.info(f"   - 平台: {health.get('platforms_count', 0)} 個")
            
        except Exception as e:
            logger.error(f"❌ DMP-Agent初始化失敗: {e}")
            raise
    
    async def cleanup(self):
        """清理資源"""
        logger.info("🧹 正在清理DMP-Agent資源...")
        await self.db_manager.close_pool()
        logger.info("✅ DMP-Agent資源清理完成")
    
    async def process_platform_data(self, platform: str, days_ago: int = 1) -> Dict[str, Any]:
        """處理特定平台的數據"""
        logger.info(f"🔄 開始處理平台數據: {platform} (days_ago={days_ago})")
        
        try:
            # 步驟1: 驗證平台配置
            if not self.config_manager.validate_config(platform):
                error_msg = f"平台配置無效: {platform}"
                logger.error(f"❌ {error_msg}")
                self.stats['errors'].append(error_msg)
                return {'success': False, 'error': error_msg}
            
            # 步驟2: 從API獲取轉化數據
            logger.info(f"📥 正在從API獲取轉化數據...")
            conversions = await self.api_fetcher.fetch_conversions(platform, days_ago)
            
            if not conversions:
                logger.warning(f"⚠️ 沒有獲取到轉化數據: {platform}")
                return {
                    'success': True,
                    'platform': platform,
                    'days_ago': days_ago,
                    'fetched_count': 0,
                    'stored_count': 0,
                    'message': '沒有新的轉化數據'
                }
            
            self.stats['total_fetched'] += len(conversions)
            logger.info(f"✅ 成功獲取 {len(conversions)} 條轉化數據")
            
            # 步驟3: 存儲到數據庫（使用高性能優化批量插入）
            logger.info(f"💾 正在存儲轉化數據到Google Cloud SQL（高性能模式）...")
            stored_ids = await self.db_manager.insert_conversion_batch_optimized(conversions, platform)
            
            self.stats['total_stored'] += len(stored_ids)
            logger.info(f"✅ 成功存儲 {len(stored_ids)} 條轉化數據")
            
            # 步驟4: 生成結果統計
            result = {
                'success': True,
                'platform': platform,
                'days_ago': days_ago,
                'fetched_count': len(conversions),
                'stored_count': len(stored_ids),
                'date_range': self.config_manager.get_date_range(days_ago),
                'processing_time': datetime.now().isoformat()
            }
            
            # 計算金額統計
            total_amount = sum(conv.get('usd_sale_amount', 0) for conv in conversions)
            total_payout = sum(conv.get('usd_payout', 0) for conv in conversions)
            
            result['amount_stats'] = {
                'total_sale_amount': total_amount,
                'total_payout': total_payout,
                'average_sale_amount': total_amount / len(conversions) if conversions else 0
            }
            
            logger.info(f"✅ 平台數據處理完成: {platform}")
            logger.info(f"   - 獲取: {len(conversions)} 條記錄")
            logger.info(f"   - 存儲: {len(stored_ids)} 條記錄")
            logger.info(f"   - 總金額: ${total_amount:,.2f} USD")
            
            return result
            
        except Exception as e:
            error_msg = f"處理平台數據失敗: {platform} - {str(e)}"
            logger.error(f"❌ {error_msg}")
            self.stats['errors'].append(error_msg)
            return {'success': False, 'platform': platform, 'error': error_msg}
    
    async def get_platform_stats(self, platform: str = None, days_ago: int = 1) -> Dict[str, Any]:
        """獲取平台統計信息"""
        logger.info(f"📊 獲取平台統計: {platform or 'ALL'} (days_ago={days_ago})")
        
        try:
            stats = await self.db_manager.get_conversion_stats(platform, days_ago)
            return stats
        except Exception as e:
            logger.error(f"❌ 獲取平台統計失敗: {e}")
            return {'error': str(e)}
    
    def print_final_summary(self):
        """打印最終統計摘要"""
        logger.info("📋 DMP-Agent執行摘要:")
        logger.info(f"   - 總獲取數量: {self.stats['total_fetched']} 條記錄")
        logger.info(f"   - 總存儲數量: {self.stats['total_stored']} 條記錄")
        
        if self.stats['errors']:
            logger.error(f"   - 錯誤數量: {len(self.stats['errors'])}")
            for error in self.stats['errors']:
                logger.error(f"     * {error}")
        else:
            logger.info("   - 沒有錯誤")
        
        logger.info("=" * 60)

async def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='DMP-Agent: 數據管理平台代理')
    parser.add_argument('--days-ago', type=int, default=1, 
                       help='獲取多少天前的數據 (默認: 1)')
    parser.add_argument('--platform', type=str, default='IAByteC',
                       help='API平台名稱 (默認: IAByteC)')
    parser.add_argument('--test-connection', action='store_true',
                       help='測試平台連接')
    parser.add_argument('--list-platforms', action='store_true',
                       help='列出可用平台')
    parser.add_argument('--stats-only', action='store_true',
                       help='只顯示統計信息，不獲取新數據')
    
    args = parser.parse_args()
    
    # 創建DMP代理實例
    agent = DMPAgent()
    
    try:
        # 初始化
        await agent.initialize()
        
        # 處理不同的命令
        if args.list_platforms:
            platforms = agent.api_fetcher.get_available_platforms()
            logger.info(f"可用平台: {platforms}")
            return
        
        if args.test_connection:
            result = await agent.api_fetcher.test_platform_connection(args.platform)
            if result:
                logger.info(f"✅ 平台連接測試成功: {args.platform}")
            else:
                logger.error(f"❌ 平台連接測試失敗: {args.platform}")
            return
        
        if args.stats_only:
            stats = await agent.get_platform_stats(args.platform, args.days_ago)
            logger.info(f"📊 平台統計: {stats}")
            return
        
        # 主要處理流程
        logger.info("🚀 開始DMP-Agent數據處理流程")
        logger.info(f"   - 平台: {args.platform}")
        logger.info(f"   - 天數: {args.days_ago} 天前")
        
        # 處理平台數據
        result = await agent.process_platform_data(args.platform, args.days_ago)
        
        # 打印結果
        if result['success']:
            logger.info("✅ 數據處理成功完成")
            logger.info(f"   - 獲取記錄: {result['fetched_count']} 條")
            logger.info(f"   - 存儲記錄: {result['stored_count']} 條")
            
            if 'amount_stats' in result:
                amount_stats = result['amount_stats']
                logger.info(f"   - 總銷售金額: ${amount_stats['total_sale_amount']:,.2f} USD")
                logger.info(f"   - 總佣金金額: ${amount_stats['total_payout']:,.2f} USD")
                logger.info(f"   - 平均銷售金額: ${amount_stats['average_sale_amount']:,.2f} USD")
        else:
            logger.error("❌ 數據處理失敗")
            logger.error(f"   - 錯誤: {result.get('error', 'Unknown')}")
        
        # 打印最終摘要
        agent.print_final_summary()
        
    except Exception as e:
        logger.error(f"❌ DMP-Agent執行失敗: {e}")
        raise
    finally:
        # 清理資源
        await agent.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 