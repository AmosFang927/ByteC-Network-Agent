#!/usr/bin/env python3
"""
Google Sheets JWT时间修正工具
解决系统时间不准确导致的JWT签名错误
"""

import os
import sys
import json
import time
import datetime
from typing import Optional, Dict, Any

def patch_jwt_timing():
    """修正JWT时间戳问题"""
    # 计算时间偏移量 - 假设当前实际应该是2024年而不是2025年
    # 2025-08-25 应该是 2024-08-25
    current_time = time.time()
    
    # 计算一年的秒数差异 (大约365天)
    year_offset = 365 * 24 * 60 * 60  # 一年的秒数
    
    # 检查是否时间明显错误 (如果时间戳对应的年份是2025年)
    current_year = datetime.datetime.fromtimestamp(current_time).year
    if current_year >= 2025:
        print(f"⚠️ 检测到异常时间: {current_year}年")
        corrected_time = current_time - year_offset
        corrected_datetime = datetime.datetime.fromtimestamp(corrected_time)
        print(f"💡 修正后时间: {corrected_datetime}")
        return corrected_time
    
    return current_time

def create_corrected_jwt_credentials(credentials_file: str) -> Optional[object]:
    """创建修正时间的JWT认证"""
    try:
        from google.oauth2.service_account import Credentials
        import google.auth.jwt as jwt
        import google.auth._helpers as helpers
        
        # 读取认证文件
        with open(credentials_file, 'r') as f:
            service_account_info = json.load(f)
        
        # 设置作用域
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets.readonly',
            'https://www.googleapis.com/auth/drive.readonly'
        ]
        
        # 手动修正JWT时间戳
        original_time = time.time
        
        def corrected_time():
            return patch_jwt_timing()
        
        # 临时替换time.time函数
        time.time = corrected_time
        helpers.utcnow = lambda: datetime.datetime.utcfromtimestamp(corrected_time())
        
        try:
            # 创建认证
            credentials = Credentials.from_service_account_info(
                service_account_info, 
                scopes=scopes
            )
            
            print("✅ JWT认证创建成功（使用修正时间）")
            return credentials
            
        finally:
            # 恢复原始time函数
            time.time = original_time
            
    except Exception as e:
        print(f"❌ JWT认证修正失败: {e}")
        return None

def test_google_sheets_connection():
    """测试Google Sheets连接"""
    try:
        credentials_file = 'solar-idea-463423-h8-bd12ec2c5361.json'
        
        if not os.path.exists(credentials_file):
            print(f"❌ 认证文件不存在: {credentials_file}")
            return False
        
        # 尝试使用修正的认证
        credentials = create_corrected_jwt_credentials(credentials_file)
        if not credentials:
            return False
        
        # 测试Google Sheets连接
        import gspread
        gc = gspread.authorize(credentials)
        
        # 尝试打开测试表格
        spreadsheet_id = '1SaHZ0igiuMBm2gHFD5JSs1hkltphdXqRAlbaZ9nEUf0'
        spreadsheet = gc.open_by_key(spreadsheet_id)
        worksheet = spreadsheet.worksheet('Data_Input_Mapping')
        
        # 读取少量数据测试
        test_data = worksheet.get('A1:C1')
        print(f"✅ Google Sheets连接测试成功")
        print(f"📊 测试数据: {test_data}")
        
        return True
        
    except Exception as e:
        print(f"❌ Google Sheets连接测试失败: {e}")
        return False

if __name__ == "__main__":
    print("=== Google Sheets JWT时间修正工具 ===")
    
    # 显示当前时间状态
    current_time = time.time()
    current_datetime = datetime.datetime.fromtimestamp(current_time)
    corrected_time = patch_jwt_timing()
    corrected_datetime = datetime.datetime.fromtimestamp(corrected_time)
    
    print(f"当前系统时间: {current_datetime}")
    print(f"修正后时间: {corrected_datetime}")
    print(f"时间差: {(current_time - corrected_time) / 3600:.1f} 小时")
    
    # 测试连接
    print("\n开始测试Google Sheets连接...")
    success = test_google_sheets_connection()
    
    if success:
        print("\n🎉 修复成功！可以正常使用Google Sheets了")
    else:
        print("\n⚠️ 修复失败，建议检查系统时间设置")