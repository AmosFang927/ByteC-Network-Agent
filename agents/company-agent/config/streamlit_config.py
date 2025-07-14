#!/usr/bin/env python3
"""
公司財務AI助手 - Streamlit 配置文件
Company Finance AI Assistant - Streamlit Configuration
"""

import os
from typing import Dict, Any

class StreamlitConfig:
    """Streamlit 應用配置"""
    
    # 應用基本配置
    APP_TITLE = "公司財務AI助手"
    APP_ICON = "💰"
    PAGE_LAYOUT = "wide"
    SIDEBAR_STATE = "expanded"
    
    # API配置
    API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:5001")
    API_TIMEOUT = 30
    HEALTH_CHECK_TIMEOUT = 5
    
    # WhoJDB配置
    WHODB_CONFIG = {
        'base_url': os.getenv("WHODB_BASE_URL", "http://localhost:8080"),
        'username': os.getenv("WHODB_USERNAME", "admin"),
        'password': os.getenv("WHODB_PASSWORD", "password")
    }
    
    # 數據庫配置
    DATABASE_CONFIG = {
        'host': os.getenv("DB_HOST", "localhost"),
        'port': int(os.getenv("DB_PORT", "5432")),
        'database': os.getenv("DB_NAME", "bytec_network"),
        'user': os.getenv("DB_USER", "postgres"),
        'password': os.getenv("DB_PASSWORD", "password")
    }
    
    # Streamlit伺服器配置
    SERVER_CONFIG = {
        'port': int(os.getenv("STREAMLIT_PORT", "8501")),
        'address': os.getenv("STREAMLIT_ADDRESS", "0.0.0.0"),
        'headless': True,
        'browser_server_address': "localhost"
    }
    
    # 快速查詢配置
    QUICK_QUERIES = [
        "今天的收入是多少？",
        "本月毛利率怎麼樣？",
        "哪個合作夥伴表現最好？",
        "現金流狀況如何？",
        "最近一週的轉化趨勢",
        "今天有多少轉化？",
        "本季度財務表現如何？",
        "最大支出項目是什麼？"
    ]
    
    # 圖表配置
    CHART_CONFIG = {
        'theme': 'streamlit',
        'use_container_width': True,
        'height': 400
    }
    
    # 指標卡片配置
    METRICS_CONFIG = {
        'total_revenue': {
            'label': '💰 總收入',
            'format': '${:,.2f}',
            'delta_format': '{:.1f}%'
        },
        'gross_margin': {
            'label': '📈 毛利率',
            'format': '{:.1f}%',
            'delta_format': '{:.1f}%'
        },
        'total_conversions': {
            'label': '🔄 轉化數',
            'format': '{:,}',
            'delta_format': '{:.1f}%'
        },
        'cash_flow': {
            'label': '💵 現金流',
            'format': '${:,.2f}',
            'delta_format': '{:.1f}%'
        }
    }
    
    # 樣式配置
    CUSTOM_CSS = """
    <style>
        .main > div {
            padding-top: 2rem;
        }
        .stChat {
            background-color: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            margin: 10px 0;
        }
        .metric-card {
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            border: 1px solid #e1e5e9;
            margin: 10px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .success-message {
            background-color: #d4edda;
            color: #155724;
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #c3e6cb;
            margin: 10px 0;
        }
        .error-message {
            background-color: #f8d7da;
            color: #721c24;
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #f5c6cb;
            margin: 10px 0;
        }
        .sidebar .sidebar-content {
            padding-top: 1rem;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 24px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            padding-left: 20px;
            padding-right: 20px;
        }
    </style>
    """
    
    # 預設儀表板數據（用於演示）
    DEFAULT_DASHBOARD_DATA = {
        'total_revenue': 125000,
        'revenue_growth': 8.5,
        'gross_margin': 42.3,
        'margin_change': 2.1,
        'total_conversions': 1250,
        'conversion_growth': 15.8,
        'cash_flow': 28000,
        'cash_flow_change': 12.4,
        'revenue_trend': [
            {'date': '2024-01-01', 'revenue': 4200},
            {'date': '2024-01-02', 'revenue': 4350},
            {'date': '2024-01-03', 'revenue': 4100},
            {'date': '2024-01-04', 'revenue': 4500},
            {'date': '2024-01-05', 'revenue': 4800}
        ],
        'partner_performance': [
            {'partner': 'ByteC', 'revenue': 50000},
            {'partner': 'InvolveAsia', 'revenue': 35000},
            {'partner': 'MKK', 'revenue': 25000},
            {'partner': 'DeepLeaper', 'revenue': 15000}
        ]
    }
    
    @classmethod
    def get_api_url(cls, endpoint: str) -> str:
        """獲取API完整URL"""
        return f"{cls.API_BASE_URL}{endpoint}"
    
    @classmethod
    def get_whodb_config(cls) -> Dict[str, Any]:
        """獲取WhoJDB配置"""
        return cls.WHODB_CONFIG.copy()
    
    @classmethod
    def get_database_config(cls) -> Dict[str, Any]:
        """獲取數據庫配置"""
        return cls.DATABASE_CONFIG.copy()
    
    @classmethod
    def get_server_config(cls) -> Dict[str, Any]:
        """獲取伺服器配置"""
        return cls.SERVER_CONFIG.copy()

# 創建全局配置實例
config = StreamlitConfig() 