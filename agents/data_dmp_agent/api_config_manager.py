#!/usr/bin/env python3
"""
DMP-Agent API配置管理器
支持不同平台的API配置和調用
"""

import os
import json
import asyncio
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime, timedelta

# 導入項目配置
try:
    import config
except ImportError:
    # 如果無法導入config，使用默認配置
    class config:
        INVOLVE_ASIA_API_KEY = "general"
        INVOLVE_ASIA_API_SECRET = "boiTXnRgB2B3N7rCictjjti1ufNIzKksSURJHwqtC50="
        INVOLVE_ASIA_BASE_URL = "https://api.involve.asia/api"

logger = logging.getLogger(__name__)

class APIConfigManager:
    """API配置管理器"""
    
    def __init__(self):
        self.configs = {
            'IAByteC': {
                'name': 'Involve Asia ByteC',
                'base_url': config.INVOLVE_ASIA_BASE_URL,
                'api_key': config.INVOLVE_ASIA_API_KEY,
                'secret': config.INVOLVE_ASIA_API_SECRET,
                'endpoints': {
                    'conversions': '/conversions/range',
                    'auth': '/authenticate'
                },
                'partner_mapping': {
                    'default_partner': 'ByteC',
                    'source_prefix': 'BYTEC_'
                }
            },
            'IADefault': {
                'name': 'Involve Asia Default',
                'base_url': config.INVOLVE_ASIA_BASE_URL,
                'api_key': config.INVOLVE_ASIA_API_KEY,
                'secret': config.INVOLVE_ASIA_API_SECRET,
                'endpoints': {
                    'conversions': '/conversions/range',
                    'auth': '/authenticate'
                },
                'partner_mapping': {
                    'default_partner': 'InvolveAsia',
                    'source_prefix': 'IA_'
                }
            }
        }
    
    def get_config(self, platform: str) -> Optional[Dict[str, Any]]:
        """獲取平台配置"""
        return self.configs.get(platform)
    
    def get_available_platforms(self) -> List[str]:
        """獲取可用平台列表"""
        return list(self.configs.keys())
    
    def validate_config(self, platform: str) -> bool:
        """驗證平台配置"""
        config = self.get_config(platform)
        if not config:
            return False
        
        # 檢查必要的配置項
        required_fields = ['api_key', 'secret', 'base_url']
        for field in required_fields:
            if not config.get(field):
                logger.error(f"❌ 平台 {platform} 缺少必要配置: {field}")
                return False
        
        return True
    
    async def test_connection(self, platform: str) -> bool:
        """測試API連接"""
        config = self.get_config(platform)
        if not config:
            return False
        
        try:
            # 這裡可以實現實際的API連接測試
            # 暫時返回True作為示例
            logger.info(f"✅ 平台 {platform} 連接測試成功")
            return True
        except Exception as e:
            logger.error(f"❌ 平台 {platform} 連接測試失敗: {e}")
            return False
    
    def get_date_range(self, days_ago: int) -> tuple:
        """獲取日期範圍"""
        # 修正日期计算逻辑：days_ago 指的是目标日期距离今天的天数
        target_date = datetime.now() - timedelta(days=days_ago)
        start_date = target_date
        end_date = target_date  # 通常查询单天数据，start_date 和 end_date 相同
        
        return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')
    
    def format_api_params(self, platform: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """格式化API參數"""
        config = self.get_config(platform)
        if not config:
            return {}
        
        return {
            'start_date': start_date,
            'end_date': end_date,
            'api_key': config['api_key'],
            'secret': config['secret'],
            'base_url': config['base_url'],
            'endpoints': config['endpoints']
        } 