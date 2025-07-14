#!/usr/bin/env python3
"""
报表生成器
从数据库生成Excel报表，并发送到飞书和邮件
"""

import os
import sys
import asyncio
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from pathlib import Path
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

# 导入ByteC-Network-Agent的现有模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from modules.feishu_uploader import FeishuUploader
from agents.data_output_agent.email_sender import EmailSender
from .database import PostbackDatabase, PartnerSummary

logger = logging.getLogger(__name__)

class ReportGenerator:
    """报表生成器"""
    
    def __init__(self, output_dir: str = "output", 
                 global_email_disabled: bool = False):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # 初始化数据库连接
        self.db = PostbackDatabase()
        
        # 初始化飞书上传和邮件发送器
        self.feishu_uploader = FeishuUploader()
        self.email_sender = EmailSender(global_email_disabled=global_email_disabled)
        
        # 邮件配置
        self.partner_email_mapping = {
            'InvolveAsia': ['partners@involveasia.com'],
            'Rector': ['rector@partners.com'],
            'DeepLeaper': ['deepleaper@partners.com'],
            'ByteC': ['bytec@partners.com'],
            'RAMPUP': ['rampup@partners.com'],
            'ALL': ['AmosFang927@gmail.com']
        }
        
        self.partner_email_enabled = {
            'InvolveAsia': True,
            'Rector': True,
            'DeepLeaper': True,
            'ByteC': True,
            'RAMPUP': True,
            'ALL': True
        }
    
    async def generate_partner_report(self, partner_name: str = "ALL",
                                    start_date: datetime = None,
                                    end_date: datetime = None,
                                    send_email: bool = True,
                                    upload_feishu: bool = True,
                                    self_email: bool = False,
                                    limit: Optional[int] = None) -> Dict[str, Any]:
        """
        生成Partner报表
        
        Args:
            partner_name: Partner名称 (ALL, InvolveAsia, Rector, DeepLeaper, ByteC, RAMPUP)
            start_date: 开始日期
            end_date: 结束日期
            send_email: 是否发送邮件
            upload_feishu: 是否上传到飞书
            limit: 限制拉取的记录数量
            
        Returns:
            Dict[str, Any]: 报表生成结果
        """
        try:
            logger.info(f"🚀 开始生成 {partner_name} 报表")
            
            # 设置默认日期范围（过去7天）
            if not end_date:
                end_date = datetime.now()
            if not start_date:
                start_date = end_date - timedelta(days=7)
            
            # 记录limit设置
            limit_info = f" (限制: {limit} 条)" if limit else ""
            logger.info(f"🔍 查询数据: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}{limit_info}")
            
            # 获取转化数据，传递limit参数
            df = await self.db.get_conversion_dataframe(partner_name, start_date, end_date, limit=limit)
            
            if df.empty:
                logger.warning(f"⚠️ 没有找到 {partner_name} 的转化数据")
                print(f"📋 提示: {partner_name} 在 {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')} 期间没有转化数据，將生成空報表並繼續執行")
                
                # 创建空的partner_summaries
                partner_summaries = []
            else:
                # 如果设置了limit且达到限制，显示信息
                if limit and len(df) >= limit:
                    logger.info(f"📊 已达到数据拉取限制: {len(df)} 条记录 (设置限制: {limit})")
                    print(f"⏹️ 数据收取已停止: 达到设置的 {limit} 条记录限制")
                
                # 获取Partner汇总
                partner_summaries = await self.db.get_partner_summary(partner_name, start_date, end_date, limit=limit)
            
            # 生成Excel文件
            excel_files = await self._generate_excel_files(df, partner_summaries, partner_name, start_date, end_date)
            
            # 計算總金額（處理空數據情況）
            if df.empty or 'USD Sale Amount' not in df.columns:
                total_amount = 0.0
            else:
                total_amount = df['USD Sale Amount'].sum()
            
            result = {
                'success': True,
                'partner_name': partner_name,
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'total_records': len(df),
                'total_amount': total_amount,
                'excel_files': excel_files,
                'partner_summaries': [summary.to_dict() for summary in partner_summaries]
            }
            
            # 飞书上传
            if upload_feishu and excel_files:
                logger.info("📤 开始上传到飞书")
                feishu_result = await self._upload_to_feishu(excel_files)
                result['feishu_upload'] = feishu_result
            
            # 邮件发送
            if send_email and excel_files:
                logger.info("✉️ 开始发送邮件")
                email_result = await self._send_emails(partner_summaries, excel_files, start_date, end_date, self_email)
                result['email_result'] = email_result
            
            logger.info(f"✅ {partner_name} 报表生成完成")
            return result
            
        except Exception as e:
            logger.error(f"❌ 生成报表失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'partner_name': partner_name
            }
    
    async def _generate_excel_files(self, df: pd.DataFrame, 
                                  partner_summaries: List[PartnerSummary],
                                  partner_name: str, 
                                  start_date: datetime,
                                  end_date: datetime) -> List[str]:
        """生成Excel文件"""
        excel_files = []
        
        try:
            if partner_name.upper() == 'ALL':
                # 为每个Partner生成单独的文件
                for summary in partner_summaries:
                    partner_df = df[df['Partner'] == summary.partner_name]
                    if not partner_df.empty:
                        file_path = await self._create_excel_file(
                            partner_df, 
                            summary.partner_name, 
                            start_date, 
                            end_date
                        )
                        excel_files.append(file_path)
                        
                        # 为每个Partner的汇总添加文件路径
                        summary.file_path = file_path
                
                # 生成总汇总文件
                main_file = await self._create_excel_file(df, "AllPartners", start_date, end_date)
                excel_files.insert(0, main_file)  # 插入到第一个位置
                
            else:
                # 生成单个Partner的文件（即使是空數據也要生成）
                file_path = await self._create_excel_file(df, partner_name, start_date, end_date)
                excel_files.append(file_path)
                
                # 为汇总添加文件路径
                if partner_summaries:
                    partner_summaries[0].file_path = file_path
            
            logger.info(f"✅ 成功生成 {len(excel_files)} 个Excel文件")
            return excel_files
            
        except Exception as e:
            logger.error(f"❌ 生成Excel文件失败: {e}")
            raise
    
    def _add_summary_header(self, ws, partner_name: str, start_date: datetime, 
                           end_date: datetime, total_conversions: int, 
                           total_amount: float, current_row: int = 1) -> int:
        """添加匯總信息到工作表頂部，返回數據開始行號"""
        # 標題樣式
        title_font = Font(bold=True, size=14, color="366092")
        info_font = Font(bold=True, size=11)
        
        # 匯總信息標題
        ws.cell(row=current_row, column=1, value="Summary:").font = title_font
        current_row += 1
        
        # Partner信息
        ws.cell(row=current_row, column=1, value=f"Partner: {partner_name}").font = info_font
        current_row += 1
        
        # 日期範圍
        date_range = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        ws.cell(row=current_row, column=1, value=f"Date Range: {date_range}").font = info_font
        current_row += 1
        
        # 總轉化數
        ws.cell(row=current_row, column=1, value=f"Total Conversions: {total_conversions}").font = info_font
        current_row += 1
        
        # 總銷售金額
        ws.cell(row=current_row, column=1, value=f"Total Sale Amount (USD): ${total_amount:,.2f}").font = info_font
        current_row += 1
        
        # 報告創建時間
        from datetime import datetime
        report_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ws.cell(row=current_row, column=1, value=f"Report Created Time: {report_time}").font = info_font
        current_row += 2  # 空一行
        
        return current_row

    async def _create_excel_file(self, df: pd.DataFrame, 
                               partner_name: str,
                               start_date: datetime,
                               end_date: datetime) -> str:
        """创建单个Excel文件，添加總表匯總Sheet + 按Source分组生成不同Sheet"""
        try:
            # 生成文件名
            date_str = f"{start_date.strftime('%Y-%m-%d')}_to_{end_date.strftime('%Y-%m-%d')}"
            filename = f"{partner_name}_ConversionReport_{date_str}.xlsx"
            file_path = self.output_dir / filename
            
            # 创建工作簿
            wb = Workbook()
            # 删除默认的工作表
            wb.remove(wb.active)
            
            # 设置标题样式
            header_font = Font(bold=True, color="FFFFFF")
            header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            header_alignment = Alignment(horizontal="center", vertical="center")
            
            # 数据样式
            data_alignment = Alignment(horizontal="left", vertical="center")
            number_alignment = Alignment(horizontal="right", vertical="center")
            
            # 1. 首先創建Partner名稱 Sheet
            summary_ws = wb.create_sheet(partner_name, 0)
            
            if not df.empty:
                # 計算總金額
                total_amount = 0
                if 'USD Sale Amount' in df.columns:
                    total_amount = df['USD Sale Amount'].sum()
                
                # 添加匯總信息區塊
                current_row = self._add_summary_header(
                    summary_ws, partner_name, start_date, end_date, 
                    len(df), total_amount, 1
                )
                
                # 寫入總表數據（所有數據）
                headers = list(df.columns)
                
                # 寫入標題行
                for col_idx, header in enumerate(headers, 1):
                    cell = summary_ws.cell(row=current_row, column=col_idx, value=header)
                    cell.font = header_font
                    cell.fill = header_fill
                    cell.alignment = header_alignment
                
                # 寫入數據行
                data_start_row = current_row + 1
                for row_idx, (_, row) in enumerate(df.iterrows(), data_start_row):
                    for col_idx, value in enumerate(row, 1):
                        cell = summary_ws.cell(row=row_idx, column=col_idx, value=value)
                        
                        # 設置數據格式
                        if isinstance(value, (int, float)):
                            cell.alignment = number_alignment
                            if 'USD Sale Amount' in headers[col_idx-1]:
                                cell.number_format = '"$"#,##0.00'
                        else:
                            cell.alignment = data_alignment
                
                # 調整列寬
                for col_idx, header in enumerate(headers, 1):
                    column_letter = get_column_letter(col_idx)
                    if 'ID' in header or 'Amount' in header:
                        summary_ws.column_dimensions[column_letter].width = 15
                    elif 'Datetime' in header:
                        summary_ws.column_dimensions[column_letter].width = 20
                    else:
                        summary_ws.column_dimensions[column_letter].width = 18
                

            
            # 2. 然後按 Source 分組創建各個 Sheet
            if not df.empty and 'Source' in df.columns:
                sources = df['Source'].unique()
                
                for source in sources:
                    if pd.isna(source) or source == '':
                        sheet_name = "Unknown_Source"
                    else:
                        # 清理 sheet 名稱，移除不允許的字符
                        sheet_name = str(source).replace('/', '_').replace('\\', '_').replace('*', '_').replace('[', '_').replace(']', '_').replace(':', '_').replace('?', '_')
                        # 限制長度
                        if len(sheet_name) > 31:
                            sheet_name = sheet_name[:31]
                    
                    # 確保 sheet 名稱唯一
                    original_name = sheet_name
                    counter = 1
                    while sheet_name in [ws.title for ws in wb.worksheets]:
                        sheet_name = f"{original_name}_{counter}"
                        if len(sheet_name) > 31:
                            sheet_name = f"{original_name[:28]}_{counter}"
                        counter += 1
                    
                    ws = wb.create_sheet(sheet_name)
                    
                    # 過濾該 Source 的數據
                    source_df = df[df['Source'] == source].copy()
                    
                    if not source_df.empty:
                        # 計算該Source的總金額
                        source_total_amount = 0
                        if 'USD Sale Amount' in source_df.columns:
                            source_total_amount = source_df['USD Sale Amount'].sum()
                        
                        # 添加匯總信息區塊
                        current_row = self._add_summary_header(
                            ws, partner_name, start_date, end_date, 
                            len(source_df), source_total_amount, 1
                        )
                        
                        headers = list(source_df.columns)
                        
                        # 寫入標題行
                        for col_idx, header in enumerate(headers, 1):
                            cell = ws.cell(row=current_row, column=col_idx, value=header)
                            cell.font = header_font
                            cell.fill = header_fill
                            cell.alignment = header_alignment
                        
                        # 寫入數據行
                        data_start_row = current_row + 1
                        for row_idx, (_, row) in enumerate(source_df.iterrows(), data_start_row):
                            for col_idx, value in enumerate(row, 1):
                                cell = ws.cell(row=row_idx, column=col_idx, value=value)
                                
                                # 設置數據格式
                                if isinstance(value, (int, float)):
                                    cell.alignment = number_alignment
                                    if 'USD Sale Amount' in headers[col_idx-1]:
                                        cell.number_format = '"$"#,##0.00'
                                else:
                                    cell.alignment = data_alignment
                        
                        # 調整列寬
                        for col_idx, header in enumerate(headers, 1):
                            column_letter = get_column_letter(col_idx)
                            if 'ID' in header or 'Amount' in header:
                                ws.column_dimensions[column_letter].width = 15
                            elif 'Datetime' in header:
                                ws.column_dimensions[column_letter].width = 20
                            else:
                                ws.column_dimensions[column_letter].width = 18
                        

            
            # 如果沒有數據，創建空的工作表
            if df.empty:
                empty_ws = wb.create_sheet("無數據")
                empty_ws.cell(row=1, column=1, value="在指定時間範圍內沒有找到轉化數據")
            
            # 保存文件
            wb.save(file_path)
            logger.info(f"✅ Excel文件已创建: {file_path}")
            
            return str(file_path)
            
        except Exception as e:
            logger.error(f"❌ 创建Excel文件失败: {e}")
            raise
    
    def _clean_sheet_name(self, name: str) -> str:
        """
        清理Excel工作表名称，移除不支持的字符
        
        Excel工作表名称限制：
        - 不能超过31个字符
        - 不能包含: [ ] : * ? / \\ '
        - 不能为空或只包含空格
        - 不能以单引号开头或结尾
        """
        import re
        
        if not name or not str(name).strip():
            return "Unknown"
        
        # 转换为字符串并去除前后空格
        clean_name = str(name).strip()
        
        # 移除或替换Excel不支持的字符
        clean_name = clean_name.replace('/', '_').replace('\\', '_')
        clean_name = clean_name.replace('[', '(').replace(']', ')')
        clean_name = clean_name.replace(':', '-').replace('*', '_')
        clean_name = clean_name.replace('?', '_').replace('\'', '')
        
        # 移除其他可能有问题的Unicode字符，保留基本字母、数字、空格和常见符号
        clean_name = re.sub(r'[^\w\s\-\(\)\_\.]', '_', clean_name)
        
        # 限制长度为31个字符
        if len(clean_name) > 31:
            clean_name = clean_name[:31]
        
        # 确保不以单引号开头或结尾
        clean_name = clean_name.strip("'")
        
        # 如果清理后为空，使用默认名称
        if not clean_name:
            clean_name = "Unknown"
        
        return clean_name
    
    async def _upload_to_feishu(self, excel_files: List[str]) -> Dict[str, Any]:
        """上传到飞书"""
        try:
            # 使用原有的FeishuUploader
            upload_result = self.feishu_uploader.upload_files(excel_files)
            
            if upload_result['success']:
                logger.info(f"✅ 飞书上传成功: {upload_result['success_count']} 个文件")
            else:
                logger.warning(f"⚠️ 飞书上传部分失败: 成功 {upload_result['success_count']} 个，失败 {upload_result['failed_count']} 个")
            
            return upload_result
            
        except Exception as e:
            logger.error(f"❌ 飞书上传失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'success_count': 0,
                'failed_count': len(excel_files)
            }
    
    async def _send_emails(self, partner_summaries: List[PartnerSummary],
                         excel_files: List[str],
                         start_date: datetime,
                         end_date: datetime,
                         self_email: bool = False) -> Dict[str, Any]:
        """发送邮件"""
        try:
            # 准备Partner邮件数据
            partner_summary_dict = {}
            for summary in partner_summaries:
                partner_summary_dict[summary.partner_name] = {
                    'records': summary.total_records,
                    'amount_formatted': summary.amount_formatted,
                    'file_path': getattr(summary, 'file_path', None),
                    'sources': summary.sources,
                    'sources_count': summary.sources_count
                }
            
            # 使用原有的EmailSender发送邮件
            email_result = self.email_sender.send_partner_reports(
                partner_summary_dict,
                None,  # feishu_upload_result
                end_date,
                start_date,
                self_email
            )
            
            if email_result['success']:
                logger.info(f"✅ 邮件发送成功: {email_result['total_sent']} 封")
            else:
                logger.warning(f"⚠️ 邮件发送部分失败: 成功 {email_result['total_sent']} 封，失败 {email_result['total_failed']} 封")
            
            return email_result
            
        except Exception as e:
            logger.error(f"❌ 邮件发送失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'total_sent': 0,
                'total_failed': len(partner_summaries)
            }
    
    async def get_available_partners(self) -> List[str]:
        """获取可用的Partner列表"""
        try:
            partners = await self.db.get_available_partners()
            # 添加特殊的ALL选项
            if 'ALL' not in partners:
                partners.insert(0, 'ALL')
            return partners
        except Exception as e:
            logger.error(f"❌ 获取Partner列表失败: {e}")
            return ['ALL']
    
    async def get_partner_preview(self, partner_name: str = "ALL",
                                start_date: datetime = None,
                                end_date: datetime = None) -> Dict[str, Any]:
        """获取Partner数据预览"""
        try:
            # 设置默认日期范围
            if not end_date:
                end_date = datetime.now()
            if not start_date:
                start_date = end_date - timedelta(days=7)
            
            # 获取汇总数据
            partner_summaries = await self.db.get_partner_summary(partner_name, start_date, end_date)
            
            # 获取最近的一些转化记录作为预览
            df = await self.db.get_conversion_dataframe(partner_name, start_date, end_date)
            
            preview_data = []
            if not df.empty:
                # 取前10条记录作为预览
                preview_df = df.head(10)
                preview_data = preview_df.to_dict('records')
            
            return {
                'success': True,
                'partner_name': partner_name,
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'total_records': len(df),
                'total_amount': df['Sale Amount (USD)'].sum() if not df.empty else 0,
                'partner_summaries': [summary.to_dict() for summary in partner_summaries],
                'preview_data': preview_data
            }
            
        except Exception as e:
            logger.error(f"❌ 获取Partner预览失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'partner_name': partner_name
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            # 检查数据库连接
            db_health = await self.db.health_check()
            
            # 检查输出目录
            output_dir_exists = self.output_dir.exists()
            output_dir_writable = os.access(self.output_dir, os.W_OK) if output_dir_exists else False
            
            return {
                'status': 'healthy' if db_health['status'] == 'healthy' else 'unhealthy',
                'database': db_health,
                'output_directory': {
                    'exists': output_dir_exists,
                    'writable': output_dir_writable,
                    'path': str(self.output_dir)
                },
                'components': {
                    'feishu_uploader': 'available',
                    'email_sender': 'available'
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ 健康检查失败: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def cleanup(self):
        """清理资源"""
        try:
            await self.db.close_pool()
            logger.info("✅ 报表生成器资源清理完成")
        except Exception as e:
            logger.error(f"❌ 清理资源失败: {e}") 