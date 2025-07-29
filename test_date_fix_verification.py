#!/usr/bin/env python3
"""
日期修復驗證測試
驗證郵件中的日期範圍顯示是否正確
"""

import sys
import os
from datetime import datetime

# 添加項目根目錄到 Python 路徑
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from agents.data_output_agent.email_sender import EmailSender

def test_date_fix_verification():
    """測試日期修復驗證"""
    print("🧪 開始日期修復驗證測試")
    
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
        'invalid_stats': {'invalid_count': 0, 'invalid_amount': 0.0}
    }
    
    print("\n📅 測試案例: 正確的日期範圍")
    print(f"   開始日期: {email_data['start_date']}")
    print(f"   結束日期: {email_data['end_date']}")
    print(f"   報告日期: {email_data['report_date']}")
    
    # 生成郵件內容
    email_body = email_sender._generate_partner_email_body(partner_name, email_data, {})
    
    # 檢查郵件內容中的日期
    print("\n📧 生成的郵件內容:")
    print("=" * 50)
    print(email_body)
    print("=" * 50)
    
    # 檢查是否包含正確的日期範圍
    expected_date_range = "2025-07-26 to 2025-07-26"
    if expected_date_range in email_body:
        print(f"✅ 郵件包含正確的日期範圍: {expected_date_range}")
    else:
        print(f"❌ 郵件中未找到正確的日期範圍: {expected_date_range}")
    
    # 檢查是否包含當前日期（不應該包含）
    current_date = datetime.now().strftime('%Y-%m-%d')
    if current_date in email_body:
        print(f"⚠️  發現當前日期 {current_date} 在郵件中")
        # 查找所有日期出現的位置
        lines = email_body.split('\n')
        for i, line in enumerate(lines):
            if current_date in line:
                print(f"   第 {i+1} 行: {line.strip()}")
    else:
        print(f"✅ 郵件中沒有包含當前日期 {current_date}")
    
    # 檢查日期範圍格式
    if "Date Range:" in email_body:
        print("✅ 郵件包含 'Date Range:' 標籤")
        # 提取日期範圍行
        for line in email_body.split('\n'):
            if "Date Range:" in line:
                print(f"   日期範圍行: {line.strip()}")
                break
    else:
        print("❌ 郵件中沒有找到 'Date Range:' 標籤")
    
    print("\n🎯 測試完成")

if __name__ == "__main__":
    test_date_fix_verification() 