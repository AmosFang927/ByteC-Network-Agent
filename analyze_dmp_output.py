#!/usr/bin/env python3
"""
分析DMP agent输出文件，排查total sale amount数值问题
"""

import pandas as pd
import sys
import os

def analyze_dmp_output(file_path):
    """分析DMP agent输出文件"""
    print(f"🔍 分析文件: {file_path}")
    
    try:
        # 读取Excel文件
        excel_file = pd.ExcelFile(file_path)
        print(f"📊 Excel文件包含的sheet: {excel_file.sheet_names}")
        
        # 读取第一个sheet
        df = pd.read_excel(file_path, sheet_name=excel_file.sheet_names[0])
        print(f"\n📋 第一个sheet的列名: {list(df.columns)}")
        print(f"📊 数据行数: {len(df)}")
        
        # 查找金额相关列
        amount_cols = [col for col in df.columns if 'amount' in col.lower() or 'sale' in col.lower()]
        print(f"\n💰 金额相关列: {amount_cols}")
        
        # 显示前几行数据
        print(f"\n📄 前5行数据:")
        print(df.head())
        
        # 如果有USD Sale Amount列，计算总和
        if 'USD Sale Amount' in df.columns:
            total_amount = df['USD Sale Amount'].sum()
            print(f"\n💰 USD Sale Amount总和: ${total_amount:,.2f}")
            
            # 显示金额分布
            print(f"\n📊 金额统计:")
            print(df['USD Sale Amount'].describe())
            
            # 检查是否有Partner列
            if 'Partner' in df.columns:
                partner_stats = df.groupby('Partner')['USD Sale Amount'].agg(['sum', 'count'])
                print(f"\n📊 按Partner分组统计:")
                print(partner_stats)
                
                # 检查是否有mockup相关列
                mockup_cols = [col for col in df.columns if 'mockup' in col.lower()]
                if mockup_cols:
                    print(f"\n🔧 Mockup相关列: {mockup_cols}")
                    for col in mockup_cols:
                        print(f"   {col}: {df[col].unique()}")
        
        # 检查Local Sale Amount列（如果有）
        if 'Local Sale Amount' in df.columns:
            local_total = df['Local Sale Amount'].sum()
            print(f"\n💱 Local Sale Amount总和: {local_total:,.2f}")
            
            # 计算汇率
            if 'USD Sale Amount' in df.columns:
                usd_total = df['USD Sale Amount'].sum()
                if local_total > 0:
                    rate = usd_total / local_total
                    print(f"💱 实际汇率: 1 USD = {1/rate:,.2f} Local Currency")
        
        # 检查Status列
        if 'Status' in df.columns:
            status_counts = df['Status'].value_counts()
            print(f"\n📋 Status分布:")
            print(status_counts)
        
        return True
        
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return False

def main():
    """主函数"""
    # 查找最新的DMP输出文件
    output_dir = "output"
    ls_bm_files = []
    
    for file in os.listdir(output_dir):
        if "LS_BM" in file and file.endswith(".xlsx") and "Passthrough" in file:
            file_path = os.path.join(output_dir, file)
            ls_bm_files.append((file_path, os.path.getmtime(file_path)))
    
    if not ls_bm_files:
        print("❌ 未找到LS_BM输出文件")
        return
    
    # 按修改时间排序，获取最新文件
    ls_bm_files.sort(key=lambda x: x[1], reverse=True)
    latest_file = ls_bm_files[0][0]
    
    print(f"🎯 分析最新的DMP输出文件: {latest_file}")
    analyze_dmp_output(latest_file)

if __name__ == "__main__":
    main()
