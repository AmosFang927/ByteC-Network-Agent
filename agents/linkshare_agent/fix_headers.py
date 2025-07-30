#!/usr/bin/env python3
"""
修正HTTP请求头以符合官方文档和SDK标准
根据官方SDK源码中的标准设置
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

def analyze_headers_difference():
    """分析当前请求头与官方文档的差异"""
    logger.info("🔍 分析HTTP请求头与官方文档的差异")
    logger.info("=" * 80)
    
    # 当前使用的请求头
    current_headers = {
        "Content-Type": "application/json",
        "User-Agent": "sdk_node/1.0.0",
        "Accept": "application/json",
        "x-tts-access-token": "ROW_*** (122字符)"
    }
    
    # 根据官方SDK源码的标准请求头 (create-trans-request-options.ts 第46-51行)
    official_sdk_headers = {
        "Content-Type": "application/json",
        "User-Agent": "sdk_node/1.0.0",
        # x-tts-access-token 在SDK中是通过参数传入
    }
    
    logger.info("📋 请求头对比:")
    logger.info(f"当前使用的请求头:")
    for key, value in current_headers.items():
        logger.info(f"  {key}: {value}")
    
    logger.info(f"\n官方SDK标准请求头:")
    for key, value in official_sdk_headers.items():
        logger.info(f"  {key}: {value}")
    
    # 分析差异
    differences = []
    
    # 检查是否有多余的Accept头
    if "Accept" in current_headers:
        differences.append({
            "问题": "多余的Accept头",
            "描述": "官方SDK没有设置Accept头",
            "建议": "移除Accept: application/json"
        })
    
    # 检查x-tts-access-token的处理方式
    differences.append({
        "问题": "x-tts-access-token处理",
        "描述": "需要确认官方文档中x-tts-access-token的标准格式",
        "建议": "验证是否应该使用不同的header名称或格式"
    })
    
    logger.info(f"\n🚨 发现的差异:")
    for i, diff in enumerate(differences, 1):
        logger.info(f"{i}. {diff['问题']}")
        logger.info(f"   描述: {diff['描述']}")
        logger.info(f"   建议: {diff['建议']}")
    
    return differences

def create_corrected_headers_test():
    """创建修正后的请求头测试"""
    logger.info(f"\n🔧 创建修正后的请求头测试")
    
    # 获取access token
    token_manager = TokenManager()
    token_data = token_manager.get_current_token()
    
    if not token_data or not token_data.get('access_token'):
        logger.error("❌ 无法获取access token")
        return None
    
    access_token = token_data['access_token']
    
    # 测试不同的请求头组合
    header_variations = {
        "当前方式": {
            "Content-Type": "application/json",
            "User-Agent": "sdk_node/1.0.0",
            "Accept": "application/json",
            "x-tts-access-token": access_token
        },
        "官方SDK标准": {
            "Content-Type": "application/json",
            "User-Agent": "sdk_node/1.0.0",
            "x-tts-access-token": access_token
        },
        "最小化标准": {
            "Content-Type": "application/json",
            "x-tts-access-token": access_token
        },
        "大写变体测试": {
            "Content-Type": "application/json",
            "User-Agent": "sdk_node/1.0.0",
            "X-TTS-Access-Token": access_token  # 尝试大写变体
        },
        "标准访问令牌头": {
            "Content-Type": "application/json",
            "User-Agent": "sdk_node/1.0.0",
            "Authorization": f"Bearer {access_token}"  # 尝试标准Authorization头
        }
    }
    
    # 准备API请求
    request_body = {
        "material": {
            "material_id": config.DEFAULT_PRODUCT_ID,
            "type": "1",
            "campaign_url": f"https://shop.tiktok.com/view/product/{config.DEFAULT_PRODUCT_ID}"
        },
        "channel": config.DEFAULT_CHANNEL,
        "tags": config.DEFAULT_TAGS
    }
    
    results = []
    
    for variation_name, headers in header_variations.items():
        logger.info(f"\n🧪 测试: {variation_name}")
        
        try:
            # 构建请求参数
            timestamp = int(time.time())
            
            # 构建签名用的请求选项
            request_option = {
                'uri': config.LINK_GENERATE_URL,
                'method': 'POST',
                'qs': {
                    'app_key': config.APP_KEY,
                    'timestamp': timestamp
                },
                'body': request_body,
                'headers': {k: v for k, v in headers.items() if k != 'x-tts-access-token' and k != 'X-TTS-Access-Token' and k != 'Authorization'}
            }
            
            # 生成签名
            signature = generate_sign_sdk_style(request_option, config.APP_SECRET)
            
            # 构建完整URL
            url = f"{config.LINK_GENERATE_URL}?app_key={config.APP_KEY}&timestamp={timestamp}&sign={signature}"
            
            logger.info(f"  请求头: {json.dumps({k: v[:20] + '...' if k in ['x-tts-access-token', 'X-TTS-Access-Token', 'Authorization'] else v for k, v in headers.items()}, indent=4)}")
            
            # 发送请求
            response = requests.post(
                url,
                headers=headers,
                json=request_body,
                timeout=30
            )
            
            result = {
                "variation": variation_name,
                "status_code": response.status_code,
                "headers_sent": {k: v[:20] + '...' if k in ['x-tts-access-token', 'X-TTS-Access-Token', 'Authorization'] else v for k, v in headers.items()},
                "success": False,
                "error": None,
                "response_data": None
            }
            
            try:
                response_json = response.json()
                result["response_data"] = response_json
                result["success"] = response.status_code == 200 and response_json.get('code') == 0
                
                if not result["success"]:
                    result["error"] = f"Code: {response_json.get('code', 'N/A')}, Message: {response_json.get('message', 'N/A')}"
                
            except:
                result["error"] = f"HTTP {response.status_code}: {response.text[:200]}"
            
            results.append(result)
            
            # 输出结果
            if result["success"]:
                logger.info(f"  ✅ 成功! 状态码: {result['status_code']}")
            else:
                logger.info(f"  ❌ 失败! 状态码: {result['status_code']}")
                logger.info(f"  错误信息: {result['error']}")
            
        except Exception as e:
            logger.error(f"  ❌ 请求异常: {e}")
            results.append({
                "variation": variation_name,
                "success": False,
                "error": str(e),
                "headers_sent": headers
            })
    
    return results

def summarize_header_findings(results):
    """总结请求头测试结果"""
    logger.info(f"\n📊 请求头测试结果总结")
    logger.info("=" * 80)
    
    successful_variations = [r for r in results if r.get("success")]
    failed_variations = [r for r in results if not r.get("success")]
    
    logger.info(f"✅ 成功的变体: {len(successful_variations)}")
    for result in successful_variations:
        logger.info(f"  - {result['variation']}")
    
    logger.info(f"\n❌ 失败的变体: {len(failed_variations)}")
    for result in failed_variations:
        logger.info(f"  - {result['variation']}: {result.get('error', '未知错误')}")
    
    # 分析错误模式
    error_patterns = {}
    for result in failed_variations:
        error = result.get('error', '')
        if 'Code:' in error:
            code = error.split('Code:')[1].split(',')[0].strip()
            if code not in error_patterns:
                error_patterns[code] = []
            error_patterns[code].append(result['variation'])
    
    if error_patterns:
        logger.info(f"\n�� 错误模式分析:")
        for code, variations in error_patterns.items():
            logger.info(f"  错误代码 {code}:")
            for var in variations:
                logger.info(f"    - {var}")
    
    # 建议
    logger.info(f"\n💡 建议:")
    if successful_variations:
        best_variation = successful_variations[0]
        logger.info(f"  ✅ 推荐使用: {best_variation['variation']}")
        logger.info(f"  请求头格式:")
        for key, value in best_variation['headers_sent'].items():
            logger.info(f"    {key}: {value}")
    else:
        logger.info(f"  ⚠️ 所有请求头变体都失败了")
        logger.info(f"  这表明问题可能不在请求头格式上")
        logger.info(f"  需要检查:")
        logger.info(f"    1. API端点和版本是否正确")
        logger.info(f"    2. Access Token是否有效")
        logger.info(f"    3. 账户权限配置")
        logger.info(f"    4. 产品推广权限")

def recommend_standard_headers():
    """推荐标准请求头配置"""
    logger.info(f"\n📝 推荐的标准请求头配置")
    logger.info("=" * 80)
    
    # 基于官方SDK源码的标准配置
    recommended_headers = {
        "Content-Type": "application/json",
        "User-Agent": "sdk_node/1.0.0",
        "x-tts-access-token": "{access_token}"
    }
    
    logger.info("基于官方SDK源码 (create-trans-request-options.ts) 的标准配置:")
    logger.info(json.dumps(recommended_headers, indent=2))
    
    logger.info(f"\n🔧 代码实现示例:")
    logger.info("""
headers = {
    "Content-Type": "application/json",
    "User-Agent": "sdk_node/1.0.0",
    "x-tts-access-token": access_token
}

# 移除非必要的Accept头
# 确保x-tts-access-token格式正确
""")
    
    return recommended_headers

if __name__ == "__main__":
    logger.info("🔍 开始分析HTTP请求头问题")
    
    # 1. 分析差异
    differences = analyze_headers_difference()
    
    # 2. 测试修正后的请求头
    results = create_corrected_headers_test()
    
    if results:
        # 3. 总结结果
        summarize_header_findings(results)
    
    # 4. 推荐标准配置
    recommend_standard_headers()
    
    logger.info(f"\n🏁 请求头分析完成!")
