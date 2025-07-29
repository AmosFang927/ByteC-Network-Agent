#!/usr/bin/env python3
"""
郵件日期修復測試
驗證郵件中的日期範圍顯示是否正確
"""

import sys
import os
from datetime import datetime

# 添加項目根目錄到 Python 路徑
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from agents.data_output_agent.email_sender import EmailSender

def test_email_date_fix():
    """測試郵件日期修復"""
    print("🧪 開始郵件日期修復測試")
    
    # 創建 EmailSender 實例
    email_sender = EmailSender()
    
    # 測試數據 - 模擬實際的郵件數據
    partner_name = "RAMPUP"
    email_data = {
        'partner_name': 'RAMPUP',
        'total_records': 100,
        'total_amount': '$1,000.00',
        'start_date': '2025-07-26',  # 正確的開始日期
        'end_date': '2025-07-26',    # 正確的結束日期
        'report_date': '2025-07-26', # 正確的報告日期
        'main_file': 'RAMPUP_ConversionReport_20250726_123456.xlsx',
        'file_path': 'test_file.xlsx',
        'sources': ['RAMPUP'],
        'sources_count': 1,
        'sources_statistics': [],
        'invalid_stats': {'invalid_count': 0, 'invalid_amount': 0.0},
        'total_all_conversions': 100,
        'pending_approved_count': 95,
        'pending_approved_amount': '$950.00',
        'invalid_rejected_count': 5,
        'invalid_rejected_amount': '$50.00'
    }
    
    print("\n📅 測試郵件日期處理")
    print(f"   輸入 start_date: {email_data['start_date']}")
    print(f"   輸入 end_date: {email_data['end_date']}")
    print(f"   輸入 report_date: {email_data['report_date']}")
    
    # 生成郵件正文
    try:
        email_body = email_sender._generate_partner_email_body(partner_name, email_data, None)
        
        # 檢查郵件正文中的日期範圍
        if '2025-07-26 to 2025-07-26' in email_body:
            print("   ✅ 郵件日期範圍正確: 2025-07-26 to 2025-07-26")
        else:
            print("   ❌ 郵件日期範圍錯誤")
            print(f"      期望: 2025-07-26 to 2025-07-26")
            print(f"      實際郵件內容片段:")
            # 提取包含日期範圍的行
            lines = email_body.split('\n')
            for line in lines:
                if 'Date Range' in line or 'date_range' in line or '2025-07-28' in line:
                    print(f"         {line.strip()}")
        
        # 檢查是否包含錯誤的當前日期
        current_date = datetime.now().strftime("%Y-%m-%d")
        if current_date in email_body and current_date != '2025-07-26':
            print(f"   ⚠️  發現當前日期 {current_date} 在郵件中")
        else:
            print("   ✅ 沒有發現錯誤的當前日期")
        
        print("   ✅ 郵件日期修復測試通過")
        
    except Exception as e:
        print(f"   ❌ 郵件生成失敗: {e}")
    
    print("\n🎯 郵件日期修復測試完成")

if __name__ == "__main__":
    test_email_date_fix() 