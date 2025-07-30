#!/usr/bin/env python3
"""
简单的 Gen Tracking Link 测试
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

def test_simple_link():
    """测试简单的 gen tracking link 功能"""
    logger.info("🔗 开始测试简单的 gen tracking link 功能...")
    
    try:
        # 1. 获取有效的 token
        token_manager = TokenManager()
        access_token = token_manager.get_valid_token()
        logger.info(f"✅ 获取到有效 token: {access_token[:30]}...")
        
        # 2. 创建链接生成器
        link_generator = LinkGenerator()
        
        # 3. 生成联盟链接
        response = link_generator.generate_affiliate_link(
            product_id="1731493745807886173",
            channel="OEM3_OPPO",
            tags=config.DEFAULT_TAGS
        )
        
        # 4. 检查结果
        if response.get('code') == 0:
            logger.info("✅ Gen tracking link 测试成功!")
            
            data = response.get('data', {})
            links = data.get('affiliate_sharing_links', [])
            
            logger.info(f"📊 生成了 {len(links)} 个链接:")
            for i, link in enumerate(links, 1):
                logger.info(f"   {i}. 标签: {link.get('tag')}")
                logger.info(f"      链接: {link.get('affiliate_sharing_link')}")
                
            return True
        else:
            logger.error(f"❌ Gen tracking link 测试失败: {response.get('message')}")
            return False
            
    except Exception as e:
        logger.error(f"❌ 测试过程中发生错误: {e}")
        return False

def main():
    """主函数"""
    logger.info("🚀 启动简单的 gen tracking link 测试...")
    
    success = test_simple_link()
    
    if success:
        logger.info("🎉 测试完成!")
        return 0
    else:
        logger.error("❌ 测试失败!")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 