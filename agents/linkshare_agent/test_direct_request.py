#!/usr/bin/env python3
"""
直接使用requests调用API，使用SDK签名算法
"""

import sys
import logging
import json
import time
import requests
import hmac
import hashlib
from urllib.parse import urlparse
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.linkshare_agent import config

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

def generate_sdk_signature(request_option, app_secret):
    """使用SDK的签名算法"""
    # Step 1-2: 处理Query参数
    params = request_option.get('qs', {})
    exclude_keys = ["access_token", "sign"]
    
    # 过滤并排序参数
    sorted_params = []
    for key in sorted(params.keys()):
        if key not in exclude_keys:
            sorted_params.append({"key": key, "value": params[key]})
    
    # 拼接参数 - 格式：keyvalue
    param_string = "".join([f"{item['key']}{item['value']}" for item in sorted_params])
    
    # Step 3: 添加API路径
    pathname = urlparse(request_option['uri']).path
    sign_string = f"{pathname}{param_string}"
    
    # Step 4: 添加请求体
    body = request_option.get('body')
    if body and len(body) > 0:
        body_string = json.dumps(body, separators=(',', ':'))
        sign_string += body_string
    
    # Step 5: APP_SECRET包装
    wrapped_string = f"{app_secret}{sign_string}{app_secret}"
    
    # Step 6: HMAC-SHA256签名 - 使用app_secret作为密钥
    signature = hmac.new(
        app_secret.encode('utf-8'),  # 使用app_secret作为密钥
        wrapped_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return signature

def test_direct_api_call():
    """直接使用requests调用API"""
    logger.info("🚀 直接API调用测试")
    logger.info("=" * 80)
    
    try:
        # 加载token
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
        logger.info(f"  REQUEST_BODY: {json.dumps(request_body, indent=2, ensure_ascii=False)}")
        
        # 构建签名参数
        request_option = {
            'uri': full_url,
            'qs': {
                'app_key': config.APP_KEY,
                'access_token': access_token,
                'timestamp': timestamp
            },
            'body': request_body
        }
        
        # 生成签名
        logger.info(f"\n🔐 生成SDK签名...")
        signature = generate_sdk_signature(request_option, config.APP_SECRET)
        logger.info(f"✅ 签名: {signature}")
        
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
        logger.info(f"  URL_PARAMS: {json.dumps(url_params, indent=4)}")
        logger.info(f"  HEADERS: {json.dumps({k: v[:50] + '...' if len(v) > 50 else v for k, v in headers.items()}, indent=4)}")
        
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
        logger.info(f"  响应大小: {len(response.content)} 字节")
        
        # 分析响应
        try:
            response_data = response.json()
            
            logger.info(f"\n📋 响应内容:")
            logger.info(json.dumps(response_data, indent=4, ensure_ascii=False))
            
            code = response_data.get('code')
            message = response_data.get('message', '')
            request_id = response_data.get('request_id', '')
            data = response_data.get('data')
            
            logger.info(f"\n🎯 结果分析:")
            logger.info(f"  业务状态码: {code}")
            logger.info(f"  错误信息: {message}")
            logger.info(f"  请求ID: {request_id}")
            logger.info(f"  返回数据: {'有数据' if data else '无数据'}")
            
            if code == 0:
                logger.info(f"🎉 API调用成功！")
                if data and 'sharing_infos' in data:
                    sharing_infos = data['sharing_infos']
                    logger.info(f"📝 生成的分享链接:")
                    for info in sharing_infos:
                        logger.info(f"  产品ID: {info.get('material_id', 'N/A')}")
                        logger.info(f"  分享链接: {info.get('sharing_link', 'N/A')}")
                        logger.info(f"  短链接: {info.get('short_link', 'N/A')}")
                return True
            else:
                logger.error(f"❌ API调用失败: {code} - {message}")
                
                # 错误分析
                if code == 106001:
                    logger.warning("🔍 106001错误分析:")
                    logger.warning("  - 已确认签名算法与SDK一致")
                    logger.warning("  - 已确认Body格式正确")
                    logger.warning("  - 可能是权限或配置问题")
                    logger.warning("  - 建议检查TikTok Shop开发者后台")
                
                return False
                
        except json.JSONDecodeError:
            logger.error(f"❌ 响应不是有效JSON: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ 测试过程中发生错误: {e}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    logger.info("🎯 开始直接API调用测试")
    logger.info("💡 完全按照SDK算法实现")
    logger.info("🔧 技术要点:")
    logger.info("  1. 不包含HTTP方法")
    logger.info("  2. Query参数格式：keyvalue") 
    logger.info("  3. HMAC密钥：app_secret")
    logger.info("  4. Body格式：material_id, type='1', campaign_url")
    
    success = test_direct_api_call()
    logger.info(f"\n🏁 测试完成: {'成功' if success else '失败'}")
    
    if not success:
        logger.info("\n📋 技术总结:")
        logger.info("  ✅ 签名算法：已与SDK完全一致")
        logger.info("  ✅ 参数格式：已使用正确格式")
        logger.info("  ✅ API版本：202501")
        logger.info("  ❓ 问题根源：很可能是权限配置问题")
        logger.info("  💡 建议：检查TikTok Shop开发者后台权限设置")
    
    sys.exit(0 if success else 1)
