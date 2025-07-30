
import { ClientConfiguration, TikTokShopNodeApiClient } from './dist/index.js';

// 从命令行参数获取配置
const appKey = process.argv[2];
const appSecret = process.argv[3];
const accessToken = process.argv[4];
const requestBodyStr = process.argv[5];

try {
    // 配置SDK
    ClientConfiguration.globalConfig.app_key = appKey;
    ClientConfiguration.globalConfig.app_secret = appSecret;

    // 创建客户端
    const client = new TikTokShopNodeApiClient({
        config: {
            sandbox: false,
        },
    });

    // 解析请求体
    const requestBody = JSON.parse(requestBodyStr);

    console.log('📤 最终SDK调用参数:');
    console.log('   App Key:', appKey);
    console.log('   Access Token:', accessToken.substring(0, 50) + '...');
    console.log('   Request Body:', JSON.stringify(requestBody, null, 2));

    // 调用SDK的AffiliateSharingLinksGenerateBatchPost方法
    const main = async () => {
        try {
            console.log('🔧 调用 AffiliateCreatorV202407Api.AffiliateSharingLinksGenerateBatchPost...');
            
            const result = await client.api.AffiliateCreatorV202407Api.AffiliateSharingLinksGenerateBatchPost(
                accessToken,
                'application/json',
                requestBody
            );
            
            console.log('✅ SDK调用成功!');
            console.log('📥 HTTP状态码:', result.response.statusCode);
            console.log('📥 响应数据:', JSON.stringify(result.body, null, 2));
            
            // 检查业务逻辑返回码
            if (result.body && result.body.code === 0) {
                console.log('🎉 业务逻辑成功!');
                console.log('FINAL_RESULT:' + JSON.stringify({ 
                    success: true, 
                    httpStatus: result.response.statusCode,
                    data: result.body 
                }));
            } else {
                console.log('❌ 业务逻辑错误:', result.body.message || '未知错误');
                console.log('FINAL_RESULT:' + JSON.stringify({ 
                    success: false, 
                    httpStatus: result.response.statusCode,
                    businessError: true,
                    error: result.body.message || '未知业务错误',
                    code: result.body.code,
                    data: result.body 
                }));
            }
        } catch (error) {
            console.log('❌ SDK调用失败:', error.message);
            console.log('🔍 错误详情:', error);
            console.log('FINAL_RESULT:' + JSON.stringify({ 
                success: false, 
                error: error.message,
                details: error.toString()
            }));
        }
    };

    main();
} catch (error) {
    console.log('❌ 初始化失败:', error.message);
    console.log('FINAL_RESULT:' + JSON.stringify({ 
        success: false, 
        error: error.message 
    }));
}
