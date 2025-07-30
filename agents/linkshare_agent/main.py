#!/usr/bin/env python3
"""
TikTok Shop 联盟营销 - 主程序
支持命令行参数生成Tracking Link
"""

import sys
import json
import logging
import subprocess
import time
import argparse
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

def print_step(step_num: int, title: str, details: str = ""):
    """打印步骤信息"""
    print(f"\n{'='*70}")
    print(f"步骤 {step_num}: {title}")
    print(f"{'='*70}")
    if details:
        print(details)

def get_fresh_access_token():
    """使用新的AUTH_CODE获取access token"""
    print_step(1, "使用AUTH_CODE获取Access Token", 
               f"AUTH_CODE: {config.AUTH_CODE[:30]}...")
    
    try:
        auth = TikTokAuth()
        token_data = auth.get_access_token(config.AUTH_CODE)
        
        print("✅ 新的Access Token获取成功!")
        print("\n📊 Token详细信息:")
        print("-" * 50)
        print(f"🔑 Access Token: {token_data.get('access_token', 'N/A')[:50]}...")
        print(f"🔄 Refresh Token: {token_data.get('refresh_token', 'N/A')[:50]}...")
        print(f"👤 Open ID: {token_data.get('open_id', 'N/A')}")
        print(f"🏪 Seller Name: {token_data.get('seller_name', 'N/A')}")
        print(f"👥 User Type: {token_data.get('user_type', 'N/A')}")
        print(f"⏰ Access Token 过期时间: {token_data.get('access_token_expire_in', 'N/A')}")
        print(f"⏰ Refresh Token 过期时间: {token_data.get('refresh_token_expire_in', 'N/A')}")
        print(f"🔐 授权范围: {', '.join(token_data.get('granted_scopes', []))}")
        
        return token_data.get('access_token')
        
    except Exception as e:
        print(f"❌ 获取Access Token失败: {e}")
        return None

def refresh_access_token():
    """使用refresh token API主动刷新access token"""
    print_step(1, "主动调用Refresh Token API", 
               "使用现有refresh token获取新的access token...")
    
    try:
        # 加载当前tokens
        with open(config.get_token_storage_path(), 'r') as f:
            tokens = json.load(f)
        
        refresh_token = tokens.get('refresh_token')
        if not refresh_token:
            print("❌ 没有找到refresh token")
            return None
        
        print(f"📋 使用Refresh Token: {refresh_token[:50]}...")
        
        auth = TikTokAuth()
        new_token_data = auth.refresh_access_token(refresh_token)
        
        print("✅ Refresh Token API调用成功!")
        print("\n📊 新Token详细信息:")
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

def update_sdk_token(access_token):
    """更新SDK中的access token"""
    print_step(2, "更新SDK中的Access Token")
    
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

def update_sdk_parameters(product_id, tags):
    """更新SDK中的产品ID和标签参数"""
    simple_test_path = Path(__file__).parent / "nodejs_sdk" / "simple_test.js"
    
    try:
        # 读取文件
        with open(simple_test_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换产品ID
        import re
        product_pattern = r'"id": "[^"]*"'
        product_replacement = f'"id": "{product_id}"'
        content = re.sub(product_pattern, product_replacement, content)
        
        # 替换campaign URL
        campaign_pattern = r'"campaignUrl": "[^"]*"'
        campaign_replacement = f'"campaignUrl": "https://shop.tiktok.com/view/product/{product_id}"'
        content = re.sub(campaign_pattern, campaign_replacement, content)
        
        # 替换标签
        tags_str = '", "'.join(tags)
        tags_pattern = r'"tags":\s*\[[^\]]*\]'
        tags_replacement = f'"tags": [\n                "{tags_str}"\n            ]'
        content = re.sub(tags_pattern, tags_replacement, content)
        
        # 写回文件
        with open(simple_test_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ 已更新SDK参数")
        print(f"📋 产品ID: {product_id}")
        print(f"🏷️ 标签: {tags}")
        return True
        
    except Exception as e:
        print(f"❌ 更新SDK参数失败: {e}")
        return False

def call_sdk_generate_tracking_link(product_id, tags):
    """调用SDK生成tracking link"""
    print_step(3, "使用SDK生成Tracking Link", 
               "调用Node.js SDK进行联盟链接生成...")
    
    try:
        # 显示配置信息
        print("📋 使用的配置参数:")
        print(f"   产品ID: {product_id}")
        print(f"   频道: {config.DEFAULT_CHANNEL}")
        print(f"   标签: {tags}")
        print(f"   App Key: {config.APP_KEY}")
        print(f"   App Version: {config.APP_VERSION}")
        
        # 调用Node.js SDK
        nodejs_sdk_dir = Path(__file__).parent / "nodejs_sdk"
        
        print("\n📡 开始调用Node.js SDK...")
        result = subprocess.run(
            ["node", "simple_test.js"],
            cwd=nodejs_sdk_dir,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        print("📤 SDK调用完成!")
        
        # 分析结果并提取链接
        success, links = analyze_and_extract_links(result.stdout)
        
        if success and links:
            print_tracking_links_result(links, product_id, tags)
        else:
            print("\n❌ 未能提取到有效的tracking links")
            print("📄 SDK原始输出:")
            print("=" * 60)
            print(result.stdout)
            if result.stderr:
                print("\n⚠️ 错误输出:")
                print(result.stderr)
            print("=" * 60)
        
        return success
        
    except Exception as e:
        print(f"❌ SDK调用失败: {e}")
        return False

def analyze_and_extract_links(output):
    """分析SDK输出并提取链接信息"""
    if not output:
        return False, []
    
    try:
        # 查找成功指标
        if "200" in output and '"code":0' in output:
            print("✅ API返回成功状态!")
            
            # 提取完整的响应体
            import re
            response_match = re.search(r'響應體: ({.*})', output)
            if response_match:
                try:
                    response_json = json.loads(response_match.group(1))
                    affiliate_links = response_json.get('data', {}).get('affiliate_sharing_links', [])
                    
                    links = []
                    for link_data in affiliate_links:
                        if 'affiliate_sharing_link' in link_data and 'tag' in link_data:
                            links.append({
                                'affiliate_sharing_link': link_data['affiliate_sharing_link'],
                                'tag': link_data['tag']
                            })
                    
                    return True, links
                except json.JSONDecodeError as e:
                    print(f"❌ JSON解析失败: {e}")
                    return False, []
            
            print("🔗 API成功，但无法解析链接信息")
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

def print_tracking_links_result(links, product_id, tags):
    """按用户要求的格式打印tracking links结果"""
    print_step(4, "Tracking Links 生成结果")
    
    print(f"🎯 产品ID: {product_id}")
    print(f"🏷️ 请求标签: {tags}")
    print(f"🔗 生成链接数量: {len(links)}")
    
    print("\n" + "="*80)
    print("📊 Generated affiliate links for each sub id:")
    print("="*80)
    
    for i, link_info in enumerate(links, 1):
        tag = link_info['tag']
        full_link = link_info['affiliate_sharing_link']
        
        print(f"\n🔸 Link {i}:")
        print(f"   Tag (Sub ID): {tag}")
        print(f"   ^affiliate_sharing_links -> tracking link: {full_link}")
        print(f"   ^^affiliate_sharing_link -> short tracking link: {full_link}")
        print(f"      (Affiliate short link, domain: www.tiktok.com)")
    
    print("\n" + "="*80)
    print("✅ 所有tracking links生成完成!")
    print("💡 每个链接都可以独立追踪佣金收益")

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='TikTok Shop 联盟营销 Tracking Link 生成器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s --product-id 1731493745807886173
  %(prog)s --product-id 1731493745807886173 --tags L_OEM1_XIAOMI_PUSH_ID L_OEM3_OPPO_PUSH_ID L_OEM2_VIVO_PUSH_ID
  %(prog)s --refresh-token --product-id 1731493745807886173
  %(prog)s --help
        """
    )
    
    parser.add_argument(
        '--product-id',
        type=str,
        default=config.DEFAULT_PRODUCT_ID,
        help=f'产品ID (默认: {config.DEFAULT_PRODUCT_ID})'
    )
    
    parser.add_argument(
        '--tags',
        nargs='+',
        default=["L_OEM1_XIAOMI_PUSH_ID", "L_OEM3_OPPO_PUSH_ID", "L_OEM2_VIVO_PUSH_ID"],
        help='标签列表 (默认: L_OEM1_XIAOMI_PUSH_ID L_OEM3_OPPO_PUSH_ID L_OEM2_VIVO_PUSH_ID)'
    )
    
    parser.add_argument(
        '--refresh-token',
        action='store_true',
        help='主动调用refresh token API，更新access token和refresh token'
    )
    
    return parser.parse_args()

def main():
    """主函数"""
    setup_logging()
    
    # 解析命令行参数
    args = parse_arguments()
    
    print("🚀 TikTok Shop 联盟营销 Tracking Link 生成器")
    print("🎯 开始生成联盟营销链接...")
    
    print(f"\n📋 输入参数:")
    print(f"   产品ID: {args.product_id}")
    print(f"   标签: {args.tags}")
    print(f"   刷新Token: {'是' if args.refresh_token else '否'}")
    
    # 步骤1: 获取access token
    if args.refresh_token:
        # 主动调用refresh token API
        access_token = refresh_access_token()
        if not access_token:
            print("\n💥 Refresh Token失败，流程终止")
            return False
    else:
        # 尝试使用现有token，失败则获取新token
        try:
            from agents.linkshare_agent.token_manager import TokenManager
            token_manager = TokenManager()
            access_token = token_manager.get_valid_token()
            print("✅ 使用现有有效Token")
            print(f"📋 Token: {access_token[:50]}...")
        except:
            access_token = get_fresh_access_token()
            if not access_token:
                print("\n💥 无法获取access token，流程终止")
                return False
    
    # 步骤2: 更新SDK中的token
    if not update_sdk_token(access_token):
        print("\n💥 无法更新SDK token，流程终止")
        return False
    
    # 步骤3: 更新SDK中的参数
    if not update_sdk_parameters(args.product_id, args.tags):
        print("\n💥 无法更新SDK参数，流程终止")
        return False
    
    # 步骤4: 调用SDK生成tracking link
    success = call_sdk_generate_tracking_link(args.product_id, args.tags)
    
    # 最终总结
    if success:
        print(f"\n🎉 Tracking Link生成成功完成!")
        print(f"📊 产品ID: {args.product_id}")
        print(f"🏷️ 标签数量: {len(args.tags)}")
        print(f"💾 Token信息已保存到: {config.get_token_storage_path()}")
        
    else:
        print(f"\n❌ Tracking Link生成失败")
        print(f"💡 请检查网络连接和API配置")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)