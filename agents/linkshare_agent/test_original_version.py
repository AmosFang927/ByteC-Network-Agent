#!/usr/bin/env python3
"""
测试原始版本的 Gen Tracking Link 功能
"""

import sys
import logging
from pathlib import Path
from agents.linkshare_agent import config

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.linkshare_agent.link_generator import LinkGenerator
from agents.linkshare_agent.token_manager import TokenManager

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_original_version():
    """测试原始版本的 gen tracking link 功能"""
    logger.info("🔗 开始测试原始版本的 gen tracking link 功能...")
    
    try:
        # 1. 检查原始token信息
        token_manager = TokenManager()
        token_info = token_manager.get_token_info()
        
        logger.info("📋 原始版本 Token 信息:")
        for key, value in token_info.items():
            if key in ['access_token', 'refresh_token']:
                logger.info(f"   {key}: {value[:30]}..." if value else f"   {key}: 未设置")
            else:
                logger.info(f"   {key}: {value}")
        
        # 2. 获取有效的 token
        access_token = token_manager.get_valid_token()
        logger.info(f"✅ 获取到有效 token: {access_token[:30]}...")
        
        # 3. 创建链接生成器
        link_generator = LinkGenerator()
        
        # 4. 生成联盟链接
        logger.info("🚀 开始生成联盟链接...")
        response = link_generator.generate_affiliate_link(
            product_id="1731493745807886173",
            channel="OEM3_OPPO",
            tags=config.DEFAULT_TAGS
        )
        
        # 5. 检查结果
        if response.get('code') == 0:
            logger.info("✅ 原始版本 Gen tracking link 测试成功!")
            
            data = response.get('data', {})
            links = data.get('affiliate_sharing_links', [])
            
            logger.info(f"📊 生成了 {len(links)} 个链接:")
            for i, link in enumerate(links, 1):
                logger.info(f"   {i}. 标签: {link.get('tag')}")
                logger.info(f"      链接: {link.get('affiliate_sharing_link')}")
                
            return True
        else:
            logger.error(f"❌ 原始版本 Gen tracking link 测试失败: {response.get('message')}")
            logger.error(f"   错误代码: {response.get('code')}")
            return False
            
    except Exception as e:
        logger.error(f"❌ 测试过程中发生错误: {e}")
        return False

def main():
    """主函数"""
    logger.info("🚀 启动原始版本测试...")
    
    success = test_original_version()
    
    if success:
        logger.info("🎉 测试完成!")
        return 0
    else:
        logger.error("❌ 测试失败!")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 