#!/usr/bin/env python3
"""
IA_BM数据处理器测试文件
测试IA_BM文件检测、字段映射、数据清理和输出格式
"""

import unittest
import pandas as pd
import tempfile
import os
from pathlib import Path
import sys

# 添加项目根目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from agents.data_dmp_agent.ia_bm_data_processor import IABMDataProcessor

class TestIABMDataProcessor(unittest.TestCase):
    """IA_BM数据处理器测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.processor = IABMDataProcessor()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_is_ia_bm_file(self):
        """测试IA_BM文件检测"""
        # 测试正确的IA_BM文件名
        self.assertTrue(self.processor.is_ia_bm_file("report_IA_BM_20250101.csv"))
        self.assertTrue(self.processor.is_ia_bm_file("data_ia_bm_latest.xlsx"))
        self.assertTrue(self.processor.is_ia_bm_file("IA_BM_export.csv"))
        
        # 测试非IA_BM文件名
        self.assertFalse(self.processor.is_ia_bm_file("report_AT_BM_20250101.csv"))
        self.assertFalse(self.processor.is_ia_bm_file("shopee_data.csv"))
        self.assertFalse(self.processor.is_ia_bm_file("normal_report.xlsx"))
    
    def test_detect_platform_column(self):
        """测试platform列检测"""
        # 测试包含platform列的DataFrame
        df1 = pd.DataFrame({
            'platform': ['IA_BM', 'IA_BM'],
            'data': [1, 2]
        })
        self.assertEqual(self.processor.detect_platform_column(df1), 'platform')
        
        # 测试包含Platform列的DataFrame
        df2 = pd.DataFrame({
            'Platform': ['IA_BM', 'IA_BM'],
            'data': [1, 2]
        })
        self.assertEqual(self.processor.detect_platform_column(df2), 'Platform')
        
        # 测试包含中文平台列的DataFrame
        df3 = pd.DataFrame({
            '平台': ['IA_BM', 'IA_BM'],
            'data': [1, 2]
        })
        self.assertEqual(self.processor.detect_platform_column(df3), '平台')
        
        # 测试不包含platform列的DataFrame
        df4 = pd.DataFrame({
            'data': [1, 2],
            'value': [3, 4]
        })
        self.assertIsNone(self.processor.detect_platform_column(df4))
    
    def test_handle_merged_cells(self):
        """测试合并单元格处理"""
        # 创建包含空值的DataFrame模拟合并单元格
        df = pd.DataFrame({
            'platform': ['IA_BM', None, None, 'AT_BM', None],
            'data': [1, 2, 3, 4, 5]
        })
        
        result_df = self.processor.handle_merged_cells(df, 'platform')
        
        # 检查前向填充是否生效
        expected_platform = ['IA_BM', 'IA_BM', 'IA_BM', 'AT_BM', 'AT_BM']
        self.assertEqual(list(result_df['platform']), expected_platform)
    
    def test_filter_ia_bm_records(self):
        """测试IA_BM记录过滤"""
        df = pd.DataFrame({
            'platform': ['IA_BM', 'AT_BM', 'IA_BM', 'SHOPEE', 'involve_asia'],
            'data': [1, 2, 3, 4, 5]
        })
        
        filtered_df = self.processor.filter_ia_bm_records(df, 'platform')
        
        # 应该只保留IA_BM和involve_asia的记录
        expected_data = [1, 3, 5]
        self.assertEqual(list(filtered_df['data']), expected_data)
        self.assertEqual(len(filtered_df), 3)
    
    def test_clean_data(self):
        """测试数据清理"""
        # 创建包含脏数据的DataFrame
        df = pd.DataFrame({
            'platform': ['IA_BM', 'IA_BM'],
            'text_field': ['  spaced  ', 'normal'],
            'empty_field': [None, ''],
            'nan_field': ['nan', 'valid']
        })
        
        cleaned_df = self.processor.clean_data(df)
        
        # 检查空格是否被清理
        self.assertEqual(cleaned_df.loc[0, 'text_field'], 'spaced')
        
        # 检查platform字段是否设置为IA_BM
        self.assertTrue(all(cleaned_df['platform'] == 'IA_BM'))
        
        # 检查'nan'字符串是否转换为NaN
        self.assertTrue(pd.isna(cleaned_df.loc[0, 'nan_field']))
    
    def create_sample_ia_bm_csv(self, filename: str) -> str:
        """创建示例IA_BM CSV文件"""
        sample_data = {
            'Platform': ['IA_BM', 'IA_BM', 'IA_BM'],
            'Advertiser Name': ['Test Advertiser', 'Another Advertiser', 'Third Advertiser'],
            'Campaign Name': ['Campaign 1', 'Campaign 2', 'Campaign 3'],
            'Offer Name': ['Product A', 'Product B', 'Product C'],
            'Sale Amount (USD)': [100.50, 250.75, 75.25],
            'Conversion Date': ['2025-01-01', '2025-01-02', '2025-01-03'],
            'Currency': ['USD', 'USD', 'USD']
        }
        
        df = pd.DataFrame(sample_data)
        file_path = os.path.join(self.temp_dir, filename)
        df.to_csv(file_path, index=False)
        return file_path
    
    def test_process_ia_bm_file_success(self):
        """测试成功处理IA_BM文件"""
        # 创建示例文件
        test_file = self.create_sample_ia_bm_csv("test_ia_bm_file.csv")
        
        # 处理文件
        result = self.processor.process_ia_bm_file(test_file, self.temp_dir)
        
        # 验证结果
        self.assertTrue(result['success'])
        self.assertEqual(result['records_processed'], 3)
        self.assertTrue(os.path.exists(result['output_file']))
        
        # 验证输出文件内容
        output_df = pd.read_csv(result['output_file'])
        self.assertGreater(len(output_df.columns), 10)  # 应该有unified fields
    
    def test_process_non_ia_bm_file(self):
        """测试处理非IA_BM文件"""
        # 创建非IA_BM文件
        non_ia_bm_file = os.path.join(self.temp_dir, "at_bm_file.csv")
        pd.DataFrame({'data': [1, 2, 3]}).to_csv(non_ia_bm_file, index=False)
        
        # 处理文件应该失败
        result = self.processor.process_ia_bm_file(non_ia_bm_file, self.temp_dir)
        
        self.assertFalse(result['success'])
        self.assertIn('不是IA_BM文件', result['error'])

if __name__ == '__main__':
    # 设置日志
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # 运行测试
    unittest.main()