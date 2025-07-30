
import { generateSign } from './dist/utils/generate-sign.js';

// 从命令行参数获取数据
const requestOptionStr = process.argv[2];
const appSecret = process.argv[3];

try {
    const requestOption = JSON.parse(requestOptionStr);
    const signature = generateSign(requestOption, appSecret);
    console.log(JSON.stringify({ success: true, signature }));
} catch (error) {
    console.log(JSON.stringify({ 
        success: false, 
        error: error.message 
    }));
}
