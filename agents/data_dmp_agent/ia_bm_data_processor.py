#!/usr/bin/env python3
"""
IA_BM数据处理器
专门处理IA_BM（Involve Asia BM）文件的数据清理和字段映射
集成现有的字段映射管理器和统一字段映射器
"""

import logging
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

# 导入现有的映射管理器
from .field_mapping_manager import FieldMappingManager
from .unified_field_mapper import UnifiedFieldMapper

logger = logging.getLogger(__name__)

class ATBMDataProcessor:
    """AT_BM数据处理器（Access Trade）"""
    
    def __init__(self, config_file: str = "config/field_mapping_config.json"):
        """
        初始化AT_BM数据处理器
        
        Args:
            config_file: 字段映射配置文件路径
        """
        self.field_mapping_manager = FieldMappingManager(config_file)
        self.unified_mapper = UnifiedFieldMapper()
        self.logger = logging.getLogger(__name__)
        
        # AT_BM处理统计
        self.stats = {
            'total_records': 0,
            'processed_records': 0,
            'mapped_fields': 0,
            'errors': []
        }
    
    def is_at_bm_file(self, filename: str) -> bool:
        """
        检查文件是否为AT_BM文件
        
        Args:
            filename: 文件名
            
        Returns:
            bool: 是否为AT_BM文件
        """
        filename_lower = filename.lower()
        return 'at_bm' in filename_lower
    
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
        
        # 如果还有空值，尝试用'IA_BM'填充
        ia_bm_mask = df[platform_col].isna()
        if ia_bm_mask.any():
            df.loc[ia_bm_mask, platform_col] = 'IA_BM'
            self.logger.info(f"为{ia_bm_mask.sum()}行填充了默认platform值: IA_BM")
        
        return df
    
    def filter_at_bm_records(self, df: pd.DataFrame, platform_col: Optional[str] = None) -> pd.DataFrame:
        """
        过滤出platform为AT_BM的记录
        
        Args:
            df: 输入DataFrame
            platform_col: platform列名
            
        Returns:
            pd.DataFrame: 过滤后的DataFrame
        """
        if platform_col and platform_col in df.columns:
            # 查找AT_BM相关的记录
            at_bm_mask = df[platform_col].str.contains(
                'AT_BM|at_bm|Access Trade|access_trade', 
                case=False, 
                na=False
            )
            filtered_df = df[at_bm_mask].copy()
            
            self.logger.info(f"从{len(df)}条记录中过滤出{len(filtered_df)}条AT_BM记录")
            return filtered_df
        else:
            # 如果没有platform列，假设整个文件都是AT_BM数据
            self.logger.info("未找到platform列，将整个文件视为AT_BM数据")
            return df.copy()
    
    def apply_field_mapping(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        应用字段映射，将原始字段映射到统一字段
        
        Args:
            df: 输入DataFrame
            
        Returns:
            Tuple[pd.DataFrame, Dict]: 映射后的DataFrame和映射信息
        """
        self.logger.info("开始应用AT_BM字段映射...")
        
        # 使用现有的字段映射管理器
        try:
            mapped_df, mapping_info = self.field_mapping_manager.map_dataframe_columns(
                df, 'access_trade'  # AT_BM映射到access_trade平台
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
        执行数据清理
        
        Args:
            df: 输入DataFrame
            
        Returns:
            pd.DataFrame: 清理后的DataFrame
        """
        self.logger.info("开始数据清理...")
        
        cleaned_df = df.copy()
        
        # 1. 移除完全空白的行
        cleaned_df = cleaned_df.dropna(how='all')
        
        # 2. 清理字符串字段的前后空格
        string_columns = cleaned_df.select_dtypes(include=['object']).columns
        for col in string_columns:
            cleaned_df[col] = cleaned_df[col].astype(str).str.strip()
            # 将'nan'字符串转换为实际的NaN
            cleaned_df[col] = cleaned_df[col].replace('nan', pd.NA)
        
        # 3. 确保platform字段为AT_BM
        if 'platform' in cleaned_df.columns:
            cleaned_df['platform'] = 'AT_BM'
        
        # 4. 设置处理时间戳
        if 'processed_date' in cleaned_df.columns:
            cleaned_df['processed_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        self.logger.info(f"数据清理完成，保留{len(cleaned_df)}条记录")
        return cleaned_df
    
    def apply_mockup_processing(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        应用Mockup数据处理 - 根据Partner特定配置
        
        Args:
            df: 输入DataFrame
            
        Returns:
            pd.DataFrame: 处理后的DataFrame
        """
        try:
            # 导入config中的mockup multiplier函数
            from config import get_partner_mockup_multiplier
            
            self.logger.info("🔄 正在应用Mockup处理...")
            
            processed_df = df.copy()
            original_total = 0
            adjusted_total = 0
            partner_multipliers = {}  # 记录每个Partner使用的倍数
            partner_stats = {}  # 记录每个Partner的统计
            
            for index, row in processed_df.iterrows():
                # 获取Partner信息
                partner = row.get('Partner', 'Unknown')
                
                # 根据Partner获取特定的mockup倍数
                if partner and partner.upper() in ['RAMPUP', 'DEEPLEAPER', 'TESTPARTNER', 'MKK', 'MP', 'FTK', 'BYTEC']:
                    mockup_multiplier = get_partner_mockup_multiplier(partner.upper())
                    partner_multipliers[partner] = mockup_multiplier
                else:
                    # 如果无法确定Partner，使用默认倍数1.0
                    mockup_multiplier = 1.0
                    partner_multipliers[partner] = mockup_multiplier
                
                # 初始化Partner统计
                if partner not in partner_stats:
                    partner_stats[partner] = {
                        'original_amount': 0,
                        'adjusted_amount': 0,
                        'count': 0
                    }
                
                # 处理金额欄位 - 支持多种欄位名稱
                amount_fields = [
                    'usd_sale_amount', 'USD Sale Amount', 'Sale Amount (USD)', 'conversion_amount', 'sale_amount'
                ]
                original_amount = 0
                amount_field_used = None
                
                for field in amount_fields:
                    if field in row and pd.notna(row[field]) and row[field] != '':
                        try:
                            amount_value = float(row[field])
                            if amount_value >= 0:  # 允许 0 金额，只排除负数
                                original_amount = amount_value
                                amount_field_used = field
                                break
                        except (ValueError, TypeError):
                            continue
                
                if original_amount and mockup_multiplier != 1.0:
                    adjusted_amount = round(original_amount * mockup_multiplier, 2)
                    # 更新所有相关的欄位
                    for field in amount_fields:
                        if field in processed_df.columns:
                            processed_df.at[index, field] = adjusted_amount
                    
                    original_total += original_amount
                    adjusted_total += adjusted_amount
                    
                    # 更新Partner统计
                    partner_stats[partner]['original_amount'] += original_amount
                    partner_stats[partner]['adjusted_amount'] += adjusted_amount
                    partner_stats[partner]['count'] += 1
                    
                    self.logger.debug(f"Mockup处理: {partner} - {amount_field_used}: ${original_amount} -> ${adjusted_amount} (倍数: {mockup_multiplier})")
                else:
                    # 即使没有调整金额，也要更新统计
                    if original_amount:
                        original_total += original_amount
                        adjusted_total += original_amount
                        partner_stats[partner]['original_amount'] += original_amount
                        partner_stats[partner]['adjusted_amount'] += original_amount
                        partner_stats[partner]['count'] += 1
                
                # 添加mockup处理标记
                processed_df.at[index, 'mockup_applied'] = True
                processed_df.at[index, 'mockup_multiplier'] = mockup_multiplier
                processed_df.at[index, 'original_usd_sale_amount'] = original_amount
            
            # 详细日志
            self.logger.info(f"📊 Mockup处理统计:")
            self.logger.info(f"   - 处理记录数: {len(processed_df)}")
            self.logger.info(f"   - 原始总金额: ${original_total:,.2f} USD")
            self.logger.info(f"   - 调整后总金额: ${adjusted_total:,.2f} USD")
            self.logger.info(f"   - 金额变化: ${adjusted_total - original_total:+,.2f} USD")
            if original_total > 0:
                change_percentage = ((adjusted_total - original_total) / original_total) * 100
                self.logger.info(f"   - 金额变化百分比: {change_percentage:+.2f}%")
            self.logger.info(f"   - Partner倍数分布: {partner_multipliers}")
            
            # 打印每个Partner的详细统计
            self.logger.info("📊 Partner详细统计 (Mockup前后金额):")
            for partner, stats in partner_stats.items():
                if stats['count'] > 0:
                    original = stats['original_amount']
                    adjusted = stats['adjusted_amount']
                    multiplier = partner_multipliers.get(partner, 1.0)
                    change = adjusted - original
                    change_pct = ((adjusted - original) / original * 100) if original > 0 else 0
                    
                    # 验证配置一致性
                    expected_multiplier = get_partner_mockup_multiplier(partner.upper() if partner else 'Unknown')
                    
                    self.logger.info(f"   💰 {partner}:")
                    self.logger.info(f"      📈 原始金额: ${original:,.2f} USD")
                    self.logger.info(f"      📈 调整后金额: ${adjusted:,.2f} USD")
                    self.logger.info(f"      📊 金额变化: ${change:+,.2f} USD ({change_pct:+.2f}%)")
                    self.logger.info(f"      ⚙️  实际倍数: {multiplier}")
                    self.logger.info(f"      ⚙️  预期倍数: {expected_multiplier} (来自 config.py)")
                    self.logger.info(f"      📋 记录数: {stats['count']}")
                    
                    # 配置一致性检查
                    if abs(multiplier - expected_multiplier) > 0.001:  # 允许微小的浮点误差
                        self.logger.warning(f"⚠️  警告: Partner '{partner}' 的实际 mockup 倍数 ({multiplier}) 与 config.py 配置 ({expected_multiplier}) 不一致！")
                        self.logger.warning(f"      请检查 config.py 中的 PARTNER_SOURCES_MAPPING['{partner}']['mockup_multiplier'] 配置")
                    else:
                        self.logger.info(f"      ✅ Mockup配置一致性检查通过")
            
            return processed_df
            
        except Exception as e:
            self.logger.error(f"❌ Mockup处理失败: {e}")
            # 如果处理失败，返回原始数据
            self.logger.warning("⚠️ 使用原始数据继续处理")
            return df
    
    def process_at_bm_file(self, file_path: str, output_dir: str = "output") -> Dict[str, Any]:
        """
        处理单个AT_BM文件的完整流程
        
        Args:
            file_path: 输入文件路径
            output_dir: 输出目录
            
        Returns:
            Dict: 处理结果
        """
        file_path = Path(file_path)
        
        self.logger.info(f"🚀 开始处理AT_BM文件: {file_path.name}")
        
        try:
            # 重置统计信息
            self.stats = {
                'total_records': 0,
                'processed_records': 0,
                'mapped_fields': 0,
                'errors': []
            }
            
            # 1. 检查文件是否为AT_BM文件
            if not self.is_at_bm_file(file_path.name):
                raise ValueError(f"文件{file_path.name}不是AT_BM文件")
            
            # 2. 读取文件
            self.logger.info("📖 读取文件...")
            if file_path.suffix.lower() == '.csv':
                df = pd.read_csv(file_path, encoding='utf-8')
            elif file_path.suffix.lower() in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            else:
                raise ValueError(f"不支持的文件格式: {file_path.suffix}")
            
            self.stats['total_records'] = len(df)
            self.logger.info(f"成功读取{len(df)}条记录，{len(df.columns)}个字段")
            
            # 3. 检测和处理platform列
            platform_col = self.detect_platform_column(df)
            if platform_col:
                df = self.handle_merged_cells(df, platform_col)
                df = self.filter_at_bm_records(df, platform_col)
            
            # 4. 应用字段映射
            self.logger.info("🔗 应用字段映射...")
            mapped_df, mapping_info = self.apply_field_mapping(df)
            
            # 5. 数据清理
            cleaned_df = self.clean_data(mapped_df)
            self.stats['processed_records'] = len(cleaned_df)
            
            # 🔧 新增步骤: 应用 Mockup 处理
            self.logger.info("💰 应用Mockup处理...")
            mockup_df = self.apply_mockup_processing(cleaned_df)
            self.stats['processed_records'] = len(mockup_df)
            
            # 6. 验证输出格式
            validation_result = self.unified_mapper.validate_unified_fields(mockup_df)
            
            # 7. 生成输出文件
            output_path = Path(output_dir) / f"at_bm_processed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            mockup_df.to_csv(output_path, index=False, encoding='utf-8')
            
            result = {
                'success': True,
                'input_file': str(file_path),
                'output_file': str(output_path),
                'stats': self.stats,
                'mapping_info': mapping_info,
                'validation': validation_result,
                'records_processed': len(mockup_df),
                'unified_fields_count': len(mockup_df.columns)
            }
            
            self.logger.info(f"✅ AT_BM文件处理完成！")
            self.logger.info(f"   输入记录: {self.stats['total_records']}")
            self.logger.info(f"   处理记录: {self.stats['processed_records']}")
            self.logger.info(f"   输出文件: {output_path}")
            self.logger.info(f"   Unified字段: {validation_result['present_count']}/{validation_result['total_required_fields']}")
            
            return result
            
        except Exception as e:
            error_msg = f"处理AT_BM文件失败: {e}"
            self.logger.error(error_msg)
            self.stats['errors'].append(error_msg)
            
            return {
                'success': False,
                'input_file': str(file_path),
                'error': error_msg,
                'stats': self.stats
            }
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """获取处理统计信息"""
        return self.stats.copy()
    
    def refresh_field_mappings(self) -> bool:
        """刷新字段映射配置"""
        try:
            return self.field_mapping_manager.refresh_mappings()
        except Exception as e:
            self.logger.error(f"刷新字段映射失败: {e}")
            return False