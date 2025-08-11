#!/usr/bin/env python3
"""
Platform Detector 單元測試
"""

import unittest
import os
import sys
import pandas as pd
from unittest.mock import Mock, patch

# 添加項目根目錄到路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.data_dmp_agent.platform_detector import PlatformDetector

class TestPlatformDetector(unittest.TestCase):
    """Platform Detector 測試類"""
    
    def setUp(self):
        """測試前準備"""
        self.detector = PlatformDetector()
    
    def test_detect_from_filename_involve_asia(self):
        """測試從文件名識別Involve Asia平台"""
        test_filenames = [
            "publisher-conversion-report--bC8s4v7v-20250731_IA_MB.csv",
            "involve_asia_report.xlsx",
            "IA_BM_data.csv",
            "report_ia_bm.xlsx"
        ]
        
        for filename in test_filenames:
            platform = self.detector.detect_from_filename(filename)
            self.assertEqual(platform, "involve_asia", f"Failed for filename: {filename}")
    
    def test_detect_from_filename_shopee(self):
        """測試從文件名識別Shopee平台"""
        test_filenames = [
            "shopee_report.csv",
            "Shopee_data.xlsx",
            "report_shopee.xlsx"
        ]
        
        for filename in test_filenames:
            platform = self.detector.detect_from_filename(filename)
            self.assertEqual(platform, "shopee", f"Failed for filename: {filename}")
    
    def test_detect_from_filename_tiktok_shop(self):
        """測試從文件名識別TikTok Shop平台"""
        test_filenames = [
            "tiktok_shop_report.csv",
            "TikTok_data.xlsx",
            "report_tiktok.xlsx"
        ]
        
        for filename in test_filenames:
            platform = self.detector.detect_from_filename(filename)
            self.assertEqual(platform, "tiktok_shop", f"Failed for filename: {filename}")
    
    def test_detect_from_filename_access_trade(self):
        """測試從文件名識別Access Trade平台"""
        test_filenames = [
            "access_trade_report.csv",
            "AT_data.xlsx",
            "report_at.xlsx"
        ]
        
        for filename in test_filenames:
            platform = self.detector.detect_from_filename(filename)
            self.assertEqual(platform, "access_trade", f"Failed for filename: {filename}")
    
    def test_detect_from_filename_unknown(self):
        """測試無法識別的文件名"""
        test_filenames = [
            "unknown_report.csv",
            "random_data.xlsx",
            "test_file.txt"
        ]
        
        for filename in test_filenames:
            platform = self.detector.detect_from_filename(filename)
            self.assertIsNone(platform, f"Should be None for filename: {filename}")
    
    def test_detect_from_content_involve_asia(self):
        """測試從內容識別Involve Asia平台"""
        test_data = {
            "Advertiser Name": ["Advertiser A", "Advertiser B"],
            "Campaign Name": ["Campaign 1", "Campaign 2"],
            "Offer Name": ["Offer 1", "Offer 2"],
            "Sale Amount (USD)": [100.50, 200.75],
            "Conversion Date": ["2024-01-01", "2024-01-02"],
            "Publisher ID": ["PUB001", "PUB002"]
        }
        df = pd.DataFrame(test_data)
        
        platform = self.detector.detect_from_content(df)
        self.assertEqual(platform, "involve_asia")
    
    def test_detect_from_content_shopee(self):
        """測試從內容識別Shopee平台"""
        test_data = {
            "Campaign Name": ["Shopee Campaign 1", "Shopee Campaign 2"],
            "Ad Group Name": ["Ad Group 1", "Ad Group 2"],
            "Product Name": ["Product 1", "Product 2"],
            "Revenue": [300.00, 450.50],
            "Date": ["2024-01-01", "2024-01-02"],
            "Publisher ID": ["SP001", "SP002"]
        }
        df = pd.DataFrame(test_data)
        
        platform = self.detector.detect_from_content(df)
        self.assertEqual(platform, "shopee")
    
    def test_detect_from_content_access_trade(self):
        """測試從內容識別Access Trade平台"""
        test_data = {
            "Advertiser Name": ["Advertiser A", "Advertiser B"],
            "Campaign Name": ["Campaign 1", "Campaign 2"],
            "Offer Name": ["Offer 1", "Offer 2"],
            "Commission": [50.25, 75.50],
            "Date": ["2024-01-01", "2024-01-02"],
            "Publisher ID": ["AT001", "AT002"]
        }
        df = pd.DataFrame(test_data)
        
        platform = self.detector.detect_from_content(df)
        self.assertEqual(platform, "access_trade")
    
    def test_detect_from_content_unknown(self):
        """測試無法從內容識別的平台"""
        test_data = {
            "Unknown Column 1": ["Data 1", "Data 2"],
            "Unknown Column 2": ["Data 3", "Data 4"]
        }
        df = pd.DataFrame(test_data)
        
        platform = self.detector.detect_from_content(df)
        self.assertIsNone(platform)
    
    def test_detect_platform_filename_priority(self):
        """測試平台識別優先級（文件名優先）"""
        # 創建一個文件名指向involve_asia，但內容指向shopee的測試
        test_data = {
            "Campaign Name": ["Shopee Campaign 1"],
            "Revenue": [300.00]
        }
        df = pd.DataFrame(test_data)
        
        file_path = "test_ia_mb.csv"  # 文件名指向involve_asia
        
        platform = self.detector.detect_platform(file_path=file_path, df=df)
        self.assertEqual(platform, "involve_asia")  # 應該優先使用文件名識別
    
    def test_detect_platform_content_fallback(self):
        """測試平台識別降級（使用內容識別）"""
        # 創建一個無法從文件名識別，但可以從內容識別的測試
        test_data = {
            "Advertiser Name": ["Advertiser A"],
            "Sale Amount (USD)": [100.50]
        }
        df = pd.DataFrame(test_data)
        
        file_path = "unknown_report.csv"  # 無法從文件名識別
        
        platform = self.detector.detect_platform(file_path=file_path, df=df)
        self.assertEqual(platform, "involve_asia")  # 應該使用內容識別
    
    def test_detect_platform_default(self):
        """測試平台識別默認值"""
        # 創建一個無法識別的測試
        test_data = {"Unknown": ["Data"]}
        df = pd.DataFrame(test_data)
        
        file_path = "unknown_file.csv"
        
        platform = self.detector.detect_platform(file_path=file_path, df=df)
        self.assertEqual(platform, "involve_asia")  # 應該返回默認平台
    
    def test_get_platform_info(self):
        """測試獲取平台信息"""
        info = self.detector.get_platform_info("involve_asia")
        
        self.assertEqual(info["platform"], "involve_asia")
        self.assertIn("filename_patterns", info)
        self.assertIn("column_patterns", info)
        self.assertIn("keywords", info)
    
    def test_get_platform_info_invalid(self):
        """測試獲取無效平台信息"""
        info = self.detector.get_platform_info("invalid_platform")
        
        self.assertEqual(info, {})
    
    def test_get_all_platforms(self):
        """測試獲取所有平台列表"""
        platforms = self.detector.get_all_platforms()
        
        expected_platforms = ["involve_asia", "shopee", "tiktok_shop", "access_trade"]
        for platform in expected_platforms:
            self.assertIn(platform, platforms)
    
    def test_add_platform_rules(self):
        """測試添加平台規則"""
        new_rules = {
            "filename_patterns": [r"test_platform"],
            "column_patterns": ["Test Column"],
            "keywords": ["test"]
        }
        
        self.detector.add_platform_rules("test_platform", new_rules)
        
        # 驗證新平台已添加
        platforms = self.detector.get_all_platforms()
        self.assertIn("test_platform", platforms)
        
        # 驗證新平台可以被識別
        platform = self.detector.detect_from_filename("test_platform_report.csv")
        self.assertEqual(platform, "test_platform")
    
    def test_validate_platform_detection_correct(self):
        """測試平台識別驗證（正確）"""
        file_path = "test_ia_mb.csv"
        expected_platform = "involve_asia"
        
        result = self.detector.validate_platform_detection(file_path, expected_platform)
        
        self.assertTrue(result)
    
    def test_validate_platform_detection_incorrect(self):
        """測試平台識別驗證（錯誤）"""
        file_path = "test_ia_mb.csv"
        expected_platform = "shopee"
        
        result = self.detector.validate_platform_detection(file_path, expected_platform)
        
        self.assertFalse(result)
    
    def test_analyze_data_content(self):
        """測試數據內容分析"""
        test_data = {
            "Sale Amount (USD)": [100.50, 200.75],
            "Conversion Date": ["2024-01-01", "2024-01-02"]
        }
        df = pd.DataFrame(test_data)
        
        # 測試involve_asia的內容分析
        score = self.detector._analyze_data_content(df, "involve_asia")
        self.assertGreater(score, 0)
        
        # 測試shopee的內容分析
        score = self.detector._analyze_data_content(df, "shopee")
        self.assertGreaterEqual(score, 0)

if __name__ == '__main__':
    unittest.main() 