"""
TikTok Shop 認證模組
處理 OAuth2 認證流程、Token 獲取等功能
"""

import requests
import logging
import time
from typing import Dict, Optional
from . import config

# 設置日誌
logger = logging.getLogger(__name__)

class TikTokAuth:
    """TikTok Shop 認證類"""
    
    def __init__(self):
        """初始化認證類"""
        self.app_key = config.APP_KEY
        self.app_secret = config.APP_SECRET
        self.auth_code = config.AUTH_CODE
        self.redirect_url = config.REDIRECT_URL
        self.session = requests.Session()
        
        # 設置默認超時和重試
        self.session.timeout = config.REQUEST_TIMEOUT
        
        logger.info(f"🔧 TikTokAuth 初始化完成 - App Key: {self.app_key[:8]}...")
        
    def get_access_token(self, auth_code: Optional[str] = None) -> Dict:
        """
        使用授權碼獲取 access_token 和 refresh_token
        
        Args:
            auth_code: 授權碼 (可選，默認使用配置中的 AUTH_CODE)
            
        Returns:
            包含 token 信息的字典
            
        Raises:
            Exception: 當 API 調用失敗時
            
        Example Response:
            {
                "access_token": "TTP_Fw8rBwAAAAAkW03FYd09DG-9INtpw361hWthei8S3fHX8iPJ5AUv99fLSCYD9-UucaqxTgNRzKZxi5-tfFMtdWqglEt5_iCk",
                "access_token_expire_in": 1660556783,
                "refresh_token": "TTP_NTUxZTNhYTQ2ZDk2YmRmZWNmYWY2YWY2YzkxNGYwNjQ3YjkzYTllYjA0YmNlMw",
                "refresh_token_expire_in": 1691487031,
                "open_id": "7010736057180325637",
                "seller_name": "Jjj test shop",
                "seller_base_region": "ID",
                "user_type": 0,
                "granted_scopes": ["seller.affiliate_collaboration.read", "seller.affiliate_collaboration.write"]
            }
        """
        logger.info("🔄 開始獲取 access_token...")
        
        # 使用提供的 auth_code 或配置中的默認值
        code = auth_code if auth_code else self.auth_code
        
        if not code:
            raise ValueError("❌ 授權碼 (auth_code) 不能為空")
        
        # 準備請求參數 - 根據 TikTok Shop API 文檔調整參數名稱
        params = {
            "app_key": self.app_key,
            "app_secret": self.app_secret,
            "grant_type": "authorized_code",  # 修正為 authorized_code (不是 authorization_code)
            "auth_code": code  # 改為 auth_code 而不是 code
        }
        
        logger.info(f"📤 發送 Token 請求 - App Key: {self.app_key[:8]}..., Code: {code[:20]}...")
        
        # 發送請求
        response_data = self._make_token_request(config.TOKEN_GET_URL, params)
        
        # 處理響應
        token_data = self._handle_api_response(response_data, "access_token")
        
        # 添加時間戳信息
        current_time = int(time.time())
        token_data['fetched_at'] = current_time
        token_data['expires_at'] = current_time + config.TOKEN_EXPIRE_TIME
        
        logger.info("✅ Access Token 獲取成功!")
        logger.info(f"🔑 Access Token: {token_data.get('access_token', '')[:20]}...")
        logger.info(f"🔄 Refresh Token: {token_data.get('refresh_token', '')[:20]}...")
        logger.info(f"👤 Open ID: {token_data.get('open_id', 'N/A')}")
        logger.info(f"🏪 Seller: {token_data.get('seller_name', 'N/A')} ({token_data.get('seller_base_region', 'N/A')})")
        
        return token_data
        
    def refresh_access_token(self, refresh_token: str) -> Dict:
        """
        刷新 access_token
        
        Args:
            refresh_token: 刷新令牌
            
        Returns:
            包含新 token 信息的字典
            
        Raises:
            Exception: 當 API 調用失敗時
        """
        logger.info("🔄 開始刷新 access_token...")
        
        if not refresh_token:
            raise ValueError("❌ 刷新令牌 (refresh_token) 不能為空")
        
        # 準備請求參數
        params = {
            "app_key": self.app_key,
            "app_secret": self.app_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }
        
        logger.info(f"📤 發送 Token 刷新請求 - Refresh Token: {refresh_token[:20]}...")
        
        # 發送請求
        response_data = self._make_token_request(config.TOKEN_REFRESH_URL, params)
        
        # 處理響應
        token_data = self._handle_api_response(response_data, "refresh_access_token")
        
        # 添加時間戳信息
        current_time = int(time.time())
        token_data['fetched_at'] = current_time
        token_data['expires_at'] = current_time + config.TOKEN_EXPIRE_TIME
        
        logger.info("✅ Access Token 刷新成功!")
        logger.info(f"🔑 New Access Token: {token_data.get('access_token', '')[:20]}...")
        
        return token_data
        
    def _make_token_request(self, url: str, params: Dict) -> Dict:
        """
        發送 Token 請求的通用方法
        
        Args:
            url: 請求 URL
            params: 請求參數
            
        Returns:
            API 響應數據
            
        Raises:
            Exception: 當請求失敗時
        """
        retry_count = 0
        last_exception = None
        
        while retry_count < config.MAX_RETRIES:
            try:
                logger.debug(f"🌐 嘗試 #{retry_count + 1} - 發送請求到: {url}")
                
                # 發送 GET 請求 (根據 TikTok Shop API 文檔)
                response = self.session.get(
                    url, 
                    params=params,
                    timeout=(config.CONNECT_TIMEOUT, config.REQUEST_TIMEOUT)
                )
                
                logger.debug(f"📈 響應狀態碼: {response.status_code}")
                logger.debug(f"📋 響應 Headers: {dict(response.headers)}")
                
                # 檢查 HTTP 狀態碼
                response.raise_for_status()
                
                # 解析 JSON 響應
                response_data = response.json()
                logger.debug(f"📊 響應數據: {response_data}")
                
                return response_data
                
            except requests.exceptions.Timeout as e:
                last_exception = e
                retry_count += 1
                if retry_count < config.MAX_RETRIES:
                    delay = config.RETRY_DELAY * (config.RETRY_BACKOFF ** (retry_count - 1))
                    logger.warning(f"⏰ 請求超時，{delay} 秒後重試 (第 {retry_count}/{config.MAX_RETRIES} 次)")
                    time.sleep(delay)
                else:
                    logger.error(f"❌ 請求最終超時失敗: {str(e)}")
                    
            except requests.exceptions.RequestException as e:
                last_exception = e
                retry_count += 1
                if retry_count < config.MAX_RETRIES:
                    delay = config.RETRY_DELAY * (config.RETRY_BACKOFF ** (retry_count - 1))
                    logger.warning(f"🌐 網路錯誤，{delay} 秒後重試 (第 {retry_count}/{config.MAX_RETRIES} 次): {str(e)}")
                    time.sleep(delay)
                else:
                    logger.error(f"❌ 網路請求最終失敗: {str(e)}")
                    
            except Exception as e:
                logger.error(f"❌ 未預期的錯誤: {str(e)}")
                raise
        
        # 如果所有重試都失敗
        raise Exception(f"❌ Token 請求失敗，已重試 {config.MAX_RETRIES} 次: {str(last_exception)}")
        
    def _handle_api_response(self, response_data: Dict, operation: str) -> Dict:
        """
        處理 API 響應
        
        Args:
            response_data: API 響應數據
            operation: 操作類型 (用於日誌)
            
        Returns:
            解析後的響應數據
            
        Raises:
            Exception: 當 API 返回錯誤時
        """
        # 檢查響應結構
        if not isinstance(response_data, dict):
            raise Exception(f"❌ 無效的響應格式: 預期字典，實際 {type(response_data)}")
        
        # 檢查錯誤碼
        code = response_data.get("code")
        message = response_data.get("message", "未知錯誤")
        request_id = response_data.get("request_id", "N/A")
        
        logger.info(f"📋 API 響應 - Code: {code}, Message: {message}, Request ID: {request_id}")
        
        if code != 0:
            # 獲取錯誤描述
            error_desc = config.API_ERROR_CODES.get(code, f"未知錯誤碼: {code}")
            error_msg = f"❌ {operation} 失敗 (錯誤碼: {code}): {error_desc} - {message}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        # 檢查數據部分
        data = response_data.get("data")
        if not data:
            raise Exception(f"❌ 響應中缺少數據部分: {response_data}")
        
        # 驗證必要字段
        if operation == "access_token":
            required_fields = ["access_token", "refresh_token", "open_id"]
        else:  # refresh_access_token
            required_fields = ["access_token"]
            
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            logger.warning(f"⚠️  響應中缺少字段: {missing_fields}")
        
        logger.info("✅ API 響應處理成功")
        return data
        
    def validate_token_format(self, token: str) -> bool:
        """
        驗證 Token 格式
        
        Args:
            token: 要驗證的 token
            
        Returns:
            True 如果格式正確
        """
        if not token or not isinstance(token, str):
            return False
            
        # TikTok Shop Token 通常以 "TTP_" 開頭
        if not token.startswith("TTP_"):
            logger.warning(f"⚠️  Token 格式可能不正確: {token[:10]}...")
            return False
            
        # 檢查長度 (TikTok Shop Token 通常較長)
        if len(token) < 50:
            logger.warning(f"⚠️  Token 長度可能不正確: {len(token)}")
            return False
            
        return True
        
    def close(self):
        """關閉 HTTP 會話"""
        if hasattr(self, 'session'):
            self.session.close()
            logger.debug("🔐 HTTP 會話已關閉")
            
    def __enter__(self):
        """上下文管理器進入"""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.close() 