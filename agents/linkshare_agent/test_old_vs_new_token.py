#!/usr/bin/env python3
"""
比较旧token和新token的API调用结果
"""

import sys
import logging
import time
import json
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.linkshare_agent.sdk_signature import generate_sign_sdk_style
from agents.linkshare_agent import config
import requests

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_token_api_call(access_token, token_name):
    """测试指定token的API调用"""
    logger.info(f"🔑 测试 {token_name} 的API调用...")
    logger.info(f"   Token: {access_token[:30]}...")
    
    try:
        # 1. 准备请求数据
        request_data = {
            "material": {
                "id": "1731493745807886173",
                "type": "1"
            },
            "channel": config.DEFAULT_CHANNEL,
            "tags": config.DEFAULT_TAGS
        }
        
        # 2. 准备请求参数
        timestamp = str(int(time.time()))
        request_params = {
            "app_key": config.APP_KEY,
            "timestamp": timestamp
        }
        
        # 3. 构建完整 URL
        full_url = f"{config.API_BASE_URL}/affiliate_creator/{config.APP_VERSION}/affiliate_sharing_links/generate_batch"
        
        # 4. 准备请求选项
        request_option = {
            'uri': full_url,
            'qs': request_params,
            'body': request_data,
            'headers': {
                'Content-Type': 'application/json'
            }
        }
        
        # 5. 使用 SDK 生成签名
        signature = generate_sign_sdk_style(request_option, config.APP_SECRET)
        logger.info(f"🔐 生成的签名: {signature[:16]}...")
        
        # 6. 准备最终请求
        url_params = {
            'app_key': config.APP_KEY,
            'timestamp': timestamp,
            'sign': signature
        }
        
        headers = {
            'Content-Type': 'application/json',
            'x-tts-access-token': access_token
        }
        
        # 7. 发送请求
        logger.info("🚀 发送 API 请求...")
        response = requests.post(
            url=full_url,
            params=url_params,
            json=request_data,
            headers=headers,
            timeout=30
        )
        
        logger.info(f"📡 API 响应状态码: {response.status_code}")
        
        # 8. 解析响应
        response_data = response.json()
        code = response_data.get('code')
        message = response_data.get('message', 'Unknown')
        
        logger.info(f"📋 API 响应 - Code: {code}, Message: {message}")
        
        if code == 0:
            logger.info(f"✅ {token_name} 测试成功!")
            
            data = response_data.get('data', {})
            links = data.get('affiliate_sharing_links', [])
            
            logger.info(f"📊 生成了 {len(links)} 个链接:")
            for i, link in enumerate(links, 1):
                logger.info(f"   {i}. 标签: {link.get('tag')}")
                logger.info(f"      链接: {link.get('affiliate_sharing_link')}")
                
            return True
        else:
            logger.error(f"❌ {token_name} 测试失败: Code {code}, {message}")
            return False
            
    except Exception as e:
        logger.error(f"❌ {token_name} 测试过程中发生错误: {e}")
        return False

def compare_tokens():
    """比较旧token和新token的API调用结果"""
    logger.info("🔍 开始比较旧token和新token的API调用结果...")
    
    try:
        # 1. 读取当前token
        token_file = Path('agents/linkshare_agent/tokens.conf')
        with open(token_file, 'r') as f:
            current_tokens = json.load(f)
        
        current_access_token = current_tokens.get('access_token', '')
        
        # 2. 读取备份token
        backup_file = token_file.with_suffix('.conf.backup')
        if not backup_file.exists():
            logger.error("❌ 未找到备份文件")
            return False
        
        with open(backup_file, 'r') as f:
            backup_tokens = json.load(f)
        
        backup_access_token = backup_tokens.get('access_token', '')
        
        # 3. 测试旧token (backup)
        logger.info("\n" + "="*60)
        logger.info("🔄 测试旧token (backup)")
        logger.info("="*60)
        
        old_result = test_token_api_call(backup_access_token, "旧token")
        
        # 4. 测试新token (current)
        logger.info("\n" + "="*60)
        logger.info("🆕 测试新token (current)")
        logger.info("="*60)
        
        new_result = test_token_api_call(current_access_token, "新token")
        
        # 5. 比较结果
        logger.info("\n" + "="*60)
        logger.info("📊 比较结果")
        logger.info("="*60)
        
        logger.info(f"旧token结果: {'✅ 成功' if old_result else '❌ 失败'}")
        logger.info(f"新token结果: {'✅ 成功' if new_result else '❌ 失败'}")
        
        if old_result and not new_result:
            logger.warning("⚠️ 问题确认: 旧token可用，新token不可用")
            logger.warning("   这说明refresh token可能导致了权限或状态问题")
        elif not old_result and new_result:
            logger.info("✅ 修复确认: 新token可用，旧token已过期")
        elif old_result and new_result:
            logger.info("✅ 都可用: 两个token都正常工作")
        else:
            logger.error("❌ 都不可用: 两个token都有问题")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 比较过程中发生错误: {e}")
        return False

def main():
    """主函数"""
    logger.info("🚀 启动旧token vs 新token测试...")
    
    success = compare_tokens()
    
    if success:
        logger.info("🎉 测试完成!")
        return 0
    else:
        logger.error("❌ 测试失败!")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 