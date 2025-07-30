#!/usr/bin/env python3
"""
基于SDK的Tracking Link生成器
所有输入参数参考config.py配置
"""

import json
import time
import logging
import requests
from typing import Dict, List, Optional, Any
from . import config
from .token_manager import TokenManager
from .sdk_signature import generate_sign_sdk_style

logger = logging.getLogger(__name__)

class SDKTrackingLinkGenerator:
    """基于SDK的Tracking Link生成器"""
    
    def __init__(self):
        """初始化生成器"""
        self.token_manager = TokenManager()
        logger.info(f"🔧 SDKTrackingLinkGenerator 初始化完成")
        
    def generate_tracking_links(self, 
                               product_id: Optional[str] = None,
                               channel: Optional[str] = None,
                               tags: Optional[List[str]] = None,
                               campaign_url: Optional[str] = None) -> Dict[str, Any]:
        """
        生成tracking links - SDK风格调用
        
        Args:
            product_id: 产品ID (可选，默认使用config.DEFAULT_PRODUCT_ID)
            channel: 频道 (可选，默认使用config.DEFAULT_CHANNEL)
            tags: 标签列表 (可选，默认使用config.DEFAULT_TAGS)
            campaign_url: 活动URL (可选，自动生成)
            
        Returns:
            包含生成结果的字典
            
        Example:
            generator = SDKTrackingLinkGenerator()
            result = generator.generate_tracking_links()
        """
        logger.info("🚀 开始SDK风格生成tracking links...")
        
        try:
            # 1. 从config.py获取默认参数
            product_id = product_id or config.DEFAULT_PRODUCT_ID
            channel = channel or config.DEFAULT_CHANNEL
            tags = tags or config.DEFAULT_TAGS.copy()
            campaign_url = campaign_url or self._generate_campaign_url(product_id)
            
            logger.info(f"📋 使用参数:")
            logger.info(f"   产品ID: {product_id}")
            logger.info(f"   频道: {channel}")
            logger.info(f"   标签: {tags}")
            logger.info(f"   活动URL: {campaign_url}")
            
            # 2. 获取access token
            access_token = self.token_manager.get_valid_token()
            logger.info(f"🔑 获取到access token: {access_token[:30]}...")
            
            # 3. 构建SDK风格的请求
            sdk_result = self._sdk_call_generate_links(
                product_id=product_id,
                channel=channel,
                tags=tags,
                campaign_url=campaign_url,
                access_token=access_token
            )
            
            return sdk_result
            
        except Exception as e:
            logger.error(f"❌ SDK调用失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": {
                    "affiliate_sharing_links": [],
                    "errors": [{"code": -1, "msg": str(e)}]
                }
            }
    
    def _generate_campaign_url(self, product_id: str) -> str:
        """从config.py生成campaign URL"""
        return config.CAMPAIGN_URL_TEMPLATE.format(product_id=product_id)
    
    def _sdk_call_generate_links(self, 
                                product_id: str,
                                channel: str,
                                tags: List[str],
                                campaign_url: str,
                                access_token: str) -> Dict[str, Any]:
        """
        SDK风格调用生成links
        """
        logger.info("🔧 构建SDK风格请求...")
        
        # 使用config.py中的参数构建请求体
        request_body = {
            "material": {
                "id": product_id,
                "type": config.MATERIAL_TYPE_PRODUCT,
                "campaignUrl": campaign_url
            },
            "channel": channel,
            "tags": tags
        }
        
        # 构建查询参数 (不包含access_token)
        timestamp = str(int(time.time()))
        query_params = {
            "app_key": config.APP_KEY,
            "timestamp": timestamp
        }
        
        # 准备SDK签名请求
        api_url = f"{config.API_BASE_URL}/affiliate_creator/{config.APP_VERSION}/affiliate_sharing_links/generate_batch"
        
        sdk_request_option = {
            'uri': api_url,
            'qs': query_params,
            'body': request_body,
            'headers': config.BASE_HEADERS
        }
        
        logger.info("🔐 调用SDK生成签名...")
        signature = generate_sign_sdk_style(sdk_request_option, config.APP_SECRET)
        logger.info(f"✅ SDK签名生成成功: {signature[:16]}...")
        
        # 构建最终请求参数
        final_query_params = {
            **query_params,
            "sign": signature
        }
        
        # 使用config.py中的请求头配置
        headers = config.get_api_headers(access_token)
        
        logger.info("📡 发送SDK风格HTTP请求...")
        logger.debug(f"URL: {api_url}")
        logger.debug(f"Query Params: {final_query_params}")
        logger.debug(f"Headers: {headers}")
        logger.debug(f"Body: {json.dumps(request_body, indent=2)}")
        
        # 发送请求
        response = requests.post(
            url=api_url,
            params=final_query_params,
            json=request_body,
            headers=headers,
            timeout=(config.CONNECT_TIMEOUT, config.REQUEST_TIMEOUT)
        )
        
        logger.info(f"📊 HTTP响应状态: {response.status_code}")
        
        # 解析响应
        if response.status_code == 200:
            response_data = response.json()
            code = response_data.get('code', -1)
            
            if code == 0:
                logger.info("🎉 SDK调用成功!")
                return {
                    "success": True,
                    "data": response_data.get('data', {}),
                    "message": response_data.get('message', 'Success'),
                    "request_id": response_data.get('request_id', '')
                }
            else:
                error_msg = config.API_ERROR_CODES.get(code, response_data.get('message', '未知错误'))
                logger.error(f"❌ API业务错误: {code} - {error_msg}")
                return {
                    "success": False,
                    "error": f"API错误 {code}: {error_msg}",
                    "data": response_data.get('data', {}),
                    "request_id": response_data.get('request_id', '')
                }
        else:
            try:
                error_data = response.json()
                error_code = error_data.get('code', response.status_code)
                error_msg = config.API_ERROR_CODES.get(error_code, error_data.get('message', '请求失败'))
                logger.error(f"❌ HTTP错误: {response.status_code} - {error_msg}")
                return {
                    "success": False,
                    "error": f"HTTP错误 {response.status_code}: {error_msg}",
                    "data": error_data.get('data', {}),
                    "request_id": error_data.get('request_id', '')
                }
            except:
                logger.error(f"❌ HTTP错误: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"HTTP错误 {response.status_code}: {response.text}",
                    "data": {},
                    "request_id": ''
                }

def generate_tracking_links_sdk(product_id: Optional[str] = None,
                               channel: Optional[str] = None,
                               tags: Optional[List[str]] = None,
                               campaign_url: Optional[str] = None) -> Dict[str, Any]:
    """
    SDK风格的便捷函数 - 直接调用生成tracking links
    所有参数从config.py获取默认值
    
    Args:
        product_id: 产品ID (可选，默认使用config.DEFAULT_PRODUCT_ID)
        channel: 频道 (可选，默认使用config.DEFAULT_CHANNEL)
        tags: 标签列表 (可选，默认使用config.DEFAULT_TAGS)
        campaign_url: 活动URL (可选，自动生成)
        
    Returns:
        包含生成结果的字典
        
    Example:
        # 使用默认配置
        result = generate_tracking_links_sdk()
        
        # 自定义部分参数
        result = generate_tracking_links_sdk(
            product_id="1234567890",
            channel="MY_CHANNEL"
        )
    """
    generator = SDKTrackingLinkGenerator()
    return generator.generate_tracking_links(
        product_id=product_id,
        channel=channel,
        tags=tags,
        campaign_url=campaign_url
    )

def print_tracking_links_result(result: Dict[str, Any]) -> None:
    """
    打印tracking links生成结果
    
    Args:
        result: generate_tracking_links_sdk的返回结果
    """
    print("\n📊 Tracking Links生成结果:")
    print("=" * 60)
    
    if result.get("success"):
        print("✅ 状态: 成功")
        print(f"💬 消息: {result.get('message', 'N/A')}")
        print(f"📋 请求ID: {result.get('request_id', 'N/A')}")
        
        data = result.get("data", {})
        affiliate_links = data.get("affiliate_sharing_links", [])
        
        if affiliate_links:
            print(f"\n🔗 成功生成 {len(affiliate_links)} 个联盟链接:")
            for i, link in enumerate(affiliate_links, 1):
                print(f"   {i}. 标签: {link.get('tag', 'N/A')}")
                print(f"      链接: {link.get('affiliate_sharing_link', 'N/A')}")
        
        errors = data.get("errors", [])
        if errors:
            print(f"\n⚠️ 发现 {len(errors)} 个错误:")
            for error in errors:
                print(f"   错误码: {error.get('code', 'N/A')}")
                print(f"   错误信息: {error.get('msg', 'N/A')}")
                if 'detail' in error:
                    detail = error['detail']
                    print(f"   详细信息: 标签={detail.get('tag', 'N/A')}, 原因={detail.get('fail_reason', 'N/A')}")
    else:
        print("❌ 状态: 失败")
        print(f"💬 错误: {result.get('error', 'N/A')}")
        print(f"📋 请求ID: {result.get('request_id', 'N/A')}")
    
    print("=" * 60)

if __name__ == "__main__":
    # SDK风格调用示例
    print("🚀 SDK风格Tracking Links生成测试")
    
    # 使用config.py中的默认配置
    result = generate_tracking_links_sdk()
    
    # 打印结果
    print_tracking_links_result(result) 