#!/usr/bin/env python3
"""
公司財務AI助手 - Streamlit 啟動腳本
Company Finance AI Assistant - Streamlit Launch Script
"""

import sys
import os
import subprocess
import time
import threading
import requests
from pathlib import Path

# 添加項目根目錄到Python路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

def check_dependencies():
    """檢查必要的依賴包"""
    required_packages = [
        'streamlit',
        'pandas',
        'plotly',
        'requests',
        'flask',
        'asyncio'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ 缺少依賴包: {', '.join(missing_packages)}")
        print("請運行: pip install -r requirements.txt")
        return False
    
    return True

def check_flask_api():
    """檢查Flask API服務是否運行"""
    try:
        response = requests.get("http://localhost:5001/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Flask API 服務正在運行")
            return True
        else:
            print(f"⚠️ Flask API 返回狀態碼: {response.status_code}")
            return False
    except Exception as e:
        print(f"⚠️ Flask API服務未運行，正在啟動...")
        return False

def start_flask_api():
    """啟動Flask API服務"""
    # 確保路徑相對於company-agent目錄
    script_dir = Path(__file__).parent
    company_agent_dir = script_dir.parent
    api_script = company_agent_dir / "backend" / "company_ai_api.py"
    
    if not api_script.exists():
        print(f"❌ 找不到API腳本: {api_script}")
        return False
    
    try:
        print("🚀 啟動Flask API服務...")
        # 在後台啟動Flask API
        subprocess.Popen([
            sys.executable, 
            str(api_script)
        ], 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE
        )
        
        # 等待服務啟動
        time.sleep(5)
        
        # 檢查服務是否啟動成功
        if check_flask_api():
            print("✅ Flask API服務啟動成功")
            return True
        else:
            print("⚠️ Flask API服務啟動中...")
            return True
        
    except Exception as e:
        print(f"❌ 啟動Flask API服務失敗: {e}")
        return False

def run_streamlit_app():
    """運行Streamlit應用"""
    # 確保路徑相對於company-agent目錄
    script_dir = Path(__file__).parent
    company_agent_dir = script_dir.parent
    streamlit_script = company_agent_dir / "frontend" / "streamlit_app.py"
    
    if not streamlit_script.exists():
        print(f"❌ 找不到Streamlit腳本: {streamlit_script}")
        return False
    
    try:
        print("🚀 啟動Streamlit應用...")
        print("🌐 應用將在 http://localhost:8501 啟動")
        print("💡 提示: 按 Ctrl+C 停止服務")
        
        # 使用subprocess.run，但會阻塞直到應用停止
        result = subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            str(streamlit_script),
            "--server.port", "8501",
            "--server.headless", "true"
        ])
        
        if result.returncode == 0:
            print("✅ Streamlit應用正常退出")
        
        return True
        
    except KeyboardInterrupt:
        print("\n👋 Streamlit應用已停止")
        return True
    except Exception as e:
        print(f"❌ 啟動Streamlit應用失敗: {e}")
        return False

def main():
    """主函數"""
    print("🏢 公司財務AI助手 - Streamlit版本")
    print("=" * 50)
    
    print("📦 檢查依賴包...")
    if not check_dependencies():
        sys.exit(1)
    
    print("🔍 檢查Flask API服務...")
    if not check_flask_api():
        if not start_flask_api():
            print("❌ 無法啟動Flask API服務")
            print("請手動運行: python backend/company_ai_api.py")
            sys.exit(1)
    
    # 運行Streamlit應用
    run_streamlit_app()

if __name__ == "__main__":
    main() 