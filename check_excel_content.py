#!/usr/bin/env python3
"""
检查Reporter Agent生成的Excel文件内容
"""
import pandas as pd

def check_excel_file(file_path):
    print(f"📊 检查文件: {file_path}")
    
    try:
        # 读取Excel文件
        xl_file = pd.ExcelFile(file_path)
        print(f"📋 发现sheets: {xl_file.sheet_names}")
        
        for sheet_name in xl_file.sheet_names:
            print(f"\n🔍 分析sheet: {sheet_name}")
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            print(f"   行数: {len(df)}")
            print(f"   列数: {len(df.columns)}")
            
            if len(df) > 0:
                print(f"   列名: {list(df.columns)}")
                
                # 检查USD Sale Amount列
                if 'USD Sale Amount' in df.columns:
                    total_amount = df['USD Sale Amount'].sum()
                    print(f"   💰 USD Sale Amount总和: ${total_amount:,.2f}")
                    
                    # 显示前几行数据
                    print(f"   📝 前5行USD Sale Amount:")
                    print(df['USD Sale Amount'].head().tolist())
                
                # 检查Partner列
                if 'Partner' in df.columns:
                    partner_counts = df['Partner'].value_counts()
                    print(f"   👥 Partner分布:")
                    for partner, count in partner_counts.items():
                        print(f"      {partner}: {count} 条记录")
            else:
                print("   ⚠️ Sheet为空")
    
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")

if __name__ == "__main__":
    file_path = "output/DeepLeaper_ConversionReport_2025-08-05_to_2025-08-10.xlsx"
    check_excel_file(file_path)

