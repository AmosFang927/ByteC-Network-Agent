#!/usr/bin/env python3
"""
TokenManager Token 管理類單元測試
"""

import unittest
import json
import time
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys

# 添加項目根目錄到路徑
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from agents.linkshare_agent.token_manager import TokenManager
from agents.linkshare_agent import config

class TestTokenManager(unittest.TestCase):
    """TokenManager 測試類"""
    
    def setUp(self):
        """測試前準備"""
        # 創建臨時目錄用於測試
        self.temp_dir = tempfile.mkdtemp()
        self.temp_token_file = Path(self.temp_dir) / "test_tokens.conf"
        
        # 創建測試用的 TokenManager
        self.token_manager = TokenManager()
        # 替換為測試路徑
        self.token_manager.token_file = self.temp_token_file
        
        # 模擬的 Token 數據
        self.mock_token_data = {
            "access_token": "TTP_Fw8rBwAAAAAkW03FYd09DG-9INtpw361hWthei8S3fHX8iPJ5AUv99fLSCYD9-UucaqxTgNRzKZxi5-tfFMtdWqglEt5_iCk",
            "refresh_token": "TTP_NTUxZTNhYTQ2ZDk2YmRmZWNmYWY2YWY2YzkxNGYwNjQ3YjkzYTllYjA0YmNlMw",
            "open_id": "7010736057180325637",
            "seller_name": "Test Shop",
            "seller_base_region": "ID",
            "fetched_at": int(time.time()) - 1000,  # 1000 秒前獲取
            "expires_at": int(time.time()) + config.TOKEN_EXPIRE_TIME - 1000,  # 還有很長時間過期
            "saved_at": int(time.time())
        }
        
        self.expired_token_data = {
            "access_token": "TTP_expired_token",
            "refresh_token": "TTP_expired_refresh",
            "open_id": "expired_id",
            "fetched_at": int(time.time()) - config.TOKEN_EXPIRE_TIME - 100,  # 已過期
            "expires_at": int(time.time()) - 100,  # 已過期
            "saved_at": int(time.time()) - config.TOKEN_EXPIRE_TIME - 100
        }
    
    def tearDown(self):
        """測試後清理"""
        # 清理臨時目錄
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_save_and_load_tokens(self):
        """測試保存和加載 Token"""
        # 保存 Token
        self.token_manager.save_tokens(self.mock_token_data)
        
        # 驗證文件是否創建
        self.assertTrue(self.temp_token_file.exists())
        
        # 加載 Token
        loaded_tokens = self.token_manager.load_tokens()
        
        # 驗證數據
        self.assertIsNotNone(loaded_tokens)
        self.assertEqual(loaded_tokens['access_token'], self.mock_token_data['access_token'])
        self.assertEqual(loaded_tokens['refresh_token'], self.mock_token_data['refresh_token'])
        self.assertIn('saved_at', loaded_tokens)
    
    def test_load_tokens_file_not_exists(self):
        """測試加載不存在的 Token 文件"""
        result = self.token_manager.load_tokens()
        self.assertIsNone(result)
    
    def test_is_token_expired_valid_token(self):
        """測試有效 Token 的過期檢查"""
        is_expired = self.token_manager.is_token_expired(self.mock_token_data)
        self.assertFalse(is_expired)
    
    def test_is_token_expired_expired_token(self):
        """測試已過期 Token 的檢查"""
        is_expired = self.token_manager.is_token_expired(self.expired_token_data)
        self.assertTrue(is_expired)
    
    def test_is_token_expired_empty_data(self):
        """測試空 Token 數據的過期檢查"""
        is_expired = self.token_manager.is_token_expired({})
        self.assertTrue(is_expired)
        
        is_expired = self.token_manager.is_token_expired(None)
        self.assertTrue(is_expired)
    
    def test_get_token_info_with_valid_token(self):
        """測試獲取有效 Token 信息"""
        # 先保存 Token
        self.token_manager.save_tokens(self.mock_token_data)
        
        # 獲取信息
        token_info = self.token_manager.get_token_info()
        
        # 驗證信息
        self.assertEqual(token_info['status'], '有效')
        self.assertEqual(token_info['access_token'], self.mock_token_data['access_token'])
        self.assertEqual(token_info['seller_name'], self.mock_token_data['seller_name'])
        self.assertFalse(token_info['is_expired'])
        self.assertIn('remaining_seconds', token_info)
    
    def test_get_token_info_no_token(self):
        """測試無 Token 時的信息獲取"""
        token_info = self.token_manager.get_token_info()
        
        # 驗證信息
        self.assertEqual(token_info['status'], '未找到 Token')
        self.assertIsNone(token_info['access_token'])
        self.assertTrue(token_info['is_expired'])
    
    def test_clear_tokens(self):
        """測試清除 Token"""
        # 先保存 Token
        self.token_manager.save_tokens(self.mock_token_data)
        self.assertTrue(self.temp_token_file.exists())
        
        # 清除 Token
        result = self.token_manager.clear_tokens()
        
        # 驗證結果
        self.assertTrue(result)
        self.assertFalse(self.temp_token_file.exists())
    
    def test_clear_tokens_no_file(self):
        """測試清除不存在的 Token 文件"""
        result = self.token_manager.clear_tokens()
        self.assertTrue(result)  # 應該仍然返回 True
    
    @patch('agents.linkshare_agent.token_manager.TikTokAuth.refresh_access_token')
    def test_refresh_token_if_needed_valid_token(self, mock_refresh):
        """測試有效 Token 時不需要刷新"""
        # 保存有效 Token
        self.token_manager.save_tokens(self.mock_token_data)
        
        # 嘗試刷新
        result = self.token_manager.refresh_token_if_needed()
        
        # 驗證結果
        self.assertFalse(result)  # 不需要刷新
        mock_refresh.assert_not_called()
    
    @patch('agents.linkshare_agent.token_manager.TikTokAuth.refresh_access_token')
    def test_refresh_token_if_needed_expired_token(self, mock_refresh):
        """測試過期 Token 時需要刷新"""
        # 模擬刷新後的新 Token
        new_token_data = self.mock_token_data.copy()
        new_token_data['access_token'] = "TTP_new_access_token"
        new_token_data['fetched_at'] = int(time.time())
        new_token_data['expires_at'] = int(time.time()) + config.TOKEN_EXPIRE_TIME
        
        mock_refresh.return_value = new_token_data
        
        # 保存過期 Token
        self.token_manager.save_tokens(self.expired_token_data)
        
        # 嘗試刷新
        result = self.token_manager.refresh_token_if_needed()
        
        # 驗證結果
        self.assertTrue(result)  # 需要刷新
        mock_refresh.assert_called_once_with(self.expired_token_data['refresh_token'])
        
        # 驗證新 Token 已保存
        loaded_tokens = self.token_manager.load_tokens()
        self.assertEqual(loaded_tokens['access_token'], new_token_data['access_token'])
    
    @patch('agents.linkshare_agent.token_manager.TikTokAuth.refresh_access_token')
    def test_get_valid_token_with_cache(self, mock_refresh):
        """測試緩存機制"""
        # 保存有效 Token
        self.token_manager.save_tokens(self.mock_token_data)
        
        # 第一次調用
        token1 = self.token_manager.get_valid_token()
        
        # 第二次調用（應該使用緩存）
        token2 = self.token_manager.get_valid_token()
        
        # 驗證結果
        self.assertEqual(token1, token2)
        self.assertEqual(token1, self.mock_token_data['access_token'])
        mock_refresh.assert_not_called()
    
    def test_validate_storage_permissions(self):
        """測試存儲權限驗證"""
        result = self.token_manager.validate_storage_permissions()
        self.assertTrue(result)
    
    def test_token_file_permissions(self):
        """測試 Token 文件權限設置"""
        # 保存 Token
        self.token_manager.save_tokens(self.mock_token_data)
        
        # 檢查文件權限
        file_stat = self.temp_token_file.stat()
        permissions = oct(file_stat.st_mode)[-3:]
        
        # 驗證權限 (600 = 僅所有者可讀寫)
        self.assertEqual(permissions, "600")
    
    def test_backup_functionality(self):
        """測試備份功能"""
        # 第一次保存
        self.token_manager.save_tokens(self.mock_token_data)
        
        # 第二次保存（應該創建備份）
        new_data = self.mock_token_data.copy()
        new_data['access_token'] = "TTP_new_token"
        self.token_manager.save_tokens(new_data)
        
        # 檢查備份文件是否存在
        backup_file = self.temp_token_file.with_suffix('.conf.backup')
        self.assertTrue(backup_file.exists())
        
        # 驗證備份內容
        with open(backup_file, 'r') as f:
            backup_data = json.load(f)
        self.assertEqual(backup_data['access_token'], self.mock_token_data['access_token'])
    
    def test_invalid_json_handling(self):
        """測試無效 JSON 文件的處理"""
        # 創建無效的 JSON 文件
        with open(self.temp_token_file, 'w') as f:
            f.write("invalid json content")
        
        # 嘗試加載
        result = self.token_manager.load_tokens()
        
        # 驗證結果
        self.assertIsNone(result)

if __name__ == '__main__':
    # 設置測試日誌級別
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    # 運行測試
    unittest.main(verbosity=2) 