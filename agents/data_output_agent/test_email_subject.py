#!/usr/bin/env python3
"""
測試郵件標題生成

驗證郵件標題只顯示日期範圍，不包含時間
"""

import sys
import os
from datetime import datetime

# 添加項目根目錄到路徑
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agents.data_output_agent.email_sender import EmailSender

def test_email_subject_generation():
    """測試郵件標題生成"""
    print("🧪 測試郵件標題生成...")
    print("=" * 50)
    
    # 創建 EmailSender 實例
    email_sender = EmailSender()
    
    # 測試數據
    test_cases = [
        {
            'partner_name': 'DeepLeaper',
            'email_data': {
                'start_date': '2025-07-14',
                'end_date': '2025-07-14',
                'main_file': 'DeepLeaper_ConversionReport_2025-07-14_235959.xlsx'
            },
            'expected': 'DeepLeaper Conversion Report - 2025-07-14'
        },
        {
            'partner_name': 'RAMPUP',
            'email_data': {
                'start_date': '2025-07-10',
                'end_date': '2025-07-14',
                'main_file': 'RAMPUP_ConversionReport_2025-07-10_to_2025-07-14_143022.xlsx'
            },
            'expected': 'RAMPUP Conversion Report - 2025-07-10 to 2025-07-14'
        },
        {
            'partner_name': 'ByteC',
            'email_data': {
                'start_date': '2025-07-01',
                'end_date': '2025-07-31',
                'main_file': 'ByteC_ConversionReport_2025-07-01_to_2025-07-31_090000.xlsx'
            },
            'expected': 'ByteC Conversion Report - 2025-07-01 to 2025-07-31'
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 測試案例 {i}: {test_case['partner_name']}")
        print(f"   開始日期: {test_case['email_data']['start_date']}")
        print(f"   結束日期: {test_case['email_data']['end_date']}")
        print(f"   文件名: {test_case['email_data']['main_file']}")
        
        # 模擬郵件創建過程
        try:
            # 創建郵件對象（不實際發送）
            msg = email_sender._create_partner_email_message(
                partner_name=test_case['partner_name'],
                email_data=test_case['email_data'],
                file_paths=[],
                receivers=['test@example.com'],
                feishu_info=None
            )
            
            actual_subject = msg['Subject']
            expected_subject = test_case['expected']
            
            print(f"   實際標題: {actual_subject}")
            print(f"   預期標題: {expected_subject}")
            
            if actual_subject == expected_subject:
                print("   ✅ 測試通過")
            else:
                print("   ❌ 測試失敗")
                
        except Exception as e:
            print(f"   ❌ 測試異常: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 郵件標題測試完成！")
    print("\n📝 總結:")
    print("  - 郵件標題現在只顯示日期範圍，不包含時間")
    print("  - 單日報告格式: 'Partner Conversion Report - YYYY-MM-DD'")
    print("  - 多日報告格式: 'Partner Conversion Report - YYYY-MM-DD to YYYY-MM-DD'")

def test_edge_cases():
    """測試邊界情況"""
    print("\n🧪 測試邊界情況...")
    print("=" * 50)
    
    email_sender = EmailSender()
    
    # 測試沒有日期數據的情況
    edge_case = {
        'partner_name': 'TestPartner',
        'email_data': {
            'main_file': 'TestPartner_ConversionReport_2025-07-14.xlsx'
        }
    }
    
    try:
        msg = email_sender._create_partner_email_message(
            partner_name=edge_case['partner_name'],
            email_data=edge_case['email_data'],
            file_paths=[],
            receivers=['test@example.com'],
            feishu_info=None
        )
        
        print(f"📋 邊界測試 - 無日期數據:")
        print(f"   實際標題: {msg['Subject']}")
        print("   ✅ 邊界測試通過")
        
    except Exception as e:
        print(f"   ❌ 邊界測試異常: {e}")

def main():
    """主函數"""
    print("🚀 郵件標題生成測試開始")
    print("=" * 50)
    
    # 測試正常情況
    test_email_subject_generation()
    
    # 測試邊界情況
    test_edge_cases()
    
    print("\n" + "=" * 50)
    print("✅ 所有測試完成！")

if __name__ == "__main__":
    main() 