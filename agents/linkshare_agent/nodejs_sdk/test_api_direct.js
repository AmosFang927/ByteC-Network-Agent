import { AffiliateCreatorV202501Api } from "./dist/api/affiliateCreatorV202501Api.js";

console.log("🚀 直接使用API类测试Gen Tracking Link");

// 配置
const app_key = "6gtqs1d5dtkka";
const app_secret = "5965f7f420ae4ffe33eff2f48e31a7fb62a76139";
const access_token = "ROW_-TqrPAAAAACo6wRybY_AaSa6Rh6LmKbhnsroaroVrJnuzYEao1G5P2kuwL98FR_SFE4qIDBJfqiSkGpuyGPTs2NImCR5Hckm8RWBXEfdtbbMSjw50VOmog";

// 请求体
const requestBody = {
    "material": {
        "material_id": "1731493745807886173",
        "type": "1",
        "campaign_url": "https://shop.tiktok.com/view/product/1731493745807886173"
    },
    "channel": "OEM1_XIAOMI",
    "tags": [
        "OEM1_XIOMI_PUSH_AUG",
        "OEM2_VIVO_PUSH_AUG"
    ]
};

console.log("📋 请求配置:");
console.log("  APP_KEY:", app_key);
console.log("  ACCESS_TOKEN:", access_token.substring(0, 50) + "...");
console.log("  REQUEST_BODY:", JSON.stringify(requestBody, null, 2));

// 创建API实例
const api = new AffiliateCreatorV202501Api();

// 设置base path和认证
api.basePath = "https://open-api.tiktokglobalshop.com";

const main = async () => {
    try {
        console.log("\n🔐 正在调用API...");
        
        const result = await api.AffiliateSharingLinksGenerateBatchPost(
            access_token,
            'application/json',
            requestBody
        );
        
        console.log("\n🎉 API调用成功!");
        console.log("📊 响应数据:");
        console.log(JSON.stringify(result.body, null, 2));
        
    } catch (error) {
        console.error("\n❌ API调用失败:");
        console.error("错误类型:", error.constructor.name);
        console.error("错误消息:", error.message);
        
        if (error.response) {
            console.error("HTTP状态码:", error.response.statusCode);
        }
        
        if (error.body) {
            try {
                const errorBody = typeof error.body === 'string' ? JSON.parse(error.body) : error.body;
                console.error("业务错误码:", errorBody.code);
                console.error("错误信息:", errorBody.message);
                console.error("请求ID:", errorBody.request_id);
            } catch (parseError) {
                console.error("错误体:", error.body);
            }
        }
    }
};

main();
