#!/usr/bin/env python3
"""
检查原始数据中的金额字段
"""

import pandas as pd
import sys
import os

def check_original_data():
    """检查原始数据中的金额字段"""
    
    # 读取原始输入文件
    file_path = 'input/all_00010101000000_00010101000000_212137008_LS_BM.csv'
    
    print(f"🔍 检查原始数据: {file_path}")
    
    try:
        # 读取CSV文件
        df = pd.read_csv(file_path)
        print(f"📊 数据行数: {len(df)}")
        
        # 显示所有列名
        print(f"\n📋 所有列名:")
        for i, col in enumerate(df.columns):
            print(f"   {i+1:2d}. {col}")
        
        # 查找可能的金额字段
        amount_keywords = ['price', 'amount', 'commission', 'reward', 'fee', 'total']
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
        
        # 检查Order Status字段
        if 'Order Status' in df.columns:
            print(f"\n📋 Order Status字段分布:")
            print(df['Order Status'].value_counts())
        
        return True
        
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return False

if __name__ == "__main__":
    check_original_data()
