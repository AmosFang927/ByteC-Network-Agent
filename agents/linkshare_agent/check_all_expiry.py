#!/usr/bin/env python3
"""
检查所有token的过期时间
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

from agents.linkshare_agent import config

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def format_timestamp(timestamp, label=""):
    """格式化时间戳为可读格式"""
    if not timestamp:
        return "未设置"
    
    try:
        dt = datetime.fromtimestamp(timestamp)
        current_time = time.time()
        
        if timestamp > current_time:
            remaining = timestamp - current_time
            days = int(remaining // 86400)
            hours = int((remaining % 86400) // 3600)
            minutes = int((remaining % 3600) // 60)
            
            status = "✅ 有效"
            if remaining < 3600:  # 少于1小时
                status = "⚠️ 即将过期"
            elif remaining < 86400:  # 少于1天
                status = "🟡 即将过期"
                
            return f"{dt.strftime('%Y-%m-%d %H:%M:%S')} ({status} - 剩余 {days}天 {hours}时 {minutes}分)"
        else:
            expired_time = current_time - timestamp
            days = int(expired_time // 86400)
            hours = int((expired_time % 86400) // 3600)
            
            return f"{dt.strftime('%Y-%m-%d %H:%M:%S')} (❌ 已过期 {days}天 {hours}时)"
    except Exception as e:
        return f"解析错误: {e}"

def check_all_expiry():
    """检查所有token的过期时间"""
    logger.info("🔍 开始检查所有token的过期时间...")
    
    current_time = time.time()
    current_dt = datetime.fromtimestamp(current_time)
    
    logger.info(f"📅 当前时间: {current_dt.strftime('%Y-%m-%d %H:%M:%S')} (时间戳: {int(current_time)})")
    logger.info("=" * 80)
    
    # 1. 检查 AUTH_CODE
    logger.info("🔑 AUTH_CODE 信息:")
    auth_code = config.AUTH_CODE
    logger.info(f"   值: {auth_code[:50]}...")
    logger.info(f"   长度: {len(auth_code)} 字符")
    logger.info(f"   格式: {'✅ 正确 (ROW_开头)' if auth_code.startswith('ROW_') else '❌ 格式错误'}")
    logger.info(f"   状态: ❌ 已过期 (无法获取新token，错误码36004004)")
    logger.info(f"   备注: AUTH_CODE通常在获取后短时间内有效，需要重新获取")
    
    logger.info("\n" + "=" * 80)
    
    # 2. 检查当前存储的token
    token_file = Path('agents/linkshare_agent/tokens.conf')
    if token_file.exists():
        logger.info("💾 当前存储的Token信息:")
        
        with open(token_file, 'r') as f:
            token_data = json.load(f)
        
        # Access Token
        access_token = token_data.get('access_token', '')
        access_token_expire = token_data.get('access_token_expire_in', 0)
        expires_at = token_data.get('expires_at', 0)
        fetched_at = token_data.get('fetched_at', 0)
        
        logger.info(f"\n🔐 Access Token:")
        logger.info(f"   值: {access_token[:50]}..." if access_token else "   值: 未设置")
        logger.info(f"   长度: {len(access_token)} 字符" if access_token else "   长度: 0")
        logger.info(f"   格式: {'✅ 正确 (ROW_开头)' if access_token.startswith('ROW_') else '❌ 格式错误'}")
        
        if access_token_expire:
            logger.info(f"   过期时间 (API返回): {format_timestamp(access_token_expire)}")
        if expires_at:
            logger.info(f"   过期时间 (计算值): {format_timestamp(expires_at)}")
        if fetched_at:
            logger.info(f"   获取时间: {format_timestamp(fetched_at)}")
        
        # Refresh Token
        refresh_token = token_data.get('refresh_token', '')
        refresh_token_expire = token_data.get('refresh_token_expire_in', 0)
        
        logger.info(f"\n🔄 Refresh Token:")
        logger.info(f"   值: {refresh_token[:50]}..." if refresh_token else "   值: 未设置")
        logger.info(f"   长度: {len(refresh_token)} 字符" if refresh_token else "   长度: 0")
        logger.info(f"   格式: {'✅ 正确 (ROW_开头)' if refresh_token.startswith('ROW_') else '❌ 格式错误'}")
        
        if refresh_token_expire:
            logger.info(f"   过期时间: {format_timestamp(refresh_token_expire)}")
        
        # 其他信息
        granted_scopes = token_data.get('granted_scopes', [])
        user_type = token_data.get('user_type')
        open_id = token_data.get('open_id', '')
        
        logger.info(f"\n👤 用户信息:")
        logger.info(f"   用户类型: {user_type}")
        logger.info(f"   Open ID: {open_id[:50]}..." if open_id else "   Open ID: 未设置")
        logger.info(f"   权限范围: {granted_scopes}")
        
    else:
        logger.warning("💾 未找到token配置文件")
    
    # 3. 检查备份token
    backup_file = token_file.with_suffix('.conf.backup')
    if backup_file.exists():
        logger.info("\n" + "=" * 80)
        logger.info("📦 备份Token信息:")
        
        with open(backup_file, 'r') as f:
            backup_data = json.load(f)
        
        backup_access = backup_data.get('access_token', '')
        backup_access_expire = backup_data.get('access_token_expire_in', 0)
        backup_refresh = backup_data.get('refresh_token', '')
        backup_refresh_expire = backup_data.get('refresh_token_expire_in', 0)
        
        logger.info(f"   Access Token: {backup_access[:50]}..." if backup_access else "   Access Token: 未设置")
        if backup_access_expire:
            logger.info(f"   Access过期时间: {format_timestamp(backup_access_expire)}")
        
        logger.info(f"   Refresh Token: {backup_refresh[:50]}..." if backup_refresh else "   Refresh Token: 未设置")
        if backup_refresh_expire:
            logger.info(f"   Refresh过期时间: {format_timestamp(backup_refresh_expire)}")
    
    logger.info("\n" + "=" * 80)
    logger.info("📋 总结:")
    logger.info("   🔑 AUTH_CODE: ❌ 已过期，需要重新获取")
    logger.info("   🔐 Access Token: ❌ 无效 (基于过期的AUTH_CODE)")
    logger.info("   🔄 Refresh Token: ❌ 无效 (基于过期的AUTH_CODE)")
    logger.info("\n💡 建议:")
    logger.info("   1. 重新获取新的AUTH_CODE")
    logger.info("   2. 更新config.py中的AUTH_CODE")
    logger.info("   3. 重新获取access_token和refresh_token")
    logger.info("   4. 测试完整的token刷新和API调用流程")

def main():
    """主函数"""
    logger.info("🚀 启动token过期时间检查...")
    
    try:
        check_all_expiry()
        logger.info("\n🎉 检查完成!")
        return 0
    except Exception as e:
        logger.error(f"❌ 检查过程中发生错误: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 