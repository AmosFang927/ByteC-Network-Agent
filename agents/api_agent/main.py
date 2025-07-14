#!/usr/bin/env python3
"""
Test Case 2: DMP-Agent整合測試
從API-Agent拉取數據，透過DMP-Agent存儲至Google Cloud SQL
支持 --days-ago 和 --platform 參數
"""

import sys
import os
import argparse
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# 添加項目根目錄到Python路徑
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('test_case2.log')
    ]
)
logger = logging.getLogger(__name__)

class TestCase2DMPAgent:
    """Test Case 2 DMP代理主類"""
    
    def __init__(self):
        self.stats = {
            'total_fetched': 0,
            'total_processed': 0,
            'total_stored': 0,
            'errors': []
        }
        self.db_manager = None
        self.api_fetcher = None
        self.config_manager = None
    
    async def initialize(self):
        """初始化DMP代理"""
        logger.info("🚀 正在初始化Test Case 2 DMP-Agent...")
        
        try:
            # 動態導入DMP-Agent模塊 - 使用增強版本
            from agents.data_dmp_agent.database_manager import EnhancedDMPDatabaseManager
            from agents.api_agent.api_data_fetcher import EnhancedAPIDataFetcher
            from agents.data_dmp_agent.api_config_manager import APIConfigManager
            
            self.db_manager = EnhancedDMPDatabaseManager()
            self.api_fetcher = EnhancedAPIDataFetcher()
            self.config_manager = APIConfigManager()
            
            # 初始化數據庫連接
            await self.db_manager.init_pool()
            
            # 自動更新數據庫架構
            logger.info("🔧 檢查並更新數據庫架構...")
            await self.db_manager.ensure_database_schema()
            logger.info("✅ 數據庫架構更新完成")
            
            # 檢查數據庫健康狀態
            health = await self.db_manager.health_check()
            if health.get('status') != 'healthy':
                raise Exception(f"數據庫不健康: {health.get('error', 'Unknown')}")
            
            logger.info("✅ Test Case 2 DMP-Agent初始化成功")
            logger.info(f"   - 數據庫連接: {health.get('conversions_count', 0)} 條轉化記錄")
            logger.info(f"   - 合作夥伴: {health.get('partners_count', 0)} 個")
            logger.info(f"   - 平台: {health.get('platforms_count', 0)} 個")
            
        except Exception as e:
            logger.error(f"❌ Test Case 2 DMP-Agent初始化失敗: {e}")
            raise
    
    async def cleanup(self):
        """清理資源"""
        logger.info("🧹 正在清理Test Case 2 DMP-Agent資源...")
        if self.db_manager:
            await self.db_manager.close_pool()
        logger.info("✅ Test Case 2 DMP-Agent資源清理完成")
    
    async def process_platform_data(self, platform: str, days_ago: int = 1, limit: int = None) -> Dict[str, Any]:
        """處理特定平台的數據"""
        logger.info(f"🔄 開始處理平台數據: {platform} (days_ago={days_ago}, limit={limit})")
        
        try:
            # 步驟1: 驗證平台配置
            if not self.config_manager.validate_config(platform):
                error_msg = f"平台配置無效: {platform}"
                logger.error(f"❌ {error_msg}")
                self.stats['errors'].append(error_msg)
                return {'success': False, 'error': error_msg}
            
            # 步驟2: 從API獲取轉化數據
            logger.info(f"📥 正在從API獲取轉化數據...")
            conversions = await self.api_fetcher.fetch_conversions(platform, days_ago, limit)
            
            # 保存原始 API 數據用於檢查
            if conversions:
                import json
                import os
                from datetime import datetime
                
                # 創建輸出目錄
                debug_dir = "debug_api_data"
                os.makedirs(debug_dir, exist_ok=True)
                
                # 生成文件名
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{debug_dir}/api_raw_data_{platform}_{days_ago}days_{timestamp}.json"
                
                # 保存原始數據
                raw_data = {
                    'metadata': {
                        'platform': platform,
                        'days_ago': days_ago,
                        'limit': limit,
                        'fetch_time': datetime.now().isoformat(),
                        'total_records': len(conversions)
                    },
                    'conversions': conversions
                }
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(raw_data, f, ensure_ascii=False, indent=2, default=str)
                
                logger.info(f"💾 原始API數據已保存: {filename}")
            
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
            
            # 詳細日誌：記錄第一條和最後一條記錄的 datetime_conversion
            if conversions:
                first_record = conversions[0]
                last_record = conversions[-1]
                logger.info(f"🔍 API數據檢查 - 第一條記錄: conversion_id={first_record.get('conversion_id')}, datetime_conversion='{first_record.get('datetime_conversion')}'")
                logger.info(f"🔍 API數據檢查 - 最後一條記錄: conversion_id={last_record.get('conversion_id')}, datetime_conversion='{last_record.get('datetime_conversion')}'")
            
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
            # 使用正確的字段名：API返回的是sale_amount和payout，而不是usd_sale_amount和usd_payout
            total_amount = 0
            total_payout = 0
            
            for conv in conversions:
                # 安全轉換字符串為浮點數
                try:
                    sale_amount = float(conv.get('sale_amount', 0)) if conv.get('sale_amount') else 0
                    total_amount += sale_amount
                except (ValueError, TypeError):
                    pass
                
                try:
                    payout = float(conv.get('payout', 0)) if conv.get('payout') else 0
                    total_payout += payout
                except (ValueError, TypeError):
                    pass
            
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
            stats = await self.db_manager.get_conversion_stats_enhanced(platform, None, days_ago)
            return stats
        except Exception as e:
            logger.error(f"❌ 獲取平台統計失敗: {e}")
            return {'error': str(e)}
    
    def print_final_summary(self):
        """打印最終統計摘要"""
        logger.info("📋 Test Case 2 DMP-Agent執行摘要:")
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
    parser = argparse.ArgumentParser(description='Test Case 2: DMP-Agent整合測試')
    parser.add_argument('--days-ago', type=int, default=2, 
                       help='獲取多少天前的數據 (默認: 2)')
    parser.add_argument('--start-date', type=str, default=None,
                       help='開始日期 (格式: YYYY-MM-DD，例如: 2025-07-12)')
    parser.add_argument('--end-date', type=str, default=None,
                       help='結束日期 (格式: YYYY-MM-DD，例如: 2025-07-12)')
    parser.add_argument('--platform', type=str, default='IAByteC',
                       help='API平台名稱 (默認: IAByteC)')
    parser.add_argument('--test-connection', action='store_true',
                       help='測試平台連接')
    parser.add_argument('--list-platforms', action='store_true',
                       help='列出可用平台')
    parser.add_argument('--stats-only', action='store_true',
                       help='只顯示統計信息，不獲取新數據')
    parser.add_argument('--limit', type=int, default=None,
                       help='限制獲取的總數據量 (例如: 1000)')
    
    args = parser.parse_args()
    
    # 處理日期參數
    calculated_days_ago = args.days_ago
    date_range_info = None
    
    if args.start_date or args.end_date:
        # 驗證日期格式並計算 days_ago
        try:
            if args.start_date and args.end_date:
                start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
                end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
                
                if start_date > end_date:
                    logger.error("❌ 開始日期不能晚於結束日期")
                    return
                
                # 計算距離今天的天數（使用開始日期）
                today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                calculated_days_ago = (today - start_date).days
                
                date_range_info = {
                    'start_date': args.start_date,
                    'end_date': args.end_date,
                    'calculated_days_ago': calculated_days_ago
                }
                
                logger.info(f"📅 使用日期範圍: {args.start_date} 到 {args.end_date}")
                logger.info(f"📅 計算得出 days_ago: {calculated_days_ago}")
                
            elif args.start_date:
                start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
                today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                calculated_days_ago = (today - start_date).days
                
                date_range_info = {
                    'start_date': args.start_date,
                    'end_date': args.start_date,  # 單日查詢
                    'calculated_days_ago': calculated_days_ago
                }
                
                logger.info(f"📅 使用單日查詢: {args.start_date}")
                logger.info(f"📅 計算得出 days_ago: {calculated_days_ago}")
                
            else:
                logger.error("❌ 如果使用日期參數，必須至少提供 --start-date")
                return
                
        except ValueError as e:
            logger.error(f"❌ 日期格式錯誤: {e}")
            logger.error("請使用格式: YYYY-MM-DD (例如: 2025-07-12)")
            return
    
    # 創建Test Case 2 DMP代理實例
    agent = TestCase2DMPAgent()
    
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
            stats = await agent.get_platform_stats(args.platform, calculated_days_ago)
            logger.info("📊 平台統計:")
            logger.info(f"   - 平台: {stats.get('platform', 'ALL')}")
            logger.info(f"   - 總轉化數量: {stats.get('total_count', 0)} 條")
            logger.info(f"   - 總銷售金額: ${stats.get('total_amount', 0):,.2f} USD")
            logger.info(f"   - 總佣金金額: ${stats.get('total_payout', 0):,.2f} USD")
            logger.info(f"   - 平均銷售金額: ${stats.get('avg_amount', 0):,.2f} USD")
            logger.info(f"   - 日期範圍: {stats.get('date_range', 'N/A')}")
            return
        
        # 主要處理流程
        logger.info("🚀 開始Test Case 2 DMP-Agent數據處理流程")
        logger.info(f"   - 平台: {args.platform}")
        if date_range_info:
            logger.info(f"   - 日期範圍: {date_range_info['start_date']} 到 {date_range_info['end_date']}")
            logger.info(f"   - 對應天數: {calculated_days_ago} 天前")
        else:
            logger.info(f"   - 天數: {calculated_days_ago} 天前")
        if args.limit:
            logger.info(f"   - 限制: {args.limit} 條記錄")
        
        # 處理平台數據
        result = await agent.process_platform_data(args.platform, calculated_days_ago, args.limit)
        
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
        logger.error(f"❌ Test Case 2 DMP-Agent執行失敗: {e}")
        raise
    finally:
        # 清理資源
        await agent.cleanup()

if __name__ == "__main__":
    print("=" * 80)
    print("🧪 Test Case 2: DMP-Agent整合測試")
    print("=" * 80)
    print("功能: 從API-Agent拉取數據，透過DMP-Agent存儲至Google Cloud SQL")
    print("支持參數:")
    print("  --days-ago 2              : 獲取2天前的數據")
    print("  --start-date 2025-07-12   : 指定開始日期")
    print("  --end-date 2025-07-12     : 指定結束日期")
    print("  --platform IAByteC        : 指定平台為IAByteC")
    print("  --test-connection         : 測試平台連接")
    print("  --list-platforms          : 列出可用平台")
    print("  --stats-only              : 只顯示統計信息")
    print("注意: 可以使用 --days-ago 或者 --start-date/--end-date，日期格式為 YYYY-MM-DD")
    print("=" * 80)
    
    asyncio.run(main()) 