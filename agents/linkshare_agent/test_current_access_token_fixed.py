#!/usr/bin/env python3
"""
修复版本：测试当前存储的ACCESS TOKEN能否直接调用Gen Tracking API
修复SDK签名的URL问题
"""

import sys
import logging
import json
import time
from pathlib import Path
from datetime import datetime

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

def check_access_token_validity(token_data):
    """检查ACCESS TOKEN的有效性"""
    current_time = time.time()
    access_token = token_data.get('access_token', '')
    access_token_expire = token_data.get('access_token_expire_in', 0)
    
    logger.info("🔍 ACCESS TOKEN有效性检查:")
    logger.info(f"   Token: {access_token[:50]}...")
    logger.info(f"   长度: {len(access_token)} 字符")
    
    if access_token_expire > current_time:
        remaining = access_token_expire - current_time
        days = int(remaining // 86400)
        hours = int((remaining % 86400) // 3600)
        minutes = int((remaining % 3600) // 60)
        
        logger.info(f"   过期时间: {datetime.fromtimestamp(access_token_expire).strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"   剩余时间: {days}天 {hours}时 {minutes}分")
        logger.info(f"   状态: ✅ 有效")
        return True, access_token
    else:
        logger.info(f"   状态: ❌ 已过期")
        return False, access_token

def test_gen_tracking_api_with_current_token():
    """使用当前ACCESS TOKEN测试Gen Tracking API"""
    logger.info("🚀 开始测试当前ACCESS TOKEN调用Gen Tracking API...")
    
    try:
        # 1. 加载当前token
        token_data = load_current_tokens()
        is_valid, access_token = check_access_token_validity(token_data)
        
        if not is_valid:
            logger.error("❌ ACCESS TOKEN已过期，无法测试")
            return False
        
        logger.info("\n" + "=" * 80)
        logger.info("🔐 使用当前ACCESS TOKEN测试Gen Tracking API:")
        
        # 2. 准备API调用参数
        import requests
        
        # API基本信息
        api_host = "https://open-api.tiktokglobalshop.com"
        api_path = "/affiliate/202407/affiliate_sharing_links/generate_batch"
        full_url = api_host + api_path
        
        # 请求体
        request_body = {
            "channel": config.DEFAULT_CHANNEL,
            "material": {
                "id": config.DEFAULT_PRODUCT_ID,
                "type": "PRODUCT"
            },
            "tags": config.DEFAULT_TAGS
        }
        
        # 🔧 修复：为SDK签名构建正确的请求选项，使用完整URL
        request_option = {
            "uri": full_url,  # 使用完整URL而不是路径
            "qs": {},  # 查询参数为空
            "headers": {
                "Content-Type": "application/json",
                "x-tts-access-token": access_token
            },
            "body": request_body
        }
        
        # 3. 使用SDK签名算法生成签名
        logger.info("🔐 使用SDK签名算法生成签名...")
        logger.info(f"   URI: {request_option['uri']}")
        signature = generate_sign_sdk_style(request_option, config.APP_SECRET)
        logger.info(f"   签名生成成功: {signature[:16]}...")
        
        # 4. 构建完整请求
        headers = {
            "Content-Type": "application/json",
            "x-tts-access-token": access_token,
            "x-tts-sign": signature,
            "x-tts-timestamp": str(int(time.time()))
        }
        
        logger.info("\n📤 发送API请求:")
        logger.info(f"   URL: {full_url}")
        logger.info(f"   Headers: {json.dumps({k: v[:50] + '...' if len(v) > 50 else v for k, v in headers.items()}, indent=6)}")
        logger.info(f"   Body: {json.dumps(request_body, indent=6)}")
        
        # 5. 发送请求
        response = requests.post(
            full_url,
            headers=headers,
            json=request_body,
            timeout=30
        )
        
        # 6. 分析响应
        logger.info(f"\n📥 API响应:")
        logger.info(f"   状态码: {response.status_code}")
        logger.info(f"   响应头: {dict(response.headers)}")
        
        try:
            response_data = response.json()
            logger.info(f"   响应体: {json.dumps(response_data, indent=6, ensure_ascii=False)}")
            
            # 判断调用是否成功
            if response.status_code == 200:
                code = response_data.get('code', -1)
                if code == 0:
                    logger.info("✅ API调用成功！")
                    logger.info("🎉 用户观点验证成功：ACCESS TOKEN可以独立使用！")
                    return True
                else:
                    message = response_data.get('message', '未知错误')
                    logger.error(f"❌ API返回错误: 代码={code}, 消息={message}")
                    
                    # 特别分析106001错误
                    if code == 106001:
                        logger.error("🔍 106001错误分析:")
                        logger.error("   - 这是签名参数无效错误")
                        logger.error("   - 虽然ACCESS TOKEN有效，但签名可能还有问题")
                        logger.error("   - 已使用SDK签名算法，需要进一步调试")
                    
                    return False
            else:
                logger.error(f"❌ HTTP错误: {response.status_code}")
                return False
                
        except json.JSONDecodeError:
            logger.error(f"❌ 响应不是有效的JSON: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ 测试过程中发生错误: {e}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")
        return False

def main():
    """主函数"""
    logger.info("🚀 启动ACCESS TOKEN有效性验证 (修复版本)...")
    logger.info("🎯 验证用户观点: ACCESS TOKEN在有效期内应该可以独立使用")
    logger.info("🔧 修复: SDK签名的URL问题")
    
    try:
        # 测试当前ACCESS TOKEN
        success = test_gen_tracking_api_with_current_token()
        
        logger.info("\n" + "=" * 80)
        logger.info("📋 修复版本测试结论:")
        if success:
            logger.info("✅ 当前ACCESS TOKEN可以正常调用Gen Tracking API")
            logger.info("✅ 用户观点完全正确: ACCESS TOKEN与AUTH_CODE过期无关")
            logger.info("✅ 修复SDK签名URL问题后成功")
        else:
            logger.info("❌ 当前ACCESS TOKEN调用Gen Tracking API仍然失败")
            logger.info("🔍 问题可能在于:")
            logger.info("   1. SDK签名算法的其他细节")
            logger.info("   2. API请求的其他格式问题")
            logger.info("   3. 需要与GitHub最新版本对比")
        
        return 0 if success else 1
        
    except Exception as e:
        logger.error(f"❌ 测试过程中发生错误: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 