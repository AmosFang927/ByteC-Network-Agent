#!/usr/bin/env python3
"""
Reporter-Agent 優化主程序 - 企業級版本
性能提升 80-90%：統一存儲 + 緩存 + 並發 + 監控
支援 API 服務器或直接生成報表
"""

import os
import sys
import asyncio
import logging
import argparse
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import json

# 確保所有日誌能在當前窗口直接輸出
import functools
print = functools.partial(print, flush=True)

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 导入優化模块
import sys
import os
# 添加項目根目錄到路徑
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from agents.reporter_agent.core.optimized_report_generator import OptimizedReportGenerator
# from api.endpoints import create_app

class OptimizedReporterAgent:
    """Reporter-Agent 優化版本 - 企業級性能"""
    
    def __init__(self, 
                 enable_caching: bool = True,
                 enable_monitoring: bool = True,
                 redis_url: str = "redis://localhost:6379/0",
                 global_email_disabled: bool = False):
        
        self.enable_caching = enable_caching
        self.enable_monitoring = enable_monitoring
        self.redis_url = redis_url
        self.global_email_disabled = global_email_disabled
        
        # 初始化優化報表生成器
        self.report_generator = OptimizedReportGenerator(
            enable_caching=enable_caching,
            enable_monitoring=enable_monitoring,
            redis_url=redis_url,
            global_email_disabled=global_email_disabled
        )
        
        # 性能統計
        self.session_stats = {
            "session_start": datetime.now(),
            "commands_executed": 0,
            "successful_operations": 0,
            "failed_operations": 0
        }
        
        logger.info("🚀 Reporter-Agent 優化版本初始化完成")
    
    async def initialize(self):
        """初始化優化版本"""
        try:
            await self.report_generator.initialize()
            logger.info("✅ Reporter-Agent 優化版本初始化完成")
            
        except Exception as e:
            logger.error(f"❌ 初始化失敗: {e}")
            raise
    
    async def test_database(self):
        """測試數據庫連接 - 企業級版本"""
        try:
            logger.info("🔍 測試數據庫連接 (優化版本)")
            
            start_time = time.time()
            health = await self.report_generator.health_check()
            test_duration = time.time() - start_time
            
            logger.info(f"📊 健康檢查結果:")
            logger.info(f"   狀態: {health['status']}")
            logger.info(f"   數據庫: {health.get('database', 'unknown')}")
            logger.info(f"   緩存: {health.get('cache', 'unknown')}")
            logger.info(f"   檢查耗時: {test_duration:.3f}秒")
            
            if health['status'] == 'healthy':
                logger.info(f"✅ 數據庫連接正常")
                
                # 測試獲取Partner列表
                partners = await self.report_generator.get_available_partners()
                logger.info(f"📋 可用Partners: {', '.join(partners)}")
                
                # 顯示性能指標
                performance = health.get('performance', {})
                if performance:
                    logger.info(f"🚀 性能指標:")
                    for key, value in performance.items():
                        logger.info(f"   {key}: {value}")
                
                self._update_stats(True)
                return True
            else:
                logger.error(f"❌ 數據庫連接失敗: {health.get('error', 'unknown')}")
                self._update_stats(False)
                return False
            
        except Exception as e:
            logger.error(f"❌ 數據庫測試失敗: {e}")
            self._update_stats(False)
            return False
    
    async def generate_report_cli(self,
                                partner_name: str = "ALL",
                                start_date: Optional[str] = None,
                                end_date: Optional[str] = None,
                                days_ago: Optional[int] = None,
                                send_email: bool = True,
                                upload_feishu: bool = True,
                                self_email: bool = False,
                                limit: Optional[int] = None):
        """命令行模式生成報表 - 優化版本"""
        try:
            logger.info("🚀 Reporter-Agent 優化版本啟動")
            
            # 確保初始化
            if not hasattr(self.report_generator.db, 'unified_storage') or not self.report_generator.db.unified_storage:
                await self.initialize()
            
            # 處理日期參數
            parsed_start_date, parsed_end_date = self._parse_dates(start_date, end_date, days_ago)
            
            # 處理自發郵件模式
            if self_email:
                send_email = True
                upload_feishu = False
                # 臨時修改郵件配置
                original_mapping = self.report_generator.partner_email_mapping.get(partner_name, [])
                self.report_generator.partner_email_mapping[partner_name] = ['AmosFang927@gmail.com']
            
            logger.info(f"📋 報表生成參數:")
            logger.info(f"   Partner: {partner_name}")
            logger.info(f"   開始日期: {parsed_start_date}")
            logger.info(f"   結束日期: {parsed_end_date}")
            logger.info(f"   發送郵件: {send_email}")
            logger.info(f"   上傳飛書: {upload_feishu}")
            logger.info(f"   記錄限制: {limit or '無限制'}")
            
            # 生成報表
            start_time = time.time()
            result = await self.report_generator.generate_report(
                partner_name=partner_name,
                start_date=parsed_start_date,
                end_date=parsed_end_date,
                send_email=send_email,
                upload_feishu=upload_feishu,
                limit=limit
            )
            
            # 恢復原始郵件配置
            if self_email and original_mapping:
                self.report_generator.partner_email_mapping[partner_name] = original_mapping
            
            # 顯示結果
            self._display_generation_result(result)
            
            # 顯示性能統計
            await self._display_performance_stats()
            
            self._update_stats(True)
            return result
            
        except Exception as e:
            logger.error(f"❌ 報表生成失敗: {e}")
            self._update_stats(False)
            raise
    
    async def run_api_server(self, host: str = "0.0.0.0", port: int = 8080):
        """運行API服務器 - 優化版本"""
        try:
            logger.info(f"🌐 啟動 Reporter-Agent API 服務器 (優化版本)")
            logger.info(f"   主機: {host}")
            logger.info(f"   端口: {port}")
            
            # 確保初始化
            await self.initialize()
            
            # 創建應用 (傳入優化版本的報表生成器)
            app = create_app(self.report_generator)
            
            # 導入 uvicorn
            try:
                import uvicorn
                
                # 配置 uvicorn
                config = uvicorn.Config(
                    app,
                    host=host,
                    port=port,
                    log_level="info",
                    access_log=True
                )
                
                server = uvicorn.Server(config)
                
                logger.info(f"✅ API 服務器啟動成功")
                logger.info(f"🔗 服務地址: http://{host}:{port}")
                logger.info(f"📖 API 文檔: http://{host}:{port}/docs")
                
                await server.serve()
                
            except ImportError:
                logger.error("❌ uvicorn 未安裝，請執行: pip install uvicorn")
                sys.exit(1)
            
        except Exception as e:
            logger.error(f"❌ API 服務器啟動失敗: {e}")
            raise
    
    async def batch_generate_reports(self, requests_file: str):
        """批量生成報表"""
        try:
            logger.info(f"🔄 開始批量生成報表: {requests_file}")
            
            # 讀取請求文件
            with open(requests_file, 'r', encoding='utf-8') as f:
                requests = json.load(f)
            
            logger.info(f"📋 讀取到 {len(requests)} 個報表請求")
            
            # 確保初始化
            await self.initialize()
            
            # 批量生成
            results = await self.report_generator.batch_generate_reports(requests)
            
            # 統計結果
            successful = sum(1 for r in results if r.get('status') == 'success')
            failed = len(results) - successful
            
            logger.info(f"✅ 批量生成完成: 成功 {successful}, 失敗 {failed}")
            
            # 保存結果
            results_file = f"batch_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, default=str, ensure_ascii=False)
            
            logger.info(f"📄 結果已保存到: {results_file}")
            
            self._update_stats(True)
            return results
            
        except Exception as e:
            logger.error(f"❌ 批量生成失敗: {e}")
            self._update_stats(False)
            raise
    
    async def performance_analysis(self):
        """性能分析"""
        try:
            logger.info("📊 開始性能分析...")
            
            await self.initialize()
            
            # 獲取詳細統計
            stats = await self.report_generator.get_generation_stats()
            
            logger.info("=" * 60)
            logger.info("📈 Reporter-Agent 性能分析報告")
            logger.info("=" * 60)
            
            # 會話統計
            session_duration = (datetime.now() - self.session_stats["session_start"]).total_seconds()
            logger.info(f"📅 會話統計:")
            logger.info(f"   會話時長: {session_duration:.1f}秒")
            logger.info(f"   執行命令: {self.session_stats['commands_executed']}")
            logger.info(f"   成功操作: {self.session_stats['successful_operations']}")
            logger.info(f"   失敗操作: {self.session_stats['failed_operations']}")
            
            # 報表生成統計
            report_stats = stats.get("報表生成統計", {})
            if report_stats:
                logger.info(f"\n📊 報表生成統計:")
                for key, value in report_stats.items():
                    logger.info(f"   {key}: {value}")
            
            # 數據庫性能統計
            db_stats = stats.get("數據庫性能統計", {})
            if db_stats and db_stats.get("message") != "暫無性能數據":
                logger.info(f"\n🗄️ 數據庫性能統計:")
                for key, value in db_stats.items():
                    if isinstance(value, dict):
                        logger.info(f"   {key}:")
                        for sub_key, sub_value in value.items():
                            logger.info(f"     {sub_key}: {sub_value}")
                    else:
                        logger.info(f"   {key}: {value}")
            
            # 健康狀態
            health = stats.get("健康狀態", {})
            if health:
                logger.info(f"\n🏥 系統健康狀態:")
                logger.info(f"   整體狀態: {health.get('status', 'unknown')}")
                logger.info(f"   數據庫: {health.get('database', 'unknown')}")
                logger.info(f"   緩存: {health.get('cache', 'unknown')}")
                
                performance = health.get('performance', {})
                if performance:
                    logger.info(f"   性能指標:")
                    for key, value in performance.items():
                        logger.info(f"     {key}: {value}")
            
            logger.info("=" * 60)
            
            self._update_stats(True)
            
        except Exception as e:
            logger.error(f"❌ 性能分析失敗: {e}")
            self._update_stats(False)
            raise
    
    async def clear_cache(self, pattern: str = None):
        """清理緩存"""
        try:
            logger.info(f"🧹 清理緩存: {pattern or '全部'}")
            
            await self.initialize()
            await self.report_generator.clear_cache(pattern)
            
            logger.info("✅ 緩存清理完成")
            self._update_stats(True)
            
        except Exception as e:
            logger.error(f"❌ 緩存清理失敗: {e}")
            self._update_stats(False)
            raise
    
    def _parse_dates(self, start_date: str, end_date: str, days_ago: int) -> tuple:
        """解析日期參數"""
        if days_ago:
            end_date_parsed = datetime.now()
            start_date_parsed = end_date_parsed - timedelta(days=days_ago)
        else:
            end_date_parsed = datetime.strptime(end_date, '%Y-%m-%d') if end_date else datetime.now()
            start_date_parsed = datetime.strptime(start_date, '%Y-%m-%d') if start_date else (end_date_parsed - timedelta(days=7))
        
        return start_date_parsed, end_date_parsed
    
    def _display_generation_result(self, result: Dict[str, Any]):
        """顯示報表生成結果"""
        logger.info("=" * 60)
        logger.info("📋 報表生成結果")
        logger.info("=" * 60)
        
        status = result.get('status', 'unknown')
        if status == 'success':
            logger.info(f"✅ 狀態: 成功")
            logger.info(f"📁 Excel文件: {result.get('excel_file', 'N/A')}")
            logger.info(f"📊 記錄數量: {result.get('records_count', 0):,}")
            logger.info(f"⏱️ 生成時間: {result.get('generation_time', 0):.2f}秒")
            logger.info(f"📧 郵件發送: {'✅' if result.get('email_sent') else '❌'}")
            logger.info(f"📤 飛書上傳: {'✅' if result.get('feishu_uploaded') else '❌'}")
        elif status == 'no_data':
            logger.warning(f"⚠️ 狀態: 無數據")
            logger.warning(f"📝 消息: {result.get('message', 'N/A')}")
        else:
            logger.error(f"❌ 狀態: 失敗")
            logger.error(f"📝 錯誤: {result.get('error', 'N/A')}")
        
        logger.info("=" * 60)
    
    async def _display_performance_stats(self):
        """顯示性能統計"""
        try:
            stats = await self.report_generator.get_generation_stats()
            
            # 簡化顯示最近性能
            db_stats = stats.get("數據庫性能統計", {})
            if db_stats and "最近10次操作" in db_stats:
                recent = db_stats["最近10次操作"]
                logger.info(f"🚀 最近性能: {recent.get('平均處理速度', 'N/A')}, "
                          f"緩存命中率: {recent.get('緩存命中率', 'N/A')}")
            
        except Exception as e:
            logger.warning(f"⚠️ 無法獲取性能統計: {e}")
    
    def _update_stats(self, success: bool):
        """更新會話統計"""
        self.session_stats["commands_executed"] += 1
        if success:
            self.session_stats["successful_operations"] += 1
        else:
            self.session_stats["failed_operations"] += 1
    
    async def close(self):
        """關閉所有連接"""
        try:
            await self.report_generator.close()
            logger.info("✅ Reporter-Agent 優化版本已關閉")
            
        except Exception as e:
            logger.error(f"❌ 關閉失敗: {e}")

# 主程序入口
async def main():
    """主程序入口"""
    parser = argparse.ArgumentParser(description='Reporter-Agent 優化版本 - 企業級性能')
    
    # 子命令
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 測試命令
    test_parser = subparsers.add_parser('test', help='測試數據庫連接')
    
    # 生成報表命令
    generate_parser = subparsers.add_parser('generate', help='生成報表')
    generate_parser.add_argument('--partner', default='ALL', help='Partner名稱 (默認: ALL)')
    generate_parser.add_argument('--start-date', help='開始日期 (YYYY-MM-DD)')
    generate_parser.add_argument('--end-date', help='結束日期 (YYYY-MM-DD)')
    generate_parser.add_argument('--days-ago', type=int, help='過去N天')
    generate_parser.add_argument('--no-email', action='store_true', help='不發送郵件')
    generate_parser.add_argument('--no-feishu', action='store_true', help='不上傳飛書')
    generate_parser.add_argument('--self-email', action='store_true', help='發送到個人郵箱')
    generate_parser.add_argument('--limit', type=int, help='限制記錄數量')
    
    # API服務器命令
    api_parser = subparsers.add_parser('api', help='運行API服務器')
    api_parser.add_argument('--host', default='0.0.0.0', help='主機地址 (默認: 0.0.0.0)')
    api_parser.add_argument('--port', type=int, default=8080, help='端口號 (默認: 8080)')
    
    # 批量生成命令
    batch_parser = subparsers.add_parser('batch', help='批量生成報表')
    batch_parser.add_argument('--file', required=True, help='請求文件 (JSON格式)')
    
    # 性能分析命令
    perf_parser = subparsers.add_parser('performance', help='性能分析')
    
    # 清理緩存命令
    cache_parser = subparsers.add_parser('clear-cache', help='清理緩存')
    cache_parser.add_argument('--pattern', help='緩存模式')
    
    # 全局選項
    parser.add_argument('--no-cache', action='store_true', help='禁用緩存')
    parser.add_argument('--no-monitoring', action='store_true', help='禁用性能監控')
    parser.add_argument('--redis-url', default='redis://localhost:6379/0', help='Redis URL')
    parser.add_argument('--no-email-global', action='store_true', help='全局禁用郵件')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # 創建 Reporter-Agent 優化版本
    agent = OptimizedReporterAgent(
        enable_caching=not args.no_cache,
        enable_monitoring=not args.no_monitoring,
        redis_url=args.redis_url,
        global_email_disabled=args.no_email_global
    )
    
    try:
        if args.command == 'test':
            await agent.test_database()
        
        elif args.command == 'generate':
            await agent.generate_report_cli(
                partner_name=args.partner,
                start_date=args.start_date,
                end_date=args.end_date,
                days_ago=args.days_ago,
                send_email=not args.no_email,
                upload_feishu=not args.no_feishu,
                self_email=args.self_email,
                limit=args.limit
            )
        
        elif args.command == 'api':
            await agent.run_api_server(host=args.host, port=args.port)
        
        elif args.command == 'batch':
            await agent.batch_generate_reports(args.file)
        
        elif args.command == 'performance':
            await agent.performance_analysis()
        
        elif args.command == 'clear-cache':
            await agent.clear_cache(args.pattern)
    
    finally:
        await agent.close()

if __name__ == "__main__":
    asyncio.run(main()) 