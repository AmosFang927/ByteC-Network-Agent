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
        self.ensure_directories()
        
    def ensure_directories(self):
        """确保必要的目录存在"""
        self.input_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
        
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
        
        # 2. 应用mockup处理（如果需要）
        if INPUT_DATA_ENABLE_MOCKUP:
            df = self._apply_mockup_processing(df)
        
        # 3. 数据清洗和标准化
        df = self._clean_and_standardize_data(df)
        
        return df
    
    def _apply_mockup_processing(self, df):
        """应用mockup处理"""
        # 查找金额相关列
        amount_columns = [col for col in df.columns if 'amount' in col.lower() or 'payout' in col.lower()]
        
        for col in amount_columns:
            if col in df.columns and df[col].dtype in ['float64', 'int64']:
                df[col] = df[col] * INPUT_DATA_MOCKUP_MULTIPLIER
                logger_info(f"已对列 '{col}' 应用mockup处理 (倍数: {INPUT_DATA_MOCKUP_MULTIPLIER})")
        
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
        for col in df_cleaned.columns:
            if df_cleaned[col].dtype == 'object':  # 只处理字符串列
                df_cleaned[col] = df_cleaned[col].apply(lambda x: clean_for_excel(x) if x is not None else x)
        
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
            # 1. 读取文件（支持Excel和CSV）
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