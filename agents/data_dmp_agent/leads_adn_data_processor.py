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
# 导入货币转换器，用于动态货币转换
from .currency_converter import currency_converter

logger = logging.getLogger(__name__)

class LeadsADNDataProcessor:
    """LeadsADN数据处理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.unified_mapper = UnifiedFieldMapper()
        
        # LeadsADN字段映射配置（只包含Google Sheets中定义的统一字段）
        self.field_mappings = {
            # 核心统一字段 - 根据Google Sheets映射
            'Conversion ID': 'Order ID',               # 转换ID（修复：使用Order ID字段，因为Action ID为空）
            'Advertiser': 'Advertiser',                # 广告主（直接映射到Advertiser字段，用于识别TTS_LinkShare等特殊广告主）
            'Datetime Conversion': 'Event Time',        # 转换时间
            'Event Value': 'Event Value',              # 原始事件金额（可能是IDR或USD）
            'USD Sale Amount': 'E.Value Release',      # 销售金额（优先使用E.Value Release字段，支持Rpxxxx格式自动转换）
            'USD Payout': 'Cost',                      # 成本/支出金额（Cost字段，支持Rpxxxx格式自动转换）
            'USD Reward': 'Revenue',                   # 奖励/佣金
            'Status': 'Conv. Status',                  # 转换状态
            'Publisher Sub ID 1': 'S1',               # 发布者子ID 1
            'Publisher Sub ID 2': 'S2',               # 发布者子ID 2
            'Publisher Sub ID 3': 'S3',               # 发布者子ID 3
            'Publisher Sub ID 4': 'S4',               # 发布者子ID 4
            'Publisher Sub ID 5': 'S5',               # 发布者子ID 5
            'Partner': 'Affiliate',                   # Partner字段从Affiliate映射（根据Google Sheets标准）
            'Advertiser Sub ID 1': 'Adv. S1',         # 广告主子ID 1
            'Advertiser Sub ID 2': 'Adv. S2',         # 广告主子ID 2
            'Advertiser Sub ID 3': 'Adv. S3',         # 广告主子ID 3
            'Advertiser Sub ID 4': 'Adv. S4',         # 广告主子ID 4
            'Advertiser Sub ID 5': 'Adv. S5',         # 广告主子ID 5
            'Category ID': 'Brand',                   # 分类ID
            'Product ID': 'Event Token',              # 产品ID
            'Customer Type': 'Geo.',                  # 客户类型
            'Campaign': 'Offer',                      # 活动（从Offer字段获取）
            'Product Name': 'Adv. Offer',            # 产品名称
            'Order ID': 'TID',                       # 订单ID
            'Click ID': 'Aff. Click ID',             # 点击ID
            'IP Address': 'IP',                      # IP地址
            'User Agent': 'UA',                     # 用户代理
            'Traffic Source': 'Traffic Tag',        # 流量来源
            'Conversion IP': 'Conv. IP',            # 转换IP
            'Original Event Value': 'Event Value'   # 保留原始Event Value作为参考
        }
        
        # 数据转换配置（动态货币转换：支持自动检测Rpxxxx格式并转换为USD）
        self.data_transformations = {
            'USD Sale Amount': {'type': 'currency_auto'},                  # 智能货币转换（支持Rpxxxx格式检测）
            'USD Payout': {'type': 'currency_auto'},                       # 智能货币转换（支持Rpxxxx格式检测）
            'USD Reward': {'type': 'numeric'},                             # Revenue字段，已经是USD
            'Datetime Conversion': {'type': 'date', 'format': '%Y-%m-%d %H:%M:%S %z', 'remove_timezone': True},  # 支持时区但移除时区信息
            'Event Value': {'type': 'numeric'},                            # 原始事件价值（IDR或USD）
            'Original Event Value': {'type': 'numeric'},                   # 备份的原始金额
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
            
            # 2. 数据预处理完成（新的智能货币转换将在字段映射阶段自动处理）
            self.logger.info("✅ 数据预处理完成，智能货币转换将在字段映射阶段处理")
            
            # 3. 预处理：应用基于Advertiser的特定货币转换（在字段映射前处理原始数据）
            cleaned_df = self._apply_advertiser_specific_currency_conversion_before_mapping(cleaned_df)
            self.logger.info("✅ 预处理特定货币转换完成")
            
            # 4. 应用字段映射
            self.logger.info(f"🔍 映射前Affiliate字段检查: {'Affiliate' in cleaned_df.columns}, 前5个值: {cleaned_df['Affiliate'].head().tolist() if 'Affiliate' in cleaned_df.columns else 'N/A'}")
            mapped_df, mapping_info = self.apply_field_mapping(cleaned_df)
            self.logger.info(f"✅ 字段映射完成，统一字段数: {len(mapped_df.columns)}")
            
            # 5. 处理Partner字段映射（从Affiliate字段获得，然后应用Partner映射）
            mapped_df = self._apply_partner_mapping(mapped_df)
            self.logger.info(f"🔍 Partner映射后检查: {'Partner' in mapped_df.columns}, 非空值: {mapped_df['Partner'].notna().sum() if 'Partner' in mapped_df.columns else 0}")
            self.logger.info("✅ Partner映射完成")
            
            # 6. 验证特定货币转换（验证预处理阶段的转换结果）
            mapped_df = self._apply_advertiser_specific_currency_conversion(mapped_df)
            self.logger.info("✅ 特定货币转换验证完成")
            
            # 7. 生成Source字段（从S1-S5拼接）
            mapped_df = self._generate_source_field(mapped_df)
            self.logger.info("✅ Source字段生成完成")
            
            # 6. 验证智能货币转换结果
            self._validate_currency_conversion(mapped_df)
            self.logger.info("✅ 智能货币转换验证完成")
            
            # 6. 添加平台信息和元数据
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
            
            self.logger.info(f"🔍 最终返回前Partner字段检查: {'Partner' in mapped_df.columns}, 非空值: {mapped_df['Partner'].notna().sum() if 'Partner' in mapped_df.columns else 0}")
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
    
    def _pre_field_mapping_currency_conversion(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        在字段映射之前进行货币转换
        处理E.Value Release字段中的印尼盾数值，转换为美元
        如果没有E.Value Release字段，则处理Event Value字段
        """
        try:
            # 检查是否有Advertiser字段
            if 'Advertiser' not in df.columns:
                self.logger.warning("⚠️ 没有Advertiser字段，跳过货币转换")
                return df
            
            # 确定要处理的字段
            value_field = None
            if 'E.Value Release' in df.columns:
                value_field = 'E.Value Release'
                self.logger.info("✅ 找到E.Value Release字段，将进行货币转换")
            elif 'Event Value' in df.columns:
                value_field = 'Event Value'
                self.logger.info("✅ 找到Event Value字段，将进行货币转换")
            else:
                self.logger.warning("⚠️ 没有找到E.Value Release或Event Value字段，跳过货币转换")
                return df
            
            # 备份原始值
            df[f'Original {value_field}'] = df[value_field].copy()
            
            # 统计需要转换的记录
            dn_bm_mask = df['Advertiser'].str.contains(r'\(2\)DN_BM', na=False)
            dn_bm_count = dn_bm_mask.sum()
            total_count = len(df)
            
            self.logger.info(f"📊 字段映射前货币转换统计:")
            self.logger.info(f"   - 总记录数: {total_count}")
            self.logger.info(f"   - (2)DN_BM记录数: {dn_bm_count}")
            self.logger.info(f"   - 需要IDR->USD转换: {dn_bm_count}")
            self.logger.info(f"   - 处理字段: {value_field}")
            
            if dn_bm_count > 0:
                # 对(2)DN_BM的记录进行IDR到USD转换
                def convert_idr_to_usd_if_needed(row):
                    """根据Advertiser字段决定是否进行货币转换"""
                    advertiser = str(row.get('Advertiser', ''))
                    value = row.get(value_field, 0)
                    
                    if '(2)DN_BM' in advertiser:
                        # IDR转换为USD
                        try:
                            usd_amount = currency_converter.convert_idr_to_usd(float(value))
                            self.logger.debug(f"IDR转换: {value} IDR -> {usd_amount} USD")
                            return usd_amount
                        except Exception as e:
                            self.logger.warning(f"货币转换失败: {e}, 使用原值")
                            return value
                    else:
                        # 其他advertiser，假设已经是USD
                        return value
                
                # 应用转换并更新字段
                df[value_field] = df.apply(convert_idr_to_usd_if_needed, axis=1)
                
                # 统计转换结果
                original_total = df.loc[dn_bm_mask, f'Original {value_field}'].sum()
                converted_total = df.loc[dn_bm_mask, value_field].sum()
                
                self.logger.info(f"💰 (2)DN_BM货币转换结果:")
                self.logger.info(f"   - 原始总金额: {original_total:,.2f} IDR")
                self.logger.info(f"   - 转换后总金额: {converted_total:,.6f} USD")
                self.logger.info(f"   - 汇率影响: {converted_total/original_total if original_total > 0 else 0:.8f}")
                
                # 为其他记录（非(2)DN_BM）保持原值
                non_dn_bm_mask = ~dn_bm_mask
                if non_dn_bm_mask.sum() > 0:
                    other_total = df.loc[non_dn_bm_mask, value_field].sum()
                    self.logger.info(f"💰 其他Advertiser金额:")
                    self.logger.info(f"   - 总金额: {other_total:,.6f} USD (保持原值)")
            else:
                self.logger.info(f"✅ 没有(2)DN_BM记录，保持{value_field}原值")
            
            # 计算最终总计
            final_total = df[value_field].sum()
            self.logger.info(f"📊 最终{value_field}总计: {final_total:,.6f} USD")
            
            return df
            
        except Exception as e:
            self.logger.error(f"字段映射前货币转换失败: {e}")
            return df
    
    def _adjust_field_mappings_for_missing_fields(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        调整字段映射以处理缺失字段的情况
        特别是处理USD Sale Amount和USD Payout字段的备用映射
        """
        adjusted_mappings = self.field_mappings.copy()
        
        # 处理USD Sale Amount字段的备用映射
        if 'USD Sale Amount' in adjusted_mappings:
            original_mapping = adjusted_mappings['USD Sale Amount']
            
            if original_mapping == 'E.Value Release' and 'E.Value Release' not in df.columns:
                # 如果E.Value Release字段不存在，使用Event Value作为备用
                if 'Event Value' in df.columns:
                    adjusted_mappings['USD Sale Amount'] = 'Event Value'
                    self.logger.info("🔧 调整USD Sale Amount映射: E.Value Release -> Event Value (备用映射)")
                else:
                    self.logger.warning("⚠️ 既没有E.Value Release也没有Event Value字段，USD Sale Amount将为空")
            elif original_mapping in df.columns:
                self.logger.info(f"✅ USD Sale Amount映射正常: {original_mapping}")
            else:
                self.logger.warning(f"⚠️ USD Sale Amount映射字段不存在: {original_mapping}")
        
        # 处理USD Payout字段的备用映射
        if 'USD Payout' in adjusted_mappings:
            original_mapping = adjusted_mappings['USD Payout']
            
            if original_mapping == 'Cost' and 'Cost' not in df.columns:
                # 如果Cost字段不存在，查找其他可能的成本字段
                cost_alternatives = ['Payout', 'Commission', 'Fee']
                found_alternative = False
                
                for alt_field in cost_alternatives:
                    if alt_field in df.columns:
                        adjusted_mappings['USD Payout'] = alt_field
                        self.logger.info(f"🔧 调整USD Payout映射: Cost -> {alt_field} (备用映射)")
                        found_alternative = True
                        break
                
                if not found_alternative:
                    self.logger.warning("⚠️ 没有找到Cost相关字段，USD Payout将为空")
            elif original_mapping in df.columns:
                self.logger.info(f"✅ USD Payout映射正常: {original_mapping}")
            else:
                self.logger.warning(f"⚠️ USD Payout映射字段不存在: {original_mapping}")
        
        return adjusted_mappings
    
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
            
            # 处理USD Sale Amount字段的备用映射
            adjusted_mappings = self._adjust_field_mappings_for_missing_fields(df)
            
            # 使用统一字段映射器进行映射
            unified_df = self.unified_mapper.map_dataframe_to_unified_fields(df, adjusted_mappings)
            
            # 应用数据转换
            unified_df = self.unified_mapper.apply_data_transformations(unified_df, self.data_transformations)
            
            mapping_info = {
                'platform': 'leads_adn',
                'field_mappings': adjusted_mappings,
                'data_transformations': self.data_transformations,
                'mapped_fields_count': len([k for k, v in adjusted_mappings.items() if v in df.columns]),
                'total_unified_fields': len(unified_df.columns)
            }
            
            self.logger.info(f"✅ LeadsADN字段映射完成: {len(unified_df.columns)} 个统一字段")
            return unified_df, mapping_info
            
        except Exception as e:
            self.logger.error(f"❌ LeadsADN字段映射失败: {e}")
            # 返回空的统一格式DataFrame
            empty_df = self.unified_mapper.map_dataframe_to_unified_fields(pd.DataFrame(), {})
            return empty_df, {'error': str(e)}
    
    def _apply_partner_mapping(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        应用Partner字段映射
        Partner字段已通过Google Sheets映射从Affiliate获得，这里只需要进行Partner名称转换
        例如：'(2)DL' -> 'DL' -> 'DeepLeaper'
        """
        try:
            if 'Partner' not in df.columns:
                self.logger.warning("⚠️ 未找到Partner字段")
                df['Partner'] = 'Unknown'
                return df
            
            # 调试：查看Partner字段的原始值
            self.logger.info(f"🔍 Partner字段映射后的原始值（前5个）: {df['Partner'].head().tolist()}")
            
            # 处理Partner字段值（从Affiliate字段映射而来）
            def process_partner_value(partner_value):
                if pd.isna(partner_value) or partner_value == '':
                    return 'Unknown'
                
                # 提取括号后的内容，例如 "(2)DL" -> "DL"
                partner_str = str(partner_value).strip()
                
                # 使用正则表达式提取括号后的内容
                import re
                match = re.search(r'\([^)]*\)(.+)', partner_str)
                if match:
                    partner_code = match.group(1).strip()
                    self.logger.debug(f"正则匹配成功: '{partner_str}' -> '{partner_code}'")
                else:
                    # 如果没有括号，使用原始值
                    partner_code = partner_str
                    self.logger.debug(f"正则匹配失败，使用原始值: '{partner_str}' -> '{partner_code}'")
                
                return partner_code
            
            # 应用Partner值处理
            df['Partner'] = df['Partner'].apply(process_partner_value)
            
            # 应用Partner映射（使用config.py的match_source_to_partner函数）
            try:
                from config import match_source_to_partner
                
                def map_partner_name(partner_code):
                    if partner_code in ['Unknown', '']:
                        return partner_code
                    
                    # 使用config.py中的映射函数
                    mapped_partner = match_source_to_partner(partner_code)
                    if mapped_partner != partner_code:  # 如果有映射结果
                        return mapped_partner
                    return partner_code
                
                # 应用Partner映射
                df['Partner'] = df['Partner'].apply(map_partner_name)
                self.logger.info("✅ Partner映射完成")
                
            except Exception as e:
                self.logger.warning(f"⚠️ Partner映射失败，使用原始值: {e}")
            
            # 统计Partner分布
            partner_counts = df['Partner'].value_counts()
            self.logger.info("📊 Partner分布统计:")
            for partner, count in partner_counts.items():
                self.logger.info(f"   - {partner}: {count} 条记录")
            
            return df
            
        except Exception as e:
            self.logger.error(f"❌ Partner映射失败: {e}")
            df['Partner'] = 'Unknown'
            return df

    def _extract_partner_info_from_raw_old(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        LeadsADN平台专用：直接从Affiliate字段提取Partner信息
        例如：Affiliate="(2)DL" -> Partner="DL"
        """
        try:
            # 确保Affiliate字段存在（需要从原始数据提取）
            if 'Affiliate' not in df.columns:
                self.logger.warning("⚠️ 未找到Affiliate字段，无法提取Partner信息")
                df['Partner'] = 'Unknown'
                return df
            
            def extract_partner_from_affiliate(affiliate_value):
                """从Affiliate字段提取Partner，支持 (数字)Partner 格式"""
                if pd.isna(affiliate_value) or str(affiliate_value).strip() == '':
                    return 'Unknown'
                
                affiliate_str = str(affiliate_value).strip()
                
                # 检查是否为空或无效值
                if not affiliate_str or affiliate_str.lower() in ['nan', 'none', 'null', '', 'unknown']:
                    return 'Unknown'
                
                # LeadsADN专用：处理 "(数字)Partner" 格式，如 "(2)DL"
                if affiliate_str.startswith('(') and ')' in affiliate_str:
                    try:
                        # 找到右括号位置
                        bracket_end = affiliate_str.index(')')
                        if bracket_end + 1 < len(affiliate_str):
                            # 提取括号后的内容作为Partner
                            partner = affiliate_str[bracket_end + 1:].strip()
                            if partner:
                                self.logger.debug(f"从Affiliate '{affiliate_str}' 提取Partner: '{partner}'")
                                return partner
                    except:
                        pass  # 如果解析失败，使用原字符串
                
                # 如果不是标准格式，直接返回原值（去除空格）
                partner = affiliate_str.strip()
                self.logger.debug(f"直接使用Affiliate值作为Partner: '{partner}'")
                return partner
            
            # 应用Partner提取
            df['Partner'] = df['Affiliate'].apply(extract_partner_from_affiliate)
            
            # 应用Partner映射（使用config.py的match_source_to_partner函数）
            try:
                import sys
                import os
                sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                from config import match_source_to_partner
                
                def map_partner_name(partner_value):
                    """将原始Partner值映射为标准Partner名称"""
                    if pd.isna(partner_value) or str(partner_value).strip() == '':
                        return 'Unknown'
                    
                    partner_str = str(partner_value).strip()
                    # 使用配置中的映射逻辑
                    mapped_partner = match_source_to_partner(partner_str)
                    return mapped_partner
                
                # 应用Partner映射
                df['Partner'] = df['Partner'].apply(map_partner_name)
                self.logger.info("✅ Partner映射完成")
                
            except Exception as e:
                self.logger.warning(f"⚠️ Partner映射失败，使用原始值: {e}")
            
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
    
    def _apply_advertiser_specific_currency_conversion_before_mapping(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        在字段映射前基于Advertiser字段应用特定的货币转换逻辑
        当Advertiser为"(5)TTS_LinkShare"时，将E.Value Release和Cost字段从印尼盾转换为美元
        """
        try:
            # 检查是否有Advertiser字段（原始字段名）
            if 'Advertiser' not in df.columns:
                self.logger.warning("⚠️ 没有Advertiser字段，跳过特定货币转换")
                return df
            
            # 检查是否有需要货币转换的记录
            tts_mask = df['Advertiser'].str.contains(r'\(5\)TTS_LinkShare', na=False)
            tts_count = tts_mask.sum()
            
            dn_bm_mask = df['Advertiser'].str.contains(r'\(2\)DN_BM', na=False)
            dn_bm_count = dn_bm_mask.sum()
            
            # 调试：显示Advertiser字段的前几个值
            self.logger.info(f"🔍 原始Advertiser字段前5个值: {df['Advertiser'].head().tolist()}")
            self.logger.info(f"🔍 原始Advertiser字段唯一值数量: {df['Advertiser'].nunique()}")
            
            total_conversion_count = tts_count + dn_bm_count
            
            if total_conversion_count == 0:
                self.logger.info("✅ 没有需要特定货币转换的记录，跳过特定货币转换")
                return df
            
            self.logger.info(f"🔍 发现需要货币转换的记录:")
            if tts_count > 0:
                self.logger.info(f"   - TTS_LinkShare: {tts_count} 条记录")
            if dn_bm_count > 0:
                self.logger.info(f"   - DN_BM: {dn_bm_count} 条记录")
            self.logger.info(f"🔍 开始预处理货币转换，总计: {total_conversion_count} 条记录")
            
            # 处理E.Value Release字段（将成为USD Sale Amount）
            if 'E.Value Release' in df.columns:
                def convert_idr_evalue_release(row):
                    """针对TTS_LinkShare和DN_BM转换E.Value Release字段"""
                    advertiser = str(row.get('Advertiser', ''))
                    original_value = row.get('E.Value Release', 0)
                    
                    # 检查是否需要转换（TTS_LinkShare或DN_BM）
                    if '(5)TTS_LinkShare' in advertiser or '(2)DN_BM' in advertiser:
                        try:
                            # 将印尼盾转换为美元
                            idr_amount = float(original_value) if original_value else 0.0
                            usd_amount = currency_converter.convert_idr_to_usd(idr_amount)
                            advertiser_type = "TTS_LinkShare" if '(5)TTS_LinkShare' in advertiser else "DN_BM"
                            self.logger.debug(f"{advertiser_type} E.Value Release转换: {idr_amount} IDR -> {usd_amount:.6f} USD")
                            return usd_amount
                        except Exception as e:
                            advertiser_type = "TTS_LinkShare" if '(5)TTS_LinkShare' in advertiser else "DN_BM"
                            self.logger.warning(f"{advertiser_type} E.Value Release转换失败: {e}")
                            return original_value
                    else:
                        return original_value
                
                # 应用转换
                df['E.Value Release'] = df.apply(convert_idr_evalue_release, axis=1)
                
                # 分别统计转换结果
                if tts_count > 0:
                    tts_evalue_converted = df.loc[tts_mask, 'E.Value Release'].sum()
                    self.logger.info(f"💰 TTS_LinkShare E.Value Release转换完成: 总金额 ${tts_evalue_converted:,.6f} USD")
                
                if dn_bm_count > 0:
                    dn_bm_evalue_converted = df.loc[dn_bm_mask, 'E.Value Release'].sum()
                    self.logger.info(f"💰 DN_BM E.Value Release转换完成: 总金额 ${dn_bm_evalue_converted:,.6f} USD")
            
            # 处理Cost字段（将成为USD Payout）
            if 'Cost' in df.columns:
                def convert_idr_cost(row):
                    """针对TTS_LinkShare和DN_BM转换Cost字段"""
                    advertiser = str(row.get('Advertiser', ''))
                    original_value = row.get('Cost', 0)
                    
                    # 检查是否需要转换（TTS_LinkShare或DN_BM）
                    if '(5)TTS_LinkShare' in advertiser or '(2)DN_BM' in advertiser:
                        try:
                            # 将印尼盾转换为美元
                            idr_amount = float(original_value) if original_value else 0.0
                            usd_amount = currency_converter.convert_idr_to_usd(idr_amount)
                            advertiser_type = "TTS_LinkShare" if '(5)TTS_LinkShare' in advertiser else "DN_BM"
                            self.logger.debug(f"{advertiser_type} Cost转换: {idr_amount} IDR -> {usd_amount:.6f} USD")
                            return usd_amount
                        except Exception as e:
                            advertiser_type = "TTS_LinkShare" if '(5)TTS_LinkShare' in advertiser else "DN_BM"
                            self.logger.warning(f"{advertiser_type} Cost转换失败: {e}")
                            return original_value
                    else:
                        return original_value
                
                # 应用转换
                df['Cost'] = df.apply(convert_idr_cost, axis=1)
                
                # 分别统计转换结果
                if tts_count > 0:
                    tts_cost_converted = df.loc[tts_mask, 'Cost'].sum()
                    self.logger.info(f"💰 TTS_LinkShare Cost转换完成: 总金额 ${tts_cost_converted:,.6f} USD")
                
                if dn_bm_count > 0:
                    dn_bm_cost_converted = df.loc[dn_bm_mask, 'Cost'].sum()
                    self.logger.info(f"💰 DN_BM Cost转换完成: 总金额 ${dn_bm_cost_converted:,.6f} USD")
            
            self.logger.info("✅ 预处理货币转换完成")
            return df
            
        except Exception as e:
            self.logger.error(f"❌ 预处理货币转换失败: {e}")
            return df

    def _apply_advertiser_specific_currency_conversion(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        基于Advertiser字段应用特定的货币转换逻辑 - 现在仅用于验证
        实际转换已在预处理阶段完成
        """
        try:
            # 检查是否有Advertiser字段
            if 'Advertiser' not in df.columns:
                self.logger.info("ℹ️ 货币转换已在预处理阶段完成")
                return df
            
            # 检查是否有需要特定转换的记录（用于验证）
            tts_mask = df['Advertiser'].str.contains(r'\(5\)TTS_LinkShare', na=False)
            tts_count = tts_mask.sum()
            
            dn_bm_mask = df['Advertiser'].str.contains(r'\(2\)DN_BM', na=False)
            dn_bm_count = dn_bm_mask.sum()
            
            total_count = tts_count + dn_bm_count
            
            if total_count > 0:
                if tts_count > 0:
                    self.logger.info(f"✅ TTS_LinkShare货币转换验证: {tts_count} 条记录已在预处理阶段完成转换")
                if dn_bm_count > 0:
                    self.logger.info(f"✅ DN_BM货币转换验证: {dn_bm_count} 条记录已在预处理阶段完成转换")
            else:
                self.logger.info("✅ 没有需要特定货币转换的记录")
            
            return df
            
        except Exception as e:
            self.logger.error(f"❌ 特定货币转换验证失败: {e}")
            return df

    def _validate_currency_conversion(self, df: pd.DataFrame) -> None:
        """
        验证智能货币转换结果
        检查 USD Sale Amount 和 USD Payout 字段的转换结果
        """
        try:
            # 验证 USD Sale Amount 字段
            if 'USD Sale Amount' in df.columns:
                usd_sale_total = df['USD Sale Amount'].sum()
                usd_sale_count = (df['USD Sale Amount'] > 0).sum()
                self.logger.info(f"💰 USD Sale Amount 验证: {usd_sale_count} 条记录，总金额 ${usd_sale_total:,.2f}")
                
                # 检查是否有原始数据用于比较
                if 'E.Value Release' in df.columns:
                    original_total = pd.to_numeric(df['E.Value Release'], errors='coerce').sum()
                    self.logger.info(f"📊 原始 E.Value Release 总计: {original_total:,.2f}")
                
                # 特别检查TTS_LinkShare的转换结果
                if 'Advertiser' in df.columns:
                    tts_mask = df['Advertiser'].str.contains(r'\(5\)TTS_LinkShare', na=False)
                    if tts_mask.sum() > 0:
                        tts_sale_total = df.loc[tts_mask, 'USD Sale Amount'].sum()
                        tts_sale_count = tts_mask.sum()
                        self.logger.info(f"🔍 TTS_LinkShare销售金额: {tts_sale_count} 条记录，总金额 ${tts_sale_total:,.2f}")
            
            # 验证 USD Payout 字段
            if 'USD Payout' in df.columns:
                usd_payout_total = df['USD Payout'].sum()
                usd_payout_count = (df['USD Payout'] > 0).sum()
                self.logger.info(f"💰 USD Payout 验证: {usd_payout_count} 条记录，总金额 ${usd_payout_total:,.2f}")
                
                # 检查是否有原始数据用于比较
                if 'Cost' in df.columns:
                    original_cost_total = pd.to_numeric(df['Cost'], errors='coerce').sum()
                    self.logger.info(f"📊 原始 Cost 总计: {original_cost_total:,.2f}")
                
                # 特别检查TTS_LinkShare的转换结果
                if 'Advertiser' in df.columns:
                    tts_mask = df['Advertiser'].str.contains(r'\(5\)TTS_LinkShare', na=False)
                    if tts_mask.sum() > 0:
                        tts_payout_total = df.loc[tts_mask, 'USD Payout'].sum()
                        tts_payout_count = tts_mask.sum()
                        self.logger.info(f"🔍 TTS_LinkShare支出金额: {tts_payout_count} 条记录，总金额 ${tts_payout_total:,.2f}")
            
            # 统计智能转换的效果
            conversion_stats = {
                'total_records': len(df),
                'usd_sale_records': (df['USD Sale Amount'] > 0).sum() if 'USD Sale Amount' in df.columns else 0,
                'usd_payout_records': (df['USD Payout'] > 0).sum() if 'USD Payout' in df.columns else 0,
                'total_usd_sale': df['USD Sale Amount'].sum() if 'USD Sale Amount' in df.columns else 0,
                'total_usd_payout': df['USD Payout'].sum() if 'USD Payout' in df.columns else 0
            }
            
            self.logger.info(f"📊 智能货币转换统计: {conversion_stats}")
            
        except Exception as e:
            self.logger.error(f"❌ 货币转换验证失败: {e}")
    
    def _generate_source_field(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        从映射后的Publisher Sub ID 1-5字段生成Source字段
        例如: Publisher Sub ID 1=(3)FTK, Publisher Sub ID 2=FTK 
        生成: Source=(3)FTK_FTK
        包含Publisher Sub ID 1（来自Affiliate字段）和其他Sub ID字段
        """
        try:
            def create_source(row):
                # LeadsADN专用逻辑：优先使用S1(DL相关)和S4(品牌)
                s1 = str(row.get('Publisher Sub ID 1', '')).strip()  # S1映射到Publisher Sub ID 1
                s4 = str(row.get('Publisher Sub ID 4', '')).strip()  # S4映射到Publisher Sub ID 4
                
                # 清理并提取有效值
                def clean_value(val):
                    if val and val not in ['nan', 'None', '']:
                        return val
                    return None
                
                s1_clean = clean_value(s1)
                s4_clean = clean_value(s4)
                
                # 生成Source：优先级 DL + 品牌
                if s1_clean and s4_clean:
                    # 提取DL部分（去除后缀数字）
                    dl_part = s1_clean.split('_')[0] if '_' in s1_clean else s1_clean
                    return f"{dl_part}_{s4_clean}"
                elif s1_clean:
                    # 只有DL部分
                    dl_part = s1_clean.split('_')[0] if '_' in s1_clean else s1_clean
                    return dl_part
                elif s4_clean:
                    # 只有品牌部分，加上DL前缀
                    return f"DL_{s4_clean}"
                else:
                    # 回退到完整的Sub ID组合
                    source_parts = []
                    for i in range(1, 6):  # Publisher Sub ID 1-5
                        col_name = f'Publisher Sub ID {i}'
                        if col_name in df.columns:
                            value = clean_value(str(row.get(col_name, '')))
                            if value:
                                source_parts.append(value)
                    
                    if source_parts:
                        return '_'.join(source_parts)
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
            
            if 'USD Payout' not in df.columns:
                self.logger.warning("⚠️ USD Payout字段缺失，设置为0")
                df['USD Payout'] = 0.0
            
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
