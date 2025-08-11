import { ClientConfiguration, TikTokShopNodeApiClient } from './nodejs_sdk/dist/index.js';

// 从命令行参数获取配置
const appKey = process.argv[2];
const appSecret = process.argv[3];
const accessToken = process.argv[4];
const requestBodyStr = process.argv[5];
const categoryAssetCipher = process.argv[6];
const pageSize = process.argv[7];
const pageToken = process.argv[8];

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

    console.log('📤 Search Tap Affiliate Orders API调用参数:');
    console.log('   App Key:', appKey);
    console.log('   Access Token:', accessToken.substring(0, 50) + '...');
    console.log('   Category Asset Cipher:', categoryAssetCipher);
    console.log('   Page Size:', pageSize);
    console.log('   Page Token:', pageToken || 'N/A');

    // 解析请求体
    let requestBody = null;
    if (requestBodyStr && requestBodyStr !== 'null') {
        try {
            requestBody = JSON.parse(requestBodyStr);
            console.log('📋 请求体:', JSON.stringify(requestBody, null, 2));
        } catch (e) {
            console.log('⚠️ 请求体解析失败:', e.message);
        }
    }

    // 调用SDK的OrdersSearchPost方法
    const main = async () => {
        try {
            console.log('🔧 调用 AffiliatePartnerV202411Api.OrdersSearchPost...');
            
            const result = await client.api.AffiliatePartnerV202411Api.OrdersSearchPost(
                parseInt(pageSize),
                categoryAssetCipher,
                accessToken,
                'application/json',
                pageToken || undefined,
                requestBody
            );
            
            console.log('✅ SDK调用成功!');
            console.log('📥 HTTP状态码:', result.response.statusCode);
            console.log('📥 响应数据:', JSON.stringify(result.body, null, 2));
            
            // 检查业务逻辑返回码
            if (result.body && result.body.code === 0) {
                console.log('🎉 业务逻辑成功!');
                
                // 提取订单数据
                const orders = result.body.data?.orders || [];
                const totalCount = result.body.data?.totalCount || 0;
                const nextPageToken = result.body.data?.nextPageToken;
                
                console.log('📊 订单统计:');
                console.log(`   总订单数: ${totalCount}`);
                console.log(`   当前页订单数: ${orders.length}`);
                console.log(`   下一页Token: ${nextPageToken || 'N/A'}`);
                
                // 显示前几个订单的基本信息
                orders.slice(0, 3).forEach((order, index) => {
                    console.log(`   📦 订单 ${index + 1}:`);
                    console.log(`      ID: ${order.orderId}`);
                    console.log(`      状态: ${order.status}`);
                    console.log(`      金额: ${order.orderAmount}`);
                    console.log(`      创建时间: ${new Date(order.createTime * 1000).toISOString()}`);
                });
                
                console.log('FINAL_RESULT:' + JSON.stringify({ 
                    success: true, 
                    httpStatus: result.response.statusCode,
                    data: result.body.data,
                    orders: orders,
                    totalCount: totalCount,
                    nextPageToken: nextPageToken
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