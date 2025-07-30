#!/usr/bin/env python3
"""
详细列印传入SDK的所有参数并总结
"""

import sys
import logging
import json
import time
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

def debug_sdk_parameters():
    """调试SDK参数"""
    logger.info("🔍 SDK参数详细调试")
    logger.info("=" * 100)
    
    try:
        # 1. 基础配置参数
        logger.info("📋 1. 基础配置参数")
        logger.info("-" * 60)
        
        config_params = {
            "APP_KEY": config.APP_KEY,
            "APP_SECRET": config.APP_SECRET,
            "APP_VERSION": config.APP_VERSION,
            "API_BASE_URL": config.API_BASE_URL,
            "DEFAULT_PRODUCT_ID": config.DEFAULT_PRODUCT_ID,
            "DEFAULT_CHANNEL": config.DEFAULT_CHANNEL,
            "DEFAULT_TAGS": config.DEFAULT_TAGS
        }
        
        for key, value in config_params.items():
            if key == "APP_SECRET":
                display_value = f"{value[:10]}...{value[-10:]}"
            elif key == "DEFAULT_TAGS":
                display_value = json.dumps(value, ensure_ascii=False)
            else:
                display_value = str(value)
            
            logger.info(f"  {key}: {display_value}")
            logger.info(f"    类型: {type(value).__name__}")
            logger.info(f"    长度: {len(str(value))} 字符")
        
        # 2. Token参数
        logger.info(f"\n📋 2. Token参数")
        logger.info("-" * 60)
        
        token_data = load_current_tokens()
        access_token = token_data.get('access_token', '')
        refresh_token = token_data.get('refresh_token', '')
        access_token_expire = token_data.get('access_token_expire_in', 0)
        granted_scopes = token_data.get('granted_scopes', [])
        
        token_params = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "access_token_expire_in": access_token_expire,
            "granted_scopes": granted_scopes,
            "user_type": token_data.get('user_type', ''),
            "open_id": token_data.get('open_id', '')
        }
        
        current_time = time.time()
        for key, value in token_params.items():
            if key in ["access_token", "refresh_token"]:
                display_value = f"{str(value)[:50]}...{str(value)[-20:]}"
            elif key == "granted_scopes":
                display_value = json.dumps(value, ensure_ascii=False)
            elif key == "open_id":
                display_value = f"{str(value)[:50]}...{str(value)[-10:]}" if len(str(value)) > 60 else str(value)
            else:
                display_value = str(value)
            
            logger.info(f"  {key}: {display_value}")
            logger.info(f"    类型: {type(value).__name__}")
            
            if key == "access_token_expire_in":
                is_valid = value > current_time
                logger.info(f"    状态: {'✅ 有效' if is_valid else '❌ 过期'}")
                if is_valid:
                    remaining = value - current_time
                    days = int(remaining // 86400)
                    hours = int((remaining % 86400) // 3600)
                    logger.info(f"    剩余时间: {days}天 {hours}时")
        
        # 3. API端点参数
        logger.info(f"\n📋 3. API端点参数")
        logger.info("-" * 60)
        
        api_host = config.API_BASE_URL
        api_path = f"/affiliate_creator/{config.APP_VERSION}/affiliate_sharing_links/generate_batch"
        full_url = api_host + api_path
        parsed_url = urlparse(full_url)
        
        endpoint_params = {
            "API_HOST": api_host,
            "API_PATH": api_path,
            "FULL_URL": full_url,
            "SCHEME": parsed_url.scheme,
            "NETLOC": parsed_url.netloc,
            "PATH": parsed_url.path
        }
        
        for key, value in endpoint_params.items():
            logger.info(f"  {key}: {value}")
            logger.info(f"    长度: {len(value)} 字符")
        
        # 4. 请求体参数
        logger.info(f"\n📋 4. 请求体参数")
        logger.info("-" * 60)
        
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
        
        logger.info(f"  完整请求体:")
        logger.info(json.dumps(request_body, indent=4, ensure_ascii=False))
        
        # 分解每个字段
        logger.info(f"\n  字段分解:")
        logger.info(f"    material.material_id: {request_body['material']['material_id']}")
        logger.info(f"      类型: {type(request_body['material']['material_id']).__name__}")
        logger.info(f"      长度: {len(request_body['material']['material_id'])} 字符")
        
        logger.info(f"    material.type: {request_body['material']['type']}")
        logger.info(f"      类型: {type(request_body['material']['type']).__name__}")
        logger.info(f"      值: '{request_body['material']['type']}' (字符串)")
        
        logger.info(f"    material.campaign_url: {request_body['material']['campaign_url']}")
        logger.info(f"      类型: {type(request_body['material']['campaign_url']).__name__}")
        logger.info(f"      长度: {len(request_body['material']['campaign_url'])} 字符")
        
        logger.info(f"    channel: {request_body['channel']}")
        logger.info(f"      类型: {type(request_body['channel']).__name__}")
        logger.info(f"      长度: {len(request_body['channel'])} 字符")
        
        logger.info(f"    tags: {request_body['tags']}")
        logger.info(f"      类型: {type(request_body['tags']).__name__}")
        logger.info(f"      数量: {len(request_body['tags'])} 个")
        for i, tag in enumerate(request_body['tags']):
            logger.info(f"        [{i}]: {tag} (长度: {len(tag)})")
        
        # 压缩后的JSON
        compressed_body = json.dumps(request_body, separators=(',', ':'))
        logger.info(f"\n  压缩后JSON:")
        logger.info(f"    {compressed_body}")
        logger.info(f"    长度: {len(compressed_body)} 字符")
        
        # 5. 签名相关参数
        logger.info(f"\n📋 5. 签名相关参数")
        logger.info("-" * 60)
        
        timestamp = str(int(time.time()))
        
        # Query参数（用于签名）
        query_params = {
            "app_key": config.APP_KEY,
            "timestamp": timestamp
            # 注意：access_token 不参与签名
        }
        
        logger.info(f"  Query参数（签名用）:")
        for key, value in query_params.items():
            logger.info(f"    {key}: {value}")
            logger.info(f"      类型: {type(value).__name__}")
            logger.info(f"      长度: {len(value)} 字符")
        
        # 按字母排序
        sorted_params = sorted(query_params.items())
        logger.info(f"\n  排序后参数:")
        for key, value in sorted_params:
            logger.info(f"    {key}: {value}")
        
        # 拼接成SDK格式
        param_string = "".join([f"{key}{value}" for key, value in sorted_params])
        logger.info(f"\n  SDK格式拼接:")
        logger.info(f"    {param_string}")
        logger.info(f"    长度: {len(param_string)} 字符")
        
        # 完整签名字符串构建
        sign_string = f"{parsed_url.path}{param_string}{compressed_body}"
        wrapped_string = f"{config.APP_SECRET}{sign_string}{config.APP_SECRET}"
        
        logger.info(f"\n  签名字符串构建:")
        logger.info(f"    路径: {parsed_url.path}")
        logger.info(f"    参数串: {param_string}")
        logger.info(f"    请求体: {compressed_body}")
        logger.info(f"    基础串: {sign_string}")
        logger.info(f"    基础串长度: {len(sign_string)} 字符")
        logger.info(f"    包装串长度: {len(wrapped_string)} 字符")
        
        # 6. HTTP请求参数
        logger.info(f"\n📋 6. HTTP请求参数")
        logger.info("-" * 60)
        
        # URL参数
        url_params = {
            'app_key': config.APP_KEY,
            'timestamp': timestamp,
            'sign': 'SIGNATURE_PLACEHOLDER'  # 实际签名会在运行时生成
        }
        
        # 请求头
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'sdk_node/1.0.0',
            'Accept': 'application/json',
            'x-tts-access-token': access_token
        }
        
        logger.info(f"  URL参数:")
        for key, value in url_params.items():
            if key == 'sign':
                logger.info(f"    {key}: [将由SDK生成]")
            else:
                logger.info(f"    {key}: {value}")
                logger.info(f"      长度: {len(value)} 字符")
        
        logger.info(f"\n  请求头:")
        for key, value in headers.items():
            if key == 'x-tts-access-token':
                display_value = f"{value[:50]}...{value[-20:]}"
            else:
                display_value = value
            logger.info(f"    {key}: {display_value}")
            logger.info(f"      长度: {len(value)} 字符")
        
        # 7. 参数总结
        logger.info(f"\n📊 7. 参数总结")
        logger.info("=" * 100)
        
        summary = {
            "配置参数": {
                "APP_KEY": f"{config.APP_KEY} ({len(config.APP_KEY)}字符)",
                "APP_SECRET": f"***SECRET*** ({len(config.APP_SECRET)}字符)",
                "APP_VERSION": config.APP_VERSION,
                "产品ID": config.DEFAULT_PRODUCT_ID,
                "渠道": "OEM1_XIAOMI",
                "标签数量": len(request_body['tags'])
            },
            "Token参数": {
                "ACCESS_TOKEN": f"ROW_*** ({len(access_token)}字符)",
                "过期状态": "✅ 有效" if access_token_expire > current_time else "❌ 过期",
                "权限scope数量": len(granted_scopes),
                "包含affiliate权限": "✅ 是" if any('affiliate' in scope.lower() for scope in granted_scopes) else "❌ 否"
            },
            "API参数": {
                "完整URL": full_url,
                "API版本": config.APP_VERSION,
                "请求方法": "POST",
                "Content-Type": "application/json"
            },
            "请求体参数": {
                "material_id": request_body['material']['material_id'],
                "type": request_body['material']['type'],
                "campaign_url长度": len(request_body['material']['campaign_url']),
                "channel": request_body['channel'],
                "tags数量": len(request_body['tags']),
                "压缩JSON长度": len(compressed_body)
            },
            "签名参数": {
                "timestamp": timestamp,
                "query_string": param_string,
                "基础字符串长度": len(sign_string),
                "包装字符串长度": len(wrapped_string),
                "HMAC密钥": "APP_SECRET"
            }
        }
        
        logger.info("最终参数汇总:")
        for category, params in summary.items():
            logger.info(f"\n  {category}:")
            for key, value in params.items():
                logger.info(f"    {key}: {value}")
        
        # 8. 关键验证点
        logger.info(f"\n✅ 8. 关键验证点")
        logger.info("=" * 100)
        
        validations = [
            ("APP_KEY长度", len(config.APP_KEY) == 13, f"{len(config.APP_KEY)}/13"),
            ("APP_SECRET长度", len(config.APP_SECRET) == 40, f"{len(config.APP_SECRET)}/40"),
            ("API版本正确", config.APP_VERSION == "202501", config.APP_VERSION),
            ("产品ID格式", config.DEFAULT_PRODUCT_ID.isdigit(), "数字格式"),
            ("ACCESS_TOKEN有效", access_token_expire > current_time, "时间检查"),
            ("包含affiliate权限", any('affiliate' in scope.lower() for scope in granted_scopes), "权限检查"),
            ("material.type格式", request_body['material']['type'] == "1", request_body['material']['type']),
            ("请求体可序列化", True, "JSON格式"),
        ]
        
        logger.info("验证结果:")
        all_valid = True
        for check, result, detail in validations:
            status = "✅ 通过" if result else "❌ 失败"
            logger.info(f"  {check}: {status} ({detail})")
            if not result:
                all_valid = False
        
        logger.info(f"\n总体验证: {'✅ 全部通过' if all_valid else '❌ 存在问题'}")
        
        return {
            "config_params": config_params,
            "token_params": token_params,
            "request_body": request_body,
            "summary": summary,
            "all_valid": all_valid
        }
        
    except Exception as e:
        logger.error(f"❌ 参数调试失败: {e}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")
        return None

if __name__ == "__main__":
    logger.info("🚀 开始SDK参数详细调试")
    result = debug_sdk_parameters()
    
    if result:
        logger.info(f"\n🎉 参数调试完成!")
        logger.info(f"📋 结论: {'所有参数都正确' if result['all_valid'] else '参数存在问题'}")
    else:
        logger.error(f"\n❌ 参数调试失败!")
    
    logger.info(f"\n💡 如果所有参数都正确但API仍然失败，问题很可能在于:")
    logger.info(f"  1. TikTok Shop开发者后台权限配置")
    logger.info(f"  2. 账户联盟营销功能未开通")
    logger.info(f"  3. 产品推广权限缺失")
    logger.info(f"  4. 应用审核状态问题")
