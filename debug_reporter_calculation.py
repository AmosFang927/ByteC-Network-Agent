#!/usr/bin/env python3
"""
调试reporter agent的计算逻辑，排查total sale amount数值问题
"""

import pandas as pd
import sys
import os

def debug_reporter_calculation():
    """调试reporter agent的计算逻辑"""
    
    # 读取DMP agent的输出文件
    file_path = 'output/Passthrough_all_00010101000000_00010101000000_395162191all_00010101000000_00010101000000_395162191_LS_BM_20250812_084805.xlsx'
    
    print(f"🔍 分析文件: {file_path}")
    
    try:
        # 读取Excel文件
        df = pd.read_excel(file_path, sheet_name='Data')
        print(f"📊 数据行数: {len(df)}")
        
        # 检查列名
        print(f"📋 列名: {list(df.columns)}")
        
        # 检查Partner分布
        print(f"\n📊 Partner分布:")
        print(df['Partner'].value_counts())
        
        # 检查Status分布
        print(f"\n📋 Status分布:")
        print(df['Status'].value_counts())
        
        # 模拟reporter agent的计算逻辑
        print(f"\n🔧 模拟Reporter Agent计算逻辑:")
        
        # 1. 计算所有记录的USD Sale Amount总和
        total_all_amount = df['USD Sale Amount'].sum()
        print(f"1. 所有记录USD Sale Amount总和: ${total_all_amount:,.2f}")
        
        # 2. 按Status过滤有效记录
        valid_statuses = ['pending', 'approved', 'approved_pending', 'processing', 'completed']
        valid_mask = df['Status'].str.lower().isin(valid_statuses)
        valid_df = df[valid_mask]
        
        print(f"2. 有效Status记录数: {len(valid_df)}")
        print(f"   有效Status记录USD Sale Amount总和: ${valid_df['USD Sale Amount'].sum():,.2f}")
        
        # 3. 按Partner分组计算
        print(f"\n3. 按Partner分组计算:")
        for partner in df['Partner'].unique():
            partner_df = df[df['Partner'] == partner]
            partner_valid_df = partner_df[valid_mask]
            
            print(f"   {partner}:")
            print(f"     总记录数: {len(partner_df)}")
            print(f"     有效记录数: {len(partner_valid_df)}")
            print(f"     总金额: ${partner_df['USD Sale Amount'].sum():,.2f}")
            print(f"     有效金额: ${partner_valid_df['USD Sale Amount'].sum():,.2f}")
            
            # 检查是否有mockup相关列
            mockup_cols = [col for col in partner_df.columns if 'mockup' in col.lower()]
            if mockup_cols:
                print(f"     Mockup相关列: {mockup_cols}")
        
        # 4. 检查是否有重复计算
        print(f"\n4. 检查数据完整性:")
        print(f"   总记录数: {len(df)}")
        print(f"   有效记录数: {len(valid_df)}")
        print(f"   无效记录数: {len(df) - len(valid_df)}")
        
        # 5. 检查金额分布
        print(f"\n5. 金额分布统计:")
        print(df['USD Sale Amount'].describe())
        
        # 6. 检查是否有异常值
        print(f"\n6. 检查异常值:")
        zero_amount = (df['USD Sale Amount'] == 0).sum()
        negative_amount = (df['USD Sale Amount'] < 0).sum()
        large_amount = (df['USD Sale Amount'] > 100).sum()
        
        print(f"   零金额记录: {zero_amount}")
        print(f"   负金额记录: {negative_amount}")
        print(f"   大金额记录(>100): {large_amount}")
        
        # 7. 检查config.py中的mockup multiplier
        print(f"\n7. 检查Mockup Multiplier配置:")
        try:
            import config
            partner = df['Partner'].iloc[0] if len(df) > 0 else 'Unknown'
            mockup_multiplier = config.get_partner_mockup_multiplier(partner)
            print(f"   {partner}的mockup multiplier: {mockup_multiplier}")
            
            # 计算mockup调整后的金额
            if mockup_multiplier != 1.0:
                adjusted_amount = total_all_amount * mockup_multiplier
                print(f"   Mockup调整后金额: ${adjusted_amount:,.2f}")
                print(f"   调整比例: {mockup_multiplier * 100}%")
        except Exception as e:
            print(f"   无法获取mockup multiplier: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        return False

if __name__ == "__main__":
    debug_reporter_calculation()
