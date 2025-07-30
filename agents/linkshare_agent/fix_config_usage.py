#!/usr/bin/env python3
"""
统一修复所有测试文件，确保使用config.py中的默认值
而不是硬编码的产品ID和其他参数
"""

import sys
import logging
import re
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

def fix_file_config_usage(file_path):
    """修复单个文件的config使用"""
    logger.info(f"🔧 修复文件: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes_made = []
        
        # 1. 修复硬编码的产品ID
        wrong_product_id = "7386714373631476783"
        if wrong_product_id in content:
            content = content.replace(f'"{wrong_product_id}"', 'config.DEFAULT_PRODUCT_ID')
            changes_made.append(f"替换产品ID: {wrong_product_id} -> config.DEFAULT_PRODUCT_ID")
        
        # 2. 修复硬编码的Channel
        hardcoded_channel_pattern = r'"channel":\s*"([^"]*)"'
        matches = re.findall(hardcoded_channel_pattern, content)
        for match in matches:
            if match in ["OEM3_OPPO", "test_channel"]:
                content = re.sub(
                    f'"channel":\\s*"{match}"',
                    '"channel": config.DEFAULT_CHANNEL',
                    content
                )
                changes_made.append(f"替换Channel: {match} -> config.DEFAULT_CHANNEL")
        
        # 3. 修复硬编码的Tags
        hardcoded_tags_patterns = [
            r'"tags":\s*\[\s*"([^"]*)"(?:,\s*"([^"]*)")?\s*\]',
            r'tags=\[\s*"([^"]*)"(?:,\s*"([^"]*)")?\s*\]'
        ]
        
        for pattern in hardcoded_tags_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                # 简化：直接替换为config.DEFAULT_TAGS
                if '"tags":' in content:
                    content = re.sub(
                        r'"tags":\s*\[[^\]]*\]',
                        '"tags": config.DEFAULT_TAGS',
                        content
                    )
                elif 'tags=[' in content:
                    content = re.sub(
                        r'tags=\[[^\]]*\]',
                        'tags=config.DEFAULT_TAGS',
                        content
                    )
                changes_made.append("替换Tags -> config.DEFAULT_TAGS")
                break
        
        # 4. 确保导入config
        if 'from agents.linkshare_agent import config' not in content:
            # 找到第一个import语句的位置
            lines = content.split('\n')
            import_insert_index = 0
            
            for i, line in enumerate(lines):
                if line.strip().startswith('import ') or line.strip().startswith('from '):
                    import_insert_index = i + 1
                elif line.strip() == '' and import_insert_index > 0:
                    break
            
            # 插入config导入
            if import_insert_index > 0:
                lines.insert(import_insert_index, 'from agents.linkshare_agent import config')
                content = '\n'.join(lines)
                changes_made.append("添加config导入")
        
        # 5. 保存修改
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"  ✅ 已修复，修改内容:")
            for change in changes_made:
                logger.info(f"    - {change}")
            return True
        else:
            logger.info(f"  ⏭️  无需修改")
            return False
            
    except Exception as e:
        logger.error(f"  ❌ 修复失败: {e}")
        return False

def find_test_files():
    """查找需要修复的测试文件"""
    linkshare_dir = Path(__file__).parent
    test_files = []
    
    # 查找所有test_*.py文件
    for file_path in linkshare_dir.glob("test_*.py"):
        test_files.append(file_path)
    
    # 查找其他可能的测试文件
    other_test_files = [
        "analyze_parameters.py",
        "debug_sdk_network.py",
        "final_signature_test.py"
    ]
    
    for filename in other_test_files:
        file_path = linkshare_dir / filename
        if file_path.exists():
            test_files.append(file_path)
    
    return test_files

def validate_config_values():
    """验证config中的默认值"""
    logger.info("🔍 验证config.py中的默认值...")
    
    logger.info(f"  DEFAULT_PRODUCT_ID: {config.DEFAULT_PRODUCT_ID}")
    logger.info(f"  DEFAULT_CHANNEL: {config.DEFAULT_CHANNEL}")
    logger.info(f"  DEFAULT_TAGS: {config.DEFAULT_TAGS}")
    
    # 验证值是否合理
    if not config.DEFAULT_PRODUCT_ID or not config.DEFAULT_PRODUCT_ID.isdigit():
        logger.warning(f"  ⚠️  DEFAULT_PRODUCT_ID可能不正确: {config.DEFAULT_PRODUCT_ID}")
    
    if not config.DEFAULT_CHANNEL:
        logger.warning(f"  ⚠️  DEFAULT_CHANNEL为空")
    
    if not config.DEFAULT_TAGS or not isinstance(config.DEFAULT_TAGS, list):
        logger.warning(f"  ⚠️  DEFAULT_TAGS可能不正确: {config.DEFAULT_TAGS}")

def main():
    """主函数"""
    logger.info("🚀 启动config使用统一修复...")
    
    try:
        # 1. 验证config默认值
        validate_config_values()
        
        logger.info("\n" + "=" * 80)
        logger.info("🔧 开始修复测试文件...")
        logger.info("=" * 80)
        
        # 2. 查找测试文件
        test_files = find_test_files()
        logger.info(f"📁 找到 {len(test_files)} 个测试文件:")
        for file_path in test_files:
            logger.info(f"  - {file_path.name}")
        
        # 3. 修复每个文件
        fixed_count = 0
        for file_path in test_files:
            if fix_file_config_usage(file_path):
                fixed_count += 1
        
        logger.info("\n" + "=" * 80)
        logger.info("📊 修复完成统计:")
        logger.info("=" * 80)
        logger.info(f"  总文件数: {len(test_files)}")
        logger.info(f"  已修复文件: {fixed_count}")
        logger.info(f"  无需修改文件: {len(test_files) - fixed_count}")
        
        logger.info("\n🎯 重要提醒:")
        logger.info("  所有测试现在应该使用:")
        logger.info(f"    - 产品ID: {config.DEFAULT_PRODUCT_ID}")
        logger.info(f"    - Channel: {config.DEFAULT_CHANNEL}")
        logger.info(f"    - Tags: {config.DEFAULT_TAGS}")
        
        logger.info("\n🎉 统一修复完成!")
        return 0
        
    except Exception as e:
        logger.error(f"❌ 修复过程中发生错误: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 