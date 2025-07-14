"""
Spider Agent 配置設定
"""

import os
from typing import Dict, Any

class SpiderConfig:
    """Spider Agent 設定類"""
    
    # 目標網站設定
    TARGET_URL = "https://app.involve.asia/publisher/report"
    LOGIN_URL = "https://app.involve.asia/login"
    
    # 輸出設定
    OUTPUT_DIR = "agents/spider_agent/output"
    SCREENSHOTS_DIR = f"{OUTPUT_DIR}/screenshots"
    ASSETS_DIR = f"{OUTPUT_DIR}/assets"
    STRUCTURE_DIR = f"{OUTPUT_DIR}/structure"
    
    # 爬取設定
    WAIT_TIMEOUT = 30000  # 30秒
    NAVIGATION_TIMEOUT = 60000  # 60秒
    
    # Google SSO 設定
    GOOGLE_LOGIN_SELECTOR = "button[data-provider='google']"
    EMAIL_SELECTOR = "input[type='email']"
    PASSWORD_SELECTOR = "input[type='password']"
    
    # 報告頁面選擇器
    REPORT_MENU_SELECTOR = "a[href*='report']"
    PERFORMANCE_REPORT_SELECTOR = "a[href*='performance']"
    
    # 瀏覽器設定
    BROWSER_CONFIG = {
        "headless": False,  # 顯示瀏覽器以便處理登入
        "viewport": {"width": 1920, "height": 1080},
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    @classmethod
    def ensure_output_dirs(cls):
        """確保輸出目錄存在"""
        os.makedirs(cls.OUTPUT_DIR, exist_ok=True)
        os.makedirs(cls.SCREENSHOTS_DIR, exist_ok=True)
        os.makedirs(cls.ASSETS_DIR, exist_ok=True)
        os.makedirs(cls.STRUCTURE_DIR, exist_ok=True)
        
    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """獲取完整設定字典"""
        return {
            "target_url": cls.TARGET_URL,
            "login_url": cls.LOGIN_URL,
            "output_dir": cls.OUTPUT_DIR,
            "screenshots_dir": cls.SCREENSHOTS_DIR,
            "assets_dir": cls.ASSETS_DIR,
            "structure_dir": cls.STRUCTURE_DIR,
            "wait_timeout": cls.WAIT_TIMEOUT,
            "navigation_timeout": cls.NAVIGATION_TIMEOUT,
            "browser_config": cls.BROWSER_CONFIG
        } 