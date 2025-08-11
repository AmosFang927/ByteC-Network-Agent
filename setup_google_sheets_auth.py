#!/usr/bin/env python3
"""
Google Sheets OAuth認證設置助手
"""

import os
import json
import logging

def create_oauth_instructions():
    """創建OAuth設置說明"""
    
    print('🔐 Google Sheets OAuth認證設置指南')
    print('=' * 60)
    
    print('''
📋 步驟1: 在Google Cloud Console創建OAuth憑證

1. 前往 Google Cloud Console: https://console.cloud.google.com/
2. 選擇或創建一個項目
3. 啟用 Google Sheets API 和 Google Drive API
4. 前往 "APIs & Services" > "Credentials"
5. 點擊 "Create Credentials" > "OAuth client ID"
6. 選擇 "Desktop application"
7. 下載credentials.json文件

📋 步驟2: 設置憑證文件

將下載的credentials.json文件放置到以下位置之一:
''')
    
    config_dir = os.path.expanduser('~/.config/gspread')
    print(f'   推薦: {config_dir}/credentials.json')
    print(f'   或者: {os.getcwd()}/config/credentials.json')
    print(f'   或者: {os.getcwd()}/credentials.json')
    
    print(f'''
📋 步驟3: 創建配置目錄

運行以下命令創建必要的目錄:
   mkdir -p {config_dir}

📋 步驟4: 測試認證

配置完成後，運行:
   python update_google_sheets_mapping.py

🔗 詳細設置指南:
https://docs.gspread.org/en/latest/oauth2.html
''')

def setup_local_credentials_template():
    """設置本地憑證模板"""
    
    config_dir = os.path.expanduser('~/.config/gspread')
    
    print(f'📁 創建配置目錄: {config_dir}')
    
    try:
        os.makedirs(config_dir, exist_ok=True)
        print(f'✅ 配置目錄已創建')
        
        # 創建憑證模板文件
        template_path = os.path.join(config_dir, 'credentials_template.json')
        
        template = {
            "installed": {
                "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
                "project_id": "your-project-id",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_secret": "YOUR_CLIENT_SECRET",
                "redirect_uris": ["http://localhost"]
            }
        }
        
        with open(template_path, 'w', encoding='utf-8') as f:
            json.dump(template, f, indent=2)
        
        print(f'📄 憑證模板已創建: {template_path}')
        print(f'   請將其重命名為 credentials.json 並填入正確的值')
        
    except Exception as e:
        print(f'❌ 創建配置目錄失敗: {e}')

def check_current_setup():
    """檢查當前設置狀態"""
    
    print('🔍 檢查當前Google Sheets認證設置')
    print('=' * 60)
    
    possible_paths = [
        os.path.expanduser('~/.config/gspread/credentials.json'),
        os.path.expanduser('~/.config/gspread/service_account.json'),
        'config/credentials.json',
        'credentials.json',
        'config/service-account-key.json',
        'service-account-key.json'
    ]
    
    found_files = []
    
    for path in possible_paths:
        if os.path.exists(path):
            found_files.append(path)
            print(f'✅ 找到憑證文件: {path}')
    
    if not found_files:
        print('❌ 未找到任何憑證文件')
        print('\n需要設置OAuth認證才能寫入Google Sheets')
    else:
        print(f'\n📊 總共找到 {len(found_files)} 個憑證文件')
    
    # 測試gspread導入
    try:
        import gspread
        print('✅ gspread庫已安裝')
    except ImportError:
        print('❌ gspread庫未安裝，請運行: pip install gspread')
    
    # 測試google-auth導入
    try:
        from google.oauth2.service_account import Credentials
        print('✅ google-auth庫已安裝')
    except ImportError:
        print('❌ google-auth庫未安裝，請運行: pip install google-auth')

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'check':
            check_current_setup()
        elif sys.argv[1] == 'setup':
            setup_local_credentials_template()
        elif sys.argv[1] == 'help':
            create_oauth_instructions()
    else:
        print('🚀 Google Sheets認證設置助手')
        print()
        check_current_setup()
        print()
        setup_local_credentials_template()
        print()
        create_oauth_instructions()