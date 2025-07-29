"""
簽名對比測試腳本
比較我們的簽名算法和 SDK 風格簽名算法的差異
"""

import json
import time
import logging
from typing import Dict, Any

from signature import generate_sign, generate_sign_sdk_style
from config import APP_KEY, APP_SECRET, API_BASE_URL, APP_VERSION

# 設置詳細日誌
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def create_test_request_option() -> Dict[str, Any]:
    """
    創建測試用的請求選項，模擬聯盟鏈接生成的真實參數
    """
    timestamp = str(int(time.time()))
    
    # API 路徑
    api_path = '/affiliate_creator/202501/affiliate_sharing_links/generate_batch'
    full_url = f'{API_BASE_URL}{api_path}'
    
    # 查詢參數（模擬我們實際發送的參數）
    query_params = {
        'app_key': APP_KEY,
        'timestamp': timestamp,
        'version': APP_VERSION,
        'access_token': 'ROW_test_access_token_for_comparison'  # 測試用 token
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
    
    # 請求頭
    headers = {
        'Content-Type': 'application/json',
        'x-tts-access-token': 'ROW_test_access_token_for_comparison'
    }
    
    # 構建請求選項
    request_option = {
        'uri': full_url,
        'qs': query_params,
        'body': request_body,
        'headers': headers
    }
    
    return request_option, timestamp

def compare_signatures():
    """
    對比兩種簽名算法的結果
    """
    print("🔍 簽名對比測試開始")
    print("=" * 80)
    
    # 創建測試參數
    request_option, timestamp = create_test_request_option()
    
    print(f"📋 測試配置:")
    print(f"   時間戳: {timestamp}")
    print(f"   API_KEY: {APP_KEY}")
    print(f"   API_SECRET: {APP_SECRET[:8]}...")
    print(f"   版本: {APP_VERSION}")
    
    print(f"\n📦 請求參數:")
    print(f"   URI: {request_option['uri']}")
    print(f"   查詢參數: {request_option['qs']}")
    print(f"   請求體: {json.dumps(request_option['body'], indent=2, ensure_ascii=False)}")
    print(f"   請求頭: {request_option['headers']}")
    
    print("\n" + "=" * 80)
    print("🆚 簽名算法對比")
    print("=" * 80)
    
    # 測試我們原來的簽名算法
    print("\n🔴 原始簽名算法:")
    try:
        original_sign = generate_sign(request_option, APP_SECRET)
        print(f"   ✅ 原始簽名: {original_sign}")
    except Exception as e:
        print(f"   ❌ 原始簽名失敗: {e}")
        original_sign = "ERROR"
    
    # 測試 SDK 風格的簽名算法
    print("\n🟢 SDK 風格簽名算法:")
    try:
        sdk_sign = generate_sign_sdk_style(request_option, APP_SECRET)
        print(f"   ✅ SDK 簽名: {sdk_sign}")
    except Exception as e:
        print(f"   ❌ SDK 簽名失敗: {e}")
        sdk_sign = "ERROR"
    
    print("\n" + "=" * 80)
    print("📊 對比結果")
    print("=" * 80)
    
    if original_sign != "ERROR" and sdk_sign != "ERROR":
        if original_sign == sdk_sign:
            print("✅ 兩種簽名完全相同！")
        else:
            print("❌ 兩種簽名不同！")
            print(f"   原始簽名: {original_sign}")
            print(f"   SDK 簽名:  {sdk_sign}")
            
            # 字符對比
            print(f"\n🔍 字符差異分析:")
            for i, (c1, c2) in enumerate(zip(original_sign, sdk_sign)):
                if c1 != c2:
                    print(f"   第 {i} 個字符不同: '{c1}' vs '{c2}'")
                    break
    else:
        print("⚠️ 其中一個或兩個簽名生成失敗")
    
    print("\n" + "=" * 80)
    print("🎯 測試結論")
    print("=" * 80)
    
    if original_sign != "ERROR" and sdk_sign != "ERROR" and original_sign == sdk_sign:
        print("🎉 簽名算法已正確！可以直接使用原始算法。")
    else:
        print("💡 需要使用 SDK 風格的簽名算法來修復問題。")
    
    return {
        'original_sign': original_sign,
        'sdk_sign': sdk_sign,
        'are_equal': original_sign == sdk_sign and original_sign != "ERROR"
    }

if __name__ == "__main__":
    result = compare_signatures()
    
    if not result['are_equal']:
        print(f"\n🔧 建議下一步:")
        print(f"   1. 使用 SDK 風格簽名算法")
        print(f"   2. 更新 link_generator.py 使用新的簽名方法")
        print(f"   3. 重新測試聯盟鏈接生成") 