#!/usr/bin/env python3
"""
电商转化数据导入处理器
支持Excel文件导入、数据处理和输出
"""

import os
import sys
import argparse
import pandas as pd
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import (
    INPUT_DATA_REMOVE_COLUMNS,
    INPUT_DATA_DIR,
    INPUT_DATA_OUTPUT_DIR,
    INPUT_DATA_ENABLE_PANDASAI_ANALYSIS,
    INPUT_DATA_ENABLE_MOCKUP,
    INPUT_DATA_MOCKUP_MULTIPLIER,
    INPUT_DATA_OUTPUT_TEMPLATE,
    MOCKUP_MULTIPLIER,
    REMOVE_COLUMNS
)
from shared.utils.logger import log_info, log_warning, log_error, print_step

# 使用简单的logger
def log_info_simple(message):
    # Removed INFO logging to reduce output noise
    pass

def log_warning_simple(message):
    print(f"[WARNING] {message}")

def log_error_simple(message):
    print(f"[ERROR] {message}")

# 使用简单的logger函数
logger_info = log_info_simple
logger_warning = log_warning_simple
logger_error = log_error_simple


class DataImporter:
    """电商转化数据导入处理器"""
    
    def __init__(self):
        self.input_dir = Path(INPUT_DATA_DIR)
        self.output_dir = Path(INPUT_DATA_OUTPUT_DIR)
        self.current_filename = None  # 添加當前文件名跟踪
        self.ensure_directories()
        
    def ensure_directories(self):
        """确保必要的目录存在"""
        self.input_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
    
    def _detect_platform_from_filename(self) -> str:
        """從文件名檢測平台"""
        if not self.current_filename:
            return 'AT_BM'  # 默認
            
        filename_lower = self.current_filename.lower()
        
        if '_ls_bm' in filename_lower or 'linkshare' in filename_lower:
            return 'LS_BM'
        elif '_at_bm' in filename_lower or 'access_trade' in filename_lower:
            return 'AT_BM'
        elif '_ia_bm' in filename_lower or 'involve_asia' in filename_lower:
            return 'IA_BM'
        elif 'leads_adn' in filename_lower or 'leadsamdn' in filename_lower:
            return 'leads_adn'
        else:
            return 'AT_BM'  # 默認
        
    def analyze_data_with_pandasai(self, df):
        """使用详细分析器分析数据"""
        try:
            # 导入我们自己的分析器
            import sys
            from pathlib import Path
            
            # 添加data_input_agent目录到Python路径
            current_dir = Path(__file__).parent
            sys.path.insert(0, str(current_dir))
            
            from data_analyzer import DataAnalyzer
            
            analyzer = DataAnalyzer()
            analysis = analyzer.analyze_dataframe(df, "input_data")
            
            # 显示详细报告
            analyzer.print_analysis_report()
            
            # 保存分析报告
            analyzer.save_analysis_to_file()
            
            # logger_info("详细数据分析完成")
            return analysis
            
        except ImportError as e:
            logger_warning(f"高级分析器导入失败: {e}，使用简单分析")
            return self._simple_data_analysis(df)
        except Exception as e:
            logger_error(f"详细数据分析失败: {e}")
            return self._simple_data_analysis(df)
    
    def _simple_data_analysis(self, df):
        """简单的数据分析"""
        analysis = {
            "总记录数": len(df),
            "列数": len(df.columns),
            "列名": list(df.columns),
            "数据类型": df.dtypes.to_dict(),
            "缺失值统计": df.isnull().sum().to_dict(),
            "数值列统计": df.describe().to_dict() if df.select_dtypes(include=['number']).shape[1] > 0 else {}
        }
        return analysis
    
    def process_data(self, df):
        """处理数据"""
        logger_info("开始数据处理...")
        
        # 1. 移除指定列
        original_columns = list(df.columns)
        columns_to_remove = [col for col in INPUT_DATA_REMOVE_COLUMNS if col in df.columns]
        
        if columns_to_remove:
            df = df.drop(columns=columns_to_remove)
            logger_info(f"已移除列: {columns_to_remove}")
        
        # 2. 添加Partner分类（如果需要）
        if 'Partner' not in df.columns:
            df = self._add_partner_classification(df)
        
        # 3. 添加Platform字段
        if 'Platform' not in df.columns:
            df['Platform'] = 'access_trade'  # AccessTrade数据默认平台
            logger_info("已添加Platform字段: access_trade")
        
        # 4. 添加Source字段
        if 'Source' not in df.columns:
            # 优先级：Publisher Sub ID 1 > aff_sub > CLICK_URL > 默认值
            source_candidates = ['Publisher Sub ID 1', 'aff_sub', 'CLICK_URL']
            source_found = False
            
            for candidate_col in source_candidates:
                if candidate_col in df.columns and not source_found:
                    if candidate_col == 'Publisher Sub ID 1':
                        # 使用 Publisher Sub ID 1 作为 Source（过滤占位符）
                        def clean_source_value(value):
                            if pd.isna(value) or str(value).strip() == '':
                                return 'Unknown'
                            
                            value_str = str(value).strip()
                            placeholder_values = ['{media_id}', '{click_id}', '--', 'unknown', 'NaN']
                            if value_str in placeholder_values:
                                return 'Unknown'
                            
                            return value_str
                        
                        df['Source'] = df['Publisher Sub ID 1'].apply(clean_source_value)
                        logger_info("已添加Source字段，基于Publisher Sub ID 1字段（过滤占位符）")
                        source_found = True
                        
                    elif candidate_col == 'aff_sub':
                        # 过滤掉占位符值
                        def clean_source_value(value):
                            if pd.isna(value) or str(value).strip() == '':
                                return 'Unknown'
                            
                            value_str = str(value).strip()
                            placeholder_values = ['{media_id}', '{click_id}', '--', 'unknown', 'NaN']
                            if value_str in placeholder_values:
                                return 'Unknown'
                            
                            return value_str
                        
                        df['Source'] = df['aff_sub'].apply(clean_source_value)
                        logger_info("已添加Source字段，基于aff_sub字段（过滤占位符）")
                        source_found = True
                        
                    elif candidate_col == 'CLICK_URL':
                        # 尝试从CLICK_URL中提取实际的source信息
                        def extract_source_from_click_url(click_url):
                            """从CLICK_URL中提取source信息"""
                            if pd.isna(click_url) or str(click_url).strip() == '':
                                return 'Unknown'
                            
                            click_url_str = str(click_url).strip()
                            
                            # 如果CLICK_URL看起来像URL，尝试提取sub_id参数
                            if click_url_str.startswith('http'):
                                import re
                                sub_id_match = re.search(r'sub_id=([^&]+)', click_url_str)
                                if sub_id_match:
                                    sub_id = sub_id_match.group(1)
                                    # 解码URL编码的参数
                                    import urllib.parse
                                    try:
                                        decoded_sub_id = urllib.parse.unquote(sub_id)
                                        return decoded_sub_id
                                    except:
                                        return sub_id
                            else:
                                # 如果CLICK_URL不是URL，直接使用其值作为source
                                placeholder_values = ['{media_id}', '{click_id}', '--', 'unknown', 'NaN']
                                if click_url_str not in placeholder_values:
                                    return click_url_str
                            
                            return 'Unknown'
                        
                        df['Source'] = df['CLICK_URL'].apply(extract_source_from_click_url)
                        logger_info("已添加Source字段，从CLICK_URL中提取")
                        source_found = True
            
            # 如果没有找到任何可用的source列，使用默认值
            if not source_found:
                df['Source'] = 'AT_BM'  # 默认source
                logger_info("已添加Source字段，使用默认值: AT_BM")
        
        # 5. 应用mockup处理（如果需要）
        if INPUT_DATA_ENABLE_MOCKUP:
            df = self._apply_mockup_processing(df)
        
        # 6. 数据清洗和标准化
        df = self._clean_and_standardize_data(df)
        
        return df
    
    def _add_partner_classification(self, df):
        """添加Partner分类"""
        import config
        import re
        
        def classify_partner(source_value):
            """根据PARTNER_SOURCES_MAPPING将source分类到对应的Partner"""
            if pd.isna(source_value) or str(source_value).strip() == '':
                return 'Unknown'
            
            source_str = str(source_value).strip()
            
            # 跳过占位符值
            placeholder_values = ['{media_id}', '{click_id}', '--', 'unknown', 'NaN']
            if source_str in placeholder_values:
                return 'Unknown'
            
            # 先检查具体的Partner (排除ByteC的通配符匹配)
            for partner_name, partner_config in config.PARTNER_SOURCES_MAPPING.items():
                # 跳过ByteC，最后处理
                if partner_name == 'ByteC':
                    continue
                    
                pattern = partner_config.get('pattern', '')
                if pattern and re.match(pattern, source_str, re.IGNORECASE):
                    return partner_name
                    
                # 如果没有pattern，检查sources列表
                sources = partner_config.get('sources', [])
                for config_source in sources:
                    if config_source == 'ALL':  # 跳过通配符
                        continue
                    if source_str.upper().startswith(config_source.upper()):
                        return partner_name
            
            # 如果没有匹配到具体Partner，默认归类为ByteC
            return 'ByteC'
        
        # 尝试多个可能的source字段
        source_columns = ['Publisher Sub ID 1', 'aff_sub', 'sub1', 'aff_sub1']
        source_column = None
        
        for col in source_columns:
            if col in df.columns:
                # 检查是否有非占位符值
                non_placeholder_values = df[col].dropna()
                non_placeholder_values = non_placeholder_values[~non_placeholder_values.isin(['{media_id}', '{click_id}', '--', 'unknown', 'NaN'])]
                
                if len(non_placeholder_values) > 0:
                    source_column = col
                    break
        
        if source_column:
            df['Partner'] = df[source_column].apply(classify_partner)
            logger_info(f"使用 {source_column} 字段添加Partner分类，分布: {df['Partner'].value_counts().to_dict()}")
        else:
            # 如果没有找到有效的source字段，從文件名檢測平台
            detected_platform = self._detect_platform_from_filename()
            df['Partner'] = detected_platform
            logger_info(f"未找到有效的source字段，使用檢測到的平台: {detected_platform}")
        
        return df
    
    def _apply_mockup_processing(self, df):
        """应用mockup处理 - 根据Partner特定配置"""
        import config
        
        # 查找金额相关列
        amount_columns = [col for col in df.columns if 'amount' in col.lower() or 'payout' in col.lower()]
        
        # 检查是否有Partner列
        if 'Partner' in df.columns:
            # 按Partner分组处理
            for partner in df['Partner'].unique():
                if pd.isna(partner) or partner == '':
                    continue
                    
                # 获取Partner特定的mockup倍数
                mockup_multiplier = config.get_partner_mockup_multiplier(partner.upper())
                
                # 获取该Partner的数据
                partner_mask = df['Partner'] == partner
                partner_data = df[partner_mask]
                
                if len(partner_data) > 0:
                    logger_info(f"Partner '{partner}' 使用mockup倍数: {mockup_multiplier}")
                    
                    # 对金额列应用mockup处理
                    for col in amount_columns:
                        if col in df.columns and df[col].dtype in ['float64', 'int64']:
                            original_total = partner_data[col].sum()
                            df.loc[partner_mask, col] = partner_data[col] * mockup_multiplier
                            adjusted_total = df.loc[partner_mask, col].sum()
                            logger_info(f"Partner '{partner}' 列 '{col}': ${original_total:,.2f} → ${adjusted_total:,.2f} (倍数: {mockup_multiplier})")
        else:
            # 如果没有Partner列，使用默认倍数
            default_multiplier = getattr(config, 'MOCKUP_MULTIPLIER', 1.0)  # 改為默認不調整
            logger_info(f"未找到Partner列，使用默认mockup倍数: {default_multiplier}")
            
            for col in amount_columns:
                if col in df.columns and df[col].dtype in ['float64', 'int64']:
                    original_total = df[col].sum()
                    df[col] = df[col] * default_multiplier
                    adjusted_total = df[col].sum()
                    logger_info(f"列 '{col}': ${original_total:,.2f} → ${adjusted_total:,.2f} (倍数: {default_multiplier})")
        
        return df
    
    def _clean_and_standardize_data(self, df):
        """数据清洗和标准化"""
        # 1. 处理缺失值
        df = df.fillna('')
        
        # 2. 标准化日期列
        date_columns = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower()]
        for col in date_columns:
            if col in df.columns:
                try:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                except:
                    pass
        
        # 3. 标准化Partner/Source列
        if 'Partner' in df.columns:
            df['Partner'] = df['Partner'].str.upper()
        
        if 'Source' in df.columns:
            df['Source'] = df['Source'].str.upper()
        
        return df
    
    def save_to_excel(self, df, original_filename, passthrough=False):
        """保存到Excel文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 处理文件名，提取纯文件名（不包含路径）
        from pathlib import Path
        filename_path = Path(original_filename)
        filename_without_ext = filename_path.stem  # 只获取文件名，不包含扩展名和路径
        
        if passthrough:
            output_filename = f"Passthrough_{filename_without_ext}_{timestamp}.xlsx"
        else:
            output_filename = INPUT_DATA_OUTPUT_TEMPLATE.format(
                original_filename=filename_without_ext,
                timestamp=timestamp
            )
        
        output_path = self.output_dir / output_filename
        
        # 保存到Excel，指定工作表名称避免长产品名称问题
        # 清理数据中的Excel不兼容字符
        from utils.excel_character_cleaner import clean_for_excel
        df_cleaned = df.copy()
        
        # 处理日期时间列，移除时区信息
        for col in df_cleaned.columns:
            if df_cleaned[col].dtype == 'object':  # 只处理字符串列
                df_cleaned[col] = df_cleaned[col].apply(lambda x: clean_for_excel(x) if x is not None else x)
            elif 'datetime' in str(df_cleaned[col].dtype).lower():
                # 移除时区信息，避免Excel保存错误
                try:
                    if hasattr(df_cleaned[col].dt, 'tz_localize'):
                        df_cleaned[col] = df_cleaned[col].dt.tz_localize(None)
                    elif hasattr(df_cleaned[col].dt, 'tz_convert'):
                        df_cleaned[col] = df_cleaned[col].dt.tz_convert(None)
                except:
                    # 如果转换失败，尝试转换为字符串
                    df_cleaned[col] = df_cleaned[col].astype(str)
                    logger_warning(f"日期时间列 {col} 转换失败，已转为字符串格式")
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df_cleaned.to_excel(writer, sheet_name='Data', index=False)
        logger_info(f"数据已保存到: {output_path}")
        
        return output_path
    
    def insert_to_cloud_sql(self, df):
        """插入到Cloud SQL（参考api-agent到dmp-agent的逻辑）"""
        try:
            # 这里需要实现Cloud SQL插入逻辑
            # 参考api-agent和dmp-agent的实现
            logger_info("Cloud SQL插入功能待实现")
            return True
        except Exception as e:
            logger_error(f"Cloud SQL插入失败: {e}")
            return False
    
    def import_data(self, filename, passthrough=False):
        """导入数据的主函数"""
        try:
            # 設置當前文件名以供平台檢測
            self.current_filename = filename
            
            # 1. 读取文件（支持Excel和CSV）
            # 检查是否是完整路径
            if Path(filename).is_absolute() or '/' in filename or '\\' in filename:
                input_path = Path(filename)
            else:
                input_path = self.input_dir / filename
            
            if not input_path.exists():
                raise FileNotFoundError(f"文件不存在: {input_path}")
            
            logger_info(f"开始读取文件: {input_path}")
            
            # 根据文件扩展名选择读取方式
            file_extension = input_path.suffix.lower()
            if file_extension in ['.xlsx', '.xls']:
                df = pd.read_excel(input_path)
            elif file_extension == '.csv':
                # 尝试不同的编码格式
                encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'gbk']
                df = None
                for encoding in encodings:
                    try:
                        df = pd.read_csv(input_path, encoding=encoding)
                        logger_info(f"成功使用 {encoding} 编码读取CSV文件")
                        break
                    except (UnicodeDecodeError, UnicodeError):
                        continue
                
                if df is None:
                    raise ValueError("无法读取CSV文件，尝试了多种编码格式都失败")
            else:
                raise ValueError(f"不支持的文件格式: {file_extension}，支持的格式: .xlsx, .xls, .csv")
            
            logger_info(f"成功读取数据，共 {len(df)} 行，{len(df.columns)} 列")
            
            # 2. 数据分析
            if INPUT_DATA_ENABLE_PANDASAI_ANALYSIS:
                analysis = self.analyze_data_with_pandasai(df)
                # logger_info("数据分析结果:")
                # for key, value in analysis.items():
                #     if isinstance(value, dict):
                #         logger_info(f"  {key}: {len(value)} 项")
                #     else:
                #         logger_info(f"  {key}: {value}")
            
            # 3. 数据处理
            processed_df = self.process_data(df)
            
            # 4. 保存处理后的数据
            output_path = self.save_to_excel(processed_df, filename, passthrough)
            
            # 5. 如果不是passthrough模式，插入到Cloud SQL
            if not passthrough:
                success = self.insert_to_cloud_sql(processed_df)
                if success:
                    logger_info("数据已成功插入Cloud SQL")
                else:
                    logger_warning("Cloud SQL插入失败，但Excel文件已保存")
            
            logger_info("数据导入处理完成")
            return output_path
            
        except Exception as e:
            logger_error(f"数据导入失败: {e}")
            raise


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="电商转化数据导入处理器")
    parser.add_argument("--import", dest="import_file", required=True, 
                       help="要导入的Excel文件名")
    parser.add_argument("--passthrough", action="store_true",
                       help="不插入Cloud SQL，直接输出Excel")
    
    args = parser.parse_args()
    
    try:
        importer = DataImporter()
        output_path = importer.import_data(args.import_file, args.passthrough)
        print(f"✅ 处理完成，输出文件: {output_path}")
        
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 