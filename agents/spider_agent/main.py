"""
Spider Agent 主程式
爬取Involve Asia網站結構並分析
"""

import asyncio
import sys
import os
from typing import Optional, Dict, Any

# 添加當前目錄到路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import SpiderConfig
from crawler.playwright_client import PlaywrightClient
from auth.google_sso_handler import GoogleSSOHandler
from crawler.structure_analyzer import StructureAnalyzer
from output.structure_exporter import StructureExporter


class SpiderAgent:
    """Spider Agent 主類"""
    
    def __init__(self):
        """初始化Spider Agent"""
        self.config = SpiderConfig()
        self.playwright_client = None
        self.sso_handler = None
        self.analyzer = None
        self.exporter = None
        
    async def initialize(self) -> bool:
        """初始化所有組件"""
        try:
            print("🕷️ 初始化Spider Agent...")
            
            # 確保輸出目錄存在
            self.config.ensure_output_dirs()
            
            # 初始化Playwright客戶端
            self.playwright_client = PlaywrightClientMCP()
            await self.playwright_client.initialize()
            
            # 初始化其他組件
            self.sso_handler = GoogleSSOHandler(self.playwright_client)
            self.analyzer = StructureAnalyzer(self.playwright_client)
            self.exporter = StructureExporter()
            
            print("✅ Spider Agent初始化完成")
            return True
            
        except Exception as e:
            print(f"❌ 初始化Spider Agent失敗: {str(e)}")
            return False
    
    async def run_full_analysis(self, email: Optional[str] = None) -> bool:
        """
        執行完整的網站分析流程
        
        Args:
            email: Google登入email（可選）
            
        Returns:
            bool: 分析是否成功
        """
        try:
            print("🚀 開始完整網站分析流程...")
            
            # Step 1: 導航到目標網站
            print("📍 Step 1: 導航到Involve Asia...")
            success = await self.playwright_client.navigate(self.config.TARGET_URL)
            if not success:
                print("❌ 導航到目標網站失敗")
                return False
            
            # 初始截圖
            await self.playwright_client.screenshot("initial_page", full_page=True)
            
            # Step 2: Google SSO登入
            print("🔐 Step 2: 執行Google SSO登入...")
            login_success = await self.sso_handler.login_with_google_sso(email)
            if not login_success:
                print("❌ Google SSO登入失敗")
                return False
            
            # 登入後截圖
            await self.playwright_client.screenshot("after_login", full_page=True)
            
            # Step 3: 導航到Report頁面
            print("📊 Step 3: 導航到Report頁面...")
            await self._navigate_to_reports()
            
            # Step 4: 導航到Performance Report
            print("📈 Step 4: 導航到Performance Report...")
            await self._navigate_to_performance_report()
            
            # Performance Report截圖
            await self.playwright_client.screenshot("performance_report", full_page=True)
            
            # Step 5: 分析頁面結構
            print("🔍 Step 5: 分析頁面結構...")
            analysis_result = await self.analyzer.analyze_page_structure(self.config.TARGET_URL)
            if not analysis_result:
                print("❌ 頁面結構分析失敗")
                return False
            
            # Step 6: 匯出分析結果
            print("💾 Step 6: 匯出分析結果...")
            exported_files = await self.exporter.export_analysis_result(
                analysis_result, 
                ['json', 'html', 'markdown', 'css']
            )
            
            # Step 7: 創建Dashboard樣板
            print("🎨 Step 7: 創建Dashboard樣板...")
            dashboard_template = await self.exporter.create_dashboard_template(analysis_result)
            
            # 顯示結果
            print("\n✅ 分析完成！生成的檔案:")
            for format_type, file_path in exported_files.items():
                print(f"   📄 {format_type.upper()}: {file_path}")
            
            if dashboard_template:
                print(f"   🎨 Dashboard樣板: {dashboard_template}")
            
            print(f"\n📸 截圖保存位置: {self.config.SCREENSHOTS_DIR}")
            print(f"📊 分析結果位置: {self.config.STRUCTURE_DIR}")
            print(f"🎨 樣式資源位置: {self.config.ASSETS_DIR}")
            
            return True
            
        except Exception as e:
            print(f"❌ 分析流程中發生錯誤: {str(e)}")
            return False
        
        finally:
            # 清理資源
            await self._cleanup()
    
    async def _navigate_to_reports(self) -> bool:
        """導航到Reports頁面"""
        try:
            # 嘗試多種可能的Report選擇器
            report_selectors = [
                "a[href*='report']",
                "button:has-text('Report')",
                "nav a:has-text('Report')",
                ".nav-item:has-text('Report')",
                "[data-testid='report-menu']",
                "li:has-text('Report') a"
            ]
            
            for selector in report_selectors:
                try:
                    await self.playwright_client.wait_for_element(selector, timeout=5000)
                    await self.playwright_client.click(selector)
                    print(f"✅ 成功點擊Report選單: {selector}")
                    await asyncio.sleep(2)  # 等待頁面載入
                    return True
                except Exception:
                    continue
            
            print("⚠️ 未找到Report選單，嘗試手動導航...")
            # 嘗試直接導航到report URL
            report_url = "https://app.involve.asia/publisher/report"
            return await self.playwright_client.navigate(report_url)
            
        except Exception as e:
            print(f"❌ 導航到Reports頁面時發生錯誤: {str(e)}")
            return False
    
    async def _navigate_to_performance_report(self) -> bool:
        """導航到Performance Report頁面"""
        try:
            # 嘗試多種可能的Performance Report選擇器
            performance_selectors = [
                "a[href*='performance']",
                "button:has-text('Performance')",
                "a:has-text('Performance Report')",
                ".report-menu a:has-text('Performance')",
                "[data-testid='performance-report']"
            ]
            
            for selector in performance_selectors:
                try:
                    await self.playwright_client.wait_for_element(selector, timeout=5000)
                    await self.playwright_client.click(selector)
                    print(f"✅ 成功點擊Performance Report: {selector}")
                    await asyncio.sleep(3)  # 等待頁面載入
                    return True
                except Exception:
                    continue
            
            print("⚠️ 未找到Performance Report選單")
            return True  # 繼續分析當前頁面
            
        except Exception as e:
            print(f"❌ 導航到Performance Report時發生錯誤: {str(e)}")
            return False
    
    async def _cleanup(self):
        """清理資源"""
        try:
            if self.playwright_client:
                await self.playwright_client.close()
                print("🔒 已清理Playwright資源")
        except Exception as e:
            print(f"⚠️ 清理資源時發生錯誤: {str(e)}")


class PlaywrightClientMCP(PlaywrightClient):
    """整合MCP Playwright工具的客戶端"""
    
    async def _mcp_navigate(self, url: str) -> bool:
        """使用MCP工具導航"""
        try:
            # 這裡將實際調用MCP Playwright工具
            print(f"🔧 使用MCP工具導航到: {url}")
            # 暫時返回True，實際使用時需要調用MCP工具
            return True
        except Exception as e:
            print(f"❌ MCP導航失敗: {str(e)}")
            return False
    
    async def _mcp_click(self, selector: str) -> bool:
        """使用MCP工具點擊"""
        try:
            print(f"🔧 使用MCP工具點擊: {selector}")
            # 暫時返回True，實際使用時需要調用MCP工具
            return True
        except Exception as e:
            print(f"❌ MCP點擊失敗: {str(e)}")
            return False
    
    async def _mcp_fill(self, selector: str, value: str) -> bool:
        """使用MCP工具填入"""
        try:
            print(f"🔧 使用MCP工具填入文字: {selector}")
            # 暫時返回True，實際使用時需要調用MCP工具
            return True
        except Exception as e:
            print(f"❌ MCP填入失敗: {str(e)}")
            return False
    
    async def _mcp_screenshot(self, name: str, full_page: bool) -> bool:
        """使用MCP工具截圖"""
        try:
            print(f"🔧 使用MCP工具截圖: {name}")
            # 暫時返回True，實際使用時需要調用MCP工具
            return True
        except Exception as e:
            print(f"❌ MCP截圖失敗: {str(e)}")
            return False
    
    async def _mcp_get_html(self) -> str:
        """使用MCP工具獲取HTML"""
        try:
            print("🔧 使用MCP工具獲取頁面HTML")
            # 暫時返回空字串，實際使用時需要調用MCP工具
            return "<html><body>Sample HTML</body></html>"
        except Exception as e:
            print(f"❌ MCP獲取HTML失敗: {str(e)}")
            return ""
    
    async def _mcp_evaluate(self, script: str) -> Any:
        """使用MCP工具執行JavaScript"""
        try:
            print(f"🔧 使用MCP工具執行JS: {script[:50]}...")
            # 暫時返回None，實際使用時需要調用MCP工具
            return None
        except Exception as e:
            print(f"❌ MCP執行JS失敗: {str(e)}")
            return None
    
    async def _mcp_close(self) -> bool:
        """使用MCP工具關閉瀏覽器"""
        try:
            print("🔧 使用MCP工具關閉瀏覽器")
            # 暫時返回True，實際使用時需要調用MCP工具
            return True
        except Exception as e:
            print(f"❌ MCP關閉瀏覽器失敗: {str(e)}")
            return False


async def main():
    """主函數"""
    print("🕷️ ByteC Spider Agent")
    print("=" * 50)
    
    # 創建Spider Agent實例
    agent = SpiderAgent()
    
    # 初始化
    if not await agent.initialize():
        print("❌ 初始化失敗")
        return
    
    # 詢問是否提供email
    print("\n請提供Google登入資訊（可選）:")
    email = input("Email (按Enter跳過): ").strip()
    if not email:
        email = None
    
    print("\n🚀 開始爬取和分析...")
    
    # 執行完整分析
    success = await agent.run_full_analysis(email)
    
    if success:
        print("\n🎉 分析完成！")
        print("📋 請檢查output目錄中的分析結果")
        print("🎨 可以使用生成的CSS和HTML樣板來改進ByteC Dashboard")
    else:
        print("\n❌ 分析失敗")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ 用戶中斷程式")
    except Exception as e:
        print(f"\n❌ 程式執行錯誤: {str(e)}")
    finally:
        print("\n👋 程式結束") 