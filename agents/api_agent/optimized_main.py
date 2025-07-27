#!/usr/bin/env python3
"""
API-Agent 完全優化主程序
API Agent Fully Optimized Main Program

完全重構的高性能版本，實現：
- 統一存儲服務集成
- 智能緩存策略
- 連接池優化
- 實時性能監控
- 自動錯誤恢復
- 批量處理優化

預期性能提升：80-90%
"""

import sys
import os
import argparse
import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json

# 添加項目根目錄到Python路徑
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# 導入優化組件
from agents.api_agent.optimized_api_data_fetcher import (
    OptimizedAPIDataFetcher,
    get_optimized_api_data_fetcher
)
from agents.data_dmp_agent.optimized_api_agent_manager import (
    OptimizedAPIAgentManager,
    OptimizationConfig,
    get_optimized_api_agent_manager
)
from agents.data_dmp_agent.api_config_manager import APIConfigManager

# 設置高性能日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('optimized_api_agent.log')
    ]
)
logger = logging.getLogger(__name__)

class OptimizedAPIAgent:
    """完全優化的API-Agent主類"""
    
    def __init__(self, config: Optional[OptimizationConfig] = None):
        self.config = config or OptimizationConfig()
        self.api_fetcher: Optional[OptimizedAPIDataFetcher] = None
        self.db_manager: Optional[OptimizedAPIAgentManager] = None
        self.config_manager = APIConfigManager()
        
        # 統計信息
        self.stats = {
            'session_start': datetime.now().isoformat(),
            'total_fetched': 0,
            'total_processed': 0,
            'total_stored': 0,
            'platforms_processed': [],
            'errors': [],
            'performance_history': []
        }
        
        # 性能跟蹤
        self.session_start_time = time.time()
        
    async def initialize(self):
        """初始化完全優化的API-Agent"""
        logger.info("🚀 正在初始化完全優化的API-Agent...")
        logger.info("="*60)
        
        try:
            # 顯示優化配置
            logger.info("🔧 優化配置:")
            logger.info(f"   - 連接池: {self.config.min_connections}-{self.config.max_connections}")
            logger.info(f"   - 緩存: {'啟用' if self.config.enable_cache else '禁用'} (TTL: {self.config.cache_ttl}s)")
            logger.info(f"   - 批量大小: {self.config.batch_size}")
            logger.info(f"   - 並發批次: {self.config.max_concurrent_batches}")
            logger.info(f"   - 監控: {'啟用' if self.config.enable_monitoring else '禁用'}")
            logger.info(f"   - 慢查詢閾值: {self.config.slow_query_threshold}s")
            
            # 初始化優化數據庫管理器
            logger.info("🗄️ 初始化優化數據庫管理器...")
            self.db_manager = await get_optimized_api_agent_manager(self.config)
            
            # 初始化優化數據獲取器
            logger.info("📡 初始化優化數據獲取器...")
            self.api_fetcher = await get_optimized_api_data_fetcher(self.config)
            
            # 執行健康檢查
            logger.info("🔍 執行系統健康檢查...")
            health = await self.health_check()
            
            if health['status'] != 'healthy':
                raise Exception(f"系統健康檢查失敗: {health}")
            
            logger.info("✅ 完全優化的API-Agent初始化成功!")
            logger.info("="*60)
            logger.info("🎯 性能優化等級: 完全優化 (預期提升 80-90%)")
            logger.info(f"   - 數據庫延遲: {health.get('database_manager', {}).get('latency_ms', 'N/A')} ms")
            logger.info(f"   - 存儲服務: {health.get('database_manager', {}).get('storage_service', 'N/A')}")
            logger.info(f"   - 優化狀態: {health.get('database_manager', {}).get('optimization_status', 'N/A')}")
            logger.info("="*60)
            
        except Exception as e:
            logger.error(f"❌ 完全優化的API-Agent初始化失敗: {e}")
            raise
    
    async def cleanup(self):
        """清理資源"""
        logger.info("🧹 正在清理完全優化的API-Agent資源...")
        
        # 生成最終性能報告
        await self.generate_final_performance_report()
        
        if self.api_fetcher:
            await self.api_fetcher.close()
        if self.db_manager:
            await self.db_manager.close()
            
        session_duration = time.time() - self.session_start_time
        logger.info(f"✅ 完全優化的API-Agent資源清理完成 (會話時長: {session_duration:.2f}秒)")
    
    async def process_platform_data_optimized(self, platform: str, days_ago: int = 1, limit: int = None) -> Dict[str, Any]:
        """完全優化的平台數據處理"""
        logger.info("="*60)
        logger.info(f"🔄 開始完全優化的平台數據處理")
        logger.info(f"   - 平台: {platform}")
        logger.info(f"   - 天數: {days_ago}")
        logger.info(f"   - 限制: {limit if limit else '無限制'}")
        logger.info("="*60)
        
        start_time = time.time()
        
        try:
            # 步驟1: 驗證平台配置
            if not self.config_manager.validate_config(platform):
                error_msg = f"平台配置無效: {platform}"
                logger.error(f"❌ {error_msg}")
                self.stats['errors'].append({
                    'error': error_msg,
                    'timestamp': datetime.now().isoformat(),
                    'platform': platform
                })
                return {'success': False, 'error': error_msg}
            
            # 步驟2: 執行完全優化的數據處理流程
            result = await self.api_fetcher.fetch_and_store_optimized(platform, days_ago, limit)
            
            # 步驟3: 更新統計信息
            if result['success']:
                self.stats['total_fetched'] += result.get('fetched_count', 0)
                self.stats['total_stored'] += result.get('stored_count', 0)
                self.stats['platforms_processed'].append({
                    'platform': platform,
                    'timestamp': datetime.now().isoformat(),
                    'fetched': result.get('fetched_count', 0),
                    'stored': result.get('stored_count', 0),
                    'duration': result.get('duration', 0)
                })
                
                # 記錄性能歷史
                performance_record = {
                    'platform': platform,
                    'timestamp': datetime.now().isoformat(),
                    'records_processed': result.get('stored_count', 0),
                    'duration': result.get('duration', 0),
                    'records_per_second': result.get('records_per_second', 0),
                    'success': True
                }
                self.stats['performance_history'].append(performance_record)
            
            duration = time.time() - start_time
            
            logger.info("="*60)
            logger.info(f"🎉 完全優化的平台數據處理完成!")
            logger.info(f"   - 平台: {platform}")
            logger.info(f"   - 結果: {'✅ 成功' if result['success'] else '❌ 失敗'}")
            logger.info(f"   - 獲取: {result.get('fetched_count', 0)} 條")
            logger.info(f"   - 存儲: {result.get('stored_count', 0)} 條")
            logger.info(f"   - 總時間: {duration:.2f} 秒")
            if result.get('records_per_second'):
                logger.info(f"   - 處理速度: {result['records_per_second']:.1f} 條/秒")
            
            # 金額統計
            if 'financial_summary' in result:
                financial = result['financial_summary']
                logger.info(f"   - 總銷售額: ${financial.get('total_sale_amount_usd', 0):,.2f} USD")
                logger.info(f"   - 總佣金: ${financial.get('total_payout_usd', 0):,.2f} USD")
            
            logger.info("="*60)
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            error_record = {
                'error': str(e),
                'platform': platform,
                'timestamp': datetime.now().isoformat(),
                'duration': duration
            }
            self.stats['errors'].append(error_record)
            
            logger.error("="*60)
            logger.error(f"❌ 完全優化的平台數據處理失敗!")
            logger.error(f"   - 平台: {platform}")
            logger.error(f"   - 錯誤: {e}")
            logger.error(f"   - 耗時: {duration:.2f} 秒")
            logger.error("="*60)
            
            return {
                'success': False,
                'platform': platform,
                'days_ago': days_ago,
                'error': str(e),
                'duration': duration
            }
    
    async def get_platform_stats_optimized(self, platform: str, days_ago: int) -> Dict[str, Any]:
        """獲取優化的平台統計信息"""
        try:
            # 使用優化查詢獲取統計
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_ago)
            
            conversions = await self.api_fetcher.fetch_conversions_optimized(platform, days_ago, limit=None)
            
            if not conversions:
                return {
                    'platform': platform,
                    'total_count': 0,
                    'total_amount': 0,
                    'total_payout': 0,
                    'avg_amount': 0,
                    'date_range': f"{start_date.date()} 到 {end_date.date()}"
                }
            
            # 計算統計信息
            total_amount = sum(conv.get('usd_sale_amount', 0) or 0 for conv in conversions)
            total_payout = sum(conv.get('usd_payout', 0) or 0 for conv in conversions)
            
            return {
                'platform': platform,
                'total_count': len(conversions),
                'total_amount': round(total_amount, 2),
                'total_payout': round(total_payout, 2),
                'avg_amount': round(total_amount / len(conversions), 2) if conversions else 0,
                'avg_payout': round(total_payout / len(conversions), 2) if conversions else 0,
                'date_range': f"{start_date.date()} 到 {end_date.date()}"
            }
            
        except Exception as e:
            logger.error(f"❌ 獲取平台統計失敗: {e}")
            return {
                'platform': platform,
                'error': str(e)
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """完整的系統健康檢查"""
        try:
            health_results = {}
            
            # API數據獲取器健康檢查
            if self.api_fetcher:
                health_results['api_fetcher'] = await self.api_fetcher.health_check()
            else:
                health_results['api_fetcher'] = {'status': 'not_initialized'}
            
            # 數據庫管理器健康檢查
            if self.db_manager:
                health_results['database_manager'] = await self.db_manager.health_check()
            else:
                health_results['database_manager'] = {'status': 'not_initialized'}
            
            # 整體系統狀態
            all_healthy = all(
                result.get('status') == 'healthy' 
                for result in health_results.values()
            )
            
            return {
                'status': 'healthy' if all_healthy else 'unhealthy',
                'optimization_level': 'full_optimization',
                'timestamp': datetime.now().isoformat(),
                **health_results
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """獲取完整的性能指標"""
        try:
            session_duration = time.time() - self.session_start_time
            
            # 獲取組件性能指標
            api_fetcher_metrics = await self.api_fetcher.get_performance_summary() if self.api_fetcher else {}
            db_manager_metrics = await self.db_manager.get_performance_metrics() if self.db_manager else {}
            
            # 計算會話統計
            total_records = self.stats['total_stored']
            overall_records_per_second = total_records / session_duration if session_duration > 0 else 0
            
            # 計算平均性能
            if self.stats['performance_history']:
                avg_records_per_second = sum(
                    record.get('records_per_second', 0) 
                    for record in self.stats['performance_history']
                ) / len(self.stats['performance_history'])
            else:
                avg_records_per_second = 0
            
            return {
                'session_summary': {
                    'duration_seconds': round(session_duration, 2),
                    'total_platforms_processed': len(self.stats['platforms_processed']),
                    'total_records_fetched': self.stats['total_fetched'],
                    'total_records_stored': self.stats['total_stored'],
                    'overall_records_per_second': round(overall_records_per_second, 2),
                    'average_records_per_second': round(avg_records_per_second, 2),
                    'success_rate': len(self.stats['platforms_processed']) / (len(self.stats['platforms_processed']) + len(self.stats['errors'])) * 100 if (self.stats['platforms_processed'] or self.stats['errors']) else 0,
                    'total_errors': len(self.stats['errors'])
                },
                'component_metrics': {
                    'api_fetcher': api_fetcher_metrics,
                    'database_manager': db_manager_metrics
                },
                'platform_history': self.stats['platforms_processed'],
                'error_history': self.stats['errors'],
                'performance_history': self.stats['performance_history'],
                'optimization_status': 'fully_optimized',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ 獲取性能指標失敗: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def generate_final_performance_report(self):
        """生成最終性能報告"""
        try:
            logger.info("📊 生成最終性能報告...")
            
            metrics = await self.get_performance_metrics()
            session = metrics.get('session_summary', {})
            
            logger.info("="*60)
            logger.info("📊 API-Agent 完全優化版 - 最終性能報告")
            logger.info("="*60)
            logger.info(f"會話時長: {session.get('duration_seconds', 0):.2f} 秒")
            logger.info(f"處理平台數: {session.get('total_platforms_processed', 0)}")
            logger.info(f"總獲取記錄: {session.get('total_records_fetched', 0):,}")
            logger.info(f"總存儲記錄: {session.get('total_records_stored', 0):,}")
            logger.info(f"整體處理速度: {session.get('overall_records_per_second', 0):.1f} 條/秒")
            logger.info(f"平均處理速度: {session.get('average_records_per_second', 0):.1f} 條/秒")
            logger.info(f"成功率: {session.get('success_rate', 0):.1f}%")
            logger.info(f"錯誤數量: {session.get('total_errors', 0)}")
            
            # 保存詳細報告到文件
            report_file = f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(metrics, f, indent=2, ensure_ascii=False)
            
            logger.info(f"詳細報告已保存到: {report_file}")
            logger.info("="*60)
            
        except Exception as e:
            logger.error(f"❌ 生成性能報告失敗: {e}")

async def main():
    """主程序入口"""
    parser = argparse.ArgumentParser(description='API-Agent 完全優化版')
    
    # 基本參數
    parser.add_argument('--platform', type=str, default='IAByteC',
                      help='平台名稱 (默認: IAByteC)')
    parser.add_argument('--days-ago', type=int, default=2,
                      help='獲取幾天前的數據 (默認: 2)')
    parser.add_argument('--limit', type=int, default=None,
                      help='限制處理的記錄數量')
    
    # 優化配置參數
    parser.add_argument('--batch-size', type=int, default=1000,
                      help='批量處理大小 (默認: 1000)')
    parser.add_argument('--max-connections', type=int, default=20,
                      help='最大數據庫連接數 (默認: 20)')
    parser.add_argument('--cache-ttl', type=int, default=300,
                      help='緩存TTL秒數 (默認: 300)')
    parser.add_argument('--disable-cache', action='store_true',
                      help='禁用緩存')
    parser.add_argument('--disable-monitoring', action='store_true',
                      help='禁用性能監控')
    
    # 功能參數
    parser.add_argument('--list-platforms', action='store_true',
                      help='列出可用平台')
    parser.add_argument('--health-check', action='store_true',
                      help='執行健康檢查')
    parser.add_argument('--performance-metrics', action='store_true',
                      help='顯示性能指標')
    parser.add_argument('--stats-only', action='store_true',
                      help='僅顯示統計信息')
    
    args = parser.parse_args()
    
    # 創建優化配置
    optimization_config = OptimizationConfig(
        batch_size=args.batch_size,
        max_connections=args.max_connections,
        cache_ttl=args.cache_ttl,
        enable_cache=not args.disable_cache,
        enable_monitoring=not args.disable_monitoring
    )
    
    # 創建優化API代理實例
    agent = OptimizedAPIAgent(optimization_config)
    
    try:
        # 初始化
        await agent.initialize()
        
        # 處理不同的命令
        if args.list_platforms:
            platforms = agent.config_manager.get_available_platforms()
            logger.info(f"🔍 可用平台: {platforms}")
            return
        
        if args.health_check:
            health = await agent.health_check()
            logger.info("🏥 系統健康檢查結果:")
            logger.info(json.dumps(health, indent=2, ensure_ascii=False))
            return
        
        if args.performance_metrics:
            metrics = await agent.get_performance_metrics()
            logger.info("📊 性能指標:")
            logger.info(json.dumps(metrics, indent=2, ensure_ascii=False))
            return
        
        if args.stats_only:
            stats = await agent.get_platform_stats_optimized(args.platform, args.days_ago)
            logger.info("📊 平台統計:")
            for key, value in stats.items():
                logger.info(f"   - {key}: {value}")
            return
        
        # 主要處理流程
        logger.info("🚀 開始API-Agent完全優化版數據處理流程")
        
        result = await agent.process_platform_data_optimized(
            platform=args.platform,
            days_ago=args.days_ago,
            limit=args.limit
        )
        
        if result['success']:
            logger.info("🎉 數據處理流程成功完成!")
        else:
            logger.error(f"❌ 數據處理流程失敗: {result.get('error')}")
            return 1
            
    except KeyboardInterrupt:
        logger.info("⚠️ 用戶中斷操作")
    except Exception as e:
        logger.error(f"❌ 程序執行失敗: {e}")
        import traceback
        logger.error(f"詳細錯誤: {traceback.format_exc()}")
        return 1
    finally:
        # 清理資源
        await agent.cleanup()
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        logger.error(f"❌ 程序啟動失敗: {e}")
        sys.exit(1) 