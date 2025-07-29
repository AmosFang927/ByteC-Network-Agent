# TikTok Shop 聯盟行銷 Agent

這是一個用於 TikTok Shop 聯盟行銷的 Python Agent，提供 OAuth2 認證、Token 管理和聯盟連結生成功能。

## 📋 功能特性

- ✅ **OAuth2 認證**: 支援 TikTok Shop 授權流程
- 🔄 **自動 Token 刷新**: 24小時自動刷新機制
- 🔗 **聯盟連結生成**: 批量生成產品聯盟分享連結
- 🔐 **HMAC-SHA256 簽名**: 符合 TikTok Shop API 安全要求
- 💾 **Token 持久化存儲**: 自動保存和管理 Token
- 📝 **詳細日誌**: 完整的操作日誌和錯誤處理
- 🛠️ **CLI 接口**: 便於命令列操作和集成

## 🚀 快速開始

### 1. 前置要求

```bash
# Python 3.7+ 
# 依賴套件
pip install requests
```

### 2. 配置設定

所有配置都在 `config.py` 中：

```python
# App 認證資訊
APP_KEY = "6gtqs1d5dtkka"
APP_SECRET = "5965f7f420ae4ffe33eff2f48e31a7fb62a76139"
REDIRECT_URL = "https://bytec-postback-agent-472712465571.asia-southeast1.run.app"
AUTH_CODE = "ROW_DkQw-wAAAABE_Ppf1X4y3-0HZBvKa934lbOqPRGhDryxogAKf4eCX8rbwI1YUoQLq8NNgtAoTaCL2NwiMdhbwhi7SvJCrywV"

# API 版本
APP_VERSION = "202501"
```

### 3. 授權流程 (已手動完成)

**Step 1-4** 已在 TikTok Shop Partner 後台手動完成：

1. ✅ **建立 App**: 從 Partner Center 建立 App，取得 `app_key`, `app_secret`
2. ✅ **生成授權 URL**: `https://shop.tiktok.com/alliance/creator/auth?app_key={app_key}&state={state_id}`
3. ✅ **使用者授權**: 登入 TikTok Shop 並完成授權
4. ✅ **取得 AUTH_CODE**: 回調中取得授權碼並存入配置

## 💻 使用方法

### 基本命令

```bash
# 進入專案目錄
cd /path/to/ByteC-Network-Agent-main

# 啟用虛擬環境 (如果使用)
source venv/bin/activate
```

### 1. 獲取 Access Token

```bash
# 使用配置中的 AUTH_CODE
python -m agents.linkshare_agent.main get-token

# 或指定特定的授權碼
python -m agents.linkshare_agent.main get-token --auth-code "YOUR_AUTH_CODE"
```

**預期輸出:**
```
🚀 開始獲取 Access Token...
✅ Access Token 獲取成功!
🔑 Access Token: TTP_Fw8rBwAAAAAkW03F...
🔄 Refresh Token: TTP_NTUxZTNhYTQ2ZDk2...
👤 Open ID: 7010736057180325637
🏪 Seller Name: Jjj test shop
🌍 Base Region: ID
💾 Token 已保存到配置文件
```

### 2. 查看 Token 信息

```bash
python -m agents.linkshare_agent.main token-info
```

### 3. 刷新 Token

```bash
python -m agents.linkshare_agent.main refresh-token
```

### 4. 生成聯盟連結

```bash
# 使用默認參數
python -m agents.linkshare_agent.main generate --pid 1731493745807886173

# 自定義頻道和標籤
python -m agents.linkshare_agent.main generate --pid 1731493745807886173 --channel "MY_CHANNEL" --tags "TAG1,TAG2,TAG3"

# 完整參數
python -m agents.linkshare_agent.main generate \
  --pid 1731493745807886173 \
  --channel "OEM3_OPPO" \
  --tags "OEM3_OPPO_PUSH,OEM2_VIVO_PUSH" \
  --campaign-url "https://shop.tiktok.com/view/product/1731493745807886173"
```

**預期輸出:**
```
🔗 開始生成產品 1731493745807886173 的聯盟連結...
📊 聯盟連結生成結果摘要:
✅ 成功生成 2 個聯盟連結:
   🏷️  標籤: OEM3_OPPO_PUSH
   🔗 連結: www.tiktok.com/asdsfe1c
   🏷️  標籤: OEM2_VIVO_PUSH
   🔗 連結: www.tiktok.com/afasdasd
📋 請求 ID: 202203070749000101890810281E8C70B7
💬 響應消息: Success
```

## 📂 項目結構

```
agents/linkshare_agent/
├── __init__.py              # 模組初始化
├── config.py                # 配置文件
├── auth.py                  # OAuth2 認證
├── token_manager.py         # Token 管理
├── signature.py             # HMAC-SHA256 簽名
├── link_generator.py        # 聯盟連結生成
├── main.py                  # CLI 主程序
├── tokens.conf              # Token 存儲文件 (自動生成)
└── README.md               # 使用說明
```

## 🔧 API 參考

### TikTokAuth 類

```python
from agents.linkshare_agent.auth import TikTokAuth

auth = TikTokAuth()
token_data = auth.get_access_token()  # 獲取 Token
refreshed_data = auth.refresh_access_token(refresh_token)  # 刷新 Token
```

### TokenManager 類

```python
from agents.linkshare_agent.token_manager import TokenManager

token_manager = TokenManager()
valid_token = token_manager.get_valid_token()  # 自動處理過期
token_manager.save_tokens(token_data)  # 保存 Token
```

### LinkGenerator 類

```python
from agents.linkshare_agent.link_generator import LinkGenerator

generator = LinkGenerator()
response = generator.generate_affiliate_link(
    product_id="1731493745807886173",
    channel="MY_CHANNEL",
    tags=["TAG1", "TAG2"]
)
```

## 🔐 簽名算法

參考 [TikTok Shop 授權文檔](https://partner.tiktokshop.com/docv2/page/authorization-overview-202407)，實現了完整的 HMAC-SHA256 簽名流程：

1. 提取並排序查詢參數 (排除 access_token 和 sign)
2. 連接參數為 `{key}{value}` 格式
3. 附加 API 路徑到簽名字符串
4. 如果有請求體，附加 JSON 序列化的內容
5. 用 `app_secret` 包裝簽名字符串
6. 使用 HMAC-SHA256 生成十六進制簽名

## 🛠️ 錯誤處理

系統提供完整的錯誤處理和重試機制：

- **API 錯誤**: 自動解析 TikTok Shop API 錯誤碼
- **網路錯誤**: 支援重試和退避策略
- **Token 過期**: 自動檢測和刷新
- **配置錯誤**: 啟動時驗證所有必要配置

## 📊 日誌系統

支援多種日誌級別：

```bash
# DEBUG 級別 (詳細調試信息)
python -m agents.linkshare_agent.main generate --pid 123 --log-level DEBUG

# INFO 級別 (預設)
python -m agents.linkshare_agent.main generate --pid 123 --log-level INFO

# WARNING 級別 (僅警告和錯誤)
python -m agents.linkshare_agent.main generate --pid 123 --log-level WARNING
```

## 🧪 測試

本專案規劃了完整的單元測試：

```bash
# 運行所有測試 (規劃中)
python -m pytest agents/linkshare_agent/tests/

# 測試特定模組
python -m pytest agents/linkshare_agent/tests/test_auth.py
python -m pytest agents/linkshare_agent/tests/test_token_manager.py
python -m pytest agents/linkshare_agent/tests/test_link_generator.py
```

## 📝 待實現功能

基礎框架已完成，以下功能將在後續階段實現：

- ✅ 項目結構和配置
- ⏳ Get Access Token 實現
- ⏳ Token 刷新機制
- ⏳ 聯盟連結生成 API
- ⏳ Unit Tests
- ⏳ 錯誤處理優化

## 🆘 故障排除

### 常見問題

1. **配置錯誤**
   ```
   ❌ 配置錯誤: 缺少必要配置: AUTH_CODE
   ```
   **解決方案**: 檢查 `config.py` 中的 `AUTH_CODE` 是否正確設置

2. **Token 過期**
   ```
   ❌ Token 已過期，正在自動刷新...
   ```
   **解決方案**: 系統會自動處理，如果持續失敗請檢查 `refresh_token`

3. **API 調用失敗**
   ```
   ❌ API request failed: 40003 簽名錯誤
   ```
   **解決方案**: 檢查系統時間是否正確，確保時間戳未過期

## 📚 相關文檔

- [TikTok Shop 授權概覽](https://partner.tiktokshop.com/docv2/page/authorization-overview-202407)
- [聯盟分享連結 API](https://bytedance.sg.larkoffice.com/docx/Duj9dVCIWoQOUgx2epAlkAvKgne)

## 📞 技術支援

如果遇到問題，請檢查：

1. 📋 配置文件是否正確
2. 🌐 網路連接是否正常
3. 📅 系統時間是否準確
4. 🔑 Auth Code 是否有效

---

**版本**: 1.0.0  
**更新日期**: 2025-01-27  
**維護者**: ByteC Network 