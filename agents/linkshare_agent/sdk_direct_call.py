#!/usr/bin/env python3
"""
直接调用SDK功能生成Tracking Link
使用最新的access token和config配置
"""

import sys
import logging
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent.parent))

# 导入SDK tracking link generator
from agents.linkshare_agent.sdk_tracking_link_generator import generate_tracking_links_sdk, print_tracking_links_result
from agents.linkshare_agent import config

def setup_logging():
    """设置日志配置"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )

def main():
    """直接调用SDK功能生成tracking link"""
    setup_logging()
    
    print("🚀 使用SDK直接生成Tracking Link")
    print("=" * 60)
    
    # 显示配置信息
    print("📋 使用的配置:")
    print(f"   产品ID: {config.DEFAULT_PRODUCT_ID}")
    print(f"   频道: {config.DEFAULT_CHANNEL}")
    print(f"   标签: {config.DEFAULT_TAGS}")
    print(f"   App Key: {config.APP_KEY}")
    print(f"   App Version: {config.APP_VERSION}")
    
    print("\n🔧 开始SDK风格调用...")
    
    try:
        # 直接调用SDK风格的生成函数
        result = generate_tracking_links_sdk(
            product_id=config.DEFAULT_PRODUCT_ID,
            channel=config.DEFAULT_CHANNEL,
            tags=config.DEFAULT_TAGS
        )
        
        # 打印结果
        print_tracking_links_result(result)
        
        # 总结
        if result.get("success"):
            print("\n🎉 SDK调用成功完成!")
            print("✅ Tracking Link已成功生成")
        else:
            print("\n❌ SDK调用失败")
            print(f"   错误: {result.get('error', '未知错误')}")
            return False
            
    except Exception as e:
        print(f"\n💥 SDK调用过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎯 程序执行成功!")
        sys.exit(0)
    else:
        print("\n💥 程序执行失败!")
        sys.exit(1)