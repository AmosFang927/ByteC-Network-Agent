
import { generateSign } from './dist/utils/generate-sign.js';

// 测试数据
const requestOption = {
    uri: process.argv[2],
    qs: JSON.parse(process.argv[3]),
    body: JSON.parse(process.argv[4]),
    headers: JSON.parse(process.argv[5])
};

const appSecret = process.argv[6];

try {
    console.log('🔐 开始生成签名...');
    console.log('📋 请求选项:', JSON.stringify(requestOption, null, 2));
    console.log('🔑 App Secret:', appSecret);
    
    const signature = generateSign(requestOption, appSecret);
    
    console.log('✅ 签名生成成功!');
    console.log('🔐 签名:', signature);
    console.log('📏 签名长度:', signature.length);
    
    // 输出用于调试的信息
    console.log('📊 调试信息:');
    console.log('- URI:', requestOption.uri);
    console.log('- 查询参数:', JSON.stringify(requestOption.qs));
    console.log('- 请求体:', JSON.stringify(requestOption.body));
    console.log('- 请求头:', JSON.stringify(requestOption.headers));
    
} catch (error) {
    console.error('❌ 签名生成失败:', error.message);
    process.exit(1);
}
