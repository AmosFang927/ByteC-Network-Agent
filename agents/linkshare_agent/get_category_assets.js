import { ClientConfiguration, TikTokShopNodeApiClient } from './nodejs_sdk/dist/index.js';

// 从命令行参数获取配置
const appKey = process.argv[2];
const appSecret = process.argv[3];
const accessToken = process.argv[4];

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

    console.log('📤 Get Authorized Category Assets API调用参数:');
    console.log('   App Key:', appKey);
    console.log('   Access Token:', accessToken.substring(0, 50) + '...');

    // 调用SDK的CategoryAssetsGet方法
    const main = async () => {
        try {
            console.log('🔧 调用 AuthorizationV202405Api.CategoryAssetsGet...');
            
            const result = await client.api.AuthorizationV202405Api.CategoryAssetsGet(
                accessToken,
                'application/json'
            );
            
            console.log('✅ SDK调用成功!');
            console.log('📥 HTTP状态码:', result.response.statusCode);
            console.log('📥 响应数据:', JSON.stringify(result.body, null, 2));
            
            // 检查业务逻辑返回码
            if (result.body && result.body.code === 0) {
                console.log('🎉 业务逻辑成功!');
                
                // 提取categoryAssetCipher
                const categoryAssets = result.body.data?.categoryAssets || [];
                console.log('📋 获取到的Category Assets:');
                categoryAssets.forEach((asset, index) => {
                    console.log(`   ${index + 1}. Category ID: ${asset.category?.id}`);
                    console.log(`      Category Name: ${asset.category?.name}`);
                    console.log(`      Target Market: ${asset.targetMarket}`);
                    console.log(`      Cipher: ${asset.cipher}`);
                    console.log('');
                });
                
                // 返回第一个可用的cipher，或者所有cipher供选择
                const availableCiphers = categoryAssets.map(asset => ({
                    categoryId: asset.category?.id,
                    categoryName: asset.category?.name,
                    targetMarket: asset.targetMarket,
                    cipher: asset.cipher
                }));
                
                console.log('FINAL_RESULT:' + JSON.stringify({ 
                    success: true, 
                    httpStatus: result.response.statusCode,
                    data: result.body.data,
                    categoryAssets: categoryAssets,
                    availableCiphers: availableCiphers,
                    // 默认使用第一个cipher
                    defaultCipher: availableCiphers.length > 0 ? availableCiphers[0].cipher : null
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