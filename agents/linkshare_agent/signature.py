"""
TikTok Shop API 簽名生成模組
"""

import json
import hmac
import hashlib
import logging
from typing import Dict, Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

def generate_sign_sdk_style(request_option: Dict[str, Any], app_secret: str) -> str:
    """
    SDK 風格的簽名生成 - 完全按照 Node.js SDK 邏輯實現
    
    參考 Node.js SDK: utils/generate-sign.ts
    """
    logger.info("🔐 開始生成 SDK 風格的 HMAC-SHA256 簽名...")
    
    # SDK 中的排除鍵：excludeKeys = ["access_token", "sign"]
    exclude_keys = ["access_token", "sign"]
    
    sign_string = ""
    
    # Step 1: Extract all query parameters excluding sign and access_token. 
    # Reorder the parameter keys in alphabetical order:
    params = request_option.get('qs', {})
    
    # 過濾掉排除的鍵，然後按字母順序排序
    filtered_keys = [key for key in params.keys() if key not in exclude_keys]
    sorted_keys = sorted(filtered_keys)
    sorted_params = [{"key": key, "value": params[key]} for key in sorted_keys]
    
    logger.debug(f"📝 Step 1 - 參數過濾和排序:")
    logger.debug(f"   原始參數: {list(params.keys())}")
    logger.debug(f"   排除鍵: {exclude_keys}")
    logger.debug(f"   過濾後鍵: {filtered_keys}")
    logger.debug(f"   排序後鍵: {sorted_keys}")
    
    # Step 2: Concatenate all the parameters in the format {key}{value}:
    param_string = ''.join([f"{item['key']}{item['value']}" for item in sorted_params])
    sign_string += param_string
    
    logger.debug(f"📝 Step 2 - 參數拼接:")
    logger.debug(f"   參數字符串: {param_string}")
    
    # Step 3: Append the string from Step 2 to the API request path:
    # const pathname = new URL(requestOption!.uri!||'').pathname;
    uri = request_option.get('uri', '')
    pathname = urlparse(uri).path if uri else ''
    sign_string = f"{pathname}{param_string}"
    
    logger.debug(f"📝 Step 3 - 附加 API 路徑:")
    logger.debug(f"   URI: {uri}")
    logger.debug(f"   路徑: {pathname}")
    logger.debug(f"   路徑+參數: {sign_string}")
    
    # Step 4: If the request header content_type is not multipart/form-data, 
    # append the API request body to the string from Step 3:
    headers = request_option.get('headers', {})
    content_type = headers.get('content_type') or headers.get('Content-Type', '')
    body = request_option.get('body', {})
    
    if content_type != "multipart/form-data" and body and len(body) > 0:
        # SDK 使用: const body = JSON.stringify(requestOption.body);
        body_str = json.dumps(body, separators=(',', ':'))
        sign_string += body_str
        logger.debug(f"📝 Step 4 - 附加請求體:")
        logger.debug(f"   Content-Type: {content_type}")
        logger.debug(f"   請求體: {body_str}")
    else:
        logger.debug(f"📝 Step 4 - 跳過請求體:")
        logger.debug(f"   Content-Type: {content_type}")
        logger.debug(f"   請求體為空或是 multipart/form-data")
    
    # Step 5: Wrap the string generated in Step 4 with the app_secret:
    wrapped_string = f"{app_secret}{sign_string}{app_secret}"
    
    logger.debug(f"📝 Step 5 - app_secret 包裝:")
    logger.debug(f"   包裝前字符串長度: {len(sign_string)}")
    logger.debug(f"   包裝後字符串長度: {len(wrapped_string)}")
    
    # Step 6: Encode your wrapped string using HMAC-SHA256:
    hmac_obj = hmac.new(
        app_secret.encode('utf-8'),
        wrapped_string.encode('utf-8'),
        hashlib.sha256
    )
    sign = hmac_obj.hexdigest()
    
    logger.info(f"✅ SDK 風格簽名生成成功: {sign[:16]}...")
    logger.debug(f"🔍 完整簽名: {sign}")
    
    return sign

"""
簽名生成模組
實現 TikTok Shop API 所需的 HMAC-SHA256 簽名算法
根據官方文檔和測試結果修正
"""

import hmac
import hashlib
import json
import logging
from typing import Dict, Any, Optional
from urllib.parse import urlparse

# 設置日誌
logger = logging.getLogger(__name__)

def generate_sign(request_option: Dict[str, Any], app_secret: str) -> str:
    """
    生成 HMAC-SHA256 簽名 - 修正版本
    
    Args:
        request_option: 請求選項字典，包含 qs (query params), uri (path), headers, body 等
        app_secret: App Secret 密鑰
        
    Returns:
        十六進制簽名字符串
    """
    logger.info("🔐 開始生成 HMAC-SHA256 簽名...")
    
    # Step 1: 提取並過濾查詢參數，只保留 app_key 和 timestamp
    params = request_option.get('qs', {})
    # 根據測試結果，只包含基本參數
    include_keys = ["app_key", "timestamp"]
    sorted_params = [
        {"key": key, "value": params[key]}
        for key in sorted(params.keys())
        if key in include_keys
    ]
    
    # Step 2: 以 {key}{value} 格式連接參數
    param_string = ''.join([f"{item['key']}{item['value']}" for item in sorted_params])
    
    # Step 3: 將 API 請求路徑附加到簽名字符串
    uri = request_option.get('uri', '')
    pathname = urlparse(uri).path if uri else ''
    sign_string = f"{pathname}{param_string}"
    
    # Step 4: 如果是 POST 請求且有請求體，則附加 JSON 序列化的請求體
    body = request_option.get('body', {})
    if body:
        body_str = json.dumps(body, separators=(',', ':'), sort_keys=True)
        sign_string += body_str
        logger.debug(f"📋 附加請求體: {body_str}")
    
    # Step 5: 用 app_secret 包裝簽名字符串
    wrapped_string = f"{app_secret}{sign_string}{app_secret}"
    
    # Step 6: 使用 HMAC-SHA256 編碼並生成十六進制簽名
    hmac_obj = hmac.new(
        app_secret.encode('utf-8'),
        wrapped_string.encode('utf-8'),
        hashlib.sha256
    )
    sign = hmac_obj.hexdigest()
    
    logger.info(f"✅ 簽名生成成功: {sign[:16]}...")
    logger.debug(f"🔍 簽名詳情: pathname={pathname}, param_string={param_string}, body_length={len(body_str) if body else 0}")
    
    return sign

def generate_simple_sign(api_path: str, app_key: str, timestamp: str, app_secret: str, 
                        request_body: Optional[Dict] = None) -> str:
    """
    簡化的簽名生成函數
    
    Args:
        api_path: API 路徑
        app_key: 應用金鑰
        timestamp: 時間戳
        app_secret: 應用密鑰
        request_body: 請求體（可選）
        
    Returns:
        十六進制簽名字符串
    """
    logger.info("🔐 使用簡化方法生成簽名...")
    
    # 構建參數字符串
    param_string = f"app_key{app_key}timestamp{timestamp}"
    
    # 構建簽名字符串
    sign_string = f"{api_path}{param_string}"
    
    # 如果有請求體，附加到末尾
    if request_body:
        body_str = json.dumps(request_body, separators=(',', ':'), sort_keys=True)
        sign_string += body_str
        logger.debug(f"📋 附加請求體: {body_str}")
    
    # 用 app_secret 包裝
    wrapped_string = f"{app_secret}{sign_string}{app_secret}"
    
    # HMAC-SHA256 編碼
    hmac_obj = hmac.new(
        app_secret.encode('utf-8'),
        wrapped_string.encode('utf-8'),
        hashlib.sha256
    )
    sign = hmac_obj.hexdigest()
    
    logger.info(f"✅ 簡化簽名生成成功: {sign[:16]}...")
    logger.debug(f"🔍 詳情: api_path={api_path}, param_string={param_string}")
    
    return sign

def validate_signature(request_option: Dict[str, Any], app_secret: str, expected_sign: str) -> bool:
    """
    驗證簽名是否正確
    
    Args:
        request_option: 請求選項字典
        app_secret: App Secret 密鑰
        expected_sign: 預期的簽名
        
    Returns:
        True 如果簽名正確
    """
    actual_sign = generate_sign(request_option, app_secret)
    is_valid = actual_sign == expected_sign
    
    if is_valid:
        logger.info("✅ 簽名驗證成功")
    else:
        logger.error(f"❌ 簽名驗證失敗: expected={expected_sign[:16]}..., actual={actual_sign[:16]}...")
    
    return is_valid 