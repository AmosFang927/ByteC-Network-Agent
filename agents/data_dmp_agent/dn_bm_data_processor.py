#!/usr/bin/env python3
"""
DN_BM Data Processor - DN_BM数据处理器
处理 DN_BM 平台的数据转换和字段映射
"""

import os
import re
import logging
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
from datetime import datetime

from .field_mapping_manager import FieldMappingManager
from .unified_field_mapper import UnifiedFieldMapper

logger = logging.getLogger(__name__)

class DNBMDataProcessor:
    """DN_BM数据处理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.field_mapping_manager = FieldMappingManager()
        self.unified_mapper = UnifiedFieldMapper()
        self.stats = {
            'total_records': 0,
            'processed_records': 0,
            'mapped_fields': 0,
            'errors': []
        }
    
    def is_dn_bm_file(self, filename: str) -> bool:
        """检查是否为DN_BM文件"""
        filename_lower = filename.lower()
        return 'dn_bm' in filename_lower
    
    def detect_platform_column(self, df: pd.DataFrame) -> Optional[str]:
        """
        检测platform列，处理可能的列名变化
        
        Args:
            df: 输入DataFrame
            
        Returns:
            str: platform列名，如果未找到返回None
        """
        possible_platform_columns = [
            'platform', 'Platform', 'PLATFORM',
            '平台', '平台名称', '平台名稱'
        ]
        
        for col in possible_platform_columns:
            if col in df.columns:
                self.logger.info(f"检测到platform列: {col}")
                return col
        
        self.logger.warning("未找到platform列，将尝试从文件名推断")
        return None
    
    def handle_merged_cells(self, df: pd.DataFrame, platform_col: str) -> pd.DataFrame:
        """
        处理合并单元格情况，确保所有行都有platform值
        
        Args:
            df: 输入DataFrame
            platform_col: platform列名
            
        Returns:
            pd.DataFrame: 处理后的DataFrame
        """
        if platform_col not in df.columns:
            return df
        
        self.logger.info(f"处理{platform_col}列的合并单元格...")
        
        # 使用前向填充处理合并单元格
        df[platform_col] = df[platform_col].ffill()
        
        # 如果还有空值，尝试用'DN_BM'填充
        dn_bm_mask = df[platform_col].isna()
        if dn_bm_mask.any():
            df.loc[dn_bm_mask, platform_col] = 'DN_BM'
            self.logger.info(f"为{dn_bm_mask.sum()}行填充了默认platform值: DN_BM")
        
        return df
    
    def filter_dn_bm_records(self, df: pd.DataFrame, platform_col: Optional[str] = None) -> pd.DataFrame:
        """
        过滤DN_BM记录
        
        Args:
            df: 输入DataFrame
            platform_col: platform列名
            
        Returns:
            pd.DataFrame: 过滤后的DataFrame
        """
        if platform_col and platform_col in df.columns:
            # 过滤DN_BM记录
            dn_bm_mask = df[platform_col].str.contains('DN_BM', case=False, na=False)
            filtered_df = df[dn_bm_mask].copy()
            self.logger.info(f"从{len(df)}条记录中过滤出{len(filtered_df)}条DN_BM记录")
            return filtered_df
        else:
            self.logger.warning("未找到platform列，返回原始数据")
            return df.copy()
    
    def apply_field_mapping(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        应用字段映射，将原始字段映射到统一字段
        
        Args:
            df: 输入DataFrame
            
        Returns:
            Tuple[pd.DataFrame, Dict]: 映射后的DataFrame和映射信息
        """
        self.logger.info("开始应用DN_BM字段映射...")
        
        # 使用现有的字段映射管理器
        try:
            mapped_df, mapping_info = self.field_mapping_manager.map_dataframe_columns(
                df, 'dn_bm'  # DN_BM映射到dn_bm平台
            )
            
            self.logger.info(f"字段映射完成，映射了{len(mapping_info.get('mapped_fields', []))}个字段")
            return mapped_df, mapping_info
            
        except Exception as e:
            self.logger.error(f"字段映射失败: {e}")
            # 如果映射失败，返回包含所有unified fields的空DataFrame
            empty_mapped_df = self.unified_mapper.map_dataframe_to_unified_fields(
                pd.DataFrame(), {}
            )
            return empty_mapped_df, {"error": str(e)}
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        清理数据
        
        Args:
            df: 输入DataFrame
            
        Returns:
            pd.DataFrame: 清理后的DataFrame
        """
        self.logger.info("开始清理DN_BM数据...")
        
        # 复制数据避免修改原始数据
        cleaned_df = df.copy()
        
        # 处理日期时间字段
        datetime_columns = ['Conversion Time', 'Click Time', 'Confirmation Time']
        for col in datetime_columns:
            if col in cleaned_df.columns:
                cleaned_df[col] = pd.to_datetime(cleaned_df[col], errors='coerce')
        
        # 处理数值字段
        numeric_columns = ['Total Price', 'Reward']
        for col in numeric_columns:
            if col in cleaned_df.columns:
                cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors='coerce')
        
        # 处理字符串字段
        string_columns = ['Site', 'Campaign Name', 'Product ID', 'Status', 'aff_sub']
        for col in string_columns:
            if col in cleaned_df.columns:
                cleaned_df[col] = cleaned_df[col].astype(str)
        
        self.logger.info("DN_BM数据清理完成")
        return cleaned_df
    
    def _add_partner_and_source_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        添加Reporter Agent需要的Partner和Source列
        
        Args:
            df: 输入DataFrame
            
        Returns:
            pd.DataFrame: 添加Partner和Source列后的DataFrame
        """
        self.logger.info("添加Partner和Source列...")
        
        # 复制数据避免修改原始数据
        result_df = df.copy()
        
        # 基于Publisher Sub ID 1 (aff_sub)确定Partner
        if 'Publisher Sub ID 1' in result_df.columns:
            aff_sub_values = result_df['Publisher Sub ID 1'].fillna('').astype(str)
            
            # 使用与config.py中相同的DeepLeaper匹配逻辑
            deepleaper_pattern = r'^DL.*|.*(OPPO|VIVO|OEM1|OEM2|OEM3|XIAOMI).*'
            
            # 创建Partner列
            result_df['Partner'] = 'UNKNOWN'
            deepleaper_mask = aff_sub_values.str.match(deepleaper_pattern, case=False, na=False)
            result_df.loc[deepleaper_mask, 'Partner'] = 'DEEPLEAPER'
            
            # 创建Source列（与aff_sub相同）
            result_df['Source'] = aff_sub_values
            result_df.loc[result_df['Source'] == '', 'Source'] = 'UNKNOWN'
            
            partner_counts = result_df['Partner'].value_counts()
            self.logger.info(f"Partner分布: {dict(partner_counts)}")
            
        else:
            self.logger.warning("未找到Publisher Sub ID 1列，设置默认Partner和Source")
            result_df['Partner'] = 'UNKNOWN'
            result_df['Source'] = 'UNKNOWN'
        
        self.logger.info("Partner和Source列添加完成")
        return result_df
    
    def process_dn_bm_file(self, file_path: str, output_dir: str = "output") -> Dict[str, Any]:
        """
        处理单个DN_BM文件的完整流程
        
        Args:
            file_path: 输入文件路径
            output_dir: 输出目录
            
        Returns:
            Dict: 处理结果
        """
        from pathlib import Path
        
        file_path = Path(file_path)
        
        self.logger.info(f"🚀 开始处理DN_BM文件: {file_path.name}")
        
        try:
            # 重置统计信息
            self.stats = {
                'total_records': 0,
                'processed_records': 0,
                'mapped_fields': 0,
                'errors': []
            }
            
            # 1. 检查文件是否为DN_BM文件
            if not self.is_dn_bm_file(file_path.name):
                raise ValueError(f"文件{file_path.name}不是DN_BM文件")
            
            # 2. 读取文件
            self.logger.info("📖 读取文件...")
            df = self._read_dn_bm_csv_correctly(file_path)
            
            self.stats['total_records'] = len(df)
            self.logger.info(f"成功读取{len(df)}条记录，{len(df.columns)}个字段")
            
            # 3. 检测和处理platform列
            platform_col = self.detect_platform_column(df)
            if platform_col:
                df = self.handle_merged_cells(df, platform_col)
                df = self.filter_dn_bm_records(df, platform_col)
            
            # 4. 应用字段映射
            self.logger.info("🔗 应用字段映射...")
            mapped_df, mapping_info = self.apply_field_mapping(df)
            
            # 5. 数据清理
            cleaned_df = self.clean_data(mapped_df)
            self.stats['processed_records'] = len(cleaned_df)
            
            # 5.5. 添加Reporter Agent需要的Partner和Source列
            cleaned_df = self._add_partner_and_source_columns(cleaned_df)
            
            # 6. 生成输出文件
            output_path = Path(output_dir) / f"dn_bm_processed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            cleaned_df.to_csv(output_path, index=False, encoding='utf-8')
            
            result = {
                'success': True,
                'input_file': str(file_path),
                'output_file': str(output_path),
                'stats': self.stats,
                'mapping_info': mapping_info,
                'records_processed': len(cleaned_df),
                'unified_fields_count': len(cleaned_df.columns)
            }
            
            self.logger.info(f"✅ DN_BM文件处理完成！")
            self.logger.info(f"   输入记录: {self.stats['total_records']}")
            self.logger.info(f"   处理记录: {self.stats['processed_records']}")
            self.logger.info(f"   输出文件: {output_path}")
            
            return result
            
        except Exception as e:
            error_msg = f"处理DN_BM文件失败: {e}"
            self.logger.error(error_msg)
            self.stats['errors'].append(error_msg)
            
            return {
                'success': False,
                'input_file': str(file_path),
                'error': error_msg,
                'stats': self.stats
            }
    
    def _read_dn_bm_csv_correctly(self, file_path):
        """
        正确读取DN_BM CSV文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            pd.DataFrame: 读取的DataFrame
        """
        try:
            # 尝试不同的编码方式
            encodings = ['utf-8', 'utf-8-sig', 'gbk', 'gb2312', 'latin1']
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    self.logger.info(f"成功使用 {encoding} 编码读取DN_BM CSV文件")
                    return df
                except UnicodeDecodeError:
                    continue
            
            # 如果所有编码都失败，使用默认编码
            df = pd.read_csv(file_path, encoding='utf-8', errors='ignore')
            self.logger.warning("使用默认编码读取文件，可能存在编码问题")
            return df
            
        except Exception as e:
            self.logger.error(f"读取DN_BM CSV文件失败: {e}")
            raise
