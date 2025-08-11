#!/usr/bin/env python3
"""
完整的 AT_BM CSV 處理腳本
使用 Google Sheets 映射並輸出最終轉化後報表
"""

import sys
import os
import pandas as pd
import logging
from datetime import datetime
from pathlib import Path

# 添加項目根目錄到 Python 路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from agents.data_dmp_agent.field_mapping_manager import FieldMappingManager
from agents.data_dmp_agent.unified_field_mapper import UnifiedFieldMapper

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_csv_file(file_path: str) -> pd.DataFrame:
    """載入 CSV 檔案"""
    print(f"📁 載入檔案: {file_path}")
    
    try:
        # 讀取 CSV 檔案
        df = pd.read_csv(file_path, encoding='utf-8')
        print(f"✅ 成功載入 CSV 檔案")
        print(f"📊 數據行數: {len(df)}")
        print(f"📊 欄位數: {len(df.columns)}")
        
        return df
        
    except Exception as e:
        print(f"❌ 載入 CSV 檔案失敗: {e}")
        raise

def convert_google_sheets_mapping_to_unified(google_sheets_mapping: dict) -> dict:
    """將 Google Sheets 映射轉換為統一欄位映射"""
    print(f"\n🔄 轉換 Google Sheets 映射到統一欄位...")
    
    # 直接使用 Google Sheets 中的 Unified Field 名稱，不進行轉換
    unified_mapping = {}
    field_mappings = google_sheets_mapping.get('field_mappings', {})
    
    for google_field, source_field in field_mappings.items():
        # 直接使用 Google Sheets 中的 Unified Field 名稱
        unified_field = google_field  # 保持原始名稱
        unified_mapping[unified_field] = source_field
        print(f"   {google_field} = {source_field}")
    
    print(f"📊 轉換完成: {len(unified_mapping)} 個映射")
    return unified_mapping

def process_data_with_mapping(df: pd.DataFrame, unified_mapping: dict) -> pd.DataFrame:
    """使用映射處理數據"""
    print(f"\n🔄 使用映射處理數據...")
    
    # 創建統一欄位映射器
    unified_mapper = UnifiedFieldMapper()
    
    # 執行映射
    unified_df = unified_mapper.map_dataframe_to_unified_fields(df, unified_mapping)
    
    print(f"📊 映射結果:")
    print(f"   - 原始數據行數: {len(df)}")
    print(f"   - 映射後數據行數: {len(unified_df)}")
    print(f"   - 映射後欄位數: {len(unified_df.columns)}")
    
    # 驗證統一欄位
    validation = unified_mapper.validate_unified_fields(unified_df)
    print(f"📊 驗證結果: {validation}")
    
    return unified_df

def add_missing_fields(unified_df: pd.DataFrame) -> pd.DataFrame:
    """添加缺失的欄位（基於 Google Sheets 標準欄位）"""
    print(f"🔧 添加缺失欄位...")
    
    # 添加基本欄位（基於 Google Sheets 標準欄位）
    unified_df['Conversion ID'] = unified_df.get('Conversion ID', '')
    unified_df['Offer ID'] = unified_df.get('Offer ID', '')
    unified_df['Offer Name'] = unified_df.get('Offer Name', '')
    unified_df['Order ID'] = unified_df.get('Order ID', '')
    unified_df['Conversion Date'] = unified_df.get('Conversion Date', '')
    unified_df['Sale Amount (USD)'] = unified_df.get('Sale Amount (USD)', 0.0)
    unified_df['Payout (USD)'] = unified_df.get('Payout (USD)', 0.0)
    unified_df['Currency'] = unified_df.get('Currency', 'USD')
    unified_df['Status'] = unified_df.get('Status', 'Pending')
    unified_df['Platform'] = unified_df.get('Platform', 'AT_BM')
    unified_df['Advertiser Name'] = unified_df.get('Advertiser Name', '')
    unified_df['Campaign Name'] = unified_df.get('Campaign Name', '')
    unified_df['Publisher ID'] = unified_df.get('Publisher ID', '')
    unified_df['Publisher Name'] = unified_df.get('Publisher Name', '')
    unified_df['Source File'] = unified_df.get('Source File', '')
    unified_df['Processed Date'] = unified_df.get('Processed Date', '')
    
    # 添加 Publisher Sub ID 欄位
    unified_df['Publisher Sub ID 1'] = unified_df.get('Publisher Sub ID 1', '')
    unified_df['Publisher Sub ID 2'] = unified_df.get('Publisher Sub ID 2', '')
    unified_df['Publisher Sub ID 3'] = unified_df.get('Publisher Sub ID 3', '')
    unified_df['Publisher Sub ID 4'] = unified_df.get('Publisher Sub ID 4', '')
    unified_df['Publisher Sub ID 5'] = unified_df.get('Publisher Sub ID 5', '')
    
    # 添加 Advertiser Sub ID 欄位
    unified_df['Advertiser Sub ID'] = unified_df.get('Advertiser Sub ID', '')
    unified_df['Advertiser Sub ID 1'] = unified_df.get('Advertiser Sub ID 1', '')
    unified_df['Advertiser Sub ID 2'] = unified_df.get('Advertiser Sub ID 2', '')
    unified_df['Advertiser Sub ID 3'] = unified_df.get('Advertiser Sub ID 3', '')
    unified_df['Advertiser Sub ID 4'] = unified_df.get('Advertiser Sub ID 4', '')
    unified_df['Advertiser Sub ID 5'] = unified_df.get('Advertiser Sub ID 5', '')
    
    # 添加 USD 金額欄位（如果沒有）
    if 'USD Sale Amount' not in unified_df.columns or unified_df['USD Sale Amount'].isna().all():
        # 使用動態匯率獲取
        try:
            import requests
            import json
            
            # 嘗試從多個API獲取匯率
            api_endpoints = [
                'https://api.exchangerate-api.com/v4/latest/USD',
                'https://api.fxratesapi.com/latest?base=USD&symbols=IDR',
                'https://open.er-api.com/v6/latest/USD'
            ]
            
            exchange_rate = None
            for api_url in api_endpoints:
                try:
                    response = requests.get(api_url, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        if 'rates' in data and 'IDR' in data['rates']:
                            exchange_rate = data['rates']['IDR']
                            print(f"💱 成功獲取動態匯率: 1 USD = {exchange_rate} IDR")
                            break
                except Exception as e:
                    print(f"⚠️ API {api_url} 失敗: {e}")
                    continue
            
            # 如果所有API都失敗，使用預設匯率
            if exchange_rate is None:
                exchange_rate = 15000
                print(f"💱 使用預設匯率: 1 USD = {exchange_rate} IDR")
            
            # 使用映射後的欄位名稱
            if 'sale_amount' in unified_df.columns:
                unified_df['USD Sale Amount'] = (unified_df['sale_amount'] / exchange_rate).round(2)
            elif 'Local Sale Amount' in unified_df.columns:
                unified_df['USD Sale Amount'] = (unified_df['Local Sale Amount'] / exchange_rate).round(2)
            else:
                print("⚠️ 未找到本地金額欄位，跳過 USD 轉換")
            
        except Exception as e:
            print(f"❌ 匯率獲取失敗: {e}")
            # 使用預設匯率
            exchange_rate = 15000
            if 'sale_amount' in unified_df.columns:
                unified_df['USD Sale Amount'] = (unified_df['sale_amount'] / exchange_rate).round(2)
            elif 'Local Sale Amount' in unified_df.columns:
                unified_df['USD Sale Amount'] = (unified_df['Local Sale Amount'] / exchange_rate).round(2)
            print(f"💱 使用預設匯率: 1 USD = {exchange_rate} IDR")
    
    if 'USD Payout' not in unified_df.columns or unified_df['USD Payout'].isna().all():
        try:
            import requests
            import json
            
            # 嘗試從多個API獲取匯率
            api_endpoints = [
                'https://api.exchangerate-api.com/v4/latest/USD',
                'https://api.fxratesapi.com/latest?base=USD&symbols=IDR',
                'https://open.er-api.com/v6/latest/USD'
            ]
            
            exchange_rate = None
            for api_url in api_endpoints:
                try:
                    response = requests.get(api_url, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        if 'rates' in data and 'IDR' in data['rates']:
                            exchange_rate = data['rates']['IDR']
                            break
                except Exception:
                    continue
            
            # 如果所有API都失敗，使用預設匯率
            if exchange_rate is None:
                exchange_rate = 15000
            
            # 使用映射後的欄位名稱
            if 'payout' in unified_df.columns:
                unified_df['USD Payout'] = (unified_df['payout'] / exchange_rate).round(2)
            elif 'Local Reward' in unified_df.columns:
                unified_df['USD Payout'] = (unified_df['Local Reward'] / exchange_rate).round(2)
            else:
                print("⚠️ 未找到本地獎勵欄位，跳過 USD 轉換")
            
        except Exception:
            # 使用預設匯率
            exchange_rate = 15000
            if 'payout' in unified_df.columns:
                unified_df['USD Payout'] = (unified_df['payout'] / exchange_rate).round(2)
            elif 'Local Reward' in unified_df.columns:
                unified_df['USD Payout'] = (unified_df['Local Reward'] / exchange_rate).round(2)
    
    # 添加 offer_id 和 offer_name（如果沒有）
    if 'Order ID' not in unified_df.columns:
        unified_df['Order ID'] = unified_df.get('Product ID', '')
    
    if 'Advertiser Name' not in unified_df.columns:
        unified_df['Advertiser Name'] = unified_df.get('Customer Type', '')
    
    print(f"✅ 已添加缺失欄位")
    return unified_df

def export_final_report(unified_df: pd.DataFrame, original_filename: str, output_dir: str = "output"):
    """輸出最終轉化後報表"""
    print(f"\n📤 輸出最終轉化後報表...")
    
    # 創建輸出目錄
    Path(output_dir).mkdir(exist_ok=True)
    
    # 生成輸出檔案名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = Path(original_filename).stem
    output_filename = f"unified_{base_name}_{timestamp}.csv"
    output_path = os.path.join(output_dir, output_filename)
    
    # 輸出到 CSV
    unified_df.to_csv(output_path, index=False, encoding='utf-8-sig')
    
    print(f"✅ 最終報表已輸出: {output_path}")
    print(f"📊 報表行數: {len(unified_df)}")
    print(f"📊 報表欄位數: {len(unified_df.columns)}")
    
    # 顯示前幾行數據
    print(f"\n📋 報表前 3 行數據:")
    print(unified_df.head(3).to_string())
    
    return output_path

def create_mapping_summary_report(google_mapping: dict, unified_mapping: dict, output_dir: str = "output"):
    """創建映射摘要報告"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_filename = f"mapping_summary_complete_{timestamp}.csv"
    summary_path = os.path.join(output_dir, summary_filename)
    
    # 創建摘要數據
    summary_data = []
    
    # Google Sheets 映射
    for google_field, source_field in google_mapping.get('field_mappings', {}).items():
        summary_data.append({
            'mapping_type': 'google_sheets',
            'google_field': google_field,
            'unified_field': unified_mapping.get(google_field, ''),
            'source_field': source_field,
            'status': 'mapped' if google_field in unified_mapping else 'unmapped'
        })
    
    if summary_data:
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_csv(summary_path, index=False, encoding='utf-8-sig')
        print(f"📋 映射摘要報告已輸出: {summary_path}")
    
    return summary_path

def main():
    """主函數"""
    print("🚀 開始完整的 AT_BM CSV 處理")
    print("=" * 60)
    
    # 檔案路徑
    input_file = "input/ID-async-report-exporter-publisher_conversion-report-id-2025-08-05-4W5IzzDQGqxfM5wy_ALL_AT_BM.csv"
    platform = "access_trade"
    
    try:
        # 1. 載入 CSV 檔案
        print("📁 步驟 1: 載入 CSV 檔案")
        df = load_csv_file(input_file)
        
        # 2. 初始化欄位映射管理器
        print(f"\n🔧 步驟 2: 初始化欄位映射管理器")
        manager = FieldMappingManager()
        
        # 3. 獲取 Google Sheets 映射
        print(f"\n🔍 步驟 3: 獲取 Google Sheets 映射")
        mapping_info = manager.get_platform_mapping_info(platform)
        google_mapping = mapping_info.get('field_mappings', {})
        print(f"📊 Google Sheets 映射數: {len(google_mapping)}")
        
        # 4. 轉換為統一欄位映射
        print(f"\n🔄 步驟 4: 轉換為統一欄位映射")
        unified_mapping = convert_google_sheets_mapping_to_unified(mapping_info)
        
        # 5. 處理數據
        print(f"\n🔄 步驟 5: 處理數據")
        unified_df = process_data_with_mapping(df, unified_mapping)
        
        # 6. 添加缺失欄位
        print(f"\n🔧 步驟 6: 添加缺失欄位")
        unified_df = add_missing_fields(unified_df)
        
        # 7. 輸出最終報表
        print(f"\n📤 步驟 7: 輸出最終報表")
        output_path = export_final_report(unified_df, os.path.basename(input_file))
        
        # 8. 創建映射摘要報告
        print(f"\n📋 步驟 8: 創建映射摘要報告")
        summary_path = create_mapping_summary_report(mapping_info, unified_mapping)
        
        print(f"\n{'='*60}")
        print("✅ 完整的 AT_BM CSV 處理完成")
        print("📁 輸出檔案:")
        print(f"   - 最終轉化後報表: {output_path}")
        print(f"   - 映射摘要報告: {summary_path}")
        
        # 顯示統計信息
        print(f"\n📊 統計信息:")
        print(f"   - 原始數據行數: {len(df)}")
        print(f"   - 轉化後數據行數: {len(unified_df)}")
        print(f"   - Google Sheets 映射數: {len(google_mapping)}")
        print(f"   - 統一欄位映射數: {len(unified_mapping)}")
        
    except Exception as e:
        print(f"❌ 處理過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 