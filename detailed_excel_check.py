#!/usr/bin/env python3
"""
详细检查Excel文件的内容和结构
"""
import pandas as pd

def detailed_check():
    file_path = "output/DeepLeaper_ConversionReport_2025-08-05_to_2025-08-10.xlsx"
    
    try:
        # 读取DeepLeaper sheet
        print("📊 详细检查DeepLeaper sheet...")
        df = pd.read_excel(file_path, sheet_name='DeepLeaper', header=None)
        
        print(f"原始数据形状: {df.shape}")
        print("\n前10行前5列:")
        print(df.iloc[:10, :5])
        
        print("\n检查是否有表头行...")
        # 查找可能的表头
        for i in range(min(20, len(df))):
            row = df.iloc[i]
            if any('USD Sale Amount' in str(cell) for cell in row if pd.notna(cell)):
                print(f"在第{i}行找到表头相关信息:")
                print(row.tolist())
                break
        
        # 尝试寻找数字数据
        print("\n寻找数字数据...")
        for i in range(min(50, len(df))):
            row = df.iloc[i]
            numeric_count = sum(1 for cell in row if pd.notna(cell) and str(cell).replace('.', '').replace('-', '').isdigit())
            if numeric_count > 5:
                print(f"第{i}行包含{numeric_count}个数字字段:")
                print([cell for cell in row if pd.notna(cell)][:10])
                break
        
        # 检查是否包含Partner信息
        print("\n检查Partner信息...")
        found_partner = False
        for i in range(min(100, len(df))):
            row = df.iloc[i]
            for cell in row:
                if pd.notna(cell) and 'DeepLeaper' in str(cell):
                    print(f"在第{i}行找到DeepLeaper: {cell}")
                    found_partner = True
                    break
            if found_partner:
                break
                
    except Exception as e:
        print(f"❌ 检查失败: {e}")

if __name__ == "__main__":
    detailed_check()

