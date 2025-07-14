"""
Google SSO 登入處理器
"""

import asyncio
from typing import Dict, Optional
from ..config import SpiderConfig


class GoogleSSOHandler:
    """Google SSO 登入處理器"""
    
    def __init__(self, playwright_client):
        """
        初始化Google SSO處理器
        
        Args:
            playwright_client: Playwright客戶端實例
        """
        self.client = playwright_client
        self.config = SpiderConfig()
        
    async def login_with_google_sso(self, email: Optional[str] = None) -> bool:
        """
        執行Google SSO登入流程
        
        Args:
            email: 登入用的Google帳號（可選）
            
        Returns:
            bool: 登入是否成功
        """
        try:
            print("🔐 開始Google SSO登入流程...")
            
            # 導航到登入頁面
            await self.client.navigate(self.config.LOGIN_URL)
            
            # 等待並點擊Google登入按鈕
            print("🔍 尋找Google登入按鈕...")
            google_button_selectors = [
                "button[data-provider='google']",
                "a[href*='google']", 
                "button:has-text('Google')",
                "[data-testid='google-login']",
                ".google-login",
                "button:has-text('Continue with Google')"
            ]
            
            google_button_found = False
            for selector in google_button_selectors:
                try:
                    await self.client.click(selector, timeout=5000)
                    google_button_found = True
                    print(f"✅ 成功點擊Google登入按鈕: {selector}")
                    break
                except Exception:
                    continue
                    
            if not google_button_found:
                print("❌ 未找到Google登入按鈕，嘗試手動登入...")
                return await self._manual_login_prompt()
            
            # 等待Google登入頁面載入
            await asyncio.sleep(3)
            
            # 如果提供了email，嘗試自動填入
            if email:
                await self._fill_google_credentials(email)
            else:
                print("⏳ 請手動完成Google登入流程...")
                return await self._wait_for_login_completion()
                
        except Exception as e:
            print(f"❌ Google SSO登入過程中發生錯誤: {str(e)}")
            return False
            
    async def _fill_google_credentials(self, email: str) -> bool:
        """
        填入Google憑證
        
        Args:
            email: Google帳號email
            
        Returns:
            bool: 填入是否成功
        """
        try:
            # 嘗試填入email
            email_selectors = [
                "input[type='email']",
                "#identifierId",
                "[data-testid='email-input']"
            ]
            
            for selector in email_selectors:
                try:
                    await self.client.fill(selector, email)
                    print(f"✅ 成功填入email: {email}")
                    
                    # 點擊下一步
                    next_selectors = [
                        "#identifierNext",
                        "button:has-text('Next')",
                        "[data-testid='next-button']"
                    ]
                    
                    for next_selector in next_selectors:
                        try:
                            await self.client.click(next_selector)
                            break
                        except Exception:
                            continue
                    
                    break
                except Exception:
                    continue
            
            print("⏳ 請手動輸入密碼並完成登入...")
            return await self._wait_for_login_completion()
            
        except Exception as e:
            print(f"❌ 填入Google憑證時發生錯誤: {str(e)}")
            return False
    
    async def _wait_for_login_completion(self, timeout: int = 120) -> bool:
        """
        等待登入完成
        
        Args:
            timeout: 等待超時時間（秒）
            
        Returns:
            bool: 登入是否成功
        """
        print("⏳ 等待登入完成...")
        
        # 檢查登入成功的指標
        success_indicators = [
            "dashboard",
            "report",
            "profile",
            "logout",
            "publisher"
        ]
        
        start_time = asyncio.get_event_loop().time()
        
        while (asyncio.get_event_loop().time() - start_time) < timeout:
            try:
                current_url = await self.client.get_current_url()
                
                # 檢查URL是否包含成功指標
                for indicator in success_indicators:
                    if indicator in current_url.lower():
                        print(f"✅ 登入成功！當前URL: {current_url}")
                        return True
                
                # 檢查頁面內容是否包含成功指標
                page_content = await self.client.get_page_content()
                for indicator in success_indicators:
                    if indicator in page_content.lower():
                        print("✅ 登入成功！")
                        return True
                        
            except Exception:
                pass
                
            await asyncio.sleep(2)
        
        print("❌ 登入超時")
        return False
    
    async def _manual_login_prompt(self) -> bool:
        """
        手動登入提示
        
        Returns:
            bool: 登入是否成功
        """
        print("🔧 請手動完成登入流程...")
        print("✋ 完成登入後，程式將自動繼續...")
        
        return await self._wait_for_login_completion()
    
    async def verify_login_status(self) -> bool:
        """
        驗證登入狀態
        
        Returns:
            bool: 是否已登入
        """
        try:
            current_url = await self.client.get_current_url()
            
            # 檢查是否在登入頁面
            if "login" in current_url.lower():
                return False
                
            # 檢查是否包含已登入的指標
            logged_in_indicators = [
                "dashboard",
                "report", 
                "profile",
                "publisher"
            ]
            
            for indicator in logged_in_indicators:
                if indicator in current_url.lower():
                    return True
                    
            return False
            
        except Exception as e:
            print(f"❌ 驗證登入狀態時發生錯誤: {str(e)}")
            return False 