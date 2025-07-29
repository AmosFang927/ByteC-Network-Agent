# TikTok Shop API 參數完整分析

## 📤 **Get Access Token 請求參數**

### **請求 URL**
```
https://auth.tiktok-shops.com/api/v2/token/get
```

### **請求方法**
```
GET
```

### **請求參數** (Query Parameters)
| 參數名 | 類型 | 必填 | 說明 | 當前值 |
|--------|------|------|------|--------|
| `app_key` | String | ✅ | 應用程式金鑰 | `6gtqs1d5dtkka` |
| `app_secret` | String | ✅ | 應用程式密鑰 | `5965f7f420ae4ffe33eff2f48e31a7fb62a76139` |
| `grant_type` | String | ✅ | 授權類型 | `authorized_code` |
| `auth_code` | String | ✅ | 授權碼 | `ROW_DkQw-wAAAABE_Ppf1X4y3-0HZBv...` |

### **完整請求 URL 示例**
```
https://auth.tiktok-shops.com:443/api/v2/token/get?app_key=6gtqs1d5dtkka&app_secret=5965f7f420ae4ffe33eff2f48e31a7fb62a76139&grant_type=authorized_code&auth_code=ROW_DkQw-wAAAABE_Ppf1X4y3-0HZBvKa934lbOqPRGhDryxogAKf4eCX8rbwI1YUoQLq8NNgtAoTaCL2NwiMdhbwhi7SvJCrywV
```

## 📥 **API 響應參數**

### **成功響應 (code: 0)** - 實際獲取的響應
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "access_token": "ROW_-TqrPAAAAACo6wRybY_AaSa6Rh6LmKbhnsroaroVrJnuzYEao1G5P2kuwL98FR_SFE4qIDBJfqiSkGpuyGPTs2NImCR5Hckm8RWBXEfdtbbMSjw50VOmog",
    "access_token_expire_in": 1754361898,
    "refresh_token": "ROW_57egEQAAAABTm-5pCNgPAZ1xyZwtit2iX-GbJMLadW75Gcpp7CrvVFGn8NPqUhPF3WM6EUvUwbILWo1P4b4c4AURgLCssiBZ",
    "refresh_token_expire_in": 1785292795,
    "open_id": "NiZvhwAAAAAoW7ttXI79EqYdEIPpOBQ-XOUVsSnUgrz-yeFRW2E5Pg",
    "seller_name": null,
    "user_type": 1,
    "granted_scopes": [
      "creator.affiliate.info",
      "creator.affiliate_collaboration.read",
      "creator.affiliate.link.write"
    ]
  },
  "request_id": "2025072910445773B601519BF2F2121A90"
}
```

#### **成功響應參數說明**
| 參數路徑 | 類型 | 說明 |
|----------|------|------|
| `code` | Integer | 響應碼，0 表示成功 |
| `message` | String | 響應消息 |
| `data.access_token` | String | 訪問令牌，用於 API 調用 |
| `data.access_token_expire_in` | Integer | access_token 過期時間戳 |
| `data.refresh_token` | String | 刷新令牌，用於刷新 access_token |
| `data.refresh_token_expire_in` | Integer | refresh_token 過期時間戳 |
| `data.open_id` | String | 賣家的唯一標識符 |
| `data.seller_name` | String | 賣家名稱 |
| `data.seller_base_region` | String | 賣家所在地區 |
| `data.user_type` | Integer | 用戶類型 |
| `data.granted_scopes` | Array | 授權的權限範圍 |
| `request_id` | String | 請求唯一標識符 |

### **錯誤響應 (code: 非0)**
```json
{
  "code": 36004004,
  "message": "invalid auth code",
  "request_id": "2025072909315666E21AF5A19E9E106BC5"
}
```

#### **當前收到的錯誤響應**
| 參數 | 值 | 說明 |
|------|----|----- |
| `code` | `36004004` | 錯誤碼：無效的授權碼 |
| `message` | `"invalid auth code"` | 錯誤描述 |
| `request_id` | `"2025072909315666E21AF5A19E9E106BC5"` | 請求 ID |

## 🔧 **已知錯誤碼對照表**

| 錯誤碼 | 錯誤描述 | 可能原因 |
|--------|----------|----------|
| `36004004` | invalid auth code | AUTH_CODE 已過期、已使用或不正確 |
| `98001004` | invalid params | 參數格式錯誤 |
| `98001005` | 授權碼已使用 | AUTH_CODE 已被使用過 |
| `98001006` | refresh_token 無效或過期 | refresh_token 問題 |
| `40001` | 參數錯誤 | 請求參數格式問題 |
| `40003` | 簽名錯誤 | 簽名驗證失敗 |
| `40004` | 時間戳過期 | 請求時間戳過期 |
| `50000` | 內部服務錯誤 | 服務器內部錯誤 |

## 🎯 **當前狀態分析**

### **✅ 認證狀態 - 完全成功！**
- ✅ **URL 正確**: `https://auth.tiktok-shops.com/api/v2/token/get`
- ✅ **方法正確**: `GET`
- ✅ **參數格式正確**: 所有必需參數都已提供
- ✅ **網路連接正常**: HTTP 200 響應
- ✅ **AUTH_CODE 有效**: 成功獲取 tokens
- ✅ **響應碼**: 0 (成功)

### **🔑 已獲取的重要參數**
| 參數名 | 值 | 過期時間 |
|--------|----|---------:|
| `access_token` | `ROW_-TqrPAAAAACo6wRy...` | 2025-08-05 02:44:58 UTC |
| `refresh_token` | `ROW_57egEQAAAABTm-5p...` | 2026-07-29 02:39:55 UTC |
| `open_id` | `NiZvhwAAAAAoW7ttXI79EqYdEIPpOBQ-XOUVsSnUgrz-yeFRW2E5Pg` | - |
| `user_type` | `1` (Creator) | - |

### **🎯 已授權的權限範圍**
- ✅ `creator.affiliate.info` - 讀取聯盟行銷基本信息
- ✅ `creator.affiliate_collaboration.read` - 讀取聯盟合作信息
- ✅ `creator.affiliate.link.write` - **生成聯盟連結** (核心功能)

### **💾 Token 管理狀態**
- ✅ **已保存到**: `agents/linkshare_agent/tokens.conf`
- ✅ **檔案權限**: `0o600` (安全)
- ✅ **自動管理**: 過期檢查、自動刷新機制已啟用
- ✅ **剩餘時間**: ~86,368 秒 (約 24 小時)

## 📋 **Refresh Token 請求參數** (未來使用)

### **請求 URL**
```
https://auth.tiktok-shops.com/api/v2/token/refresh
```

### **請求參數**
| 參數名 | 類型 | 必填 | 說明 |
|--------|------|------|------|
| `app_key` | String | ✅ | 應用程式金鑰 |
| `app_secret` | String | ✅ | 應用程式密鑰 |
| `grant_type` | String | ✅ | 固定值: `refresh_token` |
| `refresh_token` | String | ✅ | 刷新令牌 | 