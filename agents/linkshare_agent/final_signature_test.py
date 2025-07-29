"""
最終簽名對比測試
完全按照 SDK 的實際行為進行測試
"""

import json
import time
import logging
from signature import generate_sign_sdk_style
from config import APP_KEY, APP_SECRET

def test_exact_sdk_behavior():
    """
    測試與 SDK 完全相同的行為
    """
    print("🔬 最終簽名對比測試")
    print("=" * 80)
    
    # 使用固定時間戳便於對比
    timestamp = 1753761900  
    
    # 1. SDK 的查詢參數設置（來自 create-trans-request-options.ts）
    # option.qs = { timestamp, app_key, ...option.qs };
    # 對於 AffiliateSharingLinksGenerateBatchPost，初始的 option.qs 是空的 {}
    query_params = {
        "timestamp": timestamp,
        "app_key": APP_KEY
    }
    
    # 2. 請求體（SDK 格式）
    request_body = {
        "material": {
            "id": "1731493745807886173",
            "type": "PRODUCT",
            "campaignUrl": "https://shop.tiktok.com/view/product/1731493745807886173"
        },
        "channel": "OEM3_OPPO",
        "tags": [
            "OEM3_OPPO_PUSH",
            "OEM2_VIVO_PUSH"
        ]
    }
    
    # 3. 請求選項（傳遞給 generateSign 函數）
    request_option = {
        'uri': 'https://open-api.tiktokglobalshop.com/affiliate_creator/202501/affiliate_sharing_links/generate_batch',
        'qs': query_params,
        'body': request_body,
        'headers': {
            'Content-Type': 'application/json',
            'User-Agent': 'sdk_node/1.0.0'
        }
    }
    
    print(f"📋 測試參數:")
    print(f"   時間戳: {timestamp}")
    print(f"   APP_KEY: {APP_KEY}")
    print(f"   查詢參數: {query_params}")
    print(f"   請求體: {json.dumps(request_body, indent=2, ensure_ascii=False)}")
    
    # 4. 生成簽名
    print(f"\n🔐 生成簽名:")
    signature = generate_sign_sdk_style(request_option, APP_SECRET)
    
    print(f"✅ 生成的簽名: {signature}")
    
    # 5. 最終查詢參數（添加簽名後）
    final_query_params = query_params.copy()
    final_query_params["sign"] = signature
    
    print(f"\n📤 最終查詢參數:")
    print(f"   {final_query_params}")
    
    # 6. 手動驗證簽名算法步驟
    print(f"\n🔍 手動驗證簽名算法:")
    
    # Step 1: 過濾參數（排除 access_token, sign）
    filtered_params = {k: v for k, v in query_params.items() if k not in ['access_token', 'sign']}
    print(f"   Step 1 - 過濾後參數: {filtered_params}")
    
    # Step 2: 排序並拼接
    sorted_keys = sorted(filtered_params.keys())
    param_string = ''.join([f"{key}{filtered_params[key]}" for key in sorted_keys])
    print(f"   Step 2 - 排序鍵: {sorted_keys}")
    print(f"   Step 2 - 參數字符串: {param_string}")
    
    # Step 3: 加入路徑
    api_path = "/affiliate_creator/202501/affiliate_sharing_links/generate_batch"
    path_param_string = f"{api_path}{param_string}"
    print(f"   Step 3 - 路徑+參數: {path_param_string}")
    
    # Step 4: 加入請求體
    body_json = json.dumps(request_body, separators=(',', ':'))
    full_string = f"{path_param_string}{body_json}"
    print(f"   Step 4 - 完整字符串長度: {len(full_string)}")
    print(f"   Step 4 - 完整字符串: {full_string}")
    
    # Step 5: app_secret 包裝
    wrapped_string = f"{APP_SECRET}{full_string}{APP_SECRET}"
    print(f"   Step 5 - 包裝後長度: {len(wrapped_string)}")
    
    # Step 6: HMAC-SHA256
    import hmac
    import hashlib
    hmac_obj = hmac.new(
        APP_SECRET.encode('utf-8'),
        wrapped_string.encode('utf-8'),
        hashlib.sha256
    )
    manual_signature = hmac_obj.hexdigest()
    print(f"   Step 6 - 手動計算簽名: {manual_signature}")
    
    # 對比
    if signature == manual_signature:
        print(f"\n✅ 簽名算法一致！")
    else:
        print(f"\n❌ 簽名算法不一致！")
        print(f"   SDK 風格: {signature}")
        print(f"   手動計算: {manual_signature}")
    
    return signature, final_query_params

def test_with_current_timestamp():
    """
    使用當前時間戳測試（模擬實際情況）
    """
    print(f"\n" + "=" * 80)
    print("🚀 使用當前時間戳測試（實際情況模擬）")
    print("=" * 80)
    
    # 使用當前時間戳
    current_timestamp = int(time.time())
    
    # 構建查詢參數
    query_params = {
        "timestamp": current_timestamp,
        "app_key": APP_KEY
    }
    
    # 請求體
    request_body = {
        "material": {
            "id": "1731493745807886173",
            "type": "PRODUCT",
            "campaignUrl": "https://shop.tiktok.com/view/product/1731493745807886173"
        },
        "channel": "OEM3_OPPO",
        "tags": [
            "OEM3_OPPO_PUSH",
            "OEM2_VIVO_PUSH"
        ]
    }
    
    # 請求選項
    request_option = {
        'uri': 'https://open-api.tiktokglobalshop.com/affiliate_creator/202501/affiliate_sharing_links/generate_batch',
        'qs': query_params,
        'body': request_body,
        'headers': {
            'Content-Type': 'application/json',
            'User-Agent': 'sdk_node/1.0.0'
        }
    }
    
    # 生成簽名
    signature = generate_sign_sdk_style(request_option, APP_SECRET)
    
    # 最終查詢參數
    final_query_params = query_params.copy()
    final_query_params["sign"] = signature
    
    print(f"📋 當前時間戳測試:")
    print(f"   時間戳: {current_timestamp}")
    print(f"   查詢參數: {final_query_params}")
    print(f"   簽名: {signature}")
    
    # 測試 API 調用（如果有 access token）
    try:
        import sys
        sys.path.append('.')
        import token_manager
        tm = token_manager.TokenManager()
        token_data = tm.get_valid_token()
        
        if token_data:
            access_token = token_data['access_token']
            print(f"\n📤 準備 API 調用:")
            print(f"   Access Token: {access_token[:20]}...")
            
            headers = {
                'Content-Type': 'application/json',
                'x-tts-access-token': access_token
            }
            
            import requests
            response = requests.post(
                url='https://open-api.tiktokglobalshop.com/affiliate_creator/202501/affiliate_sharing_links/generate_batch',
                params=final_query_params,
                json=request_body,
                headers=headers,
                timeout=10
            )
            
            print(f"\n📡 API 響應:")
            print(f"   狀態碼: {response.status_code}")
            if response.status_code == 200:
                print("🎉 成功！簽名正確！")
                response_data = response.json()
                print(f"   響應數據: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
            else:
                print(f"   響應內容: {response.text}")
                try:
                    error_data = response.json()
                    error_code = error_data.get('code')
                    if error_code == 106001:
                        print("❌ 簽名仍然無效")
                    else:
                        print(f"💡 其他錯誤: {error_code}")
                except:
                    pass
        else:
            print("⚠️ 沒有有效的 access token，跳過 API 測試")
    except Exception as e:
        print(f"⚠️ API 測試異常: {e}")

if __name__ == "__main__":
    # 1. 固定參數測試
    test_exact_sdk_behavior()
    
    # 2. 當前時間戳測試
    test_with_current_timestamp() 