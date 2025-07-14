# 🤖 公司財務AI助手 Company Finance AI Assistant

基於 **whodb** 的自然語言財務數據查詢系統，讓您可以用自然語言與財務數據對話。

## 📋 功能特色

- 🗣️ **自然語言查詢** - 用中文或英文直接查詢財務數據
- 📊 **實時財務儀表板** - 動態顯示關鍵財務指標
- 🔍 **智能SQL生成** - 自動將自然語言轉換為SQL查詢
- 💰 **全面財務分析** - 收入、支出、毛利、現金流分析
- 📈 **趨勢分析** - 時間序列分析和同比增長
- 👥 **合作夥伴績效** - 多維度績效評估
- 🔄 **whodb整合** - 無縫連接現有數據庫管理系統

## 🚀 快速開始

### 1. 環境準備

```bash
# 克隆項目
git clone <your-repo-url>
cd ByteC-Network-Agent

# 安裝依賴
pip install -r company_ai_requirements.txt
```

### 2. 配置 whodb

確保您的 whodb 服務正在運行：

```bash
# 啟動 whodb (根據您的whodb配置)
# 例如：
docker run -d -p 8080:8080 whodb/whodb:latest
```

### 3. 配置數據庫連接

編輯 `agents/main.py` 中的數據庫配置：

```python
WHODB_CONFIG = {
    'base_url': 'http://localhost:8080',  # 您的whodb地址
    'username': 'admin',                  # whodb用戶名
    'password': 'password'                # whodb密碼
}
```

### 4. 啟動系統

```bash
# 使用啟動腳本
python run_company_ai_assistant.py

# 或使用命令行參數
python run_company_ai_assistant.py \
    --whodb-url http://localhost:8080 \
    --whodb-username admin \
    --whodb-password password \
    --api-port 5000
```

### 5. 訪問系統

- 🌐 **Web界面**: http://localhost:5000
- 🔗 **API文檔**: http://localhost:5000/api/health
- 📊 **健康檢查**: http://localhost:5000/api/health

## 💬 使用示例

### 自然語言查詢示例

```
用戶查詢: "今天的收入是多少？"
AI回復: "根據數據分析，今天的總收入為 $12,345，共有 89 次轉化記錄。"

用戶查詢: "本月的毛利率怎麼樣？"
AI回復: "本月毛利率為 23.5%，比上月提升了 2.1%。"

用戶查詢: "哪個合作夥伴的收益最高？"
AI回復: "ByteC 合作夥伴收益最高，達到 $45,678。"
```

### API使用示例

```bash
# 發送AI查詢
curl -X POST http://localhost:5000/api/company-ai-query \
  -H "Content-Type: application/json" \
  -d '{"query": "今天的收入是多少？"}'

# 獲取財務儀表板數據
curl http://localhost:5000/api/financial-dashboard?time_range=week

# 直接執行SQL查詢
curl -X POST http://localhost:5000/api/whodb-query \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT COUNT(*) FROM conversions WHERE DATE(created_at) = CURRENT_DATE"}'
```

## 🏗️ 系統架構

```
用戶自然語言查詢
         ↓
  AI查詢解析器 (NLP)
         ↓
   SQL查詢生成器
         ↓
    whodb API接口
         ↓
   PostgreSQL數據庫
         ↓
    財務計算引擎
         ↓
   結果格式化和展示
```

## 📊 支援的財務指標

### 基本指標
- 💰 **收入分析** - 總收入、日收入、月收入
- 💸 **支出分析** - 成本、費用、佣金支出
- 📈 **毛利分析** - 毛利額、毛利率、利潤趨勢
- 💵 **現金流** - 現金流入、流出、淨現金流

### 高級分析
- 📊 **同比分析** - 年度、季度、月度同比
- 🔄 **環比分析** - 月度、週度環比增長
- 👥 **合作夥伴分析** - 績效排名、貢獻度分析
- 🎯 **產品分析** - 產品線收益、轉化率分析

## 🔧 配置選項

### 環境變量

```bash
# whodb配置
WHODB_URL=http://localhost:8080
WHODB_USERNAME=admin
WHODB_PASSWORD=password

# API配置
API_HOST=0.0.0.0
API_PORT=5000
API_DEBUG=True

# 數據庫配置
DATABASE_URL=postgresql://user:password@localhost/dbname
```

### 啟動參數

```bash
python run_company_ai_assistant.py --help

選項:
  --whodb-url TEXT        whodb服務地址 (默認: http://localhost:8080)
  --whodb-username TEXT   whodb用戶名 (默認: admin)
  --whodb-password TEXT   whodb密碼 (默認: password)
  --api-host TEXT         API服務器地址 (默認: 0.0.0.0)
  --api-port INTEGER      API服務器端口 (默認: 5000)
  --debug                 啟用調試模式
  --help                  顯示幫助信息
```

## 🎯 API端點

### 核心端點

| 端點 | 方法 | 描述 |
|------|------|------|
| `/` | GET | 主頁面 |
| `/api/company-ai-query` | POST | AI查詢處理 |
| `/api/financial-dashboard` | GET | 財務儀表板數據 |
| `/api/whodb-query` | POST | 直接SQL查詢 |
| `/api/health` | GET | 健康檢查 |

### 請求格式

```json
// AI查詢
{
  "query": "今天的收入是多少？",
  "user_id": "dashboard_user"
}

// SQL查詢
{
  "sql": "SELECT COUNT(*) FROM conversions WHERE DATE(created_at) = CURRENT_DATE"
}
```

## 🛠️ 開發和擴展

### 添加新的查詢類型

1. 編輯 `agents/main.py` 中的 `AIQueryParser` 類
2. 在 `financial_keywords` 中添加新的關鍵詞
3. 在 `_generate_sql_template` 中添加新的SQL模板

### 自定義財務指標

1. 擴展 `FinancialCalculator` 類
2. 添加新的計算方法
3. 更新 `format_results_for_display` 方法

### 整合其他數據庫

1. 修改 `WhoDBClient` 類
2. 添加新的數據庫驅動
3. 更新連接配置

## 🐛 故障排除

### 常見問題

1. **whodb連接失敗**
   ```bash
   # 檢查whodb是否運行
   curl http://localhost:8080/health
   
   # 檢查防火牆設置
   netstat -tuln | grep 8080
   ```

2. **數據庫連接問題**
   ```bash
   # 檢查數據庫連接
   psql -h localhost -U username -d dbname
   
   # 檢查網絡連接
   ping your-database-host
   ```

3. **依賴項問題**
   ```bash
   # 重新安裝依賴
   pip install -r company_ai_requirements.txt --force-reinstall
   ```

### 日誌分析

```bash
# 查看應用日誌
tail -f company_ai_assistant.log

# 查看特定錯誤
grep "ERROR" company_ai_assistant.log

# 查看API請求
grep "API" company_ai_assistant.log
```

## 🔒 安全注意事項

1. **數據庫安全**
   - 使用強密碼
   - 限制數據庫訪問權限
   - 啟用SSL連接

2. **API安全**
   - 配置防火牆規則
   - 使用HTTPS（生產環境）
   - 實施認證和授權

3. **whodb安全**
   - 定期更新whodb版本
   - 限制網絡訪問
   - 備份重要數據

## 📈 性能優化

### 查詢優化
- 使用索引優化SQL查詢
- 實施查詢結果緩存
- 分頁大量數據查詢

### 系統優化
- 調整連接池大小
- 啟用壓縮
- 使用CDN加速靜態資源

## 🤝 貢獻指南

1. Fork 此項目
2. 創建功能分支: `git checkout -b feature/your-feature`
3. 提交更改: `git commit -am 'Add your feature'`
4. 推送到分支: `git push origin feature/your-feature`
5. 創建Pull Request

## 📄 許可證

本項目採用 MIT 許可證。詳見 [LICENSE](LICENSE) 文件。

## 🆘 支援

如果您遇到任何問題或需要幫助：

1. 查看 [常見問題](#故障排除)
2. 搜索 [Issues](https://github.com/your-repo/issues)
3. 創建新的 [Issue](https://github.com/your-repo/issues/new)
4. 聯繫維護人員

---

**享受您的財務數據分析之旅！** 🚀 