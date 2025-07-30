#!/usr/bin/env python3
"""
专门使用SDK签名验证Gen Tracking Link
确认SDK签名是否能正常调用API
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

def test_sdk_signature_only():
    """专门测试SDK签名"""
    logger.info("🚀 开始SDK签名专用测试...")
    
    try:
        # 1. 加载基础信息
        logger.info("\n" + "=" * 80)
        logger.info("📋 基础信息")
        logger.info("=" * 80)
        
        token_data = load_current_tokens()
        access_token = token_data.get('access_token', '')
        access_token_expire = token_data.get('access_token_expire_in', 0)
        current_time = time.time()
        
        logger.info(f"APP_KEY: {config.APP_KEY}")
        logger.info(f"APP_SECRET: {config.APP_SECRET[:10]}...{config.APP_SECRET[-10:]}")
        logger.info(f"ACCESS_TOKEN: {access_token[:30]}...{access_token[-20:]}")
        logger.info(f"TOKEN_VALID: {'✅ 有效' if access_token_expire > current_time else '❌ 过期'}")
        logger.info(f"REMAINING_TIME: {int(access_token_expire - current_time)} 秒")
        
        # 2. 构建请求参数
        logger.info("\n" + "=" * 80)
        logger.info("📋 构建请求参数")
        logger.info("=" * 80)
        
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
        
        logger.info(f"API端点: {full_url}")
        logger.info(f"请求体: {json.dumps(request_body, indent=2, ensure_ascii=False)}")
        logger.info(f"时间戳: {timestamp}")
        
        # 3. 使用SDK生成签名
        logger.info("\n" + "=" * 80)
        logger.info("🔐 使用SDK生成签名")
        logger.info("=" * 80)
        
        logger.info("传入SDK的参数:")
        logger.info(f"  URI: {request_option['uri']}")
        logger.info(f"  Query参数: {json.dumps(request_option['qs'], indent=4)}")
        logger.info(f"  Body: {json.dumps(request_option['body'], indent=4, ensure_ascii=False)}")
        logger.info(f"  Headers: {json.dumps(request_option['headers'], indent=4)}")
        
        # 调用SDK签名
        signature = generate_sign_sdk_style(request_option, config.APP_SECRET)
        
        logger.info(f"SDK生成的签名: {signature}")
        logger.info(f"签名长度: {len(signature)} 字符")
        
        # 4. 构建最终HTTP请求
        logger.info("\n" + "=" * 80)
        logger.info("🌐 构建最终HTTP请求")
        logger.info("=" * 80)
        
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
        
        logger.info(f"最终URL参数: {json.dumps(url_params, indent=2)}")
        logger.info(f"最终请求头: {json.dumps({k: v[:50] + '...' if len(v) > 50 else v for k, v in headers.items()}, indent=2)}")
        logger.info(f"最终请求体: {json.dumps(request_body, indent=2, ensure_ascii=False)}")
        
        # 5. 发送HTTP请求
        logger.info("\n" + "=" * 80)
        logger.info("📤 发送HTTP请求 (使用SDK签名)")
        logger.info("=" * 80)
        
        import requests
        
        logger.info(f"发送时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        response = requests.post(
            full_url,
            params=url_params,
            headers=headers,
            json=request_body,
            timeout=30
        )
        
        logger.info(f"接收时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"HTTP状态码: {response.status_code}")
        
        # 6. 分析响应
        logger.info("\n" + "=" * 80)
        logger.info("📥 响应分析")
        logger.info("=" * 80)
        
        logger.info(f"响应头:")
        for key, value in response.headers.items():
            logger.info(f"  {key}: {value}")
        
        try:
            response_data = response.json()
            logger.info(f"\n响应体:")
            logger.info(json.dumps(response_data, indent=4, ensure_ascii=False))
            
            # 详细分析响应
            code = response_data.get('code')
            message = response_data.get('message', '')
            request_id = response_data.get('request_id', '')
            data = response_data.get('data')
            
            logger.info(f"\n响应解析:")
            logger.info(f"  业务状态码: {code}")
            logger.info(f"  错误信息: {message}")
            logger.info(f"  请求ID: {request_id}")
            logger.info(f"  返回数据: {'有数据' if data else '无数据'}")
            
            # 判断调用结果
            if response.status_code == 200:
                if code == 0:
                    logger.info("🎉 API调用成功！")
                    if data and data.get('affiliate_sharing_links'):
                        links = data.get('affiliate_sharing_links', [])
                        logger.info(f"✅ 成功生成 {len(links)} 个联盟链接")
                        for i, link_info in enumerate(links, 1):
                            link_url = link_info.get('affiliate_sharing_link', 'N/A')
                            logger.info(f"  链接 {i}: {link_url}")
                    return True
                else:
                    logger.error(f"❌ 业务逻辑错误: {code} - {message}")
                    if code == 106001:
                        logger.error("🔍 仍然是106001签名错误，说明SDK签名也有问题")
                    elif code == 36009009:
                        logger.error("🔍 36009009路径错误，可能API版本或端点问题")
                    elif code == 40003:
                        logger.error("🔍 40003签名错误，SDK签名算法可能有问题")
                    return False
            else:
                logger.error(f"❌ HTTP错误: {response.status_code}")
                return False
                
        except json.JSONDecodeError:
            logger.error(f"❌ 响应不是有效JSON: {response.text}")
            return False
        
    except Exception as e:
        logger.error(f"❌ 测试过程中发生错误: {e}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")
        return False

def test_multiple_scenarios():
    """测试多种场景"""
    logger.info("\n" + "=" * 100)
    logger.info("🧪 测试多种场景 (都使用SDK签名)")
    logger.info("=" * 100)
    
    scenarios = [
        {
            "name": "标准配置参数",
            "body": {
                "channel": config.DEFAULT_CHANNEL,
                "material": {
                    "id": config.DEFAULT_PRODUCT_ID,
                    "type": "PRODUCT"
                },
                "tags": config.DEFAULT_TAGS
            }
        },
        {
            "name": "最小参数 (仅material)",
            "body": {
                "material": {
                    "id": config.DEFAULT_PRODUCT_ID,
                    "type": "PRODUCT"
                }
            }
        },
        {
            "name": "简化参数",
            "body": {
                "channel": "test",
                "material": {
                    "id": config.DEFAULT_PRODUCT_ID,
                    "type": "PRODUCT"
                },
                "tags": ["test"]
            }
        }
    ]
    
    results = []
    
    for i, scenario in enumerate(scenarios, 1):
        logger.info(f"\n{'=' * 60}")
        logger.info(f"测试场景 {i}: {scenario['name']}")
        logger.info(f"{'=' * 60}")
        
        try:
            token_data = load_current_tokens()
            access_token = token_data.get('access_token', '')
            
            api_host = config.API_BASE_URL
            api_path = f"/affiliate_creator/{config.APP_VERSION}/affiliate_sharing_links/generate_batch"
            full_url = api_host + api_path
            
            request_body = scenario['body']
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
            
            logger.info(f"请求体: {json.dumps(request_body, indent=2, ensure_ascii=False)}")
            
            # 使用SDK签名
            signature = generate_sign_sdk_style(request_option, config.APP_SECRET)
            
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
            
            import requests
            response = requests.post(
                full_url,
                params=url_params,
                headers=headers,
                json=request_body,
                timeout=30
            )
            
            logger.info(f"状态码: {response.status_code}")
            
            try:
                response_data = response.json()
                code = response_data.get('code')
                message = response_data.get('message', '')
                
                result = {
                    "scenario": scenario['name'],
                    "success": response.status_code == 200 and code == 0,
                    "http_status": response.status_code,
                    "business_code": code,
                    "message": message
                }
                
                if result["success"]:
                    logger.info("✅ 成功!")
                    data = response_data.get('data', {})
                    if data and data.get('affiliate_sharing_links'):
                        links = data.get('affiliate_sharing_links', [])
                        logger.info(f"🔗 生成 {len(links)} 个链接")
                else:
                    logger.info(f"❌ 失败: {code} - {message}")
                
                results.append(result)
                
            except json.JSONDecodeError:
                logger.error(f"❌ 响应非JSON: {response.text}")
                results.append({
                    "scenario": scenario['name'],
                    "success": False,
                    "http_status": response.status_code,
                    "business_code": "JSON_ERROR",
                    "message": response.text
                })
                
        except Exception as e:
            logger.error(f"❌ 场景测试失败: {e}")
            results.append({
                "scenario": scenario['name'],
                "success": False,
                "http_status": -1,
                "business_code": "EXCEPTION",
                "message": str(e)
            })
    
    # 总结结果
    logger.info(f"\n" + "=" * 100)
    logger.info("📊 多场景测试总结")
    logger.info("=" * 100)
    
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    
    logger.info(f"✅ 成功场景: {len(successful)} 个")
    logger.info(f"❌ 失败场景: {len(failed)} 个")
    
    if successful:
        logger.info(f"\n成功的场景:")
        for result in successful:
            logger.info(f"  - {result['scenario']}")
    
    if failed:
        logger.info(f"\n失败的场景:")
        for result in failed:
            logger.info(f"  - {result['scenario']}: {result['business_code']} - {result['message']}")
    
    return len(successful) > 0

def main():
    """主函数"""
    logger.info("🚀 启动SDK签名专用测试...")
    logger.info("🎯 目标: 验证使用SDK签名是否能正常调用Gen Tracking Link API")
    
    try:
        # 1. 单个标准测试
        logger.info("\n🔥 首先进行标准配置测试...")
        standard_success = test_sdk_signature_only()
        
        # 2. 多场景测试
        logger.info("\n🔥 然后进行多场景测试...")
        multiple_success = test_multiple_scenarios()
        
        # 3. 最终结论
        logger.info("\n" + "=" * 100)
        logger.info("🎯 最终结论")
        logger.info("=" * 100)
        
        if standard_success or multiple_success:
            logger.info("✅ SDK签名可以正常工作！")
            logger.info("✅ 问题不在SDK签名算法")
            logger.info("✅ Gen Tracking Link API调用成功")
            logger.info("🎉 你的判断是正确的 - 直接用SDK签名就能解决问题！")
        else:
            logger.info("❌ SDK签名仍然无法正常工作")
            logger.info("🔍 问题可能在于:")
            logger.info("   1. ACCESS TOKEN的权限scope")
            logger.info("   2. 账户配置问题")
            logger.info("   3. 其他业务层面的限制")
            logger.info("   4. SDK本身的问题")
        
        logger.info("\n🎉 SDK签名专用测试完成!")
        return 0 if (standard_success or multiple_success) else 1
        
    except Exception as e:
        logger.error(f"❌ 测试过程中发生错误: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 