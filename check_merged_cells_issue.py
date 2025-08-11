#!/usr/bin/env python3
"""
檢查Google Sheets合併單元格問題的診斷腳本
專門針對AT_BM平台配置的合併單元格處理
"""

import sys
import os
sys.path.append('/Users/amosfang/ByteC-Network-Agent-main')

from agents.data_dmp_agent.google_sheets_manager import GoogleSheetsManager
import pandas as pd
import json

def main():
    print("🔍 正在檢查Google Sheets合併單元格問題...")
    
    try:
        # 1. 初始化Google Sheets管理器
        sheets_manager = GoogleSheetsManager()
        
        print("\n📊 正在讀取原始Google Sheets數據...")
        
        # 2. 直接使用gspread檢查原始數據
        print("\n🔄 使用gspread直接讀取Google Sheets...")
        
        try:
            import gspread
            gc = gspread.service_account(filename='solar-idea-463423-h8-bd12ec2c5361.json')
            sheet = gc.open_by_key('1SaHZ0igiuMBm2gHFD5JSs1hkltphdXqRAlbaZ9nEUf0').worksheet('Data_Input_Mapping')
            
            # 獲取所有值
            all_values = sheet.get_all_values()
            print(f"原始數據行數: {len(all_values)}")
            
            # 3. 詳細檢查每一行數據
            print("\n🔎 詳細檢查每一行原始數據:")
            for i, row in enumerate(all_values):
                print(f"第{i+1}行: {row}")
                if len(row) > 0 and 'AT_BM' in str(row[0]).upper():
                    print(f"  ⚠️  發現AT_BM相關行: {row}")
        except Exception as e:
            print(f"❌ 使用gspread讀取時出錯: {e}")
            return
        
        # 4. 檢查解析後的數據
        print("\n📋 檢查解析後的平台配置:")
        try:
            field_mappings = sheets_manager.get_field_mappings()
            platforms = field_mappings.get('platforms', {})
            
            print(f"發現平台數量: {len(platforms)}")
            for platform_name, config in platforms.items():
                print(f"\n平台: {platform_name}")
                print(f"  字段映射數量: {len(config.get('field_mappings', {}))}")
                if platform_name.upper() == 'AT_BM':
                    print(f"  ✅ 找到AT_BM配置:")
                    for field, mapping in config.get('field_mappings', {}).items():
                        print(f"    {field} -> {mapping}")
        
        except Exception as e:
            print(f"❌ 解析配置時出錯: {e}")
            import traceback
            traceback.print_exc()
        
        # 5. 檢查特定的合併單元格模式
        print("\n🔍 檢查可能的合併單元格模式:")
        
        # 查看是否有空行或不完整的行
        for i, row in enumerate(all_values):
            if len(row) == 0:
                print(f"第{i+1}行: 空行")
            elif len(row) < 3:  # 假設正常行應該有3列以上
                print(f"第{i+1}行: 不完整的行 {row}")
            elif any('AT_BM' in str(cell).upper() for cell in row):
                print(f"第{i+1}行: 包含AT_BM的行 {row}")
        
        # 6. 查找包含AT_BM的所有單元格
        print("\n🎯 查找所有包含AT_BM的單元格:")
        
        at_bm_rows = []
        for i, row in enumerate(all_values):
            for j, cell in enumerate(row):
                if 'AT_BM' in str(cell).upper():
                    at_bm_rows.append((i+1, j+1, cell, row))
        
        print(f"找到{len(at_bm_rows)}個包含AT_BM的單元格:")
        for row_num, col_num, cell_value, full_row in at_bm_rows:
            print(f"  行{row_num} 列{col_num}: '{cell_value}'")
            print(f"    完整行: {full_row}")
        
        # 7. 檢查合併單元格信息
        print("\n🔍 檢查合併單元格信息:")
        try:
            # 獲取合併單元格信息
            merged_ranges = sheet.get_merged_ranges()
            print(f"發現{len(merged_ranges)}個合併單元格範圍:")
            for merge_range in merged_ranges:
                print(f"  合併範圍: {merge_range}")
                
                # 檢查這個合併範圍是否影響AT_BM相關的行
                for row_num, col_num, cell_value, full_row in at_bm_rows:
                    # 檢查是否在合併範圍內（簡化檢查）
                    print(f"    AT_BM單元格 行{row_num} 列{col_num} 可能受到合併影響")
        
        except Exception as e:
            print(f"❌ 獲取合併單元格信息時出錯: {e}")
            print("這可能表示沒有合併單元格，或者API權限不足")
        
        print("\n✅ 合併單元格檢查完成!")
        
    except Exception as e:
        print(f"❌ 檢查過程中出現錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()