#!/usr/bin/env python3
"""
修正的 AT_BM CSV 處理腳本
解決 conversion_id 錯誤和欄位匹配問題
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
        # 讀取 CSV 檔案，明確指定不使用任何列作為索引
        df = pd.read_csv(file_path, encoding='utf-8', index_col=False)
        print(f"✅ 成功載入 CSV 檔案")
        print(f"📊 數據行數: {len(df)}")
        print(f"📊 欄位數: {len(df.columns)}")
        
        # 顯示前幾個欄位來驗證
        print(f"📊 前 10 個欄位: {list(df.columns[:10])}")
        
        # 檢查 Conversion ID 和 Creative ID 欄位
        if 'Conversion ID' in df.columns and 'Creative ID' in df.columns:
            print(f"📊 Conversion ID 前3個值: {list(df['Conversion ID'].head(3))}")
            print(f"📊 Creative ID 前3個值: {list(df['Creative ID'].head(3))}")
        
        return df
        
    except Exception as e:
        print(f"❌ 載入 CSV 檔案失敗: {e}")
        raise

def create_at_bm_mapping() -> dict:
    """創建正確的 AT_BM 映射（基於 Google Sheets）"""
    print(f"\n🔧 創建 AT_BM 映射...")
    
    # 根據 Google Sheets 中的 AT_BM 映射
    mapping = {
        'Advertiser': 'Campaign Name',           # 第23行
        'Conversion ID': 'Conversion ID',        # 第24行
        'Datetime Conversion': 'Conversion Time', # 第25行
        'Local Sale Amount': 'Total Price',      # 第26行
        'Local Reward': 'Reward',               # 第27行
        'Status': 'Status',                     # 第28行
        'Publisher Sub ID 1': 'aff_sub',        # 第29行
        'Publisher Sub ID 2': 'aff_sub2',       # 第30行
        'Publisher Sub ID 3': 'aff_sub3',       # 第31行
        'Customer Type': 'Customer Type',       # 第34行
        'Category ID': 'Category ID',           # 第35行
        'Product ID': 'Product ID',             # 第36行
    }
    
    print(f"📊 AT_BM 映射配置:")
    for unified_field, source_field in mapping.items():
        print(f"   {unified_field} <- {source_field}")
    
    return mapping

def apply_mapping(df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    """應用映射到數據"""
    print(f"\n🔄 應用映射到數據...")
    
    # 創建新的 DataFrame
    mapped_df = pd.DataFrame()
    
    # 應用每個映射
    for unified_field, source_field in mapping.items():
        if source_field in df.columns:
            mapped_df[unified_field] = df[source_field]
            print(f"   ✅ {unified_field} <- {source_field}")
        else:
            mapped_df[unified_field] = ''
            print(f"   ❌ {unified_field} <- {source_field} (欄位不存在)")
    
    print(f"📊 映射結果:")
    print(f"   - 原始數據行數: {len(df)}")
    print(f"   - 映射後數據行數: {len(mapped_df)}")
    print(f"   - 映射後欄位數: {len(mapped_df.columns)}")
    
    return mapped_df

def add_additional_fields(mapped_df: pd.DataFrame) -> pd.DataFrame:
    """添加額外欄位"""
    print(f"\n🔧 添加額外欄位...")
    
    # 添加固定值欄位
    mapped_df['Currency'] = 'IDR'
    mapped_df['Partner'] = 'AT_BM'
    mapped_df['Platform'] = 'access_trade'
    mapped_df['Source'] = 'AT_BM'
    
    # 添加 USD 金額欄位
    if 'Local Sale Amount' in mapped_df.columns:
        exchange_rate = 15000  # 1 USD = 15000 IDR
        mapped_df['USD Sale Amount'] = (pd.to_numeric(mapped_df['Local Sale Amount'], errors='coerce') / exchange_rate).round(2)
    
    if 'Local Reward' in mapped_df.columns:
        exchange_rate = 15000
        mapped_df['USD Payout'] = (pd.to_numeric(mapped_df['Local Reward'], errors='coerce') / exchange_rate).round(2)
    
    # 添加空欄位
    empty_fields = [
        'Publisher Sub ID 4', 'Publisher Sub ID 5',
        'Advertiser Sub ID', 'Advertiser Sub ID 1', 'Advertiser Sub ID 2', 'Advertiser Sub ID 3', 'Advertiser Sub ID 4', 'Advertiser Sub ID 5',
        'Click ID', 'Merchant ID', 'Commission Rate', 'Tenant ID'
    ]
    
    for field in empty_fields:
        mapped_df[field] = ''
    
    print(f"✅ 已添加額外欄位")
    return mapped_df

def validate_data(mapped_df: pd.DataFrame):
    """驗證數據質量"""
    print(f"\n🔍 驗證數據質量...")
    
    # 檢查 Conversion ID
    print(f"📊 Conversion ID 驗證:")
    conversion_ids = mapped_df['Conversion ID'].unique()
    print(f"   - 唯一值數量: {len(conversion_ids)}")
    print(f"   - 前 10 個值: {list(conversion_ids[:10])}")
    
    # 檢查是否所有值都是 108007
    if len(conversion_ids) == 1 and conversion_ids[0] == '108007':
        print(f"   ❌ 錯誤：所有 Conversion ID 都是 108007")
    else:
        print(f"   ✅ Conversion ID 值正常")
    
    # 檢查其他關鍵欄位
    key_fields = ['Advertiser', 'Local Sale Amount', 'Local Reward', 'Status']
    for field in key_fields:
        if field in mapped_df.columns:
            unique_count = mapped_df[field].nunique()
            print(f"   - {field}: {unique_count} 個唯一值")

def export_report(mapped_df: pd.DataFrame, original_filename: str, output_dir: str = "output"):
    """輸出報表"""
    print(f"\n📤 輸出最終報表...")
    
    # 創建輸出目錄
    Path(output_dir).mkdir(exist_ok=True)
    
    # 生成輸出檔案名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = Path(original_filename).stem
    output_filename = f"fixed_{base_name}_{timestamp}.csv"
    output_path = os.path.join(output_dir, output_filename)
    
    # 輸出到 CSV
    mapped_df.to_csv(output_path, index=False, encoding='utf-8-sig')
    
    print(f"✅ 報表已輸出: {output_path}")
    print(f"📊 報表行數: {len(mapped_df)}")
    print(f"📊 報表欄位數: {len(mapped_df.columns)}")
    
    # 顯示前幾行數據
    print(f"\n📋 報表前 3 行數據:")
    print(mapped_df.head(3).to_string())
    
    return output_path

def create_mapping_summary(mapping: dict, output_dir: str = "output"):
    """創建映射摘要"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_filename = f"mapping_summary_fixed_{timestamp}.csv"
    summary_path = os.path.join(output_dir, summary_filename)
    
    # 創建摘要數據
    summary_data = []
    for unified_field, source_field in mapping.items():
        summary_data.append({
            'unified_field': unified_field,
            'source_field': source_field,
            'mapping_type': 'AT_BM_fixed'
        })
    
    summary_df = pd.DataFrame(summary_data)
    summary_df.to_csv(summary_path, index=False, encoding='utf-8-sig')
    
    print(f"📋 映射摘要已輸出: {summary_path}")
    return summary_path

def main():
    """主函數"""
    print("🚀 開始修正的 AT_BM CSV 處理")
    print("=" * 60)
    
    # 檔案路徑
    input_file = "input/ID-async-report-exporter-publisher_conversion-report-id-2025-08-05-4W5IzzDQGqxfM5wy_ALL_AT_BM.csv"
    
    try:
        # 1. 載入 CSV 檔案
        print("📁 步驟 1: 載入 CSV 檔案")
        df = load_csv_file(input_file)
        
        # 2. 創建正確的 AT_BM 映射
        print(f"\n🔧 步驟 2: 創建 AT_BM 映射")
        mapping = create_at_bm_mapping()
        
        # 3. 應用映射
        print(f"\n🔄 步驟 3: 應用映射")
        mapped_df = apply_mapping(df, mapping)
        
        # 4. 添加額外欄位
        print(f"\n🔧 步驟 4: 添加額外欄位")
        mapped_df = add_additional_fields(mapped_df)
        
        # 5. 驗證數據
        print(f"\n🔍 步驟 5: 驗證數據")
        validate_data(mapped_df)
        
        # 6. 輸出報表
        print(f"\n📤 步驟 6: 輸出報表")
        output_path = export_report(mapped_df, os.path.basename(input_file))
        
        # 7. 創建映射摘要
        print(f"\n📋 步驟 7: 創建映射摘要")
        summary_path = create_mapping_summary(mapping)
        
        print(f"\n{'='*60}")
        print("✅ 修正的 AT_BM CSV 處理完成")
        print("📁 輸出檔案:")
        print(f"   - 修正後報表: {output_path}")
        print(f"   - 映射摘要: {summary_path}")
        
        # 顯示統計信息
        print(f"\n📊 統計信息:")
        print(f"   - 原始數據行數: {len(df)}")
        print(f"   - 處理後數據行數: {len(mapped_df)}")
        print(f"   - 映射欄位數: {len(mapping)}")
        
    except Exception as e:
        print(f"❌ 處理過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()