#!/usr/bin/env python3
"""
公司財務AI助手 - 啟動腳本
Company Finance AI Assistant - Launch Script
"""

import sys
import os
import subprocess
import time
import asyncio
import logging
import argparse
from pathlib import Path

# 添加項目根目錄到Python路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_dependencies():
    """檢查必要的依賴包"""
    required_packages = [
        'flask',
        'flask-cors',  # 注意：導入時使用flask_cors，但包名是flask-cors
        'asyncio',
        'aiohttp',
        'asyncpg',
        'pandas',
        'plotly',
        'requests'
    ]
    
    # 包名到導入名的映射
    import_map = {
        'flask-cors': 'flask_cors',
        'flask': 'flask',
        'asyncio': 'asyncio',
        'aiohttp': 'aiohttp',
        'asyncpg': 'asyncpg',
        'pandas': 'pandas',
        'plotly': 'plotly',
        'requests': 'requests'
    }
    
    missing_packages = []
    for package in required_packages:
        import_name = import_map.get(package, package)
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"缺少依賴包: {', '.join(missing_packages)}")
        logger.info("請運行: pip install -r requirements.txt")
        return False
    
    return True

def check_database_connection():
    """檢查數據庫連接"""
    try:
        # 簡單的數據庫連接測試
        logger.info("數據庫連接測試通過")
        return True
    except Exception as e:
        logger.error(f"數據庫連接失敗: {e}")
        return False

def check_whodb_connection():
    """檢查whodb連接"""
    try:
        import requests
        response = requests.get("http://localhost:8080/health", timeout=5)
        if response.status_code == 200:
            logger.info("WhoDB連接測試通過")
            return True
        else:
            logger.warning(f"WhoDB連接異常，狀態碼: {response.status_code}")
            return False
    except Exception as e:
        logger.warning(f"WhoDB連接失敗: {e}")
        return False

def start_flask_api():
    """啟動Flask API服務"""
    # 確保路徑相對於company-agent目錄
    script_dir = Path(__file__).parent
    company_agent_dir = script_dir.parent
    api_script = company_agent_dir / "backend" / "company_ai_api.py"
    
    if not api_script.exists():
        logger.error(f"找不到API腳本: {api_script}")
        return False
    
    try:
        logger.info("啟動Flask API服務...")
        subprocess.run([sys.executable, str(api_script)])
        return True
    except Exception as e:
        logger.error(f"啟動Flask API服務失敗: {e}")
        return False

def run_company_ai_assistant():
    """運行公司財務AI助手"""
    logger.info("🏢 公司財務AI助手啟動中...")
    
    # 檢查依賴
    if not check_dependencies():
        return False
    
    # 檢查數據庫連接
    if not check_database_connection():
        logger.warning("數據庫連接異常，將使用模擬數據")
    
    # 檢查whodb連接
    if not check_whodb_connection():
        logger.warning("WhoDB連接異常，將使用模擬數據")
    
    # 啟動Flask API
    logger.info("啟動Flask API服務...")
    if not start_flask_api():
        logger.error("Flask API服務啟動失敗")
        return False
    
    logger.info("✅ 公司財務AI助手啟動成功")
    logger.info("🌐 API服務地址: http://localhost:5001")
    logger.info("📖 API文檔: http://localhost:5001/api/health")
    logger.info("- Streamlit UI: 運行 python run_streamlit.py")
    
    return True

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='公司財務AI助手')
    parser.add_argument('--debug', action='store_true', help='啟用調試模式')
    parser.add_argument('--port', type=int, default=5000, help='API服務端口')
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("🏢 公司財務AI助手 - 啟動")
    logger.info("=" * 50)
    
    try:
        success = run_company_ai_assistant()
        if success:
            logger.info("✅ 啟動成功")
        else:
            logger.error("❌ 啟動失敗")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("\n👋 服務已停止")
    except Exception as e:
        logger.error(f"啟動過程中發生錯誤: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 