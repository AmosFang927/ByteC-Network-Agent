#!/usr/bin/env python3
"""
完全按照SDK逻辑的测试
"""

import sys
import logging
import time
import json
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.linkshare_agent.token_manager import TokenManager
from agents.linkshare_agent.sdk_signature import generate_sign_sdk_style
from agents.linkshare_agent import config
import requests

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_pure_sdk_logic():
    """完全按照SDK逻辑的测试"""
    logger.info("🔐 开始完全按照SDK逻辑的测试...")
    
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
        
        # 3. 准备请求参数 - 不包含access_token（因为SDK会排除它）
        timestamp = str(int(time.time()))
        request_params = {
            "app_key": config.APP_KEY,
            "timestamp": timestamp
            # 注意：不包含 access_token，因为SDK会自动排除
        }
        
        # 4. 构建完整 URL
        full_url = f"{config.API_BASE_URL}/affiliate_creator/{config.APP_VERSION}/affiliate_sharing_links/generate_batch"
        
        # 5. 准备请求选项（用于签名计算）
        request_option = {
            'uri': full_url,
            'qs': request_params,
            'body': request_data,
            'headers': {
                'Content-Type': 'application/json'
            }
        }
        
        # 6. 使用 SDK 生成签名
        signature = generate_sign_sdk_style(request_option, config.APP_SECRET)
        logger.info(f"🔐 SDK 生成的签名: {signature[:16]}...")
        
        # 7. 准备最终请求 - URL参数与签名计算参数一致
        url_params = {
            'app_key': config.APP_KEY,
            'timestamp': timestamp,
            'sign': signature
            # 注意：access_token 只在 header 中，不在 URL 参数中
        }
        
        headers = {
            'Content-Type': 'application/json',
            'x-tts-access-token': access_token  # access_token 只在这里
        }
        
        # 8. 发送请求
        logger.info("🚀 发送 API 请求...")
        logger.info(f"🌐 URL: {full_url}")
        logger.info(f"📋 URL参数: {url_params}")
        logger.info(f"📤 请求头: {headers}")
        logger.info(f"📦 请求体: {json.dumps(request_data, indent=2)}")
        
        response = requests.post(
            url=full_url,
            params=url_params,
            json=request_data,
            headers=headers,
            timeout=30
        )
        
        logger.info(f"📡 API 响应状态码: {response.status_code}")
        logger.info(f"📥 响应内容: {response.text}")
        
        # 9. 解析响应
        response_data = response.json()
        
        if response_data.get('code') == 0:
            logger.info("✅ 纯SDK逻辑测试成功!")
            
            data = response_data.get('data', {})
            links = data.get('affiliate_sharing_links', [])
            
            logger.info(f"📊 生成了 {len(links)} 个链接:")
            for i, link in enumerate(links, 1):
                logger.info(f"   {i}. 标签: {link.get('tag')}")
                logger.info(f"      链接: {link.get('affiliate_sharing_link')}")
                
            return True
        else:
            logger.error(f"❌ 纯SDK逻辑测试失败: {response_data.get('message')}")
            return False
            
    except Exception as e:
        logger.error(f"❌ 测试过程中发生错误: {e}")
        return False

def main():
    """主函数"""
    logger.info("🚀 启动纯SDK逻辑测试...")
    
    success = test_pure_sdk_logic()
    
    if success:
        logger.info("🎉 测试完成!")
        return 0
    else:
        logger.error("❌ 测试失败!")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 