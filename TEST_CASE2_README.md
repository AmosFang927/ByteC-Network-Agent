# Test Case 2: DMP-Agent整合測試

## 📋 需求概述

Test Case 2實現了以下功能：
- 從agents/API-Agent拉取指定時間範圍數據
- 透過DMP-Agent儲存至Google Cloud SQL
- 支持命令行參數：`--days-ago` 和 `--platform`
- 不應用commission計算和mockup調整
- 直接存儲到現有的conversions表，區分platform

## 🏗️ 架構設計

### 核心組件

1. **database_manager.py** - 數據庫管理器
   - 從Reporter-Agent遷移的Google Cloud SQL存儲邏輯
   - 支持批量插入轉化數據
   - 自動創建platform、partner、source映射

2. **api_config_manager.py** - API配置管理器
   - 支持不同平台的API配置
   - 管理IAByteC等平台的特定配置

3. **api_data_fetcher.py** - API數據獲取器
   - 整合現有的involve_asia_client邏輯
   - 處理原始轉化數據格式化

4. **test_case2.py** - 主程序
   - 支持命令行參數
   - 整合所有組件的完整流程

## 📁 文件結構

```
ByteC-Network-Agent/
├── agents/
│   └── data_dmp_agent/
│       ├── database_manager.py      # 數據庫管理器
│       ├── api_config_manager.py    # API配置管理器
│       ├── api_data_fetcher.py      # API數據獲取器
│       └── main.py                  # DMP-Agent主程序
├── test_case2.py                    # Test Case 2主程序
└── TEST_CASE2_README.md            # 本文件
```

## 🚀 使用方法

### 1. 環境配置

```bash
# 設置環境變量
source ./setup_env.sh

# 或者手動設置
export INVOLVE_ASIA_API_KEY="your_api_key"
export INVOLVE_ASIA_SECRET="your_secret"
```

### 2. 基本使用

```bash
# 獲取2天前的IAByteC平台數據
python test_case2.py --days-ago 2 --platform IAByteC

# 獲取1天前的數據（默認）
python test_case2.py --days-ago 1

# 測試平台連接
python test_case2.py --test-connection --platform IAByteC

# 列出可用平台
python test_case2.py --list-platforms

# 只顯示統計信息，不獲取新數據
python test_case2.py --stats-only --platform IAByteC --days-ago 2
```

### 3. 參數說明

| 參數 | 說明 | 默認值 |
|------|------|--------|
| `--days-ago` | 獲取多少天前的數據 | 2 |
| `--platform` | API平台名稱 | IAByteC |
| `--test-connection` | 測試平台連接 | False |
| `--list-platforms` | 列出可用平台 | False |
| `--stats-only` | 只顯示統計信息 | False |

## 📊 支持的平台

- **IAByteC**: Involve Asia ByteC配置
- **IADefault**: Involve Asia默認配置

## 🔧 配置說明

### API配置
平台配置在`api_config_manager.py`中定義：

```python
'IAByteC': {
    'name': 'Involve Asia ByteC',
    'base_url': 'https://api.involve.asia',
    'api_key': os.getenv('INVOLVE_ASIA_API_KEY', ''),
    'secret': os.getenv('INVOLVE_ASIA_SECRET', ''),
    'partner_mapping': {
        'default_partner': 'ByteC',
        'source_prefix': 'BYTEC_'
    }
}
```

### 數據庫配置
數據庫連接配置在`database_manager.py`中：

```python
DB_CONFIG = {
    'host': '34.124.206.16',
    'port': 5432,
    'database': 'postback_db',
    'user': 'postback_admin',
    'password': 'ByteC2024PostBack_CloudSQL'
}
```

## 📈 數據流程

1. **API數據獲取**
   - 從Involve Asia API獲取指定日期的轉化數據
   - 根據平台配置處理數據格式

2. **數據處理**
   - 標準化轉化數據格式
   - 根據aff_sub映射partner
   - 不應用commission計算和mockup調整

3. **數據庫存儲**
   - 存儲到conversions表
   - 自動創建platform、partner、source映射
   - 支持重複數據更新

## 🗄️ 數據表結構

### conversions表
主要存儲轉化數據：
- `conversion_id`: 轉化唯一ID
- `platform_id`: 平台ID（區分不同平台）
- `partner_id`: 合作夥伴ID
- `source_id`: 來源ID
- `usd_sale_amount`: 銷售金額
- `usd_payout`: 佣金金額
- `raw_data`: 原始數據JSON

### 映射表
- `platforms`: 平台映射
- `business_partners`: 合作夥伴映射
- `sources`: 來源映射

## 📝 示例輸出

```
================================================================================
🧪 Test Case 2: DMP-Agent整合測試
================================================================================
功能: 從API-Agent拉取數據，透過DMP-Agent存儲至Google Cloud SQL
支持參數:
  --days-ago 2      : 獲取2天前的數據
  --platform IAByteC: 指定平台為IAByteC
  --test-connection : 測試平台連接
  --list-platforms  : 列出可用平台
  --stats-only      : 只顯示統計信息
================================================================================

2025-01-15 10:30:00 - __main__ - INFO - 🚀 正在初始化Test Case 2 DMP-Agent...
2025-01-15 10:30:01 - __main__ - INFO - ✅ Test Case 2 DMP-Agent初始化成功
2025-01-15 10:30:01 - __main__ - INFO -    - 數據庫連接: 53660 條轉化記錄
2025-01-15 10:30:01 - __main__ - INFO -    - 合作夥伴: 15 個
2025-01-15 10:30:01 - __main__ - INFO -    - 平台: 3 個
2025-01-15 10:30:01 - __main__ - INFO - 🚀 開始Test Case 2 DMP-Agent數據處理流程
2025-01-15 10:30:01 - __main__ - INFO -    - 平台: IAByteC
2025-01-15 10:30:01 - __main__ - INFO -    - 天數: 2 天前
2025-01-15 10:30:01 - __main__ - INFO - 🔄 開始處理平台數據: IAByteC (days_ago=2)
2025-01-15 10:30:01 - __main__ - INFO - 📥 正在從API獲取轉化數據...
2025-01-15 10:30:15 - __main__ - INFO - ✅ 成功獲取 1250 條轉化數據
2025-01-15 10:30:15 - __main__ - INFO - 💾 正在存儲轉化數據到Google Cloud SQL...
2025-01-15 10:30:18 - __main__ - INFO - ✅ 成功存儲 1250 條轉化數據
2025-01-15 10:30:18 - __main__ - INFO - ✅ 平台數據處理完成: IAByteC
2025-01-15 10:30:18 - __main__ - INFO -    - 獲取: 1250 條記錄
2025-01-15 10:30:18 - __main__ - INFO -    - 存儲: 1250 條記錄
2025-01-15 10:30:18 - __main__ - INFO -    - 總金額: $5,000.00 USD
2025-01-15 10:30:18 - __main__ - INFO - ✅ 數據處理成功完成
2025-01-15 10:30:18 - __main__ - INFO -    - 獲取記錄: 1250 條
2025-01-15 10:30:18 - __main__ - INFO -    - 存儲記錄: 1250 條
2025-01-15 10:30:18 - __main__ - INFO -    - 總銷售金額: $5,000.00 USD
2025-01-15 10:30:18 - __main__ - INFO -    - 總佣金金額: $150.00 USD
2025-01-15 10:30:18 - __main__ - INFO -    - 平均銷售金額: $4.00 USD
2025-01-15 10:30:18 - __main__ - INFO - 📋 Test Case 2 DMP-Agent執行摘要:
2025-01-15 10:30:18 - __main__ - INFO -    - 總獲取數量: 1250 條記錄
2025-01-15 10:30:18 - __main__ - INFO -    - 總存儲數量: 1250 條記錄
2025-01-15 10:30:18 - __main__ - INFO -    - 沒有錯誤
```

## 🔍 測試和驗證

### 1. 測試平台連接
```bash
python test_case2.py --test-connection --platform IAByteC
```

### 2. 查看統計信息
```bash
python test_case2.py --stats-only --platform IAByteC --days-ago 2
```

### 3. 驗證數據存儲
```bash
python query_conversion_stats.py 2025-01-13
```

## 🛠️ 故障排除

### 常見問題

1. **API Key配置錯誤**
   ```
   ❌ 平台配置無效: IAByteC
   ```
   解決：檢查環境變量設置

2. **數據庫連接失敗**
   ```
   ❌ 數據庫不健康: connection failed
   ```
   解決：檢查網絡連接和數據庫配置

3. **沒有獲取到數據**
   ```
   ⚠️ 沒有獲取到轉化數據: IAByteC
   ```
   解決：檢查日期範圍或API配置

### 日誌文件
- `test_case2.log`: 主程序日誌
- `dmp_agent.log`: DMP-Agent日誌

## 🎯 關鍵特性

✅ **已實現**
- 從API-Agent拉取指定時間範圍數據
- 透過DMP-Agent存儲至Google Cloud SQL
- 支持 --days-ago 和 --platform 參數
- 直接存儲到conversions表並區分platform
- 不應用commission計算和mockup調整

✅ **技術亮點**
- 異步處理提升性能
- 完整的錯誤處理和日誌記錄
- 支持重複數據更新
- 自動創建映射關係
- 模塊化設計便於擴展

## 📞 支持

如需幫助，請檢查：
1. 環境變量配置
2. API Key有效性
3. 數據庫連接狀態
4. 日誌文件錯誤信息 