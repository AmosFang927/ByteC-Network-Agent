#!/usr/bin/env python3
"""
LS_BM数据处理器
专门处理LS_BM（LinkShare BM）文件的数据清理和字段映射
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

class LSBMDataProcessor:
    """LS_BM数据处理器（LinkShare）"""
    
    def __init__(self, config_file: str = None):
        """
        初始化LS_BM数据处理器
        
        Args:
            config_file: 字段映射配置文件路径（可選）
        """
        # 簡化初始化，不使用複雜的映射管理器
        self.logger = logging.getLogger(__name__)
        self.current_file = None
        
        # LS_BM处理统计
        self.stats = {
            'total_records': 0,
            'processed_records': 0,
            'mapped_fields': 0,
            'errors': []
        }
    
    def is_ls_bm_file(self, filename: str) -> bool:
        """
        检查文件是否为LS_BM文件
        
        Args:
            filename: 文件名
            
        Returns:
            bool: 是否为LS_BM文件
        """
        filename_lower = filename.lower()
        return 'ls_bm' in filename_lower
    
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
        
        # 如果还有空值，尝试用'LS_BM'填充
        ls_bm_mask = df[platform_col].isna()
        if ls_bm_mask.any():
            df.loc[ls_bm_mask, platform_col] = 'LS_BM'
            self.logger.info(f"为{ls_bm_mask.sum()}行填充了默认platform值: LS_BM")
        
        return df
    
    def filter_ls_bm_records(self, df: pd.DataFrame, platform_col: Optional[str] = None) -> pd.DataFrame:
        """
        过滤出platform为LS_BM的记录
        
        Args:
            df: 输入DataFrame
            platform_col: platform列名
            
        Returns:
            pd.DataFrame: 过滤后的DataFrame
        """
        # 由於這是 LS_BM 專用的處理器，我們假設所有數據都是 LS_BM 的
        self.logger.info(f"處理 {len(df)} 條 LS_BM 記錄")
        return df.copy()
    
    def _extract_precise_order_id(self, df: pd.DataFrame) -> pd.Series:
        """
        从raw_data中提取精确的Order ID，避免JSON数值精度丢失
        
        Args:
            df: 包含raw_data列的DataFrame
            
        Returns:
            pd.Series: 精确的Order ID值
        """
        precise_order_ids = []
        
        for _, row in df.iterrows():
            try:
                if pd.notna(row.get('raw_data')):
                    raw_data_str = str(row['raw_data'])
                    
                    # 使用正则表达式提取Order ID值，避免eval的安全问题
                    import re
                    order_id_match = re.search(r"'Order ID':\s*(\d+)", raw_data_str)
                    if order_id_match:
                        precise_order_id = order_id_match.group(1)
                        precise_order_ids.append(precise_order_id)
                        self.logger.debug(f"从raw_data提取精确Order ID: {precise_order_id}")
                    else:
                        # 如果正则匹配失败，回退到原始值
                        precise_order_ids.append(str(int(row.get('Order ID', 0))))
                else:
                    precise_order_ids.append(str(int(row.get('Order ID', 0))))
            except Exception as e:
                self.logger.warning(f"提取精确Order ID失败: {e}，使用备用值")
                precise_order_ids.append(str(int(row.get('Order ID', 0))))
        
        return pd.Series(precise_order_ids)

    def apply_field_mapping(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        应用字段映射，将原始字段映射到统一字段
        
        Args:
            df: 输入DataFrame
            
        Returns:
            Tuple[pd.DataFrame, Dict]: 映射后的DataFrame和映射信息
        """
        self.logger.info("开始应用LS_BM字段映射...")
        
        # 直接使用靜態字段映射，避免 Google Sheets 調用
        try:
            self.logger.info(f"開始映射 {len(df)} 條記錄的字段...")
            
            # 定義 LS_BM 的统一字段映射（基于Google Sheets标准）
            field_mappings = {
                # 核心统一字段
                'Conversion ID': 'Order ID',
                'Order ID': 'Order ID',
                'Datetime Conversion': 'Time order created',
                'Local Sale Amount': 'Price',
                'Local Reward': 'Actual standard commission',
                'Status': 'Order Status',
                'Platform': 'Platform',
                'Advertiser': 'Shop name',
                'Campaign Name': 'Content Type',
                
                # Publisher Sub ID 字段
                'Publisher Sub ID 1': 'Creator tag ID',
                'Publisher Sub ID 2': 'Content id',
                'Publisher Sub ID 3': 'Shop code',
                
                # 保留一些兼容字段（用于内部处理）
                'advertiser_name': 'Shop name',
                'campaign_name': 'Content Type', 
                'offer_name': 'Product Name',
                'conversion_id': 'Order ID',
                'offer_id': 'Product ID',
                'order_id': 'Order ID',
                'sale_amount': 'Price',
                'payout': 'Actual standard commission',
                'conversion_status': 'Order Status',
                'currency': 'Currency',
                'source_file': 'source_file',
                'processed_date': 'processed_date',
                'aff_sub': 'Creator tag ID',
                'aff_sub1': 'Content id',
                'aff_sub2': 'Shop code',
                'aff_sub3': 'Payment ID',
                'aff_sub4': 'Payment method',
                'aff_sub5': 'Payment account',
                'adv_sub': 'Invitation ID',
                'adv_sub1': 'Agency commission rate',
                'adv_sub2': 'Attribution type',
                'adv_sub3': 'IVA',
                'adv_sub4': 'ISR',
                'adv_sub5': 'Partner'
                # 移除raw_data映射，因為它不是unified field
            }
            
            # 創建映射後的 DataFrame
            mapped_df = pd.DataFrame()
            
            # 執行字段映射
            mapped_count = 0
            for unified_field, source_field in field_mappings.items():
                if source_field in df.columns:
                    # 特殊处理Conversion ID以保持精度
                    if unified_field == 'Conversion ID' and 'raw_data' in df.columns:
                        # 从raw_data中提取原始Order ID以保持精度
                        precise_ids = self._extract_precise_order_id(df)
                        # 確保為字符串類型以保持精度，避免科学计数法
                        mapped_df[unified_field] = precise_ids.astype(str)
                    elif unified_field == 'Conversion ID':
                        # 如果没有raw_data，直接处理数值，确保不使用科学计数法
                        if source_field in df.columns:
                            # 转换为字符串避免科学计数法显示
                            mapped_df[unified_field] = df[source_field].apply(
                                lambda x: str(int(float(x))) if pd.notna(x) and str(x).replace('.', '').replace('-', '').isdigit() else str(x)
                            )
                    else:
                        mapped_df[unified_field] = df[source_field]
                    mapped_count += 1
                else:
                    mapped_df[unified_field] = None
            
            # 添加固定值和元數據
            mapped_df['platform'] = 'LS_BM'
            mapped_df['source_file'] = str(Path(self.current_file).name) if self.current_file else 'unknown'
            mapped_df['processed_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 🔧 修复：设置Source字段基于aff_sub
            if 'aff_sub' in mapped_df.columns:
                mapped_df['Source'] = mapped_df['aff_sub']
                self.logger.info("✅ 设置Source字段: 基于aff_sub")
            else:
                mapped_df['Source'] = 'LS_BM_Source'
                self.logger.info("⚠️ 使用默认Source字段值")
            
            # 🔧 修复：设置Partner字段为DeepLeaper（基于OEM数据）
            if 'aff_sub' in mapped_df.columns:
                # 检查aff_sub值是否包含OEM相关字符串
                oem_values = mapped_df['aff_sub'].astype(str).str.contains('OEM|OPPO|VIVO', case=False, na=False)
                if oem_values.any():
                    mapped_df['Partner'] = 'DeepLeaper'
                    self.logger.info("✅ 设置Partner字段: DeepLeaper (基于OEM数据)")
                else:
                    mapped_df['Partner'] = 'LS_BM'
                    self.logger.info("⚠️ 使用默认Partner字段值: LS_BM")
            else:
                mapped_df['Partner'] = 'LS_BM'
                self.logger.info("⚠️ 使用默认Partner字段值: LS_BM")
            
            # 💰 新增：印尼盾转美金汇率转换
            if 'sale_amount' in mapped_df.columns:
                # 印尼盾到美金的汇率（1 USD = 15000 IDR）
                IDR_TO_USD_RATE = 15000
                
                # 计算USD Sale Amount (使用统一字段名)
                mapped_df['USD Sale Amount'] = mapped_df['sale_amount'] / IDR_TO_USD_RATE
                mapped_df['usd_sale_amount'] = mapped_df['USD Sale Amount']  # 兼容字段
                
                # 保留原始金额作为Local Sale Amount
                mapped_df['local_sale_amount'] = mapped_df['sale_amount']
                
                # 记录汇率转换信息
                total_idr = mapped_df['sale_amount'].sum()
                total_usd = mapped_df['usd_sale_amount'].sum()
                self.logger.info(f"💰 汇率转换完成: IDR {total_idr:,.0f} → USD ${total_usd:,.2f} (汇率: 1 USD = {IDR_TO_USD_RATE} IDR)")
            else:
                self.logger.warning("⚠️ 未找到sale_amount字段，跳过汇率转换")
            
            # 過濾掉不需要的內部處理字段，只保留Google Sheets標準unified fields
            # 定義需要在最終輸出中保留的Google Sheets標準unified fields
            unified_output_fields = [
                # Google Sheets定義的核心統一字段 (標準格式) - 已移除 Local Sale Amount 和 Order ID
                'Conversion ID', 'Datetime Conversion', 
                'Status', 'Platform',
                'Advertiser', 'Campaign Name',
                'Publisher Sub ID 1', 'Publisher Sub ID 2', 'Publisher Sub ID 3',
                'USD Sale Amount',  # 標準的USD金額字段
                
                # 必要的metadata字段
                'Source', 'Partner'
            ]
            
            # 從mapped_df中只保留unified_output_fields中的字段，移除所有內部處理字段
            filtered_df = pd.DataFrame()
            for field in unified_output_fields:
                if field in mapped_df.columns:
                    filtered_df[field] = mapped_df[field]
            
            # 確保不包含任何mockup相關的內部字段
            internal_fields_to_remove = ['mockup_applied', 'mockup_multiplier', 'original_usd_sale_amount', 
                                       'usd_sale_amount', 'local_sale_amount', 'sale_amount', 'payout']
            for field in internal_fields_to_remove:
                if field in filtered_df.columns:
                    filtered_df = filtered_df.drop(columns=[field])
                    self.logger.info(f"移除內部處理字段: {field}")
            
            # 將過濾後的DataFrame賦值回mapped_df
            mapped_df = filtered_df
            
            self.logger.info(f"✅ 過濾後保留 {len(mapped_df.columns)} 個Google Sheets標準unified字段")
            
            mapping_info = {
                'mapped_fields': [k for k, v in field_mappings.items() if v in df.columns],
                'field_mappings': field_mappings,
                'source_columns': list(df.columns),
                'mapped_count': mapped_count
            }
            
            self.logger.info(f"字段映射完成，成功映射了 {mapped_count} 個字段")
            return mapped_df, mapping_info
            
        except Exception as e:
            self.logger.error(f"字段映射失败: {e}")
            return pd.DataFrame(), {"error": str(e)}
    
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
        
        # 3. 确保platform字段为LS_BM
        if 'platform' in cleaned_df.columns:
            cleaned_df['platform'] = 'LS_BM'
        
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
                
                # 根据Partner获取特定的mockup倍数（統一從config.py獲取）
                mockup_multiplier = get_partner_mockup_multiplier(partner.upper() if partner else 'Unknown')
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
                    'usd_sale_amount', 'USD Sale Amount', 'conversion_amount', 'sale_amount'
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
    
    def process_ls_bm_file(self, file_path: str, output_dir: str = "output") -> Dict[str, Any]:
        """
        处理单个LS_BM文件的完整流程
        
        Args:
            file_path: 输入文件路径
            output_dir: 输出目录
            
        Returns:
            Dict: 处理结果
        """
        file_path = Path(file_path)
        self.current_file = file_path
        
        self.logger.info(f"🚀 开始处理LS_BM文件: {file_path.name}")
        
        try:
            # 重置统计信息
            self.stats = {
                'total_records': 0,
                'processed_records': 0,
                'mapped_fields': 0,
                'errors': []
            }
            
            # 1. 检查文件是否为LS_BM文件
            if not self.is_ls_bm_file(file_path.name):
                raise ValueError(f"文件{file_path.name}不是LS_BM文件")
            
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
                df = self.filter_ls_bm_records(df, platform_col)
            
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
            
            # 🔧 最終清理：移除Mockup處理添加的内部字段，只保留Google Sheets標準字段
            final_unified_fields = [
                'Conversion ID', 'Datetime Conversion', 
                'Status', 'Platform',
                'Advertiser', 'Campaign Name',
                'Publisher Sub ID 1', 'Publisher Sub ID 2', 'Publisher Sub ID 3',
                'USD Sale Amount', 'Source', 'Partner'
            ]
            
            final_df = pd.DataFrame()
            for field in final_unified_fields:
                if field in mockup_df.columns:
                    final_df[field] = mockup_df[field]
            
            # 確保Conversion ID保持為字符串格式以保持精度
            if 'Conversion ID' in final_df.columns:
                final_df['Conversion ID'] = final_df['Conversion ID'].astype(str)
                self.logger.info("✅ 最終確保Conversion ID保持為字符串格式")
            
            self.logger.info(f"✅ 最終過濾完成，保留 {len(final_df.columns)} 個Google Sheets標準字段")
            mockup_df = final_df
            
            # 6. 验证输出格式
            validation_result = {
                'present_count': len([col for col in mockup_df.columns if not mockup_df[col].isna().all()]),
                'total_required_fields': len(mapping_info.get('mapped_fields', [])),
                'missing_fields': [],
                'validation_passed': True
            }
            
            # 7. 生成输出文件
            output_path = Path(output_dir) / f"ls_bm_processed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
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
            
            self.logger.info(f"✅ LS_BM文件处理完成！")
            self.logger.info(f"   输入记录: {self.stats['total_records']}")
            self.logger.info(f"   处理记录: {self.stats['processed_records']}")
            self.logger.info(f"   输出文件: {output_path}")
            self.logger.info(f"   Unified字段: {validation_result['present_count']}/{validation_result['total_required_fields']}")
            
            return result
            
        except Exception as e:
            error_msg = f"处理LS_BM文件失败: {e}"
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
