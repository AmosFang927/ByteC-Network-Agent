#!/usr/bin/env python3
"""
使用正确Body格式的Gen Tracking Link测试
修正请求体格式：
- material.id -> material.material_id
- material.type: "PRODUCT" -> material.type: "1"
- 添加 material.campaign_url
- 更新 channel 和 tags
"""

import sys
import logging
import json
import time
import requests
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.linkshare_agent import config
from agents.linkshare_agent.sdk_signature import generate_sign_sdk_style

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_current_tokens():
    """加载当前存储的token"""
    token_file = Path('agents/linkshare_agent/tokens.conf')
    if not token_file.exists():
        raise Exception("Token文件不存在")
    
    with open(token_file, 'r') as f:
        return json.load(f)

def test_with_correct_body_format():
    """使用正确的Body格式测试Gen Tracking Link"""
    logger.info("🚀 使用正确Body格式测试Gen Tracking Link")
    logger.info("=" * 80)
    
    try:
        # 加载基础数据
        token_data = load_current_tokens()
        access_token = token_data.get('access_token', '')
        
        api_host = config.API_BASE_URL
        api_path = f"/affiliate_creator/{config.APP_VERSION}/affiliate_sharing_links/generate_batch"
        full_url = api_host + api_path
        
        # 使用正确的请求体格式
        request_body = {
            "material": {
                "material_id": config.DEFAULT_PRODUCT_ID,
                "type": "1",
                "campaign_url": f"https://shop.tiktok.com/view/product/{config.DEFAULT_PRODUCT_ID}"
            },
            "channel": "OEM1_XIAOMI",
            "tags": [
                "OEM1_XIOMI_PUSH_AUG",
                "OEM2_VIVO_PUSH_AUG"
            ]
        }
        
        timestamp = str(int(time.time()))
        
        logger.info("📋 请求信息:")
        logger.info(f"  URL: {full_url}")
        logger.info(f"  APP_KEY: {config.APP_KEY}")
        logger.info(f"  TIMESTAMP: {timestamp}")
        logger.info(f"  REQUEST_BODY: {json.dumps(request_body, indent=4, ensure_ascii=False)}")
        
        # 构建SDK期望的request_option格式
        request_option = {
            'uri': full_url,
            'qs': {
                'app_key': config.APP_KEY,
                'access_token': access_token,
                'timestamp': timestamp
            },
            'body': request_body,
            'headers': {
                'Content-Type': 'application/json'
            }
        }
        
        # 使用SDK生成签名
        logger.info(f"\n🔐 使用SDK生成签名...")
        signature = generate_sign_sdk_style(request_option, config.APP_SECRET)
        logger.info(f"✅ SDK签名: {signature}")
        
        # 构建HTTP请求
        url_params = {
            'app_key': config.APP_KEY,
            'timestamp': timestamp,
            'sign': signature
        }
        
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'sdk_node/1.0.0',
            'Accept': 'application/json',
            'x-tts-access-token': access_token
        }
        
        logger.info(f"\n🌐 HTTP请求:")
        logger.info(f"  METHOD: POST")
        logger.info(f"  URL: {full_url}")
        logger.info(f"  URL_PARAMS: {json.dumps(url_params, indent=4)}")
        
        # 发送请求
        logger.info(f"\n📡 发送HTTP请求...")
        
        response = requests.post(
            full_url,
            params=url_params,
            headers=headers,
            json=request_body,
            timeout=30
        )
        
        logger.info(f"📊 响应信息:")
        logger.info(f"  HTTP状态码: {response.status_code}")
        
        # 分析响应
        try:
            response_data = response.json()
            
            logger.info(f"\n📋 响应内容:")
            logger.info(json.dumps(response_data, indent=4, ensure_ascii=False))
            
            code = response_data.get('code')
            message = response_data.get('message', '')
            
            if code == 0:
                logger.info(f"🎉 API调用成功！")
                return True
            else:
                logger.error(f"❌ API调用失败: {code} - {message}")
                return False
                
        except json.JSONDecodeError:
            logger.error(f"❌ 响应不是有效JSON: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ 测试过程中发生错误: {e}")
        return False

if __name__ == "__main__":
    test_with_correct_body_format()
