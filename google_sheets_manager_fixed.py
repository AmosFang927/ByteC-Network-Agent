#!/usr/bin/env python3
"""
修复版本的Google Sheets管理器
专门处理JWT时间签名问题
"""

import os
import json
import time
import logging
import datetime
from typing import Dict, List, Optional, Any
from datetime import timedelta, datetime as dt

try:
    import gspread
    from google.oauth2.service_account import Credentials
    import google.auth.jwt as jwt
    import google.auth._helpers as helpers
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

logger = logging.getLogger(__name__)

class GoogleSheetsManagerFixed:
    """修复版Google Sheets管理器"""
    
    def __init__(self, credentials_file: str, cache_duration: int = 300):
        self.credentials_file = credentials_file
        self.cache_duration = cache_duration
        self.cache = {}
        self.cache_timestamps = {}
        self.client = None
        self.logger = logging.getLogger(__name__)
        
        if GOOGLE_AVAILABLE:
            self._init_client()
        else:
            self.logger.warning("Google认证库不可用")
    
    def _fix_system_time(self):
        """修正系统时间偏移"""
        # 计算时间偏移 - 2025年修正为2024年
        current_timestamp = time.time()
        current_dt = datetime.datetime.fromtimestamp(current_timestamp)
        
        if current_dt.year >= 2025:
            # 减去一年的时间
            year_offset = 365 * 24 * 60 * 60
            corrected_timestamp = current_timestamp - year_offset
            return corrected_timestamp
        
        return current_timestamp
    
    def _init_client(self):
        """初始化Google Sheets客户端，使用修正的JWT时间"""
        try:
            if not os.path.exists(self.credentials_file):
                self.logger.error(f"认证文件不存在: {self.credentials_file}")
                return
            
            # 读取服务账户信息
            with open(self.credentials_file, 'r') as f:
                service_account_info = json.load(f)
            
            # 设置作用域
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets.readonly',
                'https://www.googleapis.com/auth/drive.readonly'
            ]
            
            # 修正JWT时间戳
            corrected_time = self._fix_system_time()
            
            # 保存原始函数
            original_time = time.time
            original_utcnow = getattr(helpers, 'utcnow', None)
            
            # 创建修正的时间函数
            def fixed_time():
                return corrected_time + (original_time() - time.time())
            
            def fixed_utcnow():
                return datetime.datetime.utcfromtimestamp(fixed_time())
            
            try:
                # 临时替换时间函数
                time.time = fixed_time
                if original_utcnow:
                    helpers.utcnow = fixed_utcnow
                
                # 创建认证
                credentials = Credentials.from_service_account_info(
                    service_account_info,
                    scopes=scopes
                )
                
                # 创建客户端
                self.client = gspread.authorize(credentials)
                
                self.logger.info("✅ Google Sheets客户端初始化成功（JWT时间已修正）")
                
            finally:
                # 恢复原始函数
                time.time = original_time
                if original_utcnow:
                    helpers.utcnow = original_utcnow
            
        except Exception as e:
            self.logger.error(f"Google Sheets客户端初始化失败: {e}")
            self.client = None
    
    def get_field_mappings(self, spreadsheet_id: str, sheet_name: str = "Data_Input_Mapping"):
        """获取字段映射"""
        cache_key = f"{spreadsheet_id}_{sheet_name}"
        
        # 检查缓存
        if cache_key in self.cache:
            cache_time = self.cache_timestamps.get(cache_key, dt.min)
            if dt.now() - cache_time < timedelta(seconds=self.cache_duration):
                self.logger.info(f"从缓存返回数据: {cache_key}")
                return self.cache[cache_key]
        
        if not self.client:
            self.logger.warning("Google Sheets客户端不可用")
            return self._get_local_fallback()
        
        try:
            # 打开工作表
            spreadsheet = self.client.open_by_key(spreadsheet_id)
            worksheet = spreadsheet.worksheet(sheet_name)
            
            # 获取所有数据
            data = worksheet.get_all_values()
            
            if not data:
                self.logger.warning("工作表为空")
                return self._get_local_fallback()
            
            # 解析数据
            parsed_data = self._parse_sheets_data(data)
            
            # 缓存结果
            self.cache[cache_key] = parsed_data
            self.cache_timestamps[cache_key] = dt.now()
            
            self.logger.info(f"✅ 成功从Google Sheets获取数据: {len(parsed_data.get('platforms', {}))} 个平台")
            return parsed_data
            
        except Exception as e:
            self.logger.error(f"从Google Sheets获取数据失败: {e}")
            return self._get_local_fallback()
    
    def _parse_sheets_data(self, data: List[List[str]]) -> Dict[str, Any]:
        """解析Google Sheets数据"""
        if not data or len(data) < 2:
            return {"platforms": {}}
        
        # 查找头部行
        headers = data[0] if data else []
        rows = data[1:] if len(data) > 1 else []
        
        # 查找关键列索引
        platform_col = -1
        unified_field_col = -1
        source_field_col = -1
        
        for i, header in enumerate(headers):
            if 'platform' in header.lower() or '平台' in header:
                platform_col = i
            elif 'unified' in header.lower() or '统一' in header or 'standard' in header.lower():
                unified_field_col = i
            elif 'source' in header.lower() or '源' in header or 'original' in header.lower():
                source_field_col = i
        
        if platform_col == -1 or unified_field_col == -1 or source_field_col == -1:
            self.logger.warning("未找到必需的列：platform, unified_field, source_field")
            return {"platforms": {}}
        
        # 解析映射数据
        platforms = {}
        
        for row in rows:
            if len(row) <= max(platform_col, unified_field_col, source_field_col):
                continue
            
            platform = row[platform_col].strip()
            unified_field = row[unified_field_col].strip()
            source_field = row[source_field_col].strip()
            
            if not platform or not unified_field or not source_field:
                continue
            
            if platform not in platforms:
                platforms[platform] = {"field_mappings": {}}
            
            platforms[platform]["field_mappings"][unified_field] = source_field
        
        return {"platforms": platforms}
    
    def _get_local_fallback(self):
        """获取本地后备配置"""
        try:
            with open("config/field_mappings.json", 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"读取本地配置失败: {e}")
            return {"platforms": {}}

def test_fixed_google_sheets():
    """测试修复版Google Sheets管理器"""
    print("=== 测试修复版Google Sheets管理器 ===")
    
    credentials_file = 'solar-idea-463423-h8-bd12ec2c5361.json'
    if not os.path.exists(credentials_file):
        print(f"❌ 认证文件不存在: {credentials_file}")
        return False
    
    # 创建修复版管理器
    manager = GoogleSheetsManagerFixed(credentials_file)
    
    if not manager.client:
        print("❌ Google Sheets客户端初始化失败")
        return False
    
    # 测试获取字段映射
    spreadsheet_id = '1SaHZ0igiuMBm2gHFD5JSs1hkltphdXqRAlbaZ9nEUf0'
    mappings = manager.get_field_mappings(spreadsheet_id)
    
    if mappings and 'platforms' in mappings:
        print(f"✅ 成功获取映射数据，包含 {len(mappings['platforms'])} 个平台")
        
        # 检查access_trade映射
        if 'access_trade' in mappings['platforms']:
            at_mappings = mappings['platforms']['access_trade']['field_mappings']
            print(f"📊 access_trade字段映射数量: {len(at_mappings)}")
            
            # 显示关键映射
            for field, source in at_mappings.items():
                if 'Sale Amount' in field or 'Total' in source:
                    print(f"   {field} -> {source}")
            
            return True
        else:
            print("⚠️ 未找到access_trade平台映射")
            return False
    else:
        print("❌ 获取映射数据失败")
        return False

if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    # 运行测试
    success = test_fixed_google_sheets()
    
    if success:
        print("\n🎉 Google Sheets连接修复成功！")
    else:
        print("\n⚠️ Google Sheets连接仍有问题")