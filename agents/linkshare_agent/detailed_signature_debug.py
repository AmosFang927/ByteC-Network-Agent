#!/usr/bin/env python3
"""
详细签名拼接过程调试 - 列印签名算法的每个步骤
包括输入前的原始数据、拼接过程、中间结果
"""

import sys
import logging
import json
import time
import hashlib
import hmac
import urllib.parse
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

def manual_signature_generation(request_option, app_secret):
    """手动实现签名生成过程，详细记录每个步骤"""
    logger.info("🔐 开始手动签名生成过程...")
    
    # 1. 解析输入参数
    logger.info("\n" + "=" * 80)
    logger.info("📋 步骤1: 解析输入参数")
    logger.info("=" * 80)
    
    uri = request_option.get('uri', '')
    qs = request_option.get('qs', {})
    body = request_option.get('body', {})
    headers = request_option.get('headers', {})
    
    logger.info(f"原始输入参数:")
    logger.info(f"  uri: {uri}")
    logger.info(f"  qs: {json.dumps(qs, indent=4)}")
    logger.info(f"  body: {json.dumps(body, indent=4, ensure_ascii=False)}")
    logger.info(f"  headers: {json.dumps(headers, indent=4)}")
    logger.info(f"  app_secret: {app_secret[:10]}...{app_secret[-10:]}")
    
    # 2. 提取URL路径
    logger.info("\n" + "=" * 80)
    logger.info("📋 步骤2: 提取URL路径")
    logger.info("=" * 80)
    
    from urllib.parse import urlparse
    parsed_url = urlparse(uri)
    path = parsed_url.path
    
    logger.info(f"完整URI: {uri}")
    logger.info(f"解析后的路径: {path}")
    logger.info(f"路径长度: {len(path)} 字符")
    
    # 3. 处理查询参数
    logger.info("\n" + "=" * 80)
    logger.info("📋 步骤3: 处理查询参数")
    logger.info("=" * 80)
    
    # 排除的参数 (根据SDK逻辑)
    exclude_keys = ['sign', 'access_token']
    logger.info(f"排除的参数键: {exclude_keys}")
    
    # 过滤查询参数
    filtered_qs = {}
    for key, value in qs.items():
        if key not in exclude_keys:
            filtered_qs[key] = value
        else:
            logger.info(f"  排除参数: {key}")
    
    logger.info(f"过滤后的查询参数: {json.dumps(filtered_qs, indent=4)}")
    
    # 排序查询参数
    sorted_keys = sorted(filtered_qs.keys())
    logger.info(f"排序后的参数键: {sorted_keys}")
    
    # 构建查询字符串
    query_parts = []
    for key in sorted_keys:
        value = filtered_qs[key]
        encoded_key = urllib.parse.quote_plus(str(key))
        encoded_value = urllib.parse.quote_plus(str(value))
        query_part = f"{encoded_key}={encoded_value}"
        query_parts.append(query_part)
        logger.info(f"  {key} -> {encoded_key}={encoded_value}")
    
    query_string = "&".join(query_parts)
    logger.info(f"最终查询字符串: {query_string}")
    logger.info(f"查询字符串长度: {len(query_string)} 字符")
    
    # 4. 处理请求体
    logger.info("\n" + "=" * 80)
    logger.info("📋 步骤4: 处理请求体")
    logger.info("=" * 80)
    
    if body:
        body_string = json.dumps(body, separators=(',', ':'), ensure_ascii=False)
        logger.info(f"原始body: {json.dumps(body, indent=4, ensure_ascii=False)}")
        logger.info(f"压缩后的body字符串: {body_string}")
        logger.info(f"Body字符串长度: {len(body_string)} 字符")
        logger.info(f"Body字符串编码: UTF-8")
    else:
        body_string = ""
        logger.info(f"Body为空")
    
    # 5. 构建签名字符串
    logger.info("\n" + "=" * 80)
    logger.info("📋 步骤5: 构建签名字符串")
    logger.info("=" * 80)
    
    # 按照SDK逻辑构建签名字符串
    if query_string:
        signature_base = f"{path}?{query_string}{body_string}"
    else:
        signature_base = f"{path}{body_string}"
    
    logger.info(f"签名基础字符串构建:")
    logger.info(f"  路径: {path}")
    if query_string:
        logger.info(f"  + 查询字符串: ?{query_string}")
    logger.info(f"  + Body字符串: {body_string}")
    logger.info(f"签名基础字符串: {signature_base}")
    logger.info(f"签名基础字符串长度: {len(signature_base)} 字符")
    
    # 6. 包装APP_SECRET
    logger.info("\n" + "=" * 80)
    logger.info("📋 步骤6: 包装APP_SECRET")
    logger.info("=" * 80)
    
    wrapped_string = f"{app_secret}{signature_base}{app_secret}"
    logger.info(f"包装过程:")
    logger.info(f"  APP_SECRET: {app_secret[:10]}...{app_secret[-10:]}")
    logger.info(f"  + 签名基础字符串: {signature_base}")
    logger.info(f"  + APP_SECRET: {app_secret[:10]}...{app_secret[-10:]}")
    logger.info(f"包装后字符串: {app_secret[:10]}...{signature_base}...{app_secret[-10:]}")
    logger.info(f"包装后字符串长度: {len(wrapped_string)} 字符")
    
    # 7. HMAC-SHA256计算
    logger.info("\n" + "=" * 80)
    logger.info("📋 步骤7: HMAC-SHA256计算")
    logger.info("=" * 80)
    
    logger.info(f"HMAC输入:")
    logger.info(f"  key (APP_SECRET): {app_secret[:10]}...{app_secret[-10:]} (长度: {len(app_secret)})")
    logger.info(f"  message: {wrapped_string[:50]}...{wrapped_string[-50:]} (长度: {len(wrapped_string)})")
    
    # 计算HMAC-SHA256
    signature_bytes = hmac.new(
        app_secret.encode('utf-8'),
        wrapped_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    logger.info(f"HMAC-SHA256结果:")
    logger.info(f"  十六进制签名: {signature_bytes}")
    logger.info(f"  签名长度: {len(signature_bytes)} 字符")
    
    return signature_bytes

def compare_with_sdk_signature(request_option, app_secret):
    """与SDK签名进行对比"""
    logger.info("\n" + "=" * 80)
    logger.info("🔄 与SDK签名进行对比")
    logger.info("=" * 80)
    
    # 手动签名
    manual_signature = manual_signature_generation(request_option, app_secret)
    
    # SDK签名
    from agents.linkshare_agent.sdk_signature import generate_sign_sdk_style
    sdk_signature = generate_sign_sdk_style(request_option, app_secret)
    
    logger.info(f"签名对比:")
    logger.info(f"  手动签名: {manual_signature}")
    logger.info(f"  SDK签名:  {sdk_signature}")
    logger.info(f"  是否一致: {'✅ 一致' if manual_signature == sdk_signature else '❌ 不一致'}")
    
    if manual_signature != sdk_signature:
        logger.warning("⚠️ 签名不一致！可能存在实现差异")
        # 逐字符对比
        min_len = min(len(manual_signature), len(sdk_signature))
        for i in range(min_len):
            if manual_signature[i] != sdk_signature[i]:
                logger.warning(f"第 {i+1} 个字符不同: 手动='{manual_signature[i]}' vs SDK='{sdk_signature[i]}'")
                break
    
    return sdk_signature

def detailed_signature_debug():
    """详细的签名调试"""
    logger.info("🚀 开始详细签名调试...")
    
    try:
        # 1. 基础信息
        logger.info("\n" + "=" * 100)
        logger.info("📋 基础配置信息")
        logger.info("=" * 100)
        
        token_data = load_current_tokens()
        access_token = token_data.get('access_token', '')
        
        logger.info(f"APP_KEY: {config.APP_KEY}")
        logger.info(f"APP_SECRET: {config.APP_SECRET[:10]}...{config.APP_SECRET[-10:]}")
        logger.info(f"ACCESS_TOKEN: {access_token[:30]}...{access_token[-20:]}")
        
        # 2. 构建请求参数
        logger.info("\n" + "=" * 100)
        logger.info("📋 构建请求参数")
        logger.info("=" * 100)
        
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
        
        logger.info(f"请求选项:")
        logger.info(f"  uri: {request_option['uri']}")
        logger.info(f"  qs: {json.dumps(request_option['qs'], indent=4)}")
        logger.info(f"  body: {json.dumps(request_option['body'], indent=4, ensure_ascii=False)}")
        logger.info(f"  headers: {json.dumps(request_option['headers'], indent=4)}")
        
        # 3. 详细的签名过程
        signature = compare_with_sdk_signature(request_option, config.APP_SECRET)
        
        # 4. 最终结果
        logger.info("\n" + "=" * 100)
        logger.info("📋 最终签名结果")
        logger.info("=" * 100)
        
        logger.info(f"最终签名: {signature}")
        logger.info(f"签名长度: {len(signature)} 字符")
        logger.info(f"签名格式: 64位十六进制字符串")
        
        # 5. 完整的API调用信息
        logger.info("\n" + "=" * 100)
        logger.info("📋 完整API调用信息")
        logger.info("=" * 100)
        
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
        
        logger.info(f"最终HTTP请求:")
        logger.info(f"  URL: {full_url}")
        logger.info(f"  查询参数: {json.dumps(url_params, indent=4)}")
        logger.info(f"  请求头: {json.dumps({k: v[:30] + '...' if len(v) > 30 else v for k, v in headers.items()}, indent=4)}")
        logger.info(f"  请求体: {json.dumps(request_body, indent=4, ensure_ascii=False)}")
        
        # 6. 发送请求测试
        logger.info("\n" + "=" * 100)
        logger.info("📋 发送请求测试")
        logger.info("=" * 100)
        
        import requests
        
        response = requests.post(
            full_url,
            params=url_params,
            headers=headers,
            json=request_body,
            timeout=30
        )
        
        logger.info(f"响应状态码: {response.status_code}")
        try:
            response_data = response.json()
            logger.info(f"响应内容: {json.dumps(response_data, indent=4, ensure_ascii=False)}")
        except json.JSONDecodeError:
            logger.info(f"响应内容 (非JSON): {response.text}")
        
        return response.status_code == 200 and response.json().get('code') == 0 if response.headers.get('content-type', '').startswith('application/json') else False
        
    except Exception as e:
        logger.error(f"❌ 调试过程中发生错误: {e}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")
        return False

def main():
    """主函数"""
    logger.info("🚀 启动详细签名拼接过程调试...")
    logger.info("🎯 目标: 详细记录签名算法的每个步骤和中间结果")
    
    try:
        success = detailed_signature_debug()
        
        logger.info("\n🎉 详细签名调试完成!")
        return 0 if success else 1
        
    except Exception as e:
        logger.error(f"❌ 调试过程中发生错误: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 