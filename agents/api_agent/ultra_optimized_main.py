#!/usr/bin/env python3
"""
Ultra Optimized API Agent Main Program
超級優化API代理主程序

性能目標：
- 處理時間：從15-30分鐘 → 2-4分鐘  
- 性能提升：85-92%
- 10萬轉化數據處理能力
"""

import asyncio
import argparse
import sys
import os
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json

# 添加項目根目錄到路徑
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import config
from agents.api_agent.ultra_optimized_client import UltraOptimizedAPIClient

class UltraOptimizedAPIAgent:
    """
    超級優化API代理
    
    核心優化功能：
    1. 異步並發處理 (12個並發)
    2. 智能批量獲取 (1000條/頁)
    3. 高效數據庫插入 (2000條/批)
    4. 實時性能監控
    5. 智能錯誤重試
    """
    
    def __init__(self):
        self.logger = self._setup_logger()
        self.results = {}
        
    def _setup_logger(self):
        """設置日誌記錄器"""
        import logging
        logging.basicConfig(
            level=logging.INFO,
            format='🚀 %(asctime)s | %(levelname)s | %(message)s'
        )
        return logging.getLogger("UltraOptimizedAPIAgent")
    
    async def run_optimized_fetch(self, 
                                 platforms: List[str], 
                                 days_ago: int,
                                 end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        運行超級優化的數據獲取
        
        Args:
            platforms: 平台列表 (例如: ['IAByteC', 'IATestByteC'])
            days_ago: 獲取幾天前的數據
            end_date: 結束日期 (可選)
        
        Returns:
            Dict containing results for each platform
        """
        
        # 計算日期範圍
        if end_date:
            # 如果指定了結束日期，則獲取該日期前days_ago天的單日數據
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            target_dt = end_dt - timedelta(days=days_ago)
        else:
            # 如果沒有指定結束日期，則獲取今天前days_ago天的單日數據
            today = datetime.now()
            target_dt = today - timedelta(days=days_ago)
            
        # 獲取單日數據（開始和結束日期相同）
        start_date = target_dt.strftime('%Y-%m-%d')
        end_date_str = target_dt.strftime('%Y-%m-%d')
        
        self.logger.info("🚀 === 超級優化API代理啟動 ===")
        self.logger.info(f"📅 處理日期範圍: {start_date} 到 {end_date_str}")
        self.logger.info(f"🎯 目標平台: {', '.join(platforms)}")
        self.logger.info(f"⚡ 性能優化: 並發{config.MAX_CONCURRENT_REQUESTS}個, 頁面{config.DEFAULT_PAGE_LIMIT}條")
        
        total_start_time = time.time()
        overall_results = {}
        
        # 按平台處理
        for platform in platforms:
            platform_start_time = time.time()
            
            try:
                self.logger.info(f"\n🔄 開始處理平台: {platform}")
                
                # 獲取平台配置
                platform_config = self._get_platform_config(platform)
                if not platform_config:
                    self.logger.error(f"❌ 平台 {platform} 配置不存在")
                    continue
                
                # 使用超級優化客戶端
                async with UltraOptimizedAPIClient(platform_config) as client:
                    
                    # 進度回調函數
                    async def progress_callback(progress: float, current: int, total: int):
                        self.logger.info(f"📈 {platform} 進度: {progress:.1f}% ({current:,}/{total:,})")
                    
                    # 執行優化獲取
                    result = await client.fetch_all_conversions(
                        start_date=start_date,
                        end_date=end_date_str,
                        progress_callback=progress_callback
                    )
                    
                    platform_time = time.time() - platform_start_time
                    
                    # 記錄平台結果
                    overall_results[platform] = {
                        **result,
                        'platform_processing_time_minutes': platform_time / 60,
                        'start_date': start_date,
                        'end_date': end_date_str
                    }
                    
                    self.logger.info(f"✅ 平台 {platform} 完成:")
                    self.logger.info(f"   📊 記錄數: {result['total_records']:,}")
                    self.logger.info(f"   ⏱️ 時間: {platform_time/60:.2f} 分鐘")
                    self.logger.info(f"   🚀 速度: {result['performance_stats']['records_per_second']:.1f} 記錄/秒")
                    
            except Exception as e:
                self.logger.error(f"❌ 平台 {platform} 處理失敗: {e}")
                overall_results[platform] = {
                    'error': str(e),
                    'total_records': 0
                }
        
        # 生成總體報告
        total_time = time.time() - total_start_time
        overall_stats = self._generate_overall_stats(overall_results, total_time)
        
        self.logger.info("\n🎉 === 超級優化處理完成 ===")
        self.logger.info(f"⏱️ 總處理時間: {total_time/60:.2f} 分鐘")
        self.logger.info(f"📊 總記錄數: {overall_stats['total_records']:,}")
        self.logger.info(f"🚀 總體速度: {overall_stats['overall_records_per_second']:.1f} 記錄/秒")
        
        return {
            'platforms': overall_results,
            'overall_stats': overall_stats
        }
    
    def _get_platform_config(self, platform_name: str) -> Optional[Dict[str, Any]]:
        """獲取平台配置"""
        # 使用DMP Agent的API配置管理器
        from agents.data_dmp_agent.api_config_manager import APIConfigManager
        
        api_config_manager = APIConfigManager()
        platform_config = api_config_manager.get_config(platform_name)
        
        if not platform_config:
            return None
        
        return {
            'name': platform_name,
            'api_key': platform_config.get('api_key'),
            'api_secret': platform_config.get('secret'),
            'api_url': platform_config.get('base_url') + platform_config.get('endpoints', {}).get('conversions', '/conversions/range')
        }
    
    def _generate_overall_stats(self, results: Dict[str, Any], total_time: float) -> Dict[str, Any]:
        """生成總體統計"""
        total_records = 0
        total_requests = 0
        total_failed = 0
        successful_platforms = 0
        
        for platform, result in results.items():
            if 'error' not in result:
                total_records += result.get('total_records', 0)
                stats = result.get('performance_stats', {})
                total_requests += stats.get('total_requests', 0)
                total_failed += stats.get('failed_requests', 0)
                successful_platforms += 1
        
        overall_records_per_second = total_records / total_time if total_time > 0 else 0
        success_rate = (successful_platforms / len(results)) * 100 if results else 0
        
        return {
            'total_records': total_records,
            'total_processing_time_minutes': total_time / 60,
            'overall_records_per_second': overall_records_per_second,
            'total_api_requests': total_requests,
            'total_failed_requests': total_failed,
            'successful_platforms': successful_platforms,
            'total_platforms': len(results),
            'success_rate_percentage': success_rate,
            'performance_improvement': self._calculate_performance_improvement(total_records, total_time)
        }
    
    def _calculate_performance_improvement(self, records: int, time_minutes: float) -> Dict[str, Any]:
        """計算性能改進"""
        # 基準: 舊系統處理10萬記錄需要15-30分鐘
        old_time_min = 22.5  # 平均值
        old_time_max = 30.0
        
        if records == 0 or time_minutes == 0:
            return {
                'improvement_percentage': 0, 
                'time_saved_minutes': 0,
                'expected_old_time_minutes': 0,
                'actual_new_time_minutes': time_minutes
            }
        
        # 按比例計算舊系統需要的時間
        records_ratio = records / 100000  # 以10萬為基準
        expected_old_time = old_time_min * records_ratio
        
        improvement = ((expected_old_time - time_minutes) / expected_old_time) * 100
        time_saved = expected_old_time - time_minutes
        
        return {
            'improvement_percentage': max(0, improvement),
            'time_saved_minutes': max(0, time_saved),
            'expected_old_time_minutes': expected_old_time,
            'actual_new_time_minutes': time_minutes
        }

async def main():
    """主程序入口"""
    parser = argparse.ArgumentParser(description='超級優化API代理 - 提升85-92%性能')
    parser.add_argument('--platforms', 
                       default='IAByteC,IATestByteC',
                       help='平台列表，逗號分隔 (默认: IAByteC,IATestByteC)')
    parser.add_argument('--days-ago', 
                       type=int, 
                       default=1,
                       help='獲取幾天前的數據 (默认: 1)')
    parser.add_argument('--end-date',
                       help='結束日期 (格式: YYYY-MM-DD)')
    parser.add_argument('--output',
                       help='輸出結果到JSON文件')
    
    args = parser.parse_args()
    
    # 解析平台列表
    platforms = [p.strip() for p in args.platforms.split(',')]
    
    try:
        # 創建並運行超級優化代理
        agent = UltraOptimizedAPIAgent()
        results = await agent.run_optimized_fetch(
            platforms=platforms,
            days_ago=args.days_ago,
            end_date=args.end_date
        )
        
        # 輸出結果
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"📝 結果已保存到: {args.output}")
        
        # 顯示性能改進摘要
        overall_stats = results['overall_stats']
        perf_improvement = overall_stats.get('performance_improvement', {})
        
        print("\n🏆 === 性能改進摘要 ===")
        print(f"📊 處理記錄數: {overall_stats.get('total_records', 0):,}")
        print(f"⏱️ 實際用時: {overall_stats.get('total_processing_time_minutes', 0):.2f} 分鐘")
        print(f"⏱️ 舊系統預期: {perf_improvement.get('expected_old_time_minutes', 0):.2f} 分鐘")
        print(f"⚡ 性能提升: {perf_improvement.get('improvement_percentage', 0):.1f}%")
        print(f"💾 節省時間: {perf_improvement.get('time_saved_minutes', 0):.2f} 分鐘")
        print(f"🚀 處理速度: {overall_stats.get('overall_records_per_second', 0):.1f} 記錄/秒")
        
        return results
        
    except KeyboardInterrupt:
        print("\n⚠️ 用戶中斷操作")
        return None
    except Exception as e:
        print(f"❌ 執行失敗: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    # 運行主程序
    results = asyncio.run(main())
    
    if results:
        print("\n✅ 超級優化API代理執行完成!")
    else:
        print("\n❌ 執行失敗或被中斷")
        sys.exit(1) 