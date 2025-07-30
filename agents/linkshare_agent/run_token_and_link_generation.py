#!/usr/bin/env python3
"""
使用最新的 AUTH_CODE 获取 access token 并生成 tracking link
包含详细的步骤打印和总结
"""

import sys
import logging
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent.parent))

# 导入相关模块
from agents.linkshare_agent import config
from agents.linkshare_agent.auth import TikTokAuth
from agents.linkshare_agent.token_manager import TokenManager
from agents.linkshare_agent.link_generator import LinkGenerator

def setup_logging():
    """设置日志配置"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )

def print_step(step_num: int, title: str, details: str = ""):
    """打印步骤信息"""
    print(f"\n{'='*60}")
    print(f"步骤 {step_num}: {title}")
    print(f"{'='*60}")
    if details:
        print(details)

def print_summary(title: str, data: dict):
    """打印总结信息"""
    print(f"\n🎯 {title}")
    print("-" * 50)
    for key, value in data.items():
        if isinstance(value, str) and len(value) > 50:
            print(f"{key}: {value[:50]}...")
        else:
            print(f"{key}: {value}")

def main():
    """主函数"""
    setup_logging()
    
    print("🚀 开始 TikTok Shop 联盟营销流程")
    print(f"使用的 AUTH_CODE: {config.AUTH_CODE[:20]}...")
    
    # 步骤 1: 初始化认证模块
    print_step(1, "初始化认证模块")
    try:
        auth = TikTokAuth()
        print("✅ TikTokAuth 初始化成功")
        print(f"   App Key: {config.APP_KEY}")
        print(f"   App Version: {config.APP_VERSION}")
        print(f"   API Base URL: {config.API_BASE_URL}")
    except Exception as e:
        print(f"❌ 认证模块初始化失败: {e}")
        return False
    
    # 步骤 2: 获取 Access Token
    print_step(2, "获取新的 Access Token", "使用最新的 AUTH_CODE 获取访问令牌...")
    try:
        print("📡 正在调用 TikTok Shop API...")
        token_data = auth.get_access_token(config.AUTH_CODE)
        print("✅ Access Token 获取成功!")
        
        # 打印 Token 信息总结
        token_summary = {
            "Access Token": token_data.get('access_token', 'N/A')[:30] + "...",
            "Refresh Token": token_data.get('refresh_token', 'N/A')[:30] + "...",
            "Open ID": token_data.get('open_id', 'N/A'),
            "Seller Name": token_data.get('seller_name', 'N/A'),
            "User Type": token_data.get('user_type', 'N/A'),
            "Access Token Expire": token_data.get('access_token_expire_in', 'N/A'),
            "Refresh Token Expire": token_data.get('refresh_token_expire_in', 'N/A'),
            "Granted Scopes": ", ".join(token_data.get('granted_scopes', []))
        }
        print_summary("Token 信息总结", token_summary)
        
    except Exception as e:
        print(f"❌ Access Token 获取失败: {e}")
        return False
    
    # 步骤 3: 初始化 Token 管理器
    print_step(3, "初始化 Token 管理器")
    try:
        token_manager = TokenManager()
        print("✅ TokenManager 初始化成功")
        print(f"   Token 存储路径: {token_manager.token_file}")
        
        # 验证 Token 有效性
        print("🔍 验证 Token 有效性...")
        valid_token = token_manager.get_valid_token()
        print(f"✅ 获取到有效的 Access Token: {valid_token[:30]}...")
        
    except Exception as e:
        print(f"❌ Token 管理器初始化失败: {e}")
        return False
    
    # 步骤 4: 初始化链接生成器
    print_step(4, "初始化联盟链接生成器")
    try:
        link_generator = LinkGenerator()
        print("✅ LinkGenerator 初始化成功")
        print(f"   使用产品 ID: {config.DEFAULT_PRODUCT_ID}")
        print(f"   使用频道: {config.DEFAULT_CHANNEL}")
        print(f"   使用标签: {config.DEFAULT_TAGS}")
        
    except Exception as e:
        print(f"❌ 链接生成器初始化失败: {e}")
        return False
    
    # 步骤 5: 生成 Tracking Link
    print_step(5, "生成联盟 Tracking Link", "使用默认产品和配置生成联盟分享链接...")
    try:
        print("📡 正在调用联盟链接生成 API...")
        link_result = link_generator.generate_affiliate_link(
            product_id=config.DEFAULT_PRODUCT_ID,
            channel=config.DEFAULT_CHANNEL,
            tags=config.DEFAULT_TAGS
        )
        
        if link_result.get('code') == 0:
            print("✅ 联盟链接生成成功!")
            
            # 提取链接数据
            data = link_result.get('data', {})
            affiliate_data = data.get('affiliate_sharing_link_and_qr_code_data', [])
            
            if affiliate_data:
                link_info = affiliate_data[0]
                link_summary = {
                    "产品 ID": link_info.get('product_id', 'N/A'),
                    "联盟链接": link_info.get('affiliate_sharing_link', 'N/A'),
                    "二维码链接": link_info.get('qr_code_link', 'N/A'),
                    "材料类型": link_info.get('material_type', 'N/A'),
                    "频道": config.DEFAULT_CHANNEL,
                    "标签": ", ".join(config.DEFAULT_TAGS)
                }
                print_summary("联盟链接信息总结", link_summary)
            else:
                print("⚠️ 没有返回联盟链接数据")
                
        else:
            print(f"❌ 联盟链接生成失败: {link_result.get('message', '未知错误')}")
            print(f"   错误代码: {link_result.get('code')}")
            return False
            
    except Exception as e:
        print(f"❌ 联盟链接生成过程出错: {e}")
        return False
    
    # 步骤 6: 最终总结
    print_step(6, "流程完成总结")
    print("🎉 所有步骤已成功完成!")
    print("\n📊 完整流程总结:")
    print("   ✅ 1. 使用最新 AUTH_CODE 获取 Access Token")
    print("   ✅ 2. Token 自动保存到本地存储")
    print("   ✅ 3. 验证 Token 有效性")
    print("   ✅ 4. 生成联盟 Tracking Link")
    print("   ✅ 5. 返回完整的联盟链接信息")
    
    print(f"\n💾 Token 信息已保存到: {config.get_token_storage_path()}")
    print("🔗 联盟链接已生成，可用于推广产品")
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎯 程序执行成功!")
        sys.exit(0)
    else:
        print("\n💥 程序执行失败!")
        sys.exit(1)