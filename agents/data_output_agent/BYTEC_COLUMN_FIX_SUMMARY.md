# ByteC Partner+Source 匯總列名修復總結

## 問題描述

ByteC 郵件模板中的 Partner+Source 匯總功能出現錯誤：
```
Partner+Source汇总: ❌ 缺少必要列: Partner列=None, Source列=None
```

## 根本原因

ByteC Excel 文件的列名結構與標準 Partner 報告不同，缺少標準的 Partner 和 Source 列。

## 修復方案

### 1. 增強列名檢測邏輯

**修改文件**: `agents/data_output_agent/email_sender.py`

**修改方法**: `_calculate_partner_source_summary()`

#### 修改前:
```python
# 找到Partner和Source列
for col in ['Partner', 'partner', 'Partner Name']:
    if col in df.columns:
        partner_column = col
        break

for col in ['Source', 'source', 'aff_sub1', 'Source Name']:
    if col in df.columns:
        source_column = col
        break

if not partner_column or not source_column:
    print_step("Partner+Source汇总", f"❌ 缺少必要列: Partner列={partner_column}, Source列={source_column}")
    return []
```

#### 修改後:
```python
# 找到Partner和Source列 - 支持更多列名变体
# Partner列查找 - 支持更多变体
for col in ['Partner', 'partner', 'Partner Name', 'partner_name', 'PartnerName', 'Company', 'company']:
    if col in df.columns:
        partner_column = col
        break

# Source列查找 - 支持更多变体
for col in ['Source', 'source', 'aff_sub1', 'Source Name', 'source_name', 'SourceName', 'aff_sub', 'Aff Sub1', 'Aff Sub']:
    if col in df.columns:
        source_column = col
        break

# 如果找不到Partner和Source列，尝试从其他列推断
if not partner_column or not source_column:
    print_step("Partner+Source汇总", f"⚠️ 未找到标准Partner/Source列，尝试推断...")
    
    # 尝试从Offer Name或其他列推断Partner信息
    if 'Offer Name' in df.columns:
        # 从Offer Name推断Partner信息
        df['Inferred_Partner'] = df['Offer Name'].str.extract(r'^([A-Za-z]+)').fillna('Unknown')
        partner_column = 'Inferred_Partner'
        print_step("Partner+Source汇总", f"🔍 从Offer Name推断Partner列: '{partner_column}'")
    
    # 尝试从其他列推断Source信息
    if 'aff_sub2' in df.columns:
        source_column = 'aff_sub2'
        print_step("Partner+Source汇总", f"🔍 使用aff_sub2作为Source列: '{source_column}'")
    elif 'aff_sub3' in df.columns:
        source_column = 'aff_sub3'
        print_step("Partner+Source汇总", f"🔍 使用aff_sub3作为Source列: '{source_column}'")
    elif 'aff_sub' in df.columns:
        source_column = 'aff_sub'
        print_step("Partner+Source汇总", f"🔍 使用aff_sub作为Source列: '{source_column}'")

if not partner_column or not source_column:
    print_step("Partner+Source汇总", f"❌ 无法找到或推断Partner/Source列: Partner='{partner_column}', Source='{source_column}'")
    print_step("Partner+Source汇总", f"📋 可用列: {list(df.columns)}")
    return []
```

### 2. 支持的列名變體

#### Partner 列支持:
- `Partner`
- `partner`
- `Partner Name`
- `partner_name`
- `PartnerName`
- `Company`
- `company`

#### Source 列支持:
- `Source`
- `source`
- `aff_sub1`
- `Source Name`
- `source_name`
- `SourceName`
- `aff_sub`
- `Aff Sub1`
- `Aff Sub`

### 3. 智能推斷功能

#### Partner 推斷:
- 從 `Offer Name` 列提取 Partner 信息
- 使用正則表達式 `^([A-Za-z]+)` 提取開頭的字母部分
- 例如: `DeepLeaper_Offer1` → `DeepLeaper`

#### Source 推斷:
- 優先使用 `aff_sub2`
- 其次使用 `aff_sub3`
- 最後使用 `aff_sub`

## 測試結果

創建了測試文件 `agents/data_output_agent/test_bytec_columns.py` 來驗證修復效果：

### 測試案例 1: 標準 ByteC 格式
- **輸入**: 包含標準 Partner 和 Source 列
- **結果**: ✅ 成功生成 3 個 Partner+Source 匯總

### 測試案例 2: 缺少 Partner/Source 列
- **輸入**: 只有 `aff_sub2` 列，無標準 Partner/Source 列
- **結果**: ✅ 成功從 Offer Name 推斷 Partner，使用 aff_sub2 作為 Source

### 測試案例 3: 只有 Offer Name
- **輸入**: 只有 Offer Name 列，無其他 Partner/Source 信息
- **結果**: ⚠️ 無法推斷 Source 列，但提供了詳細的錯誤信息

## 改進效果

1. **兼容性提升**: 支持更多 ByteC Excel 文件的列名格式
2. **智能推斷**: 能夠從現有數據推斷缺失的 Partner/Source 信息
3. **錯誤處理**: 提供更詳細的錯誤信息和調試輸出
4. **日誌優化**: 改進了日誌輸出，便於問題診斷

## 相關文件

- **修改文件**: `agents/data_output_agent/email_sender.py`
- **測試文件**: `agents/data_output_agent/test_bytec_columns.py`
- **總結文檔**: `agents/data_output_agent/BYTEC_COLUMN_FIX_SUMMARY.md`

## 使用建議

1. **優先使用標準列名**: 在生成 Excel 文件時，盡量使用標準的 Partner 和 Source 列名
2. **備用推斷**: 如果無法使用標準列名，系統會自動嘗試推斷
3. **監控日誌**: 關注 Partner+Source 匯總的日誌輸出，確保數據正確處理
4. **測試驗證**: 使用測試腳本驗證不同數據格式的處理效果 