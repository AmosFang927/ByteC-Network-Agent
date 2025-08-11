#!/usr/bin/env python3
"""
检查数据输入代理生成的输出文件
"""

import pandas as pd
import sys
import os

def check_output_file():
    """检查输出文件"""
    output_file = "output/Passthrough_ID-async-report-exporter-publisher_conversion-report-id-2025-08-05-4W5IzzDQGqxfM5wy_ALL_AT_BM_20250806_190807.xlsx"
    
    print(f"📂 检查输出文件: {output_file}")
    
    try:
        # 读取输出文件
        df = pd.read_excel(output_file, nrows=5)
        print(f"✅ 输出文件列数: {len(df.columns)}")
        print(f"✅ 输出文件行数: {len(df)}")
        
        # 检查关键字段
        print("\n📋 检查关键字段:")
        key_fields = ['Partner', 'Source', 'Platform', 'Total Price', 'Reward']
        for field in key_fields:
            if field in df.columns:
                print(f"   ✅ {field}: 存在")
                values = df[field].head(3).tolist()
                print(f"      样本值: {values}")
            else:
                print(f"   ❌ {field}: 不存在")
        
        # 检查包含特定关键词的列
        print("\n🔍 检查包含关键词的列:")
        keywords = ['partner', 'source', 'platform', 'price', 'reward']
        for keyword in keywords:
            matching_cols = [col for col in df.columns if keyword in col.lower()]
            if matching_cols:
                print(f"   {keyword.upper()}: {matching_cols}")
            else:
                print(f"   {keyword.upper()}: 无匹配列")
        
        # 显示所有列名
        print("\n📋 所有列名:")
        for i, col in enumerate(df.columns):
            print(f"   {i+1:2d}. {col}")
        
        # 显示前3行数据的关键信息
        print("\n📊 前3行数据的关键信息:")
        for i in range(min(3, len(df))):
            print(f"   行 {i+1}:")
            for field in key_fields:
                if field in df.columns:
                    value = df[field].iloc[i]
                    print(f"     {field}: {value}")
        
    except Exception as e:
        print(f"❌ 读取输出文件失败: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")

if __name__ == "__main__":
    check_output_file() 