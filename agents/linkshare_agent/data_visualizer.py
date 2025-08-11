#!/usr/bin/env python3
"""
Search Affiliate Orders API 数据可视化模块
将API响应数据转换为CSV和Excel格式
"""

import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

logger = logging.getLogger(__name__)

class DataVisualizer:
    """数据可视化类"""
    
    def __init__(self, output_dir: str = "output"):
        """
        初始化数据可视化器
        
        Args:
            output_dir: 输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        logger.info(f"🔧 DataVisualizer 初始化完成，输出目录: {self.output_dir}")
    
    def _format_timestamp(self, timestamp: Optional[int]) -> str:
        """
        格式化时间戳
        
        Args:
            timestamp: Unix时间戳
            
        Returns:
            格式化的时间字符串
        """
        if timestamp is None:
            return "N/A"
        
        try:
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, OSError):
            return f"Invalid timestamp: {timestamp}"
    
    def _format_amount(self, amount: Optional[Union[int, float]]) -> str:
        """
        格式化金额
        
        Args:
            amount: 金额数值
            
        Returns:
            格式化的金额字符串
        """
        if amount is None:
            return "0.00"
        
        try:
            return f"{float(amount):.2f}"
        except (ValueError, TypeError):
            return "0.00"
    
    def _flatten_order_data(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """
        扁平化订单数据
        
        Args:
            order: 原始订单数据
            
        Returns:
            扁平化的订单数据
        """
        flattened = {}
        
        # 基本信息
        flattened['订单ID'] = order.get('orderId', 'N/A')
        flattened['订单状态'] = order.get('status', 'N/A')
        flattened['创建时间'] = self._format_timestamp(order.get('createTime'))
        flattened['更新时间'] = self._format_timestamp(order.get('updateTime'))
        
        # 金额信息
        flattened['订单金额'] = self._format_amount(order.get('orderAmount'))
        flattened['佣金金额'] = self._format_amount(order.get('commissionAmount'))
        flattened['佣金率'] = f"{order.get('commissionRate', 0):.2f}%"
        
        # 产品信息
        product = order.get('product', {})
        flattened['产品ID'] = product.get('productId', 'N/A')
        flattened['产品名称'] = product.get('productName', 'N/A')
        flattened['产品价格'] = self._format_amount(product.get('price'))
        flattened['产品数量'] = product.get('quantity', 0)
        
        # 活动信息
        campaign = order.get('campaign', {})
        flattened['活动ID'] = campaign.get('campaignId', 'N/A')
        flattened['活动名称'] = campaign.get('campaignName', 'N/A')
        
        # 用户信息
        user = order.get('user', {})
        flattened['用户ID'] = user.get('userId', 'N/A')
        flattened['用户名'] = user.get('userName', 'N/A')
        
        # 其他信息
        flattened['订单来源'] = order.get('orderSource', 'N/A')
        flattened['支付方式'] = order.get('paymentMethod', 'N/A')
        flattened['备注'] = order.get('remark', '')
        
        return flattened
    
    def _get_csv_headers(self) -> List[str]:
        """
        获取CSV表头
        
        Returns:
            CSV表头列表
        """
        return [
            '订单ID', '订单状态', '创建时间', '更新时间',
            '订单金额', '佣金金额', '佣金率',
            '产品ID', '产品名称', '产品价格', '产品数量',
            '活动ID', '活动名称',
            '用户ID', '用户名',
            '订单来源', '支付方式', '备注'
        ]
    
    def _create_summary_data(self, orders: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        创建汇总数据
        
        Args:
            orders: 订单列表
            
        Returns:
            汇总数据字典
        """
        if not orders:
            return {
                '总订单数': 0,
                '总金额': '0.00',
                '总佣金': '0.00',
                '平均佣金率': '0.00%',
                '状态分布': {},
                '活动分布': {},
                '时间分布': {}
            }
        
        # 基础统计
        total_orders = len(orders)
        total_amount = sum(float(order.get('orderAmount', 0)) for order in orders)
        total_commission = sum(float(order.get('commissionAmount', 0)) for order in orders)
        avg_commission_rate = (total_commission / total_amount * 100) if total_amount > 0 else 0
        
        # 状态分布
        status_distribution = {}
        for order in orders:
            status = order.get('status', 'Unknown')
            status_distribution[status] = status_distribution.get(status, 0) + 1
        
        # 活动分布
        campaign_distribution = {}
        for order in orders:
            campaign_name = order.get('campaign', {}).get('campaignName', 'Unknown')
            campaign_distribution[campaign_name] = campaign_distribution.get(campaign_name, 0) + 1
        
        # 时间分布（按天）
        time_distribution = {}
        for order in orders:
            create_time = order.get('createTime')
            if create_time:
                try:
                    date_str = datetime.fromtimestamp(create_time).strftime("%Y-%m-%d")
                    time_distribution[date_str] = time_distribution.get(date_str, 0) + 1
                except (ValueError, OSError):
                    pass
        
        return {
            '总订单数': total_orders,
            '总金额': f"{total_amount:.2f}",
            '总佣金': f"{total_commission:.2f}",
            '平均佣金率': f"{avg_commission_rate:.2f}%",
            '状态分布': status_distribution,
            '活动分布': campaign_distribution,
            '时间分布': time_distribution
        }
    
    def export_to_csv(self, api_response: Dict[str, Any], filename: Optional[str] = None) -> str:
        """
        导出数据到CSV文件
        
        Args:
            api_response: API响应数据
            filename: 文件名（可选）
            
        Returns:
            输出文件路径
        """
        if not api_response.get("success"):
            logger.error(f"❌ API响应失败，无法导出数据: {api_response.get('error')}")
            raise ValueError(f"API响应失败: {api_response.get('error')}")
        
        orders = api_response.get("orders", [])
        if not orders:
            logger.warning("⚠️ 没有订单数据可导出")
            return ""
        
        # 生成文件名
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"affiliate_orders_{timestamp}.csv"
        
        filepath = self.output_dir / filename
        
        # 扁平化数据
        flattened_orders = [self._flatten_order_data(order) for order in orders]
        
        # 写入CSV
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
            fieldnames = self._get_csv_headers()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for order in flattened_orders:
                writer.writerow(order)
        
        logger.info(f"✅ CSV文件导出成功: {filepath}")
        logger.info(f"📊 导出了 {len(orders)} 条订单记录")
        
        return str(filepath)
    
    def export_to_json(self, api_response: Dict[str, Any], filename: Optional[str] = None) -> str:
        """
        导出数据到JSON文件
        
        Args:
            api_response: API响应数据
            filename: 文件名（可选）
            
        Returns:
            输出文件路径
        """
        if not api_response.get("success"):
            logger.error(f"❌ API响应失败，无法导出数据: {api_response.get('error')}")
            raise ValueError(f"API响应失败: {api_response.get('error')}")
        
        # 生成文件名
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"affiliate_orders_{timestamp}.json"
        
        filepath = self.output_dir / filename
        
        # 写入JSON
        with open(filepath, 'w', encoding='utf-8') as jsonfile:
            json.dump(api_response, jsonfile, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ JSON文件导出成功: {filepath}")
        
        return str(filepath)
    
    def create_visualization_report(self, api_response: Dict[str, Any], 
                                  formats: List[str] = None) -> Dict[str, str]:
        """
        创建可视化报告
        
        Args:
            api_response: API响应数据
            formats: 输出格式列表，支持 ['csv', 'json']
            
        Returns:
            输出文件路径字典
        """
        if formats is None:
            formats = ['csv']
        
        output_files = {}
        
        for format_type in formats:
            try:
                if format_type.lower() == 'csv':
                    output_files['csv'] = self.export_to_csv(api_response)
                elif format_type.lower() == 'json':
                    output_files['json'] = self.export_to_json(api_response)
                else:
                    logger.warning(f"⚠️ 不支持的格式: {format_type}")
            except Exception as e:
                logger.error(f"❌ 导出 {format_type} 格式失败: {e}")
        
        logger.info(f"📊 可视化报告创建完成，输出文件: {list(output_files.keys())}")
        return output_files

# 便捷函数
def export_orders_to_csv(api_response: Dict[str, Any], output_dir: str = "output") -> str:
    """
    导出订单数据到CSV文件
    
    Args:
        api_response: API响应数据
        output_dir: 输出目录
        
    Returns:
        输出文件路径
    """
    visualizer = DataVisualizer(output_dir)
    return visualizer.export_to_csv(api_response)

def create_orders_report(api_response: Dict[str, Any], 
                        output_dir: str = "output",
                        formats: List[str] = None) -> Dict[str, str]:
    """
    创建订单报告
    
    Args:
        api_response: API响应数据
        output_dir: 输出目录
        formats: 输出格式列表
        
    Returns:
        输出文件路径字典
    """
    visualizer = DataVisualizer(output_dir)
    return visualizer.create_visualization_report(api_response, formats) 