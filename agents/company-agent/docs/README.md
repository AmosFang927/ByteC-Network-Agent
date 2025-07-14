# 公司財務AI助手 - Company Finance AI Assistant

## 🎯 概述

這是一個基於 WhoDB 和 AI 技術的智能公司財務分析系統，專為 ByteC Network Agent 的 company-level 財務管理需求設計。

## 🏗️ 架構

### 模塊結構
```
agents/company-agent/
├── backend/
│   ├── main.py   # 核心AI代理
│   └── company_ai_api.py     # Flask API 服務
├── frontend/
│   ├── streamlit_app.py      # Streamlit 界面
│   └── templates/
│       └── company_ai_chat.html  # HTML 界面
├── config/
│   └── streamlit_config.py   # 配置文件
├── scripts/
│   ├── run_streamlit.py      # Streamlit 啟動腳本
│   └── run_company_ai_assistant.py  # API 啟動腳本
├── docs/
│   ├── README.md            # 此文件
│   └── STREAMLIT_README.md  # Streamlit 使用說明
├── requirements.txt         # 依賴包
└── test_app.py             # 測試腳本
```

## 🚀 快速開始

### 1. 安裝依賴

```bash
cd agents/company-agent
pip install -r requirements.txt
```

### 2. 啟動服務

#### 方式一：啟動Streamlit應用
```bash
python scripts/run_streamlit.py
```

#### 方式二：啟動Flask API
```bash
python scripts/run_company_ai_assistant.py
```

### 3. 訪問應用

- **Streamlit UI**: http://localhost:8501
- **Flask API**: http://localhost:5000

## 🌟 主要功能

### 1. 📊 財務儀表板
- 實時財務指標顯示
- 收入趨勢分析
- 合作夥伴表現評估
- 現金流監控

### 2. 💬 AI對話助手
- 自然語言財務查詢
- 智能SQL生成
- 中文問題理解
- 結果視覺化

### 3. 🔧 WhoDB整合
- 直接數據庫查詢
- 表結構分析
- 查詢結果快取
- 連接狀態監控

## 🎨 技術棧

### 前端
- **Streamlit**: 現代化UI框架
- **Plotly**: 交互式圖表
- **Pandas**: 數據處理
- **HTML/CSS/JS**: 傳統Web界面

### 後端
- **Flask**: Web API框架
- **AsyncIO**: 異步處理
- **aiohttp**: HTTP客戶端
- **WhoDB**: 數據庫管理界面

### 數據庫
- **PostgreSQL**: 主數據庫
- **asyncpg**: 異步數據庫驅動
- **psycopg2**: 同步數據庫驅動

## 🔧 配置

### 環境變量
```bash
# API配置
export API_BASE_URL="http://localhost:5000"

# WhoDB配置
export WHODB_BASE_URL="http://localhost:8080"
export WHODB_USERNAME="admin"
export WHODB_PASSWORD="password"

# 數據庫配置
export DB_HOST="localhost"
export DB_PORT="5432"
export DB_NAME="bytec_network"
export DB_USER="postgres"
export DB_PASSWORD="password"

# Streamlit配置
export STREAMLIT_PORT="8501"
export STREAMLIT_ADDRESS="0.0.0.0"
```

## 📱 使用指南

### Streamlit界面
1. 打開 http://localhost:8501
2. 使用側邊欄快速查詢
3. 在聊天界面輸入問題
4. 查看財務儀表板
5. 分析深度報告

### Flask API
1. 查看API文檔：http://localhost:5000/api/health
2. 使用POST請求查詢：`/api/company-ai-query`
3. 獲取儀表板數據：`/api/financial-dashboard`
4. 查看對話歷史：`/api/conversation-history`

## 🧪 測試

### 運行測試
```bash
python test_app.py
```

### 測試內容
- 依賴包檢查
- 配置文件驗證
- API連接測試
- 功能完整性測試

## 🛠️ 開發

### 添加新功能
1. 修改配置文件 `config/streamlit_config.py`
2. 更新後端邏輯 `main.py`
3. 調整前端界面 `frontend/streamlit_app.py`
4. 測試和部署

### 自定義查詢
1. 在配置文件中添加快速查詢
2. 擴展AI查詢解析器
3. 更新SQL模板生成器

## 📊 監控

### 系統狀態
- 實時服務監控
- 數據庫連接狀態
- WhoDB服務狀態
- API響應時間

### 性能指標
- 查詢響應時間
- 數據處理速度
- 內存使用量
- 併發處理能力

## 🔒 安全

### 數據保護
- 敏感信息加密
- 安全的數據庫連接
- API訪問控制
- 日誌記錄

### 權限管理
- 用戶認證
- 角色授權
- 操作審計
- 數據訪問控制

## 🚀 部署

### 本地部署
```bash
# 啟動完整服務
python scripts/run_company_ai_assistant.py

# 單獨啟動Streamlit
python scripts/run_streamlit.py
```

### 生產部署
```bash
# 使用Docker
docker build -t company-ai-assistant .
docker run -p 5000:5000 -p 8501:8501 company-ai-assistant

# 使用docker-compose
docker-compose up -d
```

## 📚 文檔

- [Streamlit版本詳細說明](STREAMLIT_README.md)
- [API文檔](../docs/API.md)
- [配置指南](../docs/CONFIG.md)

## 🤝 支援

如需技術支援或功能建議，請聯繫開發團隊或創建issue。

---

**版本**: 1.0.0  
**最後更新**: 2024-01-20  
**作者**: ByteC Network Agent 開發團隊 