#!/usr/bin/env python3
"""
Reporter-Agent CLI测试工具
支持测试完整的数据流程：Data-DMP-Agent → Data-Output-Agent
"""

import asyncio
import argparse
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入必要的模块
from config import (
    EMAIL_AUTO_CC, 
    PARTNER_SOURCES_MAPPING,
    get_default_date_range,
    get_partner_email_config
)
from agents.data_dmp_agent.commission_calculator import CommissionCalculator
from agents.data_output_agent.output_processor import OutputProcessor
from agents.reporter_agent.report_generator import ReportGenerator


class ReporterAgentCLI:
    """Reporter-Agent命令行测试工具"""
    
    def __init__(self):
        self.commission_calculator = CommissionCalculator()
        self.output_processor = OutputProcessor()
        self.report_generator = ReportGenerator()
        
    def parse_arguments(self):
        """解析命令行参数"""
        parser = argparse.ArgumentParser(
            description='Reporter-Agent CLI测试工具',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog='''
使用示例:
  python scripts/test_reporter_agent_cli.py --partner ByteC --date-range "2 days ago" --self-email
  python scripts/test_reporter_agent_cli.py --partner DeepLeaper --date-range "2025-01-20,2025-01-21"
  python scripts/test_reporter_agent_cli.py --partner all --date-range "1 week ago"
  python scripts/test_reporter_agent_cli.py --partner RAMPUP --self-email
            '''
        )
        
        parser.add_argument(
            '--partner', 
            type=str, 
            default='all',
            help='Partner名称 (ByteC, DeepLeaper, RAMPUP, all)'
        )
        
        parser.add_argument(
            '--date-range',
            type=str,
            default='2 days ago',
            help='日期范围 ("2 days ago", "1 week ago", "2025-01-20,2025-01-21")'
        )
        
        parser.add_argument(
            '--self-email',
            action='store_true',
            help='发送报告到自己的邮箱 (AmosFang927@gmail.com)'
        )
        
        parser.add_argument(
            '--format',
            type=str,
            default='all',
            choices=['json', 'excel', 'feishu', 'email', 'all'],
            help='输出格式 (json, excel, feishu, email, all)'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='仅测试不实际发送/上传'
        )
        
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='详细输出'
        )
        
        return parser.parse_args()
    
    def parse_date_range(self, date_range_str):
        """解析日期范围"""
        try:
            # 处理相对日期
            if 'ago' in date_range_str.lower():
                if 'days ago' in date_range_str:
                    days = int(date_range_str.split()[0])
                    end_date = datetime.now() - timedelta(days=days)
                    start_date = end_date
                elif 'week ago' in date_range_str:
                    weeks = int(date_range_str.split()[0])
                    end_date = datetime.now() - timedelta(weeks=weeks)
                    start_date = end_date - timedelta(days=6)  # 一周的数据
                else:
                    # 默认2天前
                    end_date = datetime.now() - timedelta(days=2)
                    start_date = end_date
            
            # 处理绝对日期范围
            elif ',' in date_range_str:
                start_str, end_str = date_range_str.split(',')
                start_date = datetime.strptime(start_str.strip(), '%Y-%m-%d')
                end_date = datetime.strptime(end_str.strip(), '%Y-%m-%d')
            
            # 处理单个日期
            else:
                try:
                    start_date = datetime.strptime(date_range_str, '%Y-%m-%d')
                    end_date = start_date
                except ValueError:
                    # 如果解析失败，使用默认日期范围
                    start_str, end_str = get_default_date_range()
                    start_date = datetime.strptime(start_str, '%Y-%m-%d')
                    end_date = datetime.strptime(end_str, '%Y-%m-%d')
            
            return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')
            
        except Exception as e:
            print(f"❌ 日期解析失败: {e}")
            print("使用默认日期范围...")
            start_str, end_str = get_default_date_range()
            return start_str, end_str
    
    def get_partners_to_process(self, partner_arg):
        """获取要处理的Partner列表"""
        if partner_arg.lower() == 'all':
            return list(PARTNER_SOURCES_MAPPING.keys())
        elif partner_arg in PARTNER_SOURCES_MAPPING:
            return [partner_arg]
        else:
            print(f"❌ 错误: 未知的Partner '{partner_arg}'")
            print(f"可用的Partner: {list(PARTNER_SOURCES_MAPPING.keys())}")
            return []
    
    def get_email_recipients(self, partner_name, self_email=False):
        """获取邮件收件人列表"""
        recipients = []
        
        if self_email:
            # 发送给自己
            recipients.append(EMAIL_AUTO_CC)
        else:
            # 发送给Partner的默认收件人
            partner_config = get_partner_email_config(partner_name)
            if partner_config['enabled']:
                recipients.extend(partner_config['recipients'])
        
        return recipients
    
    async def test_data_flow(self, partner_name, start_date, end_date, args):
        """测试完整数据流程"""
        print(f"\n🔄 开始测试 {partner_name} 数据流程...")
        print(f"   📅 日期范围: {start_date} 到 {end_date}")
        
        try:
            # 1. 从Data-DMP-Agent获取数据
            print(f"   📊 Step 1: 从Data-DMP-Agent获取数据...")
            
            # 这里应该调用实际的Data-DMP-Agent获取数据
            # 暂时使用模拟数据进行测试
            conversion_data = await self.get_conversion_data(partner_name, start_date, end_date)
            
            if not conversion_data:
                print(f"   ❌ 没有找到 {partner_name} 的转化数据")
                return False
            
            print(f"   ✅ 获取到 {len(conversion_data)} 条转化数据")
            
            # 2. 计算佣金
            print(f"   💰 Step 2: 计算佣金...")
            commission_data = []
            for record in conversion_data:
                commission_result = self.commission_calculator.calculate_commission(record)
                commission_data.append(commission_result)
            
            # 将partner_name添加到每条记录中
            for record in commission_data:
                record['partner_name'] = partner_name
            
            total_amount = sum(record.get('commission_amount', 0) for record in commission_data)
            print(f"   ✅ 佣金计算完成，总金额: ${total_amount:,.2f}")
            
            # 3. 处理输出
            print(f"   📤 Step 3: 处理输出...")
            
            output_results = {}
            
            # 根据format参数决定输出格式
            formats_to_process = ['json', 'excel', 'feishu', 'email'] if args.format == 'all' else [args.format]
            
            for format_type in formats_to_process:
                if format_type == 'json':
                    result = await self.output_processor.generate_json(
                        commission_data, partner_name, start_date, end_date
                    )
                    output_results['json'] = result
                    
                elif format_type == 'excel':
                    result = await self.output_processor.generate_excel(
                        commission_data, partner_name, start_date, end_date
                    )
                    output_results['excel'] = result
                    
                elif format_type == 'feishu':
                    if not args.dry_run:
                        result = await self.output_processor.upload_to_feishu(
                            commission_data, partner_name, start_date, end_date
                        )
                        output_results['feishu'] = result
                    else:
                        print(f"   🚫 Dry-run模式: 跳过飞书上传")
                        
                elif format_type == 'email':
                    recipients = self.get_email_recipients(partner_name, args.self_email)
                    if recipients and not args.dry_run:
                        result = await self.output_processor.send_email(
                            commission_data, partner_name, start_date, end_date, recipients
                        )
                        output_results['email'] = result
                    else:
                        if not recipients:
                            print(f"   ⚠️  没有配置邮件收件人")
                        else:
                            print(f"   🚫 Dry-run模式: 跳过邮件发送")
            
            # 4. 输出结果汇总
            print(f"\n   📋 输出结果汇总:")
            for format_type, result in output_results.items():
                if result and result.get('success'):
                    print(f"   ✅ {format_type.upper()}: {result.get('message', '成功')}")
                    if format_type == 'excel' and result.get('file_path'):
                        print(f"      📁 文件路径: {result['file_path']}")
                    elif format_type == 'feishu' and result.get('feishu_url'):
                        print(f"      🔗 飞书链接: {result['feishu_url']}")
                    elif format_type == 'email' and result.get('sent_to'):
                        print(f"      📧 发送给: {', '.join(result['sent_to'])}")
                else:
                    print(f"   ❌ {format_type.upper()}: {result.get('error', '失败') if result else '未处理'}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ 测试失败: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            return False
    
    async def get_conversion_data(self, partner_name, start_date, end_date):
        """从Data-DMP-Agent获取转化数据"""
        try:
            # 这里应该调用实际的Data-DMP-Agent
            # 目前使用模拟数据
            mock_data = [
                {
                    'transaction_id': f'TXN_{partner_name}_{i}',
                    'partner_name': partner_name,
                    'offer_name': 'Shopee ID (Media Buyers) - CPS',
                    'sale_amount': 100.0 + i * 10,
                    'currency': 'USD',
                    'conversion_date': start_date,
                    'status': 'confirmed'
                }
                for i in range(5)  # 模拟5条数据
            ]
            
            return mock_data
            
        except Exception as e:
            print(f"❌ 获取转化数据失败: {e}")
            return []
    
    async def run(self):
        """运行CLI测试"""
        print("🚀 Reporter-Agent CLI测试工具启动...")
        
        # 解析命令行参数
        args = self.parse_arguments()
        
        # 解析日期范围
        start_date, end_date = self.parse_date_range(args.date_range)
        
        # 获取要处理的Partner列表
        partners_to_process = self.get_partners_to_process(args.partner)
        
        if not partners_to_process:
            print("❌ 没有找到要处理的Partner")
            return
        
        print(f"📋 测试配置:")
        print(f"   🤝 Partners: {', '.join(partners_to_process)}")
        print(f"   📅 日期范围: {start_date} 到 {end_date}")
        print(f"   📧 自发邮件: {'是' if args.self_email else '否'}")
        print(f"   📄 输出格式: {args.format}")
        print(f"   🚫 Dry-run: {'是' if args.dry_run else '否'}")
        
        # 测试每个Partner
        success_count = 0
        total_count = len(partners_to_process)
        
        for partner_name in partners_to_process:
            success = await self.test_data_flow(partner_name, start_date, end_date, args)
            if success:
                success_count += 1
        
        # 输出最终结果
        print(f"\n{'='*50}")
        print(f"📊 测试结果汇总")
        print(f"{'='*50}")
        print(f"✅ 成功: {success_count}/{total_count}")
        print(f"❌ 失败: {total_count - success_count}/{total_count}")
        
        if success_count == total_count:
            print(f"🎉 所有测试通过！")
        else:
            print(f"⚠️  部分测试失败，请检查日志")


if __name__ == '__main__':
    cli = ReporterAgentCLI()
    asyncio.run(cli.run()) 