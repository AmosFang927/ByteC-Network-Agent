#!/usr/bin/env python3
"""
LS_BM数据处理器的单元测试
"""

import unittest
import pandas as pd
import os
from pathlib import Path
from datetime import datetime
from ..ls_bm_data_processor import LSBMDataProcessor

class TestLSBMDataProcessor(unittest.TestCase):
    """LS_BM数据处理器测试类"""
    
    def setUp(self):
        """测试前的准备工作"""
        self.processor = LSBMDataProcessor()
        self.test_data_dir = Path("tests/test_data")
        self.test_data_dir.mkdir(parents=True, exist_ok=True)
    
    def tearDown(self):
        """测试后的清理工作"""
        # 清理测试生成的文件
        for test_file in self.test_data_dir.glob("*"):
            if test_file.is_file():
                test_file.unlink()
        if self.test_data_dir.exists():
            self.test_data_dir.rmdir()
    
    def test_is_ls_bm_file(self):
        """测试文件类型检测"""
        self.assertTrue(self.processor.is_ls_bm_file("test_ls_bm_data.csv"))
        self.assertTrue(self.processor.is_ls_bm_file("LS_BM_report.xlsx"))
        self.assertFalse(self.processor.is_ls_bm_file("at_bm_data.csv"))
    
    def test_platform_detection(self):
        """测试平台列检测"""
        df = pd.DataFrame({
            'platform': ['LS_BM', 'LinkShare'],
            'data': [1, 2]
        })
        self.assertEqual(self.processor.detect_platform_column(df), 'platform')
        
        df = pd.DataFrame({
            'Platform': ['LS_BM', 'LinkShare'],
            'data': [1, 2]
        })
        self.assertEqual(self.processor.detect_platform_column(df), 'Platform')
        
        df = pd.DataFrame({
            'data': [1, 2]
        })
        self.assertIsNone(self.processor.detect_platform_column(df))
    
    def test_merged_cells_handling(self):
        """测试合并单元格处理"""
        df = pd.DataFrame({
            'platform': ['LS_BM', None, None, 'LinkShare', None],
            'data': [1, 2, 3, 4, 5]
        })
        result = self.processor.handle_merged_cells(df, 'platform')
        self.assertFalse(result['platform'].isna().any())
        self.assertEqual(result['platform'].iloc[1], 'LS_BM')
        self.assertEqual(result['platform'].iloc[2], 'LS_BM')
    
    def test_field_mapping(self):
        """测试字段映射"""
        test_data = pd.DataFrame({
            'Shop name': ['Shop A', 'Shop B'],
            'Content Type': ['Type A', 'Type B'],
            'Product Name': ['Product A', 'Product B'],
            'Actual standard commission': [100, 200],
            'Time order created': ['2024-03-20 10:00:00', '2024-03-20 11:00:00'],
            'Currency': ['USD', 'USD'],
            'Creator username': ['user1', 'user2']
        })
        
        mapped_df, mapping_info = self.processor.apply_field_mapping(test_data)
        
        # 验证字段映射是否正确
        self.assertIn('advertiser_name', mapped_df.columns)
        self.assertIn('campaign_name', mapped_df.columns)
        self.assertIn('offer_name', mapped_df.columns)
        self.assertIn('conversion_amount', mapped_df.columns)
        self.assertIn('conversion_date', mapped_df.columns)
        self.assertIn('currency', mapped_df.columns)
        self.assertIn('publisher_id', mapped_df.columns)
        
        # 验证数据转换是否正确
        self.assertEqual(mapped_df['advertiser_name'].iloc[0], 'Shop A')
        self.assertEqual(mapped_df['campaign_name'].iloc[0], 'Type A')
        self.assertEqual(mapped_df['conversion_amount'].iloc[0], 100)
    
    def test_data_cleaning(self):
        """测试数据清理"""
        df = pd.DataFrame({
            'col1': [' test ', 'nan', '  '],
            'col2': [1, 2, None],
            'platform': ['LS_BM', None, 'LinkShare']
        })
        
        cleaned = self.processor.clean_data(df)
        
        # 验证空格清理
        self.assertEqual(cleaned['col1'].iloc[0], 'test')
        
        # 验证nan处理
        self.assertTrue(pd.isna(cleaned['col1'].iloc[1]))
        
        # 验证platform统一
        self.assertTrue(all(cleaned['platform'] == 'LS_BM'))
    
    def test_full_processing(self):
        """测试完整处理流程"""
        # 创建测试文件
        test_file = self.test_data_dir / "test_ls_bm.csv"
        test_data = pd.DataFrame({
            'Shop name': ['Shop A', 'Shop B'],
            'Content Type': ['Type A', 'Type B'],
            'Product Name': ['Product A', 'Product B'],
            'Actual standard commission': [100, 200],
            'Time order created': ['2024-03-20 10:00:00', '2024-03-20 11:00:00'],
            'Currency': ['USD', 'USD'],
            'Creator username': ['user1', 'user2'],
            'platform': ['LS_BM', 'LS_BM']
        })
        test_data.to_csv(test_file, index=False)
        
        # 处理文件
        result = self.processor.process_ls_bm_file(str(test_file))
        
        # 验证处理结果
        self.assertTrue(result['success'])
        self.assertEqual(result['stats']['total_records'], 2)
        self.assertEqual(result['stats']['processed_records'], 2)
        self.assertTrue(os.path.exists(result['output_file']))
        
        # 验证输出文件格式
        output_df = pd.read_csv(result['output_file'])
        self.assertIn('advertiser_name', output_df.columns)
        self.assertIn('campaign_name', output_df.columns)
        self.assertIn('offer_name', output_df.columns)
        self.assertIn('conversion_amount', output_df.columns)
        self.assertIn('conversion_date', output_df.columns)
        self.assertIn('currency', output_df.columns)
        self.assertIn('publisher_id', output_df.columns)
        
        # 验证数据正确性
        self.assertEqual(output_df['advertiser_name'].iloc[0], 'Shop A')
        self.assertEqual(output_df['campaign_name'].iloc[0], 'Type A')
        self.assertEqual(output_df['conversion_amount'].iloc[0], 100)
    
    def test_error_handling(self):
        """测试错误处理"""
        # 测试不存在的文件
        result = self.processor.process_ls_bm_file("non_existent_file.csv")
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        
        # 测试无效的文件格式
        test_file = self.test_data_dir / "test_ls_bm.txt"
        test_file.touch()
        result = self.processor.process_ls_bm_file(str(test_file))
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        
        # 测试空文件
        empty_file = self.test_data_dir / "empty_ls_bm.csv"
        pd.DataFrame().to_csv(empty_file, index=False)
        result = self.processor.process_ls_bm_file(str(empty_file))
        self.assertFalse(result['success'])
        self.assertEqual(result['stats']['total_records'], 0)

if __name__ == '__main__':
    unittest.main()
