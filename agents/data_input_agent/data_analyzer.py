#!/usr/bin/env python3
"""
专门的数据分析器 - 不依赖pandasai
提供详细的数据分析和总结报告
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import json
import os


class DataAnalyzer:
    """高级数据分析器"""
    
    def __init__(self):
        self.analysis_results = {}
    
    def analyze_dataframe(self, df, filename="unknown"):
        """对DataFrame进行全面分析"""
        print(f"\n🔍 开始分析文件: {filename}")
        print("=" * 60)
        
        # 基础统计
        basic_stats = self._basic_statistics(df)
        
        # 数据质量分析
        quality_analysis = self._data_quality_analysis(df)
        
        # 列类型分析
        column_analysis = self._column_type_analysis(df)
        
        # 业务相关分析
        business_analysis = self._business_specific_analysis(df)
        
        # 生成完整报告
        full_report = {
            "文件信息": {
                "文件名": filename,
                "分析时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "数据规模": f"{len(df)} 行 × {len(df.columns)} 列"
            },
            "基础统计": basic_stats,
            "数据质量": quality_analysis,
            "列分析": column_analysis,
            "业务分析": business_analysis
        }
        
        self.analysis_results = full_report
        return full_report
    
    def _basic_statistics(self, df):
        """基础统计信息"""
        return {
            "总记录数": len(df),
            "总列数": len(df.columns),
            "内存使用": f"{df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB",
            "数值列数量": len(df.select_dtypes(include=[np.number]).columns),
            "文本列数量": len(df.select_dtypes(include=['object']).columns),
            "日期列数量": len(df.select_dtypes(include=['datetime64']).columns),
            "列名列表": list(df.columns)
        }
    
    def _data_quality_analysis(self, df):
        """数据质量分析"""
        missing_data = df.isnull().sum()
        duplicate_rows = df.duplicated().sum()
        
        quality_score = 100
        if len(df) > 0:
            quality_score -= (missing_data.sum() / (len(df) * len(df.columns))) * 30
            quality_score -= (duplicate_rows / len(df)) * 20
        
        return {
            "数据质量评分": f"{max(0, quality_score):.1f}/100",
            "缺失值统计": {
                "总缺失值": int(missing_data.sum()),
                "缺失值比例": f"{(missing_data.sum() / (len(df) * len(df.columns)) * 100):.2f}%",
                "缺失值最多的列": {
                    col: int(missing_data[col]) 
                    for col in missing_data.nlargest(5).index 
                    if missing_data[col] > 0
                }
            },
            "重复数据": {
                "重复行数": int(duplicate_rows),
                "重复率": f"{(duplicate_rows / len(df) * 100):.2f}%" if len(df) > 0 else "0%"
            },
            "数据完整性": {
                col: f"{((len(df) - missing_data[col]) / len(df) * 100):.1f}%" 
                for col in df.columns
            }
        }
    
    def _column_type_analysis(self, df):
        """列类型和分布分析"""
        column_analysis = {}
        
        for col in df.columns:
            dtype = str(df[col].dtype)
            unique_count = df[col].nunique()
            null_count = df[col].isnull().sum()
            
            analysis = {
                "数据类型": dtype,
                "唯一值数量": int(unique_count),
                "空值数量": int(null_count),
                "空值比例": f"{(null_count / len(df) * 100):.2f}%" if len(df) > 0 else "0%"
            }
            
            # 数值列的特殊分析
            if df[col].dtype in ['int64', 'float64']:
                if not df[col].isnull().all():
                    stats = df[col].describe()
                    analysis.update({
                        "最小值": float(stats['min']) if not pd.isna(stats['min']) else None,
                        "最大值": float(stats['max']) if not pd.isna(stats['max']) else None,
                        "平均值": float(stats['mean']) if not pd.isna(stats['mean']) else None,
                        "中位数": float(stats['50%']) if not pd.isna(stats['50%']) else None,
                        "标准差": float(stats['std']) if not pd.isna(stats['std']) else None
                    })
            
            # 文本列的特殊分析
            elif df[col].dtype == 'object':
                non_null = df[col].dropna()
                if len(non_null) > 0:
                    analysis.update({
                        "最常见值": str(non_null.value_counts().index[0]) if len(non_null) > 0 else None,
                        "最常见值频次": int(non_null.value_counts().iloc[0]) if len(non_null) > 0 else 0,
                        "平均长度": f"{non_null.astype(str).str.len().mean():.1f}",
                        "最长文本长度": int(non_null.astype(str).str.len().max()) if len(non_null) > 0 else 0
                    })
                    
                    # 显示前5个最常见的值
                    top_values = non_null.value_counts().head(5)
                    analysis["前5个最常见值"] = {
                        str(k): int(v) for k, v in top_values.items()
                    }
            
            column_analysis[col] = analysis
        
        return column_analysis
    
    def _business_specific_analysis(self, df):
        """业务相关分析"""
        business_insights = {
            "数据特征": {},
            "转化分析": {},
            "合作伙伴分析": {},
            "时间趋势": {}
        }
        
        # 转化相关分析
        if 'Status' in df.columns:
            status_dist = df['Status'].value_counts()
            business_insights["转化分析"]["状态分布"] = {
                str(k): int(v) for k, v in status_dist.items()
            }
            
            if 'approved' in status_dist.index:
                approval_rate = status_dist.get('approved', 0) / len(df) * 100
                business_insights["转化分析"]["批准率"] = f"{approval_rate:.2f}%"
        
        # 合作伙伴分析
        if 'Partner' in df.columns:
            partner_dist = df['Partner'].value_counts()
            business_insights["合作伙伴分析"]["合作伙伴分布"] = {
                str(k): int(v) for k, v in partner_dist.head(10).items()
            }
        
        # 金额分析
        amount_columns = [col for col in df.columns if 'amount' in col.lower() or 'payout' in col.lower()]
        if amount_columns:
            business_insights["金额分析"] = {}
            for col in amount_columns:
                if df[col].dtype in ['int64', 'float64']:
                    non_null = df[col].dropna()
                    if len(non_null) > 0:
                        business_insights["金额分析"][col] = {
                            "总金额": f"{non_null.sum():.2f}",
                            "平均金额": f"{non_null.mean():.2f}",
                            "最大单笔": f"{non_null.max():.2f}",
                            "最小单笔": f"{non_null.min():.2f}"
                        }
        
        # 时间趋势分析
        date_columns = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower()]
        if date_columns:
            business_insights["时间趋势"]["日期列"] = date_columns
            
            for col in date_columns:
                if df[col].dtype == 'object':
                    # 尝试转换为日期
                    try:
                        df[col] = pd.to_datetime(df[col], errors='coerce')
                    except:
                        continue
                
                if 'datetime' in str(df[col].dtype):
                    non_null_dates = df[col].dropna()
                    if len(non_null_dates) > 0:
                        business_insights["时间趋势"][f"{col}_分析"] = {
                            "最早日期": str(non_null_dates.min().date()),
                            "最晚日期": str(non_null_dates.max().date()),
                            "时间跨度": str((non_null_dates.max() - non_null_dates.min()).days) + " 天"
                        }
        
        return business_insights
    
    def print_analysis_report(self):
        """打印详细的分析报告"""
        if not self.analysis_results:
            print("❌ 没有分析结果可显示")
            return
        
        results = self.analysis_results
        
        print("\n📊 详细数据分析报告")
        print("=" * 80)
        
        # 文件信息
        print(f"\n📁 文件信息:")
        for key, value in results["文件信息"].items():
            print(f"  • {key}: {value}")
        
        # 基础统计
        print(f"\n📈 基础统计:")
        for key, value in results["基础统计"].items():
            if key != "列名列表":
                print(f"  • {key}: {value}")
        
        # 数据质量
        print(f"\n🎯 数据质量评估:")
        quality = results["数据质量"]
        print(f"  • 总体质量评分: {quality['数据质量评分']}")
        print(f"  • 缺失值情况: {quality['缺失值统计']['总缺失值']} 个 ({quality['缺失值统计']['缺失值比例']})")
        print(f"  • 重复数据: {quality['重复数据']['重复行数']} 行 ({quality['重复数据']['重复率']})")
        
        if quality['缺失值统计']['缺失值最多的列']:
            print(f"  • 缺失值最多的列:")
            for col, count in quality['缺失值统计']['缺失值最多的列'].items():
                print(f"    - {col}: {count} 个")
        
        # 业务分析
        print(f"\n💼 业务分析:")
        business = results["业务分析"]
        
        if "转化分析" in business and business["转化分析"]:
            print(f"  📋 转化状态分布:")
            if "状态分布" in business["转化分析"]:
                for status, count in business["转化分析"]["状态分布"].items():
                    print(f"    - {status}: {count} 条")
            if "批准率" in business["转化分析"]:
                print(f"    - 批准率: {business['转化分析']['批准率']}")
        
        if "合作伙伴分析" in business and business["合作伙伴分析"]:
            print(f"  🤝 合作伙伴分布:")
            if "合作伙伴分布" in business["合作伙伴分析"]:
                for partner, count in business["合作伙伴分析"]["合作伙伴分布"].items():
                    print(f"    - {partner}: {count} 条")
        
        if "金额分析" in business and business["金额分析"]:
            print(f"  💰 金额统计:")
            for col, stats in business["金额分析"].items():
                print(f"    - {col}:")
                for stat_name, stat_value in stats.items():
                    print(f"      • {stat_name}: {stat_value}")
        
        if "时间趋势" in business and business["时间趋势"]:
            print(f"  📅 时间分析:")
            for key, value in business["时间趋势"].items():
                if key != "日期列":
                    print(f"    - {key}: {value}")
        
        # 关键列分析
        # print(f"\n🔍 关键列详细分析:")
        # columns = results["列分析"]
        # important_columns = [col for col in columns.keys() 
        #                    if any(keyword in col.lower() 
        #                         for keyword in ['id', 'amount', 'status', 'partner', 'date'])]
        # 
        # for col in important_columns[:10]:  # 只显示前10个重要列
        #     analysis = columns[col]
        #     print(f"  📋 {col}:")
        #     print(f"    • 类型: {analysis['数据类型']}")
        #     print(f"    • 唯一值: {analysis['唯一值数量']}")
        #     print(f"    • 完整度: {(100 - float(analysis['空值比例'].replace('%', ''))):.1f}%")
        #     
        #     if '最常见值' in analysis:
        #         print(f"    • 最常见值: {analysis['最常见值']} (出现 {analysis['最常见值频次']} 次)")
        #     
        #     if '平均值' in analysis and analysis['平均值'] is not None:
        #         print(f"    • 平均值: {analysis['平均值']:.2f}")
        #         print(f"    • 范围: {analysis['最小值']:.2f} ~ {analysis['最大值']:.2f}")
        
        # print("\n" + "=" * 80)
        # print("✅ 分析报告完成")
    
    def save_analysis_to_file(self, output_dir="output"):
        """保存分析结果到文件"""
        if not self.analysis_results:
            print("❌ 没有分析结果可保存")
            return None
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data_analysis_report_{timestamp}.json"
        filepath = output_path / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.analysis_results, f, ensure_ascii=False, indent=2)
        
        # print(f"📄 分析报告已保存到: {filepath}")
        return filepath


def analyze_csv_file(filepath):
    """分析CSV文件的便捷函数"""
    analyzer = DataAnalyzer()
    
    # 读取文件
    if filepath.endswith('.csv'):
        df = pd.read_csv(filepath, encoding='utf-8')
    elif filepath.endswith(('.xlsx', '.xls')):
        df = pd.read_excel(filepath)
    else:
        raise ValueError("不支持的文件格式")
    
    # 分析
    filename = Path(filepath).name
    analyzer.analyze_dataframe(df, filename)
    
    # 显示报告
    analyzer.print_analysis_report()
    
    # 保存报告
    analyzer.save_analysis_to_file()
    
    return analyzer


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        try:
            analyze_csv_file(filepath)
        except Exception as e:
            print(f"❌ 分析失败: {e}")
    else:
        print("用法: python data_analyzer.py <文件路径>") 