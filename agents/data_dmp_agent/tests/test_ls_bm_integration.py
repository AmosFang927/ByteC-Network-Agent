#!/usr/bin/env python3
"""
LS_BM数据处理器的集成测试
测试与reporter agent的格式兼容性
"""

import unittest
import pandas as pd
import os
from pathlib import Path
from datetime import datetime
from ..ls_bm_data_processor import LSBMDataProcessor
from ..main import DMPAgent

class TestLSBMIntegration(unittest.TestCase):
    """LS_BM集成测试类"""
    
    def setUp(self):
        """测试前的准备工作"""
        self.dmp_agent = DMPAgent()
        self.test_data_dir = Path("tests/test_data")
        self.test_data_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建测试数据
        self.create_test_data()
    
    def tearDown(self):
        """测试后的清理工作"""
        # 清理测试生成的文件
        for test_file in self.test_data_dir.glob("*"):
            if test_file.is_file():
                test_file.unlink()
        if self.test_data_dir.exists():
            self.test_data_dir.rmdir()
    
    def create_test_data(self):
        """创建测试数据文件"""
        # 创建LS_BM测试文件
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
    
    async def test_dmp_agent_processing(self):
        """测试DMP Agent处理LS_BM文件"""
        test_file = str(self.test_data_dir / "test_ls_bm.csv")
        
        # 使用DMP Agent处理文件
        result = await self.dmp_agent.process_file_data(test_file)
        
        # 验证处理结果
        self.assertTrue(result['success'])
        self.assertEqual(result['platform'], 'LS_BM')
        self.assertTrue(result['records_count'] > 0)
        self.assertIsNotNone(result['processed_data'])
        
        # 验证输出文件格式
        output_file = result['processed_data']
        self.assertTrue(os.path.exists(output_file))
        
        output_df = pd.read_csv(output_file)
        
        # 验证必要字段
        required_fields = [
            'advertiser_name',
            'campaign_name',
            'offer_name',
            'conversion_amount',
            'conversion_date',
            'currency',
            'publisher_id',
            'platform'
        ]
        
        for field in required_fields:
            self.assertIn(field, output_df.columns)
        
        # 验证数据类型
        self.assertTrue(pd.api.types.is_numeric_dtype(output_df['conversion_amount']))
        self.assertTrue(pd.to_datetime(output_df['conversion_date']).notnull().all())
        
        # 验证platform字段
        self.assertTrue(all(output_df['platform'] == 'LS_BM'))
    
    async def test_multiple_files_processing(self):
        """测试多文件处理"""
        # 创建多个测试文件
        files = []
        for i in range(2):
            test_file = self.test_data_dir / f"test_ls_bm_{i}.csv"
            test_data = pd.DataFrame({
                'Shop name': [f'Shop {i}A', f'Shop {i}B'],
                'Content Type': [f'Type {i}A', f'Type {i}B'],
                'Product Name': [f'Product {i}A', f'Product {i}B'],
                'Actual standard commission': [100 * (i+1), 200 * (i+1)],
                'Time order created': ['2024-03-20 10:00:00', '2024-03-20 11:00:00'],
                'Currency': ['USD', 'USD'],
                'Creator username': [f'user{i}1', f'user{i}2'],
                'platform': ['LS_BM', 'LS_BM']
            })
            test_data.to_csv(test_file, index=False)
            files.append(str(test_file))
        
        # 使用DMP Agent处理多个文件
        result = await self.dmp_agent.process_multiple_files(files)
        
        # 验证处理结果
        self.assertTrue(result['individual_results'])
        self.assertTrue(result['merged_data'])
        self.assertEqual(result['total_records'], 4)  # 2文件 × 2记录
        
        # 验证合并文件
        self.assertTrue(os.path.exists(result['merged_filename']))
        merged_df = pd.read_csv(result['merged_filename'])
        
        # 验证数据合并正确性
        self.assertEqual(len(merged_df), 4)
        self.assertTrue(all(merged_df['platform'] == 'LS_BM'))
    
    async def test_reporter_agent_compatibility(self):
        """测试与Reporter Agent格式的兼容性"""
        test_file = str(self.test_data_dir / "test_ls_bm.csv")
        
        # 处理文件
        result = await self.dmp_agent.process_file_data(test_file)
        
        # 验证输出文件
        output_file = result['processed_data']
        output_df = pd.read_csv(output_file)
        
        # Reporter Agent所需字段
        reporter_fields = [
            'advertiser_name',
            'campaign_name',
            'offer_name',
            'conversion_amount',
            'conversion_date',
            'currency',
            'publisher_id',
            'platform',
            'source_file',
            'processed_date'
        ]
        
        # 验证所有必要字段都存在
        for field in reporter_fields:
            self.assertIn(field, output_df.columns)
        
        # 验证字段格式
        self.assertTrue(pd.api.types.is_numeric_dtype(output_df['conversion_amount']))
        self.assertTrue(pd.to_datetime(output_df['conversion_date']).notnull().all())
        self.assertTrue(pd.to_datetime(output_df['processed_date']).notnull().all())
        
        # 验证source_file字段
        self.assertTrue(all(output_df['source_file'].str.contains('test_ls_bm')))
    
    async def test_merged_cells_handling(self):
        """测试合并单元格处理的集成"""
        # 创建带有合并单元格效果的测试文件
        test_file = self.test_data_dir / "test_ls_bm_merged.csv"
        test_data = pd.DataFrame({
            'Shop name': ['Shop A', 'Shop A', 'Shop B', 'Shop B'],
            'Content Type': ['Type A', None, 'Type B', None],
            'Product Name': ['Product A', 'Product A2', 'Product B', 'Product B2'],
            'Actual standard commission': [100, 150, 200, 250],
            'Time order created': ['2024-03-20 10:00:00'] * 4,
            'Currency': ['USD'] * 4,
            'Creator username': ['user1'] * 4,
            'platform': ['LS_BM', None, 'LS_BM', None]
        })
        test_data.to_csv(test_file, index=False)
        
        # 处理文件
        result = await self.dmp_agent.process_file_data(str(test_file))
        
        # 验证处理结果
        self.assertTrue(result['success'])
        
        # 验证输出文件
        output_df = pd.read_csv(result['processed_data'])
        
        # 验证合并单元格处理
        self.assertEqual(len(output_df), 4)  # 应该保留所有记录
        self.assertTrue(all(output_df['platform'] == 'LS_BM'))  # platform应该都被填充为LS_BM
        self.assertTrue(all(output_df['advertiser_name'].notna()))  # advertiser_name不应该有空值
        
        # 验证数据正确性
        self.assertEqual(output_df['conversion_amount'].sum(), 700)  # 100 + 150 + 200 + 250

if __name__ == '__main__':
    unittest.main()
