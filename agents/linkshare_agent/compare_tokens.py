#!/usr/bin/env python3
"""
比较原始token和refresh后的token
"""

import sys
import logging
import json
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.linkshare_agent.token_manager import TokenManager

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def compare_tokens():
    """比较token信息"""
    logger.info("🔍 开始比较token信息...")
    
    try:
        # 1. 读取当前的token文件
        token_file = Path('agents/linkshare_agent/tokens.conf')
        with open(token_file, 'r') as f:
            current_tokens = json.load(f)
        
        logger.info("📋 当前token信息:")
        for key, value in current_tokens.items():
            if key in ['access_token', 'refresh_token']:
                logger.info(f"   {key}: {value[:30]}..." if value else f"   {key}: 未设置")
            else:
                logger.info(f"   {key}: {value}")
        
        # 2. 检查token的权限范围
        granted_scopes = current_tokens.get('granted_scopes', [])
        logger.info(f"\n🔐 当前token权限范围:")
        for scope in granted_scopes:
            logger.info(f"   - {scope}")
        
        # 3. 检查token的类型和状态
        user_type = current_tokens.get('user_type')
        seller_name = current_tokens.get('seller_name')
        open_id = current_tokens.get('open_id', '')
        
        logger.info(f"\n👤 用户信息:")
        logger.info(f"   用户类型: {user_type}")
        logger.info(f"   卖家名称: {seller_name}")
        logger.info(f"   Open ID: {open_id[:30]}..." if open_id else "   Open ID: 未设置")
        
        # 4. 检查token的有效期
        import time
        current_time = int(time.time())
        access_token_expire = current_tokens.get('access_token_expire_in', 0)
        refresh_token_expire = current_tokens.get('refresh_token_expire_in', 0)
        
        logger.info(f"\n⏰ token有效期:")
        logger.info(f"   当前时间: {current_time}")
        logger.info(f"   access_token过期时间: {access_token_expire}")
        logger.info(f"   refresh_token过期时间: {refresh_token_expire}")
        
        if access_token_expire > current_time:
            remaining = access_token_expire - current_time
            logger.info(f"   access_token剩余时间: {remaining}秒 ({remaining//3600}小时)")
        else:
            logger.warning("   ⚠️ access_token已过期!")
        
        # 5. 检查是否有backup文件，对比差异
        backup_file = token_file.with_suffix('.conf.backup')
        if backup_file.exists():
            logger.info(f"\n📦 发现备份文件: {backup_file}")
            with open(backup_file, 'r') as f:
                backup_tokens = json.load(f)
            
            logger.info("🔍 对比backup和当前token:")
            
            # 对比access_token
            current_access = current_tokens.get('access_token', '')
            backup_access = backup_tokens.get('access_token', '')
            
            if current_access != backup_access:
                logger.info("   📝 access_token已更新 (refresh成功)")
                logger.info(f"      旧token: {backup_access[:30]}...")
                logger.info(f"      新token: {current_access[:30]}...")
            else:
                logger.warning("   ⚠️ access_token未更新")
            
            # 对比权限范围
            current_scopes = current_tokens.get('granted_scopes', [])
            backup_scopes = backup_tokens.get('granted_scopes', [])
            
            if current_scopes != backup_scopes:
                logger.warning("   ⚠️ 权限范围发生变化!")
                logger.info(f"      旧权限: {backup_scopes}")
                logger.info(f"      新权限: {current_scopes}")
            else:
                logger.info("   ✅ 权限范围保持一致")
        
        # 6. 使用TokenManager验证token
        token_manager = TokenManager()
        valid_token = token_manager.get_valid_token()
        
        if valid_token == current_tokens.get('access_token'):
            logger.info("\n✅ TokenManager验证: token一致")
        else:
            logger.warning("\n⚠️ TokenManager验证: token不一致!")
        
        # 7. 检查token格式
        access_token = current_tokens.get('access_token', '')
        if access_token.startswith('ROW_'):
            logger.info(f"\n✅ access_token格式正确 (ROW_开头)")
            logger.info(f"   长度: {len(access_token)}")
        else:
            logger.warning(f"\n⚠️ access_token格式可能有问题: {access_token[:10]}...")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 比较过程中发生错误: {e}")
        return False

def main():
    """主函数"""
    logger.info("🚀 启动token比较...")
    
    success = compare_tokens()
    
    if success:
        logger.info("🎉 比较完成!")
        return 0
    else:
        logger.error("❌ 比较失败!")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 