#!/usr/bin/env python3
"""
测试SDK风格的Tracking Link生成功能
所有参数从config.py获取
"""

import sys
import logging
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.linkshare_agent.sdk_tracking_link_generator import (
    generate_tracking_links_sdk, 
    print_tracking_links_result,
    SDKTrackingLinkGenerator
)
from agents.linkshare_agent import config

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_sdk_function_direct():
    """测试直接调用SDK函数"""
    print("🧪 测试1: 直接调用SDK函数 (使用config.py默认参数)")
    print("=" * 70)
    
    # 使用config.py中的所有默认参数
    result = generate_tracking_links_sdk()
    
    # 打印结果
    print_tracking_links_result(result)
    
    return result.get("success", False)

def test_sdk_function_custom():
    """测试自定义参数调用SDK函数"""
    print("\n🧪 测试2: 自定义参数调用SDK函数")
    print("=" * 70)
    
    # 自定义部分参数，其他从config.py获取
    result = generate_tracking_links_sdk(
        product_id=config.DEFAULT_PRODUCT_ID,  # 明确指定产品ID
        channel="TEST_CHANNEL",  # 自定义频道
        tags=["TEST_TAG_1", "TEST_TAG_2"]  # 自定义标签
    )
    
    # 打印结果
    print_tracking_links_result(result)
    
    return result.get("success", False)

def test_sdk_class_usage():
    """测试SDK类的使用"""
    print("\n🧪 测试3: 使用SDK类")
    print("=" * 70)
    
    try:
        # 创建生成器实例
        generator = SDKTrackingLinkGenerator()
        
        # 调用生成函数
        result = generator.generate_tracking_links()
        
        # 打印结果
        print_tracking_links_result(result)
        
        return result.get("success", False)
        
    except Exception as e:
        print(f"❌ SDK类测试失败: {e}")
        return False

def test_config_parameters():
    """测试config.py参数"""
    print("\n🧪 测试4: 验证config.py参数")
    print("=" * 70)
    
    print(f"📋 当前config.py配置:")
    print(f"   DEFAULT_PRODUCT_ID: {config.DEFAULT_PRODUCT_ID}")
    print(f"   DEFAULT_CHANNEL: {config.DEFAULT_CHANNEL}")
    print(f"   DEFAULT_TAGS: {config.DEFAULT_TAGS}")
    print(f"   MATERIAL_TYPE_PRODUCT: {config.MATERIAL_TYPE_PRODUCT}")
    print(f"   CAMPAIGN_URL_TEMPLATE: {config.CAMPAIGN_URL_TEMPLATE}")
    print(f"   APP_KEY: {config.APP_KEY[:10]}...")
    print(f"   APP_VERSION: {config.APP_VERSION}")
    
    # 测试URL生成
    test_url = config.CAMPAIGN_URL_TEMPLATE.format(product_id=config.DEFAULT_PRODUCT_ID)
    print(f"   生成的Campaign URL: {test_url}")
    
    return True

def main():
    """主测试函数"""
    print("🚀 SDK风格Tracking Link生成功能测试")
    print("🎯 所有参数从config.py获取")
    print("=" * 70)
    
    # 验证配置
    try:
        config.validate_config()
        print("✅ config.py配置验证通过")
    except Exception as e:
        print(f"❌ config.py配置验证失败: {e}")
        return 1
    
    # 运行测试
    tests = [
        ("配置参数验证", test_config_parameters),
        ("直接调用SDK函数", test_sdk_function_direct),
        ("自定义参数调用", test_sdk_function_custom),
        ("SDK类使用", test_sdk_class_usage)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*20} {test_name} {'='*20}")
            success = test_func()
            results.append((test_name, success))
            print(f"✅ {test_name}: {'成功' if success else '失败'}")
        except Exception as e:
            print(f"❌ {test_name}: 异常 - {e}")
            results.append((test_name, False))
    
    # 打印测试总结
    print(f"\n{'='*70}")
    print("📊 测试结果总结:")
    success_count = sum(1 for _, success in results if success)
    total_count = len(results)
    
    for test_name, success in results:
        status = "✅ 成功" if success else "❌ 失败"
        print(f"   {test_name}: {status}")
    
    print(f"\n🎯 总体结果: {success_count}/{total_count} 成功")
    
    if success_count == total_count:
        print("🎉 所有测试通过!")
        return 0
    else:
        print("⚠️ 部分测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 