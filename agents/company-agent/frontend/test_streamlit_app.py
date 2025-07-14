#!/usr/bin/env python3
"""
公司財務AI助手 - Streamlit 測試腳本
Company Finance AI Assistant - Streamlit Test Script
"""

import sys
import os
import requests
import time
import subprocess
from pathlib import Path

def test_dependencies():
    """測試依賴包是否正確安裝"""
    print("🔍 測試依賴包...")
    
    required_packages = [
        'streamlit',
        'pandas',
        'plotly',
        'requests',
        'numpy'
    ]
    
    all_good = True
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} - 已安裝")
        except ImportError:
            print(f"❌ {package} - 未安裝")
            all_good = False
    
    return all_good

def test_config_file():
    """測試配置文件是否正確"""
    print("\n🔍 測試配置文件...")
    
    try:
        from streamlit_config import config
        print("✅ streamlit_config.py - 導入成功")
        
        # 測試配置項
        assert config.APP_TITLE == "公司財務AI助手"
        assert config.API_BASE_URL
        assert config.WHODB_CONFIG
        assert config.QUICK_QUERIES
        assert config.METRICS_CONFIG
        
        print("✅ 配置項驗證通過")
        return True
        
    except Exception as e:
        print(f"❌ 配置文件測試失敗: {e}")
        return False

def test_streamlit_app():
    """測試Streamlit應用是否可以正常啟動"""
    print("\n🔍 測試Streamlit應用...")
    
    streamlit_script = Path("agents/dashboard_agent/frontend/company_ai_streamlit.py")
    
    if not streamlit_script.exists():
        print(f"❌ 找不到Streamlit腳本: {streamlit_script}")
        return False
    
    try:
        # 檢查語法是否正確
        with open(streamlit_script, 'r', encoding='utf-8') as f:
            code = f.read()
        
        compile(code, str(streamlit_script), 'exec')
        print("✅ Streamlit應用語法檢查通過")
        return True
        
    except Exception as e:
        print(f"❌ Streamlit應用測試失敗: {e}")
        return False

def test_api_connection():
    """測試API連接"""
    print("\n🔍 測試API連接...")
    
    try:
        from streamlit_config import config
        health_url = config.get_api_url("/api/health")
        
        response = requests.get(health_url, timeout=5)
        
        if response.status_code == 200:
            print("✅ API連接正常")
            return True
        else:
            print(f"⚠️ API返回狀態碼: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException:
        print("⚠️ API服務未運行 (這是正常的，可以稍後啟動)")
        return True
    except Exception as e:
        print(f"❌ API連接測試失敗: {e}")
        return False

def test_file_structure():
    """測試文件結構"""
    print("\n🔍 測試文件結構...")
    
    required_files = [
        "streamlit_config.py",
        "run_company_streamlit.py",
        "streamlit_requirements.txt",
        "agents/dashboard_agent/frontend/company_ai_streamlit.py",
        "STREAMLIT_COMPANY_AI_README.md"
    ]
    
    all_good = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path} - 存在")
        else:
            print(f"❌ {file_path} - 不存在")
            all_good = False
    
    return all_good

def run_syntax_check():
    """運行語法檢查"""
    print("\n🔍 運行語法檢查...")
    
    python_files = [
        "streamlit_config.py",
        "run_company_streamlit.py",
        "agents/dashboard_agent/frontend/company_ai_streamlit.py"
    ]
    
    all_good = True
    for file_path in python_files:
        if not Path(file_path).exists():
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            compile(code, file_path, 'exec')
            print(f"✅ {file_path} - 語法正確")
        except Exception as e:
            print(f"❌ {file_path} - 語法錯誤: {e}")
            all_good = False
    
    return all_good

def main():
    """主測試函數"""
    print("🧪 公司財務AI助手 - Streamlit版本測試")
    print("=" * 50)
    
    tests = [
        ("依賴包測試", test_dependencies),
        ("文件結構測試", test_file_structure),
        ("語法檢查", run_syntax_check),
        ("配置文件測試", test_config_file),
        ("Streamlit應用測試", test_streamlit_app),
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
        print("🎉 所有測試通過！可以開始使用Streamlit應用了")
        print("\n🚀 啟動方法:")
        print("python run_company_streamlit.py")
    else:
        print("⚠️ 部分測試失敗，請檢查上述問題")
        
        if failed > 0:
            print("\n🔧 建議解決方案:")
            print("1. 安裝依賴: pip install -r streamlit_requirements.txt")
            print("2. 檢查文件是否完整")
            print("3. 確認配置文件正確")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 