"""
最終深度調試測試
逐項檢查與 SDK 的每個細微差異
"""

import json
import time
import requests
import hmac
import hashlib
from urllib.parse import urlencode
from signature import generate_sign_sdk_style
from config import APP_KEY, APP_SECRET

def manual_signature_generation(timestamp, request_body):
    """
    手動生成簽名，完全模擬 SDK 行為
    """
    print("🔧 手動簽名生成過程")
    print("-" * 60)
    
    # 1. 基礎參數（SDK 順序：timestamp, app_key）
    base_params = {
        "timestamp": timestamp,
        "app_key": APP_KEY
    }
    
    print(f"1️⃣ 基礎參數: {base_params}")
    
    # 2. 過濾和排序（SDK: 排除 access_token, sign）
    exclude_keys = ["access_token", "sign"]
    filtered_params = {k: v for k, v in base_params.items() if k not in exclude_keys}
    sorted_keys = sorted(filtered_params.keys())
    
    print(f"2️⃣ 過濾後參數: {filtered_params}")
    print(f"2️⃣ 排序後鍵: {sorted_keys}")
    
    # 3. 參數拼接
    param_string = ''.join([f"{key}{filtered_params[key]}" for key in sorted_keys])
    print(f"3️⃣ 參數字符串: {param_string}")
    
    # 4. API 路徑
    api_path = "/affiliate_creator/202501/affiliate_sharing_links/generate_batch"
    path_param_string = f"{api_path}{param_string}"
    print(f"4️⃣ 路徑+參數: {path_param_string}")
    
    # 5. 測試不同的 JSON 序列化
    json_options = [
        ("SDK 標準", json.dumps(request_body, separators=(',', ':'))),
        ("排序鍵", json.dumps(request_body, separators=(',', ':'), sort_keys=True)),
        ("默認", json.dumps(request_body)),
        ("確保ASCII", json.dumps(request_body, separators=(',', ':'), ensure_ascii=True)),
    ]
    
    signatures = []
    
    for option_name, body_str in json_options:
        print(f"\n5️⃣ 測試 {option_name} JSON:")
        print(f"   長度: {len(body_str)}")
        print(f"   內容: {body_str}")
        
        # 完整字符串
        full_string = f"{path_param_string}{body_str}"
        print(f"   完整字符串長度: {len(full_string)}")
        
        # app_secret 包裝
        wrapped_string = f"{APP_SECRET}{full_string}{APP_SECRET}"
        print(f"   包裝後長度: {len(wrapped_string)}")
        
        # HMAC-SHA256
        hmac_obj = hmac.new(
            APP_SECRET.encode('utf-8'),
            wrapped_string.encode('utf-8'),
            hashlib.sha256
        )
        signature = hmac_obj.hexdigest()
        print(f"   簽名: {signature}")
        
        signatures.append((option_name, signature))
    
    return signatures

def test_different_parameter_orders(timestamp, request_body):
    """
    測試不同的參數順序對簽名的影響
    """
    print(f"\n" + "=" * 80)
    print("🔄 參數順序測試")
    print("=" * 80)
    
    # 不同的參數順序
    param_orders = [
        ("SDK 設置順序", ["timestamp", "app_key"]),
        ("字母順序", ["app_key", "timestamp"]),
    ]
    
    base_url = "https://open-api.tiktokglobalshop.com/affiliate_creator/202501/affiliate_sharing_links/generate_batch"
    
    for order_name, order in param_orders:
        print(f"\n🧪 測試 {order_name}: {order}")
        
        # 按指定順序構建參數
        ordered_params = {}
        for key in order:
            if key == "timestamp":
                ordered_params[key] = timestamp
            elif key == "app_key":
                ordered_params[key] = APP_KEY
        
        print(f"   參數: {ordered_params}")
        
        # 生成簽名
        request_option = {
            'uri': base_url,
            'qs': ordered_params,
            'body': request_body,
            'headers': {'Content-Type': 'application/json'}
        }
        
        signature = generate_sign_sdk_style(request_option, APP_SECRET)
        print(f"   簽名: {signature}")

def test_api_with_different_configurations(timestamp, request_body, signatures):
    """
    使用不同的配置測試 API 調用
    """
    print(f"\n" + "=" * 80)
    print("🚀 API 調用測試")
    print("=" * 80)
    
    # 獲取 access token
    try:
        import sys
        sys.path.append('.')
        import token_manager
        tm = token_manager.TokenManager()
        token_data = tm.get_valid_token()
        
        if isinstance(token_data, str):
            access_token = token_data
        else:
            access_token = token_data['access_token']
        
        print(f"🔑 Access Token: {access_token[:20]}...")
        
    except Exception as e:
        print(f"❌ 獲取 access token 失敗: {e}")
        return
    
    base_url = "https://open-api.tiktokglobalshop.com/affiliate_creator/202501/affiliate_sharing_links/generate_batch"
    
    # 測試每個簽名
    for option_name, signature in signatures:
        print(f"\n🧪 測試 {option_name} 簽名:")
        print(f"   簽名: {signature[:20]}...")
        
        # 構建查詢參數
        query_params = {
            'app_key': APP_KEY,
            'timestamp': timestamp,
            'sign': signature
        }
        
        # 請求頭
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'sdk_node/1.0.0',
            'Accept': 'application/json',
            'x-tts-access-token': access_token
        }
        
        try:
            response = requests.post(
                url=base_url,
                params=query_params,
                json=request_body,
                headers=headers,
                timeout=10
            )
            
            print(f"   📡 狀態碼: {response.status_code}")
            
            if response.status_code == 200:
                print("   🎉 成功！")
                response_data = response.json()
                print(f"   響應: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
                return True
            else:
                try:
                    error_data = response.json()
                    error_code = error_data.get('code')
                    print(f"   ❌ 錯誤碼: {error_code}")
                    
                    if error_code != 106001:
                        print(f"   💡 進步了！不是簽名錯誤: {error_data.get('message', '')}")
                    
                except:
                    print(f"   ❌ 響應解析失敗: {response.text[:100]}")
                    
        except Exception as e:
            print(f"   ❌ 請求異常: {e}")
    
    return False

def main():
    """
    主要的調試流程
    """
    print("🔬 最終深度調試測試")
    print("=" * 80)
    
    # 測試數據
    timestamp = int(time.time())
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
    
    print(f"⏰ 測試時間戳: {timestamp}")
    print(f"📦 請求體: {json.dumps(request_body, indent=2, ensure_ascii=False)}")
    
    # 1. 手動簽名生成
    signatures = manual_signature_generation(timestamp, request_body)
    
    # 2. 參數順序測試
    test_different_parameter_orders(timestamp, request_body)
    
    # 3. API 調用測試
    success = test_api_with_different_configurations(timestamp, request_body, signatures)
    
    if success:
        print(f"\n🎉 找到成功的配置！")
    else:
        print(f"\n🤔 所有配置都未成功...")
        print(f"💡 可能需要檢查其他因素：")
        print(f"   - API 版本問題")
        print(f"   - 時區差異")
        print(f"   - 服務器端設置")
        print(f"   - 訪問權限問題")

if __name__ == "__main__":
    main() 