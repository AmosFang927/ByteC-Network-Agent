#!/usr/bin/env python3
"""
完全使用SDK进行参数拼接和签名的测试
不再手动实现任何签名逻辑，全部交给SDK处理
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

def test_pure_sdk_gen_tracking_link():
    """完全使用SDK方式测试Gen Tracking Link"""
    logger.info("🚀 开始完全SDK方式测试Gen Tracking Link")
    logger.info("=" * 80)
    
    try:
        # 1. 加载基础数据
        token_data = load_current_tokens()
        access_token = token_data.get('access_token', '')
        
        api_host = config.API_BASE_URL
        api_path = f"/affiliate_creator/{config.APP_VERSION}/affiliate_sharing_links/generate_batch"
        full_url = api_host + api_path
        
        # 2. 构建请求体
        request_body = {
            "channel": config.DEFAULT_CHANNEL,
            "material": {
                "id": config.DEFAULT_PRODUCT_ID,
                "type": "PRODUCT"
            },
            "tags": config.DEFAULT_TAGS
        }
        
        timestamp = str(int(time.time()))
        
        logger.info("📋 请求基础信息:")
        logger.info(f"  URL: {full_url}")
        logger.info(f"  APP_KEY: {config.APP_KEY}")
        logger.info(f"  TIMESTAMP: {timestamp}")
        logger.info(f"  REQUEST_BODY: {json.dumps(request_body, ensure_ascii=False)}")
        
        # 3. 构建SDK期望的request_option格式
        # 重要：这里完全按照SDK的期望格式，不做任何手动处理
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
        
        logger.info(f"\n🔧 SDK输入参数:")
        logger.info(f"  URI: {request_option['uri']}")
        logger.info(f"  QS: {json.dumps(request_option['qs'], indent=4)}")
        logger.info(f"  BODY: {json.dumps(request_option['body'], indent=4, ensure_ascii=False)}")
        logger.info(f"  HEADERS: {json.dumps(request_option['headers'], indent=4)}")
        
        # 4. 使用SDK生成签名
        logger.info(f"\n🔐 调用SDK生成签名...")
        signature = generate_sign_sdk_style(request_option, config.APP_SECRET)
        
        logger.info(f"✅ SDK签名生成成功: {signature}")
        
        # 5. 构建最终HTTP请求（完全依赖SDK结果）
        # 注意：access_token不放在URL参数中，而是放在header中
        url_params = {
            'app_key': config.APP_KEY,
            'timestamp': timestamp,
            'sign': signature
            # 注意：access_token 不在URL参数中
        }
        
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'sdk_node/1.0.0',
            'Accept': 'application/json',
            'x-tts-access-token': access_token  # access_token在header中
        }
        
        logger.info(f"\n🌐 HTTP请求构建:")
        logger.info(f"  METHOD: POST")
        logger.info(f"  URL: {full_url}")
        logger.info(f"  URL_PARAMS: {json.dumps(url_params, indent=4)}")
        logger.info(f"  HEADERS: {json.dumps({k: v[:50] + '...' if len(v) > 50 else v for k, v in headers.items()}, indent=4)}")
        logger.info(f"  BODY: {json.dumps(request_body, indent=4, ensure_ascii=False)}")
        
        # 6. 发送HTTP请求
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
        
        # 7. 分析响应
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

def test_multiple_scenarios():
    """测试多种场景"""
    logger.info(f"\n" + "=" * 100)
    logger.info(f"🧪 多场景测试")
    logger.info("=" * 100)
    
    scenarios = [
        {
            "name": "标准完整参数",
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
            "name": "最小参数",
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
        logger.info(f"\n🔬 场景{i}: {scenario['name']}")
        logger.info("-" * 50)
        
        try:
            # 使用相同的逻辑，但不同的请求体
            token_data = load_current_tokens()
            access_token = token_data.get('access_token', '')
            
            api_host = config.API_BASE_URL
            api_path = f"/affiliate_creator/{config.APP_VERSION}/affiliate_sharing_links/generate_batch"
            full_url = api_host + api_path
            
            timestamp = str(int(time.time()))
            
            request_option = {
                'uri': full_url,
                'qs': {
                    'app_key': config.APP_KEY,
                    'access_token': access_token,
                    'timestamp': timestamp
                },
                'body': scenario['body'],
                'headers': {
                    'Content-Type': 'application/json'
                }
            }
            
            # 使用SDK生成签名
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
            
            logger.info(f"  请求体: {json.dumps(scenario['body'], ensure_ascii=False)}")
            logger.info(f"  签名: {signature}")
            
            response = requests.post(
                full_url,
                params=url_params,
                headers=headers,
                json=scenario['body'],
                timeout=30
            )
            
            response_data = response.json()
            code = response_data.get('code')
            message = response_data.get('message', '')
            
            success = code == 0
            logger.info(f"  结果: {'✅ 成功' if success else f'❌ 失败 ({code}: {message})'}")
            
            results.append({
                "scenario": scenario['name'],
                "success": success,
                "code": code,
                "message": message
            })
            
        except Exception as e:
            logger.error(f"  ❌ 场景测试失败: {e}")
            results.append({
                "scenario": scenario['name'],
                "success": False,
                "code": None,
                "message": str(e)
            })
    
    # 汇总结果
    logger.info(f"\n📊 测试结果汇总:")
    success_count = sum(1 for r in results if r['success'])
    logger.info(f"  总场景数: {len(results)}")
    logger.info(f"  成功场景: {success_count}")
    logger.info(f"  失败场景: {len(results) - success_count}")
    logger.info(f"  成功率: {(success_count / len(results) * 100):.1f}%")
    
    logger.info(f"\n详细结果:")
    for result in results:
        status = "✅" if result['success'] else "❌"
        logger.info(f"  {status} {result['scenario']}: {result.get('message', 'OK')}")
    
    return results

def main():
    """主函数"""
    logger.info("🎯 开始完全SDK方式的Gen Tracking Link测试")
    logger.info("💡 关键改进：Query字符串拼接使用SDK方式（keyvaluekeyvalue）而非HTTP标准格式")
    
    try:
        # 1. 标准测试
        success = test_pure_sdk_gen_tracking_link()
        
        if success:
            logger.info(f"\n🎉 标准测试成功！继续多场景测试...")
            # 2. 多场景测试
            test_multiple_scenarios()
        else:
            logger.info(f"\n🔍 标准测试失败，继续多场景测试看是否有其他问题...")
            test_multiple_scenarios()
        
        logger.info(f"\n🏁 完全SDK方式测试完成！")
        return 0
        
    except Exception as e:
        logger.error(f"❌ 测试过程中发生错误: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 