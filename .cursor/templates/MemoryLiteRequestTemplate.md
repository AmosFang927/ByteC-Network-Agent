# 🧠 Memory Lite 模式請求模板

## 📋 標準請求格式

### 基本模板
```
[ByteC Network Agent - Memory Lite]
技術棧：Python 3.8+ + PostgreSQL + asyncpg + FastAPI
架構：Multi-Agent 系統 (API/Postback/DMP/Reporter/Dashboard)

【任務】：[明確的任務描述]
【檔案】：[完整路徑，如 agents/data_dmp_agent/database_manager.py]
【技術】：[具體技術要求和約束]
【配置】：[相關配置信息]
【期望】：[預期結果和輸出格式]
```

## 🎯 常用請求模板

### 1. Debug 錯誤修復
```
[ByteC Agent Debug - Memory Lite]
環境：Python 3.8 + PostgreSQL + asyncpg
專案：ByteC Network Agent (Multi-Agent 架構)

【錯誤檔案】：agents/[agent_name]/[filename.py]
【錯誤信息】：[完整錯誤堆疊跟踪]
【執行命令】：PYTHONUNBUFFERED=1 python [完整命令]
【預期行為】：[系統應該如何正常工作]
【修復目標】：[要解決的具體問題]

相關配置：
- MP映射：aff_sub LIKE 'MP%' AND source = 'RAMPUP'
- API限制：REQUEST_DELAY = 0.5 秒
- 資料庫：PostgreSQL with asyncpg
```

### 2. 功能開發
```
[ByteC Agent 功能開發 - Memory Lite]
專案：ByteC Network Agent (Multi-Agent 系統)
技術棧：Python + PostgreSQL + FastAPI

【新功能】：[功能詳細描述]
【目標檔案】：[要修改的具體檔案路徑]
【技術要求】：[使用的技術和框架]
【整合需求】：[與現有系統的整合方式]
【測試需求】：[如何驗證功能正確性]

專案結構：
- agents/api_agent/: API 數據收集
- agents/data_dmp_agent/: 數據管理
- agents/reporter_agent/: 報表生成
- config.py: 全域配置管理
```

### 3. 配置修改
```
[ByteC Agent 配置修改 - Memory Lite]
專案：ByteC Network Agent
配置系統：統一使用 config.py

【配置檔案】：config.py (專案根目錄)
【修改項目】：[具體要修改的配置參數]
【修改原因】：[為什麼需要這個修改]
【影響範圍】：[這個修改會影響哪些 Agent]
【驗證方法】：[如何確認修改生效]

重要配置區塊：
- PARTNER_SOURCE_MAPPING: 合作夥伴映射
- API_SECRETS: API 密鑰管理
- MOCKUP_MULTIPLIERS: 模擬倍數
- REQUEST_DELAY: API 請求間隔
```

### 4. 數據查詢/報表
```
[ByteC Agent 數據操作 - Memory Lite]
數據系統：PostgreSQL + asyncpg
報表系統：Excel + openpyxl

【操作類型】：[查詢/報表生成/數據清理]
【目標 Agent】：[reporter_agent/data_dmp_agent]
【數據範圍】：[日期範圍、合作夥伴等]
【輸出格式】：[Excel/JSON/控制台輸出]
【執行命令】：PYTHONUNBUFFERED=1 python [完整命令]

合作夥伴映射：
- MP: aff_sub LIKE 'MP%' AND source = 'RAMPUP'
- MKK: [具體映射規則]
- ByteC: [處理所有數據的特殊合作夥伴]
```

## 🔧 關鍵信息速查

### ByteC 專案核心信息
```
專案名稱：ByteC Network Agent
架構類型：Multi-Agent 系統
技術棧：Python 3.8+ + PostgreSQL + FastAPI + Streamlit

Agent 列表：
- api_agent: API 數據收集
- postback_agent: 回傳處理
- data_dmp_agent: 數據管理平台
- reporter_agent: 報表生成
- dashboard_agent: 前端展示
- spider_agent: 網頁爬蟲

核心檔案：
- config.py: 全域配置中心
- agents/*/database_manager.py: 數據庫操作
- agents/*/main.py: Agent 主程式入口
```

### 常用配置參數
```
# API 配置
REQUEST_DELAY = 0.5  # API 請求間隔

# 合作夥伴映射
PARTNER_SOURCE_MAPPING = {
    "MP": {"sources": ["RAMPUP"], "pattern": r"MP.*"}
}

# 模擬倍數
MOCKUP_MULTIPLIERS = {
    "MP": 0.9,  # MP 合作夥伴使用 90% 倍數
}

# 數據庫連接
使用 asyncpg 連接 PostgreSQL
支援連接池和異步操作
```

### 標準執行命令
```bash
# DMP Agent 查詢
PYTHONUNBUFFERED=1 python agents/data_dmp_agent/main.py --query --partner MP --start-date YYYY-MM-DD

# Reporter Agent 報表
PYTHONUNBUFFERED=1 python agents/reporter_agent/main.py --partners MP,MKK --days 3

# 測試 API 連接
PYTHONUNBUFFERED=1 python test_api_connection.py

# Debug 腳本
PYTHONUNBUFFERED=1 python -u debug_script.py
```

## 💡 Memory Lite 最佳實踐

1. **每次都當作全新對話** - 不依賴之前的上下文
2. **信息前置** - 把最重要的信息放在請求開頭
3. **路徑明確** - 總是使用完整的檔案路徑
4. **配置內聯** - 在請求中直接提供必要配置
5. **結果具體** - 明確說明期望的輸出格式

記住：Memory Lite 模式下，詳細明確比簡潔更重要！🚀 