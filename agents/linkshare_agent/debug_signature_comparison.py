#!/usr/bin/env python3
"""
比较原始signature和SDK signature的差异
"""

import sys
import logging
import time
import json
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.linkshare_agent.signature import generate_sign_sdk_style as original_signature
from agents.linkshare_agent.sdk_signature import generate_sign_sdk_style as sdk_signature
from agents.linkshare_agent import config

# 设置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def compare_signatures():
    """比较两种签名方法的差异"""
    logger.info("🔍 开始比较原始signature和SDK signature的差异...")
    
    try:
        # 1. 准备测试数据
        request_data = {
            "material": {
                "id": "1731493745807886173",
                "type": "1"
            },
            "channel": "OEM3_OPPO",
            "tags": ["OEM3_OPPO_PUSH"]
        }
        
        # 2. 准备请求参数
        timestamp = str(int(time.time()))
        request_params = {
            "app_key": config.APP_KEY,
            "access_token": "test_token",  # 添加测试token
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
        
        logger.info(f"📋 请求选项:")
        logger.info(f"   URI: {full_url}")
        logger.info(f"   查询参数: {request_params}")
        logger.info(f"   请求体: {json.dumps(request_data, indent=2)}")
        
        # 5. 使用原始签名方法
        logger.info("\n" + "="*60)
        logger.info("🔄 使用原始签名方法")
        logger.info("="*60)
        
        original_sign = original_signature(request_option, config.APP_SECRET)
        logger.info(f"🔐 原始签名: {original_sign}")
        
        # 6. 使用SDK签名方法
        logger.info("\n" + "="*60)
        logger.info("🆕 使用SDK签名方法")
        logger.info("="*60)
        
        sdk_sign = sdk_signature(request_option, config.APP_SECRET)
        logger.info(f"🔐 SDK签名: {sdk_sign}")
        
        # 7. 比较结果
        logger.info("\n" + "="*60)
        logger.info("📊 比较结果")
        logger.info("="*60)
        
        logger.info(f"原始签名: {original_sign}")
        logger.info(f"SDK签名:  {sdk_sign}")
        
        if original_sign == sdk_sign:
            logger.info("✅ 签名一致!")
        else:
            logger.warning("❌ 签名不一致!")
            logger.info(f"   长度差异: 原始({len(original_sign)}) vs SDK({len(sdk_sign)})")
            
            # 逐字符比较
            min_len = min(len(original_sign), len(sdk_sign))
            for i in range(min_len):
                if original_sign[i] != sdk_sign[i]:
                    logger.info(f"   第{i}个字符开始不同: '{original_sign[i]}' vs '{sdk_sign[i]}'")
                    logger.info(f"   原始从{i}开始: {original_sign[i:i+10]}...")
                    logger.info(f"   SDK从{i}开始:  {sdk_sign[i:i+10]}...")
                    break
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 比较过程中发生错误: {e}")
        return False

def main():
    """主函数"""
    logger.info("🚀 启动签名比较...")
    
    success = compare_signatures()
    
    if success:
        logger.info("🎉 比较完成!")
        return 0
    else:
        logger.error("❌ 比较失败!")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 