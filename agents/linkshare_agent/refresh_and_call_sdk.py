#!/usr/bin/env python3
"""
使用refresh token获取新的access token，然后调用SDK生成tracking link
"""

import sys
import json
import logging
import subprocess
import time
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
    except:
        return None

def refresh_access_token():
    """使用refresh token获取新的access token"""
    print("🔄 尝试使用refresh token刷新access token...")
    
    # 加载当前token
    tokens = load_tokens()
    if not tokens or 'refresh_token' not in tokens:
        print("❌ 没有找到refresh token")
        return None
    
    refresh_token = tokens['refresh_token']
    print(f"📋 使用refresh token: {refresh_token[:50]}...")
    
    try:
        auth = TikTokAuth()
        new_tokens = auth.refresh_access_token(refresh_token)
        
        new_access_token = new_tokens.get('access_token')
        print(f"✅ 新的 Access Token 获取成功: {new_access_token[:50]}...")
        return new_access_token
        
    except Exception as e:
        print(f"❌ 刷新 Access Token 失败: {e}")
        return None

def try_current_access_token():
    """尝试使用当前的access token"""
    print("🔍 尝试使用当前存储的access token...")
    
    tokens = load_tokens()
    if not tokens or 'access_token' not in tokens:
        print("❌ 没有找到当前的access token")
        return None
    
    access_token = tokens['access_token']
    print(f"📋 当前access token: {access_token[:50]}...")
    
    # 检查过期时间
    current_time = int(time.time())
    expires_at = tokens.get('expires_at', 0)
    
    if current_time > expires_at:
        print(f"⚠️ Token已过期 (当前时间: {current_time}, 过期时间: {expires_at})")
        return None
    else:
        print(f"✅ Token仍在有效期内 (过期时间: {expires_at})")
        return access_token

def call_sdk_with_token(access_token):
    """使用指定的access token调用SDK"""
    print(f"🚀 使用Token调用SDK: {access_token[:50]}...")
    
    # 更新simple_test.js中的access token
    simple_test_path = Path(__file__).parent / "nodejs_sdk" / "simple_test.js"
    
    try:
        # 读取文件
        with open(simple_test_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换access token
        import re
        pattern = r'const ACCESS_TOKEN = "[^"]*";'
        replacement = f'const ACCESS_TOKEN = "{access_token}";'
        new_content = re.sub(pattern, replacement, content)
        
        # 写回文件
        with open(simple_test_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✅ 已更新 simple_test.js 中的 access token")
        
        # 调用Node.js SDK
        nodejs_sdk_dir = Path(__file__).parent / "nodejs_sdk"
        
        print("📡 调用 Node.js SDK...")
        result = subprocess.run(
            ["node", "simple_test.js"],
            cwd=nodejs_sdk_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print("📤 SDK调用结果:")
        print("=" * 60)
        print("STDOUT:")
        print(result.stdout)
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        print("=" * 60)
        print(f"返回码: {result.returncode}")
        
        # 分析结果
        if "✅" in result.stdout and "成功" in result.stdout:
            print("\n🎉 SDK调用看起来成功了！")
            return True
        elif "401" in result.stdout:
            print("\n⚠️ 收到401错误，token可能无效")
            return False
        else:
            print("\n🤔 SDK调用完成，请查看上面的输出结果")
            return result.returncode == 0
        
    except Exception as e:
        print(f"❌ SDK调用失败: {e}")
        return False

def main():
    """主函数"""
    setup_logging()
    
    print("🎯 刷新Token并调用SDK生成Tracking Link")
    print("=" * 60)
    
    # 策略1: 尝试使用当前的access token
    access_token = try_current_access_token()
    
    # 策略2: 如果当前token无效，尝试refresh
    if not access_token:
        access_token = refresh_access_token()
    
    if not access_token:
        print("💥 无法获取有效的access token")
        print("🔧 建议：需要重新获取新的AUTH_CODE来重新授权")
        return False
    
    # 使用token调用SDK
    success = call_sdk_with_token(access_token)
    
    if success:
        print("\n🎉 程序执行成功！")
        print("✅ 已成功调用SDK生成Tracking Link")
    else:
        print("\n❌ 程序执行失败")
        print("💡 可能需要重新获取授权")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)