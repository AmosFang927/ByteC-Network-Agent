#!/usr/bin/env python3
"""
API-Agent 完全優化數據獲取器
API Agent Fully Optimized Data Fetcher

完全重構的高性能版本，實現：
- 整合新的優化數據庫管理器
- 異步並發處理
- 智能緩存機制
- 實時性能監控
- 自動錯誤恢復

預期性能提升：80-90%
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import json
from decimal import Decimal

# 導入優化管理器
from agents.data_dmp_agent.optimized_api_agent_manager import (
    OptimizedAPIAgentManager,
    OptimizationConfig,
    get_optimized_api_agent_manager
)

# 導入現有的API客戶端
from .involve_asia_client import InvolveAsiaAPI
from agents.data_dmp_agent.api_config_manager import APIConfigManager

# 導入配置
import config

logger = logging.getLogger(__name__)

class PerformanceTracker:
    """性能追蹤器"""
    
    def __init__(self):
        self.operations = []
        self.start_time = time.time()
        
    def record_operation(self, operation: str, duration: float, record_count: int, success: bool = True):
        """記錄操作"""
        self.operations.append({
            'operation': operation,
            'duration': duration,
            'record_count': record_count,
            'success': success,
            'timestamp': datetime.now().isoformat(),
            'records_per_second': record_count / duration if duration > 0 else 0
        })
        
    def get_summary(self) -> Dict[str, Any]:
        """獲取性能摘要"""
        if not self.operations:
            return {'total_operations': 0}
            
        total_duration = sum(op['duration'] for op in self.operations)
        total_records = sum(op['record_count'] for op in self.operations)
        successful_ops = sum(1 for op in self.operations if op['success'])
        
        return {
            'total_operations': len(self.operations),
            'successful_operations': successful_ops,
            'success_rate': (successful_ops / len(self.operations)) * 100,
            'total_duration': round(total_duration, 2),
            'total_records_processed': total_records,
            'overall_records_per_second': round(total_records / total_duration, 2) if total_duration > 0 else 0,
            'avg_operation_duration': round(total_duration / len(self.operations), 2),
            'uptime_seconds': round(time.time() - self.start_time, 2)
        }

class OptimizedAPIDataFetcher:
    """完全優化的API數據獲取器"""
    
    def __init__(self, optimization_config: Optional[OptimizationConfig] = None):
        self.config = optimization_config or OptimizationConfig()
        self.config_manager = APIConfigManager()
        self.api_clients = {}
        self.db_manager: Optional[OptimizedAPIAgentManager] = None
        self.performance_tracker = PerformanceTracker()
        self._initialized = False
        
        # 並發控制
        self.concurrent_semaphore = asyncio.Semaphore(self.config.max_concurrent_batches)
        
        # 錯誤恢復配置
        self.max_retries = 3
        self.retry_delay = 1.0
        
    async def initialize(self):
        """初始化優化數據獲取器"""
        if self._initialized:
            return
            
        try:
            logger.info("🚀 初始化完全優化的API數據獲取器...")
            
            # 初始化優化數據庫管理器
            self.db_manager = await get_optimized_api_agent_manager(self.config)
            
            # 健康檢查
            health = await self.db_manager.health_check()
            if health['status'] != 'healthy':
                raise Exception(f"數據庫管理器不健康: {health}")
            
            self._initialized = True
            logger.info("✅ 完全優化的API數據獲取器初始化完成")
            logger.info(f"   - 優化等級: {health.get('optimization_status', 'unknown')}")
            logger.info(f"   - 緩存: {'啟用' if health.get('cache_enabled') else '禁用'}")
            logger.info(f"   - 連接池: {health.get('connection_pool', 'unknown')}")
            logger.info(f"   - 批量大小: {health.get('batch_size', 'unknown')}")
            
        except Exception as e:
            logger.error(f"❌ 優化數據獲取器初始化失敗: {e}")
            raise
    
    async def get_api_client_optimized(self, platform: str) -> Optional[InvolveAsiaAPI]:
        """優化版獲取API客戶端"""
        if platform in self.api_clients:
            return self.api_clients[platform]
        
        config_data = self.config_manager.get_config(platform)
        if not config_data:
            logger.error(f"❌ 未找到平台配置: {platform}")
            return None
        
        if not self.config_manager.validate_config(platform):
            logger.error(f"❌ 平台配置無效: {platform}")
            return None
        
        # 帶重試的API客戶端創建
        for attempt in range(self.max_retries):
            try:
                api_client = InvolveAsiaAPI(
                    api_secret=config_data['secret'],
                    api_key=config_data['api_key']
                )
                
                # 執行認證
                if api_client.authenticate():
                    self.api_clients[platform] = api_client
                    logger.info(f"✅ API客戶端創建並認證成功: {platform} (第 {attempt + 1} 次嘗試)")
                    return api_client
                else:
                    logger.warning(f"⚠️ API認證失敗: {platform} (第 {attempt + 1} 次嘗試)")
                    
            except Exception as e:
                logger.warning(f"⚠️ API客戶端創建失敗: {platform} (第 {attempt + 1} 次嘗試) - {e}")
                
            if attempt < self.max_retries - 1:
                await asyncio.sleep(self.retry_delay * (attempt + 1))
        
        logger.error(f"❌ API客戶端創建最終失敗: {platform}")
        return None
    
    async def process_raw_conversions_optimized(self, raw_conversions: List[Dict], platform: str) -> List[Dict[str, Any]]:
        """優化版處理原始轉化數據"""
        start_time = time.time()
        operation = f"process_conversions_{platform}"
        
        try:
            logger.info(f"🔄 開始優化處理 {len(raw_conversions)} 條原始轉化數據...")
            
            processed_conversions = []
            
            # 並發處理數據轉換
            async def process_single_conversion(conversion: Dict) -> Optional[Dict[str, Any]]:
                try:
                    # ===== 核心分類字段處理 =====
                    platform_name = platform
                    source = conversion.get('aff_sub1') or conversion.get('aff_sub', '')
                    partner = config.match_source_to_partner(source) if source else 'Unknown'
                    
                    # ===== 核心轉化字段 =====
                    conversion_id = str(conversion.get('conversion_id', ''))
                    offer_id = str(conversion.get('offer_id', ''))
                    offer_name = conversion.get('offer_name', '')
                    order_id = conversion.get('order_id', conversion_id)
                    
                    # ===== 時間字段處理 =====
                    datetime_conversion = None
                    if conversion.get('datetime_conversion'):
                        try:
                            datetime_conversion = datetime.fromisoformat(
                                conversion['datetime_conversion'].replace('Z', '+00:00')
                            )
                        except Exception as e:
                            logger.warning(f"⚠️ 日期格式錯誤: {e}")
                    
                    # ===== 金額字段處理 - 完整映射 =====
                    def safe_decimal(value):
                        if value is None or value == '':
                            return None
                        try:
                            return float(value)
                        except (ValueError, TypeError):
                            return None
                    
                    # API返回的原始金額
                    sale_amount = safe_decimal(conversion.get('sale_amount'))
                    payout = safe_decimal(conversion.get('payout'))
                    
                    # 本地化金額
                    sale_amount_local = safe_decimal(conversion.get('sale_amount_local'))
                    payout_local = safe_decimal(conversion.get('payout_local'))
                    
                    # USD金額（優先使用API中的USD字段）
                    usd_sale_amount = safe_decimal(conversion.get('usd_sale_amount', sale_amount))
                    usd_payout = safe_decimal(conversion.get('usd_payout', payout))
                    
                    # 其他金額字段
                    myr_sale_amount = safe_decimal(conversion.get('myr_sale_amount'))
                    myr_payout = safe_decimal(conversion.get('myr_payout'))
                    base_payout = safe_decimal(conversion.get('base_payout'))
                    bonus_payout = safe_decimal(conversion.get('bonus_payout'))
                    
                    # ===== 參數字段 =====
                    # 廣告主參數
                    adv_sub = conversion.get('adv_sub', '')
                    adv_sub1 = conversion.get('adv_sub1', '')
                    adv_sub2 = conversion.get('adv_sub2', '')
                    adv_sub3 = conversion.get('adv_sub3', '')
                    adv_sub4 = conversion.get('adv_sub4', '')
                    adv_sub5 = conversion.get('adv_sub5', '')
                    
                    # 發布商參數
                    aff_sub = conversion.get('aff_sub', '')
                    aff_sub1 = conversion.get('aff_sub1', '')
                    aff_sub2 = conversion.get('aff_sub2', '')
                    aff_sub3 = conversion.get('aff_sub3', '')
                    aff_sub4 = conversion.get('aff_sub4', '')
                    aff_sub5 = conversion.get('aff_sub5', '')
                    
                    # ===== 其他字段 =====
                    currency = conversion.get('currency', 'USD')
                    conversion_currency = conversion.get('conversion_currency', currency)
                    conversion_status = conversion.get('conversion_status', 'pending')
                    offer_status = conversion.get('offer_status', 'active')
                    merchant_id = conversion.get('merchant_id')
                    affiliate_remarks = conversion.get('affiliate_remarks', '')
                    click_id = conversion.get('click_id', '')
                    click_time = conversion.get('click_time')
                    commission_rate = safe_decimal(conversion.get('commission_rate'))
                    avg_commission_rate = safe_decimal(conversion.get('avg_commission_rate'))
                    
                    # 構建完整的轉化記錄
                    processed_conversion = {
                        # 核心分類字段
                        'platform': platform_name,
                        'partner': partner,
                        'source': source,
                        
                        # 核心轉化字段
                        'conversion_id': conversion_id,
                        'offer_id': offer_id,
                        'offer_name': offer_name,
                        'order_id': order_id,
                        
                        # 時間字段
                        'datetime_conversion': datetime_conversion,
                        'datetime_conversion_updated': conversion.get('datetime_conversion_updated'),
                        'click_time': click_time,
                        
                        # 完整金額字段
                        'sale_amount_local': sale_amount_local,
                        'myr_sale_amount': myr_sale_amount,
                        'usd_sale_amount': usd_sale_amount,
                        'payout_local': payout_local,
                        'myr_payout': myr_payout,
                        'usd_payout': usd_payout,
                        'sale_amount': sale_amount,
                        'payout': payout,
                        'base_payout': base_payout,
                        'bonus_payout': bonus_payout,
                        
                        # 貨幣字段
                        'currency': currency,
                        'conversion_currency': conversion_currency,
                        
                        # 廣告主參數
                        'adv_sub': adv_sub,
                        'adv_sub1': adv_sub1,
                        'adv_sub2': adv_sub2,
                        'adv_sub3': adv_sub3,
                        'adv_sub4': adv_sub4,
                        'adv_sub5': adv_sub5,
                        
                        # 發布商參數
                        'aff_sub': aff_sub,
                        'aff_sub1': aff_sub1,
                        'aff_sub2': aff_sub2,
                        'aff_sub3': aff_sub3,
                        'aff_sub4': aff_sub4,
                        'aff_sub5': aff_sub5,
                        
                        # 狀態字段
                        'conversion_status': conversion_status,
                        'offer_status': offer_status,
                        
                        # 業務字段
                        'merchant_id': merchant_id,
                        'affiliate_remarks': affiliate_remarks,
                        'click_id': click_id,
                        
                        # 佣金字段
                        'commission_rate': commission_rate,
                        'avg_commission_rate': avg_commission_rate,
                        
                        # 系統字段
                        'tenant_id': 1,
                        'raw_data': conversion,
                        'event_time': datetime_conversion or datetime.now()
                    }
                    
                    return processed_conversion
                    
                except Exception as e:
                    logger.warning(f"⚠️ 處理單條轉化數據失敗: {e}")
                    return None
            
            # 並發處理所有轉化數據
            tasks = [process_single_conversion(conv) for conv in raw_conversions]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 過濾有效結果
            for result in results:
                if result is not None and not isinstance(result, Exception):
                    processed_conversions.append(result)
                elif isinstance(result, Exception):
                    logger.warning(f"⚠️ 並發處理異常: {result}")
            
            duration = time.time() - start_time
            self.performance_tracker.record_operation(operation, duration, len(processed_conversions), True)
            
            logger.info(f"✅ 優化數據處理完成: {len(processed_conversions)}/{len(raw_conversions)} 條記錄 ({duration:.2f}秒)")
            logger.info(f"   - 處理速度: {len(processed_conversions)/duration:.1f} 條/秒")
            
            return processed_conversions
            
        except Exception as e:
            duration = time.time() - start_time
            self.performance_tracker.record_operation(operation, duration, 0, False)
            logger.error(f"❌ 優化數據處理失敗: {e}")
            raise
    
    async def fetch_conversions_optimized(self, platform: str, days_ago: int = 1, limit: int = None) -> List[Dict[str, Any]]:
        """完全優化的轉化數據獲取"""
        if not self._initialized:
            await self.initialize()
            
        start_time = time.time()
        operation = f"fetch_conversions_{platform}"
        
        try:
            logger.info(f"🔍 開始優化轉化數據獲取: platform={platform}, days_ago={days_ago}, limit={limit}")
            
            # 獲取API客戶端
            api_client = await self.get_api_client_optimized(platform)
            if not api_client:
                raise Exception(f"無法獲取API客戶端: {platform}")
            
            # 獲取日期範圍
            start_date, end_date = self.config_manager.get_date_range(days_ago)
            logger.info(f"📅 查詢日期範圍: {start_date} 至 {end_date}")
            
            # 從API獲取原始轉化數據
            api_start_time = time.time()
            api_response = api_client.get_conversions(
                start_date=start_date,
                end_date=end_date,
                currency='USD',
                api_name=platform,
                limit=limit
            )
            api_duration = time.time() - api_start_time
            
            if not api_response or api_response.get("status") != "success":
                logger.warning(f"⚠️ API響應無效: {platform}")
                return []
            
            # 提取實際的轉化數據
            raw_conversions = api_response.get("data", {}).get("data", [])
            if not raw_conversions:
                logger.warning(f"⚠️ 沒有獲取到轉化數據: {platform}")
                return []
            
            logger.info(f"✅ API數據獲取完成: {len(raw_conversions)} 條記錄 ({api_duration:.2f}秒)")
            
            # 優化處理數據
            processed_conversions = await self.process_raw_conversions_optimized(raw_conversions, platform)
            
            # 應用限制
            if limit and len(processed_conversions) > limit:
                processed_conversions = processed_conversions[:limit]
                logger.info(f"🔢 應用數據限制: {len(processed_conversions)} 條記錄 (限制: {limit})")
            
            duration = time.time() - start_time
            self.performance_tracker.record_operation(operation, duration, len(processed_conversions), True)
            
            logger.info(f"🎯 完全優化的轉化數據獲取完成: {len(processed_conversions)} 條記錄")
            logger.info(f"   - 總耗時: {duration:.2f} 秒")
            logger.info(f"   - API耗時: {api_duration:.2f} 秒")
            logger.info(f"   - 處理耗時: {duration - api_duration:.2f} 秒")
            logger.info(f"   - 整體速度: {len(processed_conversions)/duration:.1f} 條/秒")
            
            return processed_conversions
            
        except Exception as e:
            duration = time.time() - start_time
            self.performance_tracker.record_operation(operation, duration, 0, False)
            logger.error(f"❌ 優化轉化數據獲取失敗: {str(e)}")
            import traceback
            logger.error(f"   錯誤詳情: {traceback.format_exc()}")
            raise
    
    async def store_conversions_optimized(self, conversions: List[Dict[str, Any]], platform: str) -> List[int]:
        """優化版存儲轉化數據"""
        if not self._initialized:
            await self.initialize()
            
        if not conversions:
            return []
            
        start_time = time.time()
        operation = f"store_conversions_{platform}"
        
        try:
            logger.info(f"💾 開始優化存儲轉化數據: {len(conversions)} 條記錄 (平台: {platform})")
            
            # 使用優化數據庫管理器進行批量插入
            stored_ids = await self.db_manager.batch_insert_conversions_optimized(conversions, platform)
            
            duration = time.time() - start_time
            self.performance_tracker.record_operation(operation, duration, len(stored_ids), True)
            
            logger.info(f"✅ 優化存儲完成: {len(stored_ids)}/{len(conversions)} 條記錄成功")
            logger.info(f"   - 存儲時間: {duration:.2f} 秒")
            logger.info(f"   - 存儲速度: {len(stored_ids)/duration:.1f} 條/秒")
            
            return stored_ids
            
        except Exception as e:
            duration = time.time() - start_time
            self.performance_tracker.record_operation(operation, duration, 0, False)
            logger.error(f"❌ 優化存儲失敗: {e}")
            raise
    
    async def fetch_and_store_optimized(self, platform: str, days_ago: int = 1, limit: int = None) -> Dict[str, Any]:
        """完全優化的獲取並存儲流程"""
        if not self._initialized:
            await self.initialize()
            
        start_time = time.time()
        
        try:
            logger.info(f"🚀 開始完全優化的數據處理流程: {platform}")
            
            # 步驟1: 獲取轉化數據
            conversions = await self.fetch_conversions_optimized(platform, days_ago, limit)
            
            if not conversions:
                return {
                    'success': True,
                    'platform': platform,
                    'days_ago': days_ago,
                    'fetched_count': 0,
                    'stored_count': 0,
                    'message': '沒有新的轉化數據',
                    'duration': time.time() - start_time
                }
            
            # 步驟2: 存儲轉化數據
            stored_ids = await self.store_conversions_optimized(conversions, platform)
            
            # 步驟3: 生成結果統計
            duration = time.time() - start_time
            
            result = {
                'success': True,
                'platform': platform,
                'days_ago': days_ago,
                'fetched_count': len(conversions),
                'stored_count': len(stored_ids),
                'date_range': self.config_manager.get_date_range(days_ago),
                'processing_time': datetime.now().isoformat(),
                'duration': duration,
                'records_per_second': len(stored_ids) / duration if duration > 0 else 0
            }
            
            # 計算金額統計
            total_amount = sum(conv.get('usd_sale_amount', 0) or 0 for conv in conversions)
            total_payout = sum(conv.get('usd_payout', 0) or 0 for conv in conversions)
            
            result.update({
                'financial_summary': {
                    'total_sale_amount_usd': round(total_amount, 2),
                    'total_payout_usd': round(total_payout, 2),
                    'avg_sale_amount_usd': round(total_amount / len(conversions), 2) if conversions else 0,
                    'avg_payout_usd': round(total_payout / len(conversions), 2) if conversions else 0
                }
            })
            
            logger.info(f"🎉 完全優化的數據處理流程完成!")
            logger.info(f"   - 平台: {platform}")
            logger.info(f"   - 獲取: {len(conversions)} 條")
            logger.info(f"   - 存儲: {len(stored_ids)} 條")
            logger.info(f"   - 總時間: {duration:.2f} 秒")
            logger.info(f"   - 整體速度: {len(stored_ids)/duration:.1f} 條/秒")
            logger.info(f"   - 總金額: ${total_amount:,.2f} USD")
            logger.info(f"   - 總佣金: ${total_payout:,.2f} USD")
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"❌ 完全優化的數據處理流程失敗: {e}")
            return {
                'success': False,
                'platform': platform,
                'days_ago': days_ago,
                'error': str(e),
                'duration': duration
            }
    
    async def get_performance_summary(self) -> Dict[str, Any]:
        """獲取性能摘要"""
        fetcher_stats = self.performance_tracker.get_summary()
        db_metrics = await self.db_manager.get_performance_metrics() if self.db_manager else {}
        
        return {
            'fetcher_performance': fetcher_stats,
            'database_performance': db_metrics,
            'optimization_status': 'fully_optimized',
            'timestamp': datetime.now().isoformat()
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """健康檢查"""
        if not self._initialized:
            await self.initialize()
            
        db_health = await self.db_manager.health_check() if self.db_manager else {'status': 'unavailable'}
        
        return {
            'status': 'healthy' if db_health['status'] == 'healthy' else 'unhealthy',
            'fetcher_initialized': self._initialized,
            'database_manager': db_health,
            'optimization_level': 'full_optimization',
            'api_clients_cached': len(self.api_clients),
            'timestamp': datetime.now().isoformat()
        }
    
    async def close(self):
        """關閉數據獲取器"""
        if self.db_manager:
            await self.db_manager.close()
        logger.info("✅ 完全優化的API數據獲取器已關閉")

# 全局實例
_global_optimized_fetcher: Optional[OptimizedAPIDataFetcher] = None

async def get_optimized_api_data_fetcher(config: Optional[OptimizationConfig] = None) -> OptimizedAPIDataFetcher:
    """獲取全局優化數據獲取器實例"""
    global _global_optimized_fetcher
    
    if _global_optimized_fetcher is None:
        _global_optimized_fetcher = OptimizedAPIDataFetcher(config)
        await _global_optimized_fetcher.initialize()
    
    return _global_optimized_fetcher 