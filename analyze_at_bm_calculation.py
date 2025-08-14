#!/usr/bin/env python3
"""
分析AT_BM数据的计算问题
"""

import pandas as pd
import sys
import os

def analyze_at_bm_calculation():
    """分析AT_BM数据的计算问题"""
    
    file_path = 'input/ID-async-report-exporter-publisher_conversion-report-id-2025-08-12-18nRimTm4Z1hBMXZ_0805-0810_DeepLeaper_AT_BM.csv'
    
    print("🔍 AT_BM数据问题分析:")
    
    try:
        df = pd.read_csv(file_path)
        print(f"数据行数: {len(df):,}")
        print()

        # 计算实际销售金额
        df['Calculated_Sale_Amount'] = df['Unit Price'] * df['Quantity']
        calculated_total = df['Calculated_Sale_Amount'].sum()

        print(f"Total Price (文件中的): {df['Total Price'].sum():,.0f} IDR")
        print(f"Unit Price × Quantity: {calculated_total:,.0f} IDR")
        print(f"差异: {calculated_total - df['Total Price'].sum():,.0f} IDR")
        print()

        # 检查货币转换
        print(f"🔄 货币转换分析:")
        usd_rate = 15400
        expected_usd_from_total_price = df['Total Price'].sum() / usd_rate
        expected_usd_from_calculated = calculated_total / usd_rate

        print(f"基于Total Price转USD: ${expected_usd_from_total_price:,.2f}")
        print(f"基于Quantity×Unit Price转USD: ${expected_usd_from_calculated:,.2f}")
        print()

        # 应用DeepLeaper的mockup multiplier
        print(f"🔧 DeepLeaper Mockup调整 (0.7倍):")
        print(f"基于Total Price: ${expected_usd_from_total_price * 0.7:,.2f}")
        print(f"基于Quantity×Unit Price: ${expected_usd_from_calculated * 0.7:,.2f}")
        print()

        print(f"📊 Reporter显示: $5,552.04")
        diff1 = 5552.04 - (expected_usd_from_total_price * 0.7)
        diff2 = 5552.04 - (expected_usd_from_calculated * 0.7)
        print(f"与Total Price计算值的差异: ${diff1:+,.2f}")
        print(f"与Quantity×Unit Price计算值的差异: ${diff2:+,.2f}")
        print()
        
        # 分析问题
        print("🎯 问题分析:")
        print("1. Total Price字段可能不是真正的销售金额")
        print("2. 真正的销售金额应该是 Quantity × Unit Price")
        print(f"3. 6,013,027,563 IDR ≈ ${expected_usd_from_calculated:,.2f} USD")
        print(f"4. 这个数值与您提到的60亿IDR相符")
        print()
        
        # 检查DMP agent应该使用哪个字段
        print("🔧 DMP Agent字段映射问题:")
        print("- 当前可能映射了错误的字段")
        print("- 应该使用 Quantity × Unit Price 而不是 Total Price")
        print("- 或者检查AT_BM的字段定义")
        
        return True
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        return False

if __name__ == "__main__":
    analyze_at_bm_calculation()

