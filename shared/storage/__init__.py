#!/usr/bin/env python3
"""
共享存儲模組
Shared Storage Module

統一的存儲接口層，所有 agent 都通過此模組訪問 DMP-Agent 的存儲服務
"""

from .storage_client import (
    StorageClient,
    APIAgentStorage,
    DashboardAgentStorage,
    ReporterAgentStorage,
    get_storage_client,
    create_api_agent_storage,
    create_dashboard_agent_storage,
    create_reporter_agent_storage,
    with_storage_client
)

__all__ = [
    # 核心類
    'StorageClient',
    'APIAgentStorage',
    'DashboardAgentStorage', 
    'ReporterAgentStorage',
    
    # 工廠函數
    'get_storage_client',
    'create_api_agent_storage',
    'create_dashboard_agent_storage',
    'create_reporter_agent_storage',
    
    # 裝飾器
    'with_storage_client',
]

__version__ = '1.0.0' 