#!/usr/bin/env python3
"""
统一Summary格式化工具
用于生成一致的邮件和报表Summary格式
"""

import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SummaryFormatter:
    """统一Summary格式化器"""
    
    @staticmethod
    def generate_unified_summary(
        partner_name: str,
        start_date: str,
        end_date: str,
        df: Optional[pd.DataFrame] = None,
        total_records: int = 0,
        total_amount: float = 0.0,
        sources: List[str] = None
    ) -> Dict[str, Any]:
        """
        生成统一的Summary格式
        
        Args:
            partner_name: 合作伙伴名称
            start_date: 开始日期
            end_date: 结束日期
            df: 数据DataFrame（可选）
            total_records: 总记录数
            total_amount: 总金额
            sources: 来源列表
            
        Returns:
            统一的Summary字典
        """
        try:
            # 初始化默认值
            if sources is None:
                sources = []
            
            # 计算状态统计
            status_stats = SummaryFormatter._calculate_status_statistics(df, total_records, total_amount)
            
            # 格式化来源列表
            sources_list = ", ".join(sources) if sources else "无"
            
            # 生成统一的Summary格式
            summary = {
                'partner_name': partner_name,
                'date_range': f"{start_date} 至 {end_date}",
                'total_all_conversions': status_stats['total_all_conversions'],
                'pending_approved_count': status_stats['pending_approved_count'],
                'pending_approved_amount': status_stats['pending_approved_amount'],
                'invalid_rejected_count': status_stats['invalid_rejected_count'],
                'invalid_rejected_amount': status_stats['invalid_rejected_amount'],
                'sources_list': sources_list,
                'sources': sources,
                'sources_count': len(sources),
                # 兼容性字段
                'total_records': status_stats['pending_approved_count'],  # 有效记录数
                'total_amount': status_stats['pending_approved_amount_numeric'],  # 有效金额
                'total_amount_formatted': status_stats['pending_approved_amount']
            }
            
            logger.info(f"✅ 生成统一Summary: {partner_name}, 有效转化: {status_stats['pending_approved_count']}, 金额: {status_stats['pending_approved_amount']}")
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ 生成统一Summary失败: {e}")
            # 返回默认值
            return {
                'partner_name': partner_name,
                'date_range': f"{start_date} 至 {end_date}",
                'total_all_conversions': 0,
                'pending_approved_count': 0,
                'pending_approved_amount': '$0.00',
                'invalid_rejected_count': 0,
                'invalid_rejected_amount': '$0.00',
                'sources_list': "无",
                'sources': [],
                'sources_count': 0,
                'total_records': 0,
                'total_amount': 0.0,
                'total_amount_formatted': '$0.00'
            }
    
    @staticmethod
    def _calculate_status_statistics(
        df: Optional[pd.DataFrame], 
        total_records: int = 0, 
        total_amount: float = 0.0
    ) -> Dict[str, Any]:
        """
        计算状态统计
        
        Args:
            df: 数据DataFrame
            total_records: 总记录数（备用）
            total_amount: 总金额（备用）
            
        Returns:
            状态统计字典
        """
        try:
            if df is not None and not df.empty and 'Status' in df.columns:
                # 从DataFrame计算统计
                return SummaryFormatter._calculate_from_dataframe(df)
            else:
                # 使用备用数据
                return SummaryFormatter._calculate_from_backup_data(total_records, total_amount)
                
        except Exception as e:
            logger.error(f"❌ 计算状态统计失败: {e}")
            return SummaryFormatter._get_default_status_stats()
    
    @staticmethod
    def _calculate_from_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
        """从DataFrame计算状态统计"""
        try:
            # 总转化数（所有状态）
            total_all_conversions = len(df)
            
            # 计算各状态的统计
            # 无效状态：包含invalid, rejected, cancelled, failed等
            invalid_keywords = ['invalid', 'rejected', 'cancelled', 'canceled', 'failed', 'decline']
            invalid_rejected_mask = df['Status'].str.lower().str.contains('|'.join(invalid_keywords), na=False)
            
            # 有效状态：除了无效状态外的所有其他状态
            pending_approved_mask = ~invalid_rejected_mask
            
            pending_approved_count = pending_approved_mask.sum()
            invalid_rejected_count = invalid_rejected_mask.sum()
            
            # 计算各状态的金额 (如果有 USD Sale Amount 列)
            pending_approved_amount = 0.0
            invalid_rejected_amount = 0.0
            
            if 'USD Sale Amount' in df.columns:
                # 处理可能的格式化字符串金额
                def parse_currency(value):
                    """解析货币字符串，返回数值"""
                    if pd.isna(value):
                        return 0.0
                    if isinstance(value, str):
                        # 移除美元符号、逗号和其他非数字字符
                        cleaned_value = value.replace('$', '').replace(',', '').strip()
                        try:
                            return float(cleaned_value)
                        except ValueError:
                            return 0.0
                    return float(value) if value else 0.0
                
                # 计算有效转化金额
                valid_amounts = df[pending_approved_mask]['USD Sale Amount'].apply(parse_currency)
                pending_approved_amount = valid_amounts.sum()
                
                # 计算无效转化金额
                invalid_amounts = df[invalid_rejected_mask]['USD Sale Amount'].apply(parse_currency)
                invalid_rejected_amount = invalid_amounts.sum()
            
            logger.debug(f"📊 DataFrame状态统计: 总计 {total_all_conversions}, 有效 {pending_approved_count}, 无效 {invalid_rejected_count}")
            logger.debug(f"💰 金额统计: 有效 ${pending_approved_amount:,.2f}, 无效 ${invalid_rejected_amount:,.2f}")
            
            return {
                'total_all_conversions': total_all_conversions,
                'pending_approved_count': pending_approved_count,
                'pending_approved_amount': f"${pending_approved_amount:,.2f}",
                'pending_approved_amount_numeric': pending_approved_amount,
                'invalid_rejected_count': invalid_rejected_count,
                'invalid_rejected_amount': f"${invalid_rejected_amount:,.2f}",
                'invalid_rejected_amount_numeric': invalid_rejected_amount
            }
            
        except Exception as e:
            logger.error(f"❌ 从DataFrame计算状态统计失败: {e}")
            return SummaryFormatter._get_default_status_stats()
    
    @staticmethod
    def _calculate_from_backup_data(total_records: int, total_amount: float) -> Dict[str, Any]:
        """从备用数据计算状态统计"""
        return {
            'total_all_conversions': total_records,
            'pending_approved_count': total_records,
            'pending_approved_amount': f"${total_amount:,.2f}",
            'pending_approved_amount_numeric': total_amount,
            'invalid_rejected_count': 0,
            'invalid_rejected_amount': '$0.00',
            'invalid_rejected_amount_numeric': 0.0
        }
    
    @staticmethod
    def _get_default_status_stats() -> Dict[str, Any]:
        """获取默认状态统计"""
        return {
            'total_all_conversions': 0,
            'pending_approved_count': 0,
            'pending_approved_amount': '$0.00',
            'pending_approved_amount_numeric': 0.0,
            'invalid_rejected_count': 0,
            'invalid_rejected_amount': '$0.00',
            'invalid_rejected_amount_numeric': 0.0
        }
    
    @staticmethod
    def format_summary_for_display(summary: Dict[str, Any]) -> str:
        """
        格式化Summary为显示文本
        
        Args:
            summary: Summary字典
            
        Returns:
            格式化的显示文本
        """
        lines = [
            f"Partner: {summary['partner_name']}",
            f"Date Range: {summary['date_range']}",
            f"Total Conversions (All Status): {summary['total_all_conversions']:,} 条",
            f"✅ Total Conversions (Pending/Approved): {summary['pending_approved_count']:,} 条",
            f"✅ Total Sale Amount (USD) (Pending/Approved): {summary['pending_approved_amount']}",
            f"⚠️ Total Conversions (Invalid/Rejected): {summary['invalid_rejected_count']:,} 条",
            f"⚠️ Total Sale Amount (USD) (Invalid/Rejected): {summary['invalid_rejected_amount']}",
            f"Sources: {summary['sources_list']}"
        ]
        
        return "\n".join(lines)
    
    @staticmethod
    def format_summary_for_email(summary: Dict[str, Any]) -> Dict[str, str]:
        """
        格式化Summary为邮件模板变量
        
        Args:
            summary: Summary字典
            
        Returns:
            邮件模板变量字典
        """
        return {
            'partner_name': summary['partner_name'],
            'start_date': summary['date_range'].split(' 至 ')[0],
            'end_date': summary['date_range'].split(' 至 ')[1],
            'total_all_conversions': f"{summary['total_all_conversions']:,}",
            'pending_approved_count': f"{summary['pending_approved_count']:,}",
            'pending_approved_amount': summary['pending_approved_amount'],
            'invalid_rejected_count': f"{summary['invalid_rejected_count']:,}",
            'invalid_rejected_amount': summary['invalid_rejected_amount'],
            'sources_list': summary['sources_list']
        }


# 便捷函数
def generate_unified_summary(
    partner_name: str,
    start_date: str,
    end_date: str,
    df: Optional[pd.DataFrame] = None,
    total_records: int = 0,
    total_amount: float = 0.0,
    sources: List[str] = None
) -> Dict[str, Any]:
    """便捷函数：生成统一Summary"""
    return SummaryFormatter.generate_unified_summary(
        partner_name, start_date, end_date, df, total_records, total_amount, sources
    )


def format_summary_for_display(summary: Dict[str, Any]) -> str:
    """便捷函数：格式化Summary为显示文本"""
    return SummaryFormatter.format_summary_for_display(summary)


def format_summary_for_email(summary: Dict[str, Any]) -> Dict[str, str]:
    """便捷函数：格式化Summary为邮件模板变量"""
    return SummaryFormatter.format_summary_for_email(summary) 