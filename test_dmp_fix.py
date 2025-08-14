#!/usr/bin/env python3
"""
测试DMP Agent修复后的CSV读取效果
"""

import sys
import os
import pandas as pd

# 添加项目路径
sys.path.append('/Users/amosfang/ByteC-Network-Agent-main')

def test_at_bm_processor():
    """测试修复后的AT_BM处理器"""
    
    print("🧪 测试修复后的AT_BM处理器")
    print()
    
    try:
        from agents.data_dmp_agent.at_bm_data_processor import ATBMDataProcessor
        
        # 初始化处理器
        processor = ATBMDataProcessor()
        
        # 测试文件
        file_path = 'input/ID-async-report-exporter-publisher_conversion-report-id-2025-08-12-18nRimTm4Z1hBMXZ_0805-0810_DeepLeaper_AT_BM.csv'
        
        print(f"📁 测试文件: {file_path}")
        
        # 直接测试CSV读取
        print("1. 测试直接CSV读取 (utf-8-sig):")
        df_fixed = pd.read_csv(file_path, encoding='utf-8-sig')
        
        print(f"   数据行数: {len(df_fixed)}")
        print(f"   列数: {len(df_fixed.columns)}")
        
        # 检查第一行数据
        first_row = df_fixed.iloc[0]
        up = first_row['Unit Price']
        qty = first_row['Quantity']
        tp = first_row['Total Price']
        
        print(f"   第一行: Unit Price={up}, Quantity={qty}, Total Price={tp}")
        print(f"   验证: {up} × {qty} = {up * qty}, Total Price = {tp}, 相等: {tp == up * qty}")
        
        # 计算总和
        total_price_sum = df_fixed['Total Price'].sum()
        print(f"   ✅ Total Price总和: {total_price_sum:,.0f} IDR")
        
        # 货币转换
        usd_amount = total_price_sum / 15400
        adjusted_usd = usd_amount * 0.7
        print(f"   ✅ USD转换: ${usd_amount:,.2f}")
        print(f"   ✅ DeepLeaper调整: ${adjusted_usd:,.2f}")
        
        print()
        print("2. 与旧方法对比:")
        df_old = pd.read_csv(file_path, encoding='utf-8')
        old_total = df_old['Total Price'].sum()
        print(f"   旧方法Total Price总和: {old_total:,.0f} IDR")
        print(f"   新方法Total Price总和: {total_price_sum:,.0f} IDR")
        print(f"   差异: {total_price_sum - old_total:,.0f} IDR")
        
        if total_price_sum > old_total:
            print("   ✅ 修复成功！新方法读取的数值更大且正确")
        else:
            print("   ❌ 修复可能有问题")
            
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    test_at_bm_processor()

