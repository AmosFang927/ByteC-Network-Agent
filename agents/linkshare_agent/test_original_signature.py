#!/usr/bin/env python3
"""
测试原始签名方法的 Gen Tracking Link 功能
"""

import sys
import logging
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.linkshare_agent.link_generator import LinkGenerator
from agents.linkshare_agent.token_manager import TokenManager
from agents.linkshare_agent.signature import generate_sign_sdk_style
from agents.linkshare_agent import config

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_original_signature():
    """测试原始签名方法"""
    logger.info("🔐 开始测试原始签名方法...")
    
    try:
        # 1. 获取有效的 token
        token_manager = TokenManager()
        access_token = token_manager.get_valid_token()
        logger.info(f"✅ 获取到有效 token: {access_token[:30]}...")
        
        # 2. 准备请求数据
        request_data = {
            "material": {
                "id": "1731493745807886173",
                "type": "1"
            },
            "channel": config.DEFAULT_CHANNEL,
            "tags": config.DEFAULT_TAGS
        }
        
        # 3. 准备请求参数
        import time
        timestamp = str(int(time.time()))
        request_params = {
            "app_key": config.APP_KEY,
            "timestamp": timestamp
        }
        
        # 4. 准备请求选项
        full_url = f"{config.API_BASE_URL}/affiliate_creator/{config.APP_VERSION}/affiliate_sharing_links/generate_batch"
        request_option = {
            'uri': full_url,
            'qs': request_params,
            'body': request_data,
            'headers': {
                'Content-Type': 'application/json'
            }
        }
        
        # 5. 生成签名
        signature = generate_sign_sdk_style(request_option, config.APP_SECRET)
        logger.info(f"🔐 生成的签名: {signature}")
        
        # 6. 准备最终请求
        import requests
        import json
        
        url_params = {
            'app_key': config.APP_KEY,
            'timestamp': timestamp,
            'sign': signature
        }
        
        headers = {
            'Content-Type': 'application/json',
            'x-tts-access-token': access_token
        }
        
        # 7. 发送请求
        logger.info("🚀 发送 API 请求...")
        response = requests.post(
            url=full_url,
            params=url_params,
            json=request_data,
            headers=headers,
            timeout=30
        )
        
        logger.info(f"📡 API 响应状态码: {response.status_code}")
        logger.info(f"📥 响应内容: {response.text}")
        
        # 8. 解析响应
        response_data = response.json()
        
        if response_data.get('code') == 0:
            logger.info("✅ 原始签名方法测试成功!")
            
            data = response_data.get('data', {})
            links = data.get('affiliate_sharing_links', [])
            
            logger.info(f"📊 生成了 {len(links)} 个链接:")
            for i, link in enumerate(links, 1):
                logger.info(f"   {i}. 标签: {link.get('tag')}")
                logger.info(f"      链接: {link.get('affiliate_sharing_link')}")
                
            return True
        else:
            logger.error(f"❌ 原始签名方法测试失败: {response_data.get('message')}")
            return False
            
    except Exception as e:
        logger.error(f"❌ 测试过程中发生错误: {e}")
        return False

def main():
    """主函数"""
    logger.info("🚀 启动原始签名方法测试...")
    
    success = test_original_signature()
    
    if success:
        logger.info("🎉 测试完成!")
        return 0
    else:
        logger.error("❌ 测试失败!")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 