#!/usr/bin/env python3
"""
测试 SDK 签名功能
"""

import sys
import logging
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.linkshare_agent.sdk_signature import generate_sign_sdk_style
from agents.linkshare_agent import config

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_sdk_signature():
    """测试 SDK 签名功能"""
    logger.info("🔐 开始测试 SDK 签名功能...")
    
    try:
        # 准备测试数据
        request_option = {
            "uri": "https://open-api.tiktokglobalshop.com/affiliate_creator/202501/affiliate_sharing_links/generate_batch",
            "qs": {
                "app_key": config.APP_KEY,
                "timestamp": "1753757098"
            },
            "headers": {
                "Content-Type": "application/json"
            },
            "body": {
                "material": {
                    "id": "1731493745807886173",
                    "type": "1"
                },
                "channel": config.DEFAULT_CHANNEL,
                "tags": config.DEFAULT_TAGS
            }
        }
        
        # 生成签名
        signature = generate_sign_sdk_style(request_option, config.APP_SECRET)
        
        logger.info(f"✅ SDK 签名测试成功!")
        logger.info(f"🔐 生成的签名: {signature}")
        logger.info(f"📊 签名长度: {len(signature)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ SDK 签名测试失败: {e}")
        return False

def main():
    """主函数"""
    logger.info("🚀 启动 SDK 签名测试...")
    
    success = test_sdk_signature()
    
    if success:
        logger.info("🎉 SDK 签名测试完成!")
        return 0
    else:
        logger.error("❌ SDK 签名测试失败!")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 