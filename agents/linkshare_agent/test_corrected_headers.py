#!/usr/bin/env python3
"""
修正请求头格式，完全按照官方SDK标准
根据官方SDK源码分析：
1. Content-Type通过contentType参数传入
2. Accept自动设置为application/json  
3. x-tts-access-token通过xTtsAccessToken参数传入
4. 不应该有自定义的User-Agent
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

def test_with_correct_headers():
    """使用正确的请求头测试"""
    logger.info("🔧 使用正确的请求头格式测试Gen Tracking Link")
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
        signature = generate_sign_sdk_style(request_option, config.APP_SECRET)
        
        # URL参数
        url_params = {
            'app_key': config.APP_KEY,
            'timestamp': timestamp,
            'sign': signature
        }
        
        # 根据SDK源码的正确请求头格式
        headers = {
            'Content-Type': 'application/json',  # 对应contentType参数
            'Accept': 'application/json',        # SDK自动设置
            'x-tts-access-token': access_token   # 对应xTtsAccessToken参数
            # 注意：不设置自定义User-Agent，让系统使用默认值
        }
        
        logger.info("📋 修正后的请求信息:")
        logger.info(f"  URL: {full_url}")
        logger.info(f"  URL_PARAMS: {json.dumps(url_params, indent=4)}")
        logger.info(f"  HEADERS: {json.dumps({k: v[:50] + '...' if len(v) > 50 else v for k, v in headers.items()}, indent=4)}")
        logger.info(f"  BODY: {json.dumps(request_body, indent=2, ensure_ascii=False)}")
        
        logger.info(f"\n🔍 与之前的差异:")
        logger.info(f"  ❌ 移除了: User-Agent: 'sdk_node/1.0.0'")
        logger.info(f"  ✅ 保留了: Content-Type: 'application/json'")
        logger.info(f"  ✅ 保留了: Accept: 'application/json'")
        logger.info(f"  ✅ 保留了: x-tts-access-token")
        
        # 发送请求
        logger.info(f"\n📡 发送修正后的请求...")
        
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
                return False
                
        except json.JSONDecodeError:
            logger.error(f"❌ 响应不是有效JSON: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ 测试过程中发生错误: {e}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")
        return False

def test_multiple_header_formats():
    """测试多种请求头格式"""
    logger.info(f"\n🧪 测试多种请求头格式")
    logger.info("=" * 80)
    
    header_formats = [
        {
            "name": "SDK标准格式（无User-Agent）",
            "headers": {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        },
        {
            "name": "最小格式（仅Content-Type）",
            "headers": {
                'Content-Type': 'application/json'
            }
        },
        {
            "name": "官方文档格式",
            "headers": {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'User-Agent': 'TikTok-Shop-SDK/1.0.0'
            }
        },
        {
            "name": "原有格式（含sdk_node）",
            "headers": {
                'Content-Type': 'application/json',
                'User-Agent': 'sdk_node/1.0.0',
                'Accept': 'application/json'
            }
        }
    ]
    
    results = []
    
    for i, format_test in enumerate(header_formats, 1):
        logger.info(f"\n🔬 测试{i}: {format_test['name']}")
        logger.info("-" * 50)
        
        try:
            token_data = load_current_tokens()
            access_token = token_data.get('access_token', '')
            
            api_host = config.API_BASE_URL
            api_path = f"/affiliate_creator/{config.APP_VERSION}/affiliate_sharing_links/generate_batch"
            full_url = api_host + api_path
            
            request_body = {
                "material": {
                    "material_id": config.DEFAULT_PRODUCT_ID,
                    "type": "1"
                }
            }
            
            timestamp = str(int(time.time()))
            
            request_option = {
                'uri': full_url,
                'qs': {
                    'app_key': config.APP_KEY,
                    'access_token': access_token,
                    'timestamp': timestamp
                },
                'body': request_body
            }
            
            signature = generate_sign_sdk_style(request_option, config.APP_SECRET)
            
            url_params = {
                'app_key': config.APP_KEY,
                'timestamp': timestamp,
                'sign': signature
            }
            
            # 合并测试请求头和必需的access_token
            test_headers = format_test['headers'].copy()
            test_headers['x-tts-access-token'] = access_token
            
            logger.info(f"  请求头: {json.dumps(test_headers, indent=4)}")
            
            response = requests.post(
                full_url,
                params=url_params,
                headers=test_headers,
                json=request_body,
                timeout=30
            )
            
            response_data = response.json()
            code = response_data.get('code')
            message = response_data.get('message', '')
            
            success = code == 0
            logger.info(f"  HTTP状态: {response.status_code}")
            logger.info(f"  业务状态: {code}")
            logger.info(f"  结果: {'✅ 成功' if success else f'❌ 失败 - {message}'}")
            
            results.append({
                "name": format_test['name'],
                "success": success,
                "code": code,
                "message": message,
                "headers": format_test['headers']
            })
            
        except Exception as e:
            logger.error(f"  ❌ 测试失败: {e}")
            results.append({
                "name": format_test['name'],
                "success": False,
                "code": None,
                "message": str(e),
                "headers": format_test['headers']
            })
    
    # 汇总结果
    logger.info(f"\n📊 测试结果汇总:")
    success_count = sum(1 for r in results if r['success'])
    logger.info(f"  总测试数: {len(results)}")
    logger.info(f"  成功测试: {success_count}")
    logger.info(f"  成功率: {(success_count / len(results) * 100):.1f}%")
    
    logger.info(f"\n详细结果:")
    for result in results:
        status = "✅" if result['success'] else "❌"
        logger.info(f"  {status} {result['name']}: {result.get('message', 'OK')}")
    
    return results

if __name__ == "__main__":
    logger.info("🎯 开始测试修正后的请求头格式")
    logger.info("💡 关键修正:")
    logger.info("  - 移除自定义User-Agent")
    logger.info("  - 按照SDK标准设置请求头")
    logger.info("  - 完全符合官方文档要求")
    
    # 1. 标准测试
    success = test_with_correct_headers()
    
    # 2. 多格式测试
    test_multiple_header_formats()
    
    logger.info(f"\n🏁 测试完成: {'成功' if success else '失败'}")
    
    if not success:
        logger.info(f"\n📋 如果所有请求头格式都失败，问题确实在权限配置层面")
    
    sys.exit(0 if success else 1)
