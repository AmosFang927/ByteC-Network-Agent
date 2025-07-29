#!/usr/bin/env python3
"""
日期處理單元測試
驗證郵件中的日期範圍顯示是否正確
"""

import sys
import os
from datetime import datetime, timedelta

# 添加項目根目錄到 Python 路徑
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from agents.data_output_agent.email_sender import EmailSender

def test_date_handling():
    """測試日期處理邏輯"""
    print("🧪 開始日期處理單元測試")
    
    # 創建 EmailSender 實例
    email_sender = EmailSender()
    
    # 測試數據
    partner_name = "RAMPUP"
    partner_data = {
        'records': 100,
        'amount_formatted': '$1,000.00',
        'file_path': 'test_file.xlsx',
        'sources': ['RAMPUP'],
        'sources_count': 1,
        'invalid_stats': {'invalid_count': 0, 'invalid_amount': 0.0}
    }
    
    # 測試案例 1: 正確的日期範圍
    print("\n📅 測試案例 1: 正確的日期範圍")
    start_date = datetime(2025, 7, 26)
    end_date = datetime(2025, 7, 26)
    
    email_data = email_sender._prepare_partner_email_data(
        partner_name, partner_data, end_date, start_date
    )
    
    print(f"   輸入 start_date: {start_date}")
    print(f"   輸入 end_date: {end_date}")
    print(f"   輸出 start_date: {email_data['start_date']}")
    print(f"   輸出 end_date: {email_data['end_date']}")
    
    expected_start = "2025-07-26"
    expected_end = "2025-07-26"
    
    if email_data['start_date'] == expected_start and email_data['end_date'] == expected_end:
        print("   ✅ 測試案例 1 通過")
    else:
        print("   ❌ 測試案例 1 失敗")
        print(f"      期望: {expected_start} to {expected_end}")
        print(f"      實際: {email_data['start_date']} to {email_data['end_date']}")
    
    # 測試案例 2: 只有 end_date，沒有 start_date
    print("\n📅 測試案例 2: 只有 end_date，沒有 start_date")
    email_data2 = email_sender._prepare_partner_email_data(
        partner_name, partner_data, end_date, None
    )
    
    print(f"   輸入 start_date: None")
    print(f"   輸入 end_date: {end_date}")
    print(f"   輸出 start_date: {email_data2['start_date']}")
    print(f"   輸出 end_date: {email_data2['end_date']}")
    
    if email_data2['start_date'] == expected_start and email_data2['end_date'] == expected_end:
        print("   ✅ 測試案例 2 通過")
    else:
        print("   ❌ 測試案例 2 失敗")
        print(f"      期望: {expected_start} to {expected_end}")
        print(f"      實際: {email_data2['start_date']} to {email_data2['end_date']}")
    
    # 測試案例 3: 字符串格式的日期
    print("\n📅 測試案例 3: 字符串格式的日期")
    start_date_str = "2025-07-26"
    end_date_str = "2025-07-26"
    
    email_data3 = email_sender._prepare_partner_email_data(
        partner_name, partner_data, end_date_str, start_date_str
    )
    
    print(f"   輸入 start_date: {start_date_str}")
    print(f"   輸入 end_date: {end_date_str}")
    print(f"   輸出 start_date: {email_data3['start_date']}")
    print(f"   輸出 end_date: {email_data3['end_date']}")
    
    if email_data3['start_date'] == expected_start and email_data3['end_date'] == expected_end:
        print("   ✅ 測試案例 3 通過")
    else:
        print("   ❌ 測試案例 3 失敗")
        print(f"      期望: {expected_start} to {expected_end}")
        print(f"      實際: {email_data3['start_date']} to {email_data3['end_date']}")
    
    # 測試案例 4: 不同的日期範圍
    print("\n📅 測試案例 4: 不同的日期範圍")
    start_date_diff = datetime(2025, 7, 25)
    end_date_diff = datetime(2025, 7, 26)
    
    email_data4 = email_sender._prepare_partner_email_data(
        partner_name, partner_data, end_date_diff, start_date_diff
    )
    
    print(f"   輸入 start_date: {start_date_diff}")
    print(f"   輸入 end_date: {end_date_diff}")
    print(f"   輸出 start_date: {email_data4['start_date']}")
    print(f"   輸出 end_date: {email_data4['end_date']}")
    
    expected_start_diff = "2025-07-25"
    expected_end_diff = "2025-07-26"
    
    if email_data4['start_date'] == expected_start_diff and email_data4['end_date'] == expected_end_diff:
        print("   ✅ 測試案例 4 通過")
    else:
        print("   ❌ 測試案例 4 失敗")
        print(f"      期望: {expected_start_diff} to {expected_end_diff}")
        print(f"      實際: {email_data4['start_date']} to {email_data4['end_date']}")
    
    print("\n🎯 日期處理單元測試完成")

if __name__ == "__main__":
    test_date_handling() 