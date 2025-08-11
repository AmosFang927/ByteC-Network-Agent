#!/usr/bin/env python3
"""
Export Unified Fields to CSV
將 unified field mapping 的結果輸出成 CSV 檔案
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

def create_sample_data():
    """創建範例數據"""
    data = {
        'Conversion ID': ['conv_001', 'conv_002', 'conv_003', 'conv_004', 'conv_005'],
        'Offer Name': ['Test Offer 1', 'Test Offer 2', 'Test Offer 3', 'Test Offer 4', 'Test Offer 5'],
        'Sale Amount (USD)': ['100.50', '200.75', '150.25', '300.00', '250.80'],
        'Conversion Date': ['2025-01-01', '2025-01-02', '2025-01-03', '2025-01-04', '2025-01-05'],
        'Status': ['approved', 'pending', 'approved', 'rejected', 'approved'],
        'Currency': ['USD', 'USD', 'USD', 'USD', 'USD'],
        'Order ID': ['order_001', 'order_002', 'order_003', 'order_004', 'order_005'],
        'Commission Rate': ['5.5%', '6.0%', '4.5%', '7.0%', '5.0%'],
        'Partner': ['DeepLeaper', 'RAMPUP', 'ByteC', 'MKK', 'TestPartner'],
        'Platform': ['involve_asia', 'involve_asia', 'involve_asia', 'involve_asia', 'involve_asia'],
        'Source': ['VIVO', 'OPPO', 'XIAOMI', 'OEM1', 'OEM2']
    }
    return pd.DataFrame(data)

def export_unified_fields_csv(df: pd.DataFrame, platform: str, output_dir: str = "output"):
    """
    將 DataFrame 映射到 unified fields 並輸出為 CSV
    
    Args:
        df: 原始 DataFrame
        platform: 平台名稱
        output_dir: 輸出目錄
    """
    print(f"🔄 開始處理 {platform} 平台的數據...")
    print(f"📊 原始數據: {len(df)} 行, {len(df.columns)} 欄位")
    
    # 創建輸出目錄
    Path(output_dir).mkdir(exist_ok=True)
    
    # 使用 Field Mapping Manager
    manager = FieldMappingManager()
    
    # 映射到統一欄位格式
    unified_df, mapping_info = manager.map_dataframe_columns(df, platform)
    
    # 生成輸出檔案名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"unified_fields_{platform}_{timestamp}.csv"
    filepath = os.path.join(output_dir, filename)
    
    # 輸出到 CSV
    unified_df.to_csv(filepath, index=False, encoding='utf-8-sig')
    
    print(f"✅ CSV 檔案已輸出: {filepath}")
    print(f"📊 統一欄位數據: {len(unified_df)} 行, {len(unified_df.columns)} 欄位")
    
    # 顯示映射信息
    if 'validation' in mapping_info:
        validation = mapping_info['validation']
        print(f"✅ 驗證結果: {validation['is_valid']}")
        print(f"📊 必須欄位數: {validation['total_required_fields']}")
        print(f"📊 存在欄位數: {validation['present_count']}")
        print(f"📊 缺少欄位數: {validation['missing_count']}")
    
    if 'mapping_report' in mapping_info:
        report = mapping_info['mapping_report']
        print(f"📊 映射覆蓋率: {report['mapping_coverage']:.1f}%")
    
    return filepath, unified_df, mapping_info

def export_mapping_report_csv(mapping_info: dict, output_dir: str = "output"):
    """輸出映射報告為 CSV"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"mapping_report_{timestamp}.csv"
    filepath = os.path.join(output_dir, filename)
    
    # 創建映射報告 DataFrame
    report_data = []
    
    if 'mapping_report' in mapping_info:
        report = mapping_info['mapping_report']
        
        # 已映射的欄位
        for field_info in report['mapped_fields']:
            report_data.append({
                'unified_field': field_info['unified_field'],
                'source_field': field_info['source_field'],
                'field_type': field_info['field_type'],
                'mapping_status': 'mapped'
            })
        
        # 未映射的欄位
        for field_info in report['unmapped_fields']:
            report_data.append({
                'unified_field': field_info['unified_field'],
                'source_field': '',
                'field_type': field_info['field_type'],
                'mapping_status': 'unmapped'
            })
    
    if report_data:
        report_df = pd.DataFrame(report_data)
        report_df.to_csv(filepath, index=False, encoding='utf-8-sig')
        print(f"📋 映射報告已輸出: {filepath}")
    
    return filepath

def export_validation_report_csv(mapping_info: dict, output_dir: str = "output"):
    """輸出驗證報告為 CSV"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"validation_report_{timestamp}.csv"
    filepath = os.path.join(output_dir, filename)
    
    if 'validation' in mapping_info:
        validation = mapping_info['validation']
        
        validation_data = {
            'metric': [
                'total_required_fields',
                'present_fields_count',
                'missing_fields_count',
                'validation_status'
            ],
            'value': [
                validation['total_required_fields'],
                validation['present_count'],
                validation['missing_count'],
                'PASS' if validation['is_valid'] else 'FAIL'
            ]
        }
        
        validation_df = pd.DataFrame(validation_data)
        validation_df.to_csv(filepath, index=False, encoding='utf-8-sig')
        print(f"📋 驗證報告已輸出: {filepath}")
    
    return filepath

def export_field_comparison_csv(original_df: pd.DataFrame, unified_df: pd.DataFrame, 
                               output_dir: str = "output"):
    """輸出欄位比較報告為 CSV"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"field_comparison_{timestamp}.csv"
    filepath = os.path.join(output_dir, filename)
    
    # 創建欄位比較數據
    comparison_data = []
    
    # 原始欄位
    for col in original_df.columns:
        comparison_data.append({
            'field_name': col,
            'field_type': str(original_df[col].dtype),
            'non_null_count': original_df[col].count(),
            'null_count': original_df[col].isnull().sum(),
            'field_category': 'original'
        })
    
    # 統一欄位
    for col in unified_df.columns:
        comparison_data.append({
            'field_name': col,
            'field_type': str(unified_df[col].dtype),
            'non_null_count': unified_df[col].count(),
            'null_count': unified_df[col].isnull().sum(),
            'field_category': 'unified'
        })
    
    comparison_df = pd.DataFrame(comparison_data)
    comparison_df.to_csv(filepath, index=False, encoding='utf-8-sig')
    print(f"📋 欄位比較報告已輸出: {filepath}")
    
    return filepath

def main():
    """主函數"""
    print("🚀 開始輸出 Unified Fields CSV 檔案")
    print("=" * 60)
    
    # 創建範例數據
    df = create_sample_data()
    print(f"📊 範例數據: {len(df)} 行, {len(df.columns)} 欄位")
    print(f"📊 欄位: {list(df.columns)}")
    
    # 輸出目錄
    output_dir = "output"
    
    try:
        # 處理不同平台
        platforms = ["involve_asia", "access_trade", "shopee", "tiktok_shop"]
        
        for platform in platforms:
            print(f"\n{'='*50}")
            print(f"🔄 處理平台: {platform}")
            print(f"{'='*50}")
            
            # 輸出統一欄位 CSV
            csv_filepath, unified_df, mapping_info = export_unified_fields_csv(
                df, platform, output_dir
            )
            
            # 輸出映射報告 CSV
            mapping_report_filepath = export_mapping_report_csv(mapping_info, output_dir)
            
            # 輸出驗證報告 CSV
            validation_report_filepath = export_validation_report_csv(mapping_info, output_dir)
            
            # 輸出欄位比較報告 CSV
            comparison_filepath = export_field_comparison_csv(df, unified_df, output_dir)
            
            print(f"✅ 平台 {platform} 處理完成")
            print(f"📁 輸出檔案:")
            print(f"   - 統一欄位數據: {csv_filepath}")
            print(f"   - 映射報告: {mapping_report_filepath}")
            print(f"   - 驗證報告: {validation_report_filepath}")
            print(f"   - 欄位比較: {comparison_filepath}")
        
        print(f"\n{'='*60}")
        print("✅ 所有 CSV 檔案輸出完成")
        print(f"📁 輸出目錄: {os.path.abspath(output_dir)}")
        
        # 顯示輸出檔案列表
        output_files = list(Path(output_dir).glob("*.csv"))
        print(f"📊 總共輸出 {len(output_files)} 個 CSV 檔案:")
        for file in output_files:
            print(f"   - {file.name}")
        
    except Exception as e:
        print(f"❌ 輸出過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 