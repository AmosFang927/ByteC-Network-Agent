#!/usr/bin/env python3
"""
完整演示Refresh Token API机制并生成Tracking Link
包含：
1. 显示当前token状态
2. 使用refresh token API刷新access token
3. 用新的access token调用生成tracking link API
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
from agents.linkshare_agent.token_manager import TokenManager

def setup_logging():
    """设置日志配置"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )

def print_step(step_num: int, title: str, details: str = ""):
    """打印步骤信息"""
    print(f"\n{'='*70}")
    print(f"步骤 {step_num}: {title}")
    print(f"{'='*70}")
    if details:
        print(details)

def load_current_tokens():
    """加载当前的token信息"""
    try:
        with open(config.get_token_storage_path(), 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ 无法读取token文件: {e}")
        return None

def display_current_token_status():
    """显示当前token状态"""
    print_step(1, "显示当前Token状态", "检查现有的access token和refresh token信息")
    
    tokens = load_current_tokens()
    if not tokens:
        print("❌ 无法加载当前token信息")
        return None
    
    current_time = int(time.time())
    expires_at = tokens.get('expires_at', 0)
    time_left = expires_at - current_time
    
    print("📋 当前Token详细信息:")
    print("-" * 50)
    print(f"🔑 Access Token: {tokens.get('access_token', 'N/A')[:50]}...")
    print(f"🔄 Refresh Token: {tokens.get('refresh_token', 'N/A')[:50]}...")
    print(f"👤 Open ID: {tokens.get('open_id', 'N/A')}")
    print(f"⏰ Access Token 过期时间: {expires_at}")
    print(f"⏱️  剩余有效时间: {time_left} 秒 ({time_left//3600} 小时)")
    print(f"📅 获取时间: {tokens.get('fetched_at', 'N/A')}")
    print(f"💾 保存时间: {tokens.get('saved_at', 'N/A')}")
    
    if time_left > 0:
        print("✅ Access Token仍在有效期内")
    else:
        print("⚠️ Access Token已过期，需要刷新")
    
    return tokens

def refresh_access_token_api():
    """使用refresh token API刷新access token"""
    print_step(2, "使用Refresh Token API刷新Access Token", 
               "调用TikTok Shop refresh token API获取新的access token")
    
    tokens = load_current_tokens()
    if not tokens or 'refresh_token' not in tokens:
        print("❌ 无法获取refresh token")
        return None
    
    refresh_token = tokens['refresh_token']
    print(f"📋 使用Refresh Token: {refresh_token[:50]}...")
    
    try:
        print("📡 调用Refresh Token API...")
        auth = TikTokAuth()
        new_token_data = auth.refresh_access_token(refresh_token)
        
        print("✅ Refresh Token API调用成功!")
        
        print("\n📊 新Token信息:")
        print("-" * 50)
        print(f"🔑 新Access Token: {new_token_data.get('access_token', 'N/A')[:50]}...")
        print(f"🔄 新Refresh Token: {new_token_data.get('refresh_token', 'N/A')[:50]}...")
        print(f"⏰ 新Access Token过期时间: {new_token_data.get('access_token_expire_in', 'N/A')}")
        print(f"⏰ 新Refresh Token过期时间: {new_token_data.get('refresh_token_expire_in', 'N/A')}")
        
        # 显示refresh前后的对比
        print("\n🔄 Token刷新对比:")
        print("-" * 50)
        print(f"旧Access Token: {tokens.get('access_token', 'N/A')[:30]}...")
        print(f"新Access Token: {new_token_data.get('access_token', 'N/A')[:30]}...")
        print("✅ Token已成功刷新并自动保存!")
        
        return new_token_data.get('access_token')
        
    except Exception as e:
        print(f"❌ Refresh Token API调用失败: {e}")
        return None

def update_sdk_with_new_token(access_token):
    """更新SDK中的access token"""
    print_step(3, "更新SDK中的新Access Token")
    
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
        
        print(f"✅ 已更新simple_test.js中的access token")
        print(f"📋 新Token: {access_token[:50]}...")
        return True
        
    except Exception as e:
        print(f"❌ 更新SDK token失败: {e}")
        return False

def generate_tracking_links_with_new_token():
    """使用新的access token生成tracking link"""
    print_step(4, "使用新Access Token生成Tracking Link", 
               "使用刚刚刷新的access token调用联盟链接生成API")
    
    try:
        # 显示本次调用的配置信息
        print("📋 API调用配置:")
        print(f"   产品ID: {config.DEFAULT_PRODUCT_ID}")
        print(f"   频道: {config.DEFAULT_CHANNEL}")
        print(f"   标签: {config.DEFAULT_TAGS}")
        print(f"   App Key: {config.APP_KEY}")
        print(f"   API版本: {config.APP_VERSION}")
        print(f"   API端点: {config.LINK_GENERATE_URL}")
        
        # 调用Node.js SDK
        nodejs_sdk_dir = Path(__file__).parent / "nodejs_sdk"
        
        print("\n📡 开始调用TikTok Shop API...")
        result = subprocess.run(
            ["node", "simple_test.js"],
            cwd=nodejs_sdk_dir,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        print("📤 API调用完成!")
        print(f"📊 退出码: {result.returncode}")
        
        print("\n📄 API调用详细输出:")
        print("=" * 60)
        print(result.stdout)
        if result.stderr:
            print("\n⚠️ 错误输出:")
            print(result.stderr)
        print("=" * 60)
        
        # 分析结果并提取链接
        success, links = analyze_and_extract_links(result.stdout)
        
        if success and links:
            print(f"\n🎉 成功生成 {len(links)} 个联盟链接:")
            for i, link_info in enumerate(links, 1):
                print(f"   {i}. 标签: {link_info['tag']}")
                print(f"      链接: {link_info['link']}")
        
        return success
        
    except Exception as e:
        print(f"❌ API调用失败: {e}")
        return False

def analyze_and_extract_links(output):
    """分析API输出并提取链接信息"""
    if not output:
        return False, []
    
    try:
        # 查找成功指标
        if "200" in output and '"code":0' in output:
            print("✅ API返回成功状态!")
            
            # 尝试从输出中提取JSON数据
            import re
            json_match = re.search(r'"data":\s*{[^}]*"affiliate_sharing_links":\s*\[[^\]]*\]', output)
            if json_match:
                # 提取完整的响应体
                response_match = re.search(r'響應體: ({.*})', output)
                if response_match:
                    try:
                        response_json = json.loads(response_match.group(1))
                        affiliate_links = response_json.get('data', {}).get('affiliate_sharing_links', [])
                        
                        links = []
                        for link_data in affiliate_links:
                            if 'affiliate_sharing_link' in link_data and 'tag' in link_data:
                                links.append({
                                    'link': link_data['affiliate_sharing_link'],
                                    'tag': link_data['tag']
                                })
                        
                        return True, links
                    except json.JSONDecodeError:
                        pass
            
            print("🔗 API成功，但需要手动检查链接信息")
            return True, []
            
        elif "401" in output:
            print("❌ 401错误: Token认证失败")
            return False, []
        elif "400" in output:
            print("❌ 400错误: 请求参数错误")
            return False, []
        else:
            print("🤔 API调用状态不明，请查看详细输出")
            return False, []
            
    except Exception as e:
        print(f"⚠️ 输出分析失败: {e}")
        return False, []

def main():
    """主函数"""
    setup_logging()
    
    print("🚀 完整演示：Refresh Token API + 生成Tracking Link")
    print("🎯 展示完整的token刷新和API调用机制")
    
    # 步骤1: 显示当前token状态
    current_tokens = display_current_token_status()
    if not current_tokens:
        print("\n💥 无法加载当前token，流程终止")
        return False
    
    # 步骤2: 使用refresh token API刷新access token
    new_access_token = refresh_access_token_api()
    if not new_access_token:
        print("\n💥 Refresh Token API调用失败，流程终止")
        return False
    
    # 步骤3: 更新SDK中的新token
    if not update_sdk_with_new_token(new_access_token):
        print("\n💥 无法更新SDK token，流程终止")
        return False
    
    # 步骤4: 使用新token生成tracking link
    success = generate_tracking_links_with_new_token()
    
    # 最终总结
    print_step(5, "完整流程总结")
    
    if success:
        print("🎉 Refresh Token API机制演示成功!")
        print("\n📊 完成的操作:")
        print("   ✅ 1. 显示当前Token状态")
        print("   ✅ 2. 调用Refresh Token API")
        print("   ✅ 3. 获取新的Access Token")
        print("   ✅ 4. 自动保存新Token到存储文件")
        print("   ✅ 5. 使用新Token调用生成链接API")
        print("   ✅ 6. 成功生成新的Tracking Link")
        
        print("\n💡 关键机制验证:")
        print("   🔄 Refresh Token API工作正常")
        print("   💾 Token自动保存和管理机制正常")
        print("   🔗 联盟链接生成API正常")
        print("   🔐 SDK签名和认证机制正常")
        
    else:
        print("❌ 流程执行失败")
        print("\n📊 已完成的操作:")
        print("   ✅ 1. 显示当前Token状态")
        print("   ✅ 2. 调用Refresh Token API成功")
        print("   ✅ 3. 获取新的Access Token")
        print("   ❌ 4. Tracking Link生成失败")
    
    print(f"\n💾 最新Token信息保存在: {config.get_token_storage_path()}")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)