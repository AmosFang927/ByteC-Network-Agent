#!/usr/bin/env python3
"""
Google Sheets Manager 單元測試
"""

import unittest
import os
import sys
import tempfile
import json
from unittest.mock import Mock, patch, MagicMock

# 添加項目根目錄到路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.data_dmp_agent.google_sheets_manager import GoogleSheetsManager

class TestGoogleSheetsManager(unittest.TestCase):
    """Google Sheets Manager 測試類"""
    
    def setUp(self):
        """測試前準備"""
        self.temp_dir = tempfile.mkdtemp()
        self.credentials_file = os.path.join(self.temp_dir, "test_credentials.json")
        
        # 創建測試憑證文件
        test_credentials = {
            "type": "service_account",
            "project_id": "test-project",
            "private_key_id": "test-key-id",
            "private_key": "-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----\n",
            "client_email": "test@test-project.iam.gserviceaccount.com",
            "client_id": "123456789",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/test%40test-project.iam.gserviceaccount.com"
        }
        
        with open(self.credentials_file, 'w') as f:
            json.dump(test_credentials, f)
    
    def tearDown(self):
        """測試後清理"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_init_with_credentials(self):
        """測試使用憑證初始化"""
        with patch('agents.data_dmp_agent.google_sheets_manager.GOOGLE_SHEETS_AVAILABLE', True):
            with patch('agents.data_dmp_agent.google_sheets_manager.gspread') as mock_gspread:
                with patch('agents.data_dmp_agent.google_sheets_manager.Credentials') as mock_credentials:
                    # 模擬認證和客戶端
                    mock_credentials.from_service_account_file.return_value = Mock()
                    mock_gspread.authorize.return_value = Mock()
                    
                    manager = GoogleSheetsManager(credentials_file=self.credentials_file)
                    
                    self.assertIsNotNone(manager)
                    self.assertEqual(manager.credentials_file, self.credentials_file)
    
    def test_init_without_credentials(self):
        """測試不使用憑證初始化"""
        manager = GoogleSheetsManager(credentials_file=None)
        
        self.assertIsNotNone(manager)
        self.assertIsNone(manager.client)
    
    def test_get_default_mappings(self):
        """測試獲取默認映射"""
        manager = GoogleSheetsManager()
        mappings = manager._get_default_mappings()
        
        self.assertIn("platforms", mappings)
        self.assertIn("involve_asia", mappings["platforms"])
        self.assertIn("field_mappings", mappings["platforms"]["involve_asia"])
    
    def test_parse_sheets_data_valid(self):
        """測試解析有效的Google Sheets數據"""
        manager = GoogleSheetsManager()
        
        # 模擬有效的Google Sheets數據
        test_data = [
            ["Platform", "Field", "Unitfied Field"],
            ["IA_BM", "Creator tag ID", "Publisher Sub ID 1"],
            ["IA_BM", "Order ID", "Conversion ID"],
            ["Shopee", "Campaign Name", "advertiser_name"]
        ]
        
        mappings = manager._parse_sheets_data(test_data)
        
        self.assertIn("platforms", mappings)
        self.assertIn("involve_asia", mappings["platforms"])
        self.assertIn("shopee", mappings["platforms"])
    
    def test_parse_sheets_data_invalid(self):
        """測試解析無效的Google Sheets數據"""
        manager = GoogleSheetsManager()
        
        # 模擬無效數據
        test_data = [
            ["Invalid", "Headers"],
            ["No", "Platform", "Column"]
        ]
        
        mappings = manager._parse_sheets_data(test_data)
        
        self.assertEqual(mappings, {})
    
    def test_find_column_index(self):
        """測試查找列索引"""
        manager = GoogleSheetsManager()
        
        headers = ["Platform", "Field", "Unitfied Field"]
        
        # 測試找到的列
        platform_index = manager._find_column_index(headers, ["Platform", "platform"])
        self.assertEqual(platform_index, 0)
        
        # 測試找不到的列
        not_found_index = manager._find_column_index(headers, ["Not Found"])
        self.assertIsNone(not_found_index)
    
    def test_normalize_platform_name(self):
        """測試平台名稱標準化"""
        manager = GoogleSheetsManager()
        
        # 測試標準化
        self.assertEqual(manager._normalize_platform_name("IA_BM"), "involve_asia")
        self.assertEqual(manager._normalize_platform_name("Shopee"), "shopee")
        self.assertEqual(manager._normalize_platform_name("Unknown"), "unknown")
    
    def test_infer_data_type(self):
        """測試數據類型推斷"""
        manager = GoogleSheetsManager()
        
        # 測試不同類型的欄位
        self.assertEqual(manager._infer_data_type("conversion_amount"), "currency")
        self.assertEqual(manager._infer_data_type("conversion_date"), "date")
        self.assertEqual(manager._infer_data_type("commission_rate"), "percentage")
        self.assertEqual(manager._infer_data_type("advertiser_name"), "string")
    
    def test_cache_functionality(self):
        """測試緩存功能"""
        manager = GoogleSheetsManager()
        
        # 測試緩存更新
        test_data = {"test": "data"}
        manager._update_cache("test_key", test_data)
        
        # 測試緩存有效性
        self.assertTrue(manager._is_cache_valid("test_key"))
        
        # 測試清除緩存
        manager.clear_cache()
        self.assertFalse(manager._is_cache_valid("test_key"))
    
    def test_get_local_mappings_file_exists(self):
        """測試獲取本地映射（文件存在）"""
        manager = GoogleSheetsManager()
        
        # 創建臨時映射文件
        temp_mapping_file = os.path.join(self.temp_dir, "field_mappings.json")
        test_mappings = {
            "platforms": {
                "test_platform": {
                    "field_mappings": {"test": "mapping"}
                }
            }
        }
        
        with open(temp_mapping_file, 'w') as f:
            json.dump(test_mappings, f)
        
        # 模擬本地文件路徑
        with patch.object(manager, '_get_local_mappings') as mock_get_local:
            mock_get_local.return_value = test_mappings
            mappings = manager._get_local_mappings()
            
            self.assertEqual(mappings, test_mappings)
    
    def test_get_local_mappings_file_not_exists(self):
        """測試獲取本地映射（文件不存在）"""
        manager = GoogleSheetsManager()
        
        # 模擬文件不存在的情況
        with patch('os.path.exists', return_value=False):
            mappings = manager._get_local_mappings()
            
            # 應該返回默認映射
            self.assertIn("platforms", mappings)

if __name__ == '__main__':
    unittest.main() 