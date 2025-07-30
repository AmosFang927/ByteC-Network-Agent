#!/usr/bin/env python3
"""
直接使用 Node.js SDK 的测试
"""

import subprocess
import json
import logging
from pathlib import Path
import sys

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.linkshare_agent import config

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_nodejs_direct():
    """直接使用 Node.js SDK 测试"""
    logger.info("🔐 开始直接使用 Node.js SDK 测试...")
    
    try:
        # 1. 准备测试数据
        request_data = {
            "material": {
                "id": "1731493745807886173",
                "type": "1"
            },
            "channel": config.DEFAULT_CHANNEL,
            "tags": config.DEFAULT_TAGS
        }
        
        # 2. 准备请求参数
        import time
        timestamp = str(int(time.time()))
        request_params = {
            "app_key": config.APP_KEY,
            "timestamp": timestamp
        }
        
        # 3. 构建完整 URL
        full_url = f"{config.API_BASE_URL}/affiliate_creator/{config.APP_VERSION}/affiliate_sharing_links/generate_batch"
        
        # 4. 准备请求选项
        request_option = {
            'uri': full_url,
            'qs': request_params,
            'body': request_data,
            'headers': {
                'Content-Type': 'application/json'
            }
        }
        
        # 5. 创建 Node.js 测试脚本
        sdk_path = Path(__file__).parent / "nodejs_sdk"
        test_script = sdk_path / "test-sign.js"
        
        script_content = """
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
"""
        
        with open(test_script, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        logger.info(f"📝 测试脚本已创建: {test_script}")
        
        # 6. 执行 Node.js 测试
        cmd = [
            "node",
            str(test_script),
            full_url,
            json.dumps(request_params),
            json.dumps(request_data),
            json.dumps({'Content-Type': 'application/json'}),
            config.APP_SECRET
        ]
        
        logger.info("🚀 执行 Node.js 测试...")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=sdk_path,
            timeout=30
        )
        
        if result.returncode != 0:
            logger.error(f"❌ Node.js 测试失败: {result.stderr}")
            return False
        
        logger.info("📥 Node.js 输出:")
        logger.info(result.stdout)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 测试过程中发生错误: {e}")
        return False

def main():
    """主函数"""
    logger.info("🚀 启动直接使用 Node.js SDK 的测试...")
    
    success = test_nodejs_direct()
    
    if success:
        logger.info("🎉 测试完成!")
        return 0
    else:
        logger.error("❌ 测试失败!")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 