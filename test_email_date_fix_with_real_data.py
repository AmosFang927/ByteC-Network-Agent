#!/usr/bin/env python3
"""
使用實際Excel文件的郵件日期修復測試
驗證郵件中的日期範圍顯示是否正確
"""

import sys
import os
from datetime import datetime

# 添加項目根目錄到 Python 路徑
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from agents.data_output_agent.email_sender import EmailSender

def test_email_date_fix_with_real_data():
    """使用實際Excel文件測試郵件日期修復"""
    print("🧪 開始使用實際Excel文件的郵件日期修復測試")
    
    # 創建 EmailSender 實例
    email_sender = EmailSender()
    
    # 使用實際的Excel文件
    excel_file = "output/RAMPUP_ConversionReport_2025-07-26_to_2025-07-26.xlsx"
    
    if not os.path.exists(excel_file):
        print(f"❌ Excel文件不存在: {excel_file}")
        return
    
    print(f"✅ 使用實際Excel文件: {excel_file}")
    
    # 測試數據 - 模擬實際的郵件數據
    partner_name = "RAMPUP"
    partner_data = {
        'records': 0,  # 實際數據為0
        'amount_formatted': '$0.00',
        'file_path': excel_file,
        'sources': ['RAMPUP'],
        'sources_count': 1,
        'invalid_stats': {'invalid_count': 0, 'invalid_amount': 0.0}
    }
    
    # 正確的日期參數
    start_date = '2025-07-26'
    end_date = '2025-07-26'
    
    print(f"\n📅 測試日期:")
    print(f"   開始日期: {start_date}")
    print(f"   結束日期: {end_date}")
    print(f"   預期日期範圍: 2025-07-26 to 2025-07-26")
    
    # 測試 _prepare_partner_email_data 方法
    print("\n" + "="*60)
    print("📧 測試 _prepare_partner_email_data 方法")
    print("="*60)
    
    email_data = email_sender._prepare_partner_email_data(
        partner_name=partner_name,
        partner_data=partner_data,
        end_date=end_date,
        start_date=start_date
    )
    
    print(f"✅ Email 數據準備結果:")
    print(f"   start_date: '{email_data['start_date']}'")
    print(f"   end_date: '{email_data['end_date']}'")
    print(f"   report_date: '{email_data['report_date']}'")
    print(f"   total_records: {email_data['total_records']}")
    print(f"   total_amount: {email_data['total_amount']}")
    
    # 測試郵件生成
    print("\n" + "="*60)
    print("📧 測試郵件內容生成")
    print("="*60)
    
    email_body = email_sender._generate_partner_email_body(partner_name, email_data, {})
    
    # 檢查郵件內容中的日期
    print("\n📧 生成的郵件內容片段:")
    print("="*50)
    
    # 查找日期範圍行
    lines = email_body.split('\n')
    for i, line in enumerate(lines):
        if "Date Range:" in line:
            print(f"   第 {i+1} 行: {line.strip()}")
            break
    
    # 檢查是否包含正確的日期範圍
    expected_date_range = "2025-07-26 to 2025-07-26"
    if expected_date_range in email_body:
        print(f"✅ 郵件包含正確的日期範圍: {expected_date_range}")
    else:
        print(f"❌ 郵件中未找到正確的日期範圍: {expected_date_range}")
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
        # 查找所有日期出現的位置
        for i, line in enumerate(lines):
            if current_date in line:
                print(f"   第 {i+1} 行: {line.strip()}")
    else:
        print(f"✅ 郵件中沒有包含當前日期 {current_date}")
    
    # 檢查 completion_time
    if "Generated at:" in email_body:
        print("✅ 郵件包含 'Generated at:' 標籤")
        # 提取生成時間行
        for line in lines:
            if "Generated at:" in line:
                print(f"   生成時間行: {line.strip()}")
                break
    else:
        print("❌ 郵件中沒有找到 'Generated at:' 標籤")
    
    # 檢查其他重要信息
    print("\n📊 郵件內容摘要:")
    print("="*30)
    
    # 檢查總記錄數
    if "Total Conversions (All Status):" in email_body:
        print("✅ 包含總轉化數統計")
    else:
        print("❌ 缺少總轉化數統計")
    
    # 檢查有效轉化數
    if "Total Conversions (Pending/Approved):" in email_body:
        print("✅ 包含有效轉化數統計")
    else:
        print("❌ 缺少有效轉化數統計")
    
    # 檢查金額統計
    if "Total Sale Amount (USD) (Pending/Approved):" in email_body:
        print("✅ 包含有效金額統計")
    else:
        print("❌ 缺少有效金額統計")
    
    print("\n🎯 測試完成")

if __name__ == "__main__":
    test_email_date_fix_with_real_data() 