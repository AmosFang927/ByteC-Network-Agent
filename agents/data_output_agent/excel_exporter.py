#!/usr/bin/env python3
"""
JSON到Excel转换模块
负责将JSON格式的conversion数据转换为Excel文件
"""

import json
import pandas as pd
import os
from utils.logger import print_step
import config
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows

class JSONToExcelConverter:
    """JSON到Excel转换器"""
    
    def __init__(self):
        pass
    
    def convert(self, json_data, output_filename=None):
        """
        将JSON数据转换为Excel文件
        
        Args:
            json_data: JSON数据（可以是字符串、字典或文件路径）
            output_filename: 输出文件名，如果为None则自动生成
        
        Returns:
            str: 生成的Excel文件路径
        """
        print_step("开始转换", "正在将JSON数据转换为Excel格式...")
        
        # 处理输入数据
        data = self._process_input(json_data)
        
        # 验证数据结构
        conversion_records = self._validate_and_extract(data)
        
        # 转换为DataFrame
        df = self._create_dataframe(conversion_records)
        
        # 生成输出文件名
        output_path = self._generate_output_path(output_filename)
        
        # 导出Excel
        return self._export_to_excel(df, data, output_path)
    
    def _process_input(self, json_data):
        """处理输入数据，支持多种格式"""
        if isinstance(json_data, str):
            # 检查是否是文件路径
            if os.path.isfile(json_data):
                print_step("数据加载", f"从文件加载JSON数据: {json_data}")
                try:
                    with open(json_data, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except Exception as e:
                    raise ValueError(f"无法读取JSON文件: {str(e)}")
            else:
                # 尝试解析JSON字符串
                try:
                    return json.loads(json_data)
                except json.JSONDecodeError as e:
                    raise ValueError(f"JSON解析失败: {str(e)}")
        else:
            return json_data
    
    def _validate_and_extract(self, data):
        """验证JSON结构并提取转换记录"""
        print_step("数据验证", "正在验证JSON数据结构...")
        
        # 验证基本结构
        if not isinstance(data, dict):
            raise ValueError("JSON数据必须是字典格式")
        
        if 'data' not in data:
            raise ValueError("JSON结构不正确，缺少'data'字段")
        
        if not isinstance(data['data'], dict) or 'data' not in data['data']:
            raise ValueError("JSON结构不正确，缺少'data.data'字段")
        
        # 提取转换记录数组
        conversion_records = data['data']['data']
        
        if not isinstance(conversion_records, list):
            raise ValueError("转换记录数据必须是数组格式")
        
        if not conversion_records:
            print_step("数据警告", "没有找到转换记录数据，将创建空的Excel文件")
            conversion_records = []
        else:
            print_step("数据验证完成", f"找到 {len(conversion_records)} 条转换记录")
        
        return conversion_records
    
    def _create_dataframe(self, conversion_records):
        """创建pandas DataFrame"""
        print_step("数据转换", f"正在创建DataFrame，包含 {len(conversion_records)} 条记录...")
        
        df = pd.DataFrame(conversion_records)
        
        if len(df) > 0:
            print_step("DataFrame创建", f"DataFrame包含 {len(df)} 行，{len(df.columns)} 列")
            print_step("列信息", f"列名: {list(df.columns)}")
        else:
            print_step("DataFrame创建", "创建了空的DataFrame")
        
        return df
    
    def _generate_output_path(self, output_filename):
        """生成输出文件路径"""
        if output_filename is None:
            output_filename = config.get_output_filename()
        
        # 确保文件扩展名为.xlsx
        if not output_filename.endswith('.xlsx'):
            output_filename += '.xlsx'
        
        # 确保输出目录存在
        config.ensure_output_dirs()
        
        # 生成完整路径
        output_path = os.path.join(config.OUTPUT_DIR, output_filename)
        return output_path
    
    def _export_to_excel(self, df, original_data, output_path):
        """导出DataFrame到Excel文件"""
        print_step("文件导出", f"正在导出Excel文件: {output_path}")
        
        try:
            # 使用自定义方法导出并设置货币格式
            self._export_excel_with_currency_format(df, output_path)
            
            # 输出成功信息
            print_step("导出成功", f"成功转换 {len(df)} 条记录到 {output_path}")
            
            # 输出数据概览
            self._print_conversion_summary(df, original_data, output_path)
            
            return output_path
            
        except Exception as e:
            raise RuntimeError(f"导出Excel文件失败: {str(e)}")
    
    def _export_excel_with_currency_format(self, data, filepath):
        """
        导出Excel并为所有数字字段设置千分位格式
        
        Args:
            data: 要导出的DataFrame
            filepath: 输出文件路径
        """
        # 创建工作簿和工作表
        wb = Workbook()
        ws = wb.active
        ws.title = 'Data'
        
        # 写入数据（包含标题行），清理特殊字符
        for r in dataframe_to_rows(data, index=False, header=True):
            # 清理行中的特殊字符
            cleaned_row = self._clean_row_data(r)
            ws.append(cleaned_row)
        
        # 为所有数字字段设置千分位格式
        self._apply_number_formatting(ws, data)
        
        # 保存文件
        wb.save(filepath)
    
    def _apply_number_formatting(self, worksheet, data):
        """
        为Excel工作表中的所有数字字段应用千分位格式
        
        Args:
            worksheet: Excel工作表对象
            data: DataFrame数据
        """
        format_count = 0
        
        # 定义字段格式映射
        number_format_mapping = {
            # 金额字段 - 美元格式，千分位，两位小数
            'sale_amount': '"$"#,##0.00',
            'estimated_earning': '"$"#,##0.00',
            'adv_commission': '"$"#,##0.00',
            'pub_commission': '"$"#,##0.00',
            'bytec_commission': '"$"#,##0.00',
            'payout': '"$"#,##0.00',
            'base_payout': '"$"#,##0.00',
            'bonus_payout': '"$"#,##0.00',
            
            # 整数字段 - 千分位，无小数
            'conversion_id': '#,##0',
            'click_id': '#,##0',
            'transaction_id': '#,##0',
            'advertiser_id': '#,##0',
            'publisher_id': '#,##0',
            'offer_id': '#,##0',
            'campaign_id': '#,##0',
            'count': '#,##0',
            'clicks': '#,##0',
            'conversions': '#,##0',
            
            # 小数字段 - 千分位，两位小数
            'conversion_rate': '#,##0.00',
            'commission_rate': '#,##0.00',
            'price': '#,##0.00',
            'value': '#,##0.00',
            
            # 百分比字段 - 百分比格式
            'roi': '0.00%',
            'bytec_roi': '0.00%',
            'commission_percentage': '0.00%',
            'discount_rate': '0.00%'
        }
        
        # 遍历所有列，应用格式
        for col_name in data.columns:
            if col_name in number_format_mapping:
                col_index = data.columns.get_loc(col_name) + 1  # Excel列索引从1开始
                number_format = number_format_mapping[col_name]
                
                # 应用格式到该列的所有数据行（跳过标题行）
                for row in range(2, len(data) + 2):  # 从第2行开始（第1行是标题）
                    cell = worksheet.cell(row=row, column=col_index)
                    cell.number_format = number_format
                
                format_count += 1
                print_step("数字格式", f"已为 {col_name} 字段设置千分位格式: {number_format}")
        
        print_step("格式化完成", f"✅ 成功为 {format_count} 个数字字段设置千分位格式")
    
    def _clean_row_data(self, row):
        """
        清理行数据中的特殊字符，确保Excel兼容性
        
        Args:
            row: 数据行（列表或元组）
            
        Returns:
            list: 清理后的数据行
        """
        import re
        
        cleaned_row = []
        for cell in row:
            if cell is None:
                cleaned_row.append(None)
            elif isinstance(cell, (int, float)):
                # 数字类型直接保留
                cleaned_row.append(cell)
            else:
                # 字符串类型需要清理
                cell_str = str(cell)
                
                # 移除可能导致Excel问题的控制字符和特殊Unicode字符
                # 保留基本的ASCII字符、常见Unicode字符
                cleaned_str = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', cell_str)
                
                # 移除可能有问题的Unicode字符（保留基本字母、数字、常见符号）
                # 这个正则表达式比较宽松，保留大部分字符但移除控制字符
                cleaned_str = re.sub(r'[^\x20-\x7E\u00A0-\u024F\u1E00-\u1EFF\u2000-\u206F\u20A0-\u20CF\u2100-\u214F]', '_', cleaned_str)
                
                # 移除开头的特殊字符（如不可见字符）
                cleaned_str = cleaned_str.strip()
                
                cleaned_row.append(cleaned_str)
        
        return cleaned_row
    
    def _print_conversion_summary(self, df, original_data, output_path):
        """打印转换结果摘要"""
        print_step("转换摘要", "数据转换完成，详细信息如下:")
        
        print(f"📊 数据概览:")
        print(f"   - 状态: {original_data.get('status', 'N/A')}")
        print(f"   - 消息: {original_data.get('message', 'N/A')}")
        
        data_info = original_data.get('data', {})
        print(f"   - 总记录数: {data_info.get('count', 'N/A')}")
        print(f"   - 当前页: {data_info.get('page', 'N/A')}")
        print(f"   - 每页限制: {data_info.get('limit', 'N/A')}")
        print(f"   - 获取页数: {data_info.get('pages_fetched', 'N/A')}")
        
        print(f"📄 Excel文件信息:")
        print(f"   - 文件路径: {output_path}")
        print(f"   - 工作表名: {config.EXCEL_SHEET_NAME}")
        print(f"   - 行数: {len(df)}")
        print(f"   - 列数: {len(df.columns)}")
        
        if len(df) > 0:
            print(f"   - 列名: {', '.join(df.columns)}")
        
        # 输出文件大小
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"   - 文件大小: {file_size:,} bytes")

# 便捷函数
def json_to_excel(json_data, output_filename=None):
    """
    便捷的转换函数
    
    Args:
        json_data: JSON数据（可以是字符串、字典或文件路径）
        output_filename: 输出文件名
    
    Returns:
        str: 生成的Excel文件路径
    """
    converter = JSONToExcelConverter()
    return converter.convert(json_data, output_filename) 