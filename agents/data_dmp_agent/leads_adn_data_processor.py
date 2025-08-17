#!/usr/bin/env python3
"""
LeadsADN数据处理器
处理LeadsADN平台的数据，支持从affiliate字段提取Partner信息
"""

import os
import sys
import re
import logging
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# 导入共享模块
from .unified_field_mapper import UnifiedFieldMapper
# LeadsADN数据已经是USD，不需要货币转换
# from .currency_converter import currency_converter

logger = logging.getLogger(__name__)

class LeadsADNDataProcessor:
    """LeadsADN数据处理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.unified_mapper = UnifiedFieldMapper()
        
        # LeadsADN字段映射配置（只包含Google Sheets中定义的统一字段）
        self.field_mappings = {
            # 核心统一字段 - 根据Google Sheets映射
            'Conversion ID': 'TID',                     # 交易ID
            'Advertiser': 'Offer',                     # 广告主（从Offer字段获取）
            'Datetime Conversion': 'Conv. Time',        # 转换时间
            'USD Sale Amount': 'Event Value',          # 销售金额
            'USD Reward': 'Revenue',                   # 奖励/佣金
            'Status': 'Conv. Status',                  # 转换状态
            'Publisher Sub ID 1': 'Affiliate',         # 联盟会员ID
            'Publisher Sub ID 2': 'S1',               # 发布者子ID 2
            'Publisher Sub ID 3': 'S2',               # 发布者子ID 3
            'Publisher Sub ID 4': 'S3',               # 发布者子ID 4
            'Publisher Sub ID 5': 'S4',               # 发布者子ID 5
            'Advertiser Sub ID 1': 'Adv. S1',         # 广告主子ID 1
            'Advertiser Sub ID 2': 'Adv. S2',         # 广告主子ID 2
            'Advertiser Sub ID 3': 'Adv. S3',         # 广告主子ID 3
            'Advertiser Sub ID 4': 'Adv. S4',         # 广告主子ID 4
            'Advertiser Sub ID 5': 'Adv. S5',         # 广告主子ID 5
            'Category ID': 'Brand',                   # 分类ID
            'Product ID': 'Event Token',              # 产品ID
            'Customer Type': 'Geo.',                  # 客户类型
            'Campaign': 'Offer',                      # 活动
            'Product Name': 'Adv. Offer',            # 产品名称
            'Order ID': 'TID',                       # 订单ID
            'Click ID': 'Aff. Click ID',             # 点击ID
            'IP Address': 'IP',                      # IP地址
            'User Agent': 'UA',                      # 用户代理
            'Traffic Source': 'Traffic Tag',         # 流量来源
            'Conversion IP': 'Conv. IP',             # 转换IP
            'Event Value': 'Event Value',            # 事件价值
            'Partner': 'extracted_from_affiliate'    # Partner（从Affiliate字段提取）
        }
        
        # 数据转换配置（LeadsADN数据已经是USD，只需要数据类型转换）
        self.data_transformations = {
            'USD Sale Amount': {'type': 'numeric'},                        # Event Value字段，已经是USD
            'USD Reward': {'type': 'numeric'},                             # Revenue字段，已经是USD
            'Datetime Conversion': {'type': 'date', 'format': '%Y-%m-%d %H:%M:%S %z'},  # 支持时区
            'Event Value': {'type': 'numeric'},                            # 事件价值，已经是USD
            # 特殊处理：大整数字段避免科学计数法
            'Publisher Sub ID 2': {'type': 'string'},                      # S1字段，保持字符串格式
            'Publisher Sub ID 3': {'type': 'string'},                      # S2字段，保持字符串格式
            'Publisher Sub ID 4': {'type': 'string'},                      # S3字段，保持字符串格式
            'Publisher Sub ID 5': {'type': 'string'},                      # S4字段，保持字符串格式
            'Advertiser Sub ID 1': {'type': 'string'},                     # Adv. S1字段，保持字符串格式
            'Advertiser Sub ID 2': {'type': 'string'},                     # Adv. S2字段，保持字符串格式
            'Advertiser Sub ID 3': {'type': 'string'},                     # Adv. S3字段，保持字符串格式
            'Advertiser Sub ID 4': {'type': 'string'},                     # Adv. S4字段，保持字符串格式
            'Advertiser Sub ID 5': {'type': 'string'}                      # Adv. S5字段，保持字符串格式
        }
    
    def process_data(self, df: pd.DataFrame, file_path: str = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        处理LeadsADN数据的主要方法
        
        Args:
            df: 原始DataFrame
            file_path: 原始文件路径
            
        Returns:
            Tuple[pd.DataFrame, Dict]: 处理后的DataFrame和处理信息
        """
        try:
            self.logger.info(f"🚀 开始处理LeadsADN数据，原始记录数: {len(df)}")
            
            # 1. 数据清理和预处理
            cleaned_df = self._preprocess_data(df)
            self.logger.info(f"✅ 数据预处理完成，记录数: {len(cleaned_df)}")
            
            # 2. 应用字段映射
            mapped_df, mapping_info = self.apply_field_mapping(cleaned_df)
            self.logger.info(f"✅ 字段映射完成，统一字段数: {len(mapped_df.columns)}")
            
            # 3. 提取Partner信息
            mapped_df = self._extract_partner_info(mapped_df)
            self.logger.info("✅ Partner信息提取完成")
            
            # 4. 生成Source字段（从S1-S5拼接）
            mapped_df = self._generate_source_field(mapped_df)
            self.logger.info("✅ Source字段生成完成")
            
            # 5. 添加平台信息和元数据
            mapped_df = self._add_metadata(mapped_df, file_path)
            self.logger.info("✅ 元数据添加完成")
            
            # 6. 最终验证
            validation_result = self._validate_output(mapped_df)
            
            processing_info = {
                'platform': 'leads_adn',
                'original_records': len(df),
                'processed_records': len(mapped_df),
                'field_mappings_applied': len(self.field_mappings),
                'validation': validation_result,
                'mapping_info': mapping_info
            }
            
            self.logger.info(f"🎯 LeadsADN数据处理完成: {len(mapped_df)} 条记录")
            return mapped_df, processing_info
            
        except Exception as e:
            self.logger.error(f"❌ LeadsADN数据处理失败: {e}")
            raise
    
    def _preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """数据预处理"""
        try:
            cleaned_df = df.copy()
            
            # 1. 移除完全空白的行
            cleaned_df = cleaned_df.dropna(how='all')
            
            # 2. 标准化列名（去除前后空格）
            cleaned_df.columns = cleaned_df.columns.str.strip()
            
            # 3. 处理日期格式
            date_columns = ['Conv. Time']  # 使用实际的LeadsADN字段名
            for col in date_columns:
                if col in cleaned_df.columns:
                    # 转换日期并移除时区信息以支持Excel写入
                    cleaned_df[col] = pd.to_datetime(cleaned_df[col], errors='coerce')
                    if cleaned_df[col].dt.tz is not None:
                        cleaned_df[col] = cleaned_df[col].dt.tz_localize(None)
            
            # 4. 处理数值类型
            numeric_columns = ['Revenue', 'Cost', 'Event Value']  # 使用实际的LeadsADN字段名
            for col in numeric_columns:
                if col in cleaned_df.columns:
                    cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors='coerce').fillna(0)
                    
            # 5. 特殊处理大整数字段（避免科学计数法）
            large_int_columns = ['S1', 'S2', 'S3', 'S4', 'Adv. S1', 'Adv. S2', 'Adv. S3', 'Adv. S4', 'Adv. S5']
            for col in large_int_columns:
                if col in cleaned_df.columns:
                    # 将大整数转换为字符串格式，避免科学计数法
                    cleaned_df[col] = cleaned_df[col].astype(str)
                    self.logger.debug(f"🔢 大整数字段 {col} 已转换为字符串格式")
                    
            # 验证Event Value字段（现在映射为Sale Amount）
            if 'Event Value' in cleaned_df.columns:
                self.logger.info(f"💰 Event Value字段总和: {cleaned_df['Event Value'].sum():.2f}")
            
            # 6. 处理字符串类型（去除前后空格）
            string_columns = cleaned_df.select_dtypes(include=['object']).columns
            for col in string_columns:
                if col not in date_columns:  # 跳过日期列
                    cleaned_df[col] = cleaned_df[col].astype(str).str.strip()
                    cleaned_df[col] = cleaned_df[col].replace('nan', '')
            
            self.logger.info(f"✅ 数据预处理完成: {len(cleaned_df)} 条记录")
            return cleaned_df
            
        except Exception as e:
            self.logger.error(f"❌ 数据预处理失败: {e}")
            return df
    
    def apply_field_mapping(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        应用字段映射，将原始字段映射到统一字段
        
        Args:
            df: 输入DataFrame
            
        Returns:
            Tuple[pd.DataFrame, Dict]: 映射后的DataFrame和映射信息
        """
        self.logger.info("开始应用LeadsADN字段映射...")
        
        try:
            self.logger.info(f"开始映射 {len(df)} 条记录的字段...")
            
            # 使用统一字段映射器进行映射
            unified_df = self.unified_mapper.map_dataframe_to_unified_fields(df, self.field_mappings)
            
            # 应用数据转换
            unified_df = self.unified_mapper.apply_data_transformations(unified_df, self.data_transformations)
            
            mapping_info = {
                'platform': 'leads_adn',
                'field_mappings': self.field_mappings,
                'data_transformations': self.data_transformations,
                'mapped_fields_count': len([k for k, v in self.field_mappings.items() if v in df.columns]),
                'total_unified_fields': len(unified_df.columns)
            }
            
            self.logger.info(f"✅ LeadsADN字段映射完成: {len(unified_df.columns)} 个统一字段")
            return unified_df, mapping_info
            
        except Exception as e:
            self.logger.error(f"❌ LeadsADN字段映射失败: {e}")
            # 返回空的统一格式DataFrame
            empty_df = self.unified_mapper.map_dataframe_to_unified_fields(pd.DataFrame(), {})
            return empty_df, {'error': str(e)}
    
    def _extract_partner_info(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        从affiliate字段提取Partner信息
        支持格式如: "(3)FTK", "(1)ByteC", "FTK", "ByteC" 等
        """
        try:
            if 'Publisher Sub ID 1' not in df.columns:
                self.logger.warning("⚠️ 未找到Publisher Sub ID 1字段，无法提取Partner信息")
                df['Partner'] = 'Unknown'
                return df
            
            def extract_partner(affiliate_value):
                """从affiliate值中提取Partner"""
                if pd.isna(affiliate_value) or affiliate_value == '':
                    return 'Unknown'
                
                affiliate_str = str(affiliate_value).strip()
                
                # 模式1: "(数字)Partner" 格式，如 "(3)FTK", "(1)ByteC"
                pattern1 = re.search(r'\(\d+\)([A-Za-z0-9_-]+)', affiliate_str)
                if pattern1:
                    partner = pattern1.group(1).strip()
                    self.logger.debug(f"从 '{affiliate_str}' 提取Partner: '{partner}' (模式1)")
                    return partner
                
                # 模式2: "Partner(数字)" 格式，如 "FTK(3)", "ByteC(1)"
                pattern2 = re.search(r'([A-Za-z0-9_-]+)\(\d+\)', affiliate_str)
                if pattern2:
                    partner = pattern2.group(1).strip()
                    self.logger.debug(f"从 '{affiliate_str}' 提取Partner: '{partner}' (模式2)")
                    return partner
                
                # 模式3: 纯Partner名称，如 "FTK", "ByteC"
                pattern3 = re.search(r'^([A-Za-z0-9_-]+)$', affiliate_str)
                if pattern3:
                    partner = pattern3.group(1).strip()
                    self.logger.debug(f"从 '{affiliate_str}' 提取Partner: '{partner}' (模式3)")
                    return partner
                
                # 模式4: 包含Partner关键词的复杂格式
                # 检查是否包含已知的Partner名称
                known_partners = ['FTK', 'ByteC', 'DeepLeaper', 'TikTok', 'MP']
                for partner in known_partners:
                    if partner.lower() in affiliate_str.lower():
                        self.logger.debug(f"从 '{affiliate_str}' 找到已知Partner: '{partner}' (模式4)")
                        return partner
                
                # 如果都没匹配到，返回原值（可能是新的Partner）
                self.logger.debug(f"无法解析Partner格式 '{affiliate_str}'，使用原值")
                return affiliate_str[:20]  # 限制长度，避免过长的值
            
            # 应用Partner提取
            df['Partner'] = df['Publisher Sub ID 1'].apply(extract_partner)
            
            # 统计Partner分布
            partner_counts = df['Partner'].value_counts()
            self.logger.info("📊 Partner分布统计:")
            for partner, count in partner_counts.items():
                self.logger.info(f"   - {partner}: {count} 条记录")
            
            return df
            
        except Exception as e:
            self.logger.error(f"❌ Partner信息提取失败: {e}")
            df['Partner'] = 'Unknown'
            return df
    
    def _generate_source_field(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        从映射后的Publisher Sub ID 1-5字段生成Source字段
        例如: Publisher Sub ID 1=(3)FTK, Publisher Sub ID 2=FTK 
        生成: Source=(3)FTK_FTK
        包含Publisher Sub ID 1（来自Affiliate字段）和其他Sub ID字段
        """
        try:
            def create_source(row):
                # 获取Publisher Sub ID 1-5字段的值（包含Affiliate和S1-S4）
                source_parts = []
                for i in range(1, 6):  # Publisher Sub ID 1-5
                    col_name = f'Publisher Sub ID {i}'
                    if col_name in df.columns:
                        value = str(row.get(col_name, '')).strip()
                        if value and value != 'nan' and value != 'None' and value != '':
                            source_parts.append(value)
                
                # 用下划线拼接非空值
                if source_parts:
                    source = '_'.join(source_parts)
                    return source
                else:
                    return 'Unknown'
            
            # 生成Source字段
            df['Source'] = df.apply(create_source, axis=1)
            
            # 记录Source分布
            source_dist = df['Source'].value_counts().to_dict()
            self.logger.info(f"📊 Source字段分布: {source_dist}")
            
            return df
            
        except Exception as e:
            self.logger.error(f"❌ 生成Source字段失败: {e}")
            df['Source'] = 'Unknown'
            return df
    
    def _add_metadata(self, df: pd.DataFrame, file_path: str = None) -> pd.DataFrame:
        """添加平台信息和元数据"""
        try:
            # 添加平台标识
            df['Platform'] = 'LeadsADN'
            
            # 添加源文件信息
            if file_path:
                df['Source File'] = os.path.basename(file_path)
            else:
                df['Source File'] = 'LeadsADN_Data'
            
            # 添加处理时间戳（不带时区）
            df['Processed Date'] = datetime.now().replace(tzinfo=None)
            
            # USD字段已经通过字段映射直接创建，无需额外处理
            # 验证USD字段存在
            if 'USD Sale Amount' not in df.columns:
                self.logger.warning("⚠️ USD Sale Amount字段缺失，设置为0")
                df['USD Sale Amount'] = 0.0
            
            if 'USD Reward' not in df.columns:
                self.logger.warning("⚠️ USD Reward字段缺失，设置为0")
                df['USD Reward'] = 0.0
            
            return df
            
        except Exception as e:
            self.logger.error(f"❌ 添加元数据失败: {e}")
            return df
    
    def _validate_output(self, df: pd.DataFrame) -> Dict[str, Any]:
        """验证输出数据的完整性"""
        try:
            # 检查必要的reporter_agent字段
            required_fields = [
                'USD Sale Amount', 'Advertiser', 'Conversion ID', 
                'Status', 'Partner', 'Datetime Conversion'
            ]
            
            missing_fields = []
            present_fields = []
            
            for field in required_fields:
                if field in df.columns:
                    present_fields.append(field)
                else:
                    missing_fields.append(field)
            
            # 检查数据质量
            total_records = len(df)
            non_null_conversions = df[df['Conversion ID'].notna()].shape[0] if 'Conversion ID' in df.columns else 0
            valid_amounts = df[df['USD Sale Amount'] > 0].shape[0] if 'USD Sale Amount' in df.columns else 0
            
            validation_result = {
                'total_records': total_records,
                'required_fields_present': len(present_fields),
                'required_fields_missing': len(missing_fields),
                'missing_fields': missing_fields,
                'non_null_conversions': non_null_conversions,
                'valid_amounts': valid_amounts,
                'data_quality_score': (non_null_conversions / total_records * 100) if total_records > 0 else 0
            }
            
            if missing_fields:
                self.logger.warning(f"⚠️ 缺少必要字段: {missing_fields}")
            else:
                self.logger.info("✅ 所有必要字段都存在")
            
            self.logger.info(f"📊 数据质量评分: {validation_result['data_quality_score']:.1f}%")
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f"❌ 输出验证失败: {e}")
            return {'error': str(e)}
    
    def get_platform_info(self) -> Dict[str, Any]:
        """获取平台信息"""
        return {
            'platform': 'leads_adn',
            'display_name': 'LeadsADN',
            'field_mappings': self.field_mappings,
            'data_transformations': self.data_transformations,
            'supported_formats': ['csv', 'xlsx'],
            'partner_extraction': 'affiliate_field',
            'currency_support': ['USD'],
            'description': 'LeadsADN联盟营销平台数据处理器'
        }
