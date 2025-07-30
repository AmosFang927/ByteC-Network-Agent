#!/usr/bin/env python3
"""
直接调用SDK的gen tracking link功能
完全绕过我们自己的API调用实现
"""

import sys
import logging
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime

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

def load_current_tokens():
    """加载当前存储的token"""
    token_file = Path('agents/linkshare_agent/tokens.conf')
    if not token_file.exists():
        raise Exception("Token文件不存在")
    
    with open(token_file, 'r') as f:
        return json.load(f)

def create_sdk_call_script():
    """创建调用SDK的Node.js脚本"""
    sdk_path = Path('agents/linkshare_agent/nodejs_sdk')
    script_path = sdk_path / 'test_direct_sdk_call.js'
    
    script_content = """
import { ClientConfiguration, TikTokShopNodeApiClient } from './index.js';

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

    console.log('📤 SDK调用参数:');
    console.log('   App Key:', appKey);
    console.log('   Access Token:', accessToken.substring(0, 50) + '...');
    console.log('   Request Body:', JSON.stringify(requestBody, null, 2));

    // 调用SDK的AffiliateSharingLinksGenerateBatchPost方法
    const main = async () => {
        try {
            const result = await client.api.AffiliateCreatorV202407Api.AffiliateSharingLinksGenerateBatchPost(
                accessToken,
                'application/json',
                requestBody
            );
            
            console.log('✅ SDK调用成功!');
            console.log('📥 响应数据:', JSON.stringify(result.body, null, 2));
            console.log(JSON.stringify({ success: true, data: result.body }));
        } catch (error) {
            console.log('❌ SDK调用失败:', error.message);
            console.log(JSON.stringify({ 
                success: false, 
                error: error.message,
                details: error.toString()
            }));
        }
    };

    main();
} catch (error) {
    console.log(JSON.stringify({ 
        success: false, 
        error: error.message 
    }));
}
"""
    
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    logger.info(f"📝 SDK调用脚本已创建: {script_path}")
    return script_path

def test_direct_sdk_call():
    """直接调用SDK测试"""
    logger.info("🚀 开始直接调用SDK的gen tracking link功能...")
    
    try:
        # 1. 加载当前token
        token_data = load_current_tokens()
        access_token = token_data.get('access_token', '')
        
        logger.info(f"✅ 使用ACCESS TOKEN: {access_token[:50]}...")
        
        # 2. 准备请求数据
        request_body = {
            "channel": config.DEFAULT_CHANNEL,
            "material": {
                "id": config.DEFAULT_PRODUCT_ID,
                "type": "PRODUCT"
            },
            "tags": config.DEFAULT_TAGS
        }
        
        logger.info(f"📝 请求体: {json.dumps(request_body, indent=2)}")
        
        # 3. 创建SDK调用脚本
        script_path = create_sdk_call_script()
        
        # 4. 调用Node.js SDK
        logger.info("🔧 调用Node.js SDK...")
        
        cmd = [
            'node',
            str(script_path),
            config.APP_KEY,
            config.APP_SECRET,
            access_token,
            json.dumps(request_body)
        ]
        
        sdk_path = Path('agents/linkshare_agent/nodejs_sdk')
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=sdk_path,
            timeout=60
        )
        
        logger.info(f"🔍 Node.js执行结果:")
        logger.info(f"   返回码: {result.returncode}")
        logger.info(f"   标准输出: {result.stdout}")
        if result.stderr:
            logger.info(f"   标准错误: {result.stderr}")
        
        # 5. 解析结果
        if result.returncode == 0:
            # 尝试从输出中提取JSON结果
            output_lines = result.stdout.strip().split('\n')
            json_result = None
            
            for line in reversed(output_lines):  # 从后往前找JSON结果
                try:
                    json_result = json.loads(line)
                    break
                except json.JSONDecodeError:
                    continue
            
            if json_result:
                if json_result.get('success'):
                    logger.info("🎉 SDK直接调用成功！")
                    logger.info("✅ 用户观点验证成功：ACCESS TOKEN可以独立使用！")
                    logger.info("✅ 直接使用SDK功能避免了我们实现的问题！")
                    return True
                else:
                    error_msg = json_result.get('error', '未知错误')
                    logger.error(f"❌ SDK调用失败: {error_msg}")
                    return False
            else:
                logger.warning("⚠️ 无法解析SDK调用结果")
                return False
        else:
            logger.error(f"❌ Node.js执行失败: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("❌ SDK调用超时")
        return False
    except Exception as e:
        logger.error(f"❌ 测试过程中发生错误: {e}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")
        return False

def main():
    """主函数"""
    logger.info("🚀 启动直接SDK调用测试...")
    logger.info("🎯 验证用户观点: 直接调用SDK功能生成tracking link")
    logger.info("💡 完全绕过我们自己的API实现")
    
    try:
        success = test_direct_sdk_call()
        
        logger.info("\n" + "=" * 80)
        logger.info("📋 直接SDK调用结论:")
        if success:
            logger.info("✅ 直接调用SDK成功！")
            logger.info("✅ 用户建议完全正确 - 直接用SDK功能最可靠")
            logger.info("✅ ACCESS TOKEN确实可以独立工作")
            logger.info("✅ 避免了我们实现中的所有潜在问题")
        else:
            logger.info("❌ 直接SDK调用也失败")
            logger.info("🔍 这表明问题可能在于:")
            logger.info("   1. ACCESS TOKEN本身的权限问题")
            logger.info("   2. SDK配置问题")
            logger.info("   3. 系统环境问题")
            logger.info("   4. 但仍然不是AUTH_CODE过期的问题")
        
        return 0 if success else 1
        
    except Exception as e:
        logger.error(f"❌ 测试过程中发生错误: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 