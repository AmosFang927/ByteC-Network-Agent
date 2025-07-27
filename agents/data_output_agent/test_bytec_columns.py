#!/usr/bin/env python3
"""
測試 ByteC 列名修復

驗證 Partner+Source 匯總功能能夠正確處理 ByteC 的數據結構
"""

import sys
import os
import pandas as pd
from datetime import datetime

# 添加項目根目錄到路徑
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agents.data_output_agent.email_sender import EmailSender

def test_bytec_column_detection():
    """測試 ByteC 列名檢測"""
    print("🧪 測試 ByteC 列名檢測...")
    print("=" * 50)
    
    # 創建 EmailSender 實例
    email_sender = EmailSender()
    
    # 測試數據 - 模擬 ByteC Excel 文件的列結構
    test_cases = [
        {
            'name': '標準 ByteC 格式',
            'columns': ['Offer Name', 'USD Sale Amount', 'Estimated Earning', 'Conversions', 'Partner', 'Source'],
            'data': [
                {'Offer Name': 'DeepLeaper_Offer1', 'USD Sale Amount': 100.0, 'Estimated Earning': 50.0, 'Conversions': 5, 'Partner': 'DeepLeaper', 'Source': 'DeepLeaper_Source1'},
                {'Offer Name': 'RAMPUP_Offer1', 'USD Sale Amount': 200.0, 'Estimated Earning': 100.0, 'Conversions': 10, 'Partner': 'RAMPUP', 'Source': 'RAMPUP_Source1'},
                {'Offer Name': 'MKK_Offer1', 'USD Sale Amount': 150.0, 'Estimated Earning': 75.0, 'Conversions': 8, 'Partner': 'MKK', 'Source': 'MKK_Source1'}
            ]
        },
        {
            'name': '缺少 Partner/Source 列',
            'columns': ['Offer Name', 'USD Sale Amount', 'Estimated Earning', 'Conversions', 'aff_sub2'],
            'data': [
                {'Offer Name': 'DeepLeaper_Offer1', 'USD Sale Amount': 100.0, 'Estimated Earning': 50.0, 'Conversions': 5, 'aff_sub2': 'DeepLeaper_Source1'},
                {'Offer Name': 'RAMPUP_Offer1', 'USD Sale Amount': 200.0, 'Estimated Earning': 100.0, 'Conversions': 10, 'aff_sub2': 'RAMPUP_Source1'},
                {'Offer Name': 'MKK_Offer1', 'USD Sale Amount': 150.0, 'Estimated Earning': 75.0, 'Conversions': 8, 'aff_sub2': 'MKK_Source1'}
            ]
        },
        {
            'name': '只有 Offer Name',
            'columns': ['Offer Name', 'USD Sale Amount', 'Estimated Earning', 'Conversions'],
            'data': [
                {'Offer Name': 'DeepLeaper_Offer1', 'USD Sale Amount': 100.0, 'Estimated Earning': 50.0, 'Conversions': 5},
                {'Offer Name': 'RAMPUP_Offer1', 'USD Sale Amount': 200.0, 'Estimated Earning': 100.0, 'Conversions': 10},
                {'Offer Name': 'MKK_Offer1', 'USD Sale Amount': 150.0, 'Estimated Earning': 75.0, 'Conversions': 8}
            ]
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 測試案例 {i}: {test_case['name']}")
        print(f"   列名: {test_case['columns']}")
        
        # 創建測試 DataFrame
        df = pd.DataFrame(test_case['data'])
        print(f"   數據行數: {len(df)}")
        
        try:
            # 測試 Partner+Source 匯總
            result = email_sender._calculate_partner_source_summary(df)
            
            if result:
                print(f"   ✅ 成功生成 {len(result)} 個 Partner+Source 匯總")
                for j, item in enumerate(result[:3]):  # 顯示前3個
                    print(f"      {j+1}. {item.get('partner_source', 'Unknown')}: {item.get('conversion', 0)} conversions, {item.get('sales_amount', '$0.00')}")
            else:
                print("   ⚠️ 未生成 Partner+Source 匯總")
                
        except Exception as e:
            print(f"   ❌ 測試異常: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 ByteC 列名檢測測試完成！")

def test_offer_summary():
    """測試 Offer 匯總"""
    print("\n🧪 測試 Offer 匯總...")
    print("=" * 50)
    
    email_sender = EmailSender()
    
    # 測試數據
    test_data = [
        {'Offer Name': 'DeepLeaper_Offer1', 'USD Sale Amount': 100.0, 'Estimated Earning': 50.0, 'Conversions': 5},
        {'Offer Name': 'RAMPUP_Offer1', 'USD Sale Amount': 200.0, 'Estimated Earning': 100.0, 'Conversions': 10},
        {'Offer Name': 'MKK_Offer1', 'USD Sale Amount': 150.0, 'Estimated Earning': 75.0, 'Conversions': 8},
        {'Offer Name': 'TOTAL', 'USD Sale Amount': 450.0, 'Estimated Earning': 225.0, 'Conversions': 23}  # 總計行
    ]
    
    df = pd.DataFrame(test_data)
    print(f"📊 測試數據: {len(df)} 行")
    print(f"📋 列名: {list(df.columns)}")
    
    try:
        result = email_sender._calculate_offer_level_summary(df)
        
        if result:
            print(f"✅ 成功生成 {len(result)} 個 Offer 匯總")
            for i, item in enumerate(result[:3]):  # 顯示前3個
                print(f"   {i+1}. {item.get('offer_name', 'Unknown')}: {item.get('conversion', 0)} conversions, {item.get('sales_amount', '$0.00')}")
        else:
            print("⚠️ 未生成 Offer 匯總")
            
    except Exception as e:
        print(f"❌ 測試異常: {e}")

def test_company_summary():
    """測試公司級別匯總"""
    print("\n🧪 測試公司級別匯總...")
    print("=" * 50)
    
    email_sender = EmailSender()
    
    # 測試數據
    test_data = [
        {'Offer Name': 'DeepLeaper_Offer1', 'USD Sale Amount': 100.0, 'Estimated Earning': 50.0, 'Conversions': 5},
        {'Offer Name': 'RAMPUP_Offer1', 'USD Sale Amount': 200.0, 'Estimated Earning': 100.0, 'Conversions': 10},
        {'Offer Name': 'MKK_Offer1', 'USD Sale Amount': 150.0, 'Estimated Earning': 75.0, 'Conversions': 8}
    ]
    
    df = pd.DataFrame(test_data)
    print(f"📊 測試數據: {len(df)} 行")
    
    try:
        result = email_sender._calculate_company_level_summary(df)
        
        if result:
            print("✅ 成功生成公司級別匯總")
            print(f"   總轉化數: {result.get('total_conversion', 0):,}")
            print(f"   總銷售額: {result.get('total_sales', '$0.00')}")
            print(f"   總預計收入: {result.get('total_earning', '$0.00')}")
        else:
            print("⚠️ 未生成公司級別匯總")
            
    except Exception as e:
        print(f"❌ 測試異常: {e}")

def main():
    """主函數"""
    print("🚀 ByteC 列名修復測試開始")
    print("=" * 50)
    
    # 測試列名檢測
    test_bytec_column_detection()
    
    # 測試 Offer 匯總
    test_offer_summary()
    
    # 測試公司級別匯總
    test_company_summary()
    
    print("\n" + "=" * 50)
    print("✅ 所有測試完成！")
    print("\n📝 修復總結:")
    print("  - 增強了 Partner/Source 列的檢測邏輯")
    print("  - 支持從 Offer Name 推斷 Partner 信息")
    print("  - 支持多種 aff_sub 列作為 Source")
    print("  - 改進了錯誤處理和日誌輸出")

if __name__ == "__main__":
    main() 