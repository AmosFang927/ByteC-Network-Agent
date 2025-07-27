#!/usr/bin/env python3
"""
同步版本的 Dashboard 服务
專門為 Flask 應用設計
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class SyncDashboardService:
    """同步版本的 Dashboard 服务"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def get_summary_data(self, start_date: str, end_date: str, partner_id: Optional[int] = None) -> Dict[str, Any]:
        """获取总览数据"""
        try:
            # 获取基础指标
            metrics = self.db_manager.get_summary_metrics(start_date, end_date, partner_id)
            
            # 获取趋势数据
            daily_trend = self.db_manager.get_daily_trend(start_date, end_date, partner_id)
            
            return {
                'metrics': metrics,
                'daily_trend': daily_trend
            }
        except Exception as e:
            logger.error(f"获取总览数据失败: {e}")
            return {
                'metrics': {
                    'total_conversions': 0,
                    'total_commission': 0.0,
                    'avg_commission': 0.0,
                    'unique_affiliates': 0
                },
                'daily_trend': []
            }
    
    def get_conversion_report_data(self, start_date: str, end_date: str, 
                                 partner_id: Optional[int] = None, 
                                 page: int = 1, limit: int = 100) -> Dict[str, Any]:
        """获取转换报告数据"""
        try:
            return self.db_manager.get_conversion_report_data(start_date, end_date, partner_id, page, limit)
        except Exception as e:
            logger.error(f"获取转换报告数据失败: {e}")
            return {
                'conversions': [],
                'total_count': 0,
                'page': page,
                'limit': limit
            }
    
    def get_filter_options(self) -> Dict[str, Any]:
        """获取过滤器选项"""
        try:
            return self.db_manager.get_filter_options()
        except Exception as e:
            logger.error(f"获取过滤器选项失败: {e}")
            return {'partners': [], 'statuses': []}
    
    def get_company_level_data(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """获取公司级别数据"""
        try:
            # 簡化實現，直接使用總覽數據
            return self.get_summary_data(start_date, end_date)
        except Exception as e:
            logger.error(f"获取公司级别数据失败: {e}")
            return {'metrics': {}, 'daily_trend': []}
    
    def get_offer_level_data(self, start_date: str, end_date: str, partner_id: Optional[int] = None) -> Dict[str, Any]:
        """获取优惠级别数据"""
        try:
            # 簡化實現，直接使用總覽數據
            return self.get_summary_data(start_date, end_date, partner_id)
        except Exception as e:
            logger.error(f"获取优惠级别数据失败: {e}")
            return {'metrics': {}, 'daily_trend': []}
    
    def get_partner_level_data(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """获取合作伙伴级别数据"""
        try:
            # 簡化實現，直接使用總覽數據
            return self.get_summary_data(start_date, end_date)
        except Exception as e:
            logger.error(f"获取合作伙伴级别数据失败: {e}")
            return {'metrics': {}, 'daily_trend': []}
    
    def get_enhanced_conversion_report_data(self, start_date: str, end_date: str, 
                                          partner_name: Optional[str] = None, 
                                          page: int = 1, limit: int = 100) -> Dict[str, Any]:
        """获取增强版转换报告数据"""
        try:
            # 簡化實現，如果有 partner_name，嘗試獲取 partner_id
            partner_id = None
            if partner_name:
                partners = self.db_manager.get_partners()
                for partner in partners:
                    if partner.get('partner_name') == partner_name:
                        partner_id = partner.get('id')
                        break
            
            return self.db_manager.get_conversion_report_data(start_date, end_date, partner_id, page, limit)
        except Exception as e:
            logger.error(f"获取增强版转换报告数据失败: {e}")
            return {
                'conversions': [],
                'total_count': 0,
                'page': page,
                'limit': limit
            }
    
    def get_enhanced_filter_options(self) -> Dict[str, Any]:
        """获取增强版过滤器选项"""
        try:
            return self.db_manager.get_filter_options()
        except Exception as e:
            logger.error(f"获取增强版过滤器选项失败: {e}")
            return {'partners': [], 'statuses': []}
    
    def drill_data(self, data_type: str, filter_key: str, filter_value: str, 
                   start_date: str, end_date: str) -> Dict[str, Any]:
        """数据钻取功能"""
        try:
            # 簡化實現
            return {
                'data_type': data_type,
                'filter_key': filter_key,
                'filter_value': filter_value,
                'results': []
            }
        except Exception as e:
            logger.error(f"数据钻取失败: {e}")
            return {'results': []} 