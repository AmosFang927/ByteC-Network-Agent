#!/usr/bin/env python3
"""
使用Python调用SDK的完整实现
直接调用SDK API，不手动处理签名
"""

import sys
import logging
import json
import subprocess
import tempfile
import os
from pathlib import Path

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

def call_sdk_api_direct(request_body, access_token):
    """直接调用SDK API"""
    
    # 创建CommonJS格式的Node.js脚本（避免ES module问题）
    js_code = f"""
const {{ AffiliateCreatorV202501Api }} = require('./dist/api/affiliateCreatorV202501Api');
const {{ DefaultApiAuthentication }} = require('./dist/client/config');

// 创建API实例
const api = new AffiliateCreatorV202501Api.AffiliateCreatorV202501Api();

// 配置认证
api.setDefaultAuthentication(new DefaultApiAuthentication.DefaultApiAuthentication({{
    app_key: "{config.APP_KEY}",
    app_secret: "{config.APP_SECRET}"
}}));

// 设置base path
api.basePath = "https://open-api.tiktokglobalshop.com";

const requestBody = {json.dumps(request_body)};
const accessToken = "{access_token}";

console.log("🚀 开始使用SDK调用API");
console.log("📋 配置信息:");
console.log("  APP_KEY:", "{config.APP_KEY}");
console.log("  BASE_PATH:", api.basePath);
console.log("  REQUEST_BODY:", JSON.stringify(requestBody, null, 2));

// 调用API
const main = async () => {{
    try {{
        console.log("\\n🔐 正在调用SDK...");
        
        const result = await api.affiliateSharingLinksGenerateBatchPost(
            accessToken,
            'application/json', 
            requestBody
        );
        
        console.log("\\n🎉 API调用成功!");
        console.log("📊 响应数据:");
        console.log(JSON.stringify(result.body, null, 2));
        
        // 输出结果供Python解析
        console.log("\\n__PYTHON_RESULT__");
        console.log(JSON.stringify({{ success: true, data: result.body }}));
        
    }} catch (error) {{
        console.error("\\n❌ API调用失败:");
        console.error("错误信息:", error.message);
        
        let errorData = {{ success: false, error: error.message }};
        
        // 尝试解析错误详情
        if (error.body) {{
            try {{
                const errorBody = typeof error.body === 'string' ? JSON.parse(error.body) : error.body;
                errorData.details = errorBody;
                console.error("业务错误码:", errorBody.code);
                console.error("错误详情:", errorBody.message);
                console.error("请求ID:", errorBody.request_id);
            }} catch (parseError) {{
                errorData.raw_body = error.body;
                console.error("错误体:", error.body);
            }}
        }}
        
        console.log("\\n__PYTHON_RESULT__");
        console.log(JSON.stringify(errorData));
    }}
}};

main().catch(console.error);
"""
    
    # 写入临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False, dir='agents/linkshare_agent/nodejs_sdk') as f:
        f.write(js_code)
        temp_file = f.name
    
    try:
        # 执行Node.js脚本
        result = subprocess.run(
            ['node', temp_file], 
            capture_output=True, 
            text=True, 
            cwd='agents/linkshare_agent/nodejs_sdk'
        )
        
        logger.info("Node.js输出:")
        logger.info(result.stdout)
        
        if result.stderr:
            logger.error("Node.js错误:")
            logger.error(result.stderr)
        
        # 解析结果
        if "__PYTHON_RESULT__" in result.stdout:
            result_line = result.stdout.split("__PYTHON_RESULT__")[-1].strip()
            try:
                return json.loads(result_line)
            except json.JSONDecodeError:
                logger.error(f"无法解析结果: {result_line}")
                return {"success": False, "error": "结果解析失败"}
        else:
            return {"success": False, "error": "未找到结果标记"}
            
    except Exception as e:
        logger.error(f"执行失败: {e}")
        return {"success": False, "error": str(e)}
    finally:
        # 清理临时文件
        try:
            os.unlink(temp_file)
        except:
            pass

def test_sdk_wrapper():
    """测试SDK封装"""
    logger.info("🎯 测试SDK Python封装")
    logger.info("=" * 80)
    
    try:
        # 加载token
        token_data = load_current_tokens()
        access_token = token_data.get('access_token', '')
        
        # 构建请求体
        request_body = {{
            "material": {{
                "material_id": config.DEFAULT_PRODUCT_ID,
                "type": "1",
                "campaign_url": f"https://shop.tiktok.com/view/product/{config.DEFAULT_PRODUCT_ID}"
            }},
            "channel": "OEM1_XIAOMI",
            "tags": [
                "OEM1_XIOMI_PUSH_AUG",
                "OEM2_VIVO_PUSH_AUG"
            ]
        }}
        
        logger.info("📋 请求信息:")
        logger.info(f"  PRODUCT_ID: {config.DEFAULT_PRODUCT_ID}")
        logger.info(f"  ACCESS_TOKEN: {access_token[:50]}...")
        logger.info(f"  REQUEST_BODY: {json.dumps(request_body, indent=2, ensure_ascii=False)}")
        
        # 调用SDK
        result = call_sdk_api_direct(request_body, access_token)
        
        logger.info(f"\\n📊 最终结果:")
        logger.info(f"  成功: {result.get('success', False)}")
        
        if result.get('success'):
            logger.info("🎉 API调用成功!")
            data = result.get('data', {{}})
            if data.get('data', {{}}).get('sharing_infos'):
                logger.info("📝 生成的分享链接:")
                for i, info in enumerate(data['data']['sharing_infos'], 1):
                    logger.info(f"  链接{i}:")
                    logger.info(f"    产品ID: {info.get('material_id', 'N/A')}")
                    logger.info(f"    分享链接: {info.get('sharing_link', 'N/A')}")
                    logger.info(f"    短链接: {info.get('short_link', 'N/A')}")
        else:
            logger.error("❌ API调用失败:")
            logger.error(f"  错误: {result.get('error', '未知错误')}")
            if 'details' in result:
                details = result['details']
                logger.error(f"  业务错误码: {details.get('code', 'N/A')}")
                logger.error(f"  错误信息: {details.get('message', 'N/A')}")
                logger.error(f"  请求ID: {details.get('request_id', 'N/A')}")
        
        return result.get('success', False)
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_sdk_wrapper()
    logger.info(f"\\n🏁 测试完成: {'成功' if success else '失败'}")
    sys.exit(0 if success else 1)
