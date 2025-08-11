#!/usr/bin/env python3
"""
Field Mapping Manager - 欄位映射管理器
負責將不同平台的欄位映射到標準欄位，並進行數據轉換
整合 Unified Field Mapper 確保所有 unified fields 都出現在輸出中
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd

from .google_sheets_manager import GoogleSheetsManager
from .unified_field_mapper import UnifiedFieldMapper

class FieldMappingManager:
    """欄位映射管理器"""
    
    def __init__(self, config_file: str = "config/field_mapping_config.json"):
        """
        初始化欄位映射管理器
        
        Args:
            config_file: 配置文件路徑
        """
        self.config_file = config_file
        self.logger = logging.getLogger(__name__)
        self.config = self._load_config()
        
        # 初始化Google Sheets管理器
        self.sheets_manager = None
        if self.config.get("google_sheets", {}).get("enabled", False):
            credentials_file = self.config["google_sheets"]["credentials_file"]
            if os.path.exists(credentials_file):
                self.sheets_manager = GoogleSheetsManager(
                    credentials_file=credentials_file,
                    cache_duration=self.config["google_sheets"].get("cache_duration", 300)
                )
        
        # 載入欄位映射
        self.field_mappings = self._load_field_mappings()
        
        # 標準欄位定義
        self.standard_fields = self.config.get("standard_fields", {})
        
        # 初始化統一欄位映射器
        self.unified_mapper = UnifiedFieldMapper()
    
    def _load_config(self) -> Dict[str, Any]:
        """載入配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                self.logger.warning(f"配置文件不存在: {self.config_file}")
                return {}
        except Exception as e:
            self.logger.error(f"載入配置文件失敗: {e}")
            return {}
    
    def _load_field_mappings(self) -> Dict[str, Any]:
        """載入欄位映射"""
        # 優先從Google Sheets載入
        if self.sheets_manager:
            try:
                spreadsheet_id = self.config["google_sheets"]["spreadsheet_id"]
                sheet_name = self.config["google_sheets"]["sheet_name"]
                range_name = self.config["google_sheets"]["range"]
                
                mappings = self.sheets_manager.get_field_mappings(
                    spreadsheet_id=spreadsheet_id,
                    sheet_name=sheet_name,
                    range_name=range_name
                )
                
                if mappings and "platforms" in mappings:
                    self.logger.info("成功從Google Sheets載入欄位映射")
                    return mappings
                    
            except Exception as e:
                self.logger.error(f"從Google Sheets載入欄位映射失敗: {e}")
        
        # 降級到本地配置
        fallback_file = self.config.get("fallback_config", {}).get("local_file", "config/field_mappings.json")
        if os.path.exists(fallback_file):
            try:
                with open(fallback_file, 'r', encoding='utf-8') as f:
                    mappings = json.load(f)
                    self.logger.info("成功從本地配置載入欄位映射")
                    return mappings
            except Exception as e:
                self.logger.error(f"載入本地欄位映射失敗: {e}")
        
        # 返回默認配置
        self.logger.warning("使用默認欄位映射配置")
        return self._get_default_mappings()
    
    def _get_default_mappings(self) -> Dict[str, Any]:
        """獲取默認欄位映射（基於 Google Sheets 標準欄位）"""
        return {
            "platforms": {
                "involve_asia": {
                    "field_mappings": {
                        "conversion_id": "Conversion ID",
                        "offer_id": "Offer ID",
                        "offer_name": "Offer Name",
                        "order_id": "Order ID",
                        "datetime_conversion": "Conversion Date",
                        "sale_amount": "Sale Amount (USD)",
                        "payout": "Payout (USD)",
                        "currency": "Currency",
                        "conversion_status": "Status",
                        "platform": "Platform",
                        "advertiser_name": "Advertiser Name",
                        "campaign_name": "Campaign Name",
                        "publisher_id": "Publisher ID",
                        "publisher_name": "Publisher Name",
                        "source_file": "Source File",
                        "processed_date": "Processed Date",
                        "aff_sub": "Aff Sub",
                        "aff_sub1": "Aff Sub1",
                        "aff_sub2": "Aff Sub2",
                        "aff_sub3": "Aff Sub3",
                        "aff_sub4": "Aff Sub4",
                        "aff_sub5": "Aff Sub5",
                        "adv_sub": "Adv Sub",
                        "adv_sub1": "Adv Sub1",
                        "adv_sub2": "Adv Sub2",
                        "adv_sub3": "Adv Sub3",
                        "adv_sub4": "Adv Sub4",
                        "adv_sub5": "Adv Sub5",
                        "raw_data": "Raw Data"
                    },
                    "data_transformations": {
                        "sale_amount": {"type": "currency", "currency": "USD"},
                        "payout": {"type": "currency", "currency": "USD"},
                        "datetime_conversion": {"type": "date", "format": "%Y-%m-%d"}
                    }
                },
                "access_trade": {
                    "field_mappings": {
                        "Advertiser": "Campaign ID",
                        "Conversion ID": "Campaign Name",
                        "Datetime Conversion": "Status",
                        "Local Sale Amount": "Total Price",
                        "Local Reward": "Reward",
                        "Status": "Customer Type",
                        "Publisher Sub ID 1": "aff_sub",
                        "Publisher Sub ID 2": "aff_sub2",
                        "Publisher Sub ID 3": "aff_sub3",
                        "Customer Type": "Customer Type",
                        "Category ID": "Category ID",
                        "Product ID": "Product ID"
                    },
                    "data_transformations": {
                        "Local Sale Amount": {"type": "currency", "currency": "USD"},
                        "Local Reward": {"type": "currency", "currency": "USD"},
                        "Datetime Conversion": {"type": "date", "format": "%Y-%m-%d %H:%M:%S"}
                    }
                },
                "shopee": {
                    "field_mappings": {
                        "conversion_id": "Conversion ID",
                        "offer_id": "Offer ID",
                        "offer_name": "Product Name",
                        "order_id": "Order ID",
                        "datetime_conversion": "Conversion Date",
                        "sale_amount": "Revenue",
                        "payout": "Commission",
                        "currency": "Currency",
                        "conversion_status": "Status",
                        "platform": "Platform",
                        "advertiser_name": "Advertiser Name",
                        "campaign_name": "Campaign Name",
                        "publisher_id": "Publisher ID",
                        "publisher_name": "Publisher Name",
                        "source_file": "Source File",
                        "processed_date": "Processed Date",
                        "aff_sub": "Aff Sub",
                        "aff_sub1": "Aff Sub1",
                        "aff_sub2": "Aff Sub2",
                        "aff_sub3": "Aff Sub3",
                        "aff_sub4": "Aff Sub4",
                        "aff_sub5": "Aff Sub5",
                        "adv_sub": "Adv Sub",
                        "adv_sub1": "Adv Sub1",
                        "adv_sub2": "Adv Sub2",
                        "adv_sub3": "Adv Sub3",
                        "adv_sub4": "Adv Sub4",
                        "adv_sub5": "Adv Sub5",
                        "raw_data": "Raw Data"
                    },
                    "data_transformations": {
                        "sale_amount": {"type": "currency", "currency": "USD"},
                        "payout": {"type": "currency", "currency": "USD"},
                        "datetime_conversion": {"type": "date", "format": "%Y-%m-%d"}
                    }
                },
                "tiktok_shop": {
                    "field_mappings": {
                        "conversion_id": "Conversion ID",
                        "offer_id": "Offer ID",
                        "offer_name": "Product Name",
                        "order_id": "Order ID",
                        "datetime_conversion": "Conversion Date",
                        "sale_amount": "Revenue",
                        "payout": "Commission",
                        "currency": "Currency",
                        "conversion_status": "Status",
                        "platform": "Platform",
                        "advertiser_name": "Advertiser Name",
                        "campaign_name": "Campaign Name",
                        "publisher_id": "Publisher ID",
                        "publisher_name": "Publisher Name",
                        "source_file": "Source File",
                        "processed_date": "Processed Date",
                        "aff_sub": "Aff Sub",
                        "aff_sub1": "Aff Sub1",
                        "aff_sub2": "Aff Sub2",
                        "aff_sub3": "Aff Sub3",
                        "aff_sub4": "Aff Sub4",
                        "aff_sub5": "Aff Sub5",
                        "adv_sub": "Adv Sub",
                        "adv_sub1": "Adv Sub1",
                        "adv_sub2": "Adv Sub2",
                        "adv_sub3": "Adv Sub3",
                        "adv_sub4": "Adv Sub4",
                        "adv_sub5": "Adv Sub5",
                        "raw_data": "Raw Data"
                    },
                    "data_transformations": {
                        "sale_amount": {"type": "currency", "currency": "USD"},
                        "payout": {"type": "currency", "currency": "USD"},
                        "datetime_conversion": {"type": "date", "format": "%Y-%m-%d"}
                    }
                },
                "linkshare": {
                    "field_mappings": {
                        "conversion_id": "Conversion ID",
                        "offer_id": "Offer ID",
                        "offer_name": "Product Name",
                        "order_id": "Order ID",
                        "datetime_conversion": "Conversion Date",
                        "sale_amount": "Actual standard commission",
                        "payout": "Commission",
                        "currency": "Currency",
                        "conversion_status": "Status",
                        "platform": "Platform",
                        "advertiser_name": "Shop name",
                        "campaign_name": "Content Type",
                        "publisher_id": "Creator username",
                        "publisher_name": "Creator username",
                        "source_file": "Source File",
                        "processed_date": "Processed Date",
                        "aff_sub": "Aff Sub",
                        "aff_sub1": "Aff Sub1",
                        "aff_sub2": "Aff Sub2",
                        "aff_sub3": "Aff Sub3",
                        "aff_sub4": "Aff Sub4",
                        "aff_sub5": "Aff Sub5",
                        "adv_sub": "Adv Sub",
                        "adv_sub1": "Adv Sub1",
                        "adv_sub2": "Adv Sub2",
                        "adv_sub3": "Adv Sub3",
                        "adv_sub4": "Adv Sub4",
                        "adv_sub5": "Adv Sub5",
                        "raw_data": "Raw Data"
                    },
                    "data_transformations": {
                        "sale_amount": {"type": "currency", "currency": "USD"},
                        "payout": {"type": "currency", "currency": "USD"},
                        "datetime_conversion": {"type": "date", "format": "%Y-%m-%d"}
                    }
                }
            },
            "standard_fields": [
                "platform",
                "advertiser_name",
                "campaign_name",
                "offer_name",
                "conversion_amount",
                "conversion_date",
                "currency",
                "publisher_id",
                "publisher_name",
                "source_file",
                "processed_date"
            ]
        }
    
    def map_dataframe_columns(self, df: pd.DataFrame, platform: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        將DataFrame的欄位映射到統一欄位格式
        
        Args:
            df: 原始DataFrame
            platform: 平台名稱
            
        Returns:
            Tuple[pd.DataFrame, Dict]: 映射後的DataFrame和映射信息
        """
        # 使用get_platform_mapping_info获取完整配置（支援非AT_BM平台的本地映射）
        platform_info = self.get_platform_mapping_info(platform)
        if "error" in platform_info:
            self.logger.warning(f"平台 {platform} 沒有找到欄位映射配置")
            # 返回包含所有必須 unified fields 的空 DataFrame
            empty_df = self.unified_mapper.map_dataframe_to_unified_fields(pd.DataFrame(), {})
            return empty_df, platform_info
        
        field_mappings = platform_info["field_mappings"]
        data_transformations = platform_info["data_transformations"]
        
        # 使用統一欄位映射器進行映射
        unified_df = self.unified_mapper.map_dataframe_to_unified_fields(df, field_mappings)
        
        # 應用數據轉換
        if data_transformations:
            unified_df = self.unified_mapper.apply_data_transformations(unified_df, data_transformations)
        
        # 驗證映射結果，使用Google Sheets定義的字段
        validation_result = self.unified_mapper.validate_unified_fields(unified_df, field_mappings)
        
        # 生成映射報告
        mapping_report = self.unified_mapper.get_field_mapping_report(field_mappings)
        
        # 生成映射详情
        mapped_columns = []
        unmapped_columns = []
        
        for target_field, source_field in field_mappings.items():
            if source_field and source_field in df.columns:
                mapped_columns.append({
                    "source": source_field,
                    "target": target_field
                })
            elif source_field:
                unmapped_columns.append(source_field)
        
        mapping_info = {
            "platform": platform,
            "validation": validation_result,
            "mapping_report": mapping_report,
            "original_columns": list(df.columns),
            "unified_columns": list(unified_df.columns),
            "transformations_applied": list(data_transformations.keys()),
            "mapped_columns": mapped_columns,
            "unmapped_columns": unmapped_columns
        }
        
        self.logger.info(f"欄位映射完成: {validation_result['present_count']}/{validation_result['total_required_fields']} 個必須欄位已映射")
        
        return unified_df, mapping_info
    
    def validate_mapping(self, df: pd.DataFrame, platform: str) -> Dict[str, Any]:
        """
        驗證欄位映射
        
        Args:
            df: DataFrame
            platform: 平台名稱
            
        Returns:
            Dict: 驗證結果
        """
        if platform not in self.field_mappings.get("platforms", {}):
            return {
                "is_valid": False,
                "error": f"平台 {platform} 沒有找到欄位映射配置"
            }
        
        platform_config = self.field_mappings["platforms"][platform]
        field_mappings = platform_config.get("field_mappings", {})
        
        # 使用統一欄位映射器進行驗證，使用Google Sheets定義的字段
        validation_result = self.unified_mapper.validate_unified_fields(df, field_mappings)
        mapping_report = self.unified_mapper.get_field_mapping_report(field_mappings)
        
        return {
            "is_valid": validation_result["is_valid"],
            "validation": validation_result,
            "mapping_report": mapping_report,
            "platform": platform
        }
    
    def get_available_platforms(self) -> List[str]:
        """獲取可用的平台列表"""
        return list(self.field_mappings.get("platforms", {}).keys())
    
    def get_platform_mapping_info(self, platform: str) -> Dict[str, Any]:
        """獲取平台的映射信息"""
        # 只有AT_BM相關平台才使用Google Sheets配置
        is_at_bm_platform = platform.lower() in ['access_trade', 'at_bm']
        
        if is_at_bm_platform:
            # AT_BM平台：使用Google Sheets配置
            if platform not in self.field_mappings.get("platforms", {}):
                return {"error": f"平台 {platform} 沒有找到映射配置"}
            
            platform_config = self.field_mappings["platforms"][platform]
            field_mappings = platform_config.get("field_mappings", {}).copy()
            data_transformations = platform_config.get("data_transformations", {}).copy()
            
            self.logger.info(f"AT_BM平台使用Google Sheets配置，統一字段數: {len(field_mappings)}")
            
            return {
                "platform": platform,
                "field_mappings": field_mappings,
                "data_transformations": data_transformations,
                "mapping_report": self.unified_mapper.get_field_mapping_report(field_mappings)
            }
        else:
            # 非AT_BM平台：使用本地預設映射
            self.logger.info(f"非AT_BM平台 ({platform}) 使用本地預設映射")
            
            # 返回預設的involve_asia映射配置
            if platform.lower() == 'involve_asia':
                field_mappings = {
                    'Conversion ID': 'Conversion ID',
                    'Datetime Conversion': 'Conversion Date',
                    'USD Sale Amount': 'Sale Amount (USD)',
                    'Advertiser': 'Advertiser',
                    'Order ID': 'Order ID',
                    'Status': 'Status',
                    'Publisher Sub ID 1': 'Publisher Sub ID 1',
                    'Publisher Sub ID 2': 'Publisher Sub ID 2',
                    'Publisher Sub ID 3': 'Publisher Sub ID 3',
                    'Publisher Sub ID 4': 'Publisher Sub ID 4',
                    'Publisher Sub ID 5': 'Publisher Sub ID 5',
                    'Advertiser Sub ID 2': 'Advertiser Sub ID 2',
                    'Advertiser Sub ID 3': 'Advertiser Sub ID 3',
                    'Advertiser Sub ID 4': 'Advertiser Sub ID 4',
                    'Advertiser Sub ID 5': 'Advertiser Sub ID 5'
                }
                
                data_transformations = {
                    'Datetime Conversion': {'type': 'datetime', 'format': '%Y-%m-%d %H:%M:%S'}
                }
                
                self.logger.info(f"使用involve_asia預設映射，統一字段數: {len(field_mappings)}")
                
                return {
                    "platform": platform,
                    "field_mappings": field_mappings,
                    "data_transformations": data_transformations,
                    "mapping_report": self.unified_mapper.get_field_mapping_report(field_mappings)
                }
            elif platform.lower() == 'linkshare':
                # Linkshare平台：定义核心unified fields
                field_mappings = {
                    'Conversion ID': 'conversion_id',
                    'Order ID': 'order_id', 
                    'Datetime Conversion': 'datetime_conversion',
                    'USD Sale Amount': 'usd_sale_amount',
                    'Local Sale Amount': 'local_sale_amount',
                    'Local Reward': 'payout',
                    'Status': 'conversion_status',
                    'Platform': 'platform',
                    'Advertiser': 'advertiser_name',
                    'Campaign Name': 'campaign_name',
                    'Partner': 'partner',
                    'Publisher Sub ID 1': 'aff_sub',
                    'Publisher Sub ID 2': 'aff_sub1',
                    'Publisher Sub ID 3': 'aff_sub2'
                }
                
                data_transformations = {
                    'Datetime Conversion': {'type': 'datetime', 'format': '%Y-%m-%d %H:%M:%S'},
                    'USD Sale Amount': {'type': 'currency', 'currency': 'USD'},
                    'Local Sale Amount': {'type': 'currency', 'currency': 'IDR'}
                }
                
                self.logger.info(f"使用linkshare預設映射，統一字段數: {len(field_mappings)}")
                
                return {
                    "platform": platform,
                    "field_mappings": field_mappings,
                    "data_transformations": data_transformations,
                    "mapping_report": self.unified_mapper.get_field_mapping_report(field_mappings)
                }
            else:
                # 其他平台的預設配置
                return {"error": f"平台 {platform} 沒有找到映射配置"}
        
    
    def refresh_mappings(self) -> bool:
        """刷新欄位映射（重新從Google Sheets或本地配置載入）"""
        try:
            self.field_mappings = self._load_field_mappings()
            self.logger.info("欄位映射已刷新")
            return True
        except Exception as e:
            self.logger.error(f"刷新欄位映射失敗: {e}")
            return False
    
    def export_mappings_to_json(self, output_file: str) -> bool:
        """導出欄位映射到JSON文件"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.field_mappings, f, indent=2, ensure_ascii=False)
            self.logger.info(f"欄位映射已導出到: {output_file}")
            return True
        except Exception as e:
            self.logger.error(f"導出欄位映射失敗: {e}")
            return False 