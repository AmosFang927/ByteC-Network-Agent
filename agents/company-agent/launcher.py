#!/usr/bin/env python3
"""
公司財務AI助手 - 主程式
Company Finance AI Assistant - Main Program
"""

import sys
import os
import subprocess
import time
from pathlib import Path

def main():
    """主函數"""
    print("🏢 公司財務AI助手 - 快速啟動")
    print("=" * 50)
    
    # 檢查當前目錄是否為company-agent目錄
    current_dir = Path.cwd()
    if not current_dir.name.endswith("company-agent"):
        print("❌ 請在agents/company-agent目錄中運行此腳本")
        sys.exit(1)
    
    # 提供選項
    print("請選擇啟動方式:")
    print("1. 🚀 啟動Streamlit應用 (推薦)")
    print("2. 🔧 啟動Flask API服務")
    print("3. 🧪 運行測試")
    print("4. 📚 查看文檔")
    print("5. 🔍 檢查系統狀態")
    
    choice = input("\n請輸入選項 (1-5): ").strip()
    
    if choice == "1":
        print("\n🚀 啟動Streamlit應用...")
        try:
            # 使用Popen在後台啟動
            process = subprocess.Popen([sys.executable, "scripts/run_streamlit.py"])
            print("✅ Streamlit應用已在後台啟動")
            print("🌐 訪問地址: http://localhost:8501")
            print("💡 提示: 按 Ctrl+C 停止服務")
            
            # 等待用戶停止
            try:
                process.wait()
            except KeyboardInterrupt:
                print("\n🛑 正在停止服務...")
                process.terminate()
                process.wait()
                print("👋 服務已停止")
                
        except Exception as e:
            print(f"❌ 啟動失敗: {e}")
            
    elif choice == "2":
        print("\n🔧 啟動Flask API服務...")
        try:
            # 使用Popen在後台啟動
            process = subprocess.Popen([sys.executable, "scripts/run_company_ai_assistant.py"])
            print("✅ Flask API服務已在後台啟動")
            print("🌐 API地址: http://localhost:5001")
            print("💡 提示: 按 Ctrl+C 停止服務")
            
            # 等待用戶停止
            try:
                process.wait()
            except KeyboardInterrupt:
                print("\n🛑 正在停止服務...")
                process.terminate()
                process.wait()
                print("👋 服務已停止")
                
        except Exception as e:
            print(f"❌ 啟動失敗: {e}")
            
    elif choice == "3":
        print("\n🧪 運行測試...")
        subprocess.run([sys.executable, "test_app.py"])
        
    elif choice == "4":
        print("\n📚 文檔位置:")
        print(f"- 主文檔: docs/README.md")
        print(f"- Streamlit說明: docs/STREAMLIT_README.md")
        print("\n可以用文本編輯器打開查看")
        
    elif choice == "5":
        print("\n🔍 系統狀態檢查...")
        # 簡單的狀態檢查
        required_files = [
            "main.py",
            "backend/company_ai_api.py",
            "frontend/streamlit_app.py",
            "config/streamlit_config.py",
            "requirements.txt"
        ]
        
        all_good = True
        for file_path in required_files:
            if Path(file_path).exists():
                print(f"✅ {file_path}")
            else:
                print(f"❌ {file_path}")
                all_good = False
        
        if all_good:
            print("\n✅ 系統文件完整，可以正常使用")
        else:
            print("\n❌ 系統文件不完整，請檢查安裝")
    else:
        print("❌ 無效選項")
        sys.exit(1)

if __name__ == "__main__":
    main() 