#!/usr/bin/env python3
"""
共享資料庫模組
Shared Database Module

統一的資料庫訪問層，提供高性能的資料庫管理功能
"""

from .enhanced_database_manager import (
    EnhancedDatabaseManager,
    DatabaseConfig,
    QueryMetrics,
    ConnectionPoolMonitor,
    SmartCache,
    get_database_manager,
    execute_query,
    get_conversions
)

__all__ = [
    'EnhancedDatabaseManager',
    'DatabaseConfig', 
    'QueryMetrics',
    'ConnectionPoolMonitor',
    'SmartCache',
    'get_database_manager',
    'execute_query',
    'get_conversions'
]

__version__ = '1.0.0' 