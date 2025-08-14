#!/usr/bin/env python3
"""
调试DMP agent的AT_BM处理过程
"""

import pandas as pd
import sys
import os

def debug_dmp_processing():
    """调试DMP处理过程"""
    
    print("🔍 调试DMP agent的AT_BM处理过程")
    
    # 1. 检查原始AT_BM输入
    at_bm_file = "input/ID-async-report-exporter-publisher_conversion-report-id-2025-08-12-18nRimTm4Z1hBMXZ_0805-0810_DeepLeaper_AT_BM.csv"
    
    print(f"\n1. 原始AT_BM输入文件: {at_bm_file}")
    
    try:
        df_input = pd.read_csv(at_bm_file)
        print(f"   输入数据行数: {len(df_input)}")
        
        # 检查Total Price
        total_price_input = pd.to_numeric(df_input['Total Price'], errors='coerce').sum()
        print(f"   原始Total Price总和: {total_price_input:,.0f} IDR")
        
        # 检查Status字段的问题
        print(f"   Status字段样例: {df_input['Status'].head().tolist()}")
        
        # 检查aff_sub字段
        print(f"   aff_sub字段样例: {df_input['aff_sub'].head().tolist()}")
        
    except Exception as e:
        print(f"   ❌ 读取输入文件失败: {e}")
    
    # 2. 检查DMP agent输出
    print(f"\n2. DMP agent输出文件:")
    
    output_dir = "output"
    at_bm_output_files = []
    
    for file in os.listdir(output_dir):
        if "AT_BM" in file and file.endswith(".xlsx") and "Passthrough" in file:
            file_path = os.path.join(output_dir, file)
            at_bm_output_files.append((file_path, os.path.getmtime(file_path)))
    
    if at_bm_output_files:
        # 按修改时间排序，获取最新文件
        at_bm_output_files.sort(key=lambda x: x[1], reverse=True)
        latest_output = at_bm_output_files[0][0]
        
        print(f"   最新输出文件: {latest_output}")
        
        try:
            # 读取输出Excel文件
            df_output = pd.read_excel(latest_output, sheet_name='Data')
            print(f"   输出数据行数: {len(df_output)}")
            print(f"   输出列名: {list(df_output.columns)}")
            
            if 'USD Sale Amount' in df_output.columns:
                usd_total = df_output['USD Sale Amount'].sum()
                print(f"   USD Sale Amount总和: ${usd_total:,.2f}")
                
                # 检查Status分布
                if 'Status' in df_output.columns:
                    status_counts = df_output['Status'].value_counts()
                    print(f"   Status分布: {status_counts.head().to_dict()}")
                
                # 检查Partner分布
                if 'Partner' in df_output.columns:
                    partner_counts = df_output['Partner'].value_counts()
                    print(f"   Partner分布: {partner_counts.to_dict()}")
                
                # 检查是否有Local Sale Amount
                if 'Local Sale Amount' in df_output.columns:
                    local_total = df_output['Local Sale Amount'].sum()
                    print(f"   Local Sale Amount总和: {local_total:,.0f} IDR")
                    
                    # 计算实际汇率
                    if local_total > 0 and usd_total > 0:
                        actual_rate = local_total / usd_total
                        print(f"   实际汇率: 1 USD = {actual_rate:,.2f} IDR")
                
                # 按Status过滤有效记录
                if 'Status' in df_output.columns:
                    valid_statuses = ['processing', 'completed', 'pending', 'approved']
                    valid_mask = df_output['Status'].str.lower().isin(valid_statuses)
                    valid_df = df_output[valid_mask]
                    
                    print(f"   有效记录数: {len(valid_df)}")
                    print(f"   有效记录USD Sale Amount总和: ${valid_df['USD Sale Amount'].sum():,.2f}")
                
        except Exception as e:
            print(f"   ❌ 读取输出文件失败: {e}")
    else:
        print("   未找到AT_BM输出文件")
    
    # 3. 计算预期值与实际值的对比
    print(f"\n3. 数值对比分析:")
    print(f"   原始Total Price: 66,026,755 IDR")
    print(f"   预期USD (15400汇率): ${66026755/15400:,.2f}")
    print(f"   DeepLeaper调整 (0.7倍): ${(66026755/15400)*0.7:,.2f}")
    print(f"   Reporter显示: $5,552.04")
    print(f"   差异: ${5552.04 - (66026755/15400)*0.7:+,.2f}")
    
    # 4. 可能的问题分析
    print(f"\n4. 可能的问题:")
    print("   1. Status字段包含时间戳而非状态值，可能导致数据过滤错误")
    print("   2. 货币转换可能被重复应用")
    print("   3. Mockup multiplier可能被错误应用")
    print("   4. 数据可能被重复处理或合并")

if __name__ == "__main__":
    debug_dmp_processing()

