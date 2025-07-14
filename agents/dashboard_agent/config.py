#!/usr/bin/env python3
"""
Dashboard配置文件
"""

import os
from typing import Dict, Any

class Config:
    """配置类"""
    
    # 数据库配置
    DB_CONFIG = {
        "host": os.getenv("DB_HOST", "34.124.206.16"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "database": os.getenv("DB_NAME", "postback_db"),
        "user": os.getenv("DB_USER", "postback_admin"),
        "password": os.getenv("DB_PASSWORD", "ByteC2024PostBack_CloudSQL")
    }
    
    # 应用配置
    APP_CONFIG = {
        "name": "ByteC Performance Dashboard",
        "version": "1.0.0",
        "debug": os.getenv("DEBUG", "False").lower() == "true",
        "port": int(os.getenv("PORT", "5000")),
        "host": os.getenv("HOST", "0.0.0.0")
    }
    
    # 前端配置
    FRONTEND_CONFIG = {
        "theme": "light",
        "auto_refresh": False,
        "refresh_interval": 30,  # 秒
        "chart_colors": {
            "primary": "#1f77b4",
            "secondary": "#ff7f0e", 
            "success": "#2ca02c",
            "warning": "#d62728",
            "info": "#9467bd",
            "light": "#8c564b",
            "dark": "#e377c2"
        }
    }
    
    # API配置
    API_CONFIG = {
        "timeout": 30,
        "max_page_size": 1000,
        "default_page_size": 50,
        "cache_ttl": 300  # 5分钟
    }
    
    # 导出配置
    EXPORT_CONFIG = {
        "timeout": 1800,  # 30分钟
        "max_date_range": 90,  # 最大90天
        "allowed_formats": ["xlsx", "csv", "json"]
    }
    
    @classmethod
    def get_db_config(cls) -> Dict[str, Any]:
        """获取数据库配置"""
        return cls.DB_CONFIG.copy()
    
    @classmethod
    def get_app_config(cls) -> Dict[str, Any]:
        """获取应用配置"""
        return cls.APP_CONFIG.copy()
    
    @classmethod
    def get_frontend_config(cls) -> Dict[str, Any]:
        """获取前端配置"""
        return cls.FRONTEND_CONFIG.copy()
    
    @classmethod
    def get_api_config(cls) -> Dict[str, Any]:
        """获取API配置"""
        return cls.API_CONFIG.copy()
    
    @classmethod
    def get_export_config(cls) -> Dict[str, Any]:
        """获取导出配置"""
        return cls.EXPORT_CONFIG.copy() 