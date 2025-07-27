#!/usr/bin/env python3
"""
優化查詢管理器
Optimized Query Manager

提供準備語句池和智能分批處理，大幅提升查詢性能
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Union, Tuple, AsyncGenerator
from datetime import datetime, timedelta
from decimal import Decimal
import asyncpg
from dataclasses import dataclass
from collections import defaultdict
import hashlib

logger = logging.getLogger(__name__)

@dataclass
class QueryTemplate:
    """查詢模板"""
    name: str
    sql: str
    params_count: int
    description: str
    estimated_cost: int = 1  # 1-10，查詢複雜度估算

@dataclass
class BatchConfig:
    """分批配置"""
    base_batch_size: int = 1000
    max_batch_size: int = 5000
    min_batch_size: int = 100
    parallel_batches: int = 3
    adaptive_sizing: bool = True

@dataclass
class QueryMetrics:
    """查詢指標"""
    query_name: str
    execution_count: int = 0
    total_time: float = 0.0
    avg_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    last_execution: Optional[datetime] = None

class PreparedStatementPool:
    """準備語句池"""
    
    def __init__(self, max_size: int = 50):
        self.max_size = max_size
        self.statements: Dict[str, asyncpg.PreparedStatement] = {}
        self.templates: Dict[str, QueryTemplate] = {}
        self.usage_count: Dict[str, int] = defaultdict(int)
        self.metrics: Dict[str, QueryMetrics] = defaultdict(QueryMetrics)
        
        # 預定義查詢模板
        self._register_templates()
    
    def _register_templates(self):
        """註冊查詢模板"""
        templates = [
            QueryTemplate(
                name="summary_metrics",
                sql="""
                SELECT 
                    COUNT(*) as total_conversions,
                    SUM(COALESCE(sale_amount, usd_sale_amount, 0)) as total_sales,
                    SUM(COALESCE(payout, usd_payout, 0)) as total_payout,
                    AVG(COALESCE(sale_amount, usd_sale_amount, 0)) as avg_sale_amount,
                    COUNT(DISTINCT partner_id) as unique_partners,
                    COUNT(DISTINCT offer_name) as unique_offers,
                    COUNT(DISTINCT aff_sub) as unique_sub_ids
                FROM conversions
                WHERE datetime_conversion >= $1 AND datetime_conversion < $2
                AND ($3::int IS NULL OR partner_id = $3)
                """,
                params_count=3,
                description="總覽指標查詢",
                estimated_cost=5
            ),
            QueryTemplate(
                name="daily_trend",
                sql="""
                SELECT 
                    DATE(datetime_conversion) as date,
                    COUNT(*) as conversions,
                    SUM(COALESCE(sale_amount, usd_sale_amount, 0)) as total_sales,
                    SUM(COALESCE(payout, usd_payout, 0)) as total_payout
                FROM conversions
                WHERE datetime_conversion >= $1 AND datetime_conversion < $2
                AND ($3::int IS NULL OR partner_id = $3)
                GROUP BY DATE(datetime_conversion)
                ORDER BY date
                """,
                params_count=3,
                description="日趨勢查詢",
                estimated_cost=6
            ),
            QueryTemplate(
                name="hourly_trend", 
                sql="""
                SELECT 
                    EXTRACT(hour FROM datetime_conversion) as hour,
                    COUNT(*) as conversions,
                    SUM(COALESCE(sale_amount, usd_sale_amount, 0)) as total_sales
                FROM conversions
                WHERE datetime_conversion >= $1 AND datetime_conversion < $2
                AND ($3::int IS NULL OR partner_id = $3)
                GROUP BY EXTRACT(hour FROM datetime_conversion)
                ORDER BY hour
                """,
                params_count=3,
                description="小時趨勢查詢",
                estimated_cost=4
            ),
            QueryTemplate(
                name="partner_performance",
                sql="""
                SELECT 
                    partner,
                    COUNT(*) as conversions,
                    SUM(COALESCE(sale_amount, usd_sale_amount, 0)) as total_sales,
                    SUM(COALESCE(payout, usd_payout, 0)) as total_payout,
                    AVG(COALESCE(sale_amount, usd_sale_amount, 0)) as avg_sale_amount,
                    COUNT(DISTINCT offer_name) as unique_offers,
                    MIN(datetime_conversion) as first_conversion,
                    MAX(datetime_conversion) as last_conversion
                FROM conversions
                WHERE datetime_conversion >= $1 AND datetime_conversion < $2
                AND partner IS NOT NULL
                GROUP BY partner
                ORDER BY conversions DESC
                LIMIT $3
                """,
                params_count=3,
                description="合作夥伴表現查詢",
                estimated_cost=7
            ),
            QueryTemplate(
                name="conversion_details_count",
                sql="""
                SELECT COUNT(*) as total
                FROM conversions
                WHERE datetime_conversion >= $1 AND datetime_conversion < $2
                AND ($3::text IS NULL OR partner = $3)
                """,
                params_count=3,
                description="轉化詳情計數查詢",
                estimated_cost=3
            ),
            QueryTemplate(
                name="conversion_details_data",
                sql="""
                SELECT 
                    COALESCE(platform, '') as platform,
                    COALESCE(partner, '') as partner,
                    COALESCE(source, '') as source,
                    COALESCE(conversion_id, '') as conversion_id,
                    datetime_conversion,
                    COALESCE(offer_name, '') as offer_name,
                    COALESCE(sale_amount, usd_sale_amount, 0) as usd_sale_amount,
                    COALESCE(payout, usd_payout, 0) as usd_payout,
                    COALESCE(aff_sub, '') as sub_id,
                    COALESCE(aff_sub, '') as media_id,
                    COALESCE(click_id, '') as click_id
                FROM conversions
                WHERE datetime_conversion >= $1 AND datetime_conversion < $2
                AND ($3::text IS NULL OR partner = $3)
                ORDER BY datetime_conversion DESC
                LIMIT $4 OFFSET $5
                """,
                params_count=5,
                description="轉化詳情數據查詢",
                estimated_cost=8
            ),
            QueryTemplate(
                name="offer_performance",
                sql="""
                SELECT 
                    offer_name,
                    COUNT(*) as conversions,
                    SUM(COALESCE(sale_amount, usd_sale_amount, 0)) as total_sales,
                    SUM(COALESCE(payout, usd_payout, 0)) as total_payout,
                    AVG(COALESCE(sale_amount, usd_sale_amount, 0)) as avg_sale_amount,
                    COUNT(DISTINCT aff_sub) as unique_sub_ids,
                    MIN(datetime_conversion) as first_conversion,
                    MAX(datetime_conversion) as last_conversion
                FROM conversions
                WHERE datetime_conversion >= $1 AND datetime_conversion < $2
                AND offer_name IS NOT NULL
                AND ($3::int IS NULL OR partner_id = $3)
                GROUP BY offer_name
                ORDER BY conversions DESC
                LIMIT $4
                """,
                params_count=4,
                description="Offer 表現查詢",
                estimated_cost=6
            )
        ]
        
        for template in templates:
            self.templates[template.name] = template
            self.metrics[template.name] = QueryMetrics(query_name=template.name)
    
    async def get_prepared_statement(self, conn: asyncpg.Connection, 
                                   template_name: str) -> asyncpg.PreparedStatement:
        """獲取準備語句"""
        if template_name not in self.templates:
            raise ValueError(f"未知的查詢模板: {template_name}")
        
        template = self.templates[template_name]
        cache_key = f"{id(conn)}:{template_name}"
        
        if cache_key not in self.statements:
            # 準備語句
            start_time = time.time()
            stmt = await conn.prepare(template.sql)
            prepare_time = time.time() - start_time
            
            self.statements[cache_key] = stmt
            self.usage_count[cache_key] = 0
            
            logger.debug(f"✅ 準備語句完成: {template_name} ({prepare_time:.3f}s)")
            
            # 清理舊的準備語句（如果超過限制）
            if len(self.statements) > self.max_size:
                await self._cleanup_statements()
        
        self.usage_count[cache_key] += 1
        return self.statements[cache_key]
    
    async def execute_template(self, conn: asyncpg.Connection, 
                             template_name: str, 
                             params: List[Any]) -> List[asyncpg.Record]:
        """執行模板查詢"""
        template = self.templates[template_name]
        
        if len(params) != template.params_count:
            raise ValueError(f"參數數量不匹配: 期望 {template.params_count}, 實際 {len(params)}")
        
        start_time = time.time()
        
        try:
            stmt = await self.get_prepared_statement(conn, template_name)
            result = await stmt.fetch(*params)
            
            execution_time = time.time() - start_time
            self._update_metrics(template_name, execution_time)
            
            logger.debug(f"🚀 執行查詢: {template_name} ({execution_time:.3f}s, {len(result)} 條記錄)")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ 查詢執行失敗: {template_name} ({execution_time:.3f}s) - {e}")
            raise
    
    def _update_metrics(self, template_name: str, execution_time: float):
        """更新查詢指標"""
        metrics = self.metrics[template_name]
        
        metrics.execution_count += 1
        metrics.total_time += execution_time
        metrics.avg_time = metrics.total_time / metrics.execution_count
        metrics.min_time = min(metrics.min_time, execution_time)
        metrics.max_time = max(metrics.max_time, execution_time)
        metrics.last_execution = datetime.now()
    
    async def _cleanup_statements(self):
        """清理使用次數少的準備語句"""
        # 按使用次數排序，移除最少使用的語句
        sorted_statements = sorted(self.usage_count.items(), key=lambda x: x[1])
        
        # 移除最少使用的 25% 語句
        remove_count = len(sorted_statements) // 4
        
        for cache_key, _ in sorted_statements[:remove_count]:
            if cache_key in self.statements:
                del self.statements[cache_key]
            if cache_key in self.usage_count:
                del self.usage_count[cache_key]
        
        logger.info(f"🧹 清理了 {remove_count} 個準備語句")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """獲取性能統計"""
        stats = {
            'total_templates': len(self.templates),
            'cached_statements': len(self.statements),
            'template_metrics': {}
        }
        
        for name, metrics in self.metrics.items():
            if metrics.execution_count > 0:
                stats['template_metrics'][name] = {
                    'executions': metrics.execution_count,
                    'avg_time': f"{metrics.avg_time:.3f}s",
                    'min_time': f"{metrics.min_time:.3f}s",
                    'max_time': f"{metrics.max_time:.3f}s",
                    'total_time': f"{metrics.total_time:.2f}s",
                    'last_execution': metrics.last_execution.isoformat() if metrics.last_execution else None
                }
        
        return stats

class IntelligentBatchProcessor:
    """智能分批處理器"""
    
    def __init__(self, config: BatchConfig = None):
        self.config = config or BatchConfig()
        self.execution_history: List[Dict] = []
        self.optimal_batch_sizes: Dict[str, int] = {}
    
    async def process_large_query(self, 
                                conn: asyncpg.Connection,
                                base_query: str,
                                count_query: str,
                                params: List[Any],
                                processor_func: Optional[callable] = None) -> AsyncGenerator[List[Dict], None]:
        """處理大型查詢結果集"""
        
        # 獲取總記錄數
        total_records = await conn.fetchval(count_query, *params)
        
        if total_records == 0:
            return
        
        # 計算最優批量大小
        batch_size = self._calculate_optimal_batch_size(total_records, base_query)
        batches_count = (total_records + batch_size - 1) // batch_size
        
        logger.info(f"📊 開始分批處理: {total_records} 條記錄, {batches_count} 批次, 批量大小: {batch_size}")
        
        start_time = time.time()
        
        # 並行處理配置
        semaphore = asyncio.Semaphore(self.config.parallel_batches)
        
        async def process_batch(offset: int, batch_num: int) -> Tuple[int, List[Dict]]:
            """處理單個批次"""
            async with semaphore:
                batch_start = time.time()
                
                # 添加 LIMIT 和 OFFSET
                batch_query = f"{base_query} LIMIT {batch_size} OFFSET {offset}"
                
                try:
                    rows = await conn.fetch(batch_query, *params)
                    records = [dict(row) for row in rows]
                    
                    # 如果提供了處理函數，應用處理
                    if processor_func:
                        records = processor_func(records)
                    
                    batch_time = time.time() - batch_start
                    logger.debug(f"✅ 批次 {batch_num+1}/{batches_count} 完成: {len(records)} 條記錄 ({batch_time:.2f}s)")
                    
                    return batch_num, records
                    
                except Exception as e:
                    batch_time = time.time() - batch_start
                    logger.error(f"❌ 批次 {batch_num+1} 失敗 ({batch_time:.2f}s): {e}")
                    return batch_num, []
        
        # 創建並行任務
        tasks = []
        for i in range(batches_count):
            offset = i * batch_size
            task = asyncio.create_task(process_batch(offset, i))
            tasks.append(task)
        
        # 逐步收集結果
        completed = 0
        for coro in asyncio.as_completed(tasks):
            batch_num, records = await coro
            completed += 1
            
            if records:
                yield records
            
            # 進度報告
            if completed % max(1, batches_count // 10) == 0:
                progress = (completed / batches_count) * 100
                elapsed = time.time() - start_time
                eta = (elapsed / completed) * (batches_count - completed) if completed > 0 else 0
                
                logger.info(f"📈 分批處理進度: {progress:.1f}% ({completed}/{batches_count}), 預計剩餘: {eta:.1f}s")
        
        total_time = time.time() - start_time
        
        # 記錄執行歷史
        self._record_execution(base_query, total_records, batch_size, batches_count, total_time)
        
        logger.info(f"✅ 分批處理完成: {total_records} 條記錄, 總耗時: {total_time:.2f}s")
    
    def _calculate_optimal_batch_size(self, total_records: int, query_signature: str) -> int:
        """計算最優批量大小"""
        # 基於歷史數據調整
        if query_signature in self.optimal_batch_sizes:
            historical_size = self.optimal_batch_sizes[query_signature]
        else:
            historical_size = self.config.base_batch_size
        
        # 根據數據量動態調整
        if total_records < 1000:
            optimal_size = min(total_records, self.config.min_batch_size)
        elif total_records < 10000:
            optimal_size = min(historical_size, 2000)
        elif total_records < 100000:
            optimal_size = min(historical_size * 2, self.config.max_batch_size)
        else:
            optimal_size = self.config.max_batch_size
        
        # 確保在合理範圍內
        optimal_size = max(self.config.min_batch_size, 
                          min(optimal_size, self.config.max_batch_size))
        
        return optimal_size
    
    def _record_execution(self, query_signature: str, total_records: int, 
                         batch_size: int, batches_count: int, total_time: float):
        """記錄執行歷史"""
        execution_record = {
            'query_signature': query_signature,
            'total_records': total_records,
            'batch_size': batch_size,
            'batches_count': batches_count,
            'total_time': total_time,
            'avg_time_per_batch': total_time / batches_count,
            'records_per_second': total_records / total_time,
            'timestamp': datetime.now()
        }
        
        self.execution_history.append(execution_record)
        
        # 更新最優批量大小
        self._update_optimal_batch_size(query_signature, execution_record)
        
        # 保持歷史記錄在合理範圍內
        if len(self.execution_history) > 100:
            self.execution_history = self.execution_history[-50:]
    
    def _update_optimal_batch_size(self, query_signature: str, execution_record: Dict):
        """更新最優批量大小"""
        records_per_second = execution_record['records_per_second']
        current_batch_size = execution_record['batch_size']
        
        # 如果效率很好，可以嘗試更大的批量
        if records_per_second > 1000:  # 每秒處理超過1000條記錄
            new_size = min(current_batch_size * 1.2, self.config.max_batch_size)
        elif records_per_second < 200:  # 每秒處理少於200條記錄
            new_size = max(current_batch_size * 0.8, self.config.min_batch_size)
        else:
            new_size = current_batch_size
        
        self.optimal_batch_sizes[query_signature] = int(new_size)
    
    def get_batch_stats(self) -> Dict[str, Any]:
        """獲取分批處理統計"""
        if not self.execution_history:
            return {'message': '暫無執行歷史'}
        
        recent_executions = self.execution_history[-10:]
        
        avg_records_per_second = sum(e['records_per_second'] for e in recent_executions) / len(recent_executions)
        avg_batch_size = sum(e['batch_size'] for e in recent_executions) / len(recent_executions)
        
        return {
            'total_executions': len(self.execution_history),
            'avg_records_per_second': f"{avg_records_per_second:.1f}",
            'avg_batch_size': f"{avg_batch_size:.0f}",
            'optimal_batch_sizes': self.optimal_batch_sizes,
            'config': {
                'base_batch_size': self.config.base_batch_size,
                'max_batch_size': self.config.max_batch_size,
                'parallel_batches': self.config.parallel_batches
            }
        }

class OptimizedQueryManager:
    """優化查詢管理器"""
    
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self.statement_pool = PreparedStatementPool()
        self.batch_processor = IntelligentBatchProcessor()
        self._connection: Optional[asyncpg.Connection] = None
    
    async def get_connection(self) -> asyncpg.Connection:
        """獲取數據庫連接"""
        if self._connection is None or self._connection.is_closed():
            self._connection = await asyncpg.connect(
                host=self.db_config["host"],
                port=self.db_config["port"],
                database=self.db_config["database"],
                user=self.db_config["user"],
                password=self.db_config["password"],
                command_timeout=60  # 增加超時時間
            )
        
        return self._connection
    
    async def execute_template_query(self, template_name: str, params: List[Any]) -> List[Dict]:
        """執行模板查詢"""
        conn = await self.get_connection()
        rows = await self.statement_pool.execute_template(conn, template_name, params)
        return [dict(row) for row in rows]
    
    async def execute_large_query_batched(self, 
                                        template_name: str,
                                        count_template_name: str,
                                        params: List[Any],
                                        processor_func: Optional[callable] = None) -> List[Dict]:
        """執行大型查詢（分批處理）"""
        conn = await self.get_connection()
        
        base_query = self.statement_pool.templates[template_name].sql
        count_query = self.statement_pool.templates[count_template_name].sql
        
        all_results = []
        
        async for batch_results in self.batch_processor.process_large_query(
            conn, base_query, count_query, params, processor_func
        ):
            all_results.extend(batch_results)
        
        return all_results
    
    async def get_performance_summary(self) -> Dict[str, Any]:
        """獲取性能摘要"""
        return {
            'prepared_statements': self.statement_pool.get_performance_stats(),
            'batch_processing': self.batch_processor.get_batch_stats()
        }
    
    async def close(self):
        """關閉連接"""
        if self._connection and not self._connection.is_closed():
            await self._connection.close()
        logger.info("✅ 優化查詢管理器已關閉") 