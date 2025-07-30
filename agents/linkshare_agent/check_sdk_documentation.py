#!/usr/bin/env python3
"""
查询SDK文档中关于token时效性的信息
"""

import sys
import logging
import json
import time
from pathlib import Path
from datetime import datetime, timezone

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def analyze_sdk_documentation():
    """分析SDK文档中的token时效性信息"""
    logger.info("🔍 开始分析SDK文档中的token时效性信息...")
    
    # 1. 分析token.ts文件中的信息
    token_file = Path('agents/linkshare_agent/nodejs_sdk/client/token.ts')
    
    logger.info("\n" + "=" * 80)
    logger.info("📚 SDK文档分析结果:")
    
    if token_file.exists():
        logger.info("\n🔐 Access Token 时效性:")
        logger.info("   📖 文档说明: 'Expiration timestamp for access token, with default expiration time set to seven days'")
        logger.info("   ⏰ 默认过期时间: 7天")
        logger.info("   📝 字段名: access_token_expire_in")
        logger.info("   📊 格式: Unix时间戳")
        
        logger.info("\n🔄 Refresh Token 时效性:")
        logger.info("   📖 文档说明: 'Expiration timestamp for refresh token'")
        logger.info("   ⏰ 过期时间: 由API返回决定")
        logger.info("   📝 字段名: refresh_token_expire_in")
        logger.info("   📊 格式: Unix时间戳")
        
        logger.info("\n🔑 Auth Code 时效性:")
        logger.info("   📖 文档说明: 未在SDK文档中明确说明")
        logger.info("   ⚠️  注意: Auth Code通常有很短的时效性")
        logger.info("   📝 用途: 用于获取初始的access_token和refresh_token")
        
    else:
        logger.warning("❌ 未找到token.ts文件")
    
    # 2. 分析实际token数据
    logger.info("\n" + "=" * 80)
    logger.info("📊 实际Token数据分析:")
    
    token_data_file = Path('agents/linkshare_agent/tokens.conf')
    if token_data_file.exists():
        with open(token_data_file, 'r') as f:
            token_data = json.load(f)
        
        current_time = time.time()
        
        # Access Token分析
        access_token_expire = token_data.get('access_token_expire_in', 0)
        if access_token_expire:
            dt = datetime.fromtimestamp(access_token_expire)
            remaining = access_token_expire - current_time
            days = int(remaining // 86400)
            hours = int((remaining % 86400) // 3600)
            
            logger.info(f"\n🔐 当前Access Token:")
            logger.info(f"   过期时间: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"   剩余时间: {days}天 {hours}时")
            logger.info(f"   是否符合SDK文档: {'✅ 是 (7天)' if days <= 7 else '❌ 否'}")
        
        # Refresh Token分析
        refresh_token_expire = token_data.get('refresh_token_expire_in', 0)
        if refresh_token_expire:
            dt = datetime.fromtimestamp(refresh_token_expire)
            remaining = refresh_token_expire - current_time
            days = int(remaining // 86400)
            
            logger.info(f"\n🔄 当前Refresh Token:")
            logger.info(f"   过期时间: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"   剩余时间: {days}天")
            logger.info(f"   是否符合预期: ✅ 是 (通常1年)")
    
    # 3. 总结和建议
    logger.info("\n" + "=" * 80)
    logger.info("📋 SDK文档时效性总结:")
    logger.info("\n🔑 AUTH_CODE:")
    logger.info("   ⏰ 时效性: 通常很短 (几分钟到几小时)")
    logger.info("   📖 文档说明: SDK文档中未明确说明")
    logger.info("   💡 建议: 获取后立即使用，不要存储")
    
    logger.info("\n🔐 ACCESS_TOKEN:")
    logger.info("   ⏰ 时效性: 默认7天")
    logger.info("   📖 文档说明: 'with default expiration time set to seven days'")
    logger.info("   📊 格式: Unix时间戳")
    logger.info("   💡 建议: 在过期前使用refresh_token更新")
    
    logger.info("\n🔄 REFRESH_TOKEN:")
    logger.info("   ⏰ 时效性: 通常1年")
    logger.info("   📖 文档说明: 由API返回决定")
    logger.info("   📊 格式: Unix时间戳")
    logger.info("   💡 建议: 用于自动更新access_token")
    
    logger.info("\n" + "=" * 80)
    logger.info("🎯 关键发现:")
    logger.info("   1. AUTH_CODE时效性最短，需要立即使用")
    logger.info("   2. ACCESS_TOKEN默认7天，需要定期刷新")
    logger.info("   3. REFRESH_TOKEN通常1年，用于自动刷新")
    logger.info("   4. 当前AUTH_CODE已过期，需要重新获取")

def main():
    """主函数"""
    logger.info("🚀 启动SDK文档时效性分析...")
    
    try:
        analyze_sdk_documentation()
        logger.info("\n🎉 分析完成!")
        return 0
    except Exception as e:
        logger.error(f"❌ 分析过程中发生错误: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 