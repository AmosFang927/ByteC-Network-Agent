#!/usr/bin/env python3
"""
API版本兼容性深度测试
测试不同API版本对tracking link生成的影响
"""

import sys
import logging
import time
import requests
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.linkshare_agent import config
from agents.linkshare_agent.token_manager import TokenManager
from agents.linkshare_agent.sdk_signature import generate_sign_sdk_style

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class APIVersionTester:
    """API版本测试器"""
    
    def __init__(self):
        self.token_manager = TokenManager()
        self.access_token = self.token_manager.get_valid_token()
        
    def test_api_version(self, version: str) -> dict:
        """测试特定API版本"""
        print(f"\n🧪 测试API版本: {version}")
        print("-" * 50)
        
        # 构建API URL
        api_url = f"{config.API_BASE_URL}/affiliate_creator/{version}/affiliate_sharing_links/generate_batch"
        print(f"📡 API端点: {api_url}")
        
        # 准备请求数据
        timestamp = str(int(time.time()))
        query_params = {
            "app_key": config.APP_KEY,
            "timestamp": timestamp
        }
        
        request_body = {
            "material": {
                "id": config.DEFAULT_PRODUCT_ID,
                "type": config.MATERIAL_TYPE_PRODUCT,
                "campaignUrl": config.CAMPAIGN_URL_TEMPLATE.format(product_id=config.DEFAULT_PRODUCT_ID)
            },
            "channel": config.DEFAULT_CHANNEL,
            "tags": config.DEFAULT_TAGS
        }
        
        # 准备SDK签名请求
        sdk_request_option = {
            'uri': api_url,
            'qs': query_params,
            'body': request_body,
            'headers': config.BASE_HEADERS
        }
        
        try:
            # 生成签名
            signature = generate_sign_sdk_style(sdk_request_option, config.APP_SECRET)
            print(f"🔐 签名生成成功: {signature[:16]}...")
            
            # 构建最终请求参数
            final_query_params = {
                **query_params,
                "sign": signature
            }
            
            # 发送请求
            headers = config.get_api_headers(self.access_token)
            
            response = requests.post(
                url=api_url,
                params=final_query_params,
                json=request_body,
                headers=headers,
                timeout=(config.CONNECT_TIMEOUT, config.REQUEST_TIMEOUT)
            )
            
            print(f"📊 HTTP状态码: {response.status_code}")
            
            result = {
                "version": version,
                "http_status": response.status_code,
                "success": False,
                "api_code": None,
                "message": "",
                "request_id": "",
                "error_type": ""
            }
            
            if response.status_code == 200:
                response_data = response.json()
                api_code = response_data.get('code', -1)
                result.update({
                    "api_code": api_code,
                    "message": response_data.get('message', ''),
                    "request_id": response_data.get('request_id', ''),
                    "success": api_code == 0
                })
                
                if api_code == 0:
                    print(f"🎉 API调用成功!")
                    data = response_data.get('data', {})
                    links = data.get('affiliate_sharing_links', [])
                    print(f"🔗 成功生成 {len(links)} 个链接")
                else:
                    print(f"❌ API错误: {api_code} - {response_data.get('message', '')}")
                    result["error_type"] = f"API_ERROR_{api_code}"
            else:
                try:
                    error_data = response.json()
                    result.update({
                        "api_code": error_data.get('code'),
                        "message": error_data.get('message', ''),
                        "request_id": error_data.get('request_id', '')
                    })
                    print(f"❌ HTTP错误: {response.status_code} - {error_data.get('message', '')}")
                    result["error_type"] = f"HTTP_ERROR_{response.status_code}"
                except:
                    print(f"❌ HTTP错误: {response.status_code} - 无法解析响应")
                    result["error_type"] = f"HTTP_ERROR_{response.status_code}_PARSE_FAILED"
            
            return result
            
        except Exception as e:
            print(f"❌ 请求异常: {e}")
            return {
                "version": version,
                "success": False,
                "error_type": "EXCEPTION",
                "message": str(e),
                "http_status": None,
                "api_code": None,
                "request_id": ""
            }

def main():
    """主测试函数"""
    print("🔍 TikTok Shop API版本兼容性深度测试")
    print("🎯 目标：找到最兼容的API版本")
    print("=" * 70)
    
    # 验证配置和Token
    try:
        config.validate_config()
        print("✅ config.py配置验证通过")
        
        tm = TokenManager()
        access_token = tm.get_valid_token()
        print(f"✅ Access Token获取成功: {access_token[:20]}...")
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return 1
    
    # 要测试的API版本（从最稳定到最新）
    test_versions = [
        "202407",  # 2024年7月 - 较早稳定版本
        "202409",  # 2024年9月
        "202410",  # 2024年10月
        "202412",  # 2024年12月 - 最新稳定版本
        "202501",  # 2025年1月 - 当前使用
        "202505"   # 2025年5月 - 最新版本
    ]
    
    tester = APIVersionTester()
    results = []
    
    for version in test_versions:
        try:
            result = tester.test_api_version(version)
            results.append(result)
            time.sleep(1)  # 避免请求过快
        except KeyboardInterrupt:
            print("\n⚠️ 用户中断测试")
            break
        except Exception as e:
            print(f"❌ 版本 {version} 测试异常: {e}")
    
    # 分析结果
    print(f"\n{'='*70}")
    print("📊 API版本测试结果汇总")
    print("=" * 70)
    
    success_versions = []
    failed_versions = []
    
    for result in results:
        version = result["version"]
        if result["success"]:
            print(f"✅ {version}: 成功 - {result.get('message', 'Success')}")
            success_versions.append(version)
        else:
            error_info = f"{result['error_type']} - {result.get('message', 'Unknown error')}"
            print(f"❌ {version}: 失败 - {error_info}")
            failed_versions.append((version, result))
    
    print(f"\n🎯 测试总结:")
    print(f"   成功版本: {len(success_versions)}/{len(results)}")
    print(f"   失败版本: {len(failed_versions)}/{len(results)}")
    
    if success_versions:
        print(f"\n🎉 可用的API版本:")
        for version in success_versions:
            print(f"   ✅ {version}")
        print(f"\n💡 建议使用版本: {success_versions[0]} (最稳定)")
    else:
        print(f"\n⚠️ 所有版本都失败了，错误模式分析:")
        error_patterns = {}
        for version, result in failed_versions:
            error_type = result.get('error_type', 'UNKNOWN')
            if error_type not in error_patterns:
                error_patterns[error_type] = []
            error_patterns[error_type].append(version)
        
        for error_type, versions in error_patterns.items():
            print(f"   {error_type}: {', '.join(versions)}")
        
        # 如果所有版本都是相同错误，说明问题不在版本
        if len(error_patterns) == 1:
            error_type = list(error_patterns.keys())[0]
            print(f"\n💡 结论: 所有版本都返回相同错误 ({error_type})")
            print(f"   这表明问题不在API版本，而在于其他因素：")
            print(f"   - 账户配置问题")
            print(f"   - 产品ID无效")
            print(f"   - 权限范围限制")
    
    return 0 if success_versions else 1

if __name__ == "__main__":
    sys.exit(main()) 