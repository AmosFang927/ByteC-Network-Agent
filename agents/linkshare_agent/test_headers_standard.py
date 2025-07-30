#!/usr/bin/env python3
"""
测试不同请求头组合，基于官方SDK标准
"""

import sys
import logging
import json
import requests
import time
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.linkshare_agent import config
from agents.linkshare_agent.token_manager import TokenManager
from agents.linkshare_agent.sdk_signature import generate_sign_sdk_style

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_headers_according_to_sdk():
    """根据官方SDK测试不同的请求头组合"""
    logger.info("🔧 根据官方SDK测试请求头组合")
    logger.info("=" * 80)
    
    # 获取access token
    try:
        token_manager = TokenManager()
        access_token = token_manager.get_valid_token()
        logger.info(f"✅ 获取到Access Token: {access_token[:20]}...")
    except Exception as e:
        logger.error(f"❌ 无法获取access token: {e}")
        return
    
    # 基于官方SDK的请求头变体
    header_tests = {
        "官方SDK标准": {
            "Content-Type": "application/json",
            "User-Agent": "sdk_node/1.0.0",
            "x-tts-access-token": access_token
        },
        "移除Accept头": {
            "Content-Type": "application/json", 
            "User-Agent": "sdk_node/1.0.0",
            "x-tts-access-token": access_token
            # 不包含Accept: application/json
        },
        "最小化请求头": {
            "Content-Type": "application/json",
            "x-tts-access-token": access_token
            # 只包含必要的头
        },
        "当前使用方式": {
            "Content-Type": "application/json",
            "User-Agent": "sdk_node/1.0.0", 
            "Accept": "application/json",
            "x-tts-access-token": access_token
        }
    }
    
    # 测试用的最小请求体
    request_body = {
        "material": {
            "material_id": config.DEFAULT_PRODUCT_ID,
            "type": "1"
        }
    }
    
    results = []
    
    for test_name, headers in header_tests.items():
        logger.info(f"\n🧪 测试: {test_name}")
        
        try:
            # 构建签名请求
            timestamp = int(time.time())
            
            request_option = {
                'uri': config.LINK_GENERATE_URL,
                'method': 'POST',
                'qs': {
                    'app_key': config.APP_KEY,
                    'timestamp': timestamp
                },
                'body': request_body,
                'headers': {k: v for k, v in headers.items() if k != 'x-tts-access-token'}
            }
            
            # 生成签名
            signature = generate_sign_sdk_style(request_option, config.APP_SECRET)
            
            # 构建URL
            url = f"{config.LINK_GENERATE_URL}?app_key={config.APP_KEY}&timestamp={timestamp}&sign={signature}"
            
            # 记录请求详情
            logger.info(f"  请求头:")
            for key, value in headers.items():
                if key == 'x-tts-access-token':
                    logger.info(f"    {key}: {value[:20]}...")
                else:
                    logger.info(f"    {key}: {value}")
            
            # 发送请求
            response = requests.post(
                url,
                headers=headers,
                json=request_body,
                timeout=30
            )
            
            # 处理响应
            logger.info(f"  状态码: {response.status_code}")
            
            try:
                response_data = response.json()
                logger.info(f"  响应: {json.dumps(response_data, indent=4, ensure_ascii=False)}")
                
                success = response.status_code == 200 and response_data.get('code') == 0
                
                if success:
                    logger.info(f"  ✅ 成功!")
                else:
                    error_code = response_data.get('code', 'N/A')
                    error_msg = response_data.get('message', 'N/A')
                    logger.info(f"  ❌ 失败: Code {error_code}, {error_msg}")
                
                results.append({
                    "test": test_name,
                    "success": success,
                    "status_code": response.status_code,
                    "error_code": error_code,
                    "error_message": error_msg,
                    "headers": headers
                })
                
            except Exception as json_error:
                logger.info(f"  ❌ JSON解析失败: {response.text[:200]}")
                results.append({
                    "test": test_name,
                    "success": False,
                    "status_code": response.status_code,
                    "error": f"JSON解析失败: {str(json_error)}",
                    "headers": headers
                })
                
        except Exception as e:
            logger.error(f"  ❌ 请求异常: {e}")
            results.append({
                "test": test_name,
                "success": False,
                "error": str(e),
                "headers": headers
            })
    
    return results

def analyze_results(results):
    """分析测试结果"""
    logger.info(f"\n📊 请求头测试结果分析")
    logger.info("=" * 80)
    
    successful_tests = [r for r in results if r.get('success')]
    failed_tests = [r for r in results if not r.get('success')]
    
    logger.info(f"✅ 成功的测试: {len(successful_tests)}")
    for result in successful_tests:
        logger.info(f"  - {result['test']}")
    
    logger.info(f"\n❌ 失败的测试: {len(failed_tests)}")
    for result in failed_tests:
        error = result.get('error', f"Code {result.get('error_code', 'N/A')}: {result.get('error_message', 'N/A')}")
        logger.info(f"  - {result['test']}: {error}")
    
    # 分析错误模式
    if failed_tests:
        error_codes = {}
        for result in failed_tests:
            code = result.get('error_code', 'N/A')
            if code not in error_codes:
                error_codes[code] = []
            error_codes[code].append(result['test'])
        
        logger.info(f"\n🔍 错误代码分析:")
        for code, tests in error_codes.items():
            logger.info(f"  错误代码 {code}:")
            for test in tests:
                logger.info(f"    - {test}")
    
    # 结论
    logger.info(f"\n💡 结论:")
    if successful_tests:
        logger.info(f"  ✅ 有成功的请求头组合，问题可能不在请求头格式")
        logger.info(f"  推荐使用: {successful_tests[0]['test']}")
    elif all(r.get('error_code') == 106001 for r in failed_tests if r.get('error_code')):
        logger.info(f"  ⚠️ 所有测试都返回106001 (签名参数无效)")
        logger.info(f"  这表明问题在签名或权限层面，而不是请求头格式")
    else:
        logger.info(f"  ⚠️ 多种错误模式，需要进一步调查")

def compare_with_official_sdk():
    """与官方SDK源码对比"""
    logger.info(f"\n📋 与官方SDK源码对比")
    logger.info("=" * 80)
    
    # 官方SDK源码 (create-trans-request-options.ts 第46-51行)
    official_sdk_headers = {
        "Content-Type": "application/json",
        "User-Agent": "sdk_node/1.0.0"
        # x-tts-access-token 通过参数传入，不在这里设置
    }
    
    logger.info("📁 官方SDK源码分析:")
    logger.info("文件: agents/linkshare_agent/nodejs_sdk/client/create-trans-request-options.ts")
    logger.info("第46-51行:")
    logger.info("""
    option.headers = {
      "Content-Type": "application/json",
      'User-Agent': 'sdk_node/1.0.0',
      // "x-tts-access-token": access_token,  // 注释掉了
      ...option.headers,
    };
    """)
    
    logger.info("🔍 关键发现:")
    logger.info("  1. 官方SDK只设置Content-Type和User-Agent")
    logger.info("  2. x-tts-access-token在SDK中是注释状态")
    logger.info("  3. 没有设置Accept头")
    logger.info("  4. x-tts-access-token可能通过其他方式传递")
    
    logger.info("\n💡 建议的标准请求头:")
    recommended = {
        "Content-Type": "application/json",
        "User-Agent": "sdk_node/1.0.0",
        "x-tts-access-token": "从token_manager获取"
    }
    
    for key, value in recommended.items():
        logger.info(f"  {key}: {value}")

if __name__ == "__main__":
    logger.info("🔍 开始测试HTTP请求头格式")
    
    # 1. 测试不同请求头组合
    results = test_headers_according_to_sdk()
    
    # 2. 分析结果
    analyze_results(results)
    
    # 3. 与官方SDK对比
    compare_with_official_sdk()
    
    logger.info(f"\n🏁 请求头测试完成!")
