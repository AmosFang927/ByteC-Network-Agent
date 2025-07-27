#!/usr/bin/env python3
"""
统一的Source映射工具
确保Excel生成和邮件统计使用相同的Source映射逻辑
"""

import sys
import os
import re
from typing import Dict, List, Optional

# 添加config.py路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '../..')
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from config import PARTNER_SOURCES_MAPPING
except ImportError:
    PARTNER_SOURCES_MAPPING = {}

class SourceMapper:
    """统一的Source映射器"""
    
    @staticmethod
    def map_aff_sub_to_source(aff_sub: str, partner_name: str) -> str:
        """
        将aff_sub映射到配置的Source名称
        
        Args:
            aff_sub: 原始aff_sub值 (如 "OEM2_VIVO_PUSH")
            partner_name: Partner名称 (如 "DeepLeaper")
            
        Returns:
            映射后的Source名称 (如 "VIVO")
        """
        if not aff_sub or not aff_sub.strip():
            return 'Unknown'
        
        try:
            # 获取Partner配置
            partner_config = PARTNER_SOURCES_MAPPING.get(partner_name, {})
            sources = partner_config.get('sources', [])
            
            if not sources:
                # 如果没有配置，直接使用aff_sub
                return aff_sub.strip()
            
            # 检查每个配置的source，看是否匹配
            for config_source in sources:
                # 创建匹配该source的pattern：以source名称开头或包含source名称
                patterns = [
                    f"^{config_source}.*",  # 以source开头
                    f".*{config_source}.*",  # 包含source
                ]
                
                for pattern in patterns:
                    if re.match(pattern, aff_sub, re.IGNORECASE):
                        return config_source
            
            # 如果没有匹配到任何配置的source，使用原始值
            return aff_sub.strip()
            
        except Exception:
            # 如果映射失败，使用原始值
            return aff_sub.strip()
    
    @staticmethod
    def get_sources_for_partner(partner_name: str) -> List[str]:
        """
        获取Partner配置的所有Sources
        
        Args:
            partner_name: Partner名称
            
        Returns:
            配置的Sources列表
        """
        try:
            partner_config = PARTNER_SOURCES_MAPPING.get(partner_name, {})
            return partner_config.get('sources', [])
        except Exception:
            return []
    
    @staticmethod
    def reverse_map_source_to_sheet_name(source: str, partner_name: str) -> str:
        """
        将配置的Source名称映射回Excel sheet名称
        这个方法确保Excel sheet名称和邮件统计中的Source名称一致
        
        Args:
            source: 配置的Source名称 (如 "VIVO")
            partner_name: Partner名称
            
        Returns:
            Excel sheet名称 (保持与source相同)
        """
        # 确保sheet名称符合Excel要求
        sheet_name = str(source).replace('/', '_').replace('\\', '_').replace('*', '_')
        sheet_name = sheet_name.replace('[', '_').replace(']', '_').replace(':', '_').replace('?', '_')
        
        # 限制长度
        if len(sheet_name) > 31:
            sheet_name = sheet_name[:31]
            
        return sheet_name 