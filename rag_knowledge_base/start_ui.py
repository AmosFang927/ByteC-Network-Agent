#!/usr/bin/env python3
"""
Ollama Web UI 启动脚本
"""

import subprocess
import sys
import time
import requests
import os

def check_ollama():
    """检查 Ollama 是否运行"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False

def install_dependencies():
    """安装依赖"""
    print("📦 安装 Python 依赖...")
    subprocess.run([sys.executable, "-m", "pip", "install", "streamlit", "requests"])

def start_ui():
    """启动 Web UI"""
    print("🚀 启动 Ollama Web UI...")
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", 
        "simple_ollama_ui.py",
        "--server.port", "8501",
        "--server.address", "localhost"
    ])

def main():
    print("🤖 Ollama Web UI 启动器")
    print("=" * 40)
    
    # 检查 Ollama
    print("🔍 检查 Ollama 服务...")
    if not check_ollama():
        print("❌ Ollama 服务未运行")
        print("请先启动 Ollama: brew services start ollama")
        return
    
    print("✅ Ollama 服务正常运行")
    
    # 安装依赖
    try:
        import streamlit
        import requests
        print("✅ 依赖已安装")
    except ImportError:
        print("📦 安装依赖...")
        install_dependencies()
    
    # 启动 UI
    print("🌐 启动 Web 界面...")
    print("访问地址: http://localhost:8501")
    start_ui()

if __name__ == "__main__":
    main() 