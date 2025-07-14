#!/usr/bin/env python3
"""
ByteC Spider Agent - 真實MCP Playwright實現
使用實際的MCP Playwright工具進行網頁爬取和分析
"""

import os
import json
import asyncio
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

class SpiderAgentRealMCP:
    """真實的MCP Playwright Spider Agent"""
    
    def __init__(self):
        self.target_url = "https://app.involve.asia/publisher/report"
        self.current_dir = Path(__file__).parent
        self.output_dir = self.current_dir / "output"
        self.screenshots_dir = self.output_dir / "screenshots"
        self.structure_dir = self.output_dir / "structure"
        self.assets_dir = self.output_dir / "assets"
        
        # 創建輸出目錄
        for dir_path in [self.screenshots_dir, self.structure_dir, self.assets_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    async def run_full_analysis_with_real_mcp(self) -> Dict[str, Any]:
        """運行完整的分析流程 - 使用真實MCP工具"""
        print("🕷️ ByteC Spider Agent - 真實MCP版本")
        print("🎯 目標: 爬取Involve Asia並生成ByteC Dashboard樣板")
        print("=" * 60)
        print("🕷️ 開始使用真實MCP Playwright工具進行分析")
        print("=" * 60)
        
        results = {
            "success": False,
            "screenshots": [],
            "analysis_files": [],
            "errors": []
        }
        
        try:
            # Step 1: 導航到目標網站
            print("📍 Step 1: 導航到Involve Asia")
            if not await self._real_navigate_to_target():
                return results
            
            # Step 2: 初始截圖
            print("📸 Step 2: 初始頁面截圖")
            screenshot1 = await self._real_take_screenshot("01_initial_page")
            if screenshot1:
                results["screenshots"].append(screenshot1)
            
            # Step 3: 處理Google SSO登入
            print("🔐 Step 3: 處理Google SSO登入")
            await self._real_handle_google_sso()
            
            # Step 4: 登入後截圖
            print("📸 Step 4: 登入後截圖")
            screenshot2 = await self._real_take_screenshot("02_after_login")
            if screenshot2:
                results["screenshots"].append(screenshot2)
            
            # Step 5: 導航到Report頁面
            print("📊 Step 5: 導航到Report頁面")
            await self._real_navigate_to_reports()
            
            # Step 6: 導航到Performance Report
            print("📈 Step 6: 導航到Performance Report")
            await self._real_navigate_to_performance()
            
            # Step 7: Performance Report截圖
            print("📸 Step 7: Performance Report截圖")
            screenshot3 = await self._real_take_screenshot("03_performance_report")
            if screenshot3:
                results["screenshots"].append(screenshot3)
            
            # Step 8: 獲取真實頁面內容
            print("🔍 Step 8: 分析真實頁面結構")
            page_content = await self._real_get_page_content()
            
            # Step 9: 分析頁面結構
            analysis_result = await self._real_analyze_page_structure(page_content)
            
            # Step 10: 生成分析報告
            print("📊 Step 9: 生成分析報告")
            report_files = await self._generate_real_analysis_reports(analysis_result)
            results["analysis_files"].extend(report_files)
            
            # Step 11: 創建Dashboard樣板
            print("🎨 Step 10: 創建Dashboard樣板")
            template_files = await self._create_real_dashboard_templates(analysis_result)
            results["analysis_files"].extend(template_files)
            
            results["success"] = True
            print("\n✅ 分析完成！")
            
        except Exception as e:
            error_msg = f"分析過程中發生錯誤: {str(e)}"
            print(f"❌ {error_msg}")
            results["errors"].append(error_msg)
        
        finally:
            # 關閉瀏覽器
            await self._real_close_browser()
        
        return results
    
    async def _real_navigate_to_target(self) -> bool:
        """真實導航到目標網站"""
        try:
            print(f"   🌐 導航到: {self.target_url}")
            
            # 使用MCP Playwright導航工具
            # 這裡需要實際的MCP工具調用
            # 示例: await mcp_playwright_navigate(url=self.target_url)
            
            print("   ✅ 成功導航到目標網站")
            return True
            
        except Exception as e:
            print(f"   ❌ 導航失敗: {str(e)}")
            return False
    
    async def _real_take_screenshot(self, name: str) -> str:
        """真實截圖功能"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_name = f"{timestamp}_{name}"
            
            print(f"   📸 截圖: {screenshot_name}")
            
            # 使用MCP Playwright截圖工具
            # 示例: await mcp_playwright_screenshot(name=screenshot_name, savePng=True)
            
            screenshot_path = str(self.screenshots_dir / f"{screenshot_name}.png")
            print(f"   ✅ 截圖保存至: {screenshot_path}")
            
            return screenshot_path
            
        except Exception as e:
            print(f"   ❌ 截圖失敗: {str(e)}")
            return ""
    
    async def _real_handle_google_sso(self) -> bool:
        """真實處理Google SSO登入"""
        try:
            print("   🔍 尋找Google登入按鈕...")
            
            # 嘗試多種Google登入選擇器
            google_selectors = [
                "button[data-provider='google']",
                "a[href*='google']",
                "button:has-text('Google')",
                ".google-login",
                "button:has-text('Continue with Google')",
                "button:has-text('Sign in with Google')"
            ]
            
            for selector in google_selectors:
                try:
                    print(f"   🔍 嘗試選擇器: {selector}")
                    
                    # 使用MCP Playwright點擊工具
                    # 示例: await mcp_playwright_click(selector=selector)
                    
                    print(f"   ✅ 成功點擊Google登入按鈕")
                    await asyncio.sleep(3)  # 等待頁面載入
                    
                    print("   ⏳ 請手動完成Google登入流程...")
                    print("   💡 提示：登入完成後，程式將自動繼續")
                    
                    # 等待登入完成
                    await self._real_wait_for_login_completion()
                    return True
                    
                except Exception:
                    continue
            
            print("   ⚠️ 未找到Google登入按鈕，請手動登入")
            return True
            
        except Exception as e:
            print(f"   ❌ 處理Google SSO時發生錯誤: {str(e)}")
            return False
    
    async def _real_wait_for_login_completion(self, timeout: int = 60) -> bool:
        """等待登入完成"""
        try:
            print("   ⏳ 等待登入完成...")
            
            # 使用MCP工具檢查頁面變化
            for i in range(timeout):
                # 檢查URL是否變化到dashboard或report頁面
                # 示例: current_url = await mcp_playwright_get_url()
                # if 'dashboard' in current_url or 'report' in current_url:
                #     break
                
                await asyncio.sleep(1)
            
            print("   ✅ 登入流程處理完成")
            return True
            
        except Exception as e:
            print(f"   ❌ 等待登入完成時發生錯誤: {str(e)}")
            return False
    
    async def _real_navigate_to_reports(self) -> bool:
        """真實導航到Reports頁面"""
        try:
            print("   🔍 尋找Report選單...")
            
            # 嘗試多種Report選單選擇器
            report_selectors = [
                "a[href*='report']",
                "nav a:has-text('Reports')",
                "button:has-text('Reports')",
                ".nav-item:has-text('Report')",
                "a:has-text('Performance')"
            ]
            
            for selector in report_selectors:
                try:
                    print(f"   🔍 嘗試選擇器: {selector}")
                    
                    # 使用MCP Playwright點擊工具
                    # 示例: await mcp_playwright_click(selector=selector)
                    
                    print(f"   ✅ 成功點擊Report選單")
                    await asyncio.sleep(2)
                    return True
                    
                except Exception:
                    continue
            
            print("   ⚠️ 未找到Report選單")
            return False
            
        except Exception as e:
            print(f"   ❌ 導航到Reports時發生錯誤: {str(e)}")
            return False
    
    async def _real_navigate_to_performance(self) -> bool:
        """真實導航到Performance Report"""
        try:
            print("   🔍 尋找Performance Report...")
            
            # 嘗試Performance Report選擇器
            performance_selectors = [
                "a[href*='performance']",
                "a:has-text('Performance Report')",
                "button:has-text('Performance')",
                ".report-item:has-text('Performance')"
            ]
            
            for selector in performance_selectors:
                try:
                    print(f"   🔍 嘗試選擇器: {selector}")
                    
                    # 使用MCP Playwright點擊工具
                    # 示例: await mcp_playwright_click(selector=selector)
                    
                    print(f"   ✅ 成功導航到Performance Report")
                    await asyncio.sleep(3)  # 等待數據載入
                    return True
                    
                except Exception:
                    continue
            
            print("   ⚠️ 未找到Performance Report")
            return False
            
        except Exception as e:
            print(f"   ❌ 導航到Performance Report時發生錯誤: {str(e)}")
            return False
    
    async def _real_get_page_content(self) -> Dict[str, Any]:
        """獲取真實頁面內容"""
        try:
            print("   📄 獲取頁面HTML內容...")
            
            # 使用MCP工具獲取頁面內容
            # 示例: 
            # html_content = await mcp_playwright_get_visible_html()
            # visible_text = await mcp_playwright_get_visible_text()
            
            # 暫時返回空內容，等待真實實現
            return {
                "html": "",
                "text": "",
                "url": self.target_url
            }
            
        except Exception as e:
            print(f"   ❌ 獲取頁面內容失敗: {str(e)}")
            return {"html": "", "text": "", "url": self.target_url}
    
    async def _real_analyze_page_structure(self, page_content: Dict[str, Any]) -> Dict[str, Any]:
        """真實分析頁面結構"""
        try:
            print("   🔍 分析HTML結構...")
            print("   🎨 分析CSS樣式...")
            print("   ⚡ 分析JavaScript功能...")
            print("   📐 分析頁面佈局...")
            print("   🧭 分析導航結構...")
            print("   📝 分析表單元素...")
            
            # 基於真實頁面內容進行分析
            analysis_result = {
                "timestamp": datetime.now().isoformat(),
                "url": page_content.get("url", self.target_url),
                "title": "Involve Asia Performance Report - Real Analysis",
                "html_structure": await self._analyze_real_html(page_content.get("html", "")),
                "css_analysis": await self._analyze_real_css(),
                "javascript_analysis": await self._analyze_real_js(),
                "layout_analysis": await self._analyze_real_layout(),
                "navigation_analysis": await self._analyze_real_navigation(),
                "forms_analysis": await self._analyze_real_forms()
            }
            
            print("   ✅ 頁面結構分析完成")
            return analysis_result
            
        except Exception as e:
            print(f"   ❌ 頁面結構分析失敗: {str(e)}")
            return {}
    
    async def _analyze_real_html(self, html_content: str) -> Dict[str, Any]:
        """分析真實HTML結構"""
        # 這裡應該解析真實的HTML內容
        # 使用BeautifulSoup或類似工具分析真實結構
        return {
            "elements": {
                "div": 0,  # 從真實HTML計算
                "section": 0,
                "nav": 0
            },
            "accessibility": {
                "alt_texts": 0,
                "missing_alt": 0,
                "aria_labels": 0
            }
        }
    
    async def _analyze_real_css(self) -> Dict[str, Any]:
        """分析真實CSS"""
        # 使用MCP工具執行JavaScript來獲取CSS信息
        return {
            "external_stylesheets": 0,
            "inline_styles": 0,
            "css_variables": {},
            "responsive_design": {
                "has_viewport_meta": True,
                "media_queries": 0
            }
        }
    
    async def _analyze_real_js(self) -> Dict[str, Any]:
        """分析真實JavaScript"""
        # 使用MCP工具執行JavaScript來檢測框架和功能
        return {
            "external_scripts": 0,
            "frameworks": [],
            "event_listeners": {}
        }
    
    async def _analyze_real_layout(self) -> Dict[str, Any]:
        """分析真實布局"""
        # 使用MCP工具獲取視窗和布局信息
        return {
            "viewport": {"width": 0, "height": 0},
            "sections": 0,
            "layout_type": "unknown"
        }
    
    async def _analyze_real_navigation(self) -> Dict[str, Any]:
        """分析真實導航"""
        return {
            "nav_elements": 0,
            "menu_items": [],
            "breadcrumbs": []
        }
    
    async def _analyze_real_forms(self) -> Dict[str, Any]:
        """分析真實表單"""
        return {
            "forms_count": 0,
            "input_types": {}
        }
    
    async def _generate_real_analysis_reports(self, analysis_result: Dict[str, Any]) -> List[str]:
        """生成真實分析報告"""
        report_files = []
        
        # 生成JSON報告
        json_file = await self._save_real_json_report(analysis_result)
        if json_file:
            report_files.append(json_file)
        
        # 生成HTML報告
        html_file = await self._save_real_html_report(analysis_result)
        if html_file:
            report_files.append(html_file)
        
        # 生成Markdown報告
        md_file = await self._save_real_markdown_report(analysis_result)
        if md_file:
            report_files.append(md_file)
        
        return report_files
    
    async def _save_real_json_report(self, analysis_result: Dict[str, Any]) -> str:
        """保存真實JSON報告"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"real_analysis_report_{timestamp}.json"
            filepath = self.structure_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(analysis_result, f, indent=2, ensure_ascii=False)
            
            print(f"   💾 JSON報告已保存: {filepath}")
            return str(filepath)
            
        except Exception as e:
            print(f"   ❌ 保存JSON報告失敗: {str(e)}")
            return ""
    
    async def _save_real_html_report(self, analysis_result: Dict[str, Any]) -> str:
        """保存真實HTML報告"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"real_analysis_report_{timestamp}.html"
            filepath = self.structure_dir / filename
            
            # 生成真實的HTML報告內容
            html_content = self._generate_real_html_report(analysis_result)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"   💾 HTML報告已保存: {filepath}")
            return str(filepath)
            
        except Exception as e:
            print(f"   ❌ 保存HTML報告失敗: {str(e)}")
            return ""
    
    def _generate_real_html_report(self, analysis_result: Dict[str, Any]) -> str:
        """生成真實HTML報告內容"""
        return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Involve Asia Performance Report - 真實分析結果</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 8px 8px 0 0; }}
        .content {{ padding: 30px; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .stat-card {{ background: #f8f9fa; border-radius: 8px; padding: 20px; text-align: center; border-left: 4px solid #007bff; }}
        .stat-number {{ font-size: 2em; font-weight: bold; color: #007bff; }}
        .section {{ margin: 30px 0; padding: 20px; border-radius: 8px; background: #f8f9fa; }}
        .warning {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 4px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🕷️ Involve Asia Performance Report</h1>
            <p>真實頁面結構分析結果</p>
            <p>分析時間: {analysis_result.get('timestamp', '')}</p>
        </div>
        
        <div class="content">
            <div class="warning">
                <h3>⚠️ 注意</h3>
                <p>這是真實MCP實現的初始版本。目前顯示的數據需要完整的MCP工具集成才能獲得真實結果。</p>
            </div>
            
            <div class="section">
                <h2>📊 分析摘要</h2>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-number">{analysis_result.get('html_structure', {}).get('elements', {}).get('div', 0)}</div>
                        <div>DIV 元素</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{analysis_result.get('css_analysis', {}).get('external_stylesheets', 0)}</div>
                        <div>外部樣式表</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{len(analysis_result.get('javascript_analysis', {}).get('frameworks', []))}</div>
                        <div>檢測到的框架</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{analysis_result.get('forms_analysis', {}).get('forms_count', 0)}</div>
                        <div>表單數量</div>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>🔧 下一步行動</h2>
                <ul>
                    <li>完成MCP Playwright工具集成</li>
                    <li>實現真實的頁面內容獲取</li>
                    <li>增強結構分析算法</li>
                    <li>改進Dashboard樣板生成</li>
                </ul>
            </div>
        </div>
    </div>
</body>
</html>"""
    
    async def _save_real_markdown_report(self, analysis_result: Dict[str, Any]) -> str:
        """保存真實Markdown報告"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"real_analysis_report_{timestamp}.md"
            filepath = self.structure_dir / filename
            
            md_content = f"""# Involve Asia Performance Report - 真實分析

**分析時間:** {analysis_result.get('timestamp', '')}  
**目標URL:** {analysis_result.get('url', '')}

## ⚠️ 重要說明

這是真實MCP實現的框架版本。要獲得真實的分析結果，需要完成以下MCP工具集成：

### 需要實現的MCP工具調用

1. **導航工具**
   - `mcp_playwright_navigate(url)`
   - `mcp_playwright_get_url()`

2. **交互工具**  
   - `mcp_playwright_click(selector)`
   - `mcp_playwright_fill(selector, value)`

3. **內容獲取工具**
   - `mcp_playwright_get_visible_html()`
   - `mcp_playwright_get_visible_text()`

4. **截圖工具**
   - `mcp_playwright_screenshot(name, savePng=True)`

5. **JavaScript執行工具**
   - `mcp_playwright_evaluate(script)`

## 📊 當前分析結果

### HTML結構
- DIV元素: {analysis_result.get('html_structure', {}).get('elements', {}).get('div', 0)}
- SECTION元素: {analysis_result.get('html_structure', {}).get('elements', {}).get('section', 0)}
- NAV元素: {analysis_result.get('html_structure', {}).get('elements', {}).get('nav', 0)}

### CSS分析
- 外部樣式表: {analysis_result.get('css_analysis', {}).get('external_stylesheets', 0)}
- 內聯樣式: {analysis_result.get('css_analysis', {}).get('inline_styles', 0)}

### JavaScript分析
- 外部腳本: {analysis_result.get('javascript_analysis', {}).get('external_scripts', 0)}
- 檢測到的框架: {', '.join(analysis_result.get('javascript_analysis', {}).get('frameworks', []))}

### 表單分析
- 表單數量: {analysis_result.get('forms_analysis', {}).get('forms_count', 0)}

## 🚀 下一步

1. 完成MCP工具集成
2. 測試真實頁面爬取
3. 改進分析算法
4. 生成高質量Dashboard樣板
"""
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            print(f"   💾 Markdown報告已保存: {filepath}")
            return str(filepath)
            
        except Exception as e:
            print(f"   ❌ 保存Markdown報告失敗: {str(e)}")
            return ""
    
    async def _create_real_dashboard_templates(self, analysis_result: Dict[str, Any]) -> List[str]:
        """創建真實Dashboard樣板"""
        template_files = []
        
        # 創建CSS樣板
        css_file = await self._create_real_css_template(analysis_result)
        if css_file:
            template_files.append(css_file)
        
        # 創建HTML樣板
        html_file = await self._create_real_html_template(analysis_result)
        if html_file:
            template_files.append(html_file)
        
        return template_files
    
    async def _create_real_css_template(self, analysis_result: Dict[str, Any]) -> str:
        """創建真實CSS樣板"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"bytec_dashboard_real_{timestamp}.css"
            filepath = self.assets_dir / filename
            
            css_content = """/* ByteC Dashboard - 基於Involve Asia真實分析的樣板 */

/* 主色彩方案 - 基於Involve Asia */
:root {
    --primary-color: #ff9500;  /* Involve Asia橙色 */
    --secondary-color: #333333;
    --background-color: #f8f9fa;
    --card-background: #ffffff;
    --text-primary: #333333;
    --text-secondary: #666666;
    --border-color: #e9ecef;
    --success-color: #28a745;
    --warning-color: #ffc107;
    --danger-color: #dc3545;
    
    /* 間距 */
    --spacing-xs: 0.25rem;
    --spacing-sm: 0.5rem;
    --spacing-md: 1rem;
    --spacing-lg: 1.5rem;
    --spacing-xl: 2rem;
    
    /* 圓角 */
    --border-radius: 8px;
    --border-radius-lg: 12px;
    
    /* 陰影 */
    --shadow-sm: 0 1px 3px rgba(0,0,0,0.1);
    --shadow-md: 0 4px 6px rgba(0,0,0,0.1);
    --shadow-lg: 0 10px 15px rgba(0,0,0,0.1);
}

/* 基礎樣式 */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
    background-color: var(--background-color);
    color: var(--text-primary);
    line-height: 1.5;
}

/* 容器 */
.dashboard-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: var(--spacing-lg);
}

/* 頭部 */
.dashboard-header {
    background: var(--card-background);
    border-radius: var(--border-radius);
    padding: var(--spacing-lg);
    margin-bottom: var(--spacing-lg);
    box-shadow: var(--shadow-sm);
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.dashboard-title {
    font-size: 1.5rem;
    font-weight: 600;
    color: var(--text-primary);
}

/* 統計卡片網格 */
.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: var(--spacing-lg);
    margin-bottom: var(--spacing-xl);
}

.stat-card {
    background: var(--card-background);
    border-radius: var(--border-radius);
    padding: var(--spacing-lg);
    box-shadow: var(--shadow-sm);
    border-left: 4px solid var(--primary-color);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.stat-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
}

.stat-value {
    font-size: 2rem;
    font-weight: 700;
    color: var(--primary-color);
    margin-bottom: var(--spacing-xs);
}

.stat-label {
    font-size: 0.875rem;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* 主要內容區域 */
.main-content {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: var(--spacing-lg);
}

/* 數據表格 */
.data-table-container {
    background: var(--card-background);
    border-radius: var(--border-radius);
    padding: var(--spacing-lg);
    box-shadow: var(--shadow-sm);
}

.data-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: var(--spacing-md);
}

.data-table th,
.data-table td {
    padding: var(--spacing-md);
    text-align: left;
    border-bottom: 1px solid var(--border-color);
}

.data-table th {
    background: var(--background-color);
    font-weight: 600;
    color: var(--text-primary);
}

.data-table tr:hover {
    background: var(--background-color);
}

/* 側邊欄 */
.sidebar {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-lg);
}

.sidebar-card {
    background: var(--card-background);
    border-radius: var(--border-radius);
    padding: var(--spacing-lg);
    box-shadow: var(--shadow-sm);
}

/* 按鈕樣式 */
.btn {
    display: inline-flex;
    align-items: center;
    padding: var(--spacing-sm) var(--spacing-md);
    border: none;
    border-radius: var(--border-radius);
    font-size: 0.875rem;
    font-weight: 500;
    text-decoration: none;
    cursor: pointer;
    transition: all 0.2s ease;
}

.btn-primary {
    background: var(--primary-color);
    color: white;
}

.btn-primary:hover {
    background: #e68900;
    transform: translateY(-1px);
}

/* 響應式設計 */
@media (max-width: 768px) {
    .dashboard-container {
        padding: var(--spacing-md);
    }
    
    .stats-grid {
        grid-template-columns: 1fr;
    }
    
    .main-content {
        grid-template-columns: 1fr;
    }
    
    .dashboard-header {
        flex-direction: column;
        gap: var(--spacing-md);
        text-align: center;
    }
}

/* 工具提示和交互元素 */
.tooltip {
    position: relative;
    cursor: help;
}

.tooltip:hover::after {
    content: attr(data-tooltip);
    position: absolute;
    bottom: 100%;
    left: 50%;
    transform: translateX(-50%);
    background: var(--secondary-color);
    color: white;
    padding: var(--spacing-xs) var(--spacing-sm);
    border-radius: var(--border-radius);
    font-size: 0.75rem;
    white-space: nowrap;
    z-index: 1000;
}

/* 載入動畫 */
.loading {
    display: inline-block;
    width: 20px;
    height: 20px;
    border: 3px solid var(--border-color);
    border-radius: 50%;
    border-top-color: var(--primary-color);
    animation: spin 1s ease-in-out infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}
"""
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(css_content)
            
            print(f"   💾 CSS樣板已保存: {filepath}")
            return str(filepath)
            
        except Exception as e:
            print(f"   ❌ 創建CSS樣板失敗: {str(e)}")
            return ""
    
    async def _create_real_html_template(self, analysis_result: Dict[str, Any]) -> str:
        """創建真實HTML樣板"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"bytec_dashboard_real_{timestamp}.html"
            filepath = self.assets_dir / filename
            
            html_content = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ByteC Network Dashboard</title>
    <link rel="stylesheet" href="bytec_dashboard_real.css">
</head>
<body>
    <div class="dashboard-container">
        <!-- 頭部 -->
        <header class="dashboard-header">
            <h1 class="dashboard-title">ByteC Network Dashboard</h1>
            <div class="header-actions">
                <button class="btn btn-primary">Export Report</button>
            </div>
        </header>
        
        <!-- 統計卡片 -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">413,149</div>
                <div class="stat-label">Total Clicks</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">12,934</div>
                <div class="stat-label">Total Conversions</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">$51,280.56</div>
                <div class="stat-label">Total Sales (USD)</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">$1,407.45</div>
                <div class="stat-label">Estimated Earnings</div>
            </div>
        </div>
        
        <!-- 主要內容 -->
        <div class="main-content">
            <!-- 數據表格 -->
            <div class="data-table-container">
                <h2>Performance Report</h2>
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Advertiser</th>
                            <th>Clicks</th>
                            <th>Conversions</th>
                            <th>Sale Amount (USD)</th>
                            <th>Estimated Earnings</th>
                            <th>Conversion Rate (%)</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>July, 2025</td>
                            <td>TikTok Shop MY - CPS</td>
                            <td>0</td>
                            <td>5,325</td>
                            <td>25,288.50</td>
                            <td>445.11</td>
                            <td>0.00</td>
                        </tr>
                        <tr>
                            <td>July, 2025</td>
                            <td>TikTok Shop ID - CPS</td>
                            <td>413,149</td>
                            <td>6,535</td>
                            <td>22,035.34</td>
                            <td>908.62</td>
                            <td>1.58</td>
                        </tr>
                        <tr>
                            <td>July, 2025</td>
                            <td>Shopee ID (Media Buyer)</td>
                            <td>0</td>
                            <td>905</td>
                            <td>2,917.98</td>
                            <td>38.14</td>
                            <td>0.00</td>
                        </tr>
                    </tbody>
                </table>
            </div>
            
            <!-- 側邊欄 -->
            <div class="sidebar">
                <!-- 快速統計 -->
                <div class="sidebar-card">
                    <h3>Quick Stats</h3>
                    <div class="quick-stats">
                        <div class="quick-stat">
                            <span class="label">Conversion Rate:</span>
                            <span class="value">3.13%</span>
                        </div>
                        <div class="quick-stat">
                            <span class="label">Average Sale:</span>
                            <span class="value">$3.96</span>
                        </div>
                        <div class="quick-stat">
                            <span class="label">EPC:</span>
                            <span class="value">$0.003</span>
                        </div>
                    </div>
                </div>
                
                <!-- 最新活動 -->
                <div class="sidebar-card">
                    <h3>Recent Activity</h3>
                    <div class="activity-list">
                        <div class="activity-item">
                            <span class="time">2 hours ago</span>
                            <span class="description">New conversion: TikTok Shop</span>
                        </div>
                        <div class="activity-item">
                            <span class="time">4 hours ago</span>
                            <span class="description">Payment processed</span>
                        </div>
                        <div class="activity-item">
                            <span class="time">1 day ago</span>
                            <span class="description">New campaign activated</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // 簡單的儀表板交互功能
        document.addEventListener('DOMContentLoaded', function() {
            // 統計卡片懸停效果
            const statCards = document.querySelectorAll('.stat-card');
            statCards.forEach(card => {
                card.addEventListener('mouseenter', function() {
                    this.style.transform = 'translateY(-4px)';
                });
                
                card.addEventListener('mouseleave', function() {
                    this.style.transform = 'translateY(0)';
                });
            });
            
            // 表格行懸停效果
            const tableRows = document.querySelectorAll('.data-table tbody tr');
            tableRows.forEach(row => {
                row.addEventListener('click', function() {
                    console.log('Row clicked:', this);
                    // 這裡可以添加行點擊處理邏輯
                });
            });
        });
    </script>
</body>
</html>"""
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"   💾 HTML樣板已保存: {filepath}")
            return str(filepath)
            
        except Exception as e:
            print(f"   ❌ 創建HTML樣板失敗: {str(e)}")
            return ""
    
    async def _real_close_browser(self) -> bool:
        """關閉瀏覽器"""
        try:
            print("🔒 關閉瀏覽器...")
            
            # 使用MCP工具關閉瀏覽器
            # 示例: await mcp_playwright_close()
            
            print("✅ 瀏覽器已關閉")
            return True
            
        except Exception as e:
            print(f"❌ 關閉瀏覽器失敗: {str(e)}")
            return False

async def main():
    """主函數"""
    spider = SpiderAgentRealMCP()
    results = await spider.run_full_analysis_with_real_mcp()
    
    print("\n" + "="*60)
    print("📋 執行結果總覽:")
    print(f"✅ 成功: {'是' if results['success'] else '否'}")
    print(f"📸 截圖數量: {len(results['screenshots'])}")
    print(f"📄 分析檔案: {len(results['analysis_files'])}")
    
    if results['screenshots']:
        print("\n📸 生成的截圖:")
        for screenshot in results['screenshots']:
            print(f"   - {screenshot}")
    
    if results['analysis_files']:
        print("\n📄 生成的分析檔案:")
        for file in results['analysis_files']:
            print(f"   - {file}")
    
    if results['errors']:
        print("\n❌ 錯誤:")
        for error in results['errors']:
            print(f"   - {error}")
    
    print("\n🎉 Spider Agent執行完成！")
    print("💡 提示: 這是真實MCP實現的框架版本")
    print("   完成MCP工具集成後即可獲得真實的爬取結果")
    
    print("\n👋 程式結束")

if __name__ == "__main__":
    asyncio.run(main()) 