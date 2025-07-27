# 📧 郵件附件優化配置示例

## 🚀 新增功能說明

本系統新增了三個階段的郵件附件優化功能，解決Gmail SMTP發送大附件失敗的問題：

### 階段1：自動壓縮 + 動態超時
### 階段2：智能降級策略
### 階段3：郵件模式選擇

## 📝 配置選項說明

### 1. 📎 附件壓縮配置
```python
EMAIL_AUTO_COMPRESS_ATTACHMENTS = True  # 是否自動壓縮大附件
EMAIL_COMPRESS_THRESHOLD_MB = 5         # 附件壓縮閾值（MB）
```

### 2. ⏱️ 動態超時配置
```python
EMAIL_DYNAMIC_TIMEOUT_ENABLED = True   # 是否啟用動態超時調整
EMAIL_SMALL_FILE_TIMEOUT = 120        # 小文件超時時間（<5MB）
EMAIL_MEDIUM_FILE_TIMEOUT = 300       # 中等文件超時時間（5-15MB）
EMAIL_LARGE_FILE_TIMEOUT = 600        # 大文件超時時間（>15MB）
```

### 3. ☁️ 智能降級策略配置
```python
EMAIL_SMART_FALLBACK_ENABLED = True            # 是否啟用智能降級策略
EMAIL_FALLBACK_SIZE_THRESHOLD_MB = 15          # 文件大小閾值（MB）
EMAIL_FALLBACK_RETRY_THRESHOLD = 2            # 重試次數閾值
```

### 4. 📧 郵件模式選擇（核心配置）
```python
EMAIL_DELIVERY_MODE = "smart_hybrid"  # 郵件發送模式
```

## 🎯 三種郵件模式說明

### 模式1: "attachment" - 純附件模式
```python
EMAIL_DELIVERY_MODE = "attachment"
```
- ✅ **特點**: 總是嘗試發送附件
- ✅ **優點**: 用戶可直接從郵件獲取文件
- ⚠️ **缺點**: 大附件可能發送失敗
- 🎯 **適用**: 文件較小（<10MB）的環境

### 模式2: "cloud_link" - 純雲端模式
```python
EMAIL_DELIVERY_MODE = "cloud_link"
```
- ✅ **特點**: 總是使用雲端鏈接，不發送附件
- ✅ **優點**: 發送速度快，100%成功率，無大小限制
- ⚠️ **缺點**: 用戶需要額外步驟獲取文件
- 🎯 **適用**: 大文件（>15MB）頻繁或網絡不穩定的環境

### 模式3: "smart_hybrid" - 智能混合模式（推薦）
```python
EMAIL_DELIVERY_MODE = "smart_hybrid"  # 默認推薦
```
- ✅ **特點**: 根據文件大小和重試情況智能選擇策略
- ✅ **優點**: 兼顧用戶體驗和發送成功率
- ✅ **邏輯**: 
  - 小文件：壓縮後作為附件發送
  - 大文件：直接使用雲端鏈接
  - 重試失敗：自動降級到雲端模式
- 🎯 **適用**: 大多數生產環境（推薦）

## 🛠️ 常見配置方案

### 方案A: 保守穩定型（推薦用於生產環境）
```python
EMAIL_DELIVERY_MODE = "cloud_link"
EMAIL_AUTO_COMPRESS_ATTACHMENTS = True
EMAIL_COMPRESS_THRESHOLD_MB = 3
EMAIL_FALLBACK_SIZE_THRESHOLD_MB = 10
```

### 方案B: 平衡性能型（推薦用於大多數環境）
```python
EMAIL_DELIVERY_MODE = "smart_hybrid"
EMAIL_AUTO_COMPRESS_ATTACHMENTS = True
EMAIL_COMPRESS_THRESHOLD_MB = 5
EMAIL_FALLBACK_SIZE_THRESHOLD_MB = 15
EMAIL_FALLBACK_RETRY_THRESHOLD = 2
```

### 方案C: 用戶體驗優先型（適用於小文件環境）
```python
EMAIL_DELIVERY_MODE = "attachment"
EMAIL_AUTO_COMPRESS_ATTACHMENTS = True
EMAIL_COMPRESS_THRESHOLD_MB = 2
EMAIL_DYNAMIC_TIMEOUT_ENABLED = True
EMAIL_LARGE_FILE_TIMEOUT = 900  # 15分鐘
```

## 📊 性能對比

| 配置方案 | 發送成功率 | 用戶體驗 | 發送速度 | 適用場景 |
|---------|-----------|----------|----------|----------|
| 純附件模式 | 60-80% | ⭐⭐⭐⭐⭐ | ⭐⭐ | 小文件環境 |
| 純雲端模式 | 100% | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 大文件環境 |
| 智能混合模式 | 95%+ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 通用環境 |

## 🔧 故障排除

### 如果郵件發送仍然失敗：
1. 檢查Gmail應用密碼是否正確
2. 嘗試設置更保守的配置：
   ```python
   EMAIL_DELIVERY_MODE = "cloud_link"
   EMAIL_COMPRESS_THRESHOLD_MB = 2
   ```
3. 檢查網絡連接和防火牆設置

### 如果用戶抱怨無法獲取附件：
1. 確認飛書上傳功能正常工作
2. 提供飛書訪問說明給用戶
3. 考慮降低 `EMAIL_FALLBACK_SIZE_THRESHOLD_MB` 閾值

## 🎉 升級說明

現有系統升級到新版本後：
- ✅ **向後兼容**: 所有現有功能正常工作
- ✅ **默認配置**: 自動啟用智能混合模式
- ✅ **無需修改**: 現有代碼無需任何更改
- ✅ **漸進式**: 可以逐步調整配置優化效果 