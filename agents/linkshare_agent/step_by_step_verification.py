#!/usr/bin/env python3
"""
Gen Tracking Link 每个步骤的详细验证
逐步验证每个环节，详细列印所有参数并汇总
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

def step_1_verify_configuration():
    """步骤1: 验证基础配置"""
    logger.info("🔧 步骤1: 验证基础配置")
    logger.info("=" * 80)
    
    config_items = {
        "APP_KEY": config.APP_KEY,
        "APP_SECRET": config.APP_SECRET,
        "APP_VERSION": config.APP_VERSION,
        "API_BASE_URL": config.API_BASE_URL,
        "DEFAULT_PRODUCT_ID": config.DEFAULT_PRODUCT_ID,
        "DEFAULT_CHANNEL": config.DEFAULT_CHANNEL,
        "DEFAULT_TAGS": config.DEFAULT_TAGS,
        "AUTH_BASE_URL": config.AUTH_BASE_URL,
        "TOKEN_GET_URL": config.TOKEN_GET_URL,
        "TOKEN_REFRESH_URL": config.TOKEN_REFRESH_URL,
        "LINK_GENERATE_URL": config.LINK_GENERATE_URL
    }
    
    logger.info("基础配置验证:")
    validation_results = {}
    
    for key, value in config_items.items():
        if key == "APP_SECRET":
            display_value = f"{value[:10]}...{value[-10:]}"
        elif key in ["DEFAULT_TAGS"]:
            display_value = json.dumps(value, ensure_ascii=False)
        else:
            display_value = str(value)
            
        logger.info(f"  {key}: {display_value}")
        
        # 验证逻辑
        if not value:
            validation_results[key] = "❌ 空值"
        elif key == "APP_KEY" and len(value) != 13:
            validation_results[key] = f"❌ 长度错误 ({len(value)} != 13)"
        elif key == "APP_SECRET" and len(value) != 40:
            validation_results[key] = f"❌ 长度错误 ({len(value)} != 40)"
        elif key == "APP_VERSION" and value != "202501":
            validation_results[key] = f"❌ 版本错误 ({value} != 202501)"
        elif key == "DEFAULT_PRODUCT_ID" and not value.isdigit():
            validation_results[key] = f"❌ 格式错误 (非数字)"
        else:
            validation_results[key] = "✅ 正确"
    
    logger.info("\n配置验证结果:")
    all_valid = True
    for key, result in validation_results.items():
        logger.info(f"  {key}: {result}")
        if "❌" in result:
            all_valid = False
    
    return {
        "step": "配置验证",
        "success": all_valid,
        "details": validation_results,
        "config": config_items
    }

def step_2_verify_tokens():
    """步骤2: 验证Token状态"""
    logger.info("\n🔐 步骤2: 验证Token状态")
    logger.info("=" * 80)
    
    try:
        token_data = load_current_tokens()
        current_time = time.time()
        
        # 提取token信息
        access_token = token_data.get('access_token', '')
        refresh_token = token_data.get('refresh_token', '')
        access_token_expire = token_data.get('access_token_expire_in', 0)
        refresh_token_expire = token_data.get('refresh_token_expire_in', 0)
        granted_scopes = token_data.get('granted_scopes', [])
        user_type = token_data.get('user_type', '')
        open_id = token_data.get('open_id', '')
        
        logger.info("Token详细信息:")
        logger.info(f"  ACCESS_TOKEN: {access_token[:50]}...{access_token[-20:]}")
        logger.info(f"  ACCESS_TOKEN_LENGTH: {len(access_token)} 字符")
        logger.info(f"  ACCESS_TOKEN_EXPIRE: {access_token_expire}")
        logger.info(f"  ACCESS_TOKEN_VALID: {'✅ 有效' if access_token_expire > current_time else '❌ 过期'}")
        
        if access_token_expire > current_time:
            remaining = access_token_expire - current_time
            days = int(remaining // 86400)
            hours = int((remaining % 86400) // 3600)
            minutes = int((remaining % 3600) // 60)
            logger.info(f"  ACCESS_TOKEN_REMAINING: {days}天 {hours}时 {minutes}分")
        
        logger.info(f"  REFRESH_TOKEN: {refresh_token[:50]}...{refresh_token[-20:]}")
        logger.info(f"  REFRESH_TOKEN_LENGTH: {len(refresh_token)} 字符")
        logger.info(f"  REFRESH_TOKEN_EXPIRE: {refresh_token_expire}")
        logger.info(f"  REFRESH_TOKEN_VALID: {'✅ 有效' if refresh_token_expire > current_time else '❌ 过期'}")
        
        logger.info(f"  GRANTED_SCOPES: {granted_scopes}")
        logger.info(f"  USER_TYPE: {user_type}")
        logger.info(f"  OPEN_ID: {open_id[:50]}...{open_id[-10:] if len(open_id) > 10 else open_id}")
        
        # Token验证
        token_validation = {
            "access_token_format": "✅ 正确" if access_token.startswith('ROW_') else "❌ 格式错误",
            "access_token_length": "✅ 正确" if len(access_token) > 100 else "❌ 长度异常",
            "access_token_expiry": "✅ 有效" if access_token_expire > current_time else "❌ 已过期",
            "refresh_token_format": "✅ 正确" if refresh_token.startswith('ROW_') else "❌ 格式错误",
            "granted_scopes_present": "✅ 有权限" if granted_scopes else "❌ 无权限",
            "affiliate_scope": "✅ 包含" if any('affiliate' in scope.lower() for scope in granted_scopes) else "❌ 缺失"
        }
        
        logger.info("\nToken验证结果:")
        token_valid = True
        for key, result in token_validation.items():
            logger.info(f"  {key}: {result}")
            if "❌" in result:
                token_valid = False
        
        return {
            "step": "Token验证",
            "success": token_valid,
            "details": token_validation,
            "token_info": {
                "access_token": access_token,
                "access_token_expire": access_token_expire,
                "granted_scopes": granted_scopes,
                "user_type": user_type
            }
        }
        
    except Exception as e:
        logger.error(f"Token验证失败: {e}")
        return {
            "step": "Token验证",
            "success": False,
            "details": {"error": str(e)},
            "token_info": {}
        }

def step_3_verify_api_endpoint():
    """步骤3: 验证API端点"""
    logger.info("\n🔗 步骤3: 验证API端点")
    logger.info("=" * 80)
    
    # 构建API端点
    api_host = config.API_BASE_URL
    api_path = f"/affiliate_creator/{config.APP_VERSION}/affiliate_sharing_links/generate_batch"
    full_url = api_host + api_path
    
    logger.info("API端点构建:")
    logger.info(f"  API_HOST: {api_host}")
    logger.info(f"  API_PATH: {api_path}")
    logger.info(f"  FULL_URL: {full_url}")
    logger.info(f"  URL_LENGTH: {len(full_url)} 字符")
    
    # 验证端点可达性
    import requests
    
    try:
        # 发送OPTIONS请求测试端点是否存在
        logger.info("\n测试API端点可达性:")
        response = requests.options(full_url, timeout=10)
        logger.info(f"  OPTIONS响应码: {response.status_code}")
        logger.info(f"  允许的方法: {response.headers.get('Allow', 'N/A')}")
        
        endpoint_validation = {
            "url_format": "✅ 正确" if full_url.startswith('https://') else "❌ 协议错误",
            "url_length": "✅ 正确" if len(full_url) < 200 else "❌ 过长",
            "endpoint_reachable": "✅ 可达" if response.status_code in [200, 405, 404] else "❌ 不可达"
        }
        
        logger.info("\nAPI端点验证结果:")
        endpoint_valid = True
        for key, result in endpoint_validation.items():
            logger.info(f"  {key}: {result}")
            if "❌" in result:
                endpoint_valid = False
        
        return {
            "step": "API端点验证",
            "success": endpoint_valid,
            "details": endpoint_validation,
            "endpoint_info": {
                "full_url": full_url,
                "options_status": response.status_code
            }
        }
        
    except Exception as e:
        logger.error(f"API端点测试失败: {e}")
        return {
            "step": "API端点验证", 
            "success": False,
            "details": {"error": str(e)},
            "endpoint_info": {"full_url": full_url}
        }

def step_4_verify_request_body():
    """步骤4: 验证请求体构建"""
    logger.info("\n📤 步骤4: 验证请求体构建")
    logger.info("=" * 80)
    
    # 构建标准请求体
    request_body = {
        "channel": config.DEFAULT_CHANNEL,
        "material": {
            "id": config.DEFAULT_PRODUCT_ID,
            "type": "PRODUCT"
        },
        "tags": config.DEFAULT_TAGS
    }
    
    logger.info("请求体构建:")
    logger.info(json.dumps(request_body, indent=4, ensure_ascii=False))
    
    # 验证请求体
    body_validation = {
        "channel_present": "✅ 存在" if request_body.get('channel') else "❌ 缺失",
        "channel_format": "✅ 正确" if isinstance(request_body.get('channel'), str) else "❌ 格式错误",
        "material_present": "✅ 存在" if request_body.get('material') else "❌ 缺失",
        "material_id_present": "✅ 存在" if request_body.get('material', {}).get('id') else "❌ 缺失",
        "material_id_format": "✅ 正确" if str(request_body.get('material', {}).get('id', '')).isdigit() else "❌ 非数字",
        "material_type_valid": "✅ 正确" if request_body.get('material', {}).get('type') == 'PRODUCT' else "❌ 错误",
        "tags_present": "✅ 存在" if request_body.get('tags') else "❌ 缺失",
        "tags_format": "✅ 正确" if isinstance(request_body.get('tags'), list) else "❌ 非数组",
        "json_serializable": "✅ 可序列化" if json.dumps(request_body) else "❌ 不可序列化"
    }
    
    logger.info("\n请求体验证结果:")
    body_valid = True
    for key, result in body_validation.items():
        logger.info(f"  {key}: {result}")
        if "❌" in result:
            body_valid = False
    
    # 测试不同的请求体变体
    test_bodies = [
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
    
    logger.info("\n测试请求体变体:")
    for variant in test_bodies:
        logger.info(f"  {variant['name']}: {json.dumps(variant['body'], ensure_ascii=False)}")
    
    return {
        "step": "请求体验证",
        "success": body_valid,
        "details": body_validation,
        "request_body": request_body,
        "test_variants": test_bodies
    }

def step_5_verify_signature_generation():
    """步骤5: 验证签名生成"""
    logger.info("\n🔐 步骤5: 验证签名生成")
    logger.info("=" * 80)
    
    try:
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
        
        # 构建签名参数
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
        
        logger.info("签名生成参数:")
        logger.info(f"  URI: {request_option['uri']}")
        logger.info(f"  Query参数: {json.dumps(request_option['qs'], indent=4)}")
        logger.info(f"  Body: {json.dumps(request_option['body'], indent=4, ensure_ascii=False)}")
        logger.info(f"  Headers: {json.dumps(request_option['headers'], indent=4)}")
        logger.info(f"  Timestamp: {timestamp}")
        
        # 生成签名
        signature = generate_sign_sdk_style(request_option, config.APP_SECRET)
        
        logger.info(f"\n签名生成结果:")
        logger.info(f"  SIGNATURE: {signature}")
        logger.info(f"  SIGNATURE_LENGTH: {len(signature)} 字符")
        logger.info(f"  SIGNATURE_FORMAT: {'✅ 64位十六进制' if len(signature) == 64 and all(c in '0123456789abcdef' for c in signature.lower()) else '❌ 格式错误'}")
        
        # 验证签名生成
        signature_validation = {
            "signature_generated": "✅ 成功" if signature else "❌ 失败",
            "signature_length": "✅ 正确" if len(signature) == 64 else f"❌ 错误长度 ({len(signature)})",
            "signature_format": "✅ 十六进制" if all(c in '0123456789abcdef' for c in signature.lower()) else "❌ 非十六进制",
            "timestamp_valid": "✅ 正确" if timestamp.isdigit() and len(timestamp) == 10 else "❌ 格式错误",
            "app_key_present": "✅ 存在" if config.APP_KEY else "❌ 缺失",
            "app_secret_present": "✅ 存在" if config.APP_SECRET else "❌ 缺失"
        }
        
        logger.info("\n签名验证结果:")
        signature_valid = True
        for key, result in signature_validation.items():
            logger.info(f"  {key}: {result}")
            if "❌" in result:
                signature_valid = False
        
        return {
            "step": "签名生成验证",
            "success": signature_valid,
            "details": signature_validation,
            "signature_info": {
                "signature": signature,
                "timestamp": timestamp,
                "request_option": request_option
            }
        }
        
    except Exception as e:
        logger.error(f"签名生成失败: {e}")
        return {
            "step": "签名生成验证",
            "success": False,
            "details": {"error": str(e)},
            "signature_info": {}
        }

def step_6_verify_http_request():
    """步骤6: 验证HTTP请求构建"""
    logger.info("\n🌐 步骤6: 验证HTTP请求构建")
    logger.info("=" * 80)
    
    try:
        # 使用步骤5的结果
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
        
        signature = generate_sign_sdk_style(request_option, config.APP_SECRET)
        
        # 构建最终HTTP请求参数
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
        
        logger.info("HTTP请求构建:")
        logger.info(f"  METHOD: POST")
        logger.info(f"  URL: {full_url}")
        logger.info(f"  URL_PARAMS: {json.dumps(url_params, indent=4)}")
        logger.info(f"  HEADERS: {json.dumps({k: v[:50] + '...' if len(v) > 50 else v for k, v in headers.items()}, indent=4)}")
        logger.info(f"  BODY: {json.dumps(request_body, indent=4, ensure_ascii=False)}")
        
        # 验证HTTP请求
        http_validation = {
            "method_correct": "✅ 正确" if True else "❌ 错误",  # POST is correct
            "url_valid": "✅ 正确" if full_url.startswith('https://') else "❌ 协议错误",
            "app_key_in_params": "✅ 存在" if url_params.get('app_key') else "❌ 缺失",
            "timestamp_in_params": "✅ 存在" if url_params.get('timestamp') else "❌ 缺失", 
            "signature_in_params": "✅ 存在" if url_params.get('sign') else "❌ 缺失",
            "content_type_header": "✅ 正确" if headers.get('Content-Type') == 'application/json' else "❌ 错误",
            "access_token_header": "✅ 存在" if headers.get('x-tts-access-token') else "❌ 缺失",
            "user_agent_header": "✅ 存在" if headers.get('User-Agent') else "❌ 缺失",
            "body_json_valid": "✅ 有效" if json.dumps(request_body) else "❌ 无效"
        }
        
        logger.info("\nHTTP请求验证结果:")
        http_valid = True
        for key, result in http_validation.items():
            logger.info(f"  {key}: {result}")
            if "❌" in result:
                http_valid = False
        
        return {
            "step": "HTTP请求验证",
            "success": http_valid,
            "details": http_validation,
            "http_info": {
                "url": full_url,
                "params": url_params,
                "headers": headers,
                "body": request_body
            }
        }
        
    except Exception as e:
        logger.error(f"HTTP请求构建失败: {e}")
        return {
            "step": "HTTP请求验证",
            "success": False,
            "details": {"error": str(e)},
            "http_info": {}
        }

def step_7_send_actual_request():
    """步骤7: 发送实际请求"""
    logger.info("\n📡 步骤7: 发送实际请求")
    logger.info("=" * 80)
    
    try:
        # 使用前面步骤的结果
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
        
        logger.info("发送HTTP请求:")
        logger.info(f"  请求时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        import requests
        
        response = requests.post(
            full_url,
            params=url_params,
            headers=headers,
            json=request_body,
            timeout=30
        )
        
        logger.info(f"  响应时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"  HTTP状态码: {response.status_code}")
        logger.info(f"  响应大小: {len(response.content)} 字节")
        
        # 分析响应头
        logger.info(f"\n响应头分析:")
        important_headers = ['Content-Type', 'X-Tt-Logid', 'x-tt-trace-id', 'Server-Timing']
        for header in important_headers:
            value = response.headers.get(header, 'N/A')
            logger.info(f"  {header}: {value}")
        
        # 分析响应体
        try:
            response_data = response.json()
            logger.info(f"\n响应体分析:")
            logger.info(json.dumps(response_data, indent=4, ensure_ascii=False))
            
            code = response_data.get('code')
            message = response_data.get('message', '')
            request_id = response_data.get('request_id', '')
            data = response_data.get('data')
            
            logger.info(f"\n响应解析:")
            logger.info(f"  业务状态码: {code}")
            logger.info(f"  错误信息: {message}")
            logger.info(f"  请求ID: {request_id}")
            logger.info(f"  返回数据: {'有数据' if data else '无数据'}")
            
            # 根据错误码提供详细分析
            error_analysis = {}
            if code == 106001:
                error_analysis = {
                    "error_type": "签名参数无效",
                    "possible_causes": [
                        "签名算法实现错误",
                        "时间戳过期或格式错误", 
                        "APP_KEY或APP_SECRET错误",
                        "参数顺序或编码问题"
                    ]
                }
            elif code == 36009009:
                error_analysis = {
                    "error_type": "路径无效",
                    "possible_causes": [
                        "API版本错误",
                        "端点路径错误",
                        "权限不足"
                    ]
                }
            elif code == 40003:
                error_analysis = {
                    "error_type": "签名错误",
                    "possible_causes": [
                        "签名算法错误",
                        "参数缺失或错误"
                    ]
                }
            elif code == 0:
                error_analysis = {
                    "error_type": "成功",
                    "possible_causes": ["API调用成功"]
                }
            else:
                error_analysis = {
                    "error_type": f"未知错误码: {code}",
                    "possible_causes": ["需要查阅官方文档"]
                }
            
            logger.info(f"\n错误分析:")
            logger.info(f"  错误类型: {error_analysis['error_type']}")
            logger.info(f"  可能原因:")
            for cause in error_analysis['possible_causes']:
                logger.info(f"    - {cause}")
            
            return {
                "step": "实际请求发送",
                "success": response.status_code == 200 and code == 0,
                "details": {
                    "http_status": response.status_code,
                    "business_code": code,
                    "error_message": message,
                    "request_id": request_id,
                    "has_data": bool(data),
                    "error_analysis": error_analysis
                },
                "response_info": {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "data": response_data
                }
            }
            
        except json.JSONDecodeError:
            logger.error(f"响应不是有效JSON: {response.text}")
            return {
                "step": "实际请求发送",
                "success": False,
                "details": {
                    "http_status": response.status_code,
                    "error": "响应不是有效JSON",
                    "response_text": response.text
                },
                "response_info": {}
            }
            
    except Exception as e:
        logger.error(f"发送请求失败: {e}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")
        return {
            "step": "实际请求发送",
            "success": False,
            "details": {"error": str(e)},
            "response_info": {}
        }

def generate_comprehensive_summary(step_results):
    """生成综合总结"""
    logger.info("\n" + "=" * 100)
    logger.info("📊 综合总结报告")
    logger.info("=" * 100)
    
    # 步骤成功率统计
    total_steps = len(step_results)
    successful_steps = sum(1 for result in step_results if result['success'])
    
    logger.info(f"\n总体统计:")
    logger.info(f"  总步骤数: {total_steps}")
    logger.info(f"  成功步骤: {successful_steps}")
    logger.info(f"  失败步骤: {total_steps - successful_steps}")
    logger.info(f"  成功率: {(successful_steps / total_steps * 100):.1f}%")
    
    # 各步骤详情
    logger.info(f"\n各步骤详情:")
    for i, result in enumerate(step_results, 1):
        status = "✅ 成功" if result['success'] else "❌ 失败"
        logger.info(f"  步骤{i} - {result['step']}: {status}")
    
    # 问题分析
    failed_steps = [result for result in step_results if not result['success']]
    if failed_steps:
        logger.info(f"\n问题分析:")
        for result in failed_steps:
            logger.info(f"  {result['step']}:")
            for key, value in result['details'].items():
                if isinstance(value, str) and "❌" in value:
                    logger.info(f"    - {key}: {value}")
    
    # 最终建议
    logger.info(f"\n最终建议:")
    if successful_steps == total_steps:
        logger.info("  ✅ 所有步骤都成功，API调用应该正常工作")
    elif successful_steps >= total_steps - 1:
        logger.info("  🔍 只有最后一步失败，问题可能在权限或业务层面")
        logger.info("  建议检查:")
        logger.info("    - ACCESS TOKEN的权限scope")
        logger.info("    - 账户是否开通联盟营销功能")
        logger.info("    - 产品是否有推广权限")
    else:
        logger.info("  ❌ 存在多个问题，需要逐一解决")
        logger.info("  建议优先解决配置和Token相关问题")
    
    return {
        "total_steps": total_steps,
        "successful_steps": successful_steps,
        "success_rate": successful_steps / total_steps * 100,
        "failed_steps": [r['step'] for r in failed_steps],
        "overall_success": successful_steps == total_steps
    }

def main():
    """主函数"""
    logger.info("🚀 开始Gen Tracking Link完整步骤验证...")
    logger.info("🎯 目标: 逐步验证每个环节，找出问题所在")
    
    try:
        step_results = []
        
        # 执行各个验证步骤
        step_results.append(step_1_verify_configuration())
        step_results.append(step_2_verify_tokens())
        step_results.append(step_3_verify_api_endpoint())
        step_results.append(step_4_verify_request_body())
        step_results.append(step_5_verify_signature_generation())
        step_results.append(step_6_verify_http_request())
        step_results.append(step_7_send_actual_request())
        
        # 生成综合总结
        summary = generate_comprehensive_summary(step_results)
        
        logger.info("\n🎉 完整步骤验证完成!")
        return 0 if summary['overall_success'] else 1
        
    except Exception as e:
        logger.error(f"❌ 验证过程中发生错误: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 