#!/usr/bin/env python3
"""
Field Mapping Manager 單元測試
"""

import unittest
import os
import sys
import tempfile
import json
import pandas as pd
from unittest.mock import Mock, patch, MagicMock

# 添加項目根目錄到路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.data_dmp_agent.field_mapping_manager import FieldMappingManager

class TestFieldMappingManager(unittest.TestCase):
    """Field Mapping Manager 測試類"""
    
    def setUp(self):
        """測試前準備"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, "test_config.json")
        
        # 創建測試配置文件
        test_config = {
            "google_sheets": {
                "enabled": False
            },
            "fallback_config": {
                "local_file": os.path.join(self.temp_dir, "test_mappings.json"),
                "enabled": True
            },
            "standard_fields": {
                "platform": "平台名稱",
                "advertiser_name": "廣告主名稱"
            }
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(test_config, f)
        
        # 創建測試映射文件
        test_mappings = {
            "platforms": {
                "involve_asia": {
                    "field_mappings": {
                        "advertiser_name": "Advertiser Name",
                        "campaign_name": "Campaign Name",
                        "conversion_amount": "Sale Amount (USD)"
                    },
                    "data_transformations": {
                        "conversion_amount": {"type": "currency", "currency": "USD"}
                    }
                },
                "shopee": {
                    "field_mappings": {
                        "advertiser_name": "Campaign Name",
                        "campaign_name": "Ad Group Name",
                        "conversion_amount": "Revenue"
                    }
                }
            }
        }
        
        mappings_file = os.path.join(self.temp_dir, "test_mappings.json")
        with open(mappings_file, 'w') as f:
            json.dump(test_mappings, f)
    
    def tearDown(self):
        """測試後清理"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_init_with_config(self):
        """測試使用配置文件初始化"""
        manager = FieldMappingManager(self.config_file)
        
        self.assertIsNotNone(manager)
        self.assertEqual(manager.config_file, self.config_file)
        self.assertIn("platforms", manager.field_mappings)
    
    def test_init_without_config(self):
        """測試不使用配置文件初始化"""
        manager = FieldMappingManager()
        
        self.assertIsNotNone(manager)
        self.assertIn("platforms", manager.field_mappings)
    
    def test_map_dataframe_columns_valid(self):
        """測試有效的DataFrame欄位映射"""
        manager = FieldMappingManager(self.config_file)
        
        # 創建測試DataFrame
        test_data = {
            "Advertiser Name": ["Advertiser A", "Advertiser B"],
            "Campaign Name": ["Campaign 1", "Campaign 2"],
            "Sale Amount (USD)": [100.50, 200.75]
        }
        df = pd.DataFrame(test_data)
        
        # 執行映射
        mapped_df, mapping_info = manager.map_dataframe_columns(df, "involve_asia")
        
        # 驗證結果
        self.assertIsNotNone(mapped_df)
        self.assertIn("platform", mapped_df.columns)
        self.assertIn("advertiser_name", mapped_df.columns)
        self.assertIn("campaign_name", mapped_df.columns)
        self.assertIn("conversion_amount", mapped_df.columns)
        
        # 驗證映射信息
        self.assertEqual(mapping_info["platform"], "involve_asia")
        self.assertEqual(len(mapping_info["mapped_columns"]), 3)
    
    def test_map_dataframe_columns_invalid_platform(self):
        """測試無效平台的DataFrame欄位映射"""
        manager = FieldMappingManager(self.config_file)
        
        test_data = {"Test Column": ["Test Data"]}
        df = pd.DataFrame(test_data)
        
        # 執行映射
        mapped_df, mapping_info = manager.map_dataframe_columns(df, "invalid_platform")
        
        # 應該返回空的DataFrame，因為沒有映射配置
        self.assertEqual(len(mapped_df), 0)
        self.assertEqual(mapping_info, {})
    
    def test_map_dataframe_columns_missing_columns(self):
        """測試缺失欄位的DataFrame映射"""
        manager = FieldMappingManager(self.config_file)
        
        # 創建缺少某些欄位的DataFrame
        test_data = {
            "Advertiser Name": ["Advertiser A"],
            "Campaign Name": ["Campaign 1"]
            # 缺少 "Sale Amount (USD)"
        }
        df = pd.DataFrame(test_data)
        
        # 執行映射
        mapped_df, mapping_info = manager.map_dataframe_columns(df, "involve_asia")
        
        # 驗證結果
        self.assertIn("advertiser_name", mapped_df.columns)
        self.assertIn("campaign_name", mapped_df.columns)
        self.assertNotIn("conversion_amount", mapped_df.columns)
        
        # 驗證映射信息
        self.assertEqual(len(mapping_info["mapped_columns"]), 2)
        self.assertEqual(len(mapping_info["unmapped_columns"]), 1)
    
    def test_apply_data_transformation_currency(self):
        """測試貨幣數據轉換"""
        manager = FieldMappingManager(self.config_file)
        
        # 創建測試DataFrame
        test_data = {"conversion_amount": ["100.50", "200.75"]}
        df = pd.DataFrame(test_data)
        
        # 應用貨幣轉換
        transformation = {"type": "currency", "currency": "USD"}
        result_df = manager._apply_data_transformation(df, "conversion_amount", transformation)
        
        # 驗證結果
        self.assertIn("conversion_amount", result_df.columns)
        self.assertIn("conversion_amount_currency", result_df.columns)
        self.assertEqual(result_df["conversion_amount_currency"].iloc[0], "USD")
    
    def test_apply_data_transformation_date(self):
        """測試日期數據轉換"""
        manager = FieldMappingManager(self.config_file)
        
        # 創建測試DataFrame
        test_data = {"conversion_date": ["2024-01-01", "2024-01-02"]}
        df = pd.DataFrame(test_data)
        
        # 應用日期轉換
        transformation = {"type": "date", "format": "%Y-%m-%d"}
        result_df = manager._apply_data_transformation(df, "conversion_date", transformation)
        
        # 驗證結果
        self.assertIn("conversion_date", result_df.columns)
    
    def test_validate_mapping_valid(self):
        """測試有效的映射驗證"""
        manager = FieldMappingManager(self.config_file)
        
        # 創建有效的測試DataFrame
        test_data = {
            "Advertiser Name": ["Advertiser A"],
            "Campaign Name": ["Campaign 1"],
            "Sale Amount (USD)": [100.50]
        }
        df = pd.DataFrame(test_data)
        
        # 執行驗證
        validation = manager.validate_mapping(df, "involve_asia")
        
        # 驗證結果
        self.assertTrue(validation["valid"])
        self.assertEqual(validation["platform"], "involve_asia")
        self.assertEqual(validation["mapped_columns"], 3)
    
    def test_validate_mapping_invalid_platform(self):
        """測試無效平台的映射驗證"""
        manager = FieldMappingManager(self.config_file)
        
        test_data = {"Test Column": ["Test Data"]}
        df = pd.DataFrame(test_data)
        
        # 執行驗證
        validation = manager.validate_mapping(df, "invalid_platform")
        
        # 驗證結果
        self.assertFalse(validation["valid"])
        self.assertIn("error", validation)
    
    def test_validate_mapping_no_mappings(self):
        """測試沒有映射的驗證"""
        manager = FieldMappingManager(self.config_file)
        
        # 創建沒有匹配欄位的DataFrame
        test_data = {"Unrelated Column": ["Data"]}
        df = pd.DataFrame(test_data)
        
        # 執行驗證
        validation = manager.validate_mapping(df, "involve_asia")
        
        # 驗證結果
        self.assertFalse(validation["valid"])
        self.assertEqual(validation["mapped_columns"], 0)
    
    def test_get_available_platforms(self):
        """測試獲取可用平台列表"""
        manager = FieldMappingManager(self.config_file)
        
        platforms = manager.get_available_platforms()
        
        self.assertIn("involve_asia", platforms)
        self.assertIn("shopee", platforms)
    
    def test_get_platform_mapping_info(self):
        """測試獲取平台映射信息"""
        manager = FieldMappingManager(self.config_file)
        
        info = manager.get_platform_mapping_info("involve_asia")
        
        self.assertEqual(info["platform"], "involve_asia")
        self.assertIn("field_mappings", info)
        self.assertIn("data_transformations", info)
        self.assertEqual(info["total_mappings"], 3)
    
    def test_get_platform_mapping_info_invalid(self):
        """測試獲取無效平台的映射信息"""
        manager = FieldMappingManager(self.config_file)
        
        info = manager.get_platform_mapping_info("invalid_platform")
        
        self.assertEqual(info, {})
    
    def test_refresh_mappings(self):
        """測試刷新映射"""
        manager = FieldMappingManager(self.config_file)
        
        # 執行刷新
        result = manager.refresh_mappings()
        
        self.assertTrue(result)
    
    def test_export_mappings_to_json(self):
        """測試導出映射到JSON"""
        manager = FieldMappingManager(self.config_file)
        
        export_file = os.path.join(self.temp_dir, "exported_mappings.json")
        
        # 執行導出
        result = manager.export_mappings_to_json(export_file)
        
        self.assertTrue(result)
        self.assertTrue(os.path.exists(export_file))
        
        # 驗證導出的內容
        with open(export_file, 'r') as f:
            exported_data = json.load(f)
        
        self.assertIn("platforms", exported_data)

if __name__ == '__main__':
    unittest.main() 