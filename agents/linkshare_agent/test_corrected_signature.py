#!/usr/bin/env python3
"""
修正签名算法的测试
基于SDK源码的正确实现：
1. 不包含HTTP方法
2. Query参数格式：keyvalue
3. HMAC密钥：app_secret
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

def manual_corrected_signature(request_option, app_secret):
    """基于SDK源码的正确签名算法实现"""
    logger.info("🔧 手动实现修正后的签名算法")
    logger.info("=" * 60)
    
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
    
    logger.info(f"Step 1-2: Query参数处理")
    logger.info(f"  原始参数: {params}")
    logger.info(f"  过滤后参数: {sorted_params}")
    logger.info(f"  拼接结果: {param_string}")
    
    # Step 3: 添加API路径
    pathname = urlparse(request_option['uri']).path
    sign_string = f"{pathname}{param_string}"
    
    logger.info(f"\nStep 3: 添加API路径")
    logger.info(f"  路径: {pathname}")
    logger.info(f"  拼接结果: {sign_string}")
    
    # Step 4: 添加请求体
    body = request_option.get('body')
    if (request_option.get('headers', {}).get('Content-Type') != 'multipart/form-data' 
        and body and len(body) > 0):
        body_string = json.dumps(body, separators=(',', ':'))
        sign_string += body_string
        
        logger.info(f"\nStep 4: 添加请求体")
        logger.info(f"  请求体: {body_string}")
        logger.info(f"  拼接结果: {sign_string}")
    
    # Step 5: APP_SECRET包装
    wrapped_string = f"{app_secret}{sign_string}{app_secret}"
    
    logger.info(f"\nStep 5: APP_SECRET包装")
    logger.info(f"  APP_SECRET: {app_secret[:10]}...{app_secret[-10:]}")
    logger.info(f"  包装结果: {app_secret[:10]}...{wrapped_string[50:-50]}...{app_secret[-10:]}")
    logger.info(f"  完整字符串: {wrapped_string}")
    
    # Step 6: HMAC-SHA256签名 - 使用app_secret作为密钥
    signature = hmac.new(
        app_secret.encode('utf-8'),  # 使用app_secret作为密钥
        wrapped_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    logger.info(f"\nStep 6: HMAC-SHA256签名")
    logger.info(f"  HMAC密钥: {app_secret[:10]}...{app_secret[-10:]}")
    logger.info(f"  待签名数据长度: {len(wrapped_string)} 字符")
    logger.info(f"  签名结果: {signature}")
    
    return signature

def test_corrected_signature_vs_sdk():
    """测试修正后的签名算法与SDK的对比"""
    logger.info("🚀 测试修正后的签名算法")
    logger.info("=" * 80)
    
    try:
        # 准备测试数据
        token_data = load_current_tokens()
        access_token = token_data.get('access_token', '')
        
        api_host = config.API_BASE_URL
        api_path = f"/affiliate_creator/{config.APP_VERSION}/affiliate_sharing_links/generate_batch"
        full_url = api_host + api_path
        
        request_body = {
            "channel": config.DEFAULT_CHANNEL,
            "material": {
                "id": config.DEFAULT_PRODUCT_ID,
                "type": "PRODUCT"
            },
            "tags": config.DEFAULT_TAGS
        }
        
        timestamp = str(int(time.time()))
        
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
        
        logger.info("📋 测试参数:")
        logger.info(f"  URL: {full_url}")
        logger.info(f"  APP_KEY: {config.APP_KEY}")
        logger.info(f"  TIMESTAMP: {timestamp}")
        logger.info(f"  BODY: {json.dumps(request_body, ensure_ascii=False)}")
        
        # 1. 手动修正后的签名
        manual_signature = manual_corrected_signature(request_option, config.APP_SECRET)
        
        # 2. SDK签名
        logger.info(f"\n🤖 SDK签名生成")
        logger.info("=" * 60)
        sdk_signature = generate_sign_sdk_style(request_option, config.APP_SECRET)
        logger.info(f"  SDK签名: {sdk_signature}")
        
        # 3. 对比结果
        logger.info(f"\n🔍 签名对比")
        logger.info("=" * 60)
        logger.info(f"  手动修正签名: {manual_signature}")
        logger.info(f"  SDK生成签名:  {sdk_signature}")
        logger.info(f"  签名是否一致: {'✅ 一致' if manual_signature == sdk_signature else '❌ 不一致'}")
        
        if manual_signature != sdk_signature:
            logger.warning("⚠️ 签名仍然不一致，需要进一步分析...")
            # 逐字符对比
            min_len = min(len(manual_signature), len(sdk_signature))
            for i in range(min_len):
                if manual_signature[i] != sdk_signature[i]:
                    logger.warning(f"  第{i+1}个字符不同: 手动='{manual_signature[i]}' vs SDK='{sdk_signature[i]}'")
                    break
        
        return {
            "manual_signature": manual_signature,
            "sdk_signature": sdk_signature,
            "signatures_match": manual_signature == sdk_signature,
            "request_option": request_option
        }
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")
        return None

def test_api_with_corrected_signature(signature_data):
    """使用修正后的签名测试API调用"""
    logger.info(f"\n📡 使用修正签名测试API调用")
    logger.info("=" * 80)
    
    try:
        token_data = load_current_tokens()
        access_token = token_data.get('access_token', '')
        
        api_host = config.API_BASE_URL
        api_path = f"/affiliate_creator/{config.APP_VERSION}/affiliate_sharing_links/generate_batch"
        full_url = api_host + api_path
        
        request_body = signature_data['request_option']['body']
        timestamp = signature_data['request_option']['qs']['timestamp']
        
        # 测试两种签名
        test_cases = [
            {
                "name": "手动修正签名",
                "signature": signature_data['manual_signature']
            }
        ]
        
        if signature_data['signatures_match']:
            logger.info("✅ 签名一致，只测试一种")
        else:
            test_cases.append({
                "name": "SDK生成签名",
                "signature": signature_data['sdk_signature']
            })
        
        results = []
        
        for test_case in test_cases:
            logger.info(f"\n🔬 测试: {test_case['name']}")
            logger.info("-" * 50)
            
            url_params = {
                'app_key': config.APP_KEY,
                'timestamp': timestamp,
                'sign': test_case['signature']
            }
            
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'sdk_node/1.0.0',
                'Accept': 'application/json',
                'x-tts-access-token': access_token
            }
            
            logger.info(f"  签名: {test_case['signature']}")
            
            response = requests.post(
                full_url,
                params=url_params,
                headers=headers,
                json=request_body,
                timeout=30
            )
            
            logger.info(f"  HTTP状态码: {response.status_code}")
            
            try:
                response_data = response.json()
                code = response_data.get('code')
                message = response_data.get('message', '')
                
                success = code == 0
                logger.info(f"  业务状态码: {code}")
                logger.info(f"  错误信息: {message}")
                logger.info(f"  结果: {'✅ 成功' if success else '❌ 失败'}")
                
                results.append({
                    "test_name": test_case['name'],
                    "success": success,
                    "code": code,
                    "message": message
                })
                
            except json.JSONDecodeError:
                logger.error(f"  ❌ 响应不是有效JSON: {response.text}")
                results.append({
                    "test_name": test_case['name'],
                    "success": False,
                    "code": None,
                    "message": f"Invalid JSON: {response.text}"
                })
        
        return results
        
    except Exception as e:
        logger.error(f"❌ API测试失败: {e}")
        return []

def main():
    """主函数"""
    logger.info("🎯 测试修正后的签名算法")
    logger.info("💡 修正点：")
    logger.info("  1. 不包含HTTP方法（POST）")
    logger.info("  2. Query参数格式：keyvalue 而非 key=value&")
    logger.info("  3. HMAC密钥：使用app_secret 而非空字符串")
    
    try:
        # 1. 签名对比测试
        signature_data = test_corrected_signature_vs_sdk()
        if not signature_data:
            logger.error("❌ 签名对比测试失败")
            return 1
        
        # 2. API调用测试
        api_results = test_api_with_corrected_signature(signature_data)
        
        # 3. 结果汇总
        logger.info(f"\n📊 最终结果汇总")
        logger.info("=" * 80)
        
        if signature_data['signatures_match']:
            logger.info("✅ 签名算法修正成功 - 与SDK完全一致")
        else:
            logger.info("❌ 签名算法仍有差异 - 需要进一步调试")
        
        if api_results:
            success_count = sum(1 for r in api_results if r['success'])
            logger.info(f"📡 API测试结果: {success_count}/{len(api_results)} 成功")
            
            for result in api_results:
                status = "✅" if result['success'] else "❌"
                logger.info(f"  {status} {result['test_name']}: {result.get('message', 'OK')}")
        
        logger.info(f"\n🏁 测试完成!")
        return 0
        
    except Exception as e:
        logger.error(f"❌ 测试过程中发生错误: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 