#!/usr/bin/env python3
"""
使用正确API端点测试当前ACCESS TOKEN
验证用户观点：ACCESS TOKEN在有效期内应该可以独立使用
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

def test_correct_endpoint():
    """使用正确的API端点测试"""
    logger.info("🚀 使用正确API端点测试Gen Tracking API...")
    
    try:
        # 1. 加载当前token
        token_data = load_current_tokens()
        access_token = token_data.get('access_token', '')
        
        # 2. 准备API调用参数 - 使用正确的端点
        import requests
        
        # ✅ 正确的API端点（从其他测试文件中确认）
        api_host = "https://open-api.tiktokglobalshop.com"
        api_path = "/affiliate_creator/202407/affiliate_sharing_links/generate_batch"
        full_url = api_host + api_path
        
        logger.info(f"🔗 使用正确API端点: {full_url}")
        
        # 请求体
        request_body = {
            "channel": config.DEFAULT_CHANNEL,
            "material": {
                "id": config.DEFAULT_PRODUCT_ID,
                "type": "PRODUCT"
            },
            "tags": config.DEFAULT_TAGS
        }
        
        # 构建签名需要的请求选项
        request_option = {
            "uri": full_url,
            "qs": {},
            "headers": {
                "Content-Type": "application/json",
                "x-tts-access-token": access_token
            },
            "body": request_body
        }
        
        # 3. 使用SDK签名算法生成签名
        logger.info("🔐 使用SDK签名算法生成签名...")
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
        logger.info(f"   Token: {access_token[:50]}...")
        logger.info(f"   Signature: {signature[:16]}...")
        
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
        
        try:
            response_data = response.json()
            logger.info(f"   响应体: {json.dumps(response_data, indent=6, ensure_ascii=False)}")
            
            # 判断调用是否成功
            if response.status_code == 200:
                code = response_data.get('code', -1)
                if code == 0:
                    logger.info("🎉 API调用成功！")
                    logger.info("✅ 用户观点验证成功：ACCESS TOKEN可以独立使用！")
                    logger.info("✅ 问题确实不在AUTH_CODE过期，而在API端点路径！")
                    return True
                else:
                    message = response_data.get('message', '未知错误')
                    logger.error(f"❌ API返回错误: 代码={code}, 消息={message}")
                    
                    # 分析错误
                    if code == 106001:
                        logger.error("🔍 106001错误分析:")
                        logger.error("   - 签名参数无效错误")
                        logger.error("   - 使用了正确端点和SDK签名，可能是其他细节问题")
                    elif code == 36009009:
                        logger.error("🔍 36009009错误分析:")
                        logger.error("   - 路径无效错误")
                        logger.error("   - 可能端点路径仍有问题")
                    
                    return False
            else:
                logger.error(f"❌ HTTP错误: {response.status_code}")
                if response.status_code == 404:
                    logger.error("   - 404错误说明端点路径不正确")
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
    logger.info("🚀 启动正确端点测试...")
    logger.info("🎯 验证用户观点: ACCESS TOKEN在有效期内应该可以独立使用")
    logger.info("🔧 修复: 使用正确的API端点路径")
    
    try:
        success = test_correct_endpoint()
        
        logger.info("\n" + "=" * 80)
        logger.info("📋 最终结论:")
        if success:
            logger.info("✅ 用户观点完全正确！")
            logger.info("✅ ACCESS TOKEN确实可以独立使用，与AUTH_CODE过期无关")
            logger.info("✅ 问题在于API端点路径错误")
            logger.info("✅ SDK签名算法工作正常")
        else:
            logger.info("❌ 仍有问题需要解决")
            logger.info("🔍 可能需要进一步调试:")
            logger.info("   1. 检查SDK版本或API版本")
            logger.info("   2. 对比GitHub最新版本的实现")
            logger.info("   3. 检查其他请求参数")
        
        return 0 if success else 1
        
    except Exception as e:
        logger.error(f"❌ 测试过程中发生错误: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 