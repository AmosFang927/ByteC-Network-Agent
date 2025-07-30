#!/usr/bin/env python3
"""
简化参数测试 - 测试最基本的参数组合
验证是否是参数权限问题
"""

import sys
import logging
import json
import time
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

def test_simplified_parameters():
    """测试简化的参数组合"""
    logger.info("🚀 开始简化参数测试...")
    
    try:
        token_data = load_current_tokens()
        access_token = token_data.get('access_token', '')
        logger.info(f"✅ 使用ACCESS TOKEN: {access_token[:50]}...")
        
        import requests
        
        api_host = config.API_BASE_URL
        api_path = f"/affiliate_creator/{config.APP_VERSION}/affiliate_sharing_links/generate_batch"
        full_url = api_host + api_path
        
        # 测试不同的参数组合
        test_cases = [
            {
                "name": "仅使用Material（最小参数）",
                "body": {
                    "material": {
                        "id": config.DEFAULT_PRODUCT_ID,
                        "type": "PRODUCT"
                    }
                }
            },
            {
                "name": "使用不同的产品ID",
                "body": {
                    "material": {
                        "id": "7386714373631476783",  # 之前使用的ID
                        "type": "PRODUCT"
                    }
                }
            },
            {
                "name": "添加简单Channel",
                "body": {
                    "channel": "test",
                    "material": {
                        "id": config.DEFAULT_PRODUCT_ID,
                        "type": "PRODUCT"
                    }
                }
            },
            {
                "name": "添加简单Tags",
                "body": {
                    "material": {
                        "id": config.DEFAULT_PRODUCT_ID,
                        "type": "PRODUCT"
                    },
                    "tags": ["test"]
                }
            },
            {
                "name": "完整配置参数",
                "body": {
                    "channel": config.DEFAULT_CHANNEL,
                    "material": {
                        "id": config.DEFAULT_PRODUCT_ID,
                        "type": "PRODUCT"
                    },
                    "tags": config.DEFAULT_TAGS
                }
            }
        ]
        
        results = []
        
        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"\n" + "=" * 60)
            logger.info(f"🧪 测试 {i}: {test_case['name']}")
            logger.info("=" * 60)
            
            request_body = test_case['body']
            
            # 构建签名参数
            timestamp = str(int(time.time()))
            request_params_for_signature = {
                "app_key": config.APP_KEY,
                "access_token": access_token,
                "timestamp": timestamp
            }
            
            request_option = {
                'uri': full_url,
                'qs': request_params_for_signature,
                'body': request_body,
                'headers': {
                    'Content-Type': 'application/json'
                }
            }
            
            logger.info(f"📋 请求体: {json.dumps(request_body, indent=2, ensure_ascii=False)}")
            
            try:
                # 生成签名
                signature = generate_sign_sdk_style(request_option, config.APP_SECRET)
                
                # 构建请求
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
                
                # 发送请求
                response = requests.post(
                    full_url,
                    params=url_params,
                    headers=headers,
                    json=request_body,
                    timeout=30
                )
                
                logger.info(f"📥 状态码: {response.status_code}")
                
                try:
                    response_data = response.json()
                    logger.info(f"📥 响应: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
                    
                    result = {
                        "test_name": test_case['name'],
                        "status_code": response.status_code,
                        "success": response.status_code == 200 and response_data.get('code') == 0,
                        "error_code": response_data.get('code'),
                        "error_message": response_data.get('message', ''),
                        "request_body": request_body
                    }
                    
                    if result["success"]:
                        logger.info("🎉 成功！")
                        data = response_data.get('data', {})
                        if data and data.get('affiliate_sharing_links'):
                            links = data.get('affiliate_sharing_links', [])
                            if links:
                                logger.info(f"🔗 生成的链接: {links[0].get('affiliate_sharing_link', 'N/A')}")
                    else:
                        logger.info(f"❌ 失败: {result['error_code']} - {result['error_message']}")
                    
                    results.append(result)
                    
                except json.JSONDecodeError:
                    logger.error(f"❌ 响应不是有效JSON: {response.text}")
                    results.append({
                        "test_name": test_case['name'],
                        "status_code": response.status_code,
                        "success": False,
                        "error_code": "JSON_DECODE_ERROR",
                        "error_message": response.text,
                        "request_body": request_body
                    })
                    
            except Exception as e:
                logger.error(f"❌ 测试失败: {e}")
                results.append({
                    "test_name": test_case['name'],
                    "status_code": -1,
                    "success": False,
                    "error_code": "EXCEPTION",
                    "error_message": str(e),
                    "request_body": request_body
                })
        
        # 总结结果
        logger.info(f"\n" + "=" * 80)
        logger.info("📊 测试结果总结")
        logger.info("=" * 80)
        
        successful_tests = [r for r in results if r["success"]]
        failed_tests = [r for r in results if not r["success"]]
        
        logger.info(f"✅ 成功测试: {len(successful_tests)} 个")
        logger.info(f"❌ 失败测试: {len(failed_tests)} 个")
        
        if successful_tests:
            logger.info(f"\n🎉 成功的参数组合:")
            for result in successful_tests:
                logger.info(f"  - {result['test_name']}")
                logger.info(f"    参数: {json.dumps(result['request_body'], ensure_ascii=False)}")
        
        if failed_tests:
            logger.info(f"\n❌ 失败的参数组合:")
            for result in failed_tests:
                logger.info(f"  - {result['test_name']}: {result['error_code']} - {result['error_message']}")
        
        # 分析模式
        error_codes = {}
        for result in failed_tests:
            code = result.get('error_code', 'UNKNOWN')
            if code not in error_codes:
                error_codes[code] = []
            error_codes[code].append(result['test_name'])
        
        if error_codes:
            logger.info(f"\n🔍 错误码模式分析:")
            for code, tests in error_codes.items():
                logger.info(f"  错误码 {code}: {len(tests)} 个测试")
                for test in tests:
                    logger.info(f"    - {test}")
        
        return len(successful_tests) > 0
        
    except Exception as e:
        logger.error(f"❌ 测试过程中发生错误: {e}")
        return False

def main():
    """主函数"""
    logger.info("🚀 启动简化参数测试...")
    logger.info("🎯 目标: 通过不同参数组合找出有效的配置")
    
    try:
        success = test_simplified_parameters()
        
        logger.info("\n🎉 简化参数测试完成!")
        return 0 if success else 1
        
    except Exception as e:
        logger.error(f"❌ 测试过程中发生错误: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 