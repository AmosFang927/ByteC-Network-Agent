#!/usr/bin/env python3
"""
调查Total Price与Quantity × Unit Price的差异
"""

import pandas as pd
import numpy as np

def investigate_price_discrepancy():
    """调查价格差异"""
    
    file_path = 'input/ID-async-report-exporter-publisher_conversion-report-id-2025-08-12-18nRimTm4Z1hBMXZ_0805-0810_DeepLeaper_AT_BM.csv'
    
    print("🔍 调查Total Price与Quantity × Unit Price的差异")
    
    try:
        df = pd.read_csv(file_path)
        print(f"数据行数: {len(df):,}")
        print()

        # 计算每行的差异
        df['Calculated_Total'] = df['Unit Price'] * df['Quantity']
        df['Price_Difference'] = df['Calculated_Total'] - df['Total Price']
        
        # 基本统计
        print("📊 基本统计:")
        print(f"Total Price总和: {df['Total Price'].sum():,.0f} IDR")
        print(f"Calculated Total总和: {df['Calculated_Total'].sum():,.0f} IDR")
        print(f"总差异: {df['Price_Difference'].sum():,.0f} IDR")
        print()
        
        # 检查是否有行相等
        equal_rows = (df['Total Price'] == df['Calculated_Total']).sum()
        print(f"Total Price = Calculated Total的行数: {equal_rows:,} ({equal_rows/len(df)*100:.1f}%)")
        print()
        
        # 检查前10行的详细情况
        print("🔍 前10行详细分析:")
        print("序号 | Unit Price | Quantity | Total Price | Calculated | 差异")
        print("-" * 65)
        for i in range(min(10, len(df))):
            row = df.iloc[i]
            print(f"{i+1:3d}  | {row['Unit Price']:10.0f} | {row['Quantity']:8.0f} | {row['Total Price']:11.0f} | {row['Calculated_Total']:10.0f} | {row['Price_Difference']:8.0f}")
        print()
        
        # 检查异常行
        print("🚨 异常行分析:")
        
        # 找出差异最大的行
        max_diff_idx = df['Price_Difference'].abs().idxmax()
        max_diff_row = df.loc[max_diff_idx]
        print(f"最大差异行 (行{int(max_diff_idx)+1}):")
        print(f"  Unit Price: {max_diff_row['Unit Price']}")
        print(f"  Quantity: {max_diff_row['Quantity']}")
        print(f"  Total Price: {max_diff_row['Total Price']}")
        print(f"  Calculated: {max_diff_row['Calculated_Total']}")
        print(f"  差异: {max_diff_row['Price_Difference']}")
        print()
        
        # 检查Unit Price分布
        print("💰 Unit Price分布:")
        print(df['Unit Price'].value_counts().head(10))
        print()
        
        # 检查是否有异常的Unit Price
        unique_unit_prices = df['Unit Price'].unique()
        print(f"唯一Unit Price值: {sorted(unique_unit_prices)}")
        print()
        
        # 检查Quantity的异常值
        print("📦 Quantity统计:")
        print(f"最小值: {df['Quantity'].min():,.0f}")
        print(f"最大值: {df['Quantity'].max():,.0f}")
        print(f"平均值: {df['Quantity'].mean():,.0f}")
        print(f"中位数: {df['Quantity'].median():,.0f}")
        print()
        
        # 可能的问题分析
        print("🎯 可能的问题:")
        if equal_rows == 0:
            print("1. ❌ 没有任何行的Total Price等于Unit Price × Quantity")
            print("2. 🤔 可能数据源有问题，或者字段定义不同")
            print("3. 📊 Total Price可能包含了其他费用（税费、折扣等）")
            print("4. 💡 也可能是数据导出或处理过程中的错误")
        elif equal_rows < len(df) * 0.1:
            print("1. ⚠️  只有少数行的Total Price等于Unit Price × Quantity")
            print("2. 🤔 大部分数据可能有问题")
        else:
            print("1. ✅ 大部分行的Total Price等于Unit Price × Quantity")
            print("2. 🔍 需要检查异常行的原因")
        
        # 建议
        print()
        print("💡 建议:")
        print("1. 检查数据源的字段定义")
        print("2. 确认Total Price是否包含其他费用")
        print("3. 验证数据导出过程是否正确")
        print("4. 考虑使用Quantity × Unit Price作为真实销售金额")
        
        return True
        
    except Exception as e:
        print(f"❌ 调查失败: {e}")
        return False

if __name__ == "__main__":
    investigate_price_discrepancy()
