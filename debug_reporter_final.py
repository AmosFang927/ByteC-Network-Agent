#!/usr/bin/env python3
"""
调试reporter agent的最终计算逻辑，找出$5,552.04的来源
"""

import pandas as pd
import sys
import os

def debug_reporter_final_calculation():
    """调试reporter agent的最终计算逻辑"""
    
    # 读取DMP agent的输出文件
    file_path = 'output/Passthrough_all_00010101000000_00010101000000_395162191all_00010101000000_00010101000000_395162191_LS_BM_20250812_084805.xlsx'
    
    print(f"🔍 分析文件: {file_path}")
    
    try:
        # 读取Excel文件
        df = pd.read_excel(file_path, sheet_name='Data')
        print(f"📊 数据行数: {len(df)}")
        
        # 检查是否有mockup相关列
        mockup_cols = [col for col in df.columns if 'mockup' in col.lower()]
        print(f"🔧 Mockup相关列: {mockup_cols}")
        
        # 检查是否有original_usd_sale_amount列
        if 'original_usd_sale_amount' in df.columns:
            print(f"📊 原始USD Sale Amount总和: ${df['original_usd_sale_amount'].sum():,.2f}")
            print(f"📊 当前USD Sale Amount总和: ${df['USD Sale Amount'].sum():,.2f}")
        
        # 模拟reporter agent的计算逻辑
        print(f"\n🔧 模拟Reporter Agent最终计算逻辑:")
        
        # 1. 按Status过滤有效记录
        valid_statuses = ['pending', 'approved', 'approved_pending', 'processing', 'completed']
        valid_mask = df['Status'].str.lower().isin(valid_statuses)
        valid_df = df[valid_mask]
        
        print(f"1. 有效Status记录数: {len(valid_df)}")
        print(f"   有效Status记录USD Sale Amount总和: ${valid_df['USD Sale Amount'].sum():,.2f}")
        
        # 2. 按Partner分组计算
        print(f"\n2. 按Partner分组计算:")
        for partner in df['Partner'].unique():
            partner_df = df[df['Partner'] == partner]
            partner_valid_df = partner_df[valid_mask]
            
            print(f"   {partner}:")
            print(f"     总记录数: {len(partner_df)}")
            print(f"     有效记录数: {len(partner_valid_df)}")
            print(f"     总金额: ${partner_df['USD Sale Amount'].sum():,.2f}")
            print(f"     有效金额: ${partner_valid_df['USD Sale Amount'].sum():,.2f}")
            
            # 检查是否有mockup相关列
            if 'mockup_applied' in partner_df.columns:
                mockup_applied_count = partner_df['mockup_applied'].sum()
                print(f"     Mockup已应用记录数: {mockup_applied_count}")
            
            if 'mockup_multiplier' in partner_df.columns:
                multiplier = partner_df['mockup_multiplier'].iloc[0]
                print(f"     Mockup倍数: {multiplier}")
        
        # 3. 检查是否有重复计算或遗漏
        print(f"\n3. 检查数据完整性:")
        print(f"   总记录数: {len(df)}")
        print(f"   有效记录数: {len(valid_df)}")
        print(f"   无效记录数: {len(df) - len(valid_df)}")
        
        # 4. 检查金额分布
        print(f"\n4. 金额分布统计:")
        print(df['USD Sale Amount'].describe())
        
        # 5. 检查是否有异常值
        print(f"\n5. 检查异常值:")
        zero_amount = (df['USD Sale Amount'] == 0).sum()
        negative_amount = (df['USD Sale Amount'] < 0).sum()
        large_amount = (df['USD Sale Amount'] > 100).sum()
        
        print(f"   零金额记录: {zero_amount}")
        print(f"   负金额记录: {negative_amount}")
        print(f"   大金额记录(>100): {large_amount}")
        
        # 6. 检查是否有重复记录
        print(f"\n6. 检查重复记录:")
        duplicate_conversion_ids = df['Conversion ID'].duplicated().sum()
        print(f"   重复Conversion ID记录: {duplicate_conversion_ids}")
        
        # 7. 检查是否有数据截断
        print(f"\n7. 检查数据截断:")
        # 检查是否有数据被截断到$5,552.04
        target_amount = 5552.04
        if abs(valid_df['USD Sale Amount'].sum() - target_amount) < 0.01:
            print(f"   ⚠️ 发现目标金额: ${target_amount:,.2f}")
        else:
            print(f"   ✅ 未发现目标金额，当前有效金额: ${valid_df['USD Sale Amount'].sum():,.2f}")
        
        # 8. 检查是否有其他文件影响
        print(f"\n8. 检查其他文件:")
        output_dir = "output"
        ls_bm_files = []
        
        for file in os.listdir(output_dir):
            if "LS_BM" in file and file.endswith(".xlsx") and "Passthrough" in file:
                file_path = os.path.join(output_dir, file)
                ls_bm_files.append((file_path, os.path.getmtime(file_path)))
        
        if len(ls_bm_files) > 1:
            print(f"   发现多个LS_BM文件:")
            for file_path, mtime in ls_bm_files:
                print(f"     {file_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        return False

if __name__ == "__main__":
    debug_reporter_final_calculation()
