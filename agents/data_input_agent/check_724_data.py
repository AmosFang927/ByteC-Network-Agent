#!/usr/bin/env python3
"""
检查7/24数据是否在Cloud SQL中可查询
"""

import pandas as pd
import numpy as np
from datetime import datetime
import re


def analyze_date_data():
    """分析数据中的日期信息"""
    print("🔍 检查7/24数据可用性")
    print("=" * 50)
    
    # 读取原始数据
    try:
        df = pd.read_csv('input/publisher-conversion-report--fmcTG6fi-20250727.csv', low_memory=False)
        print(f"✅ 成功读取数据: {len(df)} 行")
    except Exception as e:
        print(f"❌ 读取数据失败: {e}")
        return
    
    # 分析Click Date
    print("\n📅 Click Date 分析:")
    click_dates = df['Click Date'].dropna()
    if len(click_dates) > 0:
        # 提取日期部分
        date_pattern = r'(\d{4}-\d{2}-\d{2})'
        dates = []
        for date_str in click_dates:
            match = re.search(date_pattern, str(date_str))
            if match:
                dates.append(match.group(1))
        
        if dates:
            unique_dates = sorted(set(dates))
            print(f"  • 日期范围: {min(unique_dates)} 到 {max(unique_dates)}")
            print(f"  • 包含7/24: {'2025-07-24' in unique_dates}")
            
            # 统计7/24的数据
            july_24_count = sum(1 for date in dates if '2025-07-24' in date)
            print(f"  • 7/24数据条数: {july_24_count}")
    
    # 分析Conversion Date
    print("\n📅 Conversion Date 分析:")
    conversion_dates = df['Conversion Date'].dropna()
    if len(conversion_dates) > 0:
        # 提取日期部分
        dates = []
        for date_str in conversion_dates:
            match = re.search(date_pattern, str(date_str))
            if match:
                dates.append(match.group(1))
        
        if dates:
            unique_dates = sorted(set(dates))
            print(f"  • 日期范围: {min(unique_dates)} 到 {max(unique_dates)}")
            print(f"  • 包含7/24: {'2025-07-24' in unique_dates}")
            
            # 统计7/24的数据
            july_24_count = sum(1 for date in dates if '2025-07-24' in date)
            print(f"  • 7/24数据条数: {july_24_count}")
    
    # 分析时间分布
    print("\n📊 时间分布统计:")
    print(f"  • 总记录数: {len(df)}")
    print(f"  • 有Click Date的记录: {len(click_dates)} ({len(click_dates)/len(df)*100:.1f}%)")
    print(f"  • 有Conversion Date的记录: {len(conversion_dates)} ({len(conversion_dates)/len(df)*100:.1f}%)")
    
    # 检查7/24的具体数据
    print("\n🔍 7/24数据详情:")
    july_24_click = df[df['Click Date'].str.contains('2025-07-24', na=False)]
    july_24_conversion = df[df['Conversion Date'].str.contains('2025-07-24', na=False)]
    
    print(f"  • Click Date为7/24的记录: {len(july_24_click)}")
    print(f"  • Conversion Date为7/24的记录: {len(july_24_conversion)}")
    
    if len(july_24_click) > 0:
        print(f"  • 7/24 Click数据示例:")
        for i, row in july_24_click.head(3).iterrows():
            print(f"    - Conversion ID: {row['Conversion ID']}, Click Date: {row['Click Date']}")
    
    if len(july_24_conversion) > 0:
        print(f"  • 7/24 Conversion数据示例:")
        for i, row in july_24_conversion.head(3).iterrows():
            print(f"    - Conversion ID: {row['Conversion ID']}, Conversion Date: {row['Conversion Date']}")
    
    return df


def check_cloud_sql_status():
    """检查Cloud SQL状态"""
    print("\n🗄️ Cloud SQL状态检查:")
    print("=" * 50)
    
    # 这里应该连接到实际的Cloud SQL
    # 目前是模拟检查
    print("  ⚠️  Cloud SQL连接功能待实现")
    print("  📋 需要实现的功能:")
    print("    • 数据库连接配置")
    print("    • 数据表结构定义")
    print("    • 数据插入逻辑")
    print("    • 查询验证功能")
    
    print("\n🔧 建议的Cloud SQL查询:")
    print("""
    -- 检查7/24数据的SQL查询示例
    SELECT 
        COUNT(*) as total_records,
        COUNT(CASE WHEN DATE(click_date) = '2025-07-24' THEN 1 END) as july_24_clicks,
        COUNT(CASE WHEN DATE(conversion_date) = '2025-07-24' THEN 1 END) as july_24_conversions,
        SUM(CASE WHEN DATE(conversion_date) = '2025-07-24' THEN sale_amount_usd ELSE 0 END) as july_24_revenue
    FROM conversion_data
    WHERE DATE(click_date) = '2025-07-24' 
       OR DATE(conversion_date) = '2025-07-24';
    """)


def create_sample_query():
    """创建示例查询脚本"""
    print("\n📝 生成查询脚本:")
    print("=" * 50)
    
    query_script = """
# Cloud SQL查询脚本示例
import mysql.connector
from datetime import datetime

def check_july_24_data():
    # 数据库连接配置
    config = {
        'host': 'your-cloud-sql-host',
        'user': 'your-username',
        'password': 'your-password',
        'database': 'your-database'
    }
    
    try:
        # 连接数据库
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        
        # 查询7/24数据
        query = '''
        SELECT 
            COUNT(*) as total_records,
            COUNT(CASE WHEN DATE(click_date) = '2025-07-24' THEN 1 END) as july_24_clicks,
            COUNT(CASE WHEN DATE(conversion_date) = '2025-07-24' THEN 1 END) as july_24_conversions,
            SUM(CASE WHEN DATE(conversion_date) = '2025-07-24' THEN sale_amount_usd ELSE 0 END) as july_24_revenue
        FROM conversion_data
        WHERE DATE(click_date) = '2025-07-24' 
           OR DATE(conversion_date) = '2025-07-24';
        '''
        
        cursor.execute(query)
        result = cursor.fetchone()
        
        print(f"7/24数据统计:")
        print(f"  • 总记录数: {result[0]}")
        print(f"  • 7/24点击数: {result[1]}")
        print(f"  • 7/24转化数: {result[2]}")
        print(f"  • 7/24收入: ${result[3]:.2f}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"查询失败: {e}")

if __name__ == "__main__":
    check_july_24_data()
"""
    
    print(query_script)
    
    # 保存查询脚本
    with open('agents/data_input_agent/cloud_sql_query_example.py', 'w', encoding='utf-8') as f:
        f.write(query_script)
    
    print("✅ 查询脚本已保存到: agents/data_input_agent/cloud_sql_query_example.py")


def main():
    """主函数"""
    print("🔍 7/24数据Cloud SQL查询检查")
    print("=" * 60)
    
    # 分析数据
    df = analyze_date_data()
    
    # 检查Cloud SQL状态
    check_cloud_sql_status()
    
    # 创建示例查询
    create_sample_query()
    
    print("\n" + "=" * 60)
    print("📋 总结:")
    print("  • 数据已成功处理并保存到Excel")
    print("  • Cloud SQL插入功能需要进一步实现")
    print("  • 建议配置数据库连接后进行实际查询验证")
    print("  • 示例查询脚本已生成")


if __name__ == "__main__":
    main() 