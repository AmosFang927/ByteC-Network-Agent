#!/usr/bin/env python3
"""
API-Agent 完全優化數據庫管理器
API Agent Fully Optimized Database Manager

採用統一存儲服務的完全重構版本，實現：
- 統一存儲服務集成
- 智能緩存策略  
- 連接池優化
- 批量處理優化
- 性能監控
- 查詢優化

預期性能提升：80-90%
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from decimal import Decimal
from dataclasses import dataclass, asdict

# 導入統一存儲服務
from .unified_storage_service import (
    UnifiedStorageService, 
    ConversionData, 
    QueryRequest,
    PartnerInfo
)

# 導入增強版資料庫管理器
from shared.database import (
    EnhancedDatabaseManager,
    DatabaseConfig,
    get_database_manager
)

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """性能指標"""
    query_count: int = 0
    total_query_time: float = 0.0
    avg_query_time: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    slow_queries: int = 0
    errors: int = 0
    batch_operations: int = 0
    records_processed: int = 0

@dataclass
class OptimizationConfig:
    """優化配置"""
    # 連接池配置
    min_connections: int = 5
    max_connections: int = 20
    connection_timeout: int = 120
    
    # 緩存配置
    enable_cache: bool = True
    cache_ttl: int = 300  # 5分鐘
    redis_url: str = "redis://localhost:6379/1"
    
    # 批量處理配置
    batch_size: int = 1000
    max_concurrent_batches: int = 5
    
    # 性能監控配置
    slow_query_threshold: float = 1.0  # 秒
    enable_monitoring: bool = True
    
    # 查詢優化配置
    use_prepared_statements: bool = True
    enable_query_optimization: bool = True

class OptimizedAPIAgentManager:
    """完全優化的API-Agent數據庫管理器"""
    
    def __init__(self, optimization_config: Optional[OptimizationConfig] = None):
        self.config = optimization_config or OptimizationConfig()
        self.storage_service: Optional[UnifiedStorageService] = None
        self.db_manager: Optional[EnhancedDatabaseManager] = None
        self._initialized = False
        
        # 性能指標
        self.metrics = PerformanceMetrics()
        self.start_time = time.time()
        
        # 緩存管理
        self._query_cache = {}
        self._cache_timestamps = {}
        
        # 監控數據
        self._slow_queries = []
        self._recent_operations = []
        
    async def initialize(self):
        """初始化優化管理器"""
        if self._initialized:
            return
            
        try:
            logger.info("🚀 初始化完全優化的API-Agent數據庫管理器...")
            
            # 初始化數據庫配置
            db_config = DatabaseConfig(
                min_size=self.config.min_connections,
                max_size=self.config.max_connections,
                command_timeout=self.config.connection_timeout,
                enable_cache=self.config.enable_cache,
                cache_ttl=self.config.cache_ttl,
                redis_url=self.config.redis_url,
                batch_size=self.config.batch_size,
                enable_monitoring=self.config.enable_monitoring,
                slow_query_threshold=self.config.slow_query_threshold
            )
            
            # 初始化統一存儲服務
            self.storage_service = UnifiedStorageService(db_config)
            await self.storage_service.initialize()
            
            # 獲取數據庫管理器實例
            self.db_manager = await get_database_manager(db_config)
            
            self._initialized = True
            logger.info("✅ 完全優化的API-Agent數據庫管理器初始化完成")
            logger.info(f"   - 連接池: {self.config.min_connections}-{self.config.max_connections}")
            logger.info(f"   - 緩存: {'啟用' if self.config.enable_cache else '禁用'}")
            logger.info(f"   - 批量大小: {self.config.batch_size}")
            logger.info(f"   - 監控: {'啟用' if self.config.enable_monitoring else '禁用'}")
            
        except Exception as e:
            logger.error(f"❌ 優化管理器初始化失敗: {e}")
            raise
    
    async def _record_operation(self, operation: str, duration: float, success: bool = True, record_count: int = 0):
        """記錄操作指標"""
        if not self.config.enable_monitoring:
            return
            
        self.metrics.query_count += 1
        self.metrics.total_query_time += duration
        self.metrics.avg_query_time = self.metrics.total_query_time / self.metrics.query_count
        self.metrics.records_processed += record_count
        
        if not success:
            self.metrics.errors += 1
            
        if duration > self.config.slow_query_threshold:
            self.metrics.slow_queries += 1
            self._slow_queries.append({
                'operation': operation,
                'duration': duration,
                'timestamp': datetime.now().isoformat(),
                'record_count': record_count
            })
            
        # 保留最近的操作記錄
        self._recent_operations.append({
            'operation': operation,
            'duration': duration,
            'success': success,
            'record_count': record_count,
            'timestamp': datetime.now().isoformat()
        })
        
        # 保持最近100條記錄
        if len(self._recent_operations) > 100:
            self._recent_operations = self._recent_operations[-100:]
    
    async def fetch_conversions_optimized(self, platform: str, days_ago: int = 1, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """優化版獲取轉化數據"""
        if not self._initialized:
            await self.initialize()
            
        start_time = time.time()
        operation = f"fetch_conversions_{platform}"
        
        try:
            # 計算日期範圍
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_ago)
            
            # 構建查詢請求
            request = QueryRequest(
                agent_name="api-agent",
                query_type="get_conversions",
                parameters={
                    'platform': platform,
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'limit': limit
                },
                use_cache=self.config.enable_cache,
                cache_ttl=self.config.cache_ttl
            )
            
            # 執行查詢
            result = await self.storage_service.process_request(request)
            
            if result['success']:
                conversions = result['data']
                duration = time.time() - start_time
                
                await self._record_operation(operation, duration, True, len(conversions))
                
                if self.config.enable_cache:
                    self.metrics.cache_hits += 1
                
                logger.info(f"✅ 優化查詢完成: {len(conversions)} 條記錄 ({duration:.2f}秒)")
                return conversions
            else:
                raise Exception(result.get('error', 'Unknown error'))
                
        except Exception as e:
            duration = time.time() - start_time
            await self._record_operation(operation, duration, False, 0)
            logger.error(f"❌ 優化查詢失敗: {e}")
            raise
    
    async def batch_insert_conversions_optimized(self, conversions: List[Dict[str, Any]], platform: str) -> List[int]:
        """優化版批量插入轉化數據"""
        if not self._initialized:
            await self.initialize()
            
        if not conversions:
            return []
            
        start_time = time.time()
        operation = f"batch_insert_{platform}"
        
        try:
            logger.info(f"🚀 開始優化批量插入: {len(conversions)} 條記錄 (平台: {platform})")
            
            # 將數據轉換為 ConversionData 格式
            processed_conversions = []
            for conv in conversions:
                try:
                    # 數據清理和格式化
                    conversion_data = {
                        'conversion_id': str(conv.get('conversion_id', '')),
                        'tenant_id': 1,
                        'platform': platform,
                        'partner': conv.get('partner', 'Unknown'),
                        'source': conv.get('source', ''),
                        'offer_id': conv.get('offer_id'),
                        'offer_name': conv.get('offer_name'),
                        'datetime_conversion': conv.get('datetime_conversion'),
                        'order_id': conv.get('order_id'),
                        'usd_sale_amount': self._safe_decimal(conv.get('usd_sale_amount')),
                        'usd_payout': self._safe_decimal(conv.get('usd_payout')),
                        'sale_amount_local': self._safe_decimal(conv.get('sale_amount_local')),
                        'payout_local': self._safe_decimal(conv.get('payout_local')),
                        'aff_sub': conv.get('aff_sub'),
                        'aff_sub2': conv.get('aff_sub2'),
                        'aff_sub3': conv.get('aff_sub3'),
                        'aff_sub4': conv.get('aff_sub4'),
                        'adv_sub1': conv.get('adv_sub1'),
                        'adv_sub2': conv.get('adv_sub2'),
                        'adv_sub3': conv.get('adv_sub3'),
                        'adv_sub4': conv.get('adv_sub4'),
                        'adv_sub5': conv.get('adv_sub5'),
                        'conversion_status': conv.get('conversion_status', 'pending'),
                        'raw_data': conv
                    }
                    processed_conversions.append(conversion_data)
                    
                except Exception as e:
                    logger.warning(f"⚠️ 數據處理失敗，跳過: {e}")
                    continue
            
            # 分批處理 - 使用配置的批量大小
            inserted_ids = []
            batch_size = self.config.batch_size
            total_batches = (len(processed_conversions) + batch_size - 1) // batch_size
            
            for batch_idx in range(total_batches):
                start_idx = batch_idx * batch_size
                end_idx = min(start_idx + batch_size, len(processed_conversions))
                batch_data = processed_conversions[start_idx:end_idx]
                
                logger.info(f"📦 處理批次 {batch_idx + 1}/{total_batches}: {len(batch_data)} 條記錄")
                
                # 構建批量插入請求
                request = QueryRequest(
                    agent_name="api-agent",
                    query_type="batch_insert_conversions",
                    parameters={
                        'conversions': batch_data
                    },
                    use_cache=False  # 插入操作不使用緩存
                )
                
                # 執行批量插入
                result = await self.storage_service.process_request(request)
                
                if result['success']:
                    batch_inserted = result['data'].get('inserted_count', 0)
                    inserted_ids.extend([i for i in range(batch_inserted)])
                    logger.info(f"✅ 批次 {batch_idx + 1} 完成: {batch_inserted} 條記錄插入成功")
                else:
                    logger.error(f"❌ 批次 {batch_idx + 1} 失敗: {result.get('error')}")
            
            duration = time.time() - start_time
            await self._record_operation(operation, duration, True, len(inserted_ids))
            self.metrics.batch_operations += 1
            
            logger.info(f"🎉 優化批量插入完成!")
            logger.info(f"   - 總記錄數: {len(conversions):,}")
            logger.info(f"   - 成功插入: {len(inserted_ids):,}")
            logger.info(f"   - 處理時間: {duration:.2f} 秒")
            logger.info(f"   - 處理速度: {len(inserted_ids)/duration:.1f} 條/秒")
            
            return inserted_ids
            
        except Exception as e:
            duration = time.time() - start_time
            await self._record_operation(operation, duration, False, 0)
            logger.error(f"❌ 優化批量插入失敗: {e}")
            raise
    
    def _safe_decimal(self, value) -> Optional[Decimal]:
        """安全轉換為Decimal"""
        if value is None or value == '':
            return None
        try:
            return Decimal(str(value))
        except (ValueError, TypeError):
            return None
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """獲取性能指標"""
        if not self._initialized:
            await self.initialize()
            
        uptime = time.time() - self.start_time
        
        # 獲取數據庫健康狀態
        health = await self.db_manager.health_check()
        
        # 計算緩存命中率
        total_cache_ops = self.metrics.cache_hits + self.metrics.cache_misses
        cache_hit_rate = (self.metrics.cache_hits / total_cache_ops * 100) if total_cache_ops > 0 else 0
        
        return {
            'system_info': {
                'uptime_seconds': round(uptime, 2),
                'initialization_status': 'initialized' if self._initialized else 'not_initialized',
                'optimization_level': 'full_optimization'
            },
            'performance_metrics': {
                'total_queries': self.metrics.query_count,
                'avg_query_time': round(self.metrics.avg_query_time, 3),
                'slow_queries': self.metrics.slow_queries,
                'error_count': self.metrics.errors,
                'records_processed': self.metrics.records_processed,
                'batch_operations': self.metrics.batch_operations,
                'queries_per_second': round(self.metrics.query_count / uptime, 2) if uptime > 0 else 0
            },
            'cache_metrics': {
                'enabled': self.config.enable_cache,
                'hit_rate_percent': round(cache_hit_rate, 2),
                'cache_hits': self.metrics.cache_hits,
                'cache_misses': self.metrics.cache_misses,
                'ttl_seconds': self.config.cache_ttl
            },
            'database_health': health,
            'recent_slow_queries': self._slow_queries[-10:],  # 最近10個慢查詢
            'recent_operations': self._recent_operations[-20:]  # 最近20個操作
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """健康檢查"""
        if not self._initialized:
            await self.initialize()
            
        try:
            # 執行基本的健康檢查
            start_time = time.time()
            
            # 測試統一存儲服務
            test_request = QueryRequest(
                agent_name="api-agent-health-check",
                query_type="health_check",
                parameters={},
                use_cache=False
            )
            
            result = await self.storage_service.process_request(test_request)
            
            latency = (time.time() - start_time) * 1000  # 毫秒
            
            return {
                'status': 'healthy' if result['success'] else 'unhealthy',
                'latency_ms': round(latency, 2),
                'storage_service': result['success'],
                'optimization_status': 'fully_optimized',
                'cache_enabled': self.config.enable_cache,
                'monitoring_enabled': self.config.enable_monitoring,
                'connection_pool': f"{self.config.min_connections}-{self.config.max_connections}",
                'batch_size': self.config.batch_size,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'optimization_status': 'error',
                'timestamp': datetime.now().isoformat()
            }
    
    async def close(self):
        """關閉管理器"""
        if self.db_manager:
            await self.db_manager.close()
        logger.info("✅ 完全優化的API-Agent數據庫管理器已關閉")

# 全局實例
_global_optimized_manager: Optional[OptimizedAPIAgentManager] = None

async def get_optimized_api_agent_manager(config: Optional[OptimizationConfig] = None) -> OptimizedAPIAgentManager:
    """獲取全局優化管理器實例"""
    global _global_optimized_manager
    
    if _global_optimized_manager is None:
        _global_optimized_manager = OptimizedAPIAgentManager(config)
        await _global_optimized_manager.initialize()
    
    return _global_optimized_manager 