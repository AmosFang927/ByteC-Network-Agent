#!/usr/bin/env python3
"""
查詢Google Cloud SQL中特定日期的轉化數據統計
"""

import asyncio
import asyncpg
from datetime import datetime, timedelta
import sys
import os

# 數據庫配置
DB_CONFIG = {
    'host': '34.124.206.16',
    'port': 5432,
    'database': 'postback_db',
    'user': 'postback_admin',
    'password': 'ByteC2024PostBack_CloudSQL'
}

async def query_conversion_stats(target_date: str = "2025-07-12"):
    """查詢特定日期的轉化數據統計"""
    
    print(f"🔍 查詢 {target_date} 的轉化數據統計")
    print("=" * 60)
    
    try:
        # 連接數據庫
        conn = await asyncpg.connect(**DB_CONFIG)
        print("✅ 成功連接到Google Cloud SQL")
        
        # 設置查詢日期範圍
        start_date = datetime.strptime(target_date, "%Y-%m-%d")
        end_date = start_date + timedelta(days=1)
        
        print(f"📅 查詢範圍: {start_date} 至 {end_date}")
        
        # 1. 查詢總轉化數量
        total_count = await conn.fetchval("""
            SELECT COUNT(*) 
            FROM conversions 
            WHERE created_at >= $1 AND created_at < $2
        """, start_date, end_date)
        
        print(f"\n📊 總轉化數量: {total_count:,}")
        
        # 2. 查詢總金額統計
        amount_stats = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total_records,
                SUM(COALESCE(usd_sale_amount, 0)) as total_sale_amount,
                SUM(COALESCE(usd_payout, 0)) as total_payout,
                AVG(COALESCE(usd_sale_amount, 0)) as avg_sale_amount
            FROM conversions 
            WHERE created_at >= $1 AND created_at < $2
        """, start_date, end_date)
        
        if amount_stats:
            print(f"\n💰 金額統計:")
            total_sale = amount_stats['total_sale_amount'] or 0
            total_payout = amount_stats['total_payout'] or 0
            avg_sale = amount_stats['avg_sale_amount'] or 0
            
            print(f"   - 總銷售金額: ${total_sale:,.2f} USD")
            print(f"   - 總佣金金額: ${total_payout:,.2f} USD")
            print(f"   - 平均銷售金額: ${avg_sale:,.2f} USD")
        else:
            print(f"\n💰 金額統計: 無數據")
        
        # 3. 按Partner分組統計
        partner_stats = await conn.fetch("""
            SELECT 
                CASE 
                    WHEN aff_sub IS NULL OR aff_sub = '' THEN 'Unknown'
                    ELSE aff_sub
                END as partner_source,
                COUNT(*) as conversion_count,
                SUM(COALESCE(usd_sale_amount, 0)) as total_amount
            FROM conversions 
            WHERE created_at >= $1 AND created_at < $2
            GROUP BY 
                CASE 
                    WHEN aff_sub IS NULL OR aff_sub = '' THEN 'Unknown'
                    ELSE aff_sub
                END
            ORDER BY conversion_count DESC
        """, start_date, end_date)
        
        if partner_stats:
            print(f"\n🏢 按Partner來源統計:")
            for row in partner_stats:
                partner = row['partner_source']
                count = row['conversion_count']
                amount = row['total_amount']
                print(f"   - {partner}: {count:,} 轉化, ${amount:,.2f} USD")
        
        # 4. 按小時分佈統計
        hourly_stats = await conn.fetch("""
            SELECT 
                EXTRACT(HOUR FROM created_at) as hour,
                COUNT(*) as conversion_count
            FROM conversions 
            WHERE created_at >= $1 AND created_at < $2
            GROUP BY EXTRACT(HOUR FROM created_at)
            ORDER BY hour
        """, start_date, end_date)
        
        if hourly_stats:
            print(f"\n⏰ 按小時分佈:")
            for row in hourly_stats:
                hour = int(row['hour'])
                count = row['conversion_count']
                print(f"   - {hour:02d}:00 - {hour:02d}:59: {count:,} 轉化")
        
        # 5. 查詢最近的轉化記錄（作為範例）
        recent_conversions = await conn.fetch("""
            SELECT 
                id,
                conversion_id,
                offer_name,
                aff_sub,
                usd_sale_amount,
                usd_payout,
                created_at
            FROM conversions 
            WHERE created_at >= $1 AND created_at < $2
            ORDER BY created_at DESC
            LIMIT 5
        """, start_date, end_date)
        
        if recent_conversions:
            print(f"\n📋 最近的轉化記錄 (前5條):")
            for row in recent_conversions:
                print(f"   - ID: {row['id']}")
                print(f"     轉化ID: {row['conversion_id']}")
                print(f"     Offer: {row['offer_name']}")
                print(f"     來源: {row['aff_sub']}")
                print(f"     銷售金額: ${row['usd_sale_amount']:.2f} USD")
                print(f"     佣金: ${row['usd_payout']:.2f} USD")
                print(f"     時間: {row['created_at']}")
                print()
        
        # 6. 檢查是否有該日期的數據
        if total_count == 0:
            print(f"\n⚠️ 注意: {target_date} 沒有找到轉化數據")
            
            # 查詢最近有數據的日期
            recent_dates = await conn.fetch("""
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as count
                FROM conversions 
                WHERE created_at >= $1::timestamp - INTERVAL '30 days'
                GROUP BY DATE(created_at)
                ORDER BY date DESC
                LIMIT 10
            """, start_date)
            
            if recent_dates:
                print(f"\n📅 最近30天有數據的日期:")
                for row in recent_dates:
                    print(f"   - {row['date']}: {row['count']:,} 轉化")
        
        # 關閉連接
        await conn.close()
        print(f"\n✅ 查詢完成")
        
    except Exception as e:
        print(f"❌ 查詢失敗: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

async def main():
    """主函數"""
    target_date = "2025-07-12"
    
    # 檢查是否有命令行參數
    if len(sys.argv) > 1:
        target_date = sys.argv[1]
    
    print(f"🚀 開始查詢 {target_date} 的轉化數據統計")
    await query_conversion_stats(target_date)

if __name__ == "__main__":
    asyncio.run(main()) 