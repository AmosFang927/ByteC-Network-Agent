#!/usr/bin/env python3
"""
Enhanced Data Processor - 增強版數據處理器
集成欄位映射、平台識別和標準化處理功能
"""

import pandas as pd
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

# 導入現有模組
from .data_processor import DataProcessor
from .field_mapping_manager import FieldMappingManager
from .platform_detector import PlatformDetector

class EnhancedDataProcessor(DataProcessor):
    """增強版數據處理器"""
    
    def __init__(self, enable_field_mapping: bool = True):
        """
        初始化增強版數據處理器
        
        Args:
            enable_field_mapping: 是否啟用欄位映射功能
        """
        super().__init__()
        
        self.enable_field_mapping = enable_field_mapping
        self.logger = logging.getLogger(__name__)
        
        # 初始化欄位映射管理器
        if self.enable_field_mapping:
            self.field_mapping_manager = FieldMappingManager()
            self.platform_detector = PlatformDetector()
        else:
            self.field_mapping_manager = None
            self.platform_detector = None
        
        # 處理元數據
        self.processing_metadata = {
            "source_file": None,
            "detected_platform": None,
            "field_mapping_applied": False,
            "mapping_info": {},
            "processing_timestamp": None
        }
    
    def process_data_with_mapping(self, data_source, output_dir=None, 
                                platform=None, auto_detect_platform=True,
                                **kwargs):
        """
        帶欄位映射的數據處理流程
        
        Args:
            data_source: 數據源
            output_dir: 輸出目錄
            platform: 指定平台（如果為None則自動檢測）
            auto_detect_platform: 是否自動檢測平台
            **kwargs: 其他參數
            
        Returns:
            dict: 處理結果摘要
        """
        self.logger.info("開始增強版數據處理流程")
        
        # 記錄處理開始時間
        self.processing_metadata["processing_timestamp"] = datetime.now().isoformat()
        
        # 步驟1: 加載數據
        self._load_data(data_source)
        
        # 步驟2: 平台識別
        if self.enable_field_mapping and auto_detect_platform:
            platform = self._detect_platform(data_source)
            self.processing_metadata["detected_platform"] = platform
        
        # 步驟3: 欄位映射（如果啟用）
        if self.enable_field_mapping and platform:
            self._apply_field_mapping(platform)
        
        # 步驟4: 執行原有的數據處理流程
        result = super().process_data(data_source, output_dir, **kwargs)
        
        # 步驟5: 添加處理元數據
        result["processing_metadata"] = self.processing_metadata
        
        self.logger.info("增強版數據處理流程完成")
        return result
    
    def _detect_platform(self, data_source) -> Optional[str]:
        """
        檢測數據平台
        
        Args:
            data_source: 數據源
            
        Returns:
            str: 檢測到的平台名稱
        """
        if not self.platform_detector:
            return None
        
        try:
            # 根據數據源類型進行平台檢測
            if isinstance(data_source, str):
                # 文件路徑
                platform = self.platform_detector.detect_platform(
                    file_path=data_source, 
                    df=self.original_data
                )
            elif isinstance(data_source, pd.DataFrame):
                # DataFrame
                platform = self.platform_detector.detect_platform(df=data_source)
            else:
                # 其他類型
                platform = self.platform_detector.detect_platform(df=self.original_data)
            
            self.logger.info(f"檢測到平台: {platform}")
            return platform
            
        except Exception as e:
            self.logger.error(f"平台檢測失敗: {e}")
            return None
    
    def _apply_field_mapping(self, platform: str):
        """
        應用欄位映射
        
        Args:
            platform: 平台名稱
        """
        if not self.field_mapping_manager or not self.original_data is not None:
            return
        
        try:
            # 執行欄位映射
            mapped_df, mapping_info = self.field_mapping_manager.map_dataframe_columns(
                self.original_data, platform
            )
            
            if not mapped_df.empty:
                # 更新原始數據為映射後的數據
                self.original_data = mapped_df
                self.processing_metadata["field_mapping_applied"] = True
                self.processing_metadata["mapping_info"] = mapping_info
                
                self.logger.info(f"欄位映射完成: {len(mapping_info.get('mapped_columns', []))} 個欄位已映射")
            else:
                self.logger.warning("欄位映射失敗，使用原始數據")
                
        except Exception as e:
            self.logger.error(f"欄位映射失敗: {e}")
    
    def validate_data_structure(self, platform: str = None) -> Dict[str, Any]:
        """
        驗證數據結構
        
        Args:
            platform: 平台名稱
            
        Returns:
            Dict: 驗證結果
        """
        if not self.original_data is not None:
            return {"valid": False, "error": "沒有數據可驗證"}
        
        validation_result = {
            "valid": True,
            "total_rows": len(self.original_data),
            "total_columns": len(self.original_data.columns),
            "columns": list(self.original_data.columns),
            "missing_values": self.original_data.isnull().sum().to_dict()
        }
        
        # 如果指定了平台，進行平台特定的驗證
        if platform and self.field_mapping_manager:
            platform_validation = self.field_mapping_manager.validate_mapping(
                self.original_data, platform
            )
            validation_result.update(platform_validation)
        
        return validation_result
    
    def get_processing_summary(self) -> Dict[str, Any]:
        """
        獲取處理摘要
        
        Returns:
            Dict: 處理摘要
        """
        summary = {
            "processing_metadata": self.processing_metadata,
            "data_info": {
                "total_rows": len(self.original_data) if self.original_data is not None else 0,
                "total_columns": len(self.original_data.columns) if self.original_data is not None else 0
            }
        }
        
        if self.processing_metadata["field_mapping_applied"]:
            mapping_info = self.processing_metadata["mapping_info"]
            summary["mapping_summary"] = {
                "platform": mapping_info.get("platform"),
                "mapped_columns": len(mapping_info.get("mapped_columns", [])),
                "unmapped_columns": len(mapping_info.get("unmapped_columns", [])),
                "transformations_applied": len(mapping_info.get("transformations_applied", []))
            }
        
        return summary
    
    def export_standardized_data(self, output_path: str, format: str = "excel") -> bool:
        """
        導出標準化數據
        
        Args:
            output_path: 輸出路徑
            format: 輸出格式 (excel, csv, json)
            
        Returns:
            bool: 是否成功
        """
        try:
            if self.original_data is None or self.original_data.empty:
                self.logger.error("沒有數據可導出")
                return False
            
            if format.lower() == "excel":
                self.original_data.to_excel(output_path, index=False)
            elif format.lower() == "csv":
                self.original_data.to_csv(output_path, index=False)
            elif format.lower() == "json":
                self.original_data.to_json(output_path, orient="records", indent=2)
            else:
                self.logger.error(f"不支持的輸出格式: {format}")
                return False
            
            self.logger.info(f"標準化數據已導出到: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"導出標準化數據失敗: {e}")
            return False
    
    def get_available_platforms(self) -> List[str]:
        """獲取可用的平台列表"""
        if self.platform_detector:
            return self.platform_detector.get_all_platforms()
        return []
    
    def get_platform_mapping_info(self, platform: str) -> Dict[str, Any]:
        """獲取平台映射信息"""
        if self.field_mapping_manager:
            return self.field_mapping_manager.get_platform_mapping_info(platform)
        return {}
    
    def refresh_field_mappings(self) -> bool:
        """刷新欄位映射"""
        if self.field_mapping_manager:
            return self.field_mapping_manager.refresh_mappings()
        return False 