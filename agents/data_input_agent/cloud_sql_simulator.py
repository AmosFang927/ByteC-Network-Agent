#!/usr/bin/env python3
"""
Cloud SQL模拟器 - 演示7/24数据查询功能
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from pathlib import Path


class CloudSQLSimulator:
    """Cloud SQL模拟器"""
    
    def __init__(self):
        self.data = None
        self.load_data()
    
    def load_data(self):
        """加载处理后的数据"""
        try:
            # 查找最新的处理文件
            output_dir = Path("output")
            
            # 优先查找包含july_24的文件
            july_24_files = list(output_dir.glob("*july_24*.xlsx"))
            if july_24_files:
                latest_file = max(july_24_files, key=lambda x: x.stat().st_mtime)
                print(f"📁 加载包含7/24数据的文件: {latest_file.name}")
            else:
                # 如果没有找到包含july_24的文件，使用最新的Processed文件
                excel_files = list(output_dir.glob("Processed_*.xlsx"))
                if not excel_files:
                    print("❌ 未找到处理后的Excel文件")
                    return
                latest_file = max(excel_files, key=lambda x: x.stat().st_mtime)
                print(f"📁 加载数据文件: {latest_file.name}")
            
            self.data = pd.read_excel(latest_file)
            print(f"✅ 成功加载 {len(self.data)} 条记录")
            
        except Exception as e:
            print(f"❌ 加载数据失败: {e}")
    
    def query_july_24_data(self):
        """查询7/24数据"""
        if self.data is None:
            print("❌ 数据未加载")
            return None
        
        print("\n🔍 查询7/24数据...")
        
        # 检查可用的列
        available_columns = list(self.data.columns)
        print(f"  • 可用列: {available_columns}")
        
        # 转换日期格式（如果存在）
        if 'Conversion Date' in self.data.columns:
            self.data['Conversion Date'] = pd.to_datetime(self.data['Conversion Date'], errors='coerce')
        
        if 'Click Date' in self.data.columns:
            self.data['Click Date'] = pd.to_datetime(self.data['Click Date'], errors='coerce')
        
        # 查询7/24数据
        july_24_click = pd.DataFrame()
        july_24_conversion = pd.DataFrame()
        
        if 'Click Date' in self.data.columns:
            july_24_click = self.data[self.data['Click Date'].dt.date == pd.to_datetime('2025-07-24').date()]
        
        if 'Conversion Date' in self.data.columns:
            july_24_conversion = self.data[self.data['Conversion Date'].dt.date == pd.to_datetime('2025-07-24').date()]
        
        # 合并查询结果
        july_24_total = pd.concat([july_24_click, july_24_conversion]).drop_duplicates()
        
        result = {
            'total_records': len(july_24_total),
            'july_24_clicks': len(july_24_click),
            'july_24_conversions': len(july_24_conversion),
            'july_24_revenue': july_24_conversion['Sale Amount (USD)'].sum() if len(july_24_conversion) > 0 and 'Sale Amount (USD)' in july_24_conversion.columns else 0.0,
            'july_24_total': len(july_24_total)
        }
        
        return result
    
    def get_data_summary(self):
        """获取数据摘要"""
        if self.data is None:
            print("❌ 数据未加载")
            return None
        
        # 转换日期格式（如果存在）
        if 'Conversion Date' in self.data.columns:
            self.data['Conversion Date'] = pd.to_datetime(self.data['Conversion Date'], errors='coerce')
        
        if 'Click Date' in self.data.columns:
            self.data['Click Date'] = pd.to_datetime(self.data['Click Date'], errors='coerce')
        
        summary = {
            'total_records': len(self.data),
            'unique_conversions': self.data['Conversion ID'].nunique() if 'Conversion ID' in self.data.columns else 0,
            'unique_publishers': self.data['Publisher Sub ID 1'].nunique() if 'Publisher Sub ID 1' in self.data.columns else 0,
            'total_revenue': self.data['Sale Amount (USD)'].sum() if 'Sale Amount (USD)' in self.data.columns else 0.0,
            'avg_revenue': self.data['Sale Amount (USD)'].mean() if 'Sale Amount (USD)' in self.data.columns else 0.0,
            'earliest_date': self.data['Conversion Date'].min() if 'Conversion Date' in self.data.columns else None,
            'latest_date': self.data['Conversion Date'].max() if 'Conversion Date' in self.data.columns else None,
            'pending_count': len(self.data[self.data['Status'] == 'Pending']) if 'Status' in self.data.columns else 0,
            'approved_count': len(self.data[self.data['Status'] == 'Approved']) if 'Status' in self.data.columns else 0
        }
        
        return summary
    
    def simulate_cloud_sql_query(self, query_type="july_24"):
        """模拟Cloud SQL查询"""
        print(f"🗄️ 模拟Cloud SQL查询: {query_type}")
        print("=" * 50)
        
        if query_type == "july_24":
            result = self.query_july_24_data()
            if result:
                print("\n📊 7/24数据统计:")
                print(f"  • 总记录数: {result['total_records']}")
                print(f"  • 7/24点击数: {result['july_24_clicks']}")
                print(f"  • 7/24转化数: {result['july_24_conversions']}")
                print(f"  • 7/24收入: ${result['july_24_revenue']:.2f}")
                print(f"  • 7/24总记录: {result['july_24_total']}")
                
                if result['july_24_total'] > 0:
                    print("✅ 7/24数据在模拟Cloud SQL中可查询")
                else:
                    print("❌ 7/24数据在模拟Cloud SQL中不存在")
            else:
                print("❌ 无法查询7/24数据")
        
        elif query_type == "summary":
            summary = self.get_data_summary()
            if summary:
                print("\n📈 数据库摘要:")
                print(f"  • 总记录数: {summary['total_records']}")
                print(f"  • 唯一转化数: {summary['unique_conversions']}")
                print(f"  • 合作伙伴数: {summary['unique_publishers']}")
                print(f"  • 总收入: ${summary['total_revenue']:.2f}")
                print(f"  • 平均收入: ${summary['avg_revenue']:.2f}")
                print(f"  • 日期范围: {summary['earliest_date']} 到 {summary['latest_date']}")
                print(f"  • Pending状态: {summary['pending_count']}")
                print(f"  • Approved状态: {summary['approved_count']}")
        
        return result if query_type == "july_24" else summary


def check_july_24_availability():
    """检查7/24数据可用性"""
    print("🔍 检查7/24数据在模拟Cloud SQL中的可用性")
    print("=" * 60)
    
    simulator = CloudSQLSimulator()
    
    # 查询7/24数据
    july_24_data = simulator.simulate_cloud_sql_query("july_24")
    
    # 获取数据摘要
    summary = simulator.simulate_cloud_sql_query("summary")
    
    print("\n" + "=" * 60)
    print("📋 总结:")
    
    if july_24_data and july_24_data['july_24_total'] > 0:
        print("✅ 7/24数据在模拟Cloud SQL中可查询")
        print(f"  • 找到 {july_24_data['july_24_total']} 条7/24相关记录")
        print(f"  • 其中 {july_24_data['july_24_conversions']} 条转化记录")
        print(f"  • 7/24收入: ${july_24_data['july_24_revenue']:.2f}")
    else:
        print("❌ 7/24数据在模拟Cloud SQL中不存在")
        print("  • 当前数据范围: 2025-07-25 (全部记录)")
        print("  • 建议: 需要导入包含7/24数据的文件")
    
    print("\n🔧 实际Cloud SQL查询示例:")
    print("""
    -- 检查7/24数据的SQL查询
    SELECT 
        COUNT(*) as total_records,
        COUNT(CASE WHEN DATE(click_date) = '2025-07-24' THEN 1 END) as july_24_clicks,
        COUNT(CASE WHEN DATE(conversion_date) = '2025-07-24' THEN 1 END) as july_24_conversions,
        SUM(CASE WHEN DATE(conversion_date) = '2025-07-24' THEN sale_amount_usd ELSE 0 END) as july_24_revenue
    FROM conversion_data
    WHERE DATE(click_date) = '2025-07-24' 
       OR DATE(conversion_date) = '2025-07-24';
    """)


def create_test_data_with_july_24():
    """创建包含7/24的测试数据"""
    print("📝 创建包含7/24的测试数据")
    print("=" * 50)
    
    # 读取原始数据
    try:
        df = pd.read_csv('input/publisher-conversion-report--fmcTG6fi-20250727.csv', low_memory=False)
        print(f"✅ 读取原始数据: {len(df)} 行")
        
        # 创建一些7/24的测试数据
        test_data = []
        for i in range(100):  # 创建100条7/24的测试记录
            test_data.append({
                'Conversion ID': 999999999 + i,
                'Click Date': '2025-07-24 10:00:00',
                'Conversion Date': '2025-07-24 15:30:00',
                'Order ID': f'TEST_ORDER_{i:06d}',
                'Sale Amount (USD)': round(np.random.uniform(1, 100), 2),
                'Publisher Sub ID 1': 'TEST_PUBLISHER',
                'Status': 'Pending',
                'Advertiser': 'Test Advertiser',
                'Publisher Sub ID 2': '',
                'Publisher Sub ID 3': '',
                'Publisher Sub ID 4': '',
                'Publisher Sub ID 5': '',
                'Advertiser Sub ID 2': '',
                'Advertiser Sub ID 3': '',
                'Advertiser Sub ID 4': '',
                'Advertiser Sub ID 5': ''
            })
        
        # 合并数据
        test_df = pd.DataFrame(test_data)
        combined_df = pd.concat([df, test_df], ignore_index=True)
        
        # 保存测试数据
        test_file = 'input/test_data_with_july_24.csv'
        combined_df.to_csv(test_file, index=False)
        print(f"✅ 测试数据已保存: {test_file}")
        print(f"  • 原始数据: {len(df)} 行")
        print(f"  • 新增7/24数据: {len(test_data)} 行")
        print(f"  • 总数据: {len(combined_df)} 行")
        
        return test_file
        
    except Exception as e:
        print(f"❌ 创建测试数据失败: {e}")
        return None


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "check":
            check_july_24_availability()
        elif sys.argv[1] == "create_test":
            create_test_data_with_july_24()
        else:
            print("用法: python cloud_sql_simulator.py [check|create_test]")
    else:
        print("🔍 检查7/24数据可用性...")
        check_july_24_availability() 