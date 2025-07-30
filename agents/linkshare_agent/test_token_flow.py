#!/usr/bin/env python3
"""
测试 Token 读取和写入流程
"""

import sys
import logging
from pathlib import Path
from agents.linkshare_agent import config

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.linkshare_agent.token_manager import TokenManager
from agents.linkshare_agent.link_generator import LinkGenerator

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_token_flow():
    """测试token的读取和写入流程"""
    logger.info("🔑 开始测试 Token 读取和写入流程...")
    
    try:
        # 1. 创建token管理器
        token_manager = TokenManager()
        
        # 2. 获取当前token信息
        token_info = token_manager.get_token_info()
        logger.info("📋 当前 Token 信息:")
        for key, value in token_info.items():
            if key in ['access_token', 'refresh_token']:
                logger.info(f"   {key}: {value[:30]}..." if value else f"   {key}: 未设置")
            else:
                logger.info(f"   {key}: {value}")
        
        # 3. 获取有效token
        access_token = token_manager.get_valid_token()
        logger.info(f"✅ 获取到有效 token: {access_token[:30]}...")
        
        # 4. 创建链接生成器并测试token使用
        link_generator = LinkGenerator()
        
        # 5. 检查链接生成器是否能正确获取token
        test_token = link_generator.token_manager.get_valid_token()
        logger.info(f"✅ 链接生成器获取到 token: {test_token[:30]}...")
        
        # 6. 验证两个token是否一致
        if access_token == test_token:
            logger.info("✅ Token 一致性验证通过!")
        else:
            logger.error("❌ Token 不一致!")
            return False
        
        # 7. 检查token是否来自最新的配置文件
        import json
        with open('agents/linkshare_agent/tokens.conf', 'r') as f:
            config_data = json.load(f)
            config_token = config_data.get('access_token', '')
            
        if access_token == config_token:
            logger.info("✅ Token 与配置文件一致!")
        else:
            logger.error("❌ Token 与配置文件不一致!")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 测试过程中发生错误: {e}")
        return False

def main():
    """主函数"""
    logger.info("🚀 启动 Token 流程测试...")
    
    success = test_token_flow()
    
    if success:
        logger.info("🎉 Token 流程测试完成!")
        return 0
    else:
        logger.error("❌ Token 流程测试失败!")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 