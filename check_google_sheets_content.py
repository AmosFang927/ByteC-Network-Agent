#!/usr/bin/env python3
"""
檢查 Google Sheets 內容
了解為什麼只讀取到一個映射配置
"""

import sys
import os
import logging
from pathlib import Path

# 添加項目根目錄到 Python 路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from agents.data_dmp_agent.google_sheets_manager import GoogleSheetsManager

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_google_sheets_content():
    """檢查Google Sheets內容"""
    print("🔍 檢查 Google Sheets 內容")
    print("=" * 60)
    
    try:
        # 初始化Google Sheets管理器
        sheets_manager = GoogleSheetsManager()
        
        # 檢查連接
        print("🔧 檢查 Google Sheets 連接...")
        
        # 獲取配置信息
        config_file = "config/field_mapping_config.json"
        if os.path.exists(config_file):
            import json
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            spreadsheet_id = config.get("google_sheets", {}).get("spreadsheet_id")
            sheet_name = config.get("google_sheets", {}).get("sheet_name", "Data_Input_Mapping")
            range_name = config.get("google_sheets", {}).get("range", "A1:Z1000")
            
            print(f"📊 配置信息:")
            print(f"   - Spreadsheet ID: {spreadsheet_id}")
            print(f"   - Sheet Name: {sheet_name}")
            print(f"   - Range: {range_name}")
            
            # 直接讀取原始數據
            print(f"\n📋 讀取原始數據...")
            raw_data = sheets_manager._read_from_sheets(spreadsheet_id, sheet_name, range_name)
            
            if raw_data and 'values' in raw_data:
                values = raw_data['values']
                print(f"📊 數據行數: {len(values)}")
                
                if len(values) > 0:
                    print(f"\n📋 標題行:")
                    headers = values[0]
                    for i, header in enumerate(headers):
                        print(f"   {i+1:2d}. {header}")
                    
                    print(f"\n📋 前 5 行數據:")
                    for i, row in enumerate(values[1:6]):
                        print(f"   行 {i+1}: {row}")
                    
                    # 分析列結構
                    print(f"\n🔍 分析列結構...")
                    platform_col = sheets_manager._find_column_index(headers, ["Platform", "platform", "平台"])
                    source_field_col = sheets_manager._find_column_index(headers, ["Field", "field", "欄位", "源欄位"])
                    target_field_col = sheets_manager._find_column_index(headers, ["Unitfied Field", "Unified Field", "Target Field", "target_field", "統一欄位", "目標欄位"])
                    
                    print(f"📊 列索引:")
                    print(f"   - Platform 列: {platform_col}")
                    print(f"   - Source Field 列: {source_field_col}")
                    print(f"   - Target Field 列: {target_field_col}")
                    
                    # 檢查每個平台的映射
                    print(f"\n📊 各平台映射統計:")
                    platform_counts = {}
                    for row in values[1:]:
                        if len(row) > max(platform_col or 0, source_field_col or 0, target_field_col or 0):
                            platform = row[platform_col].strip() if platform_col is not None and platform_col < len(row) else ""
                            if platform:
                                platform_counts[platform] = platform_counts.get(platform, 0) + 1
                    
                    for platform, count in platform_counts.items():
                        print(f"   - {platform}: {count} 個映射")
                    
                    # 檢查 access_trade 平台的具體映射
                    print(f"\n📊 access_trade 平台映射:")
                    access_trade_mappings = []
                    for row in values[1:]:
                        if len(row) > max(platform_col or 0, source_field_col or 0, target_field_col or 0):
                            platform = row[platform_col].strip() if platform_col is not None and platform_col < len(row) else ""
                            if platform.lower() in ["access_trade", "at", "at_bm"]:
                                source_field = row[source_field_col].strip() if source_field_col is not None and source_field_col < len(row) else ""
                                target_field = row[target_field_col].strip() if target_field_col is not None and target_field_col < len(row) else ""
                                if source_field and target_field:
                                    access_trade_mappings.append((source_field, target_field))
                    
                    for source_field, target_field in access_trade_mappings:
                        print(f"   {source_field} -> {target_field}")
                    
                else:
                    print("❌ 沒有數據行")
            else:
                print("❌ 無法讀取數據")
                
        else:
            print("❌ 配置文件不存在")
            
    except Exception as e:
        print(f"❌ 檢查過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函數"""
    check_google_sheets_content()

if __name__ == "__main__":
    main() 