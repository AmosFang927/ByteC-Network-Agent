#!/usr/bin/env python3
"""
公司財務AI助手 - 測試腳本
Company Finance AI Assistant - Test Script
"""

import sys
import os
import requests
import time
import subprocess
import importlib.util
from pathlib import Path

# 添加項目根目錄到Python路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(project_root)
sys.path.append(current_dir)

def test_dependencies():
    """測試依賴包是否正確安裝"""
    print("🔍 測試依賴包...")
    
    required_packages = [
        'streamlit',
        'pandas',
        'plotly',
        'requests',
        'flask',
        'flask_cors',
        'aiohttp',
        'asyncpg'
    ]
    
    all_good = True
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package} - 已安裝")
        except ImportError:
            print(f"❌ {package} - 未安裝")
            all_good = False
    
    return all_good

def test_config_file():
    """測試配置文件是否正確"""
    print("\n🔍 測試配置文件...")
    
    try:
        # 嘗試直接導入本地配置
        import importlib.util
        spec = importlib.util.spec_from_file_location("streamlit_config", "config/streamlit_config.py")
        config_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config_module)
        config = config_module.config
        
        print("✅ streamlit_config.py - 導入成功")
        
        # 檢查主要配置項
        if hasattr(config, 'APP_TITLE'):
            print(f"✅ APP_TITLE: {config.APP_TITLE}")
        else:
            print("❌ APP_TITLE - 未定義")
            
        return True
    except Exception as e:
        print(f"❌ streamlit_config.py - 導入失敗: {e}")
        return False

def test_backend_modules():
    """測試後端模組是否正確"""
    print("\n🔍 測試後端模組...")
    
    try:
        from main import CompanyManagerAgent
        print("✅ CompanyManagerAgent - 導入成功")
        
        from backend.company_ai_api import app
        print("✅ Flask app - 導入成功")
        
        return True
    except ImportError as e:
        print(f"❌ 後端模組導入失敗: {e}")
        return False

def test_file_structure():
    """測試文件結構是否完整"""
    print("\n🔍 測試文件結構...")
    
    files_to_check = [
        "main.py",
        "backend/company_ai_api.py",
        "frontend/streamlit_app.py",
        "config/streamlit_config.py",
        "scripts/run_streamlit.py"
    ]
    
    all_good = True
    for file_path in files_to_check:
        if Path(file_path).exists():
            print(f"✅ {file_path} - 存在")
        else:
            print(f"❌ {file_path} - 不存在")
            all_good = False
    
    return all_good

def run_syntax_check():
    """運行語法檢查"""
    print("\n🔍 運行語法檢查...")
    
    files_to_check = [
        "main.py",
        "backend/company_ai_api.py",
        "frontend/streamlit_app.py",
        "config/streamlit_config.py",
        "scripts/run_streamlit.py"
    ]
    
    all_good = True
    for file_path in files_to_check:
        if not Path(file_path).exists():
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                compile(f.read(), file_path, 'exec')
        except SyntaxError as e:
            print(f"❌ {file_path} - 語法錯誤: {e}")
            all_good = False
    
    if all_good:
        print("✅ 語法檢查 - 通過")
    else:
        print("❌ 語法檢查 - 失敗")
    
    return all_good

def test_frontend_modules():
    """測試前端模塊是否正常"""
    print("\n🔍 測試前端模塊...")
    
    streamlit_script = Path("frontend/streamlit_app.py")
    
    if not streamlit_script.exists():
        print(f"❌ 找不到Streamlit腳本: {streamlit_script}")
        return False
    
    try:
        print("✅ Streamlit腳本 - 存在")
        return True
    except Exception as e:
        print(f"❌ 前端模塊測試失敗: {e}")
        return False

def test_api_connection():
    """測試API連接"""
    print("\n🔍 測試API連接...")
    
    try:
        # 嘗試直接導入本地配置
        import importlib.util
        spec = importlib.util.spec_from_file_location("streamlit_config", "config/streamlit_config.py")
        config_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config_module)
        config = config_module.config
        
        health_url = config.get_api_url("/api/health")
        
        response = requests.get(health_url, timeout=5)
        if response.status_code == 200:
            print("✅ API健康檢查通過")
            return True
        else:
            print(f"⚠️ API返回狀態碼: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ API連接測試失敗: {e}")
        return False

def test_launch_scripts():
    """測試啟動腳本是否存在"""
    print("\n🔍 測試啟動腳本...")
    
    scripts = [
        "scripts/run_streamlit.py",
        "scripts/run_company_ai_assistant.py"
    ]
    
    all_good = True
    for script in scripts:
        if Path(script).exists():
            print(f"✅ {script} - 存在")
        else:
            print(f"❌ {script} - 不存在")
            all_good = False
    
    return all_good

def main():
    """主測試函數"""
    print("🧪 公司財務AI助手 - 測試程序")
    print("=" * 50)
    
    tests = [
        ("依賴包測試", test_dependencies),
        ("文件結構測試", test_file_structure),
        ("語法檢查", run_syntax_check),
        ("配置文件測試", test_config_file),
        ("後端模塊測試", test_backend_modules),
        ("前端模塊測試", test_frontend_modules),
        ("啟動腳本測試", test_launch_scripts),
        ("API連接測試", test_api_connection)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} - 通過")
            else:
                failed += 1
                print(f"❌ {test_name} - 失敗")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name} - 異常: {e}")
    
    print("\n" + "=" * 50)
    print(f"🎯 測試結果: {passed} 通過, {failed} 失敗")
    
    if failed == 0:
        print("🎉 所有測試通過！系統已準備就緒")
        print("\n🚀 啟動方法:")
        print("cd agents/company-agent")
        print("python scripts/run_streamlit.py")
        print("或")
        print("python scripts/run_company_ai_assistant.py")
    else:
        print("⚠️ 部分測試失敗，請檢查上述問題")
        
        if failed > 0:
            print("\n🔧 建議解決方案:")
            print("1. 安裝依賴: pip install -r agents/company-agent/requirements.txt")
            print("2. 檢查文件是否完整")
            print("3. 確認配置文件正確")
            print("4. 檢查導入路徑是否正確")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 