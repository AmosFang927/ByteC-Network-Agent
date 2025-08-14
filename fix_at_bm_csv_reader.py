#!/usr/bin/env python3
"""
创建一个专门的AT_BM CSV读取函数，确保正确读取数据
"""

import pandas as pd
import csv
from io import StringIO

def read_at_bm_csv_correctly(file_path):
    """
    正确读取AT_BM CSV文件的函数
    解决pandas列错位问题
    """
    
    print(f"🔧 正确读取AT_BM CSV文件: {file_path}")
    
    try:
        # 使用csv模块手动解析
        all_data = []
        headers = None
        
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            csv_reader = csv.reader(f)
            headers = next(csv_reader)  # 读取标题行
            
            print(f"📋 找到 {len(headers)} 列")
            print(f"前10列: {headers[:10]}")
            
            # 找到关键列的索引
            try:
                unit_price_idx = headers.index('Unit Price')
                quantity_idx = headers.index('Quantity')
                total_price_idx = headers.index('Total Price')
                site_idx = headers.index('Site')
                
                print(f"✅ 关键列索引:")
                print(f"   Site: {site_idx}")
                print(f"   Unit Price: {unit_price_idx}")
                print(f"   Quantity: {quantity_idx}")
                print(f"   Total Price: {total_price_idx}")
                
            except ValueError as e:
                print(f"❌ 找不到必要的列: {e}")
                return None
            
            # 读取所有数据行
            for row_num, row in enumerate(csv_reader, 1):
                if len(row) > max(unit_price_idx, quantity_idx, total_price_idx, site_idx):
                    try:
                        row_data = {}
                        for i, header in enumerate(headers):
                            if i < len(row):
                                row_data[header] = row[i]
                            else:
                                row_data[header] = ''
                        all_data.append(row_data)
                        
                    except Exception as e:
                        print(f"⚠️ 第{row_num}行解析失败: {e}")
                        continue
        
        # 转换为DataFrame
        df = pd.DataFrame(all_data)
        
        # 确保数值列是正确的类型
        numeric_columns = ['Unit Price', 'Quantity', 'Total Price']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        print(f"✅ 成功读取 {len(df)} 行数据")
        
        # 验证第一行
        if len(df) > 0:
            first_row = df.iloc[0]
            site = first_row['Site']
            up = first_row['Unit Price']
            qty = first_row['Quantity']
            tp = first_row['Total Price']
            
            print(f"📊 第一行验证:")
            print(f"   Site: {site}")
            print(f"   Unit Price: {up}")
            print(f"   Quantity: {qty}")
            print(f"   Total Price: {tp}")
            print(f"   验证: {up} × {qty} = {up * qty}, 相等: {tp == up * qty}")
            
            # 计算总和
            total_price_sum = df['Total Price'].sum()
            print(f"✅ Total Price总和: {total_price_sum:,.0f} IDR")
            
            return df
        else:
            print("❌ 没有读取到数据")
            return None
            
    except Exception as e:
        print(f"❌ 读取失败: {e}")
        return None

# 测试函数
if __name__ == "__main__":
    file_path = 'input/ID-async-report-exporter-publisher_conversion-report-id-2025-08-12-18nRimTm4Z1hBMXZ_0805-0810_DeepLeaper_AT_BM.csv'
    df = read_at_bm_csv_correctly(file_path)
    
    if df is not None:
        print(f"\n🎯 修复结果:")
        print(f"总行数: {len(df)}")
        print(f"总列数: {len(df.columns)}")
        
        # 计算正确的统计
        total_price_sum = df['Total Price'].sum()
        usd_amount = total_price_sum / 15400
        adjusted_usd = usd_amount * 0.7
        
        print(f"Total Price总和: {total_price_sum:,.0f} IDR")
        print(f"USD转换: ${usd_amount:,.2f}")
        print(f"DeepLeaper调整: ${adjusted_usd:,.2f}")
        print(f"这应该是Reporter Agent显示的金额!")

