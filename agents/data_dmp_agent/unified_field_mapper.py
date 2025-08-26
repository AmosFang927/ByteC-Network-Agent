#!/usr/bin/env python3
"""
Unified Field Mapper - 統一欄位映射器
確保所有 unified field 都出現在輸出中，即使原始 field 為空
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd

logger = logging.getLogger(__name__)

class UnifiedFieldMapper:
    """統一欄位映射器"""
    
    def __init__(self):
        """初始化統一欄位映射器"""
        # 定義所有必須的 unified fields（基於 Google Sheets 標準欄位）
        self.required_unified_fields = [
            'conversion_id',
            'offer_id', 
            'offer_name',
            'order_id',
            'datetime_conversion',
            'sale_amount',
            'payout',
            'currency',
            'conversion_status',
            'platform',
            'advertiser_name',
            'Advertiser',  # 添加Google Sheets中使用的Advertiser字段
            'campaign_name',
            'publisher_id',
            'publisher_name',
            'source_file',
            'processed_date',
            'aff_sub',
            'aff_sub1',
            'aff_sub2', 
            'aff_sub3',
            'aff_sub4',
            'aff_sub5',
            'adv_sub',
            'adv_sub1',
            'adv_sub2',
            'adv_sub3',
            'adv_sub4',
            'adv_sub5',
            'raw_data'
        ]
        
        # 定義欄位類型映射（包含系統預設和Google Sheets定義的字段）
        self.field_types = {
            # 系統預設統一字段
            'conversion_id': 'string',
            'offer_id': 'string', 
            'offer_name': 'string',
            'order_id': 'string',
            'datetime_conversion': 'datetime',
            'sale_amount': 'decimal',
            'payout': 'decimal',
            'currency': 'string',
            'conversion_status': 'string',
            'platform': 'string',
            'advertiser_name': 'string',
            'campaign_name': 'string',
            'publisher_id': 'string',
            'publisher_name': 'string',
            'source_file': 'string',
            'processed_date': 'datetime',
            'aff_sub': 'string',
            'aff_sub1': 'string',
            'aff_sub2': 'string', 
            'aff_sub3': 'string',
            'aff_sub4': 'string',
            'aff_sub5': 'string',
            'adv_sub': 'string',
            'adv_sub1': 'string',
            'adv_sub2': 'string',
            'adv_sub3': 'string',
            'adv_sub4': 'string',
            'adv_sub5': 'string',
            'raw_data': 'json',
                            # Google Sheets中定義的統一字段
                'Advertiser': 'string',
                'Conversion ID': 'string',
                'Datetime Conversion': 'datetime',
                'Local Sale Amount': 'decimal',
                'Local Reward': 'decimal',
                'Status': 'string',
                'Publisher Sub ID 1': 'string',
                'Publisher Sub ID 2': 'string',
                'Publisher Sub ID 3': 'string',
                'Customer Type': 'string',
                'Category ID': 'string',
                'Product ID': 'string',
                # 新增字段
                'Custom Type': 'string',
                'USD Sale Amount': 'decimal',
                'USD Reward': 'decimal'
        }
    
    def map_dataframe_to_unified_fields(self, df: pd.DataFrame, field_mappings: Dict[str, str]) -> pd.DataFrame:
        """
        將 DataFrame 映射到統一欄位格式
        
        Args:
            df: 原始 DataFrame
            field_mappings: 欄位映射字典 {unified_field: source_field}
            
        Returns:
            映射後的 DataFrame，包含Google Sheets中定義的所有統一字段
        """
        logger.info(f"開始映射 DataFrame 到統一欄位格式，原始欄位數: {len(df.columns)}")
        
        # 創建新的 DataFrame 來存儲映射結果，保持原始數據的行數
        unified_df = pd.DataFrame(index=df.index)
        
        # 使用Google Sheets中定義的統一字段列表，而不是系統預設
        google_sheets_unified_fields = list(field_mappings.keys())
        logger.info(f"使用Google Sheets定義的統一字段: {len(google_sheets_unified_fields)}個")
        
        # 映射每個 Google Sheets 中定義的 unified field
        for unified_field in google_sheets_unified_fields:
            source_field = field_mappings.get(unified_field)
            
            if source_field and source_field in df.columns:
                # 如果源欄位存在，直接映射
                unified_df[unified_field] = df[source_field]
                logger.debug(f"映射欄位: {source_field} -> {unified_field}")
            else:
                # 如果源欄位不存在或為空，添加空的 unified field，保持原始行數
                field_type = self.field_types.get(unified_field, 'string')
                default_value = self._get_default_value(field_type)
                unified_df[unified_field] = [default_value] * len(df)
                logger.debug(f"添加空欄位: {unified_field} (類型: {field_type})")
        
        # 添加衍生字段到DataFrame（即使Google Sheets中沒有配置）
        # 移除Custom Type字段，只保留USD相關字段
        derived_fields = ['USD Sale Amount', 'USD Reward']
        for field in derived_fields:
            if field not in unified_df.columns:
                field_type = self.field_types.get(field, 'string')
                default_value = self._get_default_value(field_type)
                unified_df[field] = [default_value] * len(unified_df)
                logger.debug(f"添加衍生字段: {field}")
        
        # 處理衍生字段（需要特殊邏輯的字段）
        unified_df = self._process_derived_fields(unified_df, df)
        
        # 確保包含所有需要的字段（包括衍生字段）
        all_required_fields = google_sheets_unified_fields.copy()
        
        for field in derived_fields:
            if field not in all_required_fields:
                all_required_fields.append(field)
        
        # 確保欄位順序一致，只保留存在的字段
        final_fields = [field for field in all_required_fields if field in unified_df.columns]
        unified_df = unified_df[final_fields]
        
        logger.info(f"映射完成，統一欄位數: {len(unified_df.columns)}，數據行數: {len(unified_df)}")
        return unified_df
    
    def _get_default_value(self, field_type: str) -> Any:
        """根據欄位類型獲取默認值"""
        if field_type == 'string':
            return ''
        elif field_type == 'integer':
            return 0
        elif field_type == 'decimal':
            return 0.0
        elif field_type == 'datetime':
            return pd.NaT
        elif field_type == 'json':
            return '{}'
        else:
            return ''
    
    def validate_unified_fields(self, df: pd.DataFrame, field_mappings: Dict[str, str] = None) -> Dict[str, Any]:
        """
        驗證 DataFrame 是否包含所有必須的 unified fields
        
        Args:
            df: 要驗證的 DataFrame
            field_mappings: 字段映射字典，如果提供則使用Google Sheets定義的字段進行驗證
            
        Returns:
            驗證結果字典
        """
        missing_fields = []
        present_fields = []
        
        # 如果提供了field_mappings，使用Google Sheets定義的字段；否則使用系統預設
        fields_to_validate = list(field_mappings.keys()) if field_mappings else self.required_unified_fields
        
        for field in fields_to_validate:
            if field in df.columns:
                present_fields.append(field)
            else:
                missing_fields.append(field)
        
        validation_result = {
            'is_valid': len(missing_fields) == 0,
            'total_required_fields': len(fields_to_validate),
            'present_fields': present_fields,
            'missing_fields': missing_fields,
            'present_count': len(present_fields),
            'missing_count': len(missing_fields)
        }
        
        field_source = "Google Sheets定義" if field_mappings else "系統預設"
        if validation_result['is_valid']:
            logger.info(f"✅ 所有必須的 unified fields 都存在 ({len(present_fields)}/{len(fields_to_validate)}) - {field_source}")
        else:
            logger.warning(f"⚠️ 缺少 {len(missing_fields)} 個必須的 unified fields: {missing_fields} - {field_source}")
        
        return validation_result
    
    def get_field_mapping_report(self, field_mappings: Dict[str, str]) -> Dict[str, Any]:
        """
        生成欄位映射報告
        
        Args:
            field_mappings: 欄位映射字典
            
        Returns:
            映射報告字典
        """
        mapped_fields = []
        unmapped_fields = []
        
        for unified_field in self.required_unified_fields:
            if unified_field in field_mappings:
                source_field = field_mappings[unified_field]
                mapped_fields.append({
                    'unified_field': unified_field,
                    'source_field': source_field,
                    'field_type': self.field_types.get(unified_field, 'string')
                })
            else:
                unmapped_fields.append({
                    'unified_field': unified_field,
                    'field_type': self.field_types.get(unified_field, 'string')
                })
        
        return {
            'total_required_fields': len(self.required_unified_fields),
            'mapped_fields': mapped_fields,
            'unmapped_fields': unmapped_fields,
            'mapped_count': len(mapped_fields),
            'unmapped_count': len(unmapped_fields),
            'mapping_coverage': len(mapped_fields) / len(self.required_unified_fields) * 100
        }
    
    def _process_derived_fields(self, unified_df: pd.DataFrame, original_df: pd.DataFrame) -> pd.DataFrame:
        """
        處理衍生字段（需要特殊邏輯的字段）
        
        Args:
            unified_df: 已映射的統一字段DataFrame
            original_df: 原始DataFrame
            
        Returns:
            處理後的DataFrame
        """
        try:
            # 導入貨幣轉換器 - 使用多种导入方式以确保兼容性
            currency_converter = None
            
            # 方法1: 相对导入
            try:
                from .currency_converter import currency_converter
                logger.debug("✅ 使用相对导入加载货币转换器")
            except (ImportError, ValueError) as e:
                logger.debug(f"相对导入失败: {e}")
                
                # 方法2: 绝对导入
                try:
                    from agents.data_dmp_agent.currency_converter import currency_converter
                    logger.debug("✅ 使用绝对导入加载货币转换器")
                except ImportError as e:
                    logger.debug(f"绝对导入失败: {e}")
                    
                    # 方法3: 模块导入 + 实例获取
                    try:
                        import agents.data_dmp_agent.currency_converter as currency_converter_module
                        currency_converter = currency_converter_module.currency_converter
                        logger.debug("✅ 使用模块导入+实例获取加载货币转换器")
                    except ImportError as e:
                        logger.debug(f"模块导入失败: {e}")
                        
                        # 方法4: 动态导入（最后手段）
                        try:
                            import sys
                            import os
                            
                            # 添加agents目录到sys.path
                            current_dir = os.path.dirname(os.path.abspath(__file__))
                            agents_dir = os.path.dirname(current_dir)
                            root_dir = os.path.dirname(agents_dir)
                            
                            if root_dir not in sys.path:
                                sys.path.insert(0, root_dir)
                            
                            from agents.data_dmp_agent.currency_converter import currency_converter
                            logger.debug("✅ 使用动态路径导入加载货币转换器")
                        except Exception as e:
                            logger.error(f"所有导入方法都失败: {e}")
                            currency_converter = None
            
            # 如果导入失败，创建一个简单的回退转换器
            if currency_converter is None:
                logger.warning("⚠️ 貨幣轉換器導入失敗，使用固定匯率回退方案")
                
                class FallbackConverter:
                    def convert_idr_to_usd(self, idr_amount):
                        """使用固定汇率进行IDR到USD转换"""
                        try:
                            # 使用固定汇率 1 USD = 15000 IDR
                            return float(idr_amount) / 15000.0 if idr_amount else 0.0
                        except:
                            return 0.0
                
                currency_converter = FallbackConverter()
            
            # 移除Custom Type處理邏輯
            # 1. USD Sale Amount <- Local Sale Amount 做IDR到USD轉換
            if 'USD Sale Amount' in unified_df.columns and 'Local Sale Amount' in unified_df.columns:
                logger.info("開始處理USD Sale Amount貨幣轉換")
                unified_df['USD Sale Amount'] = unified_df['Local Sale Amount'].apply(
                    lambda x: currency_converter.convert_idr_to_usd(float(x)) if pd.notna(x) and x != '' else 0.0
                )
                logger.debug("完成USD Sale Amount轉換：IDR -> USD")
            
            # 2. USD Reward <- Local Reward 做IDR到USD轉換
            if 'USD Reward' in unified_df.columns and 'Local Reward' in unified_df.columns:
                logger.info("開始處理USD Reward貨幣轉換")
                unified_df['USD Reward'] = unified_df['Local Reward'].apply(
                    lambda x: currency_converter.convert_idr_to_usd(float(x)) if pd.notna(x) and x != '' else 0.0
                )
                logger.debug("完成USD Reward轉換：IDR -> USD")
            
            return unified_df
            
        except Exception as e:
            logger.warning(f"⚠️ 貨幣轉換失敗，使用固定匯率: {e}")
            
            # 使用回退方案：固定汇率转换
            try:
                # 1. USD Sale Amount <- Local Sale Amount 做IDR到USD轉換 (固定汇率)
                if 'USD Sale Amount' in unified_df.columns and 'Local Sale Amount' in unified_df.columns:
                    logger.info("使用固定汇率处理USD Sale Amount转换 (1 USD = 15000 IDR)")
                    unified_df['USD Sale Amount'] = unified_df['Local Sale Amount'].apply(
                        lambda x: float(x) / 15000.0 if pd.notna(x) and x != '' and x != 0 else 0.0
                    )
                
                # 2. USD Reward <- Local Reward 做IDR到USD轉換 (固定汇率)
                if 'USD Reward' in unified_df.columns and 'Local Reward' in unified_df.columns:
                    logger.info("使用固定汇率处理USD Reward转换 (1 USD = 15000 IDR)")
                    unified_df['USD Reward'] = unified_df['Local Reward'].apply(
                        lambda x: float(x) / 15000.0 if pd.notna(x) and x != '' and x != 0 else 0.0
                    )
                
                logger.info("✅ 固定汇率回退转换完成")
            except Exception as fallback_error:
                logger.error(f"❌ 固定汇率回退也失败: {fallback_error}")
            
            return unified_df
    
    def apply_data_transformations(self, df: pd.DataFrame, transformations: Dict[str, Dict[str, Any]]) -> pd.DataFrame:
        """
        應用數據轉換
        
        Args:
            df: 要轉換的 DataFrame
            transformations: 轉換配置字典
            
        Returns:
            轉換後的 DataFrame
        """
        logger.info("開始應用數據轉換")
        
        for field, config in transformations.items():
            if field in df.columns:
                transform_type = config.get('type')
                
                if transform_type == 'currency':
                    df[field] = self._transform_currency(df[field], config)
                elif transform_type == 'date':
                    df[field] = self._transform_date(df[field], config)
                elif transform_type == 'percentage':
                    df[field] = self._transform_percentage(df[field], config)
                
                logger.debug(f"應用轉換: {field} -> {transform_type}")
        
        return df
    
    def _transform_currency(self, series: pd.Series, config: Dict[str, Any]) -> pd.Series:
        """轉換貨幣欄位"""
        try:
            # 移除貨幣符號和逗號
            series = series.astype(str).str.replace(r'[$,¥€£]', '', regex=True)
            series = series.str.replace(',', '', regex=False)
            
            # 轉換為數值
            series = pd.to_numeric(series, errors='coerce')
            
            # 填充 NaN 值
            series = series.fillna(0.0)
            
            return series
        except Exception as e:
            logger.warning(f"貨幣轉換失敗: {e}")
            return series
    
    def _transform_date(self, series: pd.Series, config: Dict[str, Any]) -> pd.Series:
        """轉換日期欄位"""
        try:
            date_format = config.get('format', '%Y-%m-%d %H:%M:%S')  # 支持帶時間的格式
            
            # 嘗試不同的日期格式
            try:
                # 首先嘗試配置的格式
                series = pd.to_datetime(series, format=date_format, errors='coerce')
            except:
                # 如果失敗，使用pandas的智能解析
                series = pd.to_datetime(series, errors='coerce')
            
            return series
        except Exception as e:
            logger.warning(f"日期轉換失敗: {e}")
            return series
    
    def _transform_percentage(self, series: pd.Series, config: Dict[str, Any]) -> pd.Series:
        """轉換百分比欄位"""
        try:
            # 移除百分號
            series = series.astype(str).str.replace('%', '', regex=False)
            
            # 轉換為數值
            series = pd.to_numeric(series, errors='coerce')
            
            # 轉換為小數
            series = series / 100
            
            return series
        except Exception as e:
            logger.warning(f"百分比轉換失敗: {e}")
            return series 