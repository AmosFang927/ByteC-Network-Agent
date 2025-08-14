#!/usr/bin/env python3
"""
正确读取AT_BM CSV文件并计算真实的Total Price总和
"""

import pandas as pd
import csv
from io import StringIO

def read_csv_correctly(file_path):
    """正确读取CSV文件，避免列错位问题"""
    
    print("🔧 正确读取AT_BM CSV文件")
    print()
    
    try:
        # 方法1: 使用csv模块手动解析
        all_rows = []
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            csv_reader = csv.reader(f)
            headers = next(csv_reader)  # 读取标题行
            
            # 找到关键列的索引
            unit_price_idx = headers.index('Unit Price')
            quantity_idx = headers.index('Quantity')
            total_price_idx = headers.index('Total Price')
            
            print("📋 找到关键列索引:")
            print(f"Unit Price: 索引 {unit_price_idx}")
            print(f"Quantity: 索引 {quantity_idx}")
            print(f"Total Price: 索引 {total_price_idx}")
            print()
            
            # 读取所有数据行
            for row_num, row in enumerate(csv_reader, 1):
                if len(row) > max(unit_price_idx, quantity_idx, total_price_idx):
                    try:
                        unit_price = float(row[unit_price_idx])
                        quantity = float(row[quantity_idx])
                        total_price = float(row[total_price_idx])
                        
                        all_rows.append({
                            'Unit Price': unit_price,
                            'Quantity': quantity,
                            'Total Price': total_price,
                            'Calculated': unit_price * quantity
                        })
                    except ValueError:
                        print(f"⚠️ 第{row_num}行数据转换失败，跳过")
                        continue
                        
                if row_num <= 5:  # 显示前5行作为验证
                    up = float(row[unit_price_idx]) if row[unit_price_idx] else 0
                    qty = float(row[quantity_idx]) if row[quantity_idx] else 0
                    tp = float(row[total_price_idx]) if row[total_price_idx] else 0
                    print(f"第{row_num}行: UP={up}, Q={qty}, TP={tp}, UP×Q={up*qty}, 相等={tp==up*qty}")
        
        print()
        print("📊 正确的统计结果:")
        
        # 计算统计
        total_price_sum = sum(row['Total Price'] for row in all_rows)
        unit_price_sum = sum(row['Unit Price'] for row in all_rows)
        quantity_sum = sum(row['Quantity'] for row in all_rows)
        
        # 验证相等的行数
        equal_count = sum(1 for row in all_rows if abs(row['Total Price'] - row['Calculated']) < 0.01)
        
        print(f"总行数: {len(all_rows):,}")
        print(f"Unit Price总和: {unit_price_sum:,.0f}")
        print(f"Quantity总和: {quantity_sum:,.0f}")
        print(f"Total Price总和: {total_price_sum:,.0f} IDR")
        print(f"Total Price = Unit Price × Quantity的行数: {equal_count:,} ({equal_count/len(all_rows)*100:.1f}%)")
        print()
        
        # 货币转换
        usd_amount = total_price_sum / 15400
        print(f"✅ 正确的USD转换: {total_price_sum:,.0f} IDR = ${usd_amount:,.2f} USD")
        
        # DeepLeaper Mockup调整
        adjusted_usd = usd_amount * 0.7
        print(f"✅ DeepLeaper Mockup调整 (0.7倍): ${adjusted_usd:,.2f} USD")
        print()
        
        print("🎯 这就是Reporter Agent应该显示的金额!")
        print(f"当前Reporter显示: $5,552.04")
        print(f"应该显示: ${adjusted_usd:,.2f}")
        print(f"差异: ${adjusted_usd - 5552.04:+,.2f}")
        
        return total_price_sum, adjusted_usd
        
    except Exception as e:
        print(f"❌ 读取失败: {e}")
        return 0, 0

if __name__ == "__main__":
    file_path = 'input/ID-async-report-exporter-publisher_conversion-report-id-2025-08-12-18nRimTm4Z1hBMXZ_0805-0810_DeepLeaper_AT_BM.csv'
    read_csv_correctly(file_path)

