#!/usr/bin/env python3
"""
Google Sheets Manager - 用於讀取欄位對照表
支持緩存、錯誤處理和本地備份
只讀模式 - 不允許寫入操作
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

class GoogleSheetsManager:
    """Google Sheets管理器 - 只讀模式"""
    
    _instances = {}  # 類級別的實例緩存
    
    def __new__(cls, credentials_file: str = None, cache_duration: int = 300):
        """使用單例模式避免重複初始化"""
        key = f"{credentials_file}_{cache_duration}"
        if key not in cls._instances:
            cls._instances[key] = super().__new__(cls)
            cls._instances[key]._initialized = False
        return cls._instances[key]
    
    def __init__(self, credentials_file: str = None, cache_duration: int = 300):
        """
        初始化Google Sheets管理器（只讀模式）
        
        Args:
            credentials_file: Service Account金鑰檔案路徑
            cache_duration: 緩存時間（秒）
        """
        # 避免重複初始化
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        self.credentials_file = credentials_file
        self.cache_duration = cache_duration
        self.cache = {}
        self.cache_timestamps = {}
        self.logger = logging.getLogger(__name__)
        
        # 檢查Google Sheets API是否可用
        if not GOOGLE_SHEETS_AVAILABLE:
            self.logger.warning("Google Sheets API not available. Using local config only.")
        
        # 初始化Google Sheets客戶端（只讀模式）
        self.client = None
        if GOOGLE_SHEETS_AVAILABLE and credentials_file:
            self._initialize_client()
            
        self._initialized = True
    
    def _initialize_client(self):
        """初始化Google Sheets客戶端（只讀模式）"""
        try:
            if not os.path.exists(self.credentials_file):
                self.logger.error(f"Credentials file not found: {self.credentials_file}")
                return
            
            # 設置認證範圍 - 只讀權限
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets.readonly',
                'https://www.googleapis.com/auth/drive.readonly'
            ]
            
            # 創建認證 - 使用环境变量强制时间同步
            import time
            
            # 尝试设置环境变量来处理时间偏移
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = self.credentials_file
            
            try:
                credentials = Credentials.from_service_account_file(
                    self.credentials_file, 
                    scopes=scopes
                )
                self.logger.info("✅ JWT认证凭证创建成功")
            except Exception as jwt_error:
                self.logger.warning(f"⚠️ JWT认证失败，尝试重新创建: {jwt_error}")
                # 等待一秒后重试
                time.sleep(1)
                credentials = Credentials.from_service_account_file(
                    self.credentials_file, 
                    scopes=scopes
                )
            
            # 創建客戶端
            self.client = gspread.authorize(credentials)
            self.logger.info("Google Sheets client initialized successfully (READ-ONLY mode)")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Google Sheets client: {e}")
            self.client = None
    
    def get_field_mappings(self, spreadsheet_id: str, sheet_name: str = "FieldMappings", 
                          range_name: str = "A1:Z1000") -> Dict[str, Any]:
        """
        從Google Sheets讀取欄位對照表（只讀）
        
        Args:
            spreadsheet_id: Google Sheets文檔ID
            sheet_name: 工作表名稱
            range_name: 數據範圍
            
        Returns:
            Dict: 欄位對照表
        """
        cache_key = f"{spreadsheet_id}_{sheet_name}_{range_name}"
        
        # 檢查內存緩存
        if self._is_cache_valid(cache_key):
            self.logger.info("Using cached field mappings (memory)")
            return self.cache[cache_key]
        
        # 檢查本地文件緩存
        local_cache_file = f"cache/sheets_{cache_key.replace('/', '_')}.json"
        if self._is_local_cache_valid(local_cache_file):
            self.logger.info("Using cached field mappings (local file)")
            mappings = self._load_local_cache(local_cache_file)
            if mappings:
                self._update_cache(cache_key, mappings)
                return mappings
        
        # 嘗試從Google Sheets讀取
        if self.client:
            try:
                self.logger.info(f"Fetching fresh data from Google Sheets: {spreadsheet_id}")
                mappings = self._read_from_sheets(spreadsheet_id, sheet_name, range_name)
                if mappings:
                    self._update_cache(cache_key, mappings)
                    self._save_local_cache(local_cache_file, mappings)
                    return mappings
            except Exception as e:
                self.logger.error(f"Failed to read from Google Sheets: {e}")
                # 如果有舊的本地緩存，即使過期也使用它
                if os.path.exists(local_cache_file):
                    self.logger.warning("Using expired local cache due to Google Sheets error")
                    mappings = self._load_local_cache(local_cache_file)
                    if mappings:
                        return mappings
        
        # 降級到本地配置
        self.logger.info("Falling back to local configuration")
        return self._get_local_mappings()
    
    def _read_from_sheets(self, spreadsheet_id: str, sheet_name: str, range_name: str) -> Dict[str, Any]:
        """從Google Sheets讀取數據（只讀）"""
        try:
            # 打開文檔
            spreadsheet = self.client.open_by_key(spreadsheet_id)
            
            # 嘗試獲取指定的工作表
            try:
                worksheet = spreadsheet.worksheet(sheet_name)
            except gspread.WorksheetNotFound:
                self.logger.warning(f"Worksheet '{sheet_name}' not found. Available worksheets: {[ws.title for ws in spreadsheet.worksheets()]}")
                # 嘗試使用第一個工作表
                worksheet = spreadsheet.get_worksheet(0)
                if worksheet:
                    self.logger.info(f"Using first worksheet: {worksheet.title}")
                else:
                    self.logger.error("No worksheets found in spreadsheet")
                    return None
            
            # 讀取數據（設置超時時間）
            import socket
            socket.setdefaulttimeout(30)  # 30秒超時
            data = worksheet.get(range_name)
            
            # 解析數據
            mappings = self._parse_sheets_data(data)
            
            self.logger.info(f"Successfully read field mappings from Google Sheets worksheet: {worksheet.title}")
            return mappings
            
        except Exception as e:
            self.logger.error(f"Error reading from Google Sheets: {e}")
            return None
    
    def _parse_sheets_data(self, data: List[List[str]]) -> Dict[str, Any]:
        """解析Google Sheets數據"""
        if not data or len(data) < 2:
            return {}
        
        # 假設第一行是標題
        headers = data[0]
        rows = data[1:]
        
        # 查找關鍵列 - 根據實際格式調整
        platform_col = self._find_column_index(headers, ["Platform", "platform", "平台"])
        source_field_col = self._find_column_index(headers, ["Field", "field", "欄位", "源欄位"])
        target_field_col = self._find_column_index(headers, ["Unitfied Field", "Unified Field", "Target Field", "target_field", "統一欄位", "目標欄位"])
        
        if platform_col is None or source_field_col is None or target_field_col is None:
            self.logger.error(f"Required columns not found in Google Sheets. Headers: {headers}")
            self.logger.error(f"Platform col: {platform_col}, Source field col: {source_field_col}, Target field col: {target_field_col}")
            return {}
        
        # 構建映射
        mappings = {"platforms": {}}
        
        # 處理合併單元格：記錄當前平台
        current_platform = None
        
        for row in rows:
            if len(row) > max(platform_col, source_field_col, target_field_col):
                platform = row[platform_col].strip() if platform_col < len(row) else ""
                source_field = row[source_field_col].strip() if source_field_col < len(row) else ""
                target_field = row[target_field_col].strip() if target_field_col < len(row) else ""
                
                # 更新當前平台：如果Platform欄位有值，使用新值；否則保持前一個值
                if platform:
                    current_platform = platform
                
                # 跳過空行或標題行
                if not source_field or not target_field:
                    continue
                
                # 如果有當前平台，使用它；否則跳過這行
                if current_platform:
                    # 標準化平台名稱
                    platform_normalized = self._normalize_platform_name(current_platform)
                    
                    if platform_normalized:
                        if platform_normalized not in mappings["platforms"]:
                            mappings["platforms"][platform_normalized] = {"field_mappings": {}, "data_transformations": {}}
                        
                        mappings["platforms"][platform_normalized]["field_mappings"][target_field] = source_field
                        
                        # 根據欄位名稱推斷數據類型
                        data_type = self._infer_data_type(target_field)
                        if data_type:
                            mappings["platforms"][platform_normalized]["data_transformations"][target_field] = {
                                "type": data_type
                            }
                else:
                    # 如果沒有當前平台，跳過這行
                    self.logger.warning(f"Skipping row with no platform: {row}")
        
        return mappings
    
    def _normalize_platform_name(self, platform: str) -> str:
        """標準化平台名稱"""
        platform_lower = platform.lower()
        
        # 平台名稱映射
        platform_mapping = {
            "ia_bm": "involve_asia",
            "ia": "involve_asia",
            "involve_asia": "involve_asia",
            "shopee": "shopee",
            "tiktok": "tiktok_shop",
            "tiktok_shop": "tiktok_shop",
            "access_trade": "access_trade",
            "at": "access_trade",
            "at_bm": "access_trade",
            "linkshare": "linkshare",
            "ls_bm": "linkshare",
            "ls": "linkshare"
        }
        
        return platform_mapping.get(platform_lower, platform_lower)
    
    def _infer_data_type(self, field_name: str) -> str:
        """根據欄位名稱推斷數據類型"""
        field_lower = field_name.lower()
        
        if any(keyword in field_lower for keyword in ["amount", "revenue", "sale", "money"]):
            return "currency"
        elif any(keyword in field_lower for keyword in ["date", "time"]):
            return "date"
        elif any(keyword in field_lower for keyword in ["rate", "percentage", "commission"]):
            return "percentage"
        else:
            return "string"
    
    def _find_column_index(self, headers: List[str], possible_names: List[str]) -> Optional[int]:
        """查找列索引"""
        for i, header in enumerate(headers):
            if header.strip() in possible_names:
                return i
        return None
    
    def _get_local_mappings(self) -> Dict[str, Any]:
        """獲取本地映射配置"""
        local_config_path = "config/field_mappings.json"
        
        if os.path.exists(local_config_path):
            try:
                with open(local_config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Failed to load local mappings: {e}")
        
        # 返回默認配置
        return self._get_default_mappings()
    
    def _get_default_mappings(self) -> Dict[str, Any]:
        """獲取默認映射配置"""
        return {
            "platforms": {
                "involve_asia": {
                    "field_mappings": {
                        "advertiser_name": "Advertiser Name",
                        "campaign_name": "Campaign Name",
                        "offer_name": "Offer Name",
                        "conversion_amount": "Sale Amount (USD)",
                        "conversion_date": "Conversion Date"
                    },
                    "data_transformations": {
                        "conversion_amount": {"type": "currency", "currency": "USD"},
                        "conversion_date": {"type": "date", "format": "%Y-%m-%d"}
                    }
                },
                "shopee": {
                    "field_mappings": {
                        "advertiser_name": "Campaign Name",
                        "campaign_name": "Ad Group Name",
                        "offer_name": "Product Name",
                        "conversion_amount": "Revenue",
                        "conversion_date": "Date"
                    },
                    "data_transformations": {
                        "conversion_amount": {"type": "currency", "currency": "USD"},
                        "conversion_date": {"type": "date", "format": "%Y-%m-%d"}
                    }
                }
            }
        }
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """檢查緩存是否有效"""
        if cache_key not in self.cache or cache_key not in self.cache_timestamps:
            return False
        
        timestamp = self.cache_timestamps[cache_key]
        return datetime.now() - timestamp < timedelta(seconds=self.cache_duration)
    
    def _update_cache(self, cache_key: str, data: Dict[str, Any]):
        """更新緩存"""
        self.cache[cache_key] = data
        self.cache_timestamps[cache_key] = datetime.now()
    
    def _is_local_cache_valid(self, cache_file: str) -> bool:
        """檢查本地文件緩存是否有效"""
        if not os.path.exists(cache_file):
            return False
        
        # 檢查文件修改時間（緩存24小時）
        file_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
        return datetime.now() - file_time < timedelta(hours=24)
    
    def _load_local_cache(self, cache_file: str) -> Optional[Dict[str, Any]]:
        """加載本地緩存文件"""
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load local cache {cache_file}: {e}")
            return None
    
    def _save_local_cache(self, cache_file: str, data: Dict[str, Any]):
        """保存到本地緩存文件"""
        try:
            # 確保緩存目錄存在
            os.makedirs(os.path.dirname(cache_file), exist_ok=True)
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.logger.info(f"Saved local cache: {cache_file}")
        except Exception as e:
            self.logger.error(f"Failed to save local cache {cache_file}: {e}")
    
    def clear_cache(self):
        """清除緩存"""
        self.cache.clear()
        self.cache_timestamps.clear()
        self.logger.info("Cache cleared")
    
    def test_connection(self, spreadsheet_id: str) -> bool:
        """測試Google Sheets連接（只讀）"""
        if not self.client:
            self.logger.error("Google Sheets client not initialized")
            return False
        
        try:
            spreadsheet = self.client.open_by_key(spreadsheet_id)
            self.logger.info(f"Successfully connected to spreadsheet: {spreadsheet.title} (READ-ONLY)")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to spreadsheet: {e}")
            return False 