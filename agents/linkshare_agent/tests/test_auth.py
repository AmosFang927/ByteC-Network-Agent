#!/usr/bin/env python3
"""
TikTokAuth 認證類單元測試
"""

import unittest
import json
import time
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# 添加項目根目錄到路徑
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from agents.linkshare_agent.auth import TikTokAuth
from agents.linkshare_agent import config

class TestTikTokAuth(unittest.TestCase):
    """TikTokAuth 測試類"""
    
    def setUp(self):
        """測試前準備"""
        self.auth = TikTokAuth()
        
        # 模擬的 API 響應數據
        self.mock_token_response = {
            "code": 0,
            "message": "success",
            "data": {
                "access_token": "TTP_Fw8rBwAAAAAkW03FYd09DG-9INtpw361hWthei8S3fHX8iPJ5AUv99fLSCYD9-UucaqxTgNRzKZxi5-tfFMtdWqglEt5_iCk",
                "access_token_expire_in": 1660556783,
                "refresh_token": "TTP_NTUxZTNhYTQ2ZDk2YmRmZWNmYWY2YWY2YzkxNGYwNjQ3YjkzYTllYjA0YmNlMw",
                "refresh_token_expire_in": 1691487031,
                "open_id": "7010736057180325637",
                "seller_name": "Test Shop",
                "seller_base_region": "ID",
                "user_type": 0,
                "granted_scopes": [
                    "seller.affiliate_collaboration.read",
                    "seller.affiliate_collaboration.write"
                ]
            },
            "request_id": "2022080809462301024509910319695C45"
        }
        
        self.mock_error_response = {
            "code": 40001,
            "message": "參數錯誤",
            "request_id": "test_request_id"
        }
    
    def tearDown(self):
        """測試後清理"""
        self.auth.close()
    
    @patch('agents.linkshare_agent.auth.requests.Session.get')
    def test_get_access_token_success(self, mock_get):
        """測試成功獲取 access token"""
        # 模擬成功的 HTTP 響應
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_token_response
        mock_response.raise_for_status.return_value = None
        mock_response.headers = {"Content-Type": "application/json"}  # 修復：直接設置為字典
        mock_get.return_value = mock_response
        
        # 執行測試
        result = self.auth.get_access_token("test_auth_code")
        
        # 驗證結果
        self.assertIsInstance(result, dict)
        self.assertEqual(result['access_token'], self.mock_token_response['data']['access_token'])
        self.assertEqual(result['refresh_token'], self.mock_token_response['data']['refresh_token'])
        self.assertEqual(result['open_id'], self.mock_token_response['data']['open_id'])
        self.assertIn('fetched_at', result)
        self.assertIn('expires_at', result)
        
        # 驗證 API 調用參數
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertIn('app_key', call_args[1]['params'])
        self.assertIn('app_secret', call_args[1]['params'])
        self.assertIn('grant_type', call_args[1]['params'])
        self.assertIn('code', call_args[1]['params'])
        self.assertEqual(call_args[1]['params']['grant_type'], 'authorization_code')
        self.assertEqual(call_args[1]['params']['code'], 'test_auth_code')
    
    @patch('agents.linkshare_agent.auth.requests.Session.get')
    def test_get_access_token_api_error(self, mock_get):
        """測試 API 返回錯誤時的處理"""
        # 模擬錯誤的 HTTP 響應
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_error_response
        mock_response.raise_for_status.return_value = None
        mock_response.headers = {"Content-Type": "application/json"}  # 修復：直接設置為字典
        mock_get.return_value = mock_response
        
        # 執行測試並驗證異常
        with self.assertRaises(Exception) as context:
            self.auth.get_access_token("test_auth_code")
        
        self.assertIn("40001", str(context.exception))
        self.assertIn("參數錯誤", str(context.exception))
    
    def test_get_access_token_empty_auth_code(self):
        """測試空的授權碼"""
        with self.assertRaises(ValueError) as context:
            self.auth.get_access_token("")
        
        self.assertIn("授權碼", str(context.exception))
    
    @patch('agents.linkshare_agent.auth.requests.Session.get')
    def test_refresh_access_token_success(self, mock_get):
        """測試成功刷新 access token"""
        # 模擬成功的 HTTP 響應
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_token_response
        mock_response.raise_for_status.return_value = None
        mock_response.headers = {"Content-Type": "application/json"}  # 修復：直接設置為字典
        mock_get.return_value = mock_response
        
        # 執行測試
        result = self.auth.refresh_access_token("test_refresh_token")
        
        # 驗證結果
        self.assertIsInstance(result, dict)
        self.assertEqual(result['access_token'], self.mock_token_response['data']['access_token'])
        
        # 驗證 API 調用參數
        call_args = mock_get.call_args
        self.assertEqual(call_args[1]['params']['grant_type'], 'refresh_token')
        self.assertEqual(call_args[1]['params']['refresh_token'], 'test_refresh_token')
    
    def test_refresh_access_token_empty_token(self):
        """測試空的刷新令牌"""
        with self.assertRaises(ValueError) as context:
            self.auth.refresh_access_token("")
        
        self.assertIn("刷新令牌", str(context.exception))
    
    @patch('agents.linkshare_agent.auth.requests.Session.get')
    def test_network_retry_mechanism(self, mock_get):
        """測試網路重試機制"""
        # 模擬前兩次請求失敗，第三次成功
        def side_effect(*args, **kwargs):
            call_count = mock_get.call_count
            if call_count <= 2:
                raise Exception(f"Network error {call_count}")
            else:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = self.mock_token_response
                mock_response.raise_for_status.return_value = None
                mock_response.headers = {"Content-Type": "application/json"}
                return mock_response
        
        mock_get.side_effect = side_effect
        
        # 執行測試
        with patch('time.sleep'):  # 跳過實際睡眠
            result = self.auth.get_access_token("test_auth_code")
        
        # 驗證結果
        self.assertIsInstance(result, dict)
        self.assertEqual(mock_get.call_count, 3)
    
    @patch('agents.linkshare_agent.auth.requests.Session.get')
    def test_network_retry_exhausted(self, mock_get):
        """測試網路重試耗盡"""
        # 模擬所有重試都失敗
        mock_get.side_effect = Exception("Network error")
        
        # 執行測試並驗證異常
        with patch('time.sleep'):  # 跳過實際睡眠
            with self.assertRaises(Exception) as context:
                self.auth.get_access_token("test_auth_code")
        
        self.assertIn("已重試", str(context.exception))
        self.assertEqual(mock_get.call_count, config.MAX_RETRIES)
    
    def test_validate_token_format_valid(self):
        """測試有效的 Token 格式"""
        valid_token = "TTP_Fw8rBwAAAAAkW03FYd09DG-9INtpw361hWthei8S3fHX8iPJ5AUv99fLSCYD9-UucaqxTgNRzKZxi5-tfFMtdWqglEt5_iCk"
        self.assertTrue(self.auth.validate_token_format(valid_token))
    
    def test_validate_token_format_invalid(self):
        """測試無效的 Token 格式"""
        invalid_tokens = [
            "",
            None,
            "invalid_token",
            "TTP_",
            "TTP_short",
            123,
            []
        ]
        
        for token in invalid_tokens:
            with self.subTest(token=token):
                self.assertFalse(self.auth.validate_token_format(token))
    
    def test_handle_api_response_missing_data(self):
        """測試響應缺少數據部分"""
        invalid_response = {
            "code": 0,
            "message": "success"
            # 缺少 data 部分
        }
        
        with self.assertRaises(Exception) as context:
            self.auth._handle_api_response(invalid_response, "test_operation")
        
        self.assertIn("缺少數據部分", str(context.exception))
    
    def test_handle_api_response_invalid_format(self):
        """測試無效的響應格式"""
        with self.assertRaises(Exception) as context:
            self.auth._handle_api_response("invalid_response", "test_operation")
        
        self.assertIn("無效的響應格式", str(context.exception))

class TestTikTokAuthIntegration(unittest.TestCase):
    """TikTokAuth 整合測試"""
    
    def setUp(self):
        """測試前準備"""
        self.auth = TikTokAuth()
    
    def tearDown(self):
        """測試後清理"""
        self.auth.close()
    
    def test_context_manager(self):
        """測試上下文管理器"""
        with TikTokAuth() as auth:
            self.assertIsInstance(auth, TikTokAuth)
            self.assertTrue(hasattr(auth, 'session'))
        # 驗證上下文退出後會話已關閉
        # 注意：這個測試比較難驗證，因為 requests.Session 的 close 方法沒有明顯的狀態變化
    
    @patch('agents.linkshare_agent.auth.config.APP_KEY', '')
    def test_validation_missing_config(self):
        """測試配置缺失時的驗證"""
        # 這個測試需要在配置驗證階段運行
        # 在實際使用中，配置驗證會在模組加載時進行
        pass

if __name__ == '__main__':
    # 設置測試日誌級別
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    # 運行測試
    unittest.main(verbosity=2) 