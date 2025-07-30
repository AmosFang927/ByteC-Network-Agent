/**
 * 簡單的 SDK 測試腳本
 * 直接使用 SDK 的簽名功能和 HTTP 請求
 */

import https from 'https';
import { URL } from 'url';

// 導入 SDK 的簽名函數（編譯後的版本）
import { generateSign } from './dist/utils/generate-sign.js';

// 配置
const APP_KEY = "6gtqs1d5dtkka";
const APP_SECRET = "5965f7f420ae4ffe33eff2f48e31a7fb62a76139";
const ACCESS_TOKEN = "ROW_fcKgrgAAAACo6wRybY_AaSa6Rh6LmKbhnsroaroVrJnuzYEao1G5Px53OOhwfbmQhsOzkOb9z8u2fgQi28keGaCT-eKwVdL2iAI4S_f3oR06JfsPtjrfRw";

console.log("🧪 簡單 SDK 測試");
console.log("=" * 80);

async function testWithSDKSignature() {
    try {
        console.log("⚙️ 使用官方 SDK 簽名函數測試...");
        
        // 1. 準備請求數據
        const timestamp = Math.floor(Date.now() / 1000);
        const requestBody = {
            material: {
                id: "1731493745807886173",
                type: "1",  // 改為數字字符串，如 Python 實現中使用的
                campaignUrl: "https://shop.tiktok.com/view/product/1731493745807886173"
            },
            channel: "OEM3_OPPO",
            tags: [
                "L_OEM1_XIAOMI_PUSH_ID",
                "L_OEM3_OPPO_PUSH_ID",
                "L_OEM2_VIVO_PUSH_ID"
            ]
        };
        
        console.log(`⏰ 時間戳: ${timestamp}`);
        console.log("📦 請求體:", JSON.stringify(requestBody, null, 2));
        
        // 2. 構建請求選項（完全按照 SDK 方式）
        const requestOption = {
            uri: "https://open-api.tiktokglobalshop.com/affiliate_creator/202501/affiliate_sharing_links/generate_batch",
            qs: {
                timestamp: timestamp,
                app_key: APP_KEY
            },
            body: requestBody,
            headers: {
                "Content-Type": "application/json",
                "User-Agent": "sdk_node/1.0.0"
            }
        };
        
        console.log("📋 請求選項:");
        console.log("   URI:", requestOption.uri);
        console.log("   查詢參數:", requestOption.qs);
        console.log("   請求頭:", requestOption.headers);
        
        // 3. 使用 SDK 生成簽名
        console.log("🔐 使用 SDK 生成簽名...");
        const signature = generateSign(requestOption, APP_SECRET);
        console.log("✅ 簽名生成成功:", signature);
        
        // 4. 添加簽名到查詢參數
        requestOption.qs.sign = signature;
        console.log("📤 最終查詢參數:", requestOption.qs);
        
        // 5. 構建完整的 URL
        const url = new URL(requestOption.uri);
        Object.keys(requestOption.qs).forEach(key => {
            url.searchParams.append(key, requestOption.qs[key]);
        });
        
        console.log("🌐 完整 URL:", url.toString());
        
        // 6. 發送 HTTP 請求
        console.log("🚀 發送 HTTP 請求...");
        
        const requestData = JSON.stringify(requestBody);
        
        const options = {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'User-Agent': 'sdk_node/1.0.0',
                'Accept': 'application/json',
                'x-tts-access-token': ACCESS_TOKEN,
                'Content-Length': Buffer.byteLength(requestData)
            }
        };
        
        console.log("📤 HTTP 請求頭:", options.headers);
        
        const response = await makeHttpRequest(url, options, requestData);
        
        console.log("📡 HTTP 響應:");
        console.log("   狀態碼:", response.statusCode);
        console.log("   響應頭:", response.headers);
        console.log("   響應體:", response.body);
        
        // 7. 分析結果
        if (response.statusCode === 200) {
            console.log("🎉 API 調用成功！");
            try {
                const responseData = JSON.parse(response.body);
                console.log("📊 解析後的響應:", JSON.stringify(responseData, null, 2));
                
                if (responseData.code === 0) {
                    console.log("✅ 聯盟鏈接生成成功！");
                } else {
                    console.log(`❌ API 返回錯誤碼: ${responseData.code}`);
                    console.log(`❌ 錯誤信息: ${responseData.message}`);
                }
            } catch (e) {
                console.log("⚠️ 響應體解析失敗:", e.message);
            }
        } else {
            console.log("❌ HTTP 請求失敗");
            try {
                const errorData = JSON.parse(response.body);
                console.log(`❌ 錯誤碼: ${errorData.code}`);
                console.log(`❌ 錯誤信息: ${errorData.message}`);
                
                if (errorData.code === 106001) {
                    console.log("💡 這是簽名錯誤，說明即使使用官方 SDK 也有同樣問題！");
                } else {
                    console.log("💡 不是簽名錯誤，可能是其他問題");
                }
            } catch (e) {
                console.log("❌ 錯誤響應解析失敗");
            }
        }
        
    } catch (error) {
        console.error("❌ 測試失敗:", error.message);
        console.error("詳細錯誤:", error);
    }
}

function makeHttpRequest(url, options, data) {
    return new Promise((resolve, reject) => {
        const req = https.request(url, options, (res) => {
            let body = '';
            
            res.on('data', (chunk) => {
                body += chunk;
            });
            
            res.on('end', () => {
                resolve({
                    statusCode: res.statusCode,
                    headers: res.headers,
                    body: body
                });
            });
        });
        
        req.on('error', (error) => {
            reject(error);
        });
        
        if (data) {
            req.write(data);
        }
        
        req.end();
    });
}

// 執行測試
testWithSDKSignature().catch(error => {
    console.error("❌ 主程序異常:", error);
    process.exit(1);
}); 