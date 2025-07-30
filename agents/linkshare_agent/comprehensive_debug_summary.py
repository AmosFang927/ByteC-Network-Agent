#!/usr/bin/env python3
"""
全面调试总结 - 详细列印所有关键信息
包括签名参数前后、Gen Tracking Link的完整输入输出
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

def comprehensive_debug_test():
    """全面调试测试 - 详细记录所有参数"""
    logger.info("🚀 开始全面调试测试...")
    
    try:
        # 1. 基础配置信息
        logger.info("\n" + "=" * 100)
        logger.info("📋 基础配置信息")
        logger.info("=" * 100)
        
        logger.info(f"APP_KEY: {config.APP_KEY}")
        logger.info(f"APP_SECRET: {config.APP_SECRET[:10]}...{config.APP_SECRET[-10:]}")
        logger.info(f"APP_VERSION: {config.APP_VERSION}")
        logger.info(f"API_BASE_URL: {config.API_BASE_URL}")
        logger.info(f"DEFAULT_PRODUCT_ID: {config.DEFAULT_PRODUCT_ID}")
        logger.info(f"DEFAULT_CHANNEL: {config.DEFAULT_CHANNEL}")
        logger.info(f"DEFAULT_TAGS: {config.DEFAULT_TAGS}")
        
        # 2. Token信息
        logger.info("\n" + "=" * 100)
        logger.info("🔐 Token信息")
        logger.info("=" * 100)
        
        token_data = load_current_tokens()
        access_token = token_data.get('access_token', '')
        access_token_expire = token_data.get('access_token_expire_in', 0)
        current_time = time.time()
        
        logger.info(f"ACCESS_TOKEN: {access_token[:50]}...{access_token[-20:]}")
        logger.info(f"ACCESS_TOKEN_LENGTH: {len(access_token)} 字符")
        logger.info(f"ACCESS_TOKEN_EXPIRE: {access_token_expire}")
        logger.info(f"CURRENT_TIME: {current_time}")
        logger.info(f"TOKEN_VALID: {'✅ 有效' if access_token_expire > current_time else '❌ 过期'}")
        logger.info(f"REMAINING_TIME: {int(access_token_expire - current_time)} 秒")
        
        # 3. API端点构建
        logger.info("\n" + "=" * 100)
        logger.info("🔗 API端点构建")
        logger.info("=" * 100)
        
        api_host = config.API_BASE_URL
        api_path = f"/affiliate_creator/{config.APP_VERSION}/affiliate_sharing_links/generate_batch"
        full_url = api_host + api_path
        
        logger.info(f"API_HOST: {api_host}")
        logger.info(f"API_PATH: {api_path}")
        logger.info(f"FULL_URL: {full_url}")
        logger.info(f"URL_LENGTH: {len(full_url)} 字符")
        
        # 4. 请求体构建
        logger.info("\n" + "=" * 100)
        logger.info("📤 请求体构建")
        logger.info("=" * 100)
        
        request_body = {
            "channel": config.DEFAULT_CHANNEL,
            "material": {
                "id": config.DEFAULT_PRODUCT_ID,
                "type": "PRODUCT"
            },
            "tags": config.DEFAULT_TAGS
        }
        
        logger.info(f"REQUEST_BODY:")
        logger.info(json.dumps(request_body, indent=4, ensure_ascii=False))
        logger.info(f"REQUEST_BODY_JSON_LENGTH: {len(json.dumps(request_body))} 字符")
        
        # 5. 签名参数构建（传入签名前）
        logger.info("\n" + "=" * 100)
        logger.info("🔧 签名参数构建 (传入签名算法前)")
        logger.info("=" * 100)
        
        timestamp = str(int(time.time()))
        logger.info(f"TIMESTAMP: {timestamp}")
        logger.info(f"TIMESTAMP_LENGTH: {len(timestamp)} 字符")
        
        # 签名用的查询参数
        request_params_for_signature = {
            "app_key": config.APP_KEY,
            "access_token": access_token,
            "timestamp": timestamp
        }
        
        logger.info(f"SIGNATURE_QUERY_PARAMS:")
        for key, value in request_params_for_signature.items():
            if key == "access_token":
                logger.info(f"  {key}: {value[:30]}...{value[-10:]}")
            else:
                logger.info(f"  {key}: {value}")
        
        # 签名用的请求选项
        request_option = {
            'uri': full_url,
            'qs': request_params_for_signature,
            'body': request_body,
            'headers': {
                'Content-Type': 'application/json'
            }
        }
        
        logger.info(f"\nREQUEST_OPTION (传入SDK签名):")
        logger.info(f"  uri: {request_option['uri']}")
        logger.info(f"  qs: {json.dumps(request_option['qs'], indent=6)}")
        logger.info(f"  body: {json.dumps(request_option['body'], indent=6, ensure_ascii=False)}")
        logger.info(f"  headers: {json.dumps(request_option['headers'], indent=6)}")
        
        # 6. 调用签名算法
        logger.info("\n" + "=" * 100)
        logger.info("🔐 调用SDK签名算法")
        logger.info("=" * 100)
        
        logger.info(f"APP_SECRET (用于签名): {config.APP_SECRET[:10]}...{config.APP_SECRET[-10:]}")
        logger.info(f"APP_SECRET_LENGTH: {len(config.APP_SECRET)} 字符")
        
        # 记录签名前的详细信息
        logger.info(f"\n签名前详细信息:")
        logger.info(f"  URI: {request_option['uri']}")
        logger.info(f"  Query String 参数:")
        for key, value in sorted(request_option['qs'].items()):
            if key == "access_token":
                logger.info(f"    {key}={value[:20]}...{value[-10:]}")
            else:
                logger.info(f"    {key}={value}")
        logger.info(f"  Body JSON: {json.dumps(request_option['body'], separators=(',', ':'), ensure_ascii=False)}")
        
        # 调用签名
        signature = generate_sign_sdk_style(request_option, config.APP_SECRET)
        
        logger.info(f"\n签名结果:")
        logger.info(f"  SIGNATURE: {signature}")
        logger.info(f"  SIGNATURE_LENGTH: {len(signature)} 字符")
        
        # 7. 最终HTTP请求参数构建
        logger.info("\n" + "=" * 100)
        logger.info("🌐 最终HTTP请求参数构建")
        logger.info("=" * 100)
        
        # URL查询参数（不包含access_token）
        url_params = {
            'app_key': config.APP_KEY,
            'timestamp': timestamp,
            'sign': signature
        }
        
        logger.info(f"URL_QUERY_PARAMS:")
        for key, value in url_params.items():
            logger.info(f"  {key}: {value}")
        
        # HTTP头部
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'sdk_node/1.0.0',
            'Accept': 'application/json',
            'x-tts-access-token': access_token
        }
        
        logger.info(f"\nHTTP_HEADERS:")
        for key, value in headers.items():
            if key == "x-tts-access-token":
                logger.info(f"  {key}: {value[:30]}...{value[-10:]}")
            else:
                logger.info(f"  {key}: {value}")
        
        # 8. 完整HTTP请求信息
        logger.info("\n" + "=" * 100)
        logger.info("📡 完整HTTP请求信息")
        logger.info("=" * 100)
        
        import requests
        
        logger.info(f"HTTP_METHOD: POST")
        logger.info(f"HTTP_URL: {full_url}")
        logger.info(f"HTTP_PARAMS: {json.dumps(url_params, indent=2)}")
        logger.info(f"HTTP_HEADERS: {json.dumps({k: v[:50] + '...' if len(v) > 50 else v for k, v in headers.items()}, indent=2)}")
        logger.info(f"HTTP_BODY: {json.dumps(request_body, indent=2, ensure_ascii=False)}")
        
        # 完整的curl命令示例
        logger.info(f"\n等效CURL命令:")
        curl_headers = " ".join([f"-H '{k}: {v[:20]}...'" if len(v) > 20 else f"-H '{k}: {v}'" for k, v in headers.items()])
        curl_params = "&".join([f"{k}={v}" for k, v in url_params.items()])
        curl_body = json.dumps(request_body, separators=(',', ':'), ensure_ascii=False)
        logger.info(f"curl -X POST '{full_url}?{curl_params}' \\")
        logger.info(f"  {curl_headers} \\")
        logger.info(f"  -d '{curl_body}'")
        
        # 9. 发送HTTP请求并记录响应
        logger.info("\n" + "=" * 100)
        logger.info("📥 发送HTTP请求并记录响应")
        logger.info("=" * 100)
        
        logger.info(f"发送时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        response = requests.post(
            full_url,
            params=url_params,
            headers=headers,
            json=request_body,
            timeout=30
        )
        
        logger.info(f"响应时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"HTTP_STATUS_CODE: {response.status_code}")
        logger.info(f"RESPONSE_HEADERS:")
        for key, value in response.headers.items():
            logger.info(f"  {key}: {value}")
        
        # 10. 响应体详细分析
        logger.info("\n" + "=" * 100)
        logger.info("📋 响应体详细分析")
        logger.info("=" * 100)
        
        logger.info(f"RESPONSE_TEXT_LENGTH: {len(response.text)} 字符")
        logger.info(f"RESPONSE_ENCODING: {response.encoding}")
        
        try:
            response_data = response.json()
            logger.info(f"RESPONSE_JSON:")
            logger.info(json.dumps(response_data, indent=4, ensure_ascii=False))
            
            # 详细分析响应
            if 'code' in response_data:
                logger.info(f"\nRESPONSE_CODE: {response_data['code']}")
                logger.info(f"CODE_MEANING: {config.API_ERROR_CODES.get(response_data['code'], '未知错误码')}")
            
            if 'message' in response_data:
                logger.info(f"RESPONSE_MESSAGE: {response_data['message']}")
                
            if 'request_id' in response_data:
                logger.info(f"REQUEST_ID: {response_data['request_id']}")
                
            if 'data' in response_data:
                logger.info(f"RESPONSE_DATA: {json.dumps(response_data['data'], indent=4, ensure_ascii=False)}")
                
        except json.JSONDecodeError:
            logger.error(f"RESPONSE_NOT_JSON: {response.text}")
        
        # 11. 问题分析总结
        logger.info("\n" + "=" * 100)
        logger.info("🔍 问题分析总结")
        logger.info("=" * 100)
        
        logger.info(f"✅ 配置验证:")
        logger.info(f"  - APP_KEY: 长度 {len(config.APP_KEY)} 字符")
        logger.info(f"  - APP_SECRET: 长度 {len(config.APP_SECRET)} 字符")
        logger.info(f"  - ACCESS_TOKEN: 长度 {len(access_token)} 字符，有效期剩余 {int(access_token_expire - current_time)} 秒")
        logger.info(f"  - API版本: {config.APP_VERSION}")
        
        logger.info(f"\n✅ 参数验证:")
        logger.info(f"  - 产品ID: {config.DEFAULT_PRODUCT_ID} (长度 {len(config.DEFAULT_PRODUCT_ID)} 字符)")
        logger.info(f"  - Channel: {config.DEFAULT_CHANNEL}")
        logger.info(f"  - Tags: {config.DEFAULT_TAGS}")
        
        logger.info(f"\n✅ 技术验证:")
        logger.info(f"  - SDK签名生成: ✅ 成功")
        logger.info(f"  - HTTP请求发送: ✅ 成功")
        logger.info(f"  - 响应接收: ✅ 成功")
        
        logger.info(f"\n❌ 问题症状:")
        logger.info(f"  - HTTP状态码: {response.status_code}")
        if response.status_code != 200:
            logger.info(f"  - 错误类型: HTTP错误")
        else:
            try:
                response_data = response.json()
                if response_data.get('code') != 0:
                    logger.info(f"  - 错误类型: 业务逻辑错误")
                    logger.info(f"  - 错误码: {response_data.get('code')}")
                    logger.info(f"  - 错误信息: {response_data.get('message')}")
            except:
                pass
        
        logger.info(f"\n🎯 下一步建议:")
        logger.info(f"  1. 检查TikTok Shop开发者后台的应用配置")
        logger.info(f"  2. 验证ACCESS_TOKEN的权限scope是否包含affiliate相关权限")
        logger.info(f"  3. 确认账户是否已开通联盟营销功能")
        logger.info(f"  4. 检查产品ID是否有推广权限")
        logger.info(f"  5. 对比官方SDK的签名实现细节")
        
        return response.status_code == 200 and response.json().get('code') == 0 if response.headers.get('content-type', '').startswith('application/json') else False
        
    except Exception as e:
        logger.error(f"❌ 测试过程中发生错误: {e}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")
        return False

def main():
    """主函数"""
    logger.info("🚀 启动全面调试总结...")
    logger.info("🎯 目标: 详细记录所有签名参数和API调用的完整输入输出")
    
    try:
        success = comprehensive_debug_test()
        
        logger.info("\n🎉 全面调试总结完成!")
        return 0 if success else 1
        
    except Exception as e:
        logger.error(f"❌ 测试过程中发生错误: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 