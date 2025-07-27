#!/usr/bin/env python3
"""
API代理主程序
负责从各个API获取数据并存储到数据库
"""

import sys
import os
import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import argparse

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import config
from agents.api_agent.ultra_optimized_client import UltraOptimizedAPIClient
from agents.data_dmp_agent.api_config_manager import APIConfigManager

class APIAgent:
    """API代理主程序"""
    
    def __init__(self):
        self.logger = self._setup_logger()
        self.stats = {
            'total_fetched': 0,
            'total_stored': 0,
            'errors': []
        }
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        # 清除现有的处理器
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('🚀 %(asctime)s | %(levelname)s | %(message)s')
        console_handler.setFormatter(console_formatter)
        
        # 创建文件处理器
        file_handler = logging.FileHandler('api_agent.log')
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
        file_handler.setFormatter(file_formatter)
        
        # 设置根日志记录器
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)
        
        # 创建专用记录器
        logger = logging.getLogger("APIAgent")
        logger.setLevel(logging.INFO)
        
        # 确保强制输出
        logger.propagate = True
        
        return logger
    
    def _get_platform_config(self, platform: str) -> Optional[Dict[str, Any]]:
        """获取平台配置"""
        try:
            api_config = APIConfigManager()
            config_data = api_config.get_config(platform)
            if config_data:
                # 修复：确保包含平台代码以正确映射到数据库表
                config_data['platform_code'] = platform
            return config_data
        except Exception as e:
            self.logger.error(f"❌ 获取平台 {platform} 配置失败: {e}")
            return None
    
    async def run_ultra_optimized_mode(self, 
                                     platforms: List[str], 
                                     days_ago: int,
                                     end_date: Optional[str] = None,
                                     limit: Optional[int] = None,
                                     partner: Optional[str] = None,
                                     passthrough: bool = False,
                                     reporter_agent: bool = False) -> Dict[str, Any]:
        """
        运行超级优化模式
        
        Args:
            platforms: 平台列表 (例如: ['IAByteC', 'IATestByteC'])
            days_ago: 获取几天前的数据
            end_date: 结束日期 (可选)
            limit: 数据限制 (可选)
            partner: 指定的 Partner (可选，用于过滤 Sources)
            passthrough: 是否启用Passthrough模式 (不插入Cloud SQL)
            reporter_agent: 是否调用Reporter Agent生成报告
            
        Returns:
            Dict containing results for each platform
        """
        
        # 计算日期范围（修复后的逻辑：获取单日数据）
        if end_date:
            # 如果指定了结束日期，则获取该日期前days_ago天的单日数据
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            target_dt = end_dt - timedelta(days=days_ago)
        else:
            # 如果没有指定结束日期，则获取今天前days_ago天的单日数据
            today = datetime.now()
            target_dt = today - timedelta(days=days_ago)
            
        # 获取单日数据（开始和结束日期相同）
        start_date = target_dt.strftime('%Y-%m-%d')
        end_date_str = target_dt.strftime('%Y-%m-%d')
        
        self.logger.info("🚀 === 超级优化API代理启动 ===")
        self.logger.info(f"📅 处理日期范围: {start_date} 到 {end_date_str}")
        self.logger.info(f"🎯 目标平台: {', '.join(platforms)}")
        if partner:
            self.logger.info(f"👥 目标 Partner: {partner}")
            sources = config.get_sources_for_partner(partner)
            self.logger.info(f"📋 目标 Sources: {sources}")
        
        # 🔄 Phase 2: 显示新功能状态
        if passthrough:
            self.logger.info("🔄 Passthrough模式: 启用 - 数据不会插入Cloud SQL")
        else:
            self.logger.info("💾 标准模式: 数据将存储到Cloud SQL")
            
        if reporter_agent:
            self.logger.info("📊 Reporter Agent: 启用 - 处理完成后将生成报告")
            
        self.logger.info(f"⚡ 性能优化: 并发{config.API_AGENT_MAX_CONCURRENT_REQUESTS}个, 页面{config.DEFAULT_PAGE_LIMIT}条")
        
        total_start_time = time.time()
        overall_results = {}
        
        # 按平台处理
        for platform in platforms:
            platform_start_time = time.time()
            
            try:
                self.logger.info(f"\n🔄 开始处理平台: {platform}")
                
                # 获取平台配置
                platform_config = self._get_platform_config(platform)
                if not platform_config:
                    self.logger.error(f"❌ 平台 {platform} 配置不存在")
                    continue
                
                # 使用超级优化客户端
                async with UltraOptimizedAPIClient(platform_config) as client:
                    
                    # 进度回调函数
                    async def progress_callback(progress: float, current: int, total: int):
                        self.logger.info(f"📈 {platform} 进度: {progress:.1f}% ({current:,}/{total:,})")
                    
                    # 执行优化获取
                    result = await client.fetch_all_conversions(
                        start_date=start_date,
                        end_date=end_date_str,
                        progress_callback=progress_callback,
                        limit=limit,
                        partner=partner  # 添加 Partner 过滤
                    )
                    
                    platform_time = time.time() - platform_start_time
                    
                    # 记录平台结果
                    overall_results[platform] = {
                        **result,
                        'platform_processing_time_minutes': platform_time / 60,
                        'start_date': start_date,
                        'end_date': end_date_str
                    }
                    
                    self.logger.info(f"✅ 平台 {platform} 完成:")
                    self.logger.info(f"   📊 记录数: {result.get('total_records', 0):,}")
                    self.logger.info(f"   ⏱️ 时间: {platform_time/60:.2f} 分钟")
                    
            except Exception as e:
                self.logger.error(f"❌ 平台 {platform} 处理失败: {e}")
                overall_results[platform] = {'error': str(e)}
        
        # 计算总体统计
        total_time = time.time() - total_start_time
        
        # 生成总体统计
        overall_stats = self._calculate_overall_stats(overall_results, total_time)
        
        final_results = {
            'overall_stats': overall_stats,
            'platform_results': overall_results,
            'processing_info': {
                'mode': 'ultra_optimized',
                'start_time': datetime.fromtimestamp(total_start_time).isoformat(),
                'end_time': datetime.now().isoformat(),
                'total_time_minutes': total_time / 60,
                'passthrough_mode': passthrough,
                'reporter_agent_enabled': reporter_agent
            }
        }
        
        # 🔄 Phase 3: Agent间调用逻辑
        if reporter_agent and config.ENABLE_REPORTER_AGENT_CALLING:
            try:
                from shared.utils.agent_caller import call_reporter_agent
                
                # 🔍 打印Reporter Agent调用信息
                self.logger.info("=" * 60)
                self.logger.info("📊 准备调用Reporter Agent")
                self.logger.info("=" * 60)
                self.logger.info(f"📊 数据源: API Agent → Reporter Agent")
                self.logger.info(f"🔄 API Agent处理结果:")
                self.logger.info(f"   - 总记录数: {overall_stats.get('total_records', 0):,}")
                self.logger.info(f"   - 总金额: ${overall_stats.get('total_usd_amount', 0):,.2f} USD")
                self.logger.info(f"   - 处理平台: {', '.join(platforms)}")
                self.logger.info(f"   - Passthrough模式: {passthrough}")
                self.logger.info("=" * 60)
                
                # 为每个成功处理的平台调用Reporter Agent
                for platform in platforms:
                    if platform in overall_results and 'error' not in overall_results[platform]:
                        platform_result = overall_results[platform]
                        
                        self.logger.info(f"⚙️ 调用Reporter Agent - 平台: {platform}")
                        self.logger.info(f"   - days_ago: {days_ago}")
                        self.logger.info(f"   - 平台记录数: {platform_result.get('total_records', 0):,}")
                        self.logger.info(f"   - output_format: json")
                        
                        # 🗺️ Platform信息與Partner映射關係說明
                        try:
                            import sys
                            import os
                            sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                            from config import PARTNER_SOURCES_MAPPING
                            
                            self.logger.info("")
                            self.logger.info(f"🏢 Platform信息: {platform}")
                            self.logger.info(f"   📊 數據來源: {platform} API")
                            self.logger.info(f"   💾 存儲位置: Cloud SQL 數據庫")
                            self.logger.info(f"   🎯 後續處理: Reporter Agent將根據Partner配置生成對應報告")
                            
                            self.logger.info("")
                            self.logger.info("🗺️ 系統中的Partner映射關係總覽:")
                            for partner_name, partner_config in PARTNER_SOURCES_MAPPING.items():
                                sources = partner_config.get('sources', [])
                                if sources != ["ALL"]:
                                    source_display = ', '.join(sources)
                                    self.logger.info(f"   📋 Partner '{partner_name}' ← Sources: {source_display}")
                                else:
                                    self.logger.info(f"   📋 Partner '{partner_name}' ← Sources: ALL (所有數據)")
                            
                            self.logger.info("")
                            self.logger.info(f"ℹ️ 說明: API Agent處理Platform '{platform}' 的數據")
                            self.logger.info(f"        Reporter Agent將基於aff_sub字段值匹配對應的Partner")
                                
                        except ImportError as e:
                            self.logger.warning(f"⚠️ 無法獲取Partner映射信息: {e}")
                        
                        self.logger.info("---" * 20)
                        
                        # 🔍 打印Reporter Agent输入文件信息
                        self.logger.info("📄 Reporter Agent輸入文件信息:")
                        self.logger.info(f"   - 📊 數據來源: 直接從Cloud SQL數據庫讀取")
                        self.logger.info(f"   - 📂 導入文件: 無 (使用數據庫查詢)")
                        self.logger.info(f"   - 🎯 查詢範圍: {platform} 平台數據")
                        self.logger.info("---" * 20)
                        
                        reporter_result = await call_reporter_agent(
                            platform=platform,
                            days_ago=days_ago,
                            output_format='json'
                        )
                        
                        if reporter_result.get('success'):
                            self.logger.info(f"✅ {platform} Reporter Agent调用成功")
                        else:
                            self.logger.warning(f"⚠️ {platform} Reporter Agent调用失败: {reporter_result.get('error', 'Unknown error')}")
                        
                        # 将Reporter结果添加到final_results中
                        if 'reporter_results' not in final_results:
                            final_results['reporter_results'] = {}
                        final_results['reporter_results'][platform] = reporter_result
                        
            except Exception as e:
                self.logger.error(f"❌ Reporter Agent调用失败: {e}")
                final_results['reporter_error'] = str(e)
        
        self.logger.info("\n🎉 === 超级优化处理完成 ===")
        self.logger.info(f"⏱️ 总处理时间: {total_time/60:.2f} 分钟")
        self.logger.info(f"📊 总记录数: {overall_stats.get('total_records', 0):,}")
        self.logger.info(f"💰 总USD金额: ${overall_stats.get('total_usd_amount', 0):,.2f}")
        self.logger.info(f"💱 使用货币: {config.PREFERRED_CURRENCY}")
        self.logger.info(f"🚀 总体速度: {overall_stats.get('overall_records_per_second', 0):.1f} 记录/秒")
        
        # 添加详细的currency验证信息
        if 'currency_breakdown' in overall_stats:
            self.logger.info(f"💱 货币验证结果: {overall_stats['currency_breakdown']}")
            if overall_stats['currency_breakdown'].get('USD', 0) == overall_stats.get('total_records', 0):
                self.logger.info("✅ 货币验证通过: 所有记录都使用USD")
            else:
                self.logger.warning("⚠️ 货币验证异常: 存在非USD记录")
        
        # 添加平台级别的金额汇总
        for platform, result in overall_results.items():
            if 'error' not in result and 'stats' in result:
                platform_amount = result['stats'].get('total_usd_amount', 0)
                platform_records = result.get('total_records', 0)
                self.logger.info(f"📊 平台 {platform}: {platform_records:,} 条记录, ${platform_amount:,.2f} USD")
        
        return final_results
    
    def _calculate_overall_stats(self, platform_results: Dict[str, Any], total_time: float) -> Dict[str, Any]:
        """计算总体统计信息"""
        total_records = 0
        total_requests = 0
        total_failed = 0
        successful_platforms = 0
        total_usd_amount = 0.0
        currency_breakdown = {}
        
        for platform, result in platform_results.items():
            if 'error' not in result:
                successful_platforms += 1
                total_records += result.get('total_records', 0)
                if 'stats' in result:
                    stats = result['stats']
                    total_requests += stats.get('total_requests', 0)
                    total_failed += stats.get('failed_requests', 0)
                    total_usd_amount += stats.get('total_usd_amount', 0.0)
                    
                    # 汇总currency分布
                    platform_currency = stats.get('currency_breakdown', {})
                    for currency, count in platform_currency.items():
                        currency_breakdown[currency] = currency_breakdown.get(currency, 0) + count
        
        return {
            'total_records': total_records,
            'total_requests': total_requests,
            'failed_requests': total_failed,
            'successful_platforms': successful_platforms,
            'total_platforms': len(platform_results),
            'total_time_seconds': total_time,
            'total_usd_amount': round(total_usd_amount, 2),
            'currency_breakdown': currency_breakdown,
            'overall_records_per_second': total_records / total_time if total_time > 0 else 0
        }

def main():
    """主程序入口"""
    parser = argparse.ArgumentParser(description='API代理 - 获取转化数据')
    parser.add_argument('--days-ago', type=int, default=1, help='获取几天前的数据')
    parser.add_argument('--platform', type=str, help='要处理的平台列表 (逗号分隔)')
    parser.add_argument('--end-date', help='结束日期 (YYYY-MM-DD)')
    parser.add_argument('--limit', type=int, help='数据限制')
    parser.add_argument('--partner', help='指定的 Partner (用于过滤 Sources)')
    
    # 🧠 智能模式切换参数 - 方案1优化
    parser.add_argument('--verify-currency', action='store_true', 
                       help='启用Currency验证模式 (单线程+验证，确保所有记录为USD)')
    parser.add_argument('--concurrent', type=int, default=config.API_AGENT_DEFAULT_CONCURRENT,
                       help=f'手动设置并发数 (覆盖默认配置，1=单线程，12=最大并发，默认={config.API_AGENT_DEFAULT_CONCURRENT})')
    
    # 🔄 Phase 2: 新增参数 (Additive Only - 保持向后兼容性)
    parser.add_argument('--passthrough', action='store_true',
                       help='Passthrough模式: 不插入Cloud SQL，仅获取和处理数据')
    parser.add_argument('--reporter-agent', action='store_true',
                       help='启用Reporter Agent调用: 处理完成后调用Reporter Agent生成报告')
    
    args = parser.parse_args()
    
    # 解析平台列表
    if args.platform:
        # 支持逗号分隔的平台列表
        platforms = [p.strip() for p in args.platform.split(',')]
    else:
        # 如果没有指定平台，使用默认平台
        platforms = ['IAByteC']
    
    # 🧠 处理智能模式切换参数
    # 1. Currency验证模式覆盖
    if args.verify_currency:
        config.API_AGENT_CURRENCY_VERIFICATION_MODE = True
        config.API_AGENT_ENABLE_BATCH_CONCURRENT = False
        config.API_AGENT_FORCE_SEQUENTIAL_MODE = True
        print("🔄 已启用Currency验证模式：单线程+验证")
    
    # 2. 手动并发数覆盖
    if args.concurrent != config.API_AGENT_DEFAULT_CONCURRENT:
        config.API_AGENT_MAX_CONCURRENT_REQUESTS = args.concurrent
        if args.concurrent == 1:
            config.API_AGENT_ENABLE_BATCH_CONCURRENT = False
            config.API_AGENT_FORCE_SEQUENTIAL_MODE = True
            print(f"🔄 已手动设置为单线程模式")
        else:
            config.API_AGENT_ENABLE_BATCH_CONCURRENT = True
            config.API_AGENT_FORCE_SEQUENTIAL_MODE = False
            print(f"🔄 已手动设置并发数为 {args.concurrent}")
    else:
        print(f"🔄 使用默认并发配置: {config.API_AGENT_DEFAULT_CONCURRENT}")

    # 🔄 风险控制检查 - Phase 2 新功能
    if args.passthrough:
        print("🔄 已启用Passthrough模式：数据不会插入Cloud SQL")
    
    if args.reporter_agent:
        print("📊 已启用Reporter Agent调用：处理完成后将生成报告")

    # 运行API代理
    agent = APIAgent()
    asyncio.run(agent.run_ultra_optimized_mode(
        platforms=platforms,
        days_ago=args.days_ago,
        end_date=args.end_date,
        limit=args.limit,
        partner=args.partner,
        passthrough=args.passthrough,
        reporter_agent=args.reporter_agent
    ))

if __name__ == '__main__':
    main() 