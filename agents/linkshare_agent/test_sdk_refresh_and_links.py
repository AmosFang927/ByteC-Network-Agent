#!/usr/bin/env python3
"""
TikTok Shop SDK 測試腳本
測試 refresh token 功能和 gen tracking link 功能
"""

import sys
import time
import logging
from pathlib import Path

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.linkshare_agent.token_manager import TokenManager
from agents.linkshare_agent.auth import TikTokAuth
from agents.linkshare_agent.link_generator import LinkGenerator
from agents.linkshare_agent import config

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TikTokSDKTester:
    """TikTok Shop SDK 測試類"""
    
    def __init__(self):
        """初始化測試器"""
        self.token_manager = TokenManager()
        self.auth = TikTokAuth()
        self.link_generator = LinkGenerator()
        
        logger.info("🔧 TikTokSDKTester 初始化完成")
        
    def test_refresh_token(self) -> bool:
        """
        測試 refresh token 功能
        
        Returns:
            True 如果測試成功
        """
        logger.info("🔄 開始測試 refresh token 功能...")
        
        try:
            # 1. 獲取當前 token 信息
            logger.info("📊 獲取當前 token 信息...")
            token_info = self.token_manager.get_token_info()
            
            logger.info(f"📋 Token 狀態: {token_info['status']}")
            logger.info(f"⏰ 剩餘時間: {token_info.get('remaining_seconds', 'N/A')} 秒")
            logger.info(f"🔄 Refresh Token: {token_info.get('refresh_token', 'N/A')[:30]}...")
            
            # 2. 檢查是否需要刷新
            if token_info['is_expired']:
                logger.info("⏰ Token 已過期，開始刷新...")
            else:
                logger.info("✅ Token 仍然有效")
                
            # 3. 強制刷新 token
            logger.info("🔄 強制刷新 token...")
            refresh_token = token_info.get('refresh_token')
            
            if not refresh_token:
                logger.error("❌ 沒有可用的 refresh_token")
                return False
                
            # 使用 auth 類刷新 token
            new_token_data = self.auth.refresh_access_token(refresh_token)
            
            # 保存新的 token
            self.token_manager.save_tokens(new_token_data)
            
            logger.info("✅ Token 刷新成功!")
            logger.info(f"🔑 新的 Access Token: {new_token_data.get('access_token', '')[:30]}...")
            logger.info(f"🔄 新的 Refresh Token: {new_token_data.get('refresh_token', '')[:30]}...")
            
            # 4. 驗證新 token
            logger.info("🔍 驗證新 token...")
            new_token_info = self.token_manager.get_token_info()
            logger.info(f"📊 新 Token 狀態: {new_token_info['status']}")
            logger.info(f"⏰ 新 Token 剩餘時間: {new_token_info.get('remaining_seconds', 'N/A')} 秒")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Refresh token 測試失敗: {e}")
            return False
            
    def test_gen_tracking_link(self) -> bool:
        """
        測試生成 tracking link 功能
        
        Returns:
            True 如果測試成功
        """
        logger.info("🔗 開始測試 gen tracking link 功能...")
        
        try:
            # 1. 確保有有效的 token
            logger.info("🔑 確保有有效的 access token...")
            access_token = self.token_manager.get_valid_token()
            logger.info(f"✅ Access token 獲取成功: {access_token[:30]}...")
            
            # 2. 測試默認產品
            logger.info("📦 測試默認產品...")
            default_product_id = config.DEFAULT_PRODUCT_ID
            logger.info(f"🆔 產品 ID: {default_product_id}")
            
            # 3. 生成聯盟連結
            logger.info("🔗 生成聯盟連結...")
            response = self.link_generator.generate_affiliate_link(
                product_id=default_product_id,
                channel="OEM3_OPPO",
                tags=config.DEFAULT_TAGS
            )
            
            # 4. 檢查響應
            if response.get('code') == 0:
                logger.info("✅ 聯盟連結生成成功!")
                
                # 打印生成的連結
                data = response.get('data', {})
                links = data.get('affiliate_sharing_links', [])
                
                logger.info(f"📊 生成了 {len(links)} 個連結:")
                for i, link in enumerate(links, 1):
                    logger.info(f"   {i}. 標籤: {link.get('tag')}")
                    logger.info(f"     連結: {link.get('affiliate_sharing_link')}")
                    
                # 檢查錯誤
                errors = data.get('errors', [])
                if errors:
                    logger.warning(f"⚠️  發現 {len(errors)} 個錯誤:")
                    for error in errors:
                        logger.warning(f"   ❌ {error}")
                        
                return True
            else:
                logger.error(f"❌ 聯盟連結生成失敗: {response.get('message')}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Gen tracking link 測試失敗: {e}")
            return False
            
    def test_custom_product_link(self, product_id: str) -> bool:
        """
        測試自定義產品的 tracking link 生成
        
        Args:
            product_id: 產品 ID
            
        Returns:
            True 如果測試成功
        """
        logger.info(f"🔗 開始測試自定義產品 {product_id} 的 tracking link...")
        
        try:
            # 生成自定義產品的聯盟連結
            response = self.link_generator.generate_affiliate_link(
                product_id=product_id,
                channel="OEM2_VIVO",
                tags=config.DEFAULT_TAGS
            )
            
            if response.get('code') == 0:
                logger.info("✅ 自定義產品連結生成成功!")
                
                data = response.get('data', {})
                links = data.get('affiliate_sharing_links', [])
                
                logger.info(f"📊 生成了 {len(links)} 個連結:")
                for i, link in enumerate(links, 1):
                    logger.info(f"   {i}. 標籤: {link.get('tag')}")
                    logger.info(f"     連結: {link.get('affiliate_sharing_link')}")
                    
                return True
            else:
                logger.error(f"❌ 自定義產品連結生成失敗: {response.get('message')}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 自定義產品連結測試失敗: {e}")
            return False
            
    def run_full_test(self) -> bool:
        """
        運行完整測試套件
        
        Returns:
            True 如果所有測試都成功
        """
        logger.info("🚀 開始運行完整 SDK 測試套件...")
        
        test_results = []
        
        # 1. 測試 refresh token
        logger.info("=" * 60)
        logger.info("🔄 測試 1: Refresh Token 功能")
        logger.info("=" * 60)
        refresh_success = self.test_refresh_token()
        test_results.append(("Refresh Token", refresh_success))
        
        # 2. 測試 gen tracking link
        logger.info("=" * 60)
        logger.info("🔗 測試 2: Gen Tracking Link 功能")
        logger.info("=" * 60)
        link_success = self.test_gen_tracking_link()
        test_results.append(("Gen Tracking Link", link_success))
        
        # 3. 測試自定義產品
        logger.info("=" * 60)
        logger.info("🔗 測試 3: 自定義產品 Tracking Link")
        logger.info("=" * 60)
        custom_product_id = "1731493745807886173"  # 使用配置中的默認產品
        custom_success = self.test_custom_product_link(custom_product_id)
        test_results.append(("Custom Product Link", custom_success))
        
        # 4. 打印測試結果
        logger.info("=" * 60)
        logger.info("📊 測試結果總結")
        logger.info("=" * 60)
        
        all_passed = True
        for test_name, success in test_results:
            status = "✅ 通過" if success else "❌ 失敗"
            logger.info(f"   {test_name}: {status}")
            if not success:
                all_passed = False
                
        if all_passed:
            logger.info("🎉 所有測試都通過了!")
        else:
            logger.warning("⚠️  部分測試失敗")
            
        return all_passed

def main():
    """主函數"""
    logger.info("🚀 啟動 TikTok Shop SDK 測試...")
    
    try:
        # 創建測試器
        tester = TikTokSDKTester()
        
        # 運行完整測試
        success = tester.run_full_test()
        
        if success:
            logger.info("🎉 SDK 測試完成，所有功能正常!")
            return 0
        else:
            logger.error("❌ SDK 測試失敗，請檢查錯誤信息")
            return 1
            
    except Exception as e:
        logger.error(f"❌ 測試過程中發生錯誤: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 