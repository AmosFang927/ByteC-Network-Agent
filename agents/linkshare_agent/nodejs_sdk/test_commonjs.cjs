const { ClientConfiguration, TikTokShopNodeApiClient } = require("./dist/index.js");

console.log("🚀 使用CommonJS方式测试SDK");

// 配置
ClientConfiguration.globalConfig.app_key = "6gtqs1d5dtkka";
ClientConfiguration.globalConfig.app_secret = "5965f7f420ae4ffe33eff2f48e31a7fb62a76139";

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
console.log("  APP_KEY:", ClientConfiguration.globalConfig.app_key);
console.log("  ACCESS_TOKEN:", access_token.substring(0, 50) + "...");
console.log("  REQUEST_BODY:", JSON.stringify(requestBody, null, 2));

// 创建客户端
const client = new TikTokShopNodeApiClient({
  config: {
    sandbox: false,
  },
});

const main = async () => {
    try {
        console.log("\n🔐 正在调用SDK API...");
        
        const result = await client.api.AffiliateCreatorV202501Api.AffiliateSharingLinksGenerateBatchPost(
            access_token,
            'application/json',
            requestBody
        );
        
        console.log("\n🎉 API调用成功!");
        console.log("📊 响应数据:");
        console.log(JSON.stringify(result.body, null, 2));
        
        if (result.body && result.body.data && result.body.data.sharing_infos) {
            console.log("\n📝 生成的分享链接:");
            result.body.data.sharing_infos.forEach((info, index) => {
                console.log(`  链接${index + 1}:`);
                console.log(`    产品ID: ${info.material_id || 'N/A'}`);
                console.log(`    分享链接: ${info.sharing_link || 'N/A'}`);
                console.log(`    短链接: ${info.short_link || 'N/A'}`);
            });
        }
        
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
