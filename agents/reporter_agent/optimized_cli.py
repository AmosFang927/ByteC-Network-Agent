#!/usr/bin/env python3
"""
Reporter-Agent 優化版本命令行接口
支持與原版相同的參數格式，但使用優化的數據庫管理器
"""

import asyncio
import argparse
import sys
import os
from datetime import datetime, timedelta
import time

# 添加必要的路徑
current_dir = os.path.dirname(__file__)
project_root = os.path.join(current_dir, '../..')
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'shared'))

# 使用優化的數據庫管理器
from shared.database.enhanced_database_manager import EnhancedDatabaseManager, DatabaseConfig

class OptimizedReporterCLI:
    """優化版本的 Reporter-Agent 命令行接口"""
    
    def __init__(self):
        # 企業級數據庫配置 (避免服務器配置問題)
        self.db_config = DatabaseConfig(
            host='34.124.206.16',
            port=5432,
            database='postback_db',
            user='postback_admin',
            password='ByteC2024PostBack_CloudSQL',
            min_size=5,
            max_size=20,
            command_timeout=180,
            enable_cache=False,  # 簡化版本先禁用緩存
            enable_monitoring=True
        )
        
        self.db = None
    
    async def generate_report(self, args):
        """生成報表"""
        print("🚀 Reporter-Agent 優化版本啟動")
        
        # 計算日期範圍
        if args.days_ago:
            # 按照原版邏輯：只查詢 N 天前那一天的數據
            target_date = datetime.now() - timedelta(days=args.days_ago)
            start_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
            print(f"🗓️  days_ago={args.days_ago}, 只查詢 {args.days_ago} 天前的數據: {start_date.strftime('%Y-%m-%d')} (該天數據)")
        elif args.start_date and args.end_date:
            start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
            end_date = datetime.strptime(args.end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
            print(f"🗓️  日期範圍: {start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')}")
        else:
            # 默認獲取過去3天的數據
            end_date = datetime.now().replace(hour=23, minute=59, second=59)
            start_date = (end_date - timedelta(days=3)).replace(hour=0, minute=0, second=0)
            print(f"🗓️  默認日期範圍: {start_date.strftime('%Y-%m-%d %H:%M:%S')} 到 {end_date.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if args.limit:
            print(f"🔢 設置數據拉取限制: {args.limit} 條記錄")
        
        # 初始化數據庫連接
        print("🔗 初始化優化版本數據庫連接...")
        start_time = time.time()
        
        try:
            self.db = EnhancedDatabaseManager(self.db_config)
            await self.db.initialize()
            
            # 健康檢查
            health = await self.db.health_check()
            if health.get('status') != 'healthy':
                print(f"❌ 數據庫健康檢查失敗: {health}")
                return False
            
            init_time = time.time() - start_time
            print(f"✅ 數據庫連接初始化成功 ({init_time:.2f}秒)")
            
            # 生成報表
            await self.process_report_data(start_date, end_date, args)
            
            return True
            
        except Exception as e:
            print(f"❌ 報表生成失敗: {e}")
            return False
        finally:
            if self.db:
                await self.db.close()
    
    async def process_report_data(self, start_date, end_date, args):
        """處理報表數據"""
        total_start_time = time.time()
        
        try:
            print("🔍 開始查詢轉換數據...")
            query_start = time.time()
            
            # 構建查詢
            base_query = """
                SELECT id, conversion_id, partner, datetime_conversion, 
                       usd_sale_amount, aff_sub, aff_sub2
                FROM conversions 
                WHERE datetime_conversion >= $1 AND datetime_conversion <= $2
            """
            
            # 添加 Partner 過濾
            params = [start_date, end_date]
            if args.partner:
                base_query += " AND partner = $3"
                params.append(args.partner)
                print(f"🎯 限制 Partner: {args.partner}")
            
            # 添加排序和限制
            base_query += " ORDER BY datetime_conversion DESC"
            if args.limit:
                limit_param = f"${len(params) + 1}"
                base_query += f" LIMIT {limit_param}"
                params.append(args.limit)
            
            # 執行查詢
            conversions = await self.db.execute_query(base_query, params)
            query_time = time.time() - query_start
            
            print(f"📊 查詢完成: {len(conversions)} 條記錄 ({query_time:.2f}秒)")
            print(f"🚀 查詢速度: {len(conversions)/query_time:.1f} 記錄/秒")
            
            if not conversions:
                print("⚠️ 沒有找到符合條件的數據")
                return
            
            # 數據處理和分析
            await self.analyze_data(conversions)
            
            # 生成報表文件 (簡化版本)
            await self.generate_report_files(conversions, start_date, end_date, args)
            
            total_time = time.time() - total_start_time
            print(f"✅ 報表生成完成！總耗時: {total_time:.2f}秒")
            print(f"📈 整體處理速度: {len(conversions)/total_time:.1f} 記錄/秒")
            
        except Exception as e:
            print(f"❌ 數據處理失敗: {e}")
            raise
    
    async def analyze_data(self, conversions):
        """分析數據"""
        print("📈 開始數據分析...")
        analysis_start = time.time()
        
        try:
            # Partner 統計
            partners = {}
            total_revenue = 0
            
            for conv in conversions:
                partner = conv['partner']
                amount = float(conv['usd_sale_amount'] or 0)
                
                if partner not in partners:
                    partners[partner] = {'count': 0, 'revenue': 0}
                
                partners[partner]['count'] += 1
                partners[partner]['revenue'] += amount
                total_revenue += amount
            
            analysis_time = time.time() - analysis_start
            
            print(f"📊 分析結果 ({analysis_time:.2f}秒):")
            print(f"   總轉換數: {len(conversions)}")
            print(f"   總收入: ${total_revenue:,.2f}")
            print(f"   Partner 數量: {len(partners)}")
            
            # 顯示前5個 Partner
            top_partners = sorted(partners.items(), key=lambda x: x[1]['revenue'], reverse=True)[:5]
            print("   前5個 Partner:")
            for partner, stats in top_partners:
                print(f"     {partner}: {stats['count']} 轉換, ${stats['revenue']:,.2f}")
                
        except Exception as e:
            print(f"❌ 數據分析失敗: {e}")
    
    async def generate_report_files(self, conversions, start_date, end_date, args):
        """生成報表文件 (簡化版本)"""
        print("📄 生成報表文件...")
        
        try:
            # 創建簡單的 CSV 報表
            filename = f"report_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"
            
            with open(filename, 'w', encoding='utf-8') as f:
                # 寫入標題
                f.write("ID,Conversion ID,Partner,DateTime,USD Amount,Aff Sub,Aff Sub2\n")
                
                # 寫入數據
                for conv in conversions:
                    f.write(f"{conv['id']},{conv['conversion_id']},{conv['partner']},{conv['datetime_conversion']},{conv['usd_sale_amount']},{conv['aff_sub']},{conv['aff_sub2']}\n")
            
            print(f"✅ 報表文件已生成: {filename}")
            
            # 如果需要發送郵件
            if args.self_email:
                print("📧 報表生成完成，如需發送郵件請使用完整版本")
                
        except Exception as e:
            print(f"❌ 報表文件生成失敗: {e}")

def create_parser():
    """創建命令行參數解析器"""
    parser = argparse.ArgumentParser(
        description="Reporter-Agent 優化版本 - 解決數據庫性能問題"
    )
    
    parser.add_argument('--partner', help='Partner名稱')
    parser.add_argument('--start-date', help='開始日期 (YYYY-MM-DD)')
    parser.add_argument('--end-date', help='結束日期 (YYYY-MM-DD)')
    parser.add_argument('--days-ago', type=int, help='過去N天的數據')
    parser.add_argument('--no-email', action='store_true', help='不發送郵件')
    parser.add_argument('--no-feishu', action='store_true', help='不上傳到飛書')
    parser.add_argument('--self-email', action='store_true', help='發送郵件到自己（測試用）')
    parser.add_argument('--limit', type=int, help='限制記錄數量')
    
    return parser

async def main():
    """主程序"""
    parser = create_parser()
    args = parser.parse_args()
    
    cli = OptimizedReporterCLI()
    
    start_time = time.time()
    success = await cli.generate_report(args)
    total_time = time.time() - start_time
    
    if success:
        print(f"\n🎉 任務完成！總運行時間: {total_time:.2f}秒")
        return 0
    else:
        print(f"\n❌ 任務失敗！運行時間: {total_time:.2f}秒")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main()) 