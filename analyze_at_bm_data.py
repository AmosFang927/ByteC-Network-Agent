#!/usr/bin/env python3
"""
分析AT_BM输入数据，找出货币转换问题
"""

import pandas as pd
import sys
import os

def analyze_at_bm_data():
    """分析AT_BM输入数据"""
    
    # 查找AT_BM输入文件
    input_dir = "input"
    at_bm_files = []
    
    for file in os.listdir(input_dir):
        if "AT_BM" in file and file.endswith(".csv"):
            file_path = os.path.join(input_dir, file)
            at_bm_files.append((file_path, os.path.getmtime(file_path)))
    
    if not at_bm_files:
        print("❌ 未找到AT_BM输入文件")
        return False
    
    # 按修改时间排序，获取最新文件
    at_bm_files.sort(key=lambda x: x[1], reverse=True)
    latest_file = at_bm_files[0][0]
    
    print(f"🔍 分析AT_BM文件: {latest_file}")
    
    try:
        # 读取CSV文件
        df = pd.read_csv(latest_file)
        print(f"📊 数据行数: {len(df)}")
        
        # 显示所有列名
        print(f"\n📋 所有列名:")
        for i, col in enumerate(df.columns):
            print(f"   {i+1:2d}. {col}")
        
        # 查找可能的金额字段
        amount_keywords = ['price', 'amount', 'commission', 'reward', 'fee', 'total', 'payout']
        amount_cols = []
        
        for col in df.columns:
            col_lower = col.lower()
            for keyword in amount_keywords:
                if keyword in col_lower:
                    amount_cols.append(col)
                    break
        
        print(f"\n💰 可能的金额字段: {amount_cols}")
        
        # 检查每个金额字段的统计
        for col in amount_cols:
            try:
                # 转换为数值类型
                numeric_col = pd.to_numeric(df[col], errors='coerce')
                total = numeric_col.sum()
                non_null_count = numeric_col.count()
                null_count = numeric_col.isnull().sum()
                
                print(f"\n📊 {col}:")
                print(f"   总和: {total:,.2f}")
                print(f"   非空值数量: {non_null_count}")
                print(f"   空值数量: {null_count}")
                
                if non_null_count > 0:
                    print(f"   平均值: {numeric_col.mean():,.2f}")
                    print(f"   最大值: {numeric_col.max():,.2f}")
                    print(f"   最小值: {numeric_col.min():,.2f}")
                    
                    # 显示前几个非零值
                    non_zero = numeric_col[numeric_col > 0]
                    if len(non_zero) > 0:
                        print(f"   前5个非零值: {non_zero.head().tolist()}")
                
            except Exception as e:
                print(f"   ❌ 处理失败: {e}")
        
        # 检查Currency字段
        if 'Currency' in df.columns:
            print(f"\n💱 Currency字段分布:")
            print(df['Currency'].value_counts())
        
        # 检查Status字段
        if 'Status' in df.columns:
            print(f"\n📋 Status字段分布:")
            print(df['Status'].value_counts())
        
        # 检查aff_sub字段
        aff_sub_cols = [col for col in df.columns if 'aff_sub' in col.lower()]
        if aff_sub_cols:
            print(f"\n🔗 aff_sub相关字段: {aff_sub_cols}")
            for col in aff_sub_cols:
                unique_vals = df[col].value_counts()
                print(f"   {col} 分布: {unique_vals.head().to_dict()}")
        
        # 重点检查Total Price字段（AT_BM的主要金额字段）
        if 'Total Price' in df.columns:
            total_price = pd.to_numeric(df['Total Price'], errors='coerce')
            total_idr = total_price.sum()
            print(f"\n🎯 重点分析 Total Price 字段:")
            print(f"   Total Price总和: {total_idr:,.0f} IDR")
            
            # 计算预期的USD转换
            idr_to_usd_rate = 0.000065  # 1 IDR = 0.000065 USD
            expected_usd = total_idr * idr_to_usd_rate
            print(f"   预期USD转换 (汇率 {idr_to_usd_rate}): ${expected_usd:,.2f}")
            
            # 使用另一种汇率计算
            usd_to_idr_rate = 15400.0  # 1 USD = 15400 IDR
            expected_usd_alt = total_idr / usd_to_idr_rate
            print(f"   预期USD转换 (汇率 1/{usd_to_idr_rate}): ${expected_usd_alt:,.2f}")
            
            # 应用DeepLeaper的mockup multiplier
            try:
                import config
                mockup_multiplier = config.get_partner_mockup_multiplier('DEEPLEAPER')
                adjusted_usd = expected_usd_alt * mockup_multiplier
                print(f"   DeepLeaper Mockup调整后 ({mockup_multiplier}): ${adjusted_usd:,.2f}")
            except Exception as e:
                print(f"   无法获取mockup multiplier: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return False

if __name__ == "__main__":
    analyze_at_bm_data()

