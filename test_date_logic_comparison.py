#!/usr/bin/env python3
"""
Email vs Excel Summary Report 日期處理邏輯比較測試
驗證兩個系統的日期處理是否一致
"""

import sys
import os
from datetime import datetime

# 添加項目根目錄到 Python 路徑
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from agents.data_output_agent.email_sender import EmailSender
from agents.reporter_agent.core.report_generator import ReportGenerator
from shared.utils.summary_formatter import generate_unified_summary

def test_date_logic_comparison():
    """測試日期處理邏輯比較"""
    print("🧪 開始 Email vs Excel Summary Report 日期處理邏輯比較測試")
    
    # 測試數據
    partner_name = "RAMPUP"
    start_date = datetime(2025, 7, 26)
    end_date = datetime(2025, 7, 26)
    
    print(f"\n📅 測試日期:")
    print(f"   開始日期: {start_date}")
    print(f"   結束日期: {end_date}")
    print(f"   預期日期範圍: 2025-07-26 to 2025-07-26")
    
    # 1. 測試 Excel Summary Report 的日期處理邏輯
    print("\n" + "="*60)
    print("📊 Excel Summary Report 日期處理邏輯")
    print("="*60)
    
    # 模擬 _add_summary_header 中的邏輯
    excel_start_date_str = start_date.strftime('%Y-%m-%d')
    excel_end_date_str = end_date.strftime('%Y-%m-%d')
    
    print(f"✅ Excel 日期轉換:")
    print(f"   start_date: {start_date} → '{excel_start_date_str}'")
    print(f"   end_date: {end_date} → '{excel_end_date_str}'")
    
    # 模擬 generate_unified_summary 調用
    excel_summary = generate_unified_summary(
        partner_name=partner_name,
        start_date=excel_start_date_str,
        end_date=excel_end_date_str,
        df=None,
        total_records=100,
        total_amount=1000.0,
        sources=['RAMPUP']
    )
    
    print(f"✅ Excel Summary 結果:")
    print(f"   date_range: '{excel_summary['date_range']}'")
    print(f"   partner_name: '{excel_summary['partner_name']}'")
    
    # 2. 測試 Email 的日期處理邏輯
    print("\n" + "="*60)
    print("📧 Email 日期處理邏輯")
    print("="*60)
    
    # 創建 EmailSender 實例
    email_sender = EmailSender()
    
    # 模擬 _send_emails 中的邏輯（修復後）
    email_start_date_str = start_date.strftime('%Y-%m-%d') if start_date else None
    email_end_date_str = end_date.strftime('%Y-%m-%d') if end_date else None
    
    print(f"✅ Email 日期轉換:")
    print(f"   start_date: {start_date} → '{email_start_date_str}'")
    print(f"   end_date: {end_date} → '{email_end_date_str}'")
    
    # 模擬 _prepare_partner_email_data 中的邏輯
    partner_data = {
        'records': 100,
        'amount_formatted': '$1,000.00',
        'file_path': 'test_file.xlsx',
        'sources': ['RAMPUP'],
        'sources_count': 1,
        'invalid_stats': {'invalid_count': 0, 'invalid_amount': 0.0}
    }
    
    email_data = email_sender._prepare_partner_email_data(
        partner_name=partner_name,
        partner_data=partner_data,
        end_date=email_end_date_str,
        start_date=email_start_date_str
    )
    
    print(f"✅ Email 數據準備結果:")
    print(f"   start_date: '{email_data['start_date']}'")
    print(f"   end_date: '{email_data['end_date']}'")
    print(f"   report_date: '{email_data['report_date']}'")
    
    # 3. 比較結果
    print("\n" + "="*60)
    print("🔍 日期處理邏輯比較結果")
    print("="*60)
    
    excel_date_range = excel_summary['date_range']
    email_date_range = f"{email_data['start_date']} to {email_data['end_date']}"
    
    print(f"📊 Excel Summary Report:")
    print(f"   日期範圍: {excel_date_range}")
    
    print(f"📧 Email:")
    print(f"   日期範圍: {email_date_range}")
    
    # 檢查是否一致
    if excel_date_range == email_date_range:
        print(f"✅ 日期處理邏輯一致！")
    else:
        print(f"❌ 日期處理邏輯不一致！")
        print(f"   差異: Excel='{excel_date_range}' vs Email='{email_date_range}'")
    
    # 4. 測試郵件生成
    print("\n" + "="*60)
    print("📧 郵件內容生成測試")
    print("="*60)
    
    email_body = email_sender._generate_partner_email_body(partner_name, email_data, {})
    
    # 檢查郵件內容中的日期
    if "2025-07-26 to 2025-07-26" in email_body:
        print(f"✅ 郵件包含正確的日期範圍: 2025-07-26 to 2025-07-26")
    else:
        print(f"❌ 郵件中未找到正確的日期範圍")
        # 查找實際的日期範圍
        import re
        date_pattern = r"Date Range:\s*([^\n]+)"
        match = re.search(date_pattern, email_body)
        if match:
            print(f"   實際日期範圍: {match.group(1)}")
    
    # 檢查是否包含當前日期（不應該包含）
    current_date = datetime.now().strftime('%Y-%m-%d')
    if current_date in email_body:
        print(f"⚠️  發現當前日期 {current_date} 在郵件中")
    else:
        print(f"✅ 郵件中沒有包含當前日期 {current_date}")
    
    print("\n🎯 測試完成")

if __name__ == "__main__":
    test_date_logic_comparison() 