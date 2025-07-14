# 🕷️ ByteC Spider Agent

基於Playwright MCP的網站結構爬取和分析工具，專為爬取Involve Asia結構並改進ByteC Network Dashboard而設計。

## 📁 項目結構

```
agents/spider_agent/
├── __init__.py                     # 模組初始化
├── config.py                      # 設定檔
├── main.py                        # 主程式（框架版本）
├── main_with_mcp.py              # MCP整合版本
├── requirements.txt               # 依賴套件
├── auth/
│   ├── __init__.py
│   └── google_sso_handler.py     # Google SSO登入處理
├── crawler/
│   ├── __init__.py
│   ├── playwright_client.py      # Playwright客戶端
│   └── structure_analyzer.py     # 結構分析器
├── output/
│   ├── __init__.py
│   ├── structure_exporter.py     # 結構匯出工具
│   ├── screenshots/              # 截圖存放目錄
│   ├── structure/                # 分析結果存放目錄
│   └── assets/                   # 生成的樣板存放目錄
└── README.md                     # 說明文檔
```

## 🎯 主要功能

### 1. Google SSO自動登入
- 自動偵測Google登入按鈕
- 支援多種登入選擇器
- 智慧等待登入完成

### 2. 網站導航
- 自動點擊"Report"選單
- 導航到"Performance Report"
- 多重選擇器容錯機制

### 3. 頁面結構分析
- **HTML結構**: 語義化元素、無障礙性分析
- **CSS樣式**: 外部樣式表、響應式設計、CSS變數
- **JavaScript**: 框架檢測、事件監聽器分析
- **頁面佈局**: 視窗尺寸、區塊分佈
- **導航結構**: 選單項目、麵包屑
- **表單分析**: 輸入類型、驗證規則
- **互動元素**: 按鈕、模態框、下拉選單

### 4. 多格式匯出
- **JSON**: 結構化分析數據
- **HTML**: 美觀的分析報告
- **Markdown**: 文檔格式報告
- **CSS**: 基於分析的樣式樣板

### 5. Dashboard樣板生成
- 基於Involve Asia設計的CSS樣板
- 響應式HTML Dashboard樣板
- 可直接用於ByteC Network Dashboard

## 🚀 使用方法

### 方法1: 框架版本（需整合MCP工具）

```bash
cd agents/spider_agent
python main.py
```

### 方法2: MCP整合版本（實際爬取）

```bash
cd agents/spider_agent
python main_with_mcp.py
```

## 🔧 MCP工具整合

要使用實際的MCP Playwright工具，需要在以下位置添加實際的工具調用：

### 在 `main_with_mcp.py` 中整合

1. **導航工具**
```python
# 替換 _mcp_navigate_to_target 方法中的示意代碼
# 使用實際的 mcp_Playwright_playwright_navigate 工具
```

2. **截圖工具**
```python
# 替換 _mcp_take_screenshot 方法中的示意代碼
# 使用實際的 mcp_Playwright_playwright_screenshot 工具
```

3. **點擊工具**
```python
# 替換點擊相關方法中的示意代碼
# 使用實際的 mcp_Playwright_playwright_click 工具
```

4. **獲取內容工具**
```python
# 替換內容獲取方法中的示意代碼
# 使用實際的 mcp_Playwright_playwright_get_visible_html 工具
```

## 📊 輸出結果

### 截圖檔案
- `01_initial_page.png` - 初始頁面
- `02_after_login.png` - 登入後頁面
- `03_performance_report.png` - Performance Report頁面

### 分析報告
- `analysis_report_[timestamp].json` - 完整分析數據
- `analysis_report_[timestamp].html` - 可視化報告
- `analysis_report_[timestamp].md` - 文檔格式報告

### Dashboard樣板
- `bytec_dashboard_[timestamp].css` - 樣式樣板
- `bytec_dashboard_[timestamp].html` - HTML樣板

## 🎨 生成的樣板特色

### CSS樣板特點
- **響應式設計**: 支援多種設備尺寸
- **現代化樣式**: 使用CSS變數和Flexbox/Grid
- **組件化**: 卡片、按鈕、導航等可重用組件
- **基於分析**: 採用Involve Asia的設計模式

### HTML樣板特點
- **語義化HTML**: 使用正確的HTML5標籤
- **無障礙性**: 支援screen reader和鍵盤導航
- **模組化結構**: 易於擴展和維護
- **實用功能**: 統計卡片、圖表區域、數據表格

## 🔧 設定說明

### config.py 重要設定

```python
# 目標網站
TARGET_URL = "https://app.involve.asia/publisher/report"
LOGIN_URL = "https://app.involve.asia/login"

# 輸出目錄
OUTPUT_DIR = "agents/spider_agent/output"

# 瀏覽器設定
BROWSER_CONFIG = {
    "headless": False,  # 設為True可隱藏瀏覽器
    "viewport": {"width": 1920, "height": 1080}
}
```

## 📋 依賴套件

```
playwright>=1.40.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
cssutils>=2.7.0
requests>=2.31.0
pillow>=10.0.0
selenium>=4.15.0
```

## 🚨 注意事項

1. **登入憑證**: 需要有效的Google帳號來登入Involve Asia
2. **網絡連接**: 確保網絡連接穩定
3. **瀏覽器權限**: 可能需要允許瀏覽器彈出視窗
4. **反爬蟲**: 遵守網站的robots.txt和使用條款
5. **頻率限制**: 避免過於頻繁的請求

## 🔄 與ByteC Dashboard整合

### 步驟1: 複製生成的樣式
```bash
cp agents/spider_agent/output/assets/bytec_dashboard_*.css agents/dashboard_agent/frontend/static/css/
```

### 步驟2: 參考HTML結構
使用生成的HTML樣板改進現有的dashboard.html

### 步驟3: 應用設計模式
參考分析報告中的設計模式來優化用戶體驗

## 🐛 故障排除

### 常見問題

1. **找不到登入按鈕**
   - 檢查網站是否更新了選擇器
   - 在config.py中更新選擇器

2. **登入失敗**
   - 確認Google帳號有效
   - 檢查是否有二次驗證

3. **截圖失敗**
   - 確認輸出目錄權限
   - 檢查瀏覽器是否正常運行

4. **分析不完整**
   - 等待頁面完全載入
   - 檢查網絡連接

## 📞 支援

如有問題或建議，請聯繫開發團隊或查看項目文檔。

## 📄 授權

此工具僅供ByteC Network內部使用，請遵守相關使用條款。 