# ByteC Network Agent 架構設計

## 🏗️ 系統架構概覽

### Multi-Agent 架構設計
```
ByteC Network Agent
├── API Agent (數據收集)
├── Postback Agent (回傳處理)  
├── Data DMP Agent (數據管理)
├── Reporter Agent (報表生成)
├── Dashboard Agent (前端展示)
└── Spider Agent (網頁爬蟲)
```

## 🔧 技術棧

### 核心技術
- **語言**: Python 3.8+
- **數據庫**: PostgreSQL with asyncpg
- **API框架**: FastAPI
- **前端**: Streamlit
- **容器**: Docker

### 數據流架構
```
API Sources → API Agent → DMP Agent → Database
                                        ↓
Postback Sources → Postback Agent → DMP Agent
                                        ↓
                            Reporter Agent → Excel Reports
                                        ↓
                            Dashboard Agent → Web Interface
```

## 📊 數據模型

### 核心表結構
- `conversions`: 主要轉換數據表
- `conversions_api`: API 來源數據 (data_source_separation_enabled)
- `conversions_postback`: Postback 來源數據
- `partner_mapping`: 合作夥伴映射配置

### 配置管理
- `config.py`: 全局配置中心
- `PARTNER_SOURCE_MAPPING`: 合作夥伴映射
- `API_SECRETS`: API 密鑰管理
- `MOCKUP_MULTIPLIERS`: 數據倍數配置

## 🎯 設計原則

1. **模組化**: 每個 Agent 獨立運作
2. **可擴展**: 易於添加新的數據源和功能
3. **容錯性**: 完善的錯誤處理和重試機制
4. **性能**: 異步處理和批次操作
5. **監控**: 完整的日誌和指標收集 