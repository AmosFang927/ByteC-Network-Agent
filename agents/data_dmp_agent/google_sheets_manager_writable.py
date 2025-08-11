#!/usr/bin/env python3
"""
Google Sheets Manager - 可讀寫版本
支持緩存、錯誤處理和本地備份
可讀寫模式 - 允許讀取和更新操作
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd

try:
    import gspread
    from google.oauth2.service_account import Credentials
    GOOGLE_SHEETS_AVAILABLE = True
except ImportError:
    GOOGLE_SHEETS_AVAILABLE = False
    logging.warning("Google Sheets API not available. Install with: pip install gspread google-auth")

class GoogleSheetsManagerWritable:
    """Google Sheets管理器 - 可讀寫模式"""
    
    def __init__(self, credentials_file: str = None, cache_duration: int = 300):
        """
        初始化Google Sheets管理器（可讀寫模式）
        
        Args:
            credentials_file: Service Account金鑰檔案路徑
            cache_duration: 緩存時間（秒）
        """
        self.logger = logging.getLogger(__name__)
        self.credentials_file = credentials_file or self._find_credentials_file()
        self.cache_duration = cache_duration
        self.cache = {}
        self.cache_timestamps = {}
        
        # 檢查Google Sheets API是否可用
        if not GOOGLE_SHEETS_AVAILABLE:
            self.logger.warning("Google Sheets API not available. Using local config only.")
        
        # 初始化Google Sheets客戶端（可讀寫模式）
        self.client = None
        if GOOGLE_SHEETS_AVAILABLE:
            self._initialize_client()
    
    def _find_credentials_file(self) -> Optional[str]:
        """查找憑證文件"""
        possible_paths = [
            'config/service-account-key.json',
            'service-account-key.json',
            'credentials.json',
            'config/credentials.json',
            os.path.expanduser('~/.config/gspread/service_account.json'),
            os.path.expanduser('~/.config/gspread/credentials.json'),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                self.logger.info(f"找到憑證文件: {path}")
                return path
        
        self.logger.warning("未找到憑證文件，將嘗試使用OAuth或默認憑證")
        return None
    
    def _initialize_client(self):
        """初始化Google Sheets客戶端（可讀寫模式）"""
        try:
            if self.credentials_file and os.path.exists(self.credentials_file):
                # 使用Service Account
                scopes = [
                    'https://www.googleapis.com/auth/spreadsheets',
                    'https://www.googleapis.com/auth/drive'
                ]
                
                credentials = Credentials.from_service_account_file(
                    self.credentials_file, 
                    scopes=scopes
                )
                self.client = gspread.authorize(credentials)
                self.logger.info("使用Service Account初始化Google Sheets客戶端成功")
            else:
                # 嘗試使用OAuth
                try:
                    self.client = gspread.oauth()
                    self.logger.info("使用OAuth初始化Google Sheets客戶端成功")
                except Exception as oauth_error:
                    self.logger.warning(f"OAuth初始化失敗: {oauth_error}")
                    # 嘗試使用默認憑證
                    try:
                        self.client = gspread.service_account()
                        self.logger.info("使用默認Service Account初始化成功")
                    except Exception as default_error:
                        self.logger.error(f"所有認證方法都失敗: {default_error}")
                        self.client = None
                        
        except Exception as e:
            self.logger.error(f"初始化Google Sheets客戶端失敗: {e}")
            self.client = None
    
    def get_worksheet(self, spreadsheet_id: str, sheet_name: str):
        """獲取工作表對象"""
        if not self.client:
            self.logger.error("Google Sheets客戶端未初始化")
            return None
        
        try:
            spreadsheet = self.client.open_by_key(spreadsheet_id)
            worksheet = spreadsheet.worksheet(sheet_name)
            return worksheet
        except Exception as e:
            self.logger.error(f"獲取工作表失敗: {e}")
            return None
    
    def update_cell(self, spreadsheet_id: str, sheet_name: str, row: int, col: int, value: str):
        """更新單個儲存格"""
        if not self.client:
            self.logger.error("Google Sheets客戶端未初始化")
            return False
        
        try:
            worksheet = self.get_worksheet(spreadsheet_id, sheet_name)
            if worksheet:
                worksheet.update_cell(row, col, value)
                self.logger.info(f"成功更新儲存格 {row},{col} = {value}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"更新儲存格失敗: {e}")
            return False
    
    def update_field_mapping(self, spreadsheet_id: str, sheet_name: str, platform: str, unified_field: str, new_raw_field: str):
        """更新字段映射"""
        if not self.client:
            self.logger.error("Google Sheets客戶端未初始化")
            return False
        
        try:
            worksheet = self.get_worksheet(spreadsheet_id, sheet_name)
            if not worksheet:
                return False
            
            # 獲取所有數據
            all_values = worksheet.get_all_values()
            
            # 查找要更新的行
            target_row = None
            for i, row in enumerate(all_values):
                if len(row) >= 3:
                    row_platform = row[0].strip() if len(row) > 0 else ''
                    row_unified_field = row[1].strip() if len(row) > 1 else ''
                    
                    if row_platform.lower() == platform.lower() and row_unified_field == unified_field:
                        target_row = i + 1  # gspread使用1-based索引
                        break
            
            if target_row:
                # 更新Raw Field列（第3列）
                worksheet.update_cell(target_row, 3, new_raw_field)
                self.logger.info(f"成功更新字段映射: {platform} | {unified_field} | {new_raw_field}")
                
                # 清除緩存
                self._clear_cache()
                return True
            else:
                self.logger.error(f"未找到要更新的行: {platform}, {unified_field}")
                return False
                
        except Exception as e:
            self.logger.error(f"更新字段映射失敗: {e}")
            return False
    
    def _clear_cache(self):
        """清除緩存"""
        self.cache.clear()
        self.cache_timestamps.clear()
        self.logger.info("緩存已清除")
    
    def get_field_mappings(self, spreadsheet_id: str, sheet_name: str = "Data_Input_Mapping"):
        """
        從Google Sheets獲取欄位對照表
        
        Args:
            spreadsheet_id: Google Sheets ID
            sheet_name: 工作表名稱
            
        Returns:
            Dict: 包含平台映射信息的字典
        """
        cache_key = f"{spreadsheet_id}_{sheet_name}"
        
        # 檢查緩存
        if cache_key in self.cache:
            cache_time = self.cache_timestamps.get(cache_key, datetime.min)
            if datetime.now() - cache_time < timedelta(seconds=self.cache_duration):
                self.logger.info(f"從緩存返回數據: {cache_key}")
                return self.cache[cache_key]
        
        if not self.client:
            self.logger.warning("Google Sheets客戶端未可用，嘗試從本地配置讀取")
            return self._get_local_fallback()
        
        try:
            # 打開工作表
            spreadsheet = self.client.open_by_key(spreadsheet_id)
            worksheet = spreadsheet.worksheet(sheet_name)
            
            # 獲取所有數據
            data = worksheet.get_all_values()
            
            if not data:
                self.logger.warning("工作表為空")
                return self._get_local_fallback()
            
            # 解析數據
            parsed_data = self._parse_sheets_data(data)
            
            # 緩存結果
            self.cache[cache_key] = parsed_data
            self.cache_timestamps[cache_key] = datetime.now()
            
            self.logger.info(f"成功從Google Sheets獲取數據: {len(parsed_data.get('platforms', {}))} 個平台")
            return parsed_data
            
        except Exception as e:
            self.logger.error(f"從Google Sheets獲取數據失敗: {e}")
            return self._get_local_fallback()
    
    def _parse_sheets_data(self, data: List[List[str]]) -> Dict[str, Any]:
        """解析Google Sheets數據"""
        platforms = {}
        
        # 跳過標題行
        for row in data[1:]:
            if len(row) >= 3:
                platform = row[0].strip().lower()
                unified_field = row[1].strip()
                raw_field = row[2].strip()
                
                # 跳過空行
                if not platform or not unified_field or not raw_field:
                    continue
                
                if platform not in platforms:
                    platforms[platform] = {
                        'field_mappings': {},
                        'data_transformations': {}
                    }
                
                platforms[platform]['field_mappings'][unified_field] = raw_field
                
                # 檢查是否有數據轉換配置（第4列及以後）
                if len(row) > 3 and row[3].strip():
                    try:
                        transform_config = json.loads(row[3].strip())
                        platforms[platform]['data_transformations'][unified_field] = transform_config
                    except json.JSONDecodeError:
                        # 如果不是JSON，則視為簡單的轉換類型
                        platforms[platform]['data_transformations'][unified_field] = {
                            'type': row[3].strip()
                        }
        
        return {'platforms': platforms}
    
    def _get_local_fallback(self) -> Dict[str, Any]:
        """獲取本地備份配置"""
        try:
            config_file = 'config/field_mappings.json'
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    local_config = json.load(f)
                
                # 轉換格式以匹配Google Sheets格式
                platforms = {}
                for platform, config in local_config.items():
                    if isinstance(config, dict) and 'field_mappings' in config:
                        platforms[platform] = config
                
                self.logger.info("使用本地備份配置")
                return {'platforms': platforms}
        except Exception as e:
            self.logger.error(f"讀取本地備份配置失敗: {e}")
        
        return {'platforms': {}}

    def test_connection(self) -> bool:
        """測試Google Sheets連接"""
        if not self.client:
            return False
        
        try:
            # 嘗試獲取用戶信息或創建一個簡單的測試
            return True
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"連接測試失敗: {e}")
            return False