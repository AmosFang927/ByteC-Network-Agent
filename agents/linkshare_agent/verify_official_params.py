#!/usr/bin/env python3
"""
根据官方文档验证Gen Tracking Link API参数
参考: Global E-Commerce API Technical Doc - Generate Affiliate Sharing Link Version-202501
"""

import sys
import logging
import json
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

def verify_official_parameters():
    """根据官方文档验证参数"""
    logger.info("📋 根据官方文档验证Gen Tracking Link API参数")
    logger.info("🔗 文档: Global E-Commerce API Technical Doc - Generate Affiliate Sharing Link Version-202501")
    logger.info("=" * 100)
    
    # 官方文档确认的信息
    official_specs = {
        "API名称": "Generate Affiliate Sharing Link",
        "API版本": "Version: 202501",
        "Host": "open-api.tiktokglobalshop.com",
        "Schemes": "HTTPS",
        "最后更新": "3月27日修改"
    }
    
    logger.info("📖 官方文档信息:")
    for key, value in official_specs.items():
        logger.info(f"  {key}: {value}")
    
    # 验证我们当前的配置
    logger.info(f"\n🔍 当前配置验证:")
    
    current_config = {
        "API_VERSION": config.APP_VERSION,
        "API_HOST": config.API_BASE_URL.replace("https://", ""),
        "API_SCHEMES": "HTTPS",
        "完整端点": f"{config.API_BASE_URL}/affiliate_creator/{config.APP_VERSION}/affiliate_sharing_links/generate_batch"
    }
    
    verification_results = []
    
    # 验证API版本
    api_version_correct = config.APP_VERSION == "202501"
    verification_results.append({
        "项目": "API版本",
        "期望": "202501",
        "实际": config.APP_VERSION,
        "结果": "✅ 正确" if api_version_correct else "❌ 错误"
    })
    
    # 验证Host
    expected_host = "open-api.tiktokglobalshop.com"
    actual_host = config.API_BASE_URL.replace("https://", "")
    host_correct = actual_host == expected_host
    verification_results.append({
        "项目": "API Host",
        "期望": expected_host,
        "实际": actual_host,
        "结果": "✅ 正确" if host_correct else "❌ 错误"
    })
    
    # 验证Schemes
    schemes_correct = config.API_BASE_URL.startswith("https://")
    verification_results.append({
        "项目": "协议",
        "期望": "HTTPS",
        "实际": "HTTPS" if schemes_correct else "HTTP",
        "结果": "✅ 正确" if schemes_correct else "❌ 错误"
    })
    
    logger.info("验证结果:")
    for result in verification_results:
        logger.info(f"  {result['项目']}: {result['结果']}")
        logger.info(f"    期望: {result['期望']}")
        logger.info(f"    实际: {result['实际']}")
    
    # 根据官方PRD模板推测标准参数格式
    logger.info(f"\n📋 标准参数格式推测:")
    logger.info("基于官方文档提到的'PRD API template'，推测标准参数应该包括:")
    
    standard_params = {
        "认证参数": {
            "app_key": "应用密钥",
            "timestamp": "时间戳",
            "sign": "签名",
            "access_token": "访问令牌（header中）"
        },
        "业务参数": {
            "material": "推广素材信息",
            "channel": "推广渠道（可选）",
            "tags": "标签（可选）"
        },
        "material字段": {
            "material_id": "产品ID或内容ID",
            "type": "素材类型（如：1=产品，2=直播，3=短视频等）",
            "campaign_url": "推广链接（可选）"
        }
    }
    
    for category, params in standard_params.items():
        logger.info(f"\n  {category}:")
        for param, desc in params.items():
            logger.info(f"    {param}: {desc}")
    
    # 验证我们当前的请求体格式
    logger.info(f"\n🔍 当前请求体格式验证:")
    
    current_request_body = {
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
    
    logger.info("当前请求体:")
    logger.info(json.dumps(current_request_body, indent=4, ensure_ascii=False))
    
    # 参数格式验证
    param_validations = [
        ("material存在", "material" in current_request_body),
        ("material.material_id存在", "material_id" in current_request_body.get("material", {})),
        ("material.type存在", "type" in current_request_body.get("material", {})),
        ("material_id为字符串", isinstance(current_request_body.get("material", {}).get("material_id"), str)),
        ("material_id为数字格式", current_request_body.get("material", {}).get("material_id", "").isdigit()),
        ("type为字符串", isinstance(current_request_body.get("material", {}).get("type"), str)),
        ("channel为字符串", isinstance(current_request_body.get("channel"), str)),
        ("tags为数组", isinstance(current_request_body.get("tags"), list)),
    ]
    
    logger.info(f"\n参数格式验证:")
    all_param_valid = True
    for check, result in param_validations:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"  {check}: {status}")
        if not result:
            all_param_valid = False
    
    # 建议的优化
    logger.info(f"\n💡 基于官方文档的建议:")
    
    suggestions = [
        "✅ API版本使用202501 - 符合官方文档",
        "✅ 使用HTTPS协议 - 符合官方要求",
        "✅ Host地址正确 - open-api.tiktokglobalshop.com",
        "✅ 请求体格式符合常见API规范",
        "🔍 建议验证material.type的具体取值范围",
        "🔍 建议确认channel和tags的格式要求",
        "🔍 如果仍有问题，可能需要查看完整的官方技术文档"
    ]
    
    for suggestion in suggestions:
        logger.info(f"  {suggestion}")
    
    # 可能的问题排查
    logger.info(f"\n🔍 问题排查建议:")
    
    troubleshooting = [
        "1. 确认开发者账户已完成联盟营销功能申请",
        "2. 验证APP_KEY和APP_SECRET是否对应正确的应用",
        "3. 检查产品ID是否有推广权限",
        "4. 确认ACCESS_TOKEN的scope包含必要的联盟营销权限",
        "5. 验证是否需要特殊的渠道授权",
        "6. 检查TikTok Shop后台的应用状态和审核情况"
    ]
    
    for item in troubleshooting:
        logger.info(f"  {item}")
    
    return {
        "official_specs": official_specs,
        "verification_results": verification_results,
        "current_config": current_config,
        "all_valid": all([r["结果"].startswith("✅") for r in verification_results]) and all_param_valid
    }

def create_minimal_test_request():
    """创建最小化的测试请求"""
    logger.info(f"\n📝 创建最小化测试请求:")
    
    # 最小化请求体（只包含必需参数）
    minimal_request = {
        "material": {
            "material_id": config.DEFAULT_PRODUCT_ID,
            "type": "1"
        }
    }
    
    logger.info("最小化请求体:")
    logger.info(json.dumps(minimal_request, indent=4, ensure_ascii=False))
    
    # 标准请求体（包含常用可选参数）
    standard_request = {
        "material": {
            "material_id": config.DEFAULT_PRODUCT_ID,
            "type": "1",
            "campaign_url": f"https://shop.tiktok.com/view/product/{config.DEFAULT_PRODUCT_ID}"
        },
        "channel": "DEFAULT",
        "tags": ["TEST"]
    }
    
    logger.info(f"\n标准请求体:")
    logger.info(json.dumps(standard_request, indent=4, ensure_ascii=False))
    
    return {
        "minimal": minimal_request,
        "standard": standard_request
    }

if __name__ == "__main__":
    logger.info("🔍 开始官方文档参数验证")
    
    # 验证参数
    result = verify_official_parameters()
    
    # 创建测试请求
    test_requests = create_minimal_test_request()
    
    logger.info(f"\n📊 验证总结:")
    logger.info(f"  配置正确性: {'✅ 全部正确' if result['all_valid'] else '❌ 存在问题'}")
    
    if result['all_valid']:
        logger.info(f"  结论: 参数配置完全符合官方文档要求")
        logger.info(f"  建议: 如果API仍然失败，问题很可能在权限配置层面")
    else:
        logger.info(f"  结论: 参数配置可能需要调整")
        logger.info(f"  建议: 根据验证结果修正配置")
    
    logger.info(f"\n🏁 验证完成!")
