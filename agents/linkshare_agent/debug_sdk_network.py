"""
SDK 網路請求深度分析
模擬和對比 Node.js SDK 的實際網路請求行為
"""

import json
import time
import logging
import requests
from urllib.parse import urlencode, parse_qs, urlparse
from signature import generate_sign_sdk_style
from config import APP_KEY, APP_SECRET, APP_VERSION

# 設置詳細日誌
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def analyze_sdk_request_format():
    """
    分析 SDK 的請求格式和網路行為
    """
    print("🔬 SDK 網路請求深度分析")
    print("=" * 80)
    
    # 1. 分析時間戳格式
    print("📅 時間戳格式分析:")
    
    # Node.js: Math.floor(Date.now() / 1000)
    js_timestamp = int(time.time())  # Python 等價
    
    # 測試不同的時間戳格式
    timestamp_formats = {
        "標準 Unix 時間戳": js_timestamp,
        "字符串格式": str(js_timestamp),
        "毫秒時間戳": int(time.time() * 1000),
        "毫秒字符串": str(int(time.time() * 1000))
    }
    
    for name, ts in timestamp_formats.items():
        print(f"   {name}: {ts} (類型: {type(ts).__name__})")
    
    # 2. 分析查詢參數順序和編碼
    print(f"\n🔗 查詢參數分析:")
    
    base_params = {
        "app_key": APP_KEY,
        "timestamp": js_timestamp  # 使用標準格式
    }
    
    print(f"   基礎參數: {base_params}")
    
    # 測試不同的參數順序
    param_orders = [
        ["app_key", "timestamp"],  # 字母順序
        ["timestamp", "app_key"],  # SDK 設置順序
    ]
    
    for order in param_orders:
        ordered_params = {key: base_params[key] for key in order}
        encoded = urlencode(ordered_params)
        print(f"   順序 {order}: {encoded}")
    
    # 3. 分析請求體格式
    print(f"\n📦 請求體格式分析:")
    
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
    
    # 不同的 JSON 序列化選項
    json_formats = {
        "SDK 標準": json.dumps(request_body, separators=(',', ':')),
        "排序鍵": json.dumps(request_body, separators=(',', ':'), sort_keys=True),
        "默認格式": json.dumps(request_body),
        "縮進格式": json.dumps(request_body, indent=2)
    }
    
    for name, json_str in json_formats.items():
        print(f"   {name}: 長度 {len(json_str)}")
        print(f"   {name}: {json_str[:100]}...")
    
    # 4. 分析 HTTP 請求頭
    print(f"\n📋 HTTP 請求頭分析:")
    
    # SDK 設置的標準請求頭
    sdk_headers = {
        "Content-Type": "application/json",
        "User-Agent": "sdk_node/1.0.0",
        "Accept": "application/json"
    }
    
    print(f"   SDK 標準請求頭: {json.dumps(sdk_headers, indent=2)}")
    
    # 我們當前使用的請求頭
    our_headers = {
        "Content-Type": "application/json",
        "x-tts-access-token": "ACCESS_TOKEN_PLACEHOLDER"
    }
    
    print(f"   我們的請求頭: {json.dumps(our_headers, indent=2)}")
    
    # 對比差異
    sdk_keys = set(sdk_headers.keys())
    our_keys = set(our_headers.keys())
    
    missing_in_ours = sdk_keys - our_keys
    extra_in_ours = our_keys - sdk_keys
    
    if missing_in_ours:
        print(f"   ⚠️ 我們缺少的請求頭: {missing_in_ours}")
    if extra_in_ours:
        print(f"   ℹ️ 我們額外的請求頭: {extra_in_ours}")
    
    return js_timestamp, request_body, sdk_headers

def test_different_timestamp_formats(timestamp, request_body):
    """
    測試不同時間戳格式對簽名的影響
    """
    print(f"\n" + "=" * 80)
    print("⏰ 時間戳格式影響測試")
    print("=" * 80)
    
    # 測試不同類型的時間戳
    timestamp_tests = [
        ("整數時間戳", timestamp),
        ("字符串時間戳", str(timestamp)),
        ("前後加空格", f" {timestamp} "),
        ("零填充", f"{timestamp:010d}"),
    ]
    
    base_url = "https://open-api.tiktokglobalshop.com/affiliate_creator/202501/affiliate_sharing_links/generate_batch"
    
    for test_name, test_timestamp in timestamp_tests:
        print(f"\n🧪 測試 {test_name}: {test_timestamp} (類型: {type(test_timestamp).__name__})")
        
        # 構建請求選項
        request_option = {
            'uri': base_url,
            'qs': {
                'app_key': APP_KEY,
                'timestamp': test_timestamp
            },
            'body': request_body,
            'headers': {
                'Content-Type': 'application/json'
            }
        }
        
        try:
            signature = generate_sign_sdk_style(request_option, APP_SECRET)
            print(f"   簽名: {signature[:16]}...")
        except Exception as e:
            print(f"   ❌ 簽名生成失敗: {e}")

def test_different_header_combinations(timestamp, request_body):
    """
    測試不同請求頭組合對 API 調用的影響
    """
    print(f"\n" + "=" * 80)
    print("📋 請求頭組合測試")
    print("=" * 80)
    
    # 獲取 access token
    try:
        import sys
        sys.path.append('.')
        import token_manager
        tm = token_manager.TokenManager()
        token_data = tm.get_valid_token()
        
        if not token_data:
            print("❌ 無法獲取 access token，跳過請求頭測試")
            return
        
        access_token = token_data['access_token']
        print(f"🔑 使用 Access Token: {access_token[:20]}...")
        
    except Exception as e:
        print(f"❌ 獲取 access token 失敗: {e}")
        return
    
    base_url = "https://open-api.tiktokglobalshop.com/affiliate_creator/202501/affiliate_sharing_links/generate_batch"
    
    # 不同的請求頭組合
    header_combinations = [
        {
            "name": "最小請求頭",
            "headers": {
                "Content-Type": "application/json",
                "x-tts-access-token": access_token
            }
        },
        {
            "name": "SDK 風格請求頭",
            "headers": {
                "Content-Type": "application/json",
                "User-Agent": "sdk_node/1.0.0",
                "Accept": "application/json",
                "x-tts-access-token": access_token
            }
        },
        {
            "name": "完整請求頭",
            "headers": {
                "Content-Type": "application/json",
                "User-Agent": "sdk_node/1.0.0",
                "Accept": "application/json",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
                "x-tts-access-token": access_token
            }
        },
        {
            "name": "小寫 Content-Type",
            "headers": {
                "content-type": "application/json",
                "x-tts-access-token": access_token
            }
        }
    ]
    
    for test in header_combinations:
        print(f"\n🧪 測試 {test['name']}:")
        print(f"   請求頭: {json.dumps({k: v[:20] + '...' if k == 'x-tts-access-token' else v for k, v in test['headers'].items()}, indent=2)}")
        
        # 生成簽名
        request_option = {
            'uri': base_url,
            'qs': {
                'app_key': APP_KEY,
                'timestamp': timestamp
            },
            'body': request_body,
            'headers': test['headers']
        }
        
        signature = generate_sign_sdk_style(request_option, APP_SECRET)
        
        # 構建查詢參數
        query_params = {
            'app_key': APP_KEY,
            'timestamp': timestamp,
            'sign': signature
        }
        
        # 發送請求
        try:
            response = requests.post(
                url=base_url,
                params=query_params,
                json=request_body,
                headers=test['headers'],
                timeout=10
            )
            
            print(f"   📡 狀態碼: {response.status_code}")
            
            if response.status_code == 200:
                print("   🎉 成功！")
                response_data = response.json()
                print(f"   響應: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
                return True  # 找到成功的組合
            else:
                try:
                    error_data = response.json()
                    error_code = error_data.get('code')
                    print(f"   ❌ 錯誤碼: {error_code}")
                    if error_code != 106001:
                        print(f"   💡 不是簽名錯誤: {error_data.get('message', '')}")
                except:
                    print(f"   ❌ 響應解析失敗: {response.text[:100]}")
                    
        except Exception as e:
            print(f"   ❌ 請求異常: {e}")
    
    return False

def main():
    """
    主要的調試流程
    """
    try:
        # 1. 分析 SDK 請求格式
        timestamp, request_body, sdk_headers = analyze_sdk_request_format()
        
        # 2. 測試時間戳格式
        test_different_timestamp_formats(timestamp, request_body)
        
        # 3. 測試請求頭組合
        success = test_different_header_combinations(timestamp, request_body)
        
        if success:
            print(f"\n🎉 找到成功的請求配置！")
        else:
            print(f"\n🤔 所有測試都未成功，需要進一步分析...")
            
    except Exception as e:
        print(f"❌ 調試過程異常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 