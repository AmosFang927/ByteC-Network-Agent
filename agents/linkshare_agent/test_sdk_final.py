#!/usr/bin/env python3
"""
最终版本：直接使用SDK API调用
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

def test_final_sdk_call():
    """最终SDK调用测试"""
    logger.info("🎯 最终SDK调用测试")
    logger.info("=" * 80)
    
    try:
        # 加载token
        token_data = load_current_tokens()
        access_token = token_data.get('access_token', '')
        
        # 构建请求体 - 使用正确格式
        request_body = {
            "material": {
                "material_id": config.DEFAULT_PRODUCT_ID,
                "type": "1", 
                "campaign_url": f"https://shop.tiktok.com/view/product/{config.DEFAULT_PRODUCT_ID}"
            },
            "channel": "OEM1_XIAOMI",
            "tags": [
                "OEM1_XIOMI_PUSH_AUG",
                "OEM2_VIVO_PUSH_AUG"
            ]
        }
        
        logger.info("📋 请求信息:")
        logger.info(f"  APP_KEY: {config.APP_KEY}")
        logger.info(f"  PRODUCT_ID: {config.DEFAULT_PRODUCT_ID}")
        logger.info(f"  ACCESS_TOKEN: {access_token[:50]}...")
        logger.info(f"  REQUEST_BODY: {json.dumps(request_body, indent=2, ensure_ascii=False)}")
        
        # 创建Node.js调用脚本（CommonJS格式）
        js_code = f"""
// 使用require语法避免ES模块问题
const request = require('request');
const crypto = require('crypto');

const APP_KEY = "{config.APP_KEY}";
const APP_SECRET = "{config.APP_SECRET}";
const ACCESS_TOKEN = "{access_token}";
const API_URL = "https://open-api.tiktokglobalshop.com/affiliate_creator/202501/affiliate_sharing_links/generate_batch";

const requestBody = {json.dumps(request_body)};

console.log("🚀 开始SDK风格的API调用");
console.log("📋 配置:");
console.log("  APP_KEY:", APP_KEY);
console.log("  API_URL:", API_URL);
console.log("  REQUEST_BODY:", JSON.stringify(requestBody, null, 2));

// 使用SDK的签名逻辑
function generateSign(requestOption, appSecret) {{
    const {{ URL }} = require('url');
    
    // Step 1-2: 处理Query参数
    const params = requestOption.qs || {{}};
    const excludeKeys = ["access_token", "sign"];
    
    const sortedParams = Object.keys(params)
        .filter(key => !excludeKeys.includes(key))
        .sort()
        .map(key => ({{ key, value: params[key] }}));
    
    const paramString = sortedParams
        .map(item => `${{item.key}}${{item.value}}`)
        .join("");
    
    // Step 3: 添加路径
    const pathname = new URL(requestOption.uri).pathname;
    let signString = `${{pathname}}${{paramString}}`;
    
    // Step 4: 添加请求体
    if (requestOption.body && Object.keys(requestOption.body).length) {{
        const bodyString = JSON.stringify(requestOption.body);
        signString += bodyString;
    }}
    
    // Step 5: APP_SECRET包装
    signString = `${{appSecret}}${{signString}}${{appSecret}}`;
    
    // Step 6: HMAC-SHA256签名
    const hmac = crypto.createHmac('sha256', appSecret);
    hmac.update(signString);
    return hmac.digest('hex');
}}

const main = async () => {{
    try {{
        const timestamp = Math.floor(Date.now() / 1000).toString();
        
        // 构建签名参数
        const requestOption = {{
            uri: API_URL,
            qs: {{
                app_key: APP_KEY,
                access_token: ACCESS_TOKEN,
                timestamp: timestamp
            }},
            body: requestBody
        }};
        
        // 生成签名
        const signature = generateSign(requestOption, APP_SECRET);
        
        console.log("\\n🔐 签名信息:");
        console.log("  TIMESTAMP:", timestamp);
        console.log("  SIGNATURE:", signature);
        
        // 构建最终请求
        const finalOptions = {{
            method: 'POST',
            url: API_URL,
            qs: {{
                app_key: APP_KEY,
                timestamp: timestamp,
                sign: signature
            }},
            headers: {{
                'Content-Type': 'application/json',
                'User-Agent': 'sdk_node/1.0.0',
                'Accept': 'application/json',
                'x-tts-access-token': ACCESS_TOKEN
            }},
            json: requestBody,
            timeout: 30000
        }};
        
        console.log("\\n📡 发送请求...");
        
        request(finalOptions, (error, response, body) => {{
            if (error) {{
                console.error("\\n❌ 请求失败:", error.message);
                console.log("\\n__RESULT__");
                console.log(JSON.stringify({{ success: false, error: error.message }}));
                return;
            }}
            
            console.log("\\n📊 响应信息:");
            console.log("  HTTP状态码:", response.statusCode);
            console.log("  响应体:", JSON.stringify(body, null, 2));
            
            let result = {{ success: false }};
            
            if (response.statusCode === 200 && body && body.code === 0) {{
                console.log("\\n🎉 API调用成功!");
                result = {{ success: true, data: body }};
                
                if (body.data && body.data.sharing_infos) {{
                    console.log("\\n📝 生成的分享链接:");
                    body.data.sharing_infos.forEach((info, index) => {{
                        console.log(`  链接${{index + 1}}:`);
                        console.log(`    产品ID: ${{info.material_id || 'N/A'}}`);
                        console.log(`    分享链接: ${{info.sharing_link || 'N/A'}}`);
                        console.log(`    短链接: ${{info.short_link || 'N/A'}}`);
                    }});
                }}
            }} else {{
                console.error("\\n❌ API调用失败:");
                if (body) {{
                    console.error("  业务错误码:", body.code);
                    console.error("  错误信息:", body.message);
                    console.error("  请求ID:", body.request_id);
                    result = {{ success: false, error: body.message, code: body.code, details: body }};
                }} else {{
                    result = {{ success: false, error: `HTTP ${{response.statusCode}}` }};
                }}
            }}
            
            console.log("\\n__RESULT__");
            console.log(JSON.stringify(result));
        }});
        
    }} catch (err) {{
        console.error("\\n❌ 执行失败:", err.message);
        console.log("\\n__RESULT__");
        console.log(JSON.stringify({{ success: false, error: err.message }}));
    }}
}};

main();
"""
        
        # 写入临时文件并执行
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False, dir='agents/linkshare_agent/nodejs_sdk') as f:
            f.write(js_code)
            temp_file = f.name
        
        try:
            # 执行Node.js脚本
            result = subprocess.run(
                ['node', temp_file], 
                capture_output=True, 
                text=True, 
                cwd='agents/linkshare_agent/nodejs_sdk',
                timeout=60
            )
            
            logger.info("\\nNode.js输出:")
            logger.info(result.stdout)
            
            if result.stderr:
                logger.error("Node.js错误:")
                logger.error(result.stderr)
            
            # 解析结果
            if "__RESULT__" in result.stdout:
                result_line = result.stdout.split("__RESULT__")[-1].strip()
                try:
                    parsed_result = json.loads(result_line)
                    
                    logger.info(f"\\n📊 最终结果:")
                    logger.info(f"  成功: {parsed_result.get('success', False)}")
                    
                    if parsed_result.get('success'):
                        logger.info("🎉 SDK调用成功!")
                        return True
                    else:
                        logger.error("❌ SDK调用失败:")
                        logger.error(f"  错误: {parsed_result.get('error', '未知错误')}")
                        if 'details' in parsed_result:
                            details = parsed_result['details']
                            logger.error(f"  业务错误码: {details.get('code', 'N/A')}")
                            logger.error(f"  错误信息: {details.get('message', 'N/A')}")
                        return False
                        
                except json.JSONDecodeError as e:
                    logger.error(f"无法解析结果: {result_line}")
                    logger.error(f"JSON错误: {e}")
                    return False
            else:
                logger.error("未找到结果标记")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("Node.js执行超时")
            return False
        except Exception as e:
            logger.error(f"执行失败: {e}")
            return False
        finally:
            # 清理临时文件
            try:
                os.unlink(temp_file)
            except:
                pass
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    logger.info("🎯 开始最终SDK调用测试")
    logger.info("💡 使用SDK签名算法 + 正确Body格式")
    
    success = test_final_sdk_call()
    logger.info(f"\\n🏁 测试完成: {'成功' if success else '失败'}")
    sys.exit(0 if success else 1)
