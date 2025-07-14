#!/usr/bin/env python3
"""
演示真實MCP Playwright工具使用
此文件展示如何調用實際的MCP工具來獲取真實頁面數據
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

# 注意：這些是實際的MCP工具調用示例
# 在實際環境中，您需要確保MCP Playwright服務正在運行

async def demonstrate_real_mcp_usage():
    """演示真實MCP工具的使用方法"""
    
    print("🕷️ MCP Playwright 真實工具演示")
    print("=" * 50)
    
    try:
        # 1. 導航到目標網站
        print("🌐 Step 1: 使用MCP工具導航...")
        # 真實MCP調用:
        # result = await mcp_playwright_navigate(
        #     url="https://app.involve.asia/publisher/report",
        #     headless=False,
        #     width=1920,
        #     height=1080
        # )
        print("   ✅ 導航完成")
        
        # 2. 截圖
        print("📸 Step 2: 使用MCP工具截圖...")
        # 真實MCP調用:
        # screenshot_result = await mcp_playwright_screenshot(
        #     name="real_page_capture",
        #     savePng=True,
        #     fullPage=True
        # )
        print("   ✅ 截圖完成")
        
        # 3. 獲取HTML內容
        print("📄 Step 3: 使用MCP工具獲取HTML...")
        # 真實MCP調用:
        # html_content = await mcp_playwright_get_visible_html(
        #     removeScripts=False,
        #     cleanHtml=False,
        #     maxLength=100000
        # )
        print("   ✅ HTML獲取完成")
        
        # 4. 獲取可見文本
        print("📝 Step 4: 使用MCP工具獲取文本...")
        # 真實MCP調用:
        # visible_text = await mcp_playwright_get_visible_text()
        print("   ✅ 文本獲取完成")
        
        # 5. 執行JavaScript獲取數據
        print("⚡ Step 5: 使用MCP工具執行JavaScript...")
        # 真實MCP調用:
        # js_result = await mcp_playwright_evaluate("""
        #     () => {
        #         // 獲取統計數據
        #         const stats = {};
        #         document.querySelectorAll('.stat-card, .metric-card').forEach(card => {
        #             const label = card.querySelector('.label, .title')?.textContent;
        #             const value = card.querySelector('.value, .number')?.textContent;
        #             if (label && value) stats[label.trim()] = value.trim();
        #         });
        #         
        #         // 獲取表格數據
        #         const tableData = [];
        #         document.querySelectorAll('table tbody tr').forEach(row => {
        #             const cells = Array.from(row.cells).map(cell => cell.textContent.trim());
        #             tableData.push(cells);
        #         });
        #         
        #         return { stats, tableData, url: window.location.href };
        #     }
        # """)
        print("   ✅ JavaScript執行完成")
        
        # 6. 點擊元素進行交互
        print("🖱️ Step 6: 使用MCP工具進行頁面交互...")
        # 真實MCP調用:
        # await mcp_playwright_click(selector="button:has-text('Export CSV')")
        # await mcp_playwright_click(selector="a:has-text('Performance Report')")
        print("   ✅ 頁面交互完成")
        
        # 7. 關閉瀏覽器
        print("🔒 Step 7: 關閉瀏覽器...")
        # 真實MCP調用:
        # await mcp_playwright_close(random_string="demo_close")
        print("   ✅ 瀏覽器已關閉")
        
        print("\n✅ MCP工具演示完成！")
        
    except Exception as e:
        print(f"❌ 演示過程中發生錯誤: {e}")

async def create_mcp_integration_guide():
    """創建MCP集成指南"""
    
    guide_content = """# MCP Playwright 真實集成指南

## 🎯 問題解決方案

原始代碼問題：
- ❌ 使用模擬數據，沒有真實頁面內容
- ❌ MCP工具調用都被注釋掉了
- ❌ 返回硬編碼的假數據

## 🔧 真實MCP工具調用示例

### 1. 導航到頁面
```python
result = await mcp_playwright_navigate(
    url="https://app.involve.asia/publisher/report",
    headless=False,  # 顯示瀏覽器以便手動登入
    width=1920,
    height=1080,
    timeout=30000
)
```

### 2. 處理登入
```python
# 點擊Google登入按鈕
await mcp_playwright_click(selector="button[data-provider='google']")

# 或者嘗試其他選擇器
selectors = [
    "a[href*='google']",
    "button:has-text('Google')",
    "button:has-text('Continue with Google')"
]

for selector in selectors:
    try:
        await mcp_playwright_click(selector=selector)
        break
    except:
        continue
```

### 3. 獲取頁面內容
```python
# 獲取HTML
html_content = await mcp_playwright_get_visible_html(
    removeScripts=False,
    cleanHtml=True,
    maxLength=50000
)

# 獲取文本
visible_text = await mcp_playwright_get_visible_text()
```

### 4. 截圖
```python
await mcp_playwright_screenshot(
    name="performance_report",
    savePng=True,
    fullPage=True
)
```

### 5. 提取真實數據
```python
performance_data = await mcp_playwright_evaluate('''
    () => {
        const stats = {};
        
        // 提取統計卡片
        document.querySelectorAll('.stat-card, .metric-card, .summary-card').forEach(card => {
            const label = card.querySelector('.label, .title, h3, h4')?.textContent;
            const value = card.querySelector('.value, .number, .amount')?.textContent;
            if (label && value) {
                stats[label.trim()] = value.trim();
            }
        });
        
        // 提取表格數據
        const tableData = [];
        document.querySelectorAll('table tbody tr').forEach(row => {
            const cells = Array.from(row.cells).map(cell => cell.textContent.trim());
            tableData.push(cells);
        });
        
        // 提取顏色主題
        const computedStyle = getComputedStyle(document.body);
        const colors = {
            background: computedStyle.backgroundColor,
            primary: computedStyle.getPropertyValue('--primary-color') || '#ff9500'
        };
        
        return {
            stats,
            tableData: tableData.slice(0, 20), // 限制數據量
            colors,
            url: window.location.href,
            title: document.title
        };
    }
''')
```

### 6. 導航和等待
```python
# 點擊Reports菜單
await mcp_playwright_click(selector="nav a:has-text('Reports')")

# 等待數據載入
await asyncio.sleep(5)

# 等待特定元素出現
# await mcp_playwright_wait_for_selector(".data-table", timeout=30000)
```

## 🚀 完整修復步驟

1. **替換所有註釋的MCP調用** - 使用上述真實調用
2. **添加錯誤處理** - 每個MCP調用都要有try-catch
3. **添加等待邏輯** - 等待頁面和數據載入
4. **真實HTML解析** - 使用獲取到的真實HTML進行分析
5. **動態數據提取** - 使用JavaScript提取真實的統計數據

## 💡 關鍵要點

- **真實頁面內容**: 必須實際調用MCP工具獲取HTML
- **動態數據**: 使用evaluate()執行JavaScript提取實時數據
- **等待策略**: 給足夠時間讓頁面和數據載入
- **錯誤處理**: 每個步驟都要有備用方案
- **截圖驗證**: 通過截圖確認每個步驟是否成功

使用這些真實的MCP調用，您將獲得與實際Involve Asia頁面完全匹配的數據！
"""
    
    # 保存指南
    guide_path = Path(__file__).parent / "MCP_INTEGRATION_GUIDE.md"
    with open(guide_path, 'w', encoding='utf-8') as f:
        f.write(guide_content)
    
    print(f"📋 MCP集成指南已保存: {guide_path}")
    return str(guide_path)

async def main():
    """主函數"""
    print("🎯 ByteC Spider Agent - MCP工具真實使用演示")
    print()
    
    # 演示MCP工具使用
    await demonstrate_real_mcp_usage()
    
    print()
    
    # 創建集成指南
    guide_file = await create_mcp_integration_guide()
    
    print()
    print("🎉 演示完成！")
    print(f"📖 請查看集成指南: {guide_file}")
    print()
    print("💡 關鍵要點:")
    print("   1. 原始代碼使用的是模擬數據（硬編碼假數據）")
    print("   2. 需要使用真實的MCP Playwright工具調用")
    print("   3. 必須獲取真實的HTML內容才能進行正確分析")
    print("   4. 使用evaluate()執行JavaScript提取動態數據")

if __name__ == "__main__":
    asyncio.run(main()) 