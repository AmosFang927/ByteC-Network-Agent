# 🧠 Cursor Memory Lite 設置指南

## 🎯 設置步驟

### 1. 開啟 Cursor 設定
1. 打開 Cursor 應用程式
2. 按下 `Cmd + ,` (Mac) 或 `Ctrl + ,` (Windows/Linux)
3. 或點擊選單：**Cursor → Preferences**

### 2. 導航到 Model 設定
1. 在左側選單中點擊 **"Model"**
2. 或直接搜尋 "Model" 設定

### 3. 啟用 Memory Lite 模式
在 Model 設定頁面中：

#### 找到 Memory 相關設定
- 尋找 **"Memory"** 或 **"Memory Mode"** 選項
- 可能的位置：
  - `Preferences → Model → Memory`
  - `Preferences → AI → Memory`
  - `Preferences → Advanced → Memory`

#### 選擇 Memory Lite 模式
- 將 Memory 模式從 **"Full"** 改為 **"Lite"**
- 或從 **"Enabled"** 改為 **"Lite Mode"**
- 或直接選擇 **"Memory Lite"** 選項

### 4. 確認設置
- 設置完成後，Cursor 會顯示 Memory Lite 已啟用
- 您可能會看到提示：**"Memory Lite mode enabled"**

## 🔧 替代設置路徑

如果上述路徑不存在，請嘗試以下位置：

### 路徑 1: AI 設定
```
Preferences → AI → Memory → Lite Mode
```

### 路徑 2: 實驗性功能
```
Preferences → Experimental → Memory Lite
```

### 路徑 3: 進階設定
```
Preferences → Advanced → Memory → Lite
```

### 路徑 4: 搜尋功能
1. 在設定頁面按 `Cmd/Ctrl + F`
2. 搜尋 "Memory Lite" 或 "Lite"
3. 直接點擊搜尋結果

## 🚨 如果找不到 Memory Lite 選項

### 可能原因：
1. **Cursor 版本過舊** - 需要更新到最新版本
2. **功能尚未發布** - Memory Lite 可能是測試版功能
3. **地區限制** - 某些功能可能僅在特定地區可用

### 解決方案：
1. **更新 Cursor**:
   - 檢查是否有更新可用
   - 下載最新版本

2. **加入測試版**:
   - 在 Cursor 官網註冊測試版
   - 或加入 Discord 社群獲取測試版

3. **手動啟用** (如果支援):
   - 在設定中搜尋 "experimental"
   - 啟用實驗性功能

## ✅ 驗證設置成功

### 檢查方法：
1. **重啟 Cursor** 後檢查設定是否保持
2. **開始新對話** 測試 Memory Lite 效果
3. **觀察行為變化**:
   - AI 不再引用之前的對話
   - 每次都需要完整上下文
   - 工具調用次數限制更嚴格

### 測試腳本：
```
[ByteC Network Agent - Memory Lite 測試]
技術棧：Python 3.8+ + PostgreSQL + asyncpg
專案：Multi-Agent 系統

【測試任務】：驗證 Memory Lite 模式是否生效
【預期行為】：AI 需要完整上下文，不依賴之前對話
【驗證方法】：觀察 AI 是否要求更多背景信息
```

## 📋 設置完成檢查清單

- [ ] 找到並開啟 Cursor Preferences
- [ ] 導航到 Model 或 AI 設定
- [ ] 找到 Memory 相關選項
- [ ] 啟用 Memory Lite 模式
- [ ] 確認設置已保存
- [ ] 重啟 Cursor 驗證設置
- [ ] 測試新對話確認效果

## 🎯 設置完成後的使用

### 使用新的工作模式：
1. **參考模板**: `.cursor/templates/MemoryLiteRequestTemplate.md`
2. **遵循規則**: `.cursor/rules/MemoryLiteMode.mdc`
3. **監控效率**: 使用 `cursor_usage_tracker.py`

### 關鍵提醒：
- 每次對話都當作全新開始
- 提供完整的背景信息
- 使用明確的檔案路徑
- 工具調用限制在 12 次以內

**Memory Lite 模式設置完成後，您將體驗到更節省額度的 AI 輔助開發！** 🚀 