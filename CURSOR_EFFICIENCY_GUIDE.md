# 🎯 Cursor 效率監控指南

## 📋 概述

本指南提供完整的 Cursor 額度使用監控和優化系統，幫助您：
- 追蹤每次對話的效率指標
- 分析工具調用模式
- 獲得個性化的優化建議
- 建立長期的使用效率趨勢

## 🛠️ 工具組件

### 1. Cursor Rules (自動優化)
- **位置**: `.cursor/rules/CursorQuotaOptimization.mdc`
- **功能**: 自動指導 AI 使用更節省額度的策略
- **啟用**: Cursor 自動載入，無需手動設置

### 2. 使用追蹤器 (手動記錄)
- **檔案**: `cursor_usage_tracker.py`
- **功能**: 手動記錄和分析對話指標
- **使用**: `python cursor_usage_tracker.py`

### 3. 日誌分析器 (半自動)
- **檔案**: `cursor_log_analyzer.py`
- **功能**: 從對話文本自動提取指標
- **使用**: `python cursor_log_analyzer.py`

### 4. Memory Lite 模式支援
- **規則檔案**: `.cursor/rules/MemoryLiteMode.mdc`
- **模板檔案**: `.cursor/templates/MemoryLiteRequestTemplate.md`
- **功能**: 針對 Memory Lite 模式優化的工作策略

## 🚀 快速開始

### 第一次使用

1. **確認 Cursor Rules 已啟用**
   ```bash
   # 檢查規則文件是否存在
   ls .cursor/rules/
   ```

2. **開始第一次對話追蹤**
   ```bash
   python cursor_usage_tracker.py
   # 選擇 "1. 開始新對話追蹤"
   ```

3. **分析現有對話** (可選)
   ```bash
   python cursor_log_analyzer.py
   # 選擇 "1. 分析剪貼板內容"
   ```

### 日常使用工作流程

#### 📊 每次對話結束後
1. 複製對話內容到剪貼板
2. 運行: `python cursor_log_analyzer.py`
3. 選擇 "1. 分析剪貼板內容"
4. 查看效率報告和建議

#### 📈 每週檢查
```bash
python cursor_usage_tracker.py
# 選擇 "5. 生成報告"
```

## 📊 指標說明

### 核心指標

| 指標 | 說明 | 理想值 | Memory Lite |
|------|------|--------|-------------|
| **工具調用次數** | 每次對話使用的工具總數 | < 20 | ≤ 12 |
| **解決問題數** | 成功完成的任務數量 | ≥ 1 | ≥ 1 |
| **效率比率** | 問題數 / 工具調用數 | > 0.1 | > 0.15 |
| **複雜度** | 任務難度評分 (1-5) | - | - |

### 效率評級

- **🏆 優秀** (效率比率 > 0.3): 高效解決問題
- **⚡ 良好** (效率比率 0.1-0.3): 正常使用範圍  
- **⚠️ 需改進** (效率比率 < 0.1): 建議優化策略

## 🎯 優化策略

### 工具調用優化

#### ✅ 推薦做法
- 明確問題範圍後再開始
- 優先使用 `grep_search` 進行精確搜索
- 基於已知信息進行targeted操作
- 一次性完成相關修改

#### ❌ 避免做法
- 探索性的廣泛搜索
- 重複搜索相同內容
- 未經規劃的連續工具調用
- 過度使用 `codebase_search`

### 對話管理

#### 🔄 何時分割對話
- 工具調用超過 25 次 (Memory Lite: 15 次)
- 處理多個不相關問題
- 任務複雜度評分 > 4
- 對話持續時間過長

#### 📋 任務規劃建議
1. **明確目標**: 列出具體要完成的任務
2. **評估複雜度**: 預估所需工具調用數量
3. **分階段執行**: 複雜任務分解為子任務
4. **優先級排序**: 先解決最重要的問題

## 📈 監控報告

### 每週效率報告
```bash
python cursor_usage_tracker.py
# 選擇 "4. 查看統計" 
# 輸入天數: 7
```

### 自定義分析
```python
from cursor_usage_tracker import CursorUsageTracker

tracker = CursorUsageTracker()
stats = tracker.get_recent_stats(30)  # 最近 30 天
print(stats)
```

## 🔧 高級配置

### Memory Lite 模式設定

如果您使用 Cursor 測試版的 Memory Lite 選項：

1. **啟用 Memory Lite 模式**:
   - 在 Cursor 設定中尋找 "Memory Lite" 或類似選項
   - 啟用該選項以關閉長期記憶功能

2. **調整工作策略**:
   - 使用 `.cursor/templates/MemoryLiteRequestTemplate.md` 模板
   - 每次請求都提供完整上下文
   - 工具調用限制降低至 10-12 次

3. **使用請求模板**:
```markdown
[ByteC Network Agent - Memory Lite]
技術棧：Python 3.8+ + PostgreSQL + asyncpg
【任務】：具體任務描述
【檔案】：完整檔案路徑
【配置】：相關配置信息
```

### 自定義 Cursor Rules

編輯 `.cursor/rules/CursorQuotaOptimization.mdc`:

```markdown
### 自定義優化規則
- 單次回應最多 X 個工具調用 (Memory Lite: ≤ 12)
- 複雜度 > Y 時建議分解任務
- 特定項目的工具使用偏好
- Memory Lite 模式自包含原則
```

### 分析參數調整

編輯 `cursor_log_analyzer.py` 中的參數:

```python
# 複雜度判斷標準
complexity_indicators = {
    'your_keyword': score,  # 添加項目特定關鍵詞
}

# 效率評級標準 (Memory Lite 調整)
efficiency_thresholds = {
    'excellent': 0.3,
    'good': 0.15,  # Memory Lite 下提高標準
    'needs_improvement': 0.0
}
```

## 🚨 警告與限制

### ⚠️ 注意事項
- 追蹤器需要手動記錄數據
- 日誌分析基於文本匹配，可能有誤差
- 效率指標僅供參考，需結合實際情況
- Memory Lite 模式下需要更多上下文信息

### 🔒 隱私保護
- 所有數據存儲在本地
- 不會上傳任何對話內容
- 可隨時刪除追蹤數據

## 📞 故障排除

### 常見問題

1. **Rules 不生效**
   - 檢查 Cursor Settings 中的 "Enable Cursor Rules"
   - 確認 `.cursor/rules/` 目錄權限

2. **追蹤器無法運行**
   ```bash
   pip install dataclasses  # Python < 3.7
   ```

3. **日誌分析錯誤**
   ```bash
   pip install pyperclip  # 剪貼板功能
   ```

4. **Memory Lite 模式問題**
   - 確認 Cursor 版本支援 Memory Lite
   - 使用提供的請求模板
   - 每次請求都包含完整上下文

## 🎉 開始優化

現在您已經有了完整的 Cursor 效率監控系統！

**下一步行動**:
1. 確認 Cursor Rules 已生效
2. 如果使用 Memory Lite，檢查相關設定
3. 開始記錄當前對話
4. 建立每週檢查習慣
5. 根據報告調整使用策略

記住：持續監控和調整是提升效率的關鍵！🚀 