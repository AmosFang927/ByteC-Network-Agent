#!/usr/bin/env python3
"""
Reporter-Agent 主启动文件 - 優化版本
支持运行API服务器或直接生成报表
集成優化方案：統一存儲 + 緩存 + 並發 + 監控
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

# 修復導入路徑問題
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# 强制日志输出到前台
# import sys  # 已在上面導入
# import os   # 已在上面導入

# 设置环境变量强制输出不被缓冲
os.environ['PYTHONUNBUFFERED'] = '1'

# 配置日志强制输出到前台
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
    force=True
)

# 确保所有logger都输出到stdout
for handler in logging.root.handlers:
    handler.setStream(sys.stdout)

logger = logging.getLogger(__name__)

# 强制刷新stdout
sys.stdout.flush()

# 导入模块 - 使用絕對導入避免相對導入錯誤
try:
    from agents.reporter_agent.core.report_generator import ReportGenerator
    from agents.reporter_agent.core.database import PostbackDatabase
    # from agents.reporter_agent.api.endpoints import create_app
except ImportError as e:
    # 如果絕對導入失敗，嘗試相對導入
    logger.warning(f"絕對導入失敗，嘗試相對導入: {e}")
    try:
        from core.report_generator import ReportGenerator
        from core.database import PostbackDatabase
        # from api.endpoints import create_app
    except ImportError as e2:
        logger.error(f"導入失敗: {e2}")
        print("❌ 模組導入失敗，請檢查 PYTHONPATH 設置")
        sys.exit(1)

class PerformanceMonitor:
    """性能監控器"""
    
    def __init__(self):
        self.start_time = None
        self.metrics = {}
    
    def start_timer(self, operation: str):
        """開始計時"""
        self.start_time = time.time()
        logger.info(f"⏱️  開始執行: {operation}")
    
    def end_timer(self, operation: str):
        """結束計時並記錄"""
        if self.start_time:
            duration = time.time() - self.start_time
            self.metrics[operation] = duration
            logger.info(f"✅ 完成執行: {operation} (耗時: {duration:.2f}秒)")
            return duration
        return 0
    
    def get_metrics(self) -> Dict[str, Any]:
        """獲取性能指標"""
        return self.metrics.copy()

async def generate_report_cli(partner_name: str = "ALL",
                            start_date: Optional[str] = None,
                            end_date: Optional[str] = None,
                            days_ago: Optional[int] = None,
                            send_email: bool = True,
                            upload_feishu: bool = True,
                            self_email: bool = False,
                            limit: Optional[int] = None,
                            enable_monitoring: bool = True,
                            import_file: Optional[str] = None):
    """命令行模式生成报表 - 增強版本"""
    
    # 初始化性能監控
    monitor = PerformanceMonitor() if enable_monitoring else None
    
    try:
        logger.info("🚀 Reporter-Agent 命令行模式启动 (優化版本)")
        
        if monitor:
            monitor.start_timer("完整報表生成流程")
        
        # 🔍 檢查是否使用文件導入模式
        if import_file:
            logger.info(f"📁 檔案導入模式: {import_file}")
            
            # 實現從DMP文件讀取數據並生成報告
            try:
                import pandas as pd
                
                # 檢查文件是否存在
                if not os.path.exists(import_file):
                    raise FileNotFoundError(f"導入文件不存在: {import_file}")
                
                logger.info(f"📊 正在讀取DMP輸出文件...")
                
                # 讀取DMP Agent輸出的Excel文件
                df = pd.read_excel(import_file)
                # logger.info(f"✅ 成功讀取文件: {len(df):,} 行數據, {len(df.columns)} 列")
                
                # 🔍 打印數據結構以便調試
                # logger.info(f"📋 文件列名: {list(df.columns)}")
                # if len(df) > 0:
                #     logger.info("📊 前幾行數據預覽:")
                #     for i, row in df.head(3).iterrows():
                #         logger.info(f"   行 {i}: {dict(row)}")
                
                # 直接使用現有的報告生成邏輯，但傳入讀取的數據
                # 創建一個特殊的報告生成器，用於處理文件數據
                from agents.reporter_agent.core.file_report_generator import FileReportGenerator
                
                file_generator = FileReportGenerator()
                
                # 使用文件數據生成報告
                result = await file_generator.generate_report_from_file(
                    df=df,
                    partner_name=partner_name,
                    import_file_path=import_file,
                    send_email=send_email,
                    upload_feishu=upload_feishu,
                    self_email=self_email,
                    start_date=start_date,
                    end_date=end_date
                )
                
                if monitor:
                    monitor.end_timer("完整報表生成流程")
                
                # 輸出結果
                if result['success']:
                    logger.info("✅ 文件導入報表生成成功")
                    logger.info(f"📊 Partner: {result['partner_name']}")
                    logger.info(f"📄 原始文件: {import_file}")
                    logger.info(f"📝 處理記錄數: {result['total_records']:,}")
                    logger.info(f"💰 總金額: ${result['total_amount']:,.2f}")
                    logger.info(f"📁 生成文件: {len(result['excel_files'])} 個")
                    
                    for file_path in result['excel_files']:
                        logger.info(f"   📄 {file_path}")
                else:
                    logger.error(f"❌ 文件導入報表生成失敗: {result['error']}")
                    if monitor:
                        monitor.end_timer("完整報表生成流程")
                    sys.exit(1)
                
                # 性能監控報告
                if monitor:
                    monitor_result = monitor.get_metrics()
                    logger.info("📊 性能監控報告:")
                    logger.info(f"   🕐 總執行時間: {monitor_result.get('完整報表生成流程', 0):.2f}秒")
                    logger.info(f"   📦 處理記錄數: {result['total_records']:,}")
                    
                    # 保存性能報告
                    performance_report = {
                        "timestamp": datetime.now().isoformat(),
                        "mode": "file_import",
                        "import_file": import_file,
                        "partner": partner_name,
                        "records_processed": result['total_records'],
                        "total_time": monitor_result.get('完整報表生成流程', 0),
                        "metrics": monitor_result,
                        "records_per_second": result['total_records'] / monitor_result.get('完整報表生成流程', 1) if monitor_result.get('完整報表生成流程', 0) > 0 else 0
                    }
                    
                    performance_file = f"output/performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    with open(performance_file, 'w') as f:
                        json.dump(performance_report, f, indent=2)
                    # logger.info(f"📄 性能報告已保存: {performance_file}")
                
                return  # 檔案導入模式完成，直接返回
                
            except ImportError:
                logger.error("❌ 無法導入 FileReportGenerator，將使用標準數據庫查詢模式")
            except Exception as e:
                logger.error(f"❌ 檔案導入失敗: {e}")
                logger.info("🔄 回退到標準數據庫查詢模式")
        
        # 创建报表生成器
        generator = ReportGenerator()
        
        # 处理日期参数
        if days_ago:
            # --days-ago 2 表示拉取2天前那一日的數據
            target_date = datetime.now() - timedelta(days=days_ago)
            start_dt = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_dt = start_dt + timedelta(days=1) - timedelta(seconds=1)  # 該天的23:59:59
            logger.info(f"🗓️  days_ago={days_ago}, 拉取日期範圍: {start_dt.strftime('%Y-%m-%d %H:%M:%S')} 到 {end_dt.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
            end_dt = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None
            if start_dt:
                start_dt = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)
            if end_dt:
                end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # 添加limit日志
        if limit:
            logger.info(f"🔢 设置数据拉取限制: {limit} 条记录")
        
        # 性能監控 - 數據查詢階段
        if monitor:
            monitor.start_timer("數據庫查詢")
        
        # 生成报表
        result = await generator.generate_partner_report(
            partner_name=partner_name,
            start_date=start_dt,
            end_date=end_dt,
            send_email=send_email,
            upload_feishu=upload_feishu,
            self_email=self_email,
            limit=limit
        )
        
        if monitor:
            monitor.end_timer("數據庫查詢")
        
        # 输出结果
        if result['success']:
            logger.info("✅ 报表生成成功")
            logger.info(f"📊 Partner: {result['partner_name']}")
            logger.info(f"📅 日期范围: {result['start_date']} 至 {result['end_date']}")
            logger.info(f"📝 总记录数: {result['total_records']:,}")
            logger.info(f"💰 总金额: ${result['total_amount']:,.2f}")
            logger.info(f"📁 生成文件: {len(result['excel_files'])} 个")
            
            # 如果设置了limit且达到限制，显示提示信息
            if limit and result['total_records'] >= limit:
                logger.info(f"⚠️ 已达到设置的数据拉取限制 ({limit} 条)，程序正常继续运行")
                print(f"📋 提示: 由于设置了 --limit {limit} 参数，只处理了前 {limit} 条转化记录")
                print("🔄 如需处理更多数据，请调整 --limit 参数或移除该参数")
        else:
            logger.error(f"❌ 报表生成失败: {result['error']}")
            if monitor:
                monitor.end_timer("完整報表生成流程")
            sys.exit(1)
        
        # 性能監控報告
        if monitor:
            total_time = monitor.end_timer("完整報表生成流程")
            metrics = monitor.get_metrics()
            
            logger.info("📊 性能監控報告:")
            logger.info(f"   🕐 總執行時間: {total_time:.2f}秒")
            logger.info(f"   📦 處理記錄數: {result['total_records']:,}")
            
            if result['total_records'] > 0:
                records_per_second = result['total_records'] / total_time
                logger.info(f"   ⚡ 處理速度: {records_per_second:.2f} 記錄/秒")
            
            # 保存性能指標到文件
            performance_file = f"output/performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            os.makedirs("output", exist_ok=True)
            
            performance_data = {
                'timestamp': datetime.now().isoformat(),
                'partner': partner_name,
                'records_processed': result['total_records'],
                'total_time': total_time,
                'metrics': metrics,
                'records_per_second': result['total_records'] / total_time if total_time > 0 else 0
            }
            
            with open(performance_file, 'w', encoding='utf-8') as f:
                json.dump(performance_data, f, indent=2, ensure_ascii=False)
            
            # logger.info(f"📄 性能報告已保存: {performance_file}")
        
        # 清理资源
        try:
            await generator.cleanup()
        except Exception as cleanup_error:
            logger.warning(f"⚠️ 資源清理警告: {cleanup_error}")
        
    except Exception as e:
        logger.error(f"❌ 命令行执行失败: {e}")
        if monitor:
            monitor.end_timer("完整報表生成流程")
        sys.exit(1)

async def test_database():
    """测试数据库连接 - 增強版本"""
    try:
        logger.info("🔍 测试数据库连接")
        
        # 性能監控
        monitor = PerformanceMonitor()
        monitor.start_timer("數據庫連接測試")
        
        db = PostbackDatabase()
        health = await db.health_check()
        
        logger.info(f"数据库状态: {health['status']}")
        if health['status'] == 'healthy':
            logger.info(f"✅ 数据库连接正常")
            logger.info(f"   租户数量: {health.get('tenant_count', 'N/A')}")
            logger.info(f"   转化记录数: {health.get('conversion_count', 'N/A')}")
            
            # 額外的連接測試
            logger.info("🔍 執行額外的連接測試...")
            
            # 測試獲取Partner列表
            try:
                partners = await db.get_available_partners()
                logger.info(f"📋 可用Partners: {', '.join(partners) if partners else '無'}")
            except Exception as e:
                logger.warning(f"⚠️ 獲取Partners失敗: {e}")
            
            # 測試簡單查詢
            try:
                test_data = await db.get_conversion_dataframe(
                    partner_name="ALL", 
                    limit=5
                )
                logger.info(f"📊 測試查詢成功: 獲取 {len(test_data)} 條測試記錄")
            except Exception as e:
                logger.warning(f"⚠️ 測試查詢失敗: {e}")
                
        else:
            logger.error(f"❌ 数据库连接失败: {health.get('error', '未知錯誤')}")
            sys.exit(1)
        
        # 關閉連接
        try:
            await db.close_pool()
        except:
            pass
        
        test_time = monitor.end_timer("數據庫連接測試")
        logger.info(f"✅ 数据库测试完成 (耗時: {test_time:.2f}秒)")
        
    except Exception as e:
        logger.error(f"❌ 数据库测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

def run_api_server(host: str = "0.0.0.0", port: int = 8080):
    """运行API服务器"""
    try:
        logger.info("🚀 Reporter-Agent API 服务器启动")
        logger.info(f"🌐 监听地址: http://{host}:{port}")
        
        # 動態導入以避免早期導入錯誤
        try:
            from agents.reporter_agent.api.endpoints import create_app
        except ImportError:
            from api.endpoints import create_app
        
        import uvicorn
        app = create_app()
        
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info",
            access_log=True
        )
        
    except Exception as e:
        logger.error(f"❌ API服务器启动失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

def main():
    """主函数 - 增強版本"""
    parser = argparse.ArgumentParser(
        description="Reporter-Agent - 基于 bytec-network 的实时报表生成系统 (優化版本)"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # API 服务器模式
    api_parser = subparsers.add_parser('api', help='运行API服务器')
    api_parser.add_argument('--host', default='0.0.0.0', help='监听地址')
    api_parser.add_argument('--port', type=int, default=8080, help='监听端口')
    
    # 命令行生成模式
    generate_parser = subparsers.add_parser('generate', help='生成报表')
    generate_parser.add_argument('--partner', default='ALL', help='Partner名称')
    generate_parser.add_argument('--start-date', help='开始日期 (YYYY-MM-DD)')
    generate_parser.add_argument('--end-date', help='结束日期 (YYYY-MM-DD)')
    generate_parser.add_argument('--days-ago', type=int, help='过去N天的数据')
    generate_parser.add_argument('--import', dest='import_file', help='从DMP Agent输出的文件导入数据 (ex: output/DMP_temp_xxx.xlsx)')
    generate_parser.add_argument('--no-email', action='store_true', help='不发送邮件')
    generate_parser.add_argument('--no-feishu', action='store_true', help='不上传到飞书')
    generate_parser.add_argument('--self-email', action='store_true', help='发送邮件到自己（测试用）')
    generate_parser.add_argument('--limit', type=int, help='限制API拉取的转化数量，达到此数量后停止收取数据')
    generate_parser.add_argument('--no-monitoring', action='store_true', help='禁用性能監控')
    
    # 测试模式
    test_parser = subparsers.add_parser('test', help='测试数据库连接')
    
    # 性能測試模式
    perf_parser = subparsers.add_parser('performance', help='性能基準測試')
    perf_parser.add_argument('--partner', default='ALL', help='Partner名称')
    perf_parser.add_argument('--records', type=int, default=1000, help='測試記錄數量')
    
    args = parser.parse_args()
    
    if args.command == 'api':
        # API服务器模式
        run_api_server(args.host, args.port)
        
    elif args.command == 'generate':
        # 命令行生成模式
        asyncio.run(generate_report_cli(
            partner_name=args.partner,
            start_date=args.start_date,
            end_date=args.end_date,
            days_ago=args.days_ago,
            send_email=not args.no_email,
            upload_feishu=not args.no_feishu,
            self_email=args.self_email,
            limit=args.limit,
            enable_monitoring=not args.no_monitoring,
            import_file=args.import_file
        ))
        
    elif args.command == 'test':
        # 测试模式
        asyncio.run(test_database())
        
    elif args.command == 'performance':
        # 性能基準測試
        asyncio.run(performance_benchmark(args.partner, args.records))
        
    else:
        # 默认显示帮助
        parser.print_help()

async def performance_benchmark(partner_name: str = "ALL", test_records: int = 1000):
    """性能基準測試"""
    logger.info("🚀 開始性能基準測試")
    logger.info(f"   📊 測試Partner: {partner_name}")
    logger.info(f"   🔢 測試記錄數: {test_records}")
    
    monitor = PerformanceMonitor()
    
    try:
        # 測試數據庫查詢性能
        monitor.start_timer("數據庫查詢測試")
        
        db = PostbackDatabase()
        await db.init_pool()
        
        # 執行查詢測試
        df = await db.get_conversion_dataframe(
            partner_name=partner_name,
            limit=test_records
        )
        
        query_time = monitor.end_timer("數據庫查詢測試")
        
        # 計算性能指標
        records_processed = len(df)
        records_per_second = records_processed / query_time if query_time > 0 else 0
        
        logger.info("📊 性能基準測試結果:")
        logger.info(f"   📦 實際處理記錄數: {records_processed:,}")
        logger.info(f"   🕐 查詢時間: {query_time:.2f}秒")
        logger.info(f"   ⚡ 處理速度: {records_per_second:.2f} 記錄/秒")
        
        # 評估性能等級
        if records_per_second > 500:
            performance_grade = "優秀 🏆"
        elif records_per_second > 200:
            performance_grade = "良好 ✅"
        elif records_per_second > 100:
            performance_grade = "中等 ⚠️"
        else:
            performance_grade = "需要優化 ❌"
        
        logger.info(f"   🎯 性能等級: {performance_grade}")
        
        # 保存基準測試結果
        benchmark_file = f"output/benchmark_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs("output", exist_ok=True)
        
        benchmark_data = {
            'timestamp': datetime.now().isoformat(),
            'partner': partner_name,
            'requested_records': test_records,
            'actual_records': records_processed,
            'query_time': query_time,
            'records_per_second': records_per_second,
            'performance_grade': performance_grade,
            'metrics': monitor.get_metrics()
        }
        
        with open(benchmark_file, 'w', encoding='utf-8') as f:
            json.dump(benchmark_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📄 基準測試報告已保存: {benchmark_file}")
        
        await db.close_pool()
        
    except Exception as e:
        logger.error(f"❌ 性能基準測試失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return

if __name__ == "__main__":
    main() 