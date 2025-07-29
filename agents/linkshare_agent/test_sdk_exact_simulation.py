"""
精確模擬 SDK 行為的測試腳本
完全按照 create-trans-request-options.ts 的邏輯執行
"""

import json
import time
import logging
from typing import Dict, Any

from signature import generate_sign_sdk_style
from config import APP_KEY, APP_SECRET, API_BASE_URL, APP_VERSION

# 設置詳細日誌
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def simulate_sdk_request_preparation():
    """
    完全模擬 SDK 的請求準備過程
    """
    print("🔬 精確模擬 SDK 請求準備過程")
    print("=" * 80)
    
    # 1. 模擬 SDK 的時間戳生成：Math.floor(Date.now() / 1000)
    timestamp = int(time.time())  # 等同於 Math.floor(Date.now() / 1000)
    
    # 2. 模擬 API 請求的初始設置（來自 affiliateCreatorV202501Api.ts）
    api_path = '/affiliate_creator/202501/affiliate_sharing_links/generate_batch'
    base_path = 'https://open-api.tiktokglobalshop.com'
    full_uri = f"{base_path}{api_path}"
    
    # 3. 模擬請求體
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
    
    print(f"📋 基礎信息:")
    print(f"   時間戳: {timestamp}")
    print(f"   API 路徑: {api_path}")
    print(f"   完整 URI: {full_uri}")
    print(f"   請求體: {json.dumps(request_body, indent=2, ensure_ascii=False)}")
    
    # 4. 模擬 create-trans-request-options.ts 的邏輯
    print(f"\n🔧 模擬 createTransRequestOptionsInterceptor:")
    
    # 初始查詢參數（在 API 調用中可能已設置的）
    initial_qs = {}  # 對於這個 API，通常開始時是空的
    
    # Step 1: 設置基本參數 (lines 25-29)
    option_qs = {
        "timestamp": timestamp,
        "app_key": APP_KEY,
        **initial_qs
    }
    print(f"   Step 1 - 設置基本參數: {option_qs}")
    
    # Step 2: 處理數組參數 (lines 31-44)
    # 這段代碼會將數組轉換為逗號分隔的字符串
    new_qs = {}
    for key in option_qs:
        element = option_qs[key]
        if isinstance(element, list):
            new_qs[key] = ",".join(map(str, element))
        else:
            new_qs[key] = element
    option_qs = new_qs
    print(f"   Step 2 - 處理數組參數: {option_qs}")
    
    # Step 3: 設置請求頭 (lines 46-51)
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "sdk_node/1.0.0"
    }
    print(f"   Step 3 - 設置請求頭: {headers}")
    
    # 5. 構建完整的請求選項 (用於簽名生成)
    request_option = {
        'uri': full_uri,
        'qs': option_qs,
        'body': request_body,
        'headers': headers
    }
    
    print(f"\n🔐 生成簽名:")
    print(f"   請求選項: {json.dumps(request_option, indent=2, ensure_ascii=False, default=str)}")
    
    # Step 4: 生成簽名 (line 53)
    signature = generate_sign_sdk_style(request_option, APP_SECRET)
    
    # Step 5: 添加簽名到查詢參數 (line 53)
    option_qs["sign"] = signature
    
    print(f"\n✅ 最終結果:")
    print(f"   最終查詢參數: {option_qs}")
    print(f"   簽名: {signature}")
    
    return {
        'timestamp': timestamp,
        'query_params': option_qs,
        'headers': headers,
        'body': request_body,
        'signature': signature,
        'uri': full_uri
    }

def test_with_real_access_token():
    """
    使用真實的 access token 進行測試
    """
    print(f"\n" + "=" * 80)
    print("🚀 使用真實 Access Token 測試")
    print("=" * 80)
    
    # 獲取真實的 access token
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    import token_manager
    tm = token_manager.TokenManager()
    token_data = tm.get_valid_token()
    
    if not token_data:
        print("❌ 無法獲取有效的 access token")
        return
    
    access_token = token_data['access_token']
    print(f"🔑 Access Token: {access_token[:20]}...")
    
    # 準備SDK風格的請求
    sdk_result = simulate_sdk_request_preparation()
    
    # 添加 access token 到請求頭（模擬 x-tts-access-token）
    headers = sdk_result['headers'].copy()
    headers['x-tts-access-token'] = access_token
    
    print(f"\n📤 發送實際API請求:")
    print(f"   URL: {sdk_result['uri']}")
    print(f"   查詢參數: {sdk_result['query_params']}")
    print(f"   請求頭: {headers}")
    print(f"   請求體: {json.dumps(sdk_result['body'], indent=2, ensure_ascii=False)}")
    
    # 發送請求
    import requests
    try:
        response = requests.post(
            url=sdk_result['uri'],
            params=sdk_result['query_params'],
            json=sdk_result['body'],
            headers=headers,
            timeout=10
        )
        
        print(f"\n📡 API 響應:")
        print(f"   狀態碼: {response.status_code}")
        print(f"   響應內容: {response.text}")
        
        if response.status_code == 200:
            print("🎉 成功！SDK 風格的簽名正確！")
        else:
            try:
                error_data = response.json()
                error_code = error_data.get('code')
                if error_code == 106001:
                    print("❌ 仍然是簽名錯誤，需要進一步調試")
                else:
                    print(f"💡 不同的錯誤碼: {error_code}，可能簽名正確但參數有問題")
            except:
                print("❌ 無法解析錯誤響應")
                
    except Exception as e:
        print(f"❌ 請求異常: {e}")

if __name__ == "__main__":
    # 1. 模擬 SDK 請求準備
    simulate_sdk_request_preparation()
    
    # 2. 使用真實 token 測試
    test_with_real_access_token() 