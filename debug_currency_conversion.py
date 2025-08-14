#!/usr/bin/env python3
"""
调试货币转换问题，分析IDR到USD的转换
"""

import pandas as pd
import sys
import os

def debug_currency_conversion():
    """调试货币转换问题"""
    
    print("🔍 调试货币转换问题")
    
    # 1. 检查原始输入文件
    print("\n1. 检查原始输入文件:")
    input_dir = "input"
    ls_bm_files = []
    
    for file in os.listdir(input_dir):
        if "LS_BM" in file and file.endswith(".csv"):
            file_path = os.path.join(input_dir, file)
            ls_bm_files.append((file_path, os.path.getmtime(file_path)))
    
    if ls_bm_files:
        # 按修改时间排序，获取最新文件
        ls_bm_files.sort(key=lambda x: x[1], reverse=True)
        latest_file = ls_bm_files[0][0]
        
        print(f"   最新输入文件: {latest_file}")
        
        try:
            # 读取原始CSV文件
            df = pd.read_csv(latest_file)
            print(f"   数据行数: {len(df)}")
            print(f"   列名: {list(df.columns)}")
            
            # 查找金额相关列
            amount_cols = [col for col in df.columns if 'amount' in col.lower() or 'sale' in col.lower()]
            print(f"   金额相关列: {amount_cols}")
            
            # 检查Local Sale Amount
            if 'Local Sale Amount' in df.columns:
                local_total = df['Local Sale Amount'].sum()
                print(f"   Local Sale Amount总和: {local_total:,.0f} IDR")
                
                # 计算预期的USD转换
                idr_to_usd_rate = 0.000065  # 1 IDR = 0.000065 USD
                expected_usd = local_total * idr_to_usd_rate
                print(f"   预期USD转换 (汇率 {idr_to_usd_rate}): ${expected_usd:,.2f}")
                
                # 使用另一种汇率计算
                usd_to_idr_rate = 15400.0  # 1 USD = 15400 IDR
                expected_usd_alt = local_total / usd_to_idr_rate
                print(f"   预期USD转换 (汇率 1/{usd_to_idr_rate}): ${expected_usd_alt:,.2f}")
                
            elif 'sale_amount' in df.columns:
                sale_total = df['sale_amount'].sum()
                print(f"   sale_amount总和: {sale_total:,.2f}")
                
        except Exception as e:
            print(f"   读取输入文件失败: {e}")
    else:
        print("   未找到LS_BM输入文件")
    
    # 2. 检查DMP agent输出文件
    print("\n2. 检查DMP agent输出文件:")
    output_dir = "output"
    output_files = []
    
    for file in os.listdir(output_dir):
        if "LS_BM" in file and file.endswith(".xlsx") and "Passthrough" in file:
            file_path = os.path.join(output_dir, file)
            output_files.append((file_path, os.path.getmtime(file_path)))
    
    if output_files:
        # 按修改时间排序，获取最新文件
        output_files.sort(key=lambda x: x[1], reverse=True)
        latest_output = output_files[0][0]
        
        print(f"   最新输出文件: {latest_output}")
        
        try:
            # 读取输出Excel文件
            df = pd.read_excel(latest_output, sheet_name='Data')
            print(f"   数据行数: {len(df)}")
            
            if 'USD Sale Amount' in df.columns:
                usd_total = df['USD Sale Amount'].sum()
                print(f"   USD Sale Amount总和: ${usd_total:,.2f}")
                
                # 检查是否有Local Sale Amount字段
                if 'Local Sale Amount' in df.columns:
                    local_total = df['Local Sale Amount'].sum()
                    print(f"   Local Sale Amount总和: {local_total:,.0f} IDR")
                    
                    # 计算实际汇率
                    if local_total > 0:
                        actual_rate = usd_total / local_total
                        print(f"   实际汇率: 1 USD = {1/actual_rate:,.2f} IDR")
                        print(f"   实际汇率: 1 IDR = {actual_rate:.8f} USD")
                
        except Exception as e:
            print(f"   读取输出文件失败: {e}")
    else:
        print("   未找到LS_BM输出文件")
    
    # 3. 检查货币转换器配置
    print("\n3. 检查货币转换器配置:")
    try:
        from agents.data_dmp_agent.currency_converter import currency_converter
        
        # 测试IDR到USD转换
        test_idr = 6000000000
        converted_usd = currency_converter.convert_idr_to_usd(test_idr)
        print(f"   测试转换: {test_idr:,.0f} IDR → ${converted_usd:,.2f} USD")
        
        # 获取汇率
        rate = currency_converter.get_exchange_rate('IDR', 'USD')
        print(f"   当前汇率: 1 IDR = {rate:.8f} USD")
        print(f"   当前汇率: 1 USD = {1/rate:,.2f} IDR")
        
    except Exception as e:
        print(f"   检查货币转换器失败: {e}")
    
    # 4. 分析问题
    print("\n4. 问题分析:")
    print("   如果原始Local Sale Amount是6,000,000,000 IDR:")
    print("   - 使用汇率 1 USD = 15,400 IDR: 6,000,000,000 ÷ 15,400 = $389,610.39")
    print("   - 使用汇率 1 IDR = 0.000065 USD: 6,000,000,000 × 0.000065 = $390,000.00")
    print("   - Reporter agent显示: $5,552.04")
    print("   - 差异巨大，可能存在以下问题:")
    print("     1. 货币转换过程中出现错误")
    print("     2. 数据被重复处理或截断")
    print("     3. Mockup multiplier被错误应用")
    print("     4. 汇率设置不正确")

if __name__ == "__main__":
    debug_currency_conversion()
