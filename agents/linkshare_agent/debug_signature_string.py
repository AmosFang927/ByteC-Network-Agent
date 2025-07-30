#!/usr/bin/env python3
"""
SDK签名拼接串详细调试
展示传入SDK前的完整签名字符串构建过程
"""

import sys
import logging
import json
import time
import urllib.parse
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

def manual_signature_string_construction():
    """手动构建签名字符串，展示每个步骤"""
    logger.info("🔧 手动构建签名字符串 - 逐步展示")
    logger.info("=" * 80)
    
    try:
        # 1. 基础数据准备
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
        
        logger.info("📋 基础数据:")
        logger.info(f"  URL: {full_url}")
        logger.info(f"  APP_KEY: {config.APP_KEY}")
        logger.info(f"  APP_SECRET: {config.APP_SECRET[:10]}...{config.APP_SECRET[-10:]}")
        logger.info(f"  TIMESTAMP: {timestamp}")
        logger.info(f"  ACCESS_TOKEN: {access_token[:50]}...{access_token[-20:]}")
        logger.info(f"  REQUEST_BODY: {json.dumps(request_body, separators=(',', ':'), ensure_ascii=False)}")
        
        # 2. 解析URL
        from urllib.parse import urlparse
        parsed_url = urlparse(full_url)
        
        logger.info(f"\n🔗 URL解析:")
        logger.info(f"  SCHEME: {parsed_url.scheme}")
        logger.info(f"  NETLOC: {parsed_url.netloc}")
        logger.info(f"  PATH: {parsed_url.path}")
        logger.info(f"  QUERY: {parsed_url.query}")
        
        # 3. 构建Query参数 (排除sign和access_token)
        query_params = {
            "app_key": config.APP_KEY,
            "timestamp": timestamp
            # 注意: access_token 不参与签名
            # 注意: sign 不参与签名
        }
        
        logger.info(f"\n📝 Query参数构建 (用于签名):")
        for key, value in query_params.items():
            logger.info(f"  {key}: {value}")
        
        # 4. 按键名排序Query参数
        sorted_query_items = sorted(query_params.items())
        
        logger.info(f"\n🔤 Query参数排序:")
        for key, value in sorted_query_items:
            logger.info(f"  {key}: {value}")
        
        # 5. 构建Query字符串
        query_string_parts = []
        for key, value in sorted_query_items:
            # URL编码键值对
            encoded_key = urllib.parse.quote_plus(str(key))
            encoded_value = urllib.parse.quote_plus(str(value))
            query_string_parts.append(f"{encoded_key}={encoded_value}")
        
        query_string = "&".join(query_string_parts)
        
        logger.info(f"\n🔗 Query字符串构建:")
        logger.info(f"  编码前: {dict(sorted_query_items)}")
        logger.info(f"  编码后各部分:")
        for part in query_string_parts:
            logger.info(f"    {part}")
        logger.info(f"  最终Query字符串: {query_string}")
        
        # 6. 处理请求体
        # 将JSON压缩为最紧凑格式
        compressed_body = json.dumps(request_body, separators=(',', ':'), ensure_ascii=False)
        
        logger.info(f"\n📤 请求体处理:")
        logger.info(f"  原始Body: {json.dumps(request_body, indent=2, ensure_ascii=False)}")
        logger.info(f"  压缩Body: {compressed_body}")
        logger.info(f"  Body长度: {len(compressed_body)} 字符")
        
        # 7. 构建基础签名字符串
        # 格式: HTTP方法 + 路径 + Query字符串 + 请求体
        http_method = "POST"
        path = parsed_url.path
        
        base_string_parts = [
            http_method,
            path,
            query_string,
            compressed_body
        ]
        
        base_string = "".join(base_string_parts)
        
        logger.info(f"\n🔨 基础签名字符串构建:")
        logger.info(f"  HTTP方法: '{http_method}'")
        logger.info(f"  路径: '{path}'")
        logger.info(f"  Query字符串: '{query_string}'")
        logger.info(f"  请求体: '{compressed_body}'")
        logger.info(f"  拼接规则: HTTP方法 + 路径 + Query字符串 + 请求体")
        logger.info(f"  基础字符串: '{base_string}'")
        logger.info(f"  基础字符串长度: {len(base_string)} 字符")
        
        # 8. 用APP_SECRET包装
        wrapped_string = config.APP_SECRET + base_string + config.APP_SECRET
        
        logger.info(f"\n🔐 APP_SECRET包装:")
        logger.info(f"  APP_SECRET: '{config.APP_SECRET[:10]}...{config.APP_SECRET[-10:]}'")
        logger.info(f"  包装规则: APP_SECRET + 基础字符串 + APP_SECRET")
        logger.info(f"  包装后字符串: '{config.APP_SECRET[:10]}...{wrapped_string[50:-50]}...{config.APP_SECRET[-10:]}'")
        logger.info(f"  包装后长度: {len(wrapped_string)} 字符")
        
        # 9. 展示完整的待签名字符串
        logger.info(f"\n📋 完整待签名字符串:")
        logger.info(f"  完整字符串: '{wrapped_string}'")
        logger.info(f"  字符串长度: {len(wrapped_string)} 字符")
        
        # 10. 生成HMAC-SHA256签名 (手动计算)
        import hmac
        import hashlib
        
        # 注意：这里用空字符串作为HMAC密钥，因为SDK的实现就是这样的
        manual_signature = hmac.new(
            b'',  # 空密钥
            wrapped_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        logger.info(f"\n🔑 HMAC-SHA256签名计算:")
        logger.info(f"  HMAC密钥: '' (空字符串)")
        logger.info(f"  待签名数据: {wrapped_string[:50]}...{wrapped_string[-50:]}")
        logger.info(f"  签名算法: HMAC-SHA256")
        logger.info(f"  手动计算签名: {manual_signature}")
        
        return {
            "url": full_url,
            "query_params": query_params,
            "sorted_query_items": sorted_query_items,
            "query_string": query_string,
            "request_body": request_body,
            "compressed_body": compressed_body,
            "http_method": http_method,
            "path": path,
            "base_string": base_string,
            "wrapped_string": wrapped_string,
            "manual_signature": manual_signature,
            "timestamp": timestamp,
            "access_token": access_token
        }
        
    except Exception as e:
        logger.error(f"❌ 手动构建签名字符串失败: {e}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")
        return None

def sdk_signature_comparison(manual_data):
    """使用SDK生成签名并对比"""
    logger.info(f"\n🤖 SDK签名生成对比")
    logger.info("=" * 80)
    
    try:
        # 构建request_option (SDK期望的格式)
        request_option = {
            'uri': manual_data['url'],
            'qs': {
                "app_key": config.APP_KEY,
                "access_token": manual_data['access_token'],
                "timestamp": manual_data['timestamp']
            },
            'body': manual_data['request_body'],
            'headers': {
                'Content-Type': 'application/json'
            }
        }
        
        logger.info(f"📋 SDK输入参数:")
        logger.info(f"  URI: {request_option['uri']}")
        logger.info(f"  QS: {json.dumps(request_option['qs'], indent=4)}")
        logger.info(f"  BODY: {json.dumps(request_option['body'], indent=4, ensure_ascii=False)}")
        logger.info(f"  HEADERS: {json.dumps(request_option['headers'], indent=4)}")
        logger.info(f"  APP_SECRET: {config.APP_SECRET[:10]}...{config.APP_SECRET[-10:]}")
        
        # 调用SDK生成签名
        sdk_signature = generate_sign_sdk_style(request_option, config.APP_SECRET)
        
        logger.info(f"\n🔍 签名对比:")
        logger.info(f"  手动计算签名: {manual_data['manual_signature']}")
        logger.info(f"  SDK生成签名:  {sdk_signature}")
        logger.info(f"  签名是否一致: {'✅ 一致' if manual_data['manual_signature'] == sdk_signature else '❌ 不一致'}")
        
        if manual_data['manual_signature'] != sdk_signature:
            logger.warning("⚠️ 签名不一致！分析差异...")
            
            # 逐字符对比
            min_len = min(len(manual_data['manual_signature']), len(sdk_signature))
            for i in range(min_len):
                if manual_data['manual_signature'][i] != sdk_signature[i]:
                    logger.warning(f"  第{i+1}个字符不同: 手动='{manual_data['manual_signature'][i]}' vs SDK='{sdk_signature[i]}'")
                    break
            
            if len(manual_data['manual_signature']) != len(sdk_signature):
                logger.warning(f"  长度不同: 手动={len(manual_data['manual_signature'])} vs SDK={len(sdk_signature)}")
        
        return {
            "sdk_signature": sdk_signature,
            "manual_signature": manual_data['manual_signature'],
            "signatures_match": manual_data['manual_signature'] == sdk_signature,
            "request_option": request_option
        }
        
    except Exception as e:
        logger.error(f"❌ SDK签名生成失败: {e}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")
        return None

def detailed_parameter_breakdown(manual_data, sdk_data):
    """详细参数分解分析"""
    logger.info(f"\n📊 详细参数分解分析")
    logger.info("=" * 80)
    
    logger.info(f"🔢 数值参数:")
    logger.info(f"  APP_KEY: {config.APP_KEY} (长度: {len(config.APP_KEY)})")
    logger.info(f"  APP_SECRET: {config.APP_SECRET} (长度: {len(config.APP_SECRET)})")
    logger.info(f"  TIMESTAMP: {manual_data['timestamp']} (长度: {len(manual_data['timestamp'])})")
    logger.info(f"  PRODUCT_ID: {config.DEFAULT_PRODUCT_ID} (长度: {len(config.DEFAULT_PRODUCT_ID)})")
    logger.info(f"  CHANNEL: {config.DEFAULT_CHANNEL} (长度: {len(config.DEFAULT_CHANNEL)})")
    
    logger.info(f"\n🔗 URL分解:")
    logger.info(f"  完整URL: {manual_data['url']}")
    logger.info(f"  URL长度: {len(manual_data['url'])}")
    logger.info(f"  路径: {manual_data['path']}")
    logger.info(f"  路径长度: {len(manual_data['path'])}")
    
    logger.info(f"\n📝 Query参数分解:")
    logger.info(f"  原始参数: {manual_data['query_params']}")
    logger.info(f"  排序后: {dict(manual_data['sorted_query_items'])}")
    logger.info(f"  Query字符串: {manual_data['query_string']}")
    logger.info(f"  Query长度: {len(manual_data['query_string'])}")
    
    logger.info(f"\n📤 Body分解:")
    logger.info(f"  原始Body: {json.dumps(manual_data['request_body'], ensure_ascii=False)}")
    logger.info(f"  压缩Body: {manual_data['compressed_body']}")
    logger.info(f"  Body长度: {len(manual_data['compressed_body'])}")
    
    logger.info(f"\n🔨 签名字符串分解:")
    logger.info(f"  HTTP方法: '{manual_data['http_method']}' (长度: {len(manual_data['http_method'])})")
    logger.info(f"  路径: '{manual_data['path']}' (长度: {len(manual_data['path'])})")
    logger.info(f"  Query: '{manual_data['query_string']}' (长度: {len(manual_data['query_string'])})")
    logger.info(f"  Body: '{manual_data['compressed_body']}' (长度: {len(manual_data['compressed_body'])})")
    logger.info(f"  基础字符串: '{manual_data['base_string'][:100]}...' (总长度: {len(manual_data['base_string'])})")
    logger.info(f"  包装字符串: 'SECRET+基础字符串+SECRET' (总长度: {len(manual_data['wrapped_string'])})")
    
    logger.info(f"\n🔑 签名结果:")
    logger.info(f"  手动签名: {manual_data['manual_signature']}")
    if sdk_data:
        logger.info(f"  SDK签名:  {sdk_data['sdk_signature']}")
        logger.info(f"  一致性: {'✅ 一致' if sdk_data['signatures_match'] else '❌ 不一致'}")

def generate_final_summary(manual_data, sdk_data):
    """生成最终总结"""
    logger.info(f"\n" + "=" * 100)
    logger.info(f"📋 最终总结")
    logger.info("=" * 100)
    
    logger.info(f"\n🎯 关键发现:")
    
    if sdk_data and sdk_data['signatures_match']:
        logger.info(f"  ✅ 手动构建的签名字符串与SDK完全一致")
        logger.info(f"  ✅ 签名算法实现正确")
        logger.info(f"  ✅ 参数拼接逻辑正确")
    else:
        logger.info(f"  ❌ 手动构建的签名字符串与SDK不一致")
        logger.info(f"  ❌ 需要进一步分析差异原因")
    
    logger.info(f"\n📐 签名字符串构建规则总结:")
    logger.info(f"  1. HTTP方法: POST")
    logger.info(f"  2. API路径: {manual_data['path']}")
    logger.info(f"  3. Query参数: 按key排序，URL编码，用&连接")
    logger.info(f"  4. 请求体: JSON压缩格式，无空格")
    logger.info(f"  5. 基础字符串: 方法+路径+Query+Body")
    logger.info(f"  6. 包装字符串: APP_SECRET+基础字符串+APP_SECRET")
    logger.info(f"  7. 签名: HMAC-SHA256(空密钥, 包装字符串)")
    
    logger.info(f"\n🔍 具体数值:")
    logger.info(f"  基础字符串长度: {len(manual_data['base_string'])} 字符")
    logger.info(f"  包装字符串长度: {len(manual_data['wrapped_string'])} 字符")
    logger.info(f"  最终签名: {manual_data['manual_signature']}")
    
    if sdk_data:
        logger.info(f"  SDK签名: {sdk_data['sdk_signature']}")
        
    logger.info(f"\n💡 建议:")
    if sdk_data and sdk_data['signatures_match']:
        logger.info(f"  ✅ 签名实现无误，问题可能在权限或配置层面")
        logger.info(f"  ✅ 可以专注于账户权限和产品配置问题")
    else:
        logger.info(f"  ❌ 需要深入分析SDK实现细节")
        logger.info(f"  ❌ 检查参数编码、排序或拼接逻辑")

def main():
    """主函数"""
    logger.info("🔍 开始SDK签名拼接串详细分析...")
    
    try:
        # 1. 手动构建签名字符串
        manual_data = manual_signature_string_construction()
        if not manual_data:
            logger.error("❌ 手动构建失败，程序退出")
            return 1
        
        # 2. SDK签名对比
        sdk_data = sdk_signature_comparison(manual_data)
        
        # 3. 详细参数分解
        detailed_parameter_breakdown(manual_data, sdk_data)
        
        # 4. 生成最终总结
        generate_final_summary(manual_data, sdk_data)
        
        logger.info(f"\n🎉 签名拼接串分析完成!")
        return 0
        
    except Exception as e:
        logger.error(f"❌ 分析过程中发生错误: {e}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 