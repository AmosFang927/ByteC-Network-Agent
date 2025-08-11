# Unified Field Mapping 使用範例

## 概述

本項目已實現以下兩個主要需求：

1. **Google Sheets 只讀模式** - 確保只能讀取數據，不能寫入
2. **所有 unified field 為必須呈現欄** - 確保所有 unified field 都出現在輸出中，即使原始 field 為空

## 功能特點

### 1. Google Sheets 只讀模式

- 修改了 `GoogleSheetsManager` 類，使用只讀權限
- 移除了所有寫入操作
- 使用 `spreadsheets.readonly` 和 `drive.readonly` 權限範圍

### 2. Unified Field 映射

- 創建了 `UnifiedFieldMapper` 類來處理統一欄位映射
- 定義了 30 個必須的 unified fields
- 確保所有 unified fields 都出現在輸出中，即使原始 field 為空
- 提供適當的默認值（空字符串、0、0.0 等）

## 使用範例

### 基本使用

```python
from agents.data_dmp_agent.field_mapping_manager import FieldMappingManager
from agents.data_dmp_agent.unified_field_mapper import UnifiedFieldMapper

# 創建管理器
manager = FieldMappingManager()

# 創建測試數據
import pandas as pd
data = {
    'Conversion ID': ['conv_001', 'conv_002'],
    'Offer Name': ['Test Offer 1', 'Test Offer 2'],
    'Sale Amount (USD)': ['100.50', '200.75']
}
df = pd.DataFrame(data)

# 映射到統一欄位格式
platform = "involve_asia"
unified_df, mapping_info = manager.map_dataframe_columns(df, platform)

print(f"映射後欄位數: {len(unified_df.columns)}")
print(f"必須欄位數: {mapping_info['validation']['total_required_fields']}")
print(f"存在欄位數: {mapping_info['validation']['present_count']}")
```

### 直接使用 UnifiedFieldMapper

```python
from agents.data_dmp_agent.unified_field_mapper import UnifiedFieldMapper

# 創建映射器
mapper = UnifiedFieldMapper()

# 定義欄位映射
field_mappings = {
    'conversion_id': 'Conversion ID',
    'offer_name': 'Offer Name',
    'sale_amount': 'Sale Amount (USD)',
    'datetime_conversion': 'Conversion Date'
}

# 執行映射
unified_df = mapper.map_dataframe_to_unified_fields(df, field_mappings)

# 驗證結果
validation_result = mapper.validate_unified_fields(unified_df)
print(f"驗證通過: {validation_result['is_valid']}")
```

### Google Sheets 只讀模式

```python
from agents.data_dmp_agent.google_sheets_manager import GoogleSheetsManager

# 創建只讀管理器
manager = GoogleSheetsManager(credentials_file="path/to/credentials.json")

# 測試連接
spreadsheet_id = "your_spreadsheet_id"
connection_success = manager.test_connection(spreadsheet_id)

if connection_success:
    # 讀取欄位映射
    mappings = manager.get_field_mappings(
        spreadsheet_id=spreadsheet_id,
        sheet_name="FieldMappings",
        range_name="A1:Z1000"
    )
    print("成功從 Google Sheets 讀取映射")
else:
    print("Google Sheets 連接失敗")
```

## 必須的 Unified Fields

系統定義了以下 30 個必須的 unified fields：

### 核心欄位
- `conversion_id` - 轉化 ID
- `offer_id` - Offer ID
- `offer_name` - Offer 名稱
- `order_id` - 訂單 ID
- `datetime_conversion` - 轉化時間
- `sale_amount` - 銷售金額
- `payout` - 支付金額
- `currency` - 貨幣
- `conversion_status` - 轉化狀態

### 合作夥伴欄位
- `partner` - 合作夥伴
- `platform` - 平台
- `source` - 來源

### 追蹤欄位
- `aff_sub` - 聯盟追蹤參數
- `aff_sub1` - 聯盟追蹤參數 1
- `aff_sub2` - 聯盟追蹤參數 2
- `aff_sub3` - 聯盟追蹤參數 3
- `aff_sub4` - 聯盟追蹤參數 4
- `aff_sub5` - 聯盟追蹤參數 5

### 廣告主欄位
- `adv_sub` - 廣告主追蹤參數
- `adv_sub1` - 廣告主追蹤參數 1
- `adv_sub2` - 廣告主追蹤參數 2
- `adv_sub3` - 廣告主追蹤參數 3
- `adv_sub4` - 廣告主追蹤參數 4
- `adv_sub5` - 廣告主追蹤參數 5

### 其他欄位
- `click_id` - 點擊 ID
- `merchant_id` - 商家 ID
- `commission_rate` - 佣金率
- `tenant_id` - 租戶 ID
- `raw_data` - 原始數據

## 欄位類型映射

系統會根據欄位類型提供適當的默認值：

- **string** - 空字符串 `''`
- **integer** - 整數 `0`
- **decimal** - 浮點數 `0.0`
- **datetime** - `pd.NaT`
- **json** - 空 JSON 對象 `'{}'`

## 數據轉換

系統支援以下數據轉換：

### 貨幣轉換
```python
# 移除貨幣符號和逗號，轉換為數值
transformations = {
    'sale_amount': {'type': 'currency', 'currency': 'USD'}
}
```

### 日期轉換
```python
# 轉換日期格式
transformations = {
    'datetime_conversion': {'type': 'date', 'format': '%Y-%m-%d'}
}
```

### 百分比轉換
```python
# 轉換百分比為小數
transformations = {
    'commission_rate': {'type': 'percentage'}
}
```

## 測試

運行測試腳本來驗證功能：

```bash
python test_unified_field_mapping.py
```

測試包括：
1. Unified Field Mapper 基本功能
2. Field Mapping Manager 整合
3. Google Sheets 只讀模式
4. 空欄位處理

## 配置

### Google Sheets 配置

在 `config/field_mapping_config.json` 中配置：

```json
{
  "google_sheets": {
    "enabled": true,
    "credentials_file": "path/to/credentials.json",
    "spreadsheet_id": "your_spreadsheet_id",
    "sheet_name": "FieldMappings",
    "range": "A1:Z1000",
    "cache_duration": 300
  }
}
```

### 本地配置

如果 Google Sheets 不可用，系統會使用本地配置：

```json
{
  "platforms": {
    "involve_asia": {
      "field_mappings": {
        "conversion_id": "Conversion ID",
        "offer_name": "Offer Name",
        "sale_amount": "Sale Amount (USD)"
      },
      "data_transformations": {
        "sale_amount": {"type": "currency", "currency": "USD"}
      }
    }
  }
}
```

## 錯誤處理

系統提供完善的錯誤處理：

1. **Google Sheets 連接失敗** - 自動降級到本地配置
2. **欄位映射缺失** - 自動添加空的 unified field
3. **數據轉換失敗** - 保留原始數據並記錄警告
4. **驗證失敗** - 提供詳細的錯誤信息

## 性能優化

1. **緩存機制** - Google Sheets 數據緩存 5 分鐘
2. **批量處理** - 支援大量數據的批量映射
3. **延遲轉換** - 只在需要時進行數據轉換
4. **內存優化** - 避免不必要的數據複製

## 日誌記錄

系統提供詳細的日誌記錄：

```python
import logging
logging.basicConfig(level=logging.INFO)

# 查看映射過程
logger = logging.getLogger('agents.data_dmp_agent.field_mapping_manager')
```

日誌包括：
- 映射進度
- 驗證結果
- 錯誤信息
- 性能統計 