#!/usr/bin/env python3
"""
DMP-Agent 查詢工具
查詢數據庫中的 partner 和 source 統計信息
支持 --start-date, --end-date, --days-ago, --partner 參數
"""

import sys
import os
import argparse
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import re

# 添加項目根目錄到Python路徑
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DMPQueryAgent:
    """DMP查詢代理主類"""
    
    def __init__(self):
        self.db_manager = None
        
    async def initialize(self):
        """初始化數據庫連接"""
        logger.info("🚀 正在初始化DMP查詢代理...")
        
        try:
            from agents.data_dmp_agent.database_manager import EnhancedDMPDatabaseManager
            
            self.db_manager = EnhancedDMPDatabaseManager()
            await self.db_manager.init_pool()
            
            # 檢查數據庫健康狀態
            health = await self.db_manager.health_check()
            if health.get('status') != 'healthy':
                raise Exception(f"數據庫不健康: {health.get('error', 'Unknown')}")
            
            logger.info("✅ DMP查詢代理初始化成功")
            
        except Exception as e:
            logger.error(f"❌ DMP查詢代理初始化失敗: {e}")
            raise
    
    async def cleanup(self):
        """清理資源"""
        if self.db_manager:
            await self.db_manager.close_pool()
        logger.info("✅ DMP查詢代理資源清理完成")
    
    def parse_date_arguments(self, args) -> tuple:
        """解析日期參數"""
        if args.start_date and args.end_date:
            # 使用指定的日期範圍
            start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
            end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
            days_ago = None
        elif args.days_ago:
            # 使用幾天前的數據
            end_date = datetime.now() - timedelta(days=1)  # 昨天
            start_date = end_date - timedelta(days=args.days_ago - 1)
            days_ago = args.days_ago
        else:
            # 默認查詢昨天的數據
            end_date = datetime.now() - timedelta(days=1)
            start_date = end_date
            days_ago = 1
        
        return start_date, end_date, days_ago
    
    def get_mockup_multiplier(self, partner_name: str) -> tuple:
        """獲取partner的mockup乘數"""
        try:
            from config import PARTNER_SOURCES_MAPPING
            
            partner_config = PARTNER_SOURCES_MAPPING.get(partner_name, {})
            
            # 檢查是否有特殊配置
            if partner_name == "ByteC":
                return True, 1.0  # ByteC使用原始數據
            elif partner_name in ["DeepLeaper", "RAMPUP", "MKK", "MP"]:
                return True, 0.9  # 其他partner使用90%的mockup
            else:
                return False, 1.0  # 默認不使用mockup
        except ImportError:
            return False, 1.0
    
    def get_partner_mapping_info(self, partner_name: str) -> Dict[str, Any]:
        """獲取partner的映射信息"""
        try:
            from config import PARTNER_SOURCES_MAPPING, get_pattern_for_partner, get_sources_for_partner
            
            partner_config = PARTNER_SOURCES_MAPPING.get(partner_name, {})
            pattern = get_pattern_for_partner(partner_name)
            sources = get_sources_for_partner(partner_name)
            
            # 生成映射邏輯描述
            if pattern:
                mapping_logic = f"aff_sub LIKE '{pattern.replace('.*', '%')}'"
            elif sources and sources != ["ALL"]:
                source_list = ', '.join([f"'{s}'" for s in sources])
                mapping_logic = f"aff_sub IN ({source_list})"
            else:
                mapping_logic = "所有數據"
            
            return {
                'pattern': pattern,
                'sources': sources,
                'mapping_logic': mapping_logic,
                'email_enabled': partner_config.get('email_enabled', False),
                'platform': partner_config.get('platform', 'Unknown')
            }
        except ImportError:
            return {
                'pattern': '',
                'sources': [],
                'mapping_logic': '無法獲取映射信息',
                'email_enabled': False,
                'platform': 'Unknown'
            }
    
    def format_currency(self, amount: float) -> str:
        """格式化貨幣顯示"""
        if amount is None or amount == 0:
            return "$0.00 USD"
        return f"${amount:,.2f} USD"
    
    def format_percentage(self, rate: float) -> str:
        """格式化百分比顯示"""
        if rate is None or rate == 0:
            return "0.00%"
        return f"{rate:.2f}%"
    
    async def query_stats_simple(self, partner_filter: str = None, days_ago: int = 1) -> Dict[str, Any]:
        """簡化的統計查詢"""
        try:
            async with self.db_manager.pool.acquire() as conn:
                # 設置超時
                await conn.execute("SET statement_timeout = '300s'")
                
                # 基礎統計
                base_query = """
                SELECT 
                    COUNT(*) as total_conversions,
                    SUM(COALESCE(usd_sale_amount, sale_amount, 0)) as total_usd_amount,
                    SUM(COALESCE(usd_payout, payout, 0)) as total_usd_payout
                FROM conversions_api
                WHERE DATE(datetime_conversion) >= CURRENT_DATE - INTERVAL '%s days'
                """
                
                if partner_filter:
                    base_query += " AND partner = $1"
                    basic_stats = await conn.fetchrow(base_query % days_ago, partner_filter)
                else:
                    basic_stats = await conn.fetchrow(base_query % days_ago)
                
                # Partner分析
                partner_query = """
                SELECT 
                    partner,
                    platform,
                    COUNT(*) as conversion_count,
                    SUM(COALESCE(usd_sale_amount, sale_amount, 0)) as total_amount
                FROM conversions_api
                WHERE DATE(datetime_conversion) >= CURRENT_DATE - INTERVAL '%s days'
                """
                
                if partner_filter:
                    partner_query += " AND partner = $1"
                    partner_query += " GROUP BY partner, platform ORDER BY conversion_count DESC"
                    partner_stats = await conn.fetch(partner_query % days_ago, partner_filter)
                else:
                    partner_query += " GROUP BY partner, platform ORDER BY conversion_count DESC LIMIT 20"
                    partner_stats = await conn.fetch(partner_query % days_ago)
                
                # Source分析（簡化）
                source_query = """
                SELECT 
                    aff_sub as source,
                    partner,
                    COUNT(*) as conversion_count,
                    SUM(COALESCE(usd_sale_amount, sale_amount, 0)) as total_amount
                FROM conversions_api
                WHERE DATE(datetime_conversion) >= CURRENT_DATE - INTERVAL '%s days'
                AND aff_sub IS NOT NULL
                """
                
                if partner_filter:
                    source_query += " AND partner = $1"
                    source_query += " GROUP BY source, partner ORDER BY conversion_count DESC LIMIT 10"
                    source_stats = await conn.fetch(source_query % days_ago, partner_filter)
                else:
                    source_query += " GROUP BY source, partner ORDER BY conversion_count DESC LIMIT 20"
                    source_stats = await conn.fetch(source_query % days_ago)
                
                return {
                    'query_info': {
                        'partner_filter': partner_filter,
                        'days_ago': days_ago,
                        'query_time': datetime.now().isoformat()
                    },
                    'basic_stats': dict(basic_stats) if basic_stats else {},
                    'partner_breakdown': [dict(row) for row in partner_stats],
                    'top_sources': [dict(row) for row in source_stats],
                }
                
        except Exception as e:
            import traceback
            error_msg = f"{str(e)}\n{traceback.format_exc()}"
            logger.error(f"❌ 簡化查詢失敗: {error_msg}")
            return {
                'error': error_msg,
                'query_info': {
                    'partner_filter': partner_filter,
                    'days_ago': days_ago,
                    'query_time': datetime.now().isoformat()
                }
            }
    
    async def query_partner_stats(self, start_date: datetime, end_date: datetime, 
                                 days_ago: int, partner_filter: str = None) -> Dict[str, Any]:
        """查詢partner統計信息"""
        logger.info(f"📊 查詢partner統計信息...")
        logger.info(f"   日期範圍: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
        logger.info(f"   Partner過濾: {partner_filter or 'ALL'}")
        
        # 過濾掉 "ALL" 參數
        if partner_filter and partner_filter.upper() == "ALL":
            partner_filter = None
        
        # 調用數據庫查詢 - 使用簡化版本
        stats = await self.query_stats_simple(
            partner_filter=partner_filter,
            days_ago=days_ago
        )
        
        if 'error' in stats:
            raise Exception(f"查詢失敗: {stats['error']}")
        
        return stats
    
    def generate_source_distribution(self, source_stats: List[Dict], partner_name: str) -> List[Dict]:
        """生成source分布信息"""
        # 過濾該partner的source
        partner_sources = [s for s in source_stats if s.get('partner') == partner_name]
        
        # 按轉化數排序，取前5個
        sorted_sources = sorted(partner_sources, key=lambda x: x.get('conversion_count', 0), reverse=True)[:5]
        
        return sorted_sources
    
    def print_partner_report(self, stats: Dict[str, Any], start_date: datetime, end_date: datetime):
        """打印partner報告"""
        basic_stats = stats.get('basic_stats', {})
        partner_breakdown = stats.get('partner_breakdown', [])
        source_stats = stats.get('top_sources', [])
        
        # 計算總計
        total_conversions = basic_stats.get('total_conversions', 0)
        total_amount = float(basic_stats.get('total_usd_amount', 0)) if basic_stats.get('total_usd_amount') else 0
        total_payout = float(basic_stats.get('total_usd_payout', 0)) if basic_stats.get('total_usd_payout') else 0
        avg_commission_rate = (total_payout / total_amount * 100) if total_amount > 0 else 0
        
        print(f"\n{'='*80}")
        print(f" Partner 統計報告 ({start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')})")
        print(f"{'='*80}")
        
        # 查詢參數
        print(f"\n🔍 查詢參數:")
        print(f"   - 日期範圍: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
        print(f"   - Partner: {stats.get('query_info', {}).get('partner_filter', 'ALL')}")
        print(f"   - 總記錄數: {total_conversions:,} 條")
        
        # Partner詳細統計
        print(f"\n📈 Partner 詳細統計:")
        print(f"{'='*80}")
        
        for i, partner_data in enumerate(partner_breakdown, 1):
            partner_name = partner_data.get('partner', 'Unknown')
            conversion_count = partner_data.get('conversion_count', 0)
            total_amount = float(partner_data.get('total_amount', 0)) if partner_data.get('total_amount') else 0
            platform = partner_data.get('platform', 'Unknown')
            
            # 計算佣金率
            commission_rate = 0.5  # 默認佣金率
            commission_amount = float(total_amount) * (commission_rate / 100)
            
            # 獲取mockup信息
            has_mockup, mockup_multiplier = self.get_mockup_multiplier(partner_name)
            
            # 獲取映射信息
            mapping_info = self.get_partner_mapping_info(partner_name)
            
            print(f"\n{i}. {partner_name}")
            print(f"   📊 轉化數: {conversion_count:,} 條")
            print(f"   💰 銷售額: {self.format_currency(total_amount)}")
            print(f"   佣金: {self.format_currency(commission_amount)}")
            print(f"   📊 佣金率: {self.format_percentage(commission_rate)}")
            print(f"   Platform: {platform}")
            print(f"   Mockup: {'是' if has_mockup else '否'} (乘數: {mockup_multiplier})")
            print(f"   📋 數據欄位: usd_sale_amount, usd_payout")
            
            # Source映射情況
            print(f"   \n   Source 映射情況:")
            print(f"      映射邏輯: {mapping_info['mapping_logic']} → {partner_name}")
            
            # 生成source分布
            source_distribution = self.generate_source_distribution(source_stats, partner_name)
            if source_distribution:
                print(f"      📊 Source 分布:")
                for source_data in source_distribution:
                    source_name = source_data.get('source', 'Unknown')
                    source_count = source_data.get('conversion_count', 0)
                    source_amount = float(source_data.get('total_amount', 0)) if source_data.get('total_amount') else 0
                    print(f"         - {source_name}: {source_count:,} 條 ({self.format_currency(source_amount)})")
            else:
                print(f"      📊 Source 分布: 無數據")
        
        # 映射邏輯總覽
        print(f"\n📊 映射邏輯總覽:")
        print(f"{'='*80}")
        print(f" Partner 映射規則:")
        
        try:
            from config import PARTNER_SOURCES_MAPPING
            for partner_name, config in PARTNER_SOURCES_MAPPING.items():
                pattern = config.get('pattern', '')
                if pattern:
                    display_pattern = pattern.replace('.*', '%')
                    print(f"   - {partner_name}: aff_sub LIKE '{display_pattern}'")
                else:
                    sources = config.get('sources', [])
                    if sources and sources != ["ALL"]:
                        print(f"   - {partner_name}: aff_sub IN ({', '.join(sources)})")
                    else:
                        print(f"   - {partner_name}: 所有數據")
        except ImportError:
            print("   - 無法載入映射配置")
        
        # 總計
        print(f"\n 總計:")
        print(f"   📊 總轉化數: {total_conversions:,} 條")
        print(f"   總銷售額: {self.format_currency(total_amount)}")
        print(f"   💸 總佣金: {self.format_currency(total_payout)}")
        print(f"   平均佣金率: {self.format_percentage(avg_commission_rate)}")
        print(f"{'='*80}")
    
    async def run_query(self, args):
        """執行查詢"""
        try:
            # 初始化
            await self.initialize()
            
            # 解析日期參數
            start_date, end_date, days_ago = self.parse_date_arguments(args)
            
            # 執行查詢
            stats = await self.query_partner_stats(
                start_date=start_date,
                end_date=end_date,
                days_ago=days_ago,
                partner_filter=args.partner
            )
            
            # 打印報告
            self.print_partner_report(stats, start_date, end_date)
            
        except Exception as e:
            logger.error(f"❌ 查詢失敗: {e}")
            sys.exit(1)
        finally:
            await self.cleanup()

def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description="DMP-Agent 查詢工具 - 查詢partner和source統計信息",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
  # 查詢特定日期範圍
  python agents/data_dmp_agent/query_dmp_agent.py --start-date 2025-07-17 --end-date 2025-07-17
  
  # 查詢幾天前的數據
  python agents/data_dmp_agent/query_dmp_agent.py --days-ago 2
  
  # 查詢特定partner
  python agents/data_dmp_agent/query_dmp_agent.py --days-ago 1 --partner DeepLeaper
  
  # 查詢所有partner
  python agents/data_dmp_agent/query_dmp_agent.py --days-ago 1 --partner ALL
        """
    )
    
    # 日期參數組
    date_group = parser.add_mutually_exclusive_group()
    date_group.add_argument(
        '--start-date',
        type=str,
        help='開始日期 (YYYY-MM-DD)'
    )
    date_group.add_argument(
        '--end-date', 
        type=str,
        help='結束日期 (YYYY-MM-DD)'
    )
    date_group.add_argument(
        '--days-ago',
        type=int,
        default=1,
        help='幾天前的數據 (默認: 1)'
    )
    
    # Partner參數
    parser.add_argument(
        '--partner',
        type=str,
        help='指定partner名稱 (例如: DeepLeaper, RAMPUP, ALL)'
    )
    
    args = parser.parse_args()
    
    # 驗證參數
    if args.start_date and not args.end_date:
        parser.error("--start-date 需要配合 --end-date 使用")
    if args.end_date and not args.start_date:
        parser.error("--end-date 需要配合 --start-date 使用")
    
    # 執行查詢
    agent = DMPQueryAgent()
    asyncio.run(agent.run_query(args))

if __name__ == "__main__":
    main() 