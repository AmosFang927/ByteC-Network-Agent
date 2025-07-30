#!/usr/bin/env python3
"""
尝试使用refresh token获取新的access token
"""

import sys
import json
import logging
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent.parent))

from agents.linkshare_agent import config
from agents.linkshare_agent.auth import TikTokAuth

def setup_logging():
    """设置日志配置"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )

def load_tokens():
    """加载当前的token信息"""
    try:
        with open(config.get_token_storage_path(), 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ 无法读取token文件: {e}")
        return None

def main():
    """主函数"""
    setup_logging()
    
    print("🔄 尝试使用Refresh Token获取新的Access Token")
    print("=" * 60)
    
    # 1. 加载当前tokens
    tokens = load_tokens()
    if not tokens:
        print("💥 无法读取当前token信息")
        return False
    
    print("📋 当前Token信息:")
    print(f"   Access Token: {tokens.get('access_token', 'N/A')[:50]}...")
    print(f"   Refresh Token: {tokens.get('refresh_token', 'N/A')[:50]}...")
    print(f"   Open ID: {tokens.get('open_id', 'N/A')}")
    print(f"   过期时间: {tokens.get('expires_at', 'N/A')}")
    
    refresh_token = tokens.get('refresh_token')
    if not refresh_token:
        print("❌ 没有找到refresh token")
        return False
    
    # 2. 尝试刷新access token
    print("\n🔄 使用refresh token获取新的access token...")
    
    try:
        auth = TikTokAuth()
        new_token_data = auth.refresh_access_token(refresh_token)
        
        print("✅ 新的Access Token获取成功!")
        print(f"🔑 新Access Token: {new_token_data.get('access_token', 'N/A')[:50]}...")
        print(f"🔄 新Refresh Token: {new_token_data.get('refresh_token', 'N/A')[:50]}...")
        print(f"⏰ 过期时间: {new_token_data.get('access_token_expire_in', 'N/A')}")
        
        print("\n📊 Token刷新成功总结:")
        print("-" * 40)
        print(f"✅ 旧Token已失效，新Token已获取")
        print(f"✅ 新Token可用于API调用")
        print(f"✅ Token信息已自动保存到存储文件")
        
        return True
        
    except Exception as e:
        print(f"❌ 刷新access token失败: {e}")
        print("\n💡 可能的原因:")
        print("   1. Refresh token也已过期")
        print("   2. 应用授权被撤销")
        print("   3. 需要重新获取新的AUTH_CODE")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎯 Token刷新成功！现在可以使用新token调用API")
        sys.exit(0)
    else:
        print("\n💥 Token刷新失败！")
        sys.exit(1)