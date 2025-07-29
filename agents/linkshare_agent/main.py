#!/usr/bin/env python3
"""
TikTok Shop 聯盟行銷 Agent 主程序
提供命令列接口來生成聯盟連結、管理 Token 等
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Optional

# 添加項目根目錄到路徑
sys.path.append(str(Path(__file__).parent.parent.parent))

from . import config
from .auth import TikTokAuth
from .token_manager import TokenManager
from .link_generator import LinkGenerator

def setup_logging(level: str = "INFO"):
    """設置日誌配置"""
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {level}')
    
    logging.basicConfig(
        level=numeric_level,
        format=config.LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def get_access_token_command(args):
    """獲取 Access Token 命令"""
    print("🚀 開始獲取 Access Token...")
    
    try:
        auth = TikTokAuth()
        token_data = auth.get_access_token(args.auth_code)
        
        print("✅ Access Token 獲取成功!")
        print(f"🔑 Access Token: {token_data.get('access_token', 'N/A')}")
        print(f"🔄 Refresh Token: {token_data.get('refresh_token', 'N/A')}")
        print(f"👤 Open ID: {token_data.get('open_id', 'N/A')}")
        print(f"🏪 Seller Name: {token_data.get('seller_name', 'N/A')}")
        print(f"🌍 Base Region: {token_data.get('seller_base_region', 'N/A')}")
        
        # 保存 Token
        token_manager = TokenManager()
        token_manager.save_tokens(token_data)
        print("💾 Token 已保存到配置文件")
        
    except Exception as e:
        print(f"❌ 獲取 Access Token 失敗: {str(e)}")
        sys.exit(1)

def refresh_token_command(args):
    """刷新 Token 命令"""
    print("🔄 開始刷新 Access Token...")
    
    try:
        token_manager = TokenManager()
        if token_manager.refresh_token_if_needed():
            print("✅ Token 刷新成功!")
        else:
            print("ℹ️  Token 仍然有效，無需刷新")
            
    except Exception as e:
        print(f"❌ 刷新 Token 失敗: {str(e)}")
        sys.exit(1)

def generate_link_command(args):
    """生成聯盟連結命令"""
    product_id = args.product_id or config.DEFAULT_PRODUCT_ID
    print(f"🔗 開始生成產品 {product_id} 的聯盟連結...")
    
    try:
        link_generator = LinkGenerator()
        
        # 使用命令列參數或默認值
        channel = args.channel if args.channel else link_generator.get_default_channel()
        
        # 處理 tags 參數 - 如果提供了字符串，按逗號分割；否則使用默認值
        if args.tags:
            # 檢查 args.tags 是字符串還是列表
            if isinstance(args.tags, str):
                tags = [tag.strip() for tag in args.tags.split(',') if tag.strip()]
            else:
                # 如果已經是列表，直接使用
                tags = args.tags
        else:
            tags = link_generator.get_default_tags()
        
        response = link_generator.generate_affiliate_link(
            product_id=product_id,
            channel=channel,
            tags=tags,
            campaign_url=args.campaign_url
        )
        
        print("✅ 聯盟連結生成完成!")
        
    except Exception as e:
        print(f"❌ 生成聯盟連結失敗: {str(e)}")
        sys.exit(1)

def token_info_command(args):
    """查看 Token 信息命令"""
    print("📋 查看當前 Token 信息...")
    
    try:
        token_manager = TokenManager()
        token_info = token_manager.get_token_info()
        
        if token_info:
            print("✅ Token 信息:")
            for key, value in token_info.items():
                if key == 'access_token':
                    print(f"   🔑 {key}: {value[:20]}..." if value else f"   🔑 {key}: 未設置")
                elif key == 'refresh_token':
                    print(f"   🔄 {key}: {value[:20]}..." if value else f"   🔄 {key}: 未設置")
                else:
                    print(f"   📝 {key}: {value}")
        else:
            print("⚠️  未找到 Token 信息")
            
    except Exception as e:
        print(f"❌ 查看 Token 信息失敗: {str(e)}")
        sys.exit(1)

def clear_tokens_command(args):
    """清除 Token 命令"""
    print("🗑️  開始清除存儲的 Token...")
    
    try:
        token_manager = TokenManager()
        if token_manager.clear_tokens():
            print("✅ Token 清除成功!")
        else:
            print("⚠️  Token 清除失敗或文件不存在")
            
    except Exception as e:
        print(f"❌ 清除 Token 失敗: {str(e)}")
        sys.exit(1)

def validate_permissions_command(args):
    """驗證文件權限命令"""
    print("🔐 檢查 Token 存儲權限...")
    
    try:
        token_manager = TokenManager()
        if token_manager.validate_storage_permissions():
            print("✅ 存儲權限正常")
        else:
            print("⚠️  存儲權限可能有問題，請檢查文件權限")
            
    except Exception as e:
        print(f"❌ 權限檢查失敗: {str(e)}")
        sys.exit(1)

def diagnose_auth_code_command(args):
    """診斷 AUTH_CODE 狀態"""
    print("🔍 診斷 AUTH_CODE 狀態...")
    
    try:
        # 檢查配置
        print(f"📋 當前配置:")
        print(f"   🔑 APP_KEY: {config.APP_KEY}")
        print(f"   🔒 APP_SECRET: {config.APP_SECRET[:20]}...")
        print(f"   🔗 REDIRECT_URL: {config.REDIRECT_URL}")
        print(f"   📝 AUTH_CODE: {config.AUTH_CODE[:30]}...")
        print(f"   🌐 TOKEN_GET_URL: {config.TOKEN_GET_URL}")
        
        # 檢查 AUTH_CODE 格式
        auth_code = config.AUTH_CODE
        print(f"\n🧐 AUTH_CODE 分析:")
        print(f"   📏 長度: {len(auth_code)} 字符")
        print(f"   🔤 格式: {'✅ 正確' if auth_code.startswith('ROW_') else '❌ 格式不正確'}")
        print(f"   ⏰ 建議: AUTH_CODE 通常在獲取後較短時間內有效")
        
        # 嘗試簡單的 API 連接測試
        print(f"\n🌐 API 連接測試:")
        auth = TikTokAuth()
        
        # 手動構建測試請求來檢查連接
        import requests
        test_url = config.TOKEN_GET_URL
        test_params = {
            "app_key": config.APP_KEY,
            "app_secret": config.APP_SECRET,
            "grant_type": "authorized_code",
            "auth_code": "INVALID_TEST_CODE"  # 故意使用無效代碼來測試連接
        }
        
        try:
            response = requests.get(test_url, params=test_params, timeout=10)
            print(f"   📡 API 端點可達: ✅")
            print(f"   📈 HTTP 狀態: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                error_code = data.get('code')
                if error_code in [36004004, 98001004]:
                    print(f"   🎯 API 格式正確: ✅ (錯誤碼 {error_code} 表示請求格式正確，只是 auth_code 無效)")
                else:
                    print(f"   ⚠️  未預期的錯誤碼: {error_code}")
            else:
                print(f"   ❌ HTTP 錯誤: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ 連接失敗: {str(e)}")
        
        print(f"\n💡 建議:")
        print(f"   1. 確認 AUTH_CODE 是最新獲取的")
        print(f"   2. AUTH_CODE 通常只能使用一次")
        print(f"   3. 檢查是否在正確的 TikTok Shop 環境中獲取")
        print(f"   4. 如果仍有問題，可能需要重新進行授權流程")
        
    except Exception as e:
        print(f"❌ 診斷失敗: {str(e)}")
        sys.exit(1)

def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description="TikTok Shop 聯盟行銷 Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 獲取 Access Token
  python -m agents.linkshare_agent.main get-token
  
  # 刷新 Token
  python -m agents.linkshare_agent.main refresh-token
  
  # 生成聯盟連結 (使用默認參數)
  python -m agents.linkshare_agent.main generate --pid 1731493745807886173
  
  # 生成聯盟連結 (自定義參數)
  python -m agents.linkshare_agent.main generate --pid 1731493745807886173 --channel "MY_CHANNEL" --tags "TAG1,TAG2"
  
  # 查看 Token 信息
  python -m agents.linkshare_agent.main token-info
  
  # 清除 Token
  python -m agents.linkshare_agent.main clear-tokens
  
  # 檢查權限
  python -m agents.linkshare_agent.main validate-permissions
        """
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="日誌級別 (默認: INFO)"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # get-token 子命令
    get_token_parser = subparsers.add_parser("get-token", help="獲取 Access Token")
    get_token_parser.add_argument(
        "--auth-code",
        help="授權碼 (可選，默認使用配置文件中的 AUTH_CODE)"
    )
    
    # refresh-token 子命令
    refresh_token_parser = subparsers.add_parser("refresh-token", help="刷新 Access Token")
    
    # generate 子命令
    generate_parser = subparsers.add_parser("generate", help="生成聯盟連結")
    generate_parser.add_argument(
        "--pid", "--product-id",
        dest="product_id",
        help="產品 ID (可選，默認使用配置中的 DEFAULT_PRODUCT_ID)"
    )
    generate_parser.add_argument(
        "--channel",
        help="頻道名稱 (可選，默認使用配置中的 DEFAULT_CHANNEL)"
    )
    generate_parser.add_argument(
        "--tags",
        help="標籤列表，用逗號分隔 (可選，默認使用配置中的 DEFAULT_TAGS)"
    )
    generate_parser.add_argument(
        "--campaign-url",
        help="活動 URL (可選，會自動生成)"
    )
    
    # token-info 子命令
    token_info_parser = subparsers.add_parser("token-info", help="查看 Token 信息")
    
    # clear-tokens 子命令
    clear_tokens_parser = subparsers.add_parser("clear-tokens", help="清除存儲的 Token")
    
    # validate-permissions 子命令
    validate_permissions_parser = subparsers.add_parser("validate-permissions", help="驗證文件權限")
    
    # diagnose-auth-code 子命令
    diagnose_auth_code_parser = subparsers.add_parser("diagnose-auth-code", help="診斷 AUTH_CODE 狀態")
    
    args = parser.parse_args()
    
    # 設置日誌
    setup_logging(args.log_level)
    
    # 驗證配置
    try:
        config.validate_config()
    except ValueError as e:
        print(f"❌ 配置錯誤: {e}")
        sys.exit(1)
    
    # 處理 tags 參數
    if hasattr(args, 'tags') and args.tags:
        args.tags = [tag.strip() for tag in args.tags.split(',')]
    
    # 根據命令執行相應的函數
    if args.command == "get-token":
        get_access_token_command(args)
    elif args.command == "refresh-token":
        refresh_token_command(args)
    elif args.command == "generate":
        generate_link_command(args)
    elif args.command == "token-info":
        token_info_command(args)
    elif args.command == "clear-tokens":
        clear_tokens_command(args)
    elif args.command == "validate-permissions":
        validate_permissions_command(args)
    elif args.command == "diagnose-auth-code":
        diagnose_auth_code_command(args)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main() 