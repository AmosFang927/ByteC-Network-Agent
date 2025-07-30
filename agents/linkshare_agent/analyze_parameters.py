#!/usr/bin/env python3
"""
详细分析Gen Tracking API的业务参数
列印所有参数并总结格式要求
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

def analyze_parameters():
    """分析所有业务参数"""
    logger.info("🔍 分析Gen Tracking API的业务参数...")
    
    logger.info("\n" + "=" * 80)
    logger.info("📋 API请求参数结构分析")
    logger.info("=" * 80)
    
    # 1. 请求体结构分析
    logger.info("\n🔧 请求体结构 (GenerateAffiliateSharingLinkRequestBody):")
    
    request_structure = {
        "channel": {
            "type": "string (可选)",
            "description": "The customized promotion channel",
            "example_values": [
                "OEM3_OPPO",
                "OEM2_VIVO", 
                "test_channel"
            ],
            "config_default": config.DEFAULT_CHANNEL
        },
        "material": {
            "type": "GenerateAffiliateSharingLinkRequestBodyMaterial (可选)",
            "description": "推广材料信息",
            "structure": {
                "id": {
                    "type": "string (可选)",
                    "description": "The ID of product/campaign/showcase that our partner wants to promote",
                    "example_values": [
                        "1731493745807886173",  # 早期测试中使用
                        config.DEFAULT_PRODUCT_ID   # 最近测试中使用
                    ]
                },
                "type": {
                    "type": "string (可选)",
                    "description": "PRODUCT, CAMPAIGN, SHOWCASE",
                    "valid_values": ["PRODUCT", "CAMPAIGN", "SHOWCASE"],
                    "usage_note": "When type==PRODUCT, use pid as id; when type==CAMPAIGN, use campaign ID as id and pass campaign_url; when type==SHOWCASE, no need to pass id and campaign_url",
                    "example_values": ["PRODUCT"]
                },
                "campaign_url": {
                    "type": "string (可选)",
                    "description": "The original url of the campaign page (only for CAMPAIGN type)",
                    "note": "只在type=CAMPAIGN时需要"
                }
            }
        },
        "tags": {
            "type": "Array<string> (可选)",
            "description": "The parameter provided for creator to record his own tracking info",
            "example_values": [
                ["OEM3_OPPO_PUSH"],
                ["OEM3_OPPO_PUSH", "TEST_TAG"],
                ["OEM2_VIVO_PUSH", "CUSTOM_TEST"]
            ],
            "config_default": config.DEFAULT_TAGS
        }
    }
    
    # 2. 打印详细参数分析
    for param_name, param_info in request_structure.items():
        logger.info(f"\n📝 {param_name.upper()}:")
        logger.info(f"   类型: {param_info['type']}")
        logger.info(f"   描述: {param_info['description']}")
        
        if 'config_default' in param_info:
            logger.info(f"   配置默认值: {param_info['config_default']}")
        
        if 'example_values' in param_info:
            logger.info(f"   示例值:")
            for example in param_info['example_values']:
                logger.info(f"     - {example}")
        
        if 'structure' in param_info:
            logger.info(f"   子结构:")
            for sub_param, sub_info in param_info['structure'].items():
                logger.info(f"     {sub_param}:")
                logger.info(f"       类型: {sub_info['type']}")
                logger.info(f"       描述: {sub_info['description']}")
                if 'valid_values' in sub_info:
                    logger.info(f"       有效值: {sub_info['valid_values']}")
                if 'example_values' in sub_info:
                    logger.info(f"       示例值: {sub_info['example_values']}")
                if 'usage_note' in sub_info:
                    logger.info(f"       使用说明: {sub_info['usage_note']}")
    
    # 3. 我们当前使用的参数分析
    logger.info("\n" + "=" * 80)
    logger.info("🔎 当前测试中使用的参数分析")
    logger.info("=" * 80)
    
    current_params = {
        "channel": config.DEFAULT_CHANNEL,
        "material": {
            "id": config.DEFAULT_PRODUCT_ID,
            "type": "PRODUCT"
        },
        "tags": config.DEFAULT_TAGS
    }
    
    logger.info(f"\n📤 当前使用的参数:")
    logger.info(json.dumps(current_params, indent=4, ensure_ascii=False))
    
    # 4. 参数验证分析
    logger.info(f"\n🔍 参数验证分析:")
    
    # Channel分析
    logger.info(f"\n✅ CHANNEL: '{current_params['channel']}'")
    logger.info(f"   - 格式: ✅ 字符串")
    logger.info(f"   - 值: ✅ 符合OEM_品牌格式")
    logger.info(f"   - 配置默认: {config.DEFAULT_CHANNEL}")
    logger.info(f"   - 匹配: {'✅ 是' if current_params['channel'] == config.DEFAULT_CHANNEL else '❌ 否'}")
    
    # Material分析
    material = current_params['material']
    logger.info(f"\n✅ MATERIAL:")
    logger.info(f"   - ID: '{material['id']}'")
    logger.info(f"     格式: ✅ 字符串")
    logger.info(f"     长度: {len(material['id'])} 字符")
    logger.info(f"     是否纯数字: {'✅ 是' if material['id'].isdigit() else '❌ 否'}")
    logger.info(f"   - TYPE: '{material['type']}'")
    logger.info(f"     格式: ✅ 字符串")
    logger.info(f"     有效值: {'✅ 有效' if material['type'] in ['PRODUCT', 'CAMPAIGN', 'SHOWCASE'] else '❌ 无效'}")
    
    # Tags分析  
    tags = current_params['tags']
    logger.info(f"\n✅ TAGS: {tags}")
    logger.info(f"   - 格式: ✅ 字符串数组")
    logger.info(f"   - 数量: {len(tags)} 个")
    logger.info(f"   - 配置默认: {config.DEFAULT_TAGS}")
    logger.info(f"   - 是否包含默认标签: {'✅ 是' if any(tag in config.DEFAULT_TAGS for tag in tags) else '❌ 否'}")
    
    # 5. 不同测试文件中的参数对比
    logger.info("\n" + "=" * 80)
    logger.info("📊 不同测试文件中的参数对比")
    logger.info("=" * 80)
    
    test_variations = [
        {
            "file": "早期测试 (final_signature_test.py等)",
            "params": {
                "channel": config.DEFAULT_CHANNEL,
                "material": {"id": "1731493745807886173", "type": "PRODUCT"},
                "tags": config.DEFAULT_TAGS
            }
        },
        {
            "file": "最近测试 (test_correct_version.py等)",
            "params": {
                "channel": config.DEFAULT_CHANNEL, 
                "material": {"id": config.DEFAULT_PRODUCT_ID, "type": "PRODUCT"},
                "tags": config.DEFAULT_TAGS
            }
        },
        {
            "file": "多标签测试 (test_sdk_signature.py)",
            "params": {
                "channel": config.DEFAULT_CHANNEL,
                "material": {"id": "1731493745807886173", "type": "PRODUCT"},
                "tags": config.DEFAULT_TAGS
            }
        }
    ]
    
    for variation in test_variations:
        logger.info(f"\n📁 {variation['file']}:")
        logger.info(f"   参数: {json.dumps(variation['params'], ensure_ascii=False)}")
    
    # 6. 可能的问题分析
    logger.info("\n" + "=" * 80)
    logger.info("🔬 可能的参数问题分析")
    logger.info("=" * 80)
    
    logger.info(f"\n🤔 可能的问题:")
    logger.info(f"1. 📋 产品ID权限问题:")
    logger.info(f"   - 当前使用ID: 7386714373631476783")
    logger.info(f"   - 早期使用ID: 1731493745807886173") 
    logger.info(f"   - 可能某个产品ID没有推广权限")
    
    logger.info(f"\n2. 📋 Channel权限问题:")
    logger.info(f"   - 当前使用: OEM3_OPPO")
    logger.info(f"   - 可能该频道没有权限或格式不正确")
    
    logger.info(f"\n3. 📋 Tags格式问题:")
    logger.info(f"   - 当前使用: ['OEM3_OPPO_PUSH']")
    logger.info(f"   - 可能标签格式或内容有限制")
    
    logger.info(f"\n4. 📋 Material类型问题:")
    logger.info(f"   - 当前使用: PRODUCT")
    logger.info(f"   - 可能需要其他类型或额外参数")
    
    # 7. 建议的测试方案
    logger.info("\n" + "=" * 80)
    logger.info("💡 建议的测试方案")
    logger.info("=" * 80)
    
    suggestions = [
        {
            "name": "使用早期成功的产品ID",
            "params": {
                "channel": config.DEFAULT_CHANNEL,
                "material": {"id": "1731493745807886173", "type": "PRODUCT"},
                "tags": config.DEFAULT_TAGS
            }
        },
        {
            "name": "简化参数测试",
            "params": {
                "material": {"id": "1731493745807886173", "type": "PRODUCT"}
            }
        },
        {
            "name": "不同Channel测试",
            "params": {
                "channel": config.DEFAULT_CHANNEL,
                "material": {"id": "1731493745807886173", "type": "PRODUCT"},
                "tags": config.DEFAULT_TAGS
            }
        }
    ]
    
    for i, suggestion in enumerate(suggestions, 1):
        logger.info(f"\n💡 建议 {i}: {suggestion['name']}")
        logger.info(f"   参数: {json.dumps(suggestion['params'], indent=6, ensure_ascii=False)}")

def main():
    """主函数"""
    logger.info("🚀 启动参数分析...")
    
    try:
        analyze_parameters()
        logger.info("\n🎉 参数分析完成!")
        return 0
    except Exception as e:
        logger.error(f"❌ 分析过程中发生错误: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 