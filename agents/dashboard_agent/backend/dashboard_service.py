#!/usr/bin/env python3
"""
Dashboard业务逻辑服务
处理dashboard的业务逻辑和数据处理
"""

import asyncio
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime, timedelta
from decimal import Decimal

from agents.dashboard_agent.backend.database_manager import DatabaseManager

# 配置日志
logger = logging.getLogger(__name__)

class DashboardService:
    """Dashboard业务逻辑服务"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def _convert_decimals(self, data: Any) -> Any:
        """递归转换数据中的Decimal类型为float，以便JSON序列化"""
        if isinstance(data, Decimal):
            return float(data)
        elif isinstance(data, dict):
            return {key: self._convert_decimals(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._convert_decimals(item) for item in data]
        elif isinstance(data, tuple):
            return tuple(self._convert_decimals(item) for item in data)
        else:
            return data
    
    # =============================================================================
    # 总览数据服务
    # =============================================================================
    
    async def get_summary_data(self, start_date: str, end_date: str, partner_id: Optional[int] = None) -> Dict[str, Any]:
        """获取总览数据"""
        try:
            # 并行获取所有数据
            metrics_task = self.db_manager.get_summary_metrics(start_date, end_date, partner_id)
            daily_trend_task = self.db_manager.get_daily_trend(start_date, end_date, partner_id)
            hourly_trend_task = self.db_manager.get_hourly_trend(start_date, end_date, partner_id)
            
            metrics, daily_trend, hourly_trend = await asyncio.gather(
                metrics_task, daily_trend_task, hourly_trend_task
            )
            
            # 计算转化率等衍生指标
            processed_metrics = self._process_summary_metrics(metrics)
            
            result = {
                "metrics": processed_metrics,
                "daily_trend": daily_trend,
                "hourly_trend": hourly_trend,
                "top_hours": self._get_top_hours(hourly_trend),
                "growth_rate": self._calculate_growth_rate(daily_trend)
            }
            
            # 转换所有Decimal类型
            return self._convert_decimals(result)
        except Exception as e:
            logger.error(f"获取总览数据失败: {e}")
            return {}
    
    def _process_summary_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """处理总览指标"""
        if not metrics:
            return {}
        
        # 计算转化率等衍生指标
        processed = dict(metrics)
        
        # 计算平均每个合作伙伴的转化数
        if metrics.get('unique_partners', 0) > 0:
            processed['avg_conversions_per_partner'] = metrics['total_conversions'] / metrics['unique_partners']
        else:
            processed['avg_conversions_per_partner'] = 0
        
        # 计算每个offer的平均转化数
        if metrics.get('unique_offers', 0) > 0:
            processed['avg_conversions_per_offer'] = metrics['total_conversions'] / metrics['unique_offers']
        else:
            processed['avg_conversions_per_offer'] = 0
        
        # 计算利润率
        if metrics.get('total_sales', 0) > 0:
            processed['profit_margin'] = (metrics['total_payout'] / metrics['total_sales']) * 100
        else:
            processed['profit_margin'] = 0
        
        return processed
    
    def _get_top_hours(self, hourly_trend: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """获取表现最好的小时"""
        if not hourly_trend:
            return []
        
        # 按转化数排序，返回前5个小时
        sorted_hours = sorted(hourly_trend, key=lambda x: x['conversions'], reverse=True)
        return sorted_hours[:5]
    
    def _calculate_growth_rate(self, daily_trend: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算增长率"""
        if len(daily_trend) < 2:
            return {"daily_growth": 0, "trend": "stable"}
        
        # 计算最近两天的增长率
        recent_days = sorted(daily_trend, key=lambda x: x['date'])[-2:]
        
        if len(recent_days) >= 2:
            today_conversions = recent_days[-1]['conversions']
            yesterday_conversions = recent_days[-2]['conversions']
            
            if yesterday_conversions > 0:
                growth_rate = ((today_conversions - yesterday_conversions) / yesterday_conversions) * 100
                trend = "up" if growth_rate > 0 else "down" if growth_rate < 0 else "stable"
            else:
                growth_rate = 0
                trend = "stable"
        else:
            growth_rate = 0
            trend = "stable"
        
        return {
            "daily_growth": round(growth_rate, 2),
            "trend": trend
        }
    
    # =============================================================================
    # 公司级别数据服务
    # =============================================================================
    
    async def get_company_level_data(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """获取公司级别数据"""
        try:
            # 并行获取公司和地区数据
            company_task = self.db_manager.get_company_performance(start_date, end_date)
            region_task = self.db_manager.get_region_performance(start_date, end_date)
            
            company_data, region_data = await asyncio.gather(company_task, region_task)
            
            return {
                "company_performance": company_data,
                "region_performance": region_data,
                "top_companies": self._get_top_performers(company_data, 5),
                "top_regions": self._get_top_performers(region_data, 5),
                "company_summary": self._calculate_company_summary(company_data),
                "region_summary": self._calculate_region_summary(region_data)
            }
        except Exception as e:
            logger.error(f"获取公司级别数据失败: {e}")
            return {}
    
    def _get_top_performers(self, data: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
        """获取表现最好的前N名"""
        if not data:
            return []
        
        sorted_data = sorted(data, key=lambda x: x['conversions'], reverse=True)
        return sorted_data[:limit]
    
    def _calculate_company_summary(self, company_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算公司数据摘要"""
        if not company_data:
            return {}
        
        total_conversions = sum(item['conversions'] for item in company_data)
        total_sales = sum(item['total_sales'] for item in company_data)
        
        return {
            "total_companies": len(company_data),
            "total_conversions": total_conversions,
            "total_sales": total_sales,
            "avg_conversions_per_company": total_conversions / len(company_data) if company_data else 0
        }
    
    def _calculate_region_summary(self, region_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算地区数据摘要"""
        if not region_data:
            return {}
        
        total_conversions = sum(item['conversions'] for item in region_data)
        total_sales = sum(item['total_sales'] for item in region_data)
        
        return {
            "total_regions": len(region_data),
            "total_conversions": total_conversions,
            "total_sales": total_sales,
            "avg_conversions_per_region": total_conversions / len(region_data) if region_data else 0
        }
    
    # =============================================================================
    # 产品级别数据服务
    # =============================================================================
    
    async def get_offer_level_data(self, start_date: str, end_date: str, partner_id: Optional[int] = None) -> Dict[str, Any]:
        """获取产品级别数据"""
        try:
            offer_data = await self.db_manager.get_offer_performance(start_date, end_date, partner_id)
            
            return {
                "offer_performance": offer_data,
                "top_offers": self._get_top_performers(offer_data, 10),
                "offer_summary": self._calculate_offer_summary(offer_data),
                "offer_categories": self._categorize_offers(offer_data)
            }
        except Exception as e:
            logger.error(f"获取产品级别数据失败: {e}")
            return {}
    
    def _calculate_offer_summary(self, offer_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算产品数据摘要"""
        if not offer_data:
            return {}
        
        total_conversions = sum(item['conversions'] for item in offer_data)
        total_sales = sum(item['total_sales'] for item in offer_data)
        
        return {
            "total_offers": len(offer_data),
            "total_conversions": total_conversions,
            "total_sales": total_sales,
            "avg_conversions_per_offer": total_conversions / len(offer_data) if offer_data else 0
        }
    
    def _categorize_offers(self, offer_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """对产品进行分类"""
        categories = {}
        
        for offer in offer_data:
            offer_name = offer.get('offer_name', '').lower()
            
            # 简单的分类逻辑
            if 'shopee' in offer_name:
                category = 'Shopee'
            elif 'lazada' in offer_name:
                category = 'Lazada'
            elif 'grab' in offer_name:
                category = 'Grab'
            elif 'tiktok' in offer_name:
                category = 'TikTok'
            else:
                category = 'Others'
            
            if category not in categories:
                categories[category] = {
                    'count': 0,
                    'conversions': 0,
                    'total_sales': 0
                }
            
            categories[category]['count'] += 1
            categories[category]['conversions'] += offer['conversions']
            categories[category]['total_sales'] += offer['total_sales']
        
        return categories
    
    # =============================================================================
    # 合作伙伴级别数据服务
    # =============================================================================
    
    async def get_partner_level_data(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """获取合作伙伴级别数据"""
        try:
            # 并行获取合作伙伴和Sub ID数据
            partner_task = self.db_manager.get_partner_performance(start_date, end_date)
            sub_id_task = self.db_manager.get_sub_id_performance(start_date, end_date)
            
            partner_data, sub_id_data = await asyncio.gather(partner_task, sub_id_task)
            
            return {
                "partner_performance": partner_data,
                "sub_id_performance": sub_id_data,
                "top_partners": self._get_top_performers(partner_data, 10),
                "top_sub_ids": self._get_top_performers(sub_id_data, 20),
                "partner_summary": self._calculate_partner_summary(partner_data),
                "sub_id_summary": self._calculate_sub_id_summary(sub_id_data)
            }
        except Exception as e:
            logger.error(f"获取合作伙伴级别数据失败: {e}")
            return {}
    
    def _calculate_partner_summary(self, partner_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算合作伙伴数据摘要"""
        if not partner_data:
            return {}
        
        active_partners = [p for p in partner_data if p['conversions'] > 0]
        total_conversions = sum(item['conversions'] for item in active_partners)
        total_sales = sum(item['total_sales'] for item in active_partners)
        
        return {
            "total_partners": len(partner_data),
            "active_partners": len(active_partners),
            "total_conversions": total_conversions,
            "total_sales": total_sales,
            "avg_conversions_per_partner": total_conversions / len(active_partners) if active_partners else 0
        }
    
    def _calculate_sub_id_summary(self, sub_id_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算Sub ID数据摘要"""
        if not sub_id_data:
            return {}
        
        total_conversions = sum(item['conversions'] for item in sub_id_data)
        total_sales = sum(item['total_sales'] for item in sub_id_data)
        
        return {
            "total_sub_ids": len(sub_id_data),
            "total_conversions": total_conversions,
            "total_sales": total_sales,
            "avg_conversions_per_sub_id": total_conversions / len(sub_id_data) if sub_id_data else 0
        }
    
    # =============================================================================
    # 转化报告数据服务
    # =============================================================================
    
    async def get_conversion_report_data(self, start_date: str, end_date: str, partner_id: Optional[int] = None,
                                       page: int = 1, limit: int = 100) -> Dict[str, Any]:  # 修改默认值为100
        """获取转化报告数据"""
        try:
            conversion_data = await self.db_manager.get_detailed_conversions(
                start_date, end_date, partner_id, page, limit
            )
            
            # 处理转化报告数据
            processed_data = self._process_conversion_report(conversion_data)
            
            return processed_data
        except Exception as e:
            logger.error(f"获取转化报告数据失败: {e}")
            return {}
    
    def _process_conversion_report(self, conversion_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理转化报告数据"""
        if not conversion_data.get('records'):
            return conversion_data
        
        records = conversion_data['records']
        
        # 安全的数值提取函数
        def safe_float(value, default=0.0):
            """安全地提取浮点数值"""
            if value is None or value == '':
                return default
            try:
                return float(value)
            except (ValueError, TypeError):
                return default
        
        # 计算汇总信息 - 使用安全的数值转换
        total_sales = sum(safe_float(record.get('Sale Amount (USD)')) for record in records)
        total_payout = sum(safe_float(record.get('Payout (USD)')) for record in records)
        
        conversion_data['summary'] = {
            'total_records': len(records),
            'total_sales': total_sales,
            'total_payout': total_payout,
            'avg_sale_amount': total_sales / len(records) if records else 0,
            'avg_payout': total_payout / len(records) if records else 0
        }
        
        return conversion_data
    
    async def get_enhanced_conversion_report_data(self, start_date: str, end_date: str, partner_name: Optional[str] = None,
                                                page: int = 1, limit: int = 100) -> Dict[str, Any]:
        """获取增强版转化报告数据 - 使用新的数据库字段结构"""
        try:
            conversion_data = await self.db_manager.get_enhanced_detailed_conversions(
                start_date, end_date, partner_name, page, limit
            )
            
            # 处理增强版转化报告数据
            processed_data = self._process_enhanced_conversion_report(conversion_data)
            
            return processed_data
        except Exception as e:
            logger.error(f"获取增强版转化报告数据失败: {e}")
            return {
                "records": [],
                "total": 0,
                "total_sale_amount": 0,
                "avg_commission_rate": 0,
                "page": page,
                "limit": limit,
                "pages": 0,
                "summary": {}
            }
    
    def _process_enhanced_conversion_report(self, conversion_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理增强版转化报告数据"""
        if not conversion_data.get('records'):
            return conversion_data
        
        records = conversion_data['records']
        
        # 计算详细汇总信息
        total_conversions = conversion_data.get('total', 0)
        total_sale_amount = conversion_data.get('total_sale_amount', 0) or 0
        avg_commission_rate = conversion_data.get('avg_commission_rate', 0) or 0
        
        # 安全的数值提取函数
        def safe_float(value, default=0.0):
            """安全地提取浮点数值"""
            if value is None or value == '':
                return default
            try:
                return float(value)
            except (ValueError, TypeError):
                return default
        
        # 从当前页面记录计算额外统计
        page_sale_amount = sum(safe_float(record.get('Sale Amount')) for record in records)
        page_payout = sum(safe_float(record.get('Payout')) for record in records)
        page_usd_sale = sum(safe_float(record.get('USD Sale Amount')) for record in records)
        page_usd_payout = sum(safe_float(record.get('USD Payout')) for record in records)
        
        # 计算平台分布
        platform_stats = {}
        partner_stats = {}
        status_stats = {}
        
        for record in records:
            # 平台统计
            platform = record.get('Platform') or 'Unknown'
            if platform not in platform_stats:
                platform_stats[platform] = {'count': 0, 'sale_amount': 0}
            platform_stats[platform]['count'] += 1
            platform_stats[platform]['sale_amount'] += safe_float(record.get('Sale Amount'))
            
            # 合作伙伴统计
            partner = record.get('Partner') or 'Unknown'
            if partner not in partner_stats:
                partner_stats[partner] = {'count': 0, 'sale_amount': 0}
            partner_stats[partner]['count'] += 1
            partner_stats[partner]['sale_amount'] += safe_float(record.get('Sale Amount'))
            
            # 状态统计
            status = record.get('Conversion Status') or 'Unknown'
            if status not in status_stats:
                status_stats[status] = 0
            status_stats[status] += 1
        
        conversion_data['summary'] = {
            'total_conversions': total_conversions,
            'total_sale_amount': safe_float(total_sale_amount),
            'avg_commission_rate': safe_float(avg_commission_rate),
            'page_records': len(records),
            'page_sale_amount': page_sale_amount,
            'page_payout': page_payout,
            'page_usd_sale': page_usd_sale,
            'page_usd_payout': page_usd_payout,
            'avg_page_sale': page_sale_amount / len(records) if records else 0,
            'avg_page_payout': page_payout / len(records) if records else 0,
            'platform_distribution': platform_stats,
            'partner_distribution': partner_stats,
            'status_distribution': status_stats
        }
        
        return conversion_data

    # =============================================================================
    # 过滤器和配置数据服务
    # =============================================================================
    
    async def get_filter_options(self) -> Dict[str, Any]:
        """获取过滤器选项"""
        try:
            # 并行获取所有过滤器选项
            partners_task = self.db_manager.get_effective_partners()  # 使用基于实际数据的partners
            platforms_task = self.db_manager.get_platforms()
            
            partners, platforms = await asyncio.gather(partners_task, platforms_task)
            
            return {
                "partners": partners,
                "platforms": platforms,
                "date_ranges": self._get_date_range_options(),
                "time_zones": ["UTC", "Asia/Singapore", "Asia/Jakarta"]
            }
        except Exception as e:
            logger.error(f"获取过滤器选项失败: {e}")
            return {}
    
    async def get_enhanced_filter_options(self) -> Dict[str, Any]:
        """获取增强版过滤器选项 - 使用新的数据库字段"""
        try:
            # 获取基于新字段的合作伙伴列表
            partners = await self.db_manager.get_enhanced_partners()
            platforms = await self.db_manager.get_platforms()
            
            return {
                "partners": partners,
                "platforms": platforms,
                "date_ranges": self._get_date_range_options(),
                "time_zones": ["UTC", "Asia/Singapore", "Asia/Jakarta"]
            }
        except Exception as e:
            logger.error(f"获取增强版过滤器选项失败: {e}")
            return {
                "partners": [{"partner_name": "All Partners", "conversion_count": 0}],
                "platforms": [],
                "date_ranges": self._get_date_range_options(),
                "time_zones": ["UTC", "Asia/Singapore", "Asia/Jakarta"]
            }
    
    def _get_date_range_options(self) -> List[Dict[str, Any]]:
        """获取日期范围选项"""
        today = datetime.now()
        
        return [
            {
                "label": "今天",
                "value": "today",
                "start_date": today.strftime('%Y-%m-%d'),
                "end_date": today.strftime('%Y-%m-%d')
            },
            {
                "label": "昨天",
                "value": "yesterday",
                "start_date": (today - timedelta(days=1)).strftime('%Y-%m-%d'),
                "end_date": (today - timedelta(days=1)).strftime('%Y-%m-%d')
            },
            {
                "label": "最近7天",
                "value": "last_7_days",
                "start_date": (today - timedelta(days=7)).strftime('%Y-%m-%d'),
                "end_date": today.strftime('%Y-%m-%d')
            },
            {
                "label": "最近30天",
                "value": "last_30_days",
                "start_date": (today - timedelta(days=30)).strftime('%Y-%m-%d'),
                "end_date": today.strftime('%Y-%m-%d')
            },
            {
                "label": "本月",
                "value": "this_month",
                "start_date": today.replace(day=1).strftime('%Y-%m-%d'),
                "end_date": today.strftime('%Y-%m-%d')
            },
            {
                "label": "上月",
                "value": "last_month",
                "start_date": (today.replace(day=1) - timedelta(days=1)).replace(day=1).strftime('%Y-%m-%d'),
                "end_date": (today.replace(day=1) - timedelta(days=1)).strftime('%Y-%m-%d')
            }
        ]
    
    # =============================================================================
    # 数据钻取服务
    # =============================================================================
    
    async def drill_data(self, data_type: str, filter_key: str, filter_value: str,
                        start_date: str, end_date: str) -> Dict[str, Any]:
        """数据钻取服务"""
        try:
            drill_result = await self.db_manager.drill_down_data(
                data_type, filter_key, filter_value, start_date, end_date
            )
            
            return {
                "drill_type": data_type,
                "filter": {
                    "key": filter_key,
                    "value": filter_value
                },
                "results": drill_result,
                "summary": self._calculate_drill_summary(drill_result)
            }
        except Exception as e:
            logger.error(f"数据钻取失败: {e}")
            return {}
    
    def _calculate_drill_summary(self, drill_result: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算钻取数据摘要"""
        if not drill_result:
            return {}
        
        total_conversions = sum(item.get('conversions', 0) for item in drill_result)
        total_sales = sum(item.get('total_sales', 0) for item in drill_result)
        
        return {
            "total_items": len(drill_result),
            "total_conversions": total_conversions,
            "total_sales": total_sales,
            "avg_conversions_per_item": total_conversions / len(drill_result) if drill_result else 0
        } 