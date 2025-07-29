/**
 * TikTok Shop SDK 官方測試腳本
 * 直接使用官方 SDK 測試聯盟鏈接生成
 */

import { ClientConfiguration, TikTokShopNodeApiClient } from "./dist/index.js";

// 從 Python 配置中讀取的相同配置
const APP_KEY = "6gtqs1d5dtkka";
const APP_SECRET = "5965f7f420ae4ffe33eff2f48e31a7fb62a76139";
const ACCESS_TOKEN = "ROW_-TqrPAAAAACo6wRybY_AaSa6Rh6LmKbhnsroaroVrJnuzYEao1G5P2kuwL98FR_SFE4qIDBJfqiSkGpuyGPTs2NImCR5Hckm8RWBXEfdtbbMSjw50VOmog";

console.log("🚀 TikTok Shop SDK 官方測試");
console.log("=" * 80);

async function testOfficialSDK() {
    try {
        // 1. 配置全局設置
        console.log("⚙️ 配置 SDK...");
        ClientConfiguration.globalConfig.app_key = APP_KEY;
        ClientConfiguration.globalConfig.app_secret = APP_SECRET;
        
        // 2. 創建客戶端
        console.log("🔧 創建 API 客戶端...");
        const client = new TikTokShopNodeApiClient({
            config: {
                sandbox: false,  // 使用生產環境
            },
        });
        
        console.log("✅ SDK 初始化完成");
        console.log(`📋 App Key: ${APP_KEY}`);
        console.log(`🔑 Access Token: ${ACCESS_TOKEN.substring(0, 20)}...`);
        
        // 3. 準備測試數據
        const requestBody = {
            material: {
                id: "1731493745807886173",
                type: "PRODUCT",
                campaignUrl: "https://shop.tiktok.com/view/product/1731493745807886173"
            },
            channel: "OEM3_OPPO",
            tags: [
                "OEM3_OPPO_PUSH",
                "OEM2_VIVO_PUSH"
            ]
        };
        
        console.log("\n📦 請求數據:");
        console.log(JSON.stringify(requestBody, null, 2));
        
        // 4. 調用官方 SDK API
        console.log("\n🚀 調用官方 SDK API...");
        const result = await client.api.AffiliateCreatorV202501Api.AffiliateSharingLinksGenerateBatchPost(
            ACCESS_TOKEN,
            'application/json',
            requestBody
        );
        
        console.log("\n🎉 API 調用成功！");
        console.log("📡 響應狀態:", result.response.statusCode);
        console.log("📊 響應數據:", JSON.stringify(result.body, null, 2));
        
        // 5. 分析響應
        if (result.body && result.body.code === 0) {
            console.log("\n✅ 聯盟鏈接生成成功！");
            if (result.body.data && result.body.data.affiliate_sharing_links) {
                console.log(`🔗 生成了 ${result.body.data.affiliate_sharing_links.length} 個鏈接:`);
                result.body.data.affiliate_sharing_links.forEach((link, index) => {
                    console.log(`   ${index + 1}. ${link.url}`);
                });
            }
        } else {
            console.log("\n❌ API 調用返回錯誤");
            console.log(`錯誤碼: ${result.body.code}`);
            console.log(`錯誤信息: ${result.body.message}`);
        }
        
    } catch (error) {
        console.error("\n❌ SDK 測試失敗:");
        console.error("錯誤類型:", error.constructor.name);
        console.error("錯誤信息:", error.message);
        
        if (error.response) {
            console.error("HTTP 狀態碼:", error.response.statusCode);
            console.error("響應頭:", error.response.headers);
            console.error("響應體:", error.body);
        }
        
        if (error.stack) {
            console.error("詳細堆棧:");
            console.error(error.stack);
        }
    }
}

async function debugSDKRequest() {
    /**
     * 調試 SDK 的實際請求過程
     */
    console.log("\n" + "=" * 80);
    console.log("🔍 SDK 請求調試");
    console.log("=" * 80);
    
    try {
        // 導入請求生成工具
        const { generateSign } = await import("./dist/utils/generate-sign.js");
        
        // 模擬 SDK 的請求生成過程
        const timestamp = Math.floor(Date.now() / 1000);
        const requestOption = {
            uri: "https://open-api.tiktokglobalshop.com/affiliate_creator/202501/affiliate_sharing_links/generate_batch",
            qs: {
                timestamp: timestamp,
                app_key: APP_KEY
            },
            body: {
                material: {
                    id: "1731493745807886173",
                    type: "PRODUCT",
                    campaignUrl: "https://shop.tiktok.com/view/product/1731493745807886173"
                },
                channel: "OEM3_OPPO",
                tags: [
                    "OEM3_OPPO_PUSH",
                    "OEM2_VIVO_PUSH"
                ]
            },
            headers: {
                "Content-Type": "application/json",
                "User-Agent": "sdk_node/1.0.0"
            }
        };
        
        console.log("📋 請求選項:");
        console.log("   URI:", requestOption.uri);
        console.log("   查詢參數:", requestOption.qs);
        console.log("   請求體:", JSON.stringify(requestOption.body, null, 2));
        console.log("   請求頭:", requestOption.headers);
        
        // 生成簽名
        const signature = generateSign(requestOption, APP_SECRET);
        console.log("🔐 生成的簽名:", signature);
        
        // 添加簽名到查詢參數
        requestOption.qs.sign = signature;
        console.log("📤 最終查詢參數:", requestOption.qs);
        
    } catch (error) {
        console.error("❌ SDK 調試失敗:", error.message);
    }
}

// 執行測試
async function main() {
    console.log("🧪 開始 TikTok Shop SDK 測試");
    
    // 1. 官方 SDK 測試
    await testOfficialSDK();
    
    // 2. SDK 請求調試
    await debugSDKRequest();
    
    console.log("\n🎯 測試完成");
    console.log("=" * 80);
}

main().catch(error => {
    console.error("❌ 主程序異常:", error);
    process.exit(1);
}); 