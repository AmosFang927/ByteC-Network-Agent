"""
聯盟連結生成模組
處理 TikTok Shop 聯盟分享連結的生成
"""

import time
import json
import requests
import logging
from typing import Dict, List, Optional
from . import config
from .token_manager import TokenManager
from .signature import generate_sign_sdk_style

# 設置日誌
logger = logging.getLogger(__name__)

class LinkGenerator:
    """聯盟連結生成類"""
    
    def __init__(self):
        """初始化連結生成器"""
        self.token_manager = TokenManager()
        self.app_key = config.APP_KEY
        self.app_secret = config.APP_SECRET
        self.app_version = config.APP_VERSION
        self.api_base_url = config.API_BASE_URL
        logger.info(f"🔧 LinkGenerator 初始化完成 - App Key: {self.app_key[:10]}...")
        
    def generate_affiliate_link(self, 
                              product_id: Optional[str] = None,
                              channel: Optional[str] = None,
                              tags: Optional[List[str]] = None,
                              campaign_url: Optional[str] = None) -> Dict:
        """
        生成聯盟分享連結
        
        Args:
            product_id: 產品 ID (可選，默認使用配置中的 DEFAULT_PRODUCT_ID)
            channel: 頻道名稱 (可選，默認使用配置中的 DEFAULT_CHANNEL)
            tags: 標籤列表 (可選，默認使用配置中的 DEFAULT_TAGS)
            campaign_url: 活動 URL (可選，會自動生成)
            
        Returns:
            包含聯盟連結和錯誤信息的字典
            
        Example:
            response = {
                "code": 0,
                "data": {
                    "affiliate_sharing_links": [
                        {
                            "tag": "OEM3_OPPO_PUSH",
                            "affiliate_sharing_link": "www.tiktok.com/asdsfe1c"
                        }
                    ],
                    "errors": []
                },
                "message": "Success",
                "request_id": "202203070749000101890810281E8C70B7"
            }
        """
        # 使用默認值
        product_id = product_id or config.DEFAULT_PRODUCT_ID
        channel = channel or config.DEFAULT_CHANNEL
        tags = tags or config.DEFAULT_TAGS.copy()
        campaign_url = campaign_url or self.generate_campaign_url(product_id)
        
        logger.info(f"🔗 開始生成產品 {product_id} 的聯盟連結...")
        logger.info(f"📊 頻道: {channel}")
        logger.info(f"🏷️  標籤: {tags}")
        logger.info(f"🌐 活動URL: {campaign_url}")
        
        try:
            # 1. 獲取有效的 access token
            logger.info("🔑 獲取有效的 access token...")
            access_token = self.token_manager.get_valid_token()
            logger.info(f"✅ Access token 獲取成功: {access_token[:30]}...")
            
            # 2. 準備請求數據
            logger.info("📝 準備請求數據...")
            request_data = self._prepare_request_data(product_id, channel, tags, campaign_url)
            
            # 3. 構建請求參數
            logger.info("⚙️  構建請求參數...")
            request_params = self._build_request_params(access_token)
            
            # 4. 發送 API 請求
            logger.info("🚀 發送 API 請求...")
            response = self._make_api_request(request_params, request_data)
            
            # 5. 處理響應
            response_data = self._handle_response(response)
            
            # 6. 打印響應摘要
            self._print_response_summary(response_data)
            
            return response_data
            
        except Exception as e:
            logger.error(f"❌ 聯盟連結生成失敗: {e}")
            return {
                "code": -1,
                "message": f"生成失敗: {str(e)}",
                "data": {
                    "affiliate_sharing_links": [],
                    "errors": [{"code": -1, "msg": str(e)}]
                }
            }
        
    def _prepare_request_data(self, 
                            product_id: str,
                            channel: str,
                            tags: List[str],
                            campaign_url: str) -> Dict:
        """
        準備請求數據 - 使用 SDK 風格的格式
        
        Args:
            product_id: 產品 ID
            channel: 頻道名稱
            tags: 標籤列表
            campaign_url: 活動 URL
            
        Returns:
            請求體字典
        """
        # 根據 SDK 的請求體格式
        request_data = {
            "material": {
                "id": product_id,  # SDK 使用 "id" 而不是 "material_id"
                "type": "1",  # 正確！應該使用 "1" 而不是 "PRODUCT"
                "campaignUrl": campaign_url  # SDK 使用駝峰命名
            },
            "channel": channel,
            "tags": tags
        }
        
        logger.debug(f"📋 請求數據: {json.dumps(request_data, indent=2, ensure_ascii=False)}")
        return request_data
        
    def _build_request_params(self, access_token: str) -> Dict:
        """
        構建請求參數
        
        Args:
            access_token: 訪問令牌
            
        Returns:
            請求參數字典
        """
        timestamp = str(int(time.time()))
        
        request_params = {
            "app_key": self.app_key,
            "access_token": access_token,  # 簽名計算需要包含 access_token
            "timestamp": timestamp
            # 注意：SDK 不會在查詢參數中包含 version
        }
        
        logger.debug(f"⚙️  請求參數: {request_params}")
        return request_params
        
    def _make_api_request(self, request_params: Dict, request_data: Dict) -> requests.Response:
        """
        發送 API 請求
        """
        # 構建完整 URL
        full_url = f"{config.API_BASE_URL}/affiliate_creator/{config.APP_VERSION}/affiliate_sharing_links/generate_batch"
        
        # 準備請求選項（用於簽名計算）
        request_option = {
            'uri': full_url,
            'qs': request_params,
            'body': request_data,
            'headers': {
                'Content-Type': 'application/json'
            }
        }
        
        # 使用 SDK 風格的簽名算法
        signature = generate_sign_sdk_style(request_option, config.APP_SECRET)
        logger.info(f"🔐 使用 SDK 風格簽名: {signature[:16]}...")
        
        # 準備 URL 參數（移除 access_token，它應該在 header 中）
        url_params = {
            'app_key': config.APP_KEY,
            'timestamp': request_params['timestamp'],
            'sign': signature
            # 注意：SDK 不包含 version 在查詢參數中
        }
        
        # 準備請求頭（添加 SDK 風格的請求頭）
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'sdk_node/1.0.0',  # 添加 SDK 風格的 User-Agent
            'Accept': 'application/json',     # 添加 Accept 請求頭
            'x-tts-access-token': request_params['access_token']
        }
        
        logger.debug(f"🌐 API URL: {full_url}")
        logger.debug(f"📋 URL 參數: {url_params}")
        logger.debug(f"📤 請求頭: {headers}")
        logger.debug(f"📦 請求體: {json.dumps(request_data, indent=2, ensure_ascii=False)}")
        
        try:
            response = requests.post(
                url=full_url,
                params=url_params,
                json=request_data,
                headers=headers,
                                 timeout=(config.CONNECT_TIMEOUT, config.REQUEST_TIMEOUT)
            )
            
            logger.info(f"📡 API 響應狀態碼: {response.status_code}")
            logger.debug(f"📥 響應內容: {response.text}")
            
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ API 請求異常: {e}")
            raise
        
    def _handle_response(self, response: requests.Response) -> Dict:
        """
        處理 API 響應
        
        Args:
            response: HTTP 響應對象
            
        Returns:
            解析後的響應數據
            
        Raises:
            Exception: 當 API 返回錯誤時
        """
        try:
            response_data = response.json()
            logger.debug(f"📊 完整響應數據: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
            
            # 檢查響應碼
            code = response_data.get('code')
            message = response_data.get('message', 'Unknown')
            request_id = response_data.get('request_id', 'N/A')
            
            logger.info(f"📋 API 響應 - Code: {code}, Message: {message}, Request ID: {request_id}")
            
            if code == 0:
                logger.info("✅ API 響應處理成功")
                return response_data
            else:
                # 檢查是否有已知的錯誤碼對應
                error_msg = config.API_ERROR_CODES.get(code, message)
                raise Exception(f"API 錯誤 {code}: {error_msg}")
                
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON 解析錯誤: {e}")
            logger.error(f"📝 響應內容: {response.text}")
            raise Exception(f"響應解析失敗: {e}")
        
    def _print_response_summary(self, response_data: Dict) -> None:
        """
        打印響應摘要
        
        Args:
            response_data: API 響應數據
        """
        logger.info("📊 聯盟連結生成結果摘要:")
        
        # 打印成功的連結
        if 'data' in response_data and 'affiliate_sharing_links' in response_data['data']:
            links = response_data['data']['affiliate_sharing_links']
            logger.info(f"✅ 成功生成 {len(links)} 個聯盟連結:")
            for link in links:
                logger.info(f"   🏷️  標籤: {link.get('tag')}")
                logger.info(f"   🔗 連結: {link.get('affiliate_sharing_link')}")
        
        # 打印錯誤信息
        if 'data' in response_data and 'errors' in response_data['data']:
            errors = response_data['data']['errors']
            if errors:
                logger.warning(f"⚠️  發現 {len(errors)} 個錯誤:")
                for error in errors:
                    logger.warning(f"   ❌ 錯誤碼: {error.get('code')}")
                    logger.warning(f"   📝 錯誤信息: {error.get('msg')}")
                    if 'detail' in error:
                        detail = error['detail']
                        logger.warning(f"   🏷️  問題標籤: {detail.get('tag')}")
                        logger.warning(f"   🔍 失敗原因: {detail.get('fail_reason')}")
        
        logger.info(f"📋 請求 ID: {response_data.get('request_id')}")
        logger.info(f"💬 響應消息: {response_data.get('message')}")
        
    def get_default_channel(self) -> str:
        """獲取默認頻道"""
        return config.DEFAULT_CHANNEL
        
    def get_default_tags(self) -> List[str]:
        """獲取默認標籤"""
        return config.DEFAULT_TAGS.copy()
        
    def generate_campaign_url(self, product_id: str) -> str:
        """
        生成活動 URL
        
        Args:
            product_id: 產品 ID
            
        Returns:
            活動 URL
        """
        return config.CAMPAIGN_URL_TEMPLATE.format(product_id=product_id) 