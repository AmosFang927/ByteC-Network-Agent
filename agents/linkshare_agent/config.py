"""
TikTok Shop 聯盟行銷 Agent 配置文件
包含 API 認證資訊、Token 管理設定等
"""

import os
from pathlib import Path

# ================================
# TikTok Shop API 基本配置
# ================================

# App 認證資訊 (由用戶提供)
APP_KEY = "6gtqs1d5dtkka"
APP_SECRET = "5965f7f420ae4ffe33eff2f48e31a7fb62a76139"
REDIRECT_URL = "https://bytec-postback-agent-472712465571.asia-southeast1.run.app"
AUTH_CODE = "ROW_zrhDPAAAAABE_Ppf1X4y3-0HZBvKa934lbOqPRGhDryxogAKf4eCX8Q-c8nBCcFyAdmlWQGd_8Dc5OOlhAns3GR3H8KAxGKA"

# API 版本
APP_VERSION = "202501"

# TikTok Shop API URLs
AUTH_BASE_URL = "https://auth.tiktok-shops.com"
API_BASE_URL = "https://open-api.tiktokglobalshop.com"

# API Endpoints
TOKEN_GET_URL = f"{AUTH_BASE_URL}/api/v2/token/get"
TOKEN_REFRESH_URL = f"{AUTH_BASE_URL}/api/v2/token/refresh" 
LINK_GENERATE_URL = f"{API_BASE_URL}/affiliate_creator/{APP_VERSION}/affiliate_sharing_links/generate_batch"

# ================================
# Token 管理配置
# ================================

# Token 存儲文件路徑
TOKEN_STORAGE_FILE = os.path.join(os.path.dirname(__file__), "tokens.conf")

# Token 有效期設定 (24小時 = 86400秒)
TOKEN_EXPIRE_TIME = 86400
TOKEN_REFRESH_BUFFER = 3600  # 提前1小時刷新

# Token 初始值 (將在首次獲取後更新)
access_token = ""
refresh_token = ""

# ================================
# API 請求配置 
# ================================

# 請求超時設定 (秒)
REQUEST_TIMEOUT = 30
CONNECT_TIMEOUT = 10

# 重試配置
MAX_RETRIES = 3
RETRY_DELAY = 1  # 初始延遲時間 (秒)
RETRY_BACKOFF = 2  # 退避倍數

# ================================
# 聯盟連結生成配置
# ================================

# 默認產品 ID (用於測試)
DEFAULT_PRODUCT_ID = "1731493745807886173"

# 默認 Campaign URL 模板
CAMPAIGN_URL_TEMPLATE = "https://shop.tiktok.com/view/product/{product_id}"

# 默認 Channel 和 Tags
DEFAULT_CHANNEL = "OEM3_OPPO"
DEFAULT_TAGS = ["OEM3_OPPO_PUSH", "OEM2_VIVO_PUSH"]

# 材料類型
MATERIAL_TYPE_PRODUCT = "1"

# ================================
# 日誌配置
# ================================

# 日誌級別
LOG_LEVEL = "INFO"

# 日誌格式
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# ================================
# 錯誤處理配置
# ================================

# API 錯誤碼對應
API_ERROR_CODES = {
    16661001: "標籤無效",
    40001: "參數錯誤", 
    40003: "簽名錯誤",
    40004: "時間戳過期",
    50000: "內部服務錯誤",
    98001004: "參數無效 (可能是 auth_code 過期)",
    98001005: "授權碼已使用",
    98001006: "refresh_token 無效或過期",
    36004004: "無效的授權碼 (auth_code 已過期或不正確)",
    36009004: "訪問令牌頭部無效",
    106001: "簽名參數無效"
}

# ================================
# 輔助函數
# ================================

def get_token_storage_path():
    """獲取 Token 存儲文件的完整路徑"""
    return Path(TOKEN_STORAGE_FILE).resolve()

def is_development():
    """判斷是否為開發環境"""
    return os.getenv("ENVIRONMENT", "production") == "development"

def get_log_level():
    """獲取日誌級別"""
    return os.getenv("LOG_LEVEL", LOG_LEVEL)

# ================================
# 配置驗證
# ================================

def validate_config():
    """驗證配置是否完整"""
    required_configs = [
        ("APP_KEY", APP_KEY),
        ("APP_SECRET", APP_SECRET), 
        ("REDIRECT_URL", REDIRECT_URL),
        ("AUTH_CODE", AUTH_CODE)
    ]
    
    missing_configs = []
    for name, value in required_configs:
        if not value or value.strip() == "":
            missing_configs.append(name)
    
    if missing_configs:
        raise ValueError(f"缺少必要配置: {', '.join(missing_configs)}")
    
    return True

# 在模組載入時驗證配置
if __name__ != "__main__":
    validate_config() 