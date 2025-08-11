#!/usr/bin/env python3
"""
检查DMP Agent的输出和映射问题
"""

import pandas as pd
import sys
import os

def check_dmp_mapping():
    """检查DMP Agent的映射问题"""
    
    # 读取原始输入文件
    input_file = "output/Passthrough_ID-async-report-exporter-publisher_conversion-report-id-2025-08-05-4W5IzzDQGqxfM5wy_ALL_AT_BM_20250806_190807.xlsx"
    output_file = "output/at_bm_processed_20250806_191802.csv"
    
    print("🔍 检查DMP Agent映射问题...")
    
    try:
        # 读取输入文件
        input_df = pd.read_excel(input_file, nrows=3)
        print(f"✅ 输入文件列数: {len(input_df.columns)}")
        print(f"✅ 输入文件行数: {len(input_df)}")
        
        # 检查关键字段
        print("\n📋 输入文件关键字段:")
        key_fields = ['Partner', 'Source', 'Platform', 'Total Price', 'Reward', 'Conversion ID', 'Site']
        for field in key_fields:
            if field in input_df.columns:
                values = input_df[field].head(3).tolist()
                print(f"   ✅ {field}: {values}")
            else:
                print(f"   ❌ {field}: 不存在")
        
        # 读取输出文件
        output_df = pd.read_csv(output_file, nrows=3)
        print(f"\n✅ 输出文件列数: {len(output_df.columns)}")
        print(f"✅ 输出文件行数: {len(output_df)}")
        
        # 检查输出文件的关键字段
        print("\n📋 输出文件关键字段:")
        output_key_fields = ['conversion_id', 'sale_amount', 'payout', 'platform', 'advertiser_name', 'campaign_name']
        for field in output_key_fields:
            if field in output_df.columns:
                values = output_df[field].head(3).tolist()
                print(f"   ✅ {field}: {values}")
            else:
                print(f"   ❌ {field}: 不存在")
        
        # 检查字段映射关系
        print("\n🔧 字段映射分析:")
        
        # 检查Conversion ID映射
        if 'Conversion ID' in input_df.columns and 'conversion_id' in output_df.columns:
            print(f"   Conversion ID -> conversion_id: {input_df['Conversion ID'].iloc[0]} -> {output_df['conversion_id'].iloc[0]}")
        
        # 检查Total Price映射
        if 'Total Price' in input_df.columns and 'sale_amount' in output_df.columns:
            print(f"   Total Price -> sale_amount: {input_df['Total Price'].iloc[0]} -> {output_df['sale_amount'].iloc[0]}")
        
        # 检查Reward映射
        if 'Reward' in input_df.columns and 'payout' in output_df.columns:
            print(f"   Reward -> payout: {input_df['Reward'].iloc[0]} -> {output_df['payout'].iloc[0]}")
        
        # 检查Site映射
        if 'Site' in input_df.columns and 'advertiser_name' in output_df.columns:
            print(f"   Site -> advertiser_name: {input_df['Site'].iloc[0]} -> {output_df['advertiser_name'].iloc[0]}")
        
        # 检查Campaign Name映射
        if 'Campaign Name' in input_df.columns and 'campaign_name' in output_df.columns:
            print(f"   Campaign Name -> campaign_name: {input_df['Campaign Name'].iloc[0]} -> {output_df['campaign_name'].iloc[0]}")
        
        # 检查Platform映射
        if 'Platform' in input_df.columns and 'platform' in output_df.columns:
            print(f"   Platform -> platform: {input_df['Platform'].iloc[0]} -> {output_df['platform'].iloc[0]}")
        
        # 检查Partner映射
        if 'Partner' in input_df.columns:
            print(f"   Partner: {input_df['Partner'].iloc[0]}")
        
        # 检查Source映射
        if 'Source' in input_df.columns:
            print(f"   Source: {input_df['Source'].iloc[0]}")
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")

if __name__ == "__main__":
    check_dmp_mapping() 