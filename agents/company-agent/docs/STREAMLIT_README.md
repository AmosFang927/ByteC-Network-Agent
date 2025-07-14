# 公司財務AI助手 - Streamlit版本

## 🎯 概述

這是一個基於 Streamlit 的公司財務AI助手，專為 company-level 的財務數據查詢和分析而設計。它將原有的 HTML/CSS/JavaScript 前端重構為現代化的 Streamlit 應用，同時保持與現有 Flask 後端 API 的兼容性。

## 🚀 快速開始

### 1. 安裝依賴

```bash
pip install -r streamlit_requirements.txt
```

### 2. 啟動服務

```bash
python run_company_streamlit.py
```

系統將自動：
- 檢查必要的依賴包
- 啟動 Flask API 服務（如果未運行）
- 啟動 Streamlit 應用

### 3. 訪問應用

在瀏覽器中打開：`http://localhost:8501`

## 🏗️ 架構設計

### 技術棧
- **前端**: Streamlit + Plotly + Pandas
- **後端**: Flask API (現有系統)
- **數據庫**: PostgreSQL + WhoJDB
- **AI**: 現有的 CompanyManagerAgent

### 文件結構
```
├── agents/dashboard_agent/frontend/
│   └── company_ai_streamlit.py          # 主要Streamlit應用
├── streamlit_config.py                  # 配置文件
├── run_company_streamlit.py             # 啟動腳本
├── streamlit_requirements.txt           # 依賴文件
└── STREAMLIT_COMPANY_AI_README.md       # 說明文件
```

## 🌟 主要功能

### 1. 📊 財務儀表板
- **實時指標卡片**: 總收入、毛利率、轉化數、現金流
- **趨勢圖表**: 收入趨勢、合作夥伴表現
- **自動刷新**: 可配置的數據更新頻率

### 2. 💬 AI對話助手
- **自然語言查詢**: 支援中文財務問題
- **智能SQL生成**: 自動將問題轉換為SQL查詢
- **結果視覺化**: 自動生成圖表和表格
- **對話歷史**: 持久化的聊天記錄

### 3. 📈 深度分析
- **財務分析**: 多維度財務指標分析
- **合作夥伴分析**: 夥伴表現評估和排名
- **趨勢預測**: 基於歷史數據的預測分析

### 4. ⚡ 快速查詢
- 預設常用查詢按鈕
- 一鍵獲取關鍵財務指標
- 自定義查詢模板

## 🔧 配置選項

### 環境變量
```bash
# API配置
API_BASE_URL=http://localhost:5000

# WhoJDB配置
WHODB_BASE_URL=http://localhost:8080
WHODB_USERNAME=admin
WHODB_PASSWORD=password

# 數據庫配置
DB_HOST=localhost
DB_PORT=5432
DB_NAME=bytec_network
DB_USER=postgres
DB_PASSWORD=password

# Streamlit配置
STREAMLIT_PORT=8501
STREAMLIT_ADDRESS=0.0.0.0
```

### 配置文件 (`streamlit_config.py`)
- 應用基本設定
- API端點配置
- 圖表樣式配置
- 快速查詢模板
- 預設儀表板數據

## 🎨 界面特色

### 1. 現代化設計
- **響應式布局**: 適配不同屏幕尺寸
- **美觀的UI**: 使用Streamlit的現代化組件
- **自定義CSS**: 符合公司品牌的樣式

### 2. 交互體驗
- **側邊欄導航**: 快速查詢和系統狀態
- **標籤頁布局**: 清晰的功能分區
- **實時反饋**: 即時的加載狀態和錯誤提示

### 3. 數據可視化
- **Plotly圖表**: 交互式的數據視覺化
- **指標卡片**: 直觀的KPI展示
- **表格展示**: 結構化的數據呈現

## 📱 使用方法

### 1. AI對話
1. 在"AI對話"標籤頁中輸入問題
2. 系統自動生成SQL查詢
3. 顯示查詢結果和視覺化圖表
4. 查看完整的對話歷史

### 2. 財務儀表板
1. 切換到"財務儀表板"標籤頁
2. 查看實時財務指標
3. 分析收入趨勢和合作夥伴表現
4. 使用"重新加載"按鈕刷新數據

### 3. 快速查詢
1. 在側邊欄選擇預設查詢
2. 點擊按鈕自動執行查詢
3. 結果會顯示在AI對話界面

## 🔍 與HTML版本的差異

### 優勢
- **更好的用戶體驗**: Streamlit提供更流暢的交互
- **自動化圖表**: 無需手動處理Plotly配置
- **狀態管理**: 內建的session state管理
- **組件豐富**: 豐富的UI組件和布局選項

### 兼容性
- **API兼容**: 完全兼容現有的Flask API
- **功能等價**: 實現所有原有HTML版本的功能
- **數據格式**: 使用相同的數據格式和結構

## 🛠️ 開發指南

### 添加新功能
1. 在 `streamlit_config.py` 中添加配置
2. 在 `company_ai_streamlit.py` 中實現功能
3. 更新 `streamlit_requirements.txt` 如需新依賴

### 自定義樣式
1. 修改 `streamlit_config.py` 中的 `CUSTOM_CSS`
2. 使用 `st.markdown()` 應用自定義樣式
3. 配置 `CHART_CONFIG` 調整圖表外觀

### 添加新的快速查詢
1. 在 `streamlit_config.py` 的 `QUICK_QUERIES` 中添加
2. 系統會自動生成側邊欄按鈕
3. 無需修改其他代碼

## 📊 性能優化

### 1. 數據快取
- 使用 `st.cache_data` 快取API響應
- 配置適當的TTL時間
- 避免重複的數據請求

### 2. 異步處理
- 非阻塞的API調用
- 並行處理多個請求
- 優化長時間運行的查詢

### 3. 響應式設計
- 自適應布局
- 移動端友好
- 快速加載時間

## 🚀 部署建議

### 1. 本地開發
```bash
streamlit run agents/dashboard_agent/frontend/company_ai_streamlit.py --server.port=8501
```

### 2. 生產環境
```bash
# 使用啟動腳本
python run_company_streamlit.py

# 或直接使用Streamlit
streamlit run company_ai_streamlit.py --server.port=8501 --server.address=0.0.0.0
```

### 3. Docker部署
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY streamlit_requirements.txt .
RUN pip install -r streamlit_requirements.txt
COPY . .
CMD ["streamlit", "run", "agents/dashboard_agent/frontend/company_ai_streamlit.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

## 🔧 故障排除

### 1. 常見問題
- **API連接失敗**: 檢查Flask服務是否運行
- **依賴包缺失**: 運行 `pip install -r streamlit_requirements.txt`
- **端口衝突**: 修改 `streamlit_config.py` 中的端口設定

### 2. 日誌和調試
- 查看終端輸出的錯誤信息
- 使用 `st.write()` 進行調試
- 檢查瀏覽器開發者工具

### 3. 性能問題
- 使用 `st.cache_data` 快取數據
- 優化大數據集的處理
- 考慮分頁或限制數據量

## 🎯 未來規劃

### 1. 功能增強
- 更多的財務分析工具
- 高級的數據可視化
- 機器學習預測功能

### 2. 用戶體驗
- 個性化儀表板
- 自定義報表生成
- 離線數據功能

### 3. 集成擴展
- 更多數據源集成
- 第三方API支持
- 自動化報告發送

---

## 📞 技術支持

如有問題或建議，請聯繫開發團隊或查看相關文檔。

**注意**: 此版本專為 company-level 使用，其他頁面仍使用原有的 HTML/CSS/JavaScript 實現。 