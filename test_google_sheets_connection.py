#!/usr/bin/env python3
"""
测试Google Sheets连接
用于诊断和修复JWT签名错误
"""

import os
import sys
import time
import logging
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(__file__))

try:
    import gspread
    from google.oauth2.service_account import Credentials
    from google.auth.exceptions import RefreshError
    GOOGLE_SHEETS_AVAILABLE = True
except ImportError as e:
    print(f"❌ Google Sheets API 库未安装: {e}")
    print("请运行: pip install gspread google-auth")
    sys.exit(1)

def test_google_sheets_connection():
    """测试Google Sheets连接"""
    print("🔍 Google Sheets连接诊断工具")
    print("=" * 50)
    
    # 检查配置文件
    credentials_file = "solar-idea-463423-h8-bd12ec2c5361.json"
    if not os.path.exists(credentials_file):
        print(f"❌ 凭据文件不存在: {credentials_file}")
        return False
    
    print(f"✅ 凭据文件存在: {credentials_file}")
    
    # 检查系统时间
    current_time = datetime.now()
    print(f"🕐 当前系统时间: {current_time}")
    
    # 检查时间是否合理（2024年）
    if current_time.year != 2024:
        print(f"⚠️  警告: 系统时间异常 (年份: {current_time.year})")
        print("这可能是导致JWT签名错误的原因")
        
        # 建议解决方案
        print("\n💡 建议解决方案:")
        print("1. 手动设置正确的系统时间")
        print("2. 启用网络时间同步")
        print("3. 重新生成Google服务账号密钥")
        
        return False
    
    # 测试Google Sheets API连接
    try:
        print("\n🔄 正在测试Google Sheets API连接...")
        
        # 设置认证范围
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets.readonly',
            'https://www.googleapis.com/auth/drive.readonly'
        ]
        
        # 创建认证
        credentials = Credentials.from_service_account_file(
            credentials_file, 
            scopes=scopes
        )
        
        # 创建客户端
        client = gspread.authorize(credentials)
        print("✅ Google Sheets客户端创建成功")
        
        # 测试访问指定的表格
        spreadsheet_id = "1SaHZ0igiuMBm2gHFD5JSs1hkltphdXqRAlbaZ9nEUf0"
        print(f"\n🔄 正在测试访问表格: {spreadsheet_id}")
        
        spreadsheet = client.open_by_key(spreadsheet_id)
        print(f"✅ 成功打开表格: {spreadsheet.title}")
        
        # 列出所有工作表
        worksheets = spreadsheet.worksheets()
        print(f"📋 发现工作表 ({len(worksheets)} 个):")
        for i, ws in enumerate(worksheets, 1):
            print(f"  {i}. {ws.title}")
        
        # 测试读取数据
        if worksheets:
            first_sheet = worksheets[0]
            print(f"\n🔄 正在测试读取数据 (工作表: {first_sheet.title})...")
            
            # 读取前5行数据
            data = first_sheet.get("A1:Z5")
            print(f"✅ 成功读取数据: {len(data)} 行")
            
            if data:
                print("📄 数据预览:")
                for i, row in enumerate(data[:3], 1):
                    print(f"  行{i}: {row[:5]}...")  # 只显示前5列
        
        print("\n🎉 Google Sheets连接测试完全成功!")
        return True
        
    except RefreshError as e:
        print(f"❌ JWT/认证错误: {e}")
        print("\n💡 可能的解决方案:")
        print("1. 检查系统时间是否正确")
        print("2. 检查Google服务账号是否有效")
        print("3. 检查表格访问权限")
        print("4. 重新生成服务账号密钥")
        return False
        
    except Exception as e:
        print(f"❌ 连接错误: {e}")
        print(f"错误类型: {type(e).__name__}")
        return False

def check_system_environment():
    """检查系统环境"""
    print("\n🔍 系统环境检查")
    print("=" * 30)
    
    # 检查Python版本
    print(f"🐍 Python版本: {sys.version}")
    
    # 检查相关库版本
    try:
        import gspread
        print(f"📊 gspread版本: {gspread.__version__}")
    except:
        print("❌ gspread未安装")
    
    try:
        import google.auth
        print(f"🔐 google-auth版本: {google.auth.__version__}")
    except:
        print("❌ google-auth未安装")
    
    # 检查网络连接
    try:
        import urllib.request
        urllib.request.urlopen('https://www.google.com', timeout=5)
        print("🌐 网络连接: 正常")
    except:
        print("❌ 网络连接: 异常")

def main():
    """主函数"""
    print("🚀 Google Sheets连接诊断工具")
    print("=" * 50)
    
    # 检查系统环境
    check_system_environment()
    
    # 测试连接
    success = test_google_sheets_connection()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 诊断完成: Google Sheets连接正常")
    else:
        print("❌ 诊断完成: 发现问题，请按照建议解决")

if __name__ == "__main__":
    main()
