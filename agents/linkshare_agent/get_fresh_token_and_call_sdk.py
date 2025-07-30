#!/usr/bin/env python3
"""
获取最新的access token然后调用SDK生成tracking link
"""

import sys
import json
import logging
import subprocess
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

def get_fresh_access_token():
    """获取最新的access token"""
    print("🔄 获取最新的 Access Token...")
    
    try:
        auth = TikTokAuth()
        token_data = auth.get_access_token(config.AUTH_CODE)
        
        access_token = token_data.get('access_token')
        print(f"✅ 新的 Access Token 获取成功: {access_token[:50]}...")
        return access_token
        
    except Exception as e:
        print(f"❌ 获取 Access Token 失败: {e}")
        return None

def call_sdk_with_fresh_token(access_token):
    """使用fresh token调用SDK"""
    print("🚀 使用最新Token调用SDK...")
    
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
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ SDK调用失败: {e}")
        return False

def main():
    """主函数"""
    setup_logging()
    
    print("🎯 获取最新Token并调用SDK生成Tracking Link")
    print("=" * 60)
    
    # 1. 获取最新的access token
    access_token = get_fresh_access_token()
    if not access_token:
        print("💥 无法获取access token，程序终止")
        return False
    
    # 2. 使用最新token调用SDK
    success = call_sdk_with_fresh_token(access_token)
    
    if success:
        print("\n🎉 程序执行成功！")
        print("✅ 已使用最新的access token调用SDK")
        print("✅ Tracking Link生成过程已完成")
    else:
        print("\n❌ 程序执行失败")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)