#!/usr/bin/env python3
"""
Data Input Agent - 电商转化数据导入和处理主程序
支持Excel文件导入、数据分析、Cloud SQL存储和passthrough模式
"""

import sys
import os
import argparse
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import config
from agents.data_input_agent.data_importer import DataImporter
from agents.data_input_agent.data_analyzer import DataAnalyzer


class DataInputAgent:
    """Data Input Agent主程序"""
    
    def __init__(self):
        self.logger = self._setup_logger()
        self.data_importer = DataImporter()
        self.data_analyzer = DataAnalyzer()
        self.stats = {
            'files_processed': 0,
            'records_imported': 0,
            'records_analyzed': 0,
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
        console_formatter = logging.Formatter('📊 %(asctime)s | %(levelname)s | %(message)s')
        console_handler.setFormatter(console_formatter)
        
        # 强制刷新输出
        sys.stdout.reconfigure(line_buffering=True)
        sys.stderr.reconfigure(line_buffering=True)
        
        # 创建文件处理器
        file_handler = logging.FileHandler('data_input_agent.log')
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
        file_handler.setFormatter(file_formatter)
        
        # 设置根日志记录器
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)
        
        # 创建专用记录器
        logger = logging.getLogger("DataInputAgent")
        logger.setLevel(logging.INFO)
        logger.propagate = True
        
        # 添加自定义处理器来强制刷新
        class FlushHandler(logging.StreamHandler):
            def emit(self, record):
                super().emit(record)
                sys.stdout.flush()
                sys.stderr.flush()
        
        # 替换控制台处理器
        for handler in logger.handlers[:]:
            if isinstance(handler, logging.StreamHandler):
                logger.removeHandler(handler)
        
        flush_handler = FlushHandler(sys.stdout)
        flush_handler.setLevel(logging.INFO)
        flush_handler.setFormatter(console_formatter)
        logger.addHandler(flush_handler)
        
        return logger
    
    def list_available_files(self) -> List[str]:
        """列出可用的输入文件"""
        input_dir = Path(config.INPUT_DATA_DIR)
        if not input_dir.exists():
            self.logger.warning(f"输入目录不存在: {input_dir}")
            return []
        
        excel_files = []
        for ext in ['*.xlsx', '*.xls', '*.csv']:
            excel_files.extend(input_dir.glob(ext))
        
        return [f.name for f in excel_files]
    
    def get_files_from_folder(self, folder_path: str) -> List[str]:
        """从指定文件夹获取所有Excel/CSV文件"""
        folder = Path(folder_path)
        if not folder.exists():
            self.logger.error(f"文件夹不存在: {folder_path}")
            return []
        
        if not folder.is_dir():
            self.logger.error(f"路径不是文件夹: {folder_path}")
            return []
        
        excel_files = []
        for ext in ['*.xlsx', '*.xls', '*.csv']:
            excel_files.extend(folder.glob(ext))
        
        # 按文件名排序
        excel_files.sort(key=lambda x: x.name)
        
        file_list = [str(f) for f in excel_files]
        self.logger.info(f"📁 从文件夹 {folder_path} 找到 {len(file_list)} 个文件")
        for file in file_list:
            self.logger.info(f"   - {Path(file).name}")
        
        return file_list
    
    async def process_file(self, filename: str, passthrough: bool = False, 
                          analyze_only: bool = False, enable_dmp_forward: bool = False,
                          reporter_agent: bool = False, days_ago: int = 1,
                          partner: str = None, partner_list: list = None, self_email: bool = False,
                          start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """处理单个文件"""
        self.logger.info(f"🔄 开始处理文件: {filename}")
        
        result = {
            'filename': filename,
            'success': False,
            'output_path': None,
            'analysis': None,
            'records_count': 0,
            'passthrough_mode': passthrough,
            'analyze_only': analyze_only
        }
        
        try:
            # 步骤1: 数据分析
            if not analyze_only:
                # Removed analysis logging to reduce output noise
                analysis_result = await self._analyze_file(filename)
                result['analysis'] = analysis_result
                self.stats['records_analyzed'] += analysis_result.get('record_count', 0)
            
            # 步骤2: 数据导入处理
            if not analyze_only:
                self.logger.info("📥 执行数据导入...")
                output_path = self.data_importer.import_data(filename, passthrough)
                result['output_path'] = output_path
                result['success'] = True
                self.stats['records_imported'] += self._count_records_in_file(output_path)
            else:
                # 仅分析模式
                analysis_result = await self._analyze_file(filename)
                result['analysis'] = analysis_result
                result['success'] = True
                self.stats['records_analyzed'] += analysis_result.get('record_count', 0)
            
            # 步骤3: Agent间调用 (如果启用)
            if enable_dmp_forward and not analyze_only:
                if passthrough:
                    self.logger.info("🔗 转发数据到DMP Agent (Passthrough模式: 不插入Cloud SQL，产生temp excel)...")
                else:
                    self.logger.info("🔗 转发数据到DMP Agent (标准模式: 插入Cloud SQL)...")
                dmp_result = await self._forward_to_dmp_agent(result['output_path'], filename, days_ago, partner, partner_list, passthrough, self_email, start_date, end_date)
                result['dmp_forward'] = dmp_result
            
            if reporter_agent and not analyze_only:
                self.logger.info("📊 转发数据到Reporter Agent...")
                reporter_result = await self._forward_to_reporter_agent(result, days_ago, partner, partner_list, self_email, start_date, end_date)
                result['reporter_forward'] = reporter_result
            
            self.stats['files_processed'] += 1
            self.logger.info(f"✅ 文件处理完成: {filename}")
            
        except Exception as e:
            error_msg = f"文件处理失败: {filename} - {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            self.stats['errors'].append(error_msg)
            result['error'] = str(e)
        
        return result
    
    async def _analyze_file(self, filename: str) -> Dict[str, Any]:
        """分析文件数据"""
        try:
            import pandas as pd
            
            # 检查是否是完整路径
            if Path(filename).is_absolute() or '/' in filename or '\\' in filename:
                input_path = Path(filename)
            else:
                input_path = Path(config.INPUT_DATA_DIR) / filename
            
            # 读取文件
            if filename.endswith('.csv'):
                df = pd.read_csv(input_path)
            else:
                df = pd.read_excel(input_path)
            
            # 执行分析
            analysis = self.data_analyzer.analyze_dataframe(df, filename)
            
            return {
                'record_count': len(df),
                'column_count': len(df.columns),
                'analysis_details': analysis,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"文件分析失败: {e}")
            return {'error': str(e)}
    
    def _count_records_in_file(self, filepath: str) -> int:
        """计算文件中的记录数"""
        try:
            import pandas as pd
            if filepath.endswith('.csv'):
                df = pd.read_csv(filepath)
            else:
                df = pd.read_excel(filepath)
            return len(df)
        except:
            return 0
    
    async def _forward_to_dmp_agent(self, output_path: str, filename: str, days_ago: int = 1, partner: str = None, partner_list: list = None, passthrough: bool = False, self_email: bool = False, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """转发数据到DMP Agent"""
        try:
            if not config.ENABLE_AGENT_INTER_CALLING:
                self.logger.warning("🔗 Agent间调用功能已禁用，跳过DMP Agent转发")
                return {
                    'success': True,
                    'message': 'Agent间调用功能已禁用',
                    'dmp_forward': None
                }
            
            from shared.utils.agent_caller import call_dmp_agent
            
            # 🔍 检测数据中的Partner信息
            detected_platform = self._detect_platform_from_data(output_path)
            if detected_platform:
                self.logger.info(f"🎯 检测到数据中的Partner: {detected_platform}")
                platform_to_use = detected_platform
            else:
                self.logger.info("⚠️ 无法检测到Partner，使用默认平台")
                platform_to_use = "IAByteC"  # 默认平台
            
            # 🔍 打印DMP Agent调用信息
            self.logger.info("=" * 60)
            self.logger.info("🔗 准备调用DMP Agent")
            self.logger.info("=" * 60)
            self.logger.info(f"📊 数据源: Data Input Agent")
            self.logger.info(f"📄 原始输入文件: {filename}")
            self.logger.info(f"📁 处理后输出文件: {output_path}")
            self.logger.info(f"📅 日期範圍: {start_date} to {end_date} (days_ago: {days_ago})")
            self.logger.info(f"⚙️ 调用参数:")
            self.logger.info(f"   - import_file: {filename}")
            self.logger.info(f"   - days_ago: {days_ago}")
            self.logger.info(f"   - start_date: {start_date}")
            self.logger.info(f"   - end_date: {end_date}")
            self.logger.info(f"   - data_source: file (由Data Input Agent调用)")
            
            if passthrough:
                self.logger.info("🔄 DMP Agent模式: Passthrough (不插入Cloud SQL，产生temp excel)")
            else:
                self.logger.info("💾 DMP Agent模式: 标准模式 (插入Cloud SQL)")
            
            self.logger.info("=" * 60)
            self.logger.info(f"🔗 调用DMP Agent: platform={platform_to_use}, days_ago={days_ago}, passthrough={passthrough}")
            
            # 构建额外参数
            additional_args = []
            
            # 🎯 優先添加原始輸入文件路徑，讓agent_caller能檢測到並使用--import模式
            additional_args.append(filename)
            
            # 🔧 检测LeadsADN文件并强制指定平台
            filename_lower = str(filename).lower()
            if 'leads_adn' in filename_lower or 'leadsamdn' in filename_lower:
                additional_args.extend(['--force-platform', 'leads_adn'])
                self.logger.info(f"🎯 检测到LeadsADN文件，强制指定平台为leads_adn")
            
            if start_date and end_date:
                additional_args.extend(['--start-date', start_date, '--end-date', end_date])
            if partner:
                additional_args.extend(['--partner', partner])
            if self_email:
                additional_args.append('--self-email')
            
            # 🔧 修复: 显式指定使用file数据源（从Data Input Agent调用）
            additional_args.extend(['--data-source', 'file'])
            
            # 调用DMP Agent处理数据（传递检测到的platform）
            result = await call_dmp_agent(
                platform=platform_to_use,  # 使用检测到的platform而不是None
                days_ago=days_ago,
                passthrough=passthrough,  # 传递passthrough参数给DMP Agent
                additional_args=additional_args if additional_args else None
            )
            
            if result.get('success'):
                self.logger.info("✅ DMP Agent执行成功")
                
                # 🔍 顯示DMP Agent輸出文件信息
                if result.get('output_file_path'):
                    self.logger.info("📁 DMP Agent輸出文件:")
                    self.logger.info(f"   - 📄 文件路徑: {result['output_file_path']}")
                    self.logger.info(f"   - 🎯 用途: 後續Reporter Agent --import參數")
                elif result.get('passthrough_mode'):
                    self.logger.info("⚠️ Passthrough模式但未生成輸出文件")
            else:
                self.logger.error(f"❌ DMP Agent调用失败: {result.get('error', 'Unknown error')}")
            
            return {
                'success': result.get('success', False),
                'message': 'DMP Agent调用完成',
                'dmp_result': result,
                'output_path': output_path,
                'start_date': start_date,
                'end_date': end_date
            }
        except Exception as e:
            error_msg = f"DMP Agent调用异常: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            return {'success': False, 'error': error_msg}
    
    def _detect_platform_from_data(self, file_path: str) -> str:
        """从数据文件中检测Partner/Platform信息"""
        try:
            import pandas as pd
            
            # 检查文件名是否包含LeadsADN标识
            filename = str(file_path).lower()
            if 'leads_adn' in filename or 'leadsamdn' in filename:
                return 'FTK'  # LeadsADN文件通常对应FTK Partner
            
            # 读取Excel文件
            df = pd.read_excel(file_path)
            
            # 检查是否有Publisher Sub ID 1列
            if 'Publisher Sub ID 1' in df.columns:
                # 获取所有非空的Source值
                sources = df['Publisher Sub ID 1'].dropna().unique()
                
                # 检测Partner
                for source in sources:
                    source_str = str(source).strip()
                    
                    # 检查是否匹配FTK
                    if source_str.upper().startswith('FTK') or '(3)FTK' in source_str:
                        return 'FTK'
                    # 检查是否匹配RAMPUP
                    elif source_str.upper().startswith('RAMPUP'):
                        return 'RAMPUP'
                    # 检查是否匹配DeepLeaper相关
                    elif any(source_str.upper().startswith(prefix) for prefix in ['OPPO', 'VIVO', 'OEM1', 'OEM2', 'OEM3', 'XIAOMI']):
                        return 'DeepLeaper'
                    # 检查是否匹配MKK
                    elif source_str.upper().startswith('MKK'):
                        return 'MKK'
                    # 检查是否匹配MP
                    elif source_str.upper() == 'MP':
                        return 'MP'
                    # 检查是否匹配TestPartner
                    elif source_str.upper().startswith('TESTPARTNER'):
                        return 'TestPartner'
            
            # 检查是否有原始LeadsADN字段（Affiliate字段）
            if 'Affiliate' in df.columns:
                affiliates = df['Affiliate'].dropna().unique()
                for affiliate in affiliates:
                    affiliate_str = str(affiliate).strip()
                    if '(3)FTK' in affiliate_str or 'FTK' in affiliate_str.upper():
                        return 'FTK'
            
            # 如果没有检测到特定Partner，返回默认值
            return 'IAByteC'
            
        except Exception as e:
            self.logger.warning(f"⚠️ 检测Partner失败: {e}")
            return 'IAByteC'  # 默认返回IAByteC
    
    async def _forward_to_reporter_agent(self, process_result: Dict[str, Any], days_ago: int = 1, partner: str = None, partner_list: list = None, self_email: bool = False, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """转发数据到Reporter Agent"""
        try:
            if not config.ENABLE_REPORTER_AGENT_CALLING:
                self.logger.warning("📊 Reporter Agent调用功能已禁用，跳过报告生成")
                return {
                    'success': True,
                    'message': 'Reporter Agent调用功能已禁用',
                    'process_result': process_result
                }
            
            from shared.utils.agent_caller import call_reporter_agent
            
            # 優先使用傳入的 start_date 和 end_date 參數
            if start_date is None or end_date is None:
                # 從 DMP Agent 結果中獲取日期範圍
                process_result_start_date = process_result.get('start_date')
                process_result_end_date = process_result.get('end_date')
                
                # 如果沒有從 DMP Agent 獲取到日期，則重新計算
                if not process_result_start_date or not process_result_end_date:
                    target_date = datetime.now() - timedelta(days=days_ago)
                    start_date = target_date.strftime("%Y-%m-%d")
                    end_date = target_date.strftime("%Y-%m-%d")
                else:
                    # 使用 DMP Agent 返回的日期
                    start_date = process_result_start_date
                    end_date = process_result_end_date
            else:
                # 確保使用傳入的日期，不重新計算
                start_date = start_date
                end_date = end_date
            
            # 🔍 打印Reporter Agent调用信息
            self.logger.info("=" * 60)
            self.logger.info("📊 准备调用Reporter Agent")
            self.logger.info("=" * 60)
            self.logger.info(f"📊 数据源: Data Input Agent → DMP Agent → Reporter Agent")
            self.logger.info(f"📅 日期範圍: {start_date} to {end_date} (days_ago: {days_ago})")
            self.logger.info(f"🔄 DMP Agent处理结果:")
            if process_result.get('dmp_forward'):
                dmp_result = process_result['dmp_forward']
                self.logger.info(f"   - DMP Agent成功: {dmp_result.get('success', False)}")
                if dmp_result.get('success'):
                    self.logger.info("   - DMP Agent已完成数据处理")
                else:
                    self.logger.info(f"   - DMP Agent错误: {dmp_result.get('error', 'Unknown')}")
            else:
                self.logger.info("   - 未启用DMP Agent转发")
            
            self.logger.info(f"⚙️ Reporter Agent参数:")
            self.logger.info(f"   - platform/partner: {partner or 'IAByteC'}")
            self.logger.info(f"   - days_ago: {days_ago}")
            self.logger.info(f"   - self_email: {self_email}")
            self.logger.info(f"   - output_format: json")
            
            # 🗺️ Partner與Source映射關係重點列印
            try:
                import sys
                import os
                sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                from config import PARTNER_SOURCES_MAPPING, get_pattern_for_partner, get_sources_for_partner
                
                # 修正：partner可能是ALL，需要特別处理
                if partner == 'ALL':
                    self.logger.info("")
                    self.logger.info("🗺️ 報告範圍: ALL Partners (所有合作夥伴)")
                    self.logger.info("   📊 數據來源: Data Input Agent處理的文件數據")
                    self.logger.info("   🎯 報告產生: Reporter Agent將生成所有Partner的匯總報告")
                    
                    self.logger.info("")
                    self.logger.info("🗺️ 系統中的Partner映射關係總覽:")
                    for partner_name, partner_config in PARTNER_SOURCES_MAPPING.items():
                        sources = partner_config.get('sources', [])
                        if sources != ["ALL"]:
                            source_display = ', '.join(sources)
                            self.logger.info(f"   📋 Partner '{partner_name}' ← Sources: {source_display}")
                        else:
                            self.logger.info(f"   📋 Partner '{partner_name}' ← Sources: ALL (所有數據)")
                else:
                    # 處理特定Partner
                    target_partner = partner
                    self.logger.info("")
                    self.logger.info(f"🗺️ Partner '{target_partner}' 映射關係:")
                    
                    partner_config = PARTNER_SOURCES_MAPPING.get(target_partner, {})
                    pattern = get_pattern_for_partner(target_partner)
                    sources = get_sources_for_partner(target_partner)
                    
                    if target_partner in PARTNER_SOURCES_MAPPING:
                        self.logger.info(f"   📋 目標Partner: {target_partner}")
                        
                        # 🔍 重點映射關係：Source 對應 Partner
                        if sources and sources != ["ALL"]:
                            self.logger.info(f"   🎯 Source → Partner 映射關係:")
                            for source in sources:
                                self.logger.info(f"      📊 Source '{source}' → Partner '{target_partner}'")
                            self.logger.info(f"   📊 Source數量: {len(sources)} 個")
                            
                            if pattern:
                                # 顯示正則表達式匹配模式
                                self.logger.info(f"   🔍 Pattern匹配規則: {pattern}")
                                self.logger.info(f"      ↳ SQL條件: aff_sub REGEXP '{pattern}'")
                            else:
                                # 顯示精確匹配
                                source_list = ', '.join([f"'{s}'" for s in sources])
                                self.logger.info(f"   📝 精確匹配: aff_sub IN ({source_list})")
                        else:
                            self.logger.info(f"   🌐 數據範圍: 所有Source → Partner '{target_partner}' (ALL)")
                            self.logger.info(f"   🔍 匹配規則: 處理全部轉化數據")
                        
                        self.logger.info(f"   📧 Email通知: {'啟用' if partner_config.get('email_enabled', False) else '關閉'}")
                        
                        # 顯示實際要產生的報告範圍
                        if pattern or (sources and sources != ["ALL"]):
                            self.logger.info(f"   📋 報告產生範圍: 篩選後的{target_partner}數據")
                        else:
                            self.logger.info(f"   📋 報告產生範圍: 全部轉化數據")
                    else:
                        self.logger.warning(f"   ⚠️ Partner '{target_partner}' 不在系統配置中")
                        self.logger.info(f"   🔍 將使用默認處理邏輯")
                    
            except ImportError as e:
                self.logger.warning(f"⚠️ 無法獲取Partner映射信息: {e}")
            
            self.logger.info("=" * 60)
            
            # 构建额外参数
            additional_args = []
            # 只在不是默认值时添加self-email参数
            if self_email:
                additional_args.append('--self-email')
            # 添加日期參數
            additional_args.extend(['--start-date', start_date, '--end-date', end_date])
            
            # 🔍 获取DMP Agent输出文件路径用于Reporter Agent --import参数
            import_file_path = None
            if process_result.get('dmp_forward') and process_result['dmp_forward'].get('dmp_result'):
                import_file_path = process_result['dmp_forward']['dmp_result'].get('output_file_path')
            
            # 🔍 打印Reporter Agent即将使用的输入文件信息
            if import_file_path:
                self.logger.info("")
                self.logger.info("📄 Reporter Agent輸入文件信息:")
                self.logger.info(f"   - 📂 導入文件: {import_file_path}")
                self.logger.info(f"   - 📊 數據來源: DMP Agent輸出")
                self.logger.info(f"   - 📅 日期範圍: {start_date} to {end_date}")
                self.logger.info("=" * 60)
            
            # 调用Reporter Agent生成报告
            result = await call_reporter_agent(
                platform=partner,  # 直接传递partner，让agent_caller处理默认值
                days_ago=days_ago,
                output_format='json',
                import_file=import_file_path,  # 传递DMP Agent的输出文件
                additional_args=additional_args if additional_args else None
            )
            
            if result.get('success'):
                self.logger.info("✅ Reporter Agent调用成功")
            else:
                self.logger.error(f"❌ Reporter Agent调用失败: {result.get('error', 'Unknown error')}")
            
            return {
                'success': result.get('success', False),
                'message': 'Reporter Agent调用完成',
                'reporter_result': result,
                'process_result': process_result
            }
        except Exception as e:
            error_msg = f"Reporter Agent调用异常: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            return {'success': False, 'error': error_msg}
    
    async def batch_process(self, filenames: List[str], **kwargs) -> List[Dict[str, Any]]:
        """批量处理多个文件"""
        self.logger.info(f"🚀 开始批量处理 {len(filenames)} 个文件")
        
        results = []
        for filename in filenames:
            result = await self.process_file(filename, **kwargs)
            results.append(result)
        
        return results
    
    def print_statistics(self):
        """打印处理统计信息"""
        self.logger.info("=" * 60)
        self.logger.info("📊 Data Input Agent 处理统计")
        self.logger.info("=" * 60)
        self.logger.info(f"✅ 文件处理数量: {self.stats['files_processed']}")
        self.logger.info(f"📥 记录导入数量: {self.stats['records_imported']}")
        # Removed analysis logging to reduce output noise
        
        if self.stats['errors']:
            self.logger.info(f"❌ 错误数量: {len(self.stats['errors'])}")
            for error in self.stats['errors']:
                self.logger.info(f"   - {error}")
        else:
            self.logger.info("✅ 无处理错误")
        
        self.logger.info("=" * 60)


async def main():
    """主程序入口"""
    parser = argparse.ArgumentParser(
        description='Data Input Agent - 电商转化数据导入和处理',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 导入单个文件到Cloud SQL
  python agents/data_input_agent/main.py --import sample_data.xlsx
  
  # 仅分析模式（不导入）
  python agents/data_input_agent/main.py --import sample_data.xlsx --analyze-only
  
  # Passthrough模式（不插入Cloud SQL）
  python agents/data_input_agent/main.py --import sample_data.xlsx --passthrough
  
  # 启用DMP Agent转发（标准模式：插入Cloud SQL）
  python agents/data_input_agent/main.py --import sample_data.xlsx --dmp-forward
  
  # DMP Agent转发 + Passthrough模式（不插入Cloud SQL，产生temp excel）
  python agents/data_input_agent/main.py --import sample_data.xlsx --dmp-forward --passthrough
  
  # 启用Reporter Agent转发
  python agents/data_input_agent/main.py --import sample_data.xlsx --reporter-agent
  
  # 完整流水线：Input → DMP(Passthrough) → Reporter
  python agents/data_input_agent/main.py --import sample_data.xlsx --dmp-forward --reporter-agent --passthrough --days-ago 2 --partner ALL --self-email
  
  # 多Partners处理：DeepLeaper和RAMPUP
  python agents/data_input_agent/main.py --import sample_data.xlsx --dmp-forward --reporter-agent --passthrough --days-ago 2 --partner DeepLeaper,RAMPUP --self-email
  
  # 批量处理多个文件
  python agents/data_input_agent/main.py --batch-import data1.xlsx,data2.xlsx --passthrough
  
  # 处理文件夹中的所有文件
  python agents/data_input_agent/main.py --import-folder input --dmp-forward --passthrough
  
  # 列出可用文件
  python agents/data_input_agent/main.py --list-files
        """
    )
    
    # 文件处理参数
    parser.add_argument('--import', dest='import_file', type=str,
                       help='要导入的Excel/CSV文件名')
    parser.add_argument('--batch-import', dest='batch_files', type=str,
                       help='批量导入文件（逗号分隔）')
    parser.add_argument('--import-folder', dest='import_folder', type=str,
                       help='导入指定文件夹下的所有Excel/CSV文件')
    
    # 模式控制参数 (Phase 2: Additive Only)
    parser.add_argument('--passthrough', action='store_true',
                       help='Passthrough模式: 不插入Cloud SQL，仅处理和输出文件')
    parser.add_argument('--analyze-only', action='store_true',
                       help='仅分析模式: 只分析数据，不进行导入')
    
    # Agent间调用参数 (Phase 2: Additive Only)
    parser.add_argument('--dmp-forward', action='store_true',
                       help='转发处理结果到DMP Agent')
    parser.add_argument('--reporter-agent', action='store_true',
                       help='转发处理结果到Reporter Agent')
    
    # Agent间调用的传递参数
    parser.add_argument('--days-ago', type=int, default=1,
                       help='传递给DMP Agent和Reporter Agent的天数参数 (默认: 1)')
    parser.add_argument('--partner', type=str,
                       help='传递给DMP Agent和Reporter Agent的partner参数 (支持逗号分隔多个partners，例如: DeepLeaper,RAMPUP)')
    parser.add_argument('--self-email', action='store_true',
                       help='传递给Reporter Agent的自发邮件参数')
    parser.add_argument('--start-date', type=str,
                       help='开始日期 (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str,
                       help='结束日期 (YYYY-MM-DD)')
    
    # 功能参数
    parser.add_argument('--list-files', action='store_true',
                       help='列出可用的输入文件')
    parser.add_argument('--stats-only', action='store_true',
                       help='仅显示统计信息')
    
    # 高级参数
    parser.add_argument('--output-format', choices=['excel', 'csv'], default='excel',
                       help='输出文件格式 (默认: excel)')
    parser.add_argument('--enable-mockup', action='store_true',
                       help='启用数据模拟扩展')
    
    args = parser.parse_args()
    
    # 参数验证
    if not any([args.import_file, args.batch_files, args.import_folder, args.list_files, args.stats_only]):
        parser.error("必须指定一个操作: --import, --batch-import, --import-folder, --list-files, 或 --stats-only")
    
    # 创建Data Input Agent实例
    agent = DataInputAgent()
    
    try:
        # 处理不同的命令
        if args.list_files:
            files = agent.list_available_files()
            agent.logger.info(f"📁 可用输入文件 ({len(files)} 个):")
            for file in files:
                agent.logger.info(f"   - {file}")
            return

        if args.stats_only:
            agent.print_statistics()
            return
        
        # 处理多partners参数
        partner_list = []
        if args.partner:
            partner_list = [p.strip() for p in args.partner.split(',') if p.strip()]
            agent.logger.info(f"🎯 处理多个Partners: {', '.join(partner_list)}")
        
        # 处理参数组合验证 - 默认启用 dmp-forward 和 passthrough
        process_kwargs = {
            'passthrough': True,  # 默认启用 passthrough
            'analyze_only': args.analyze_only,
            'enable_dmp_forward': True,  # 默认启用 dmp-forward
            'reporter_agent': args.reporter_agent,
            'days_ago': args.days_ago,
            'partner': args.partner,  # 保持原始字符串格式传递给其他agent
            'partner_list': partner_list,  # 添加解析后的partner列表
            'self_email': args.self_email,
            'start_date': args.start_date,
            'end_date': args.end_date
        }
        
        # 风险控制检查
        if args.passthrough:
            agent.logger.info("🔄 启用Passthrough模式 - 数据不会插入Cloud SQL")
        
        if args.analyze_only:
            pass  # Removed analysis logging to reduce output noise
        
        # 主要处理流程
        if args.import_file:
            # 单文件处理
            agent.logger.info("🚀 开始Data Input Agent单文件处理")
            result = await agent.process_file(args.import_file, **process_kwargs)
            
            if result['success']:
                agent.logger.info(f"✅ 文件处理成功: {args.import_file}")
                if result.get('output_path'):
                    agent.logger.info(f"📄 输出文件: {result['output_path']}")
            else:
                agent.logger.error(f"❌ 文件处理失败: {args.import_file}")
                if result.get('error'):
                    agent.logger.error(f"   错误: {result['error']}")
        
        elif args.batch_files:
            # 批量文件处理
            filenames = [f.strip() for f in args.batch_files.split(',')]
            agent.logger.info(f"🚀 开始Data Input Agent批量处理 ({len(filenames)} 个文件)")
            
            results = await agent.batch_process(filenames, **process_kwargs)
            
            # 统计结果
            success_count = sum(1 for r in results if r['success'])
            agent.logger.info(f"✅ 批量处理完成: {success_count}/{len(filenames)} 成功")
        
        elif args.import_folder:
            # 文件夹处理
            agent.logger.info(f"📁 开始处理文件夹: {args.import_folder}")
            
            # 获取文件夹中的所有文件
            file_list = agent.get_files_from_folder(args.import_folder)
            
            if not file_list:
                agent.logger.error(f"❌ 文件夹 {args.import_folder} 中没有找到可处理的文件")
                return
            
            # 将文件列表转换为 --import 参数格式
            import_files = ','.join([Path(f).name for f in file_list])
            agent.logger.info(f"🔄 转换为批量导入参数: --import {import_files}")
            
            # 使用批量处理逻辑 - 注意：file_list 已经是完整路径，不需要再加 input/ 前缀
            results = await agent.batch_process(file_list, **process_kwargs)
            
            # 统计结果
            success_count = sum(1 for r in results if r['success'])
            agent.logger.info(f"✅ 文件夹处理完成: {success_count}/{len(file_list)} 成功")
        
        # 显示最终统计
        agent.print_statistics()
        
    except Exception as e:
        agent.logger.error(f"❌ Data Input Agent 执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 