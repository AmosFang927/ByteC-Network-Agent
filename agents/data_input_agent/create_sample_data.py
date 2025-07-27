#!/usr/bin/env python3
"""
创建示例数据文件用于测试
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

def create_sample_data():
    """创建示例数据"""
    # 创建示例数据
    np.random.seed(42)
    n_records = 100
    
    # 生成日期范围
    start_date = datetime.now() - timedelta(days=30)
    dates = [start_date + timedelta(days=i) for i in range(n_records)]
    
    # 创建示例数据
    data = {
        'Click ID': [f'CLICK_{i:06d}' for i in range(n_records)],
        'Click Date': dates,
        'Recorded On': dates,
        'Click to Conversion Time': np.random.randint(1, 1440, n_records),
        'Website/Property': ['Shopee', 'TikTok', 'Lazada'] * (n_records // 3) + ['Shopee'] * (n_records % 3),
        'Campaign Name': [f'Campaign_{i}' for i in range(n_records)],
        'Sale Amount (Conversion Currency)': np.random.uniform(10, 1000, n_records),
        'Estimated Earnings (USD)': np.random.uniform(1, 100, n_records),
        'Invoice No': [f'INV_{i:06d}' for i in range(n_records)],
        'general.Base Payout': np.random.uniform(0.5, 50, n_records),
        'general.Bonus Payout': np.random.uniform(0, 10, n_records),
        'Remarks': ['Good', 'Excellent', 'Average'] * (n_records // 3) + ['Good'] * (n_records % 3),
        'Click Origin Country': ['ID', 'MY', 'TH', 'PH', 'VN'] * (n_records // 5) + ['ID'] * (n_records % 5),
        'Device Type': ['Mobile', 'Desktop', 'Tablet'] * (n_records // 3) + ['Mobile'] * (n_records % 3),
        'Source': ['RAMPUP', 'DeepLeaper', 'ByteC'] * (n_records // 3) + ['RAMPUP'] * (n_records % 3),
        'Browser': ['Chrome', 'Safari', 'Firefox'] * (n_records // 3) + ['Chrome'] * (n_records % 3),
        'Ref URL': [f'https://example.com/ref_{i}' for i in range(n_records)],
        'User Agent': [f'Mozilla/5.0 (compatible; TestBot/{i})' for i in range(n_records)],
        
        # 保留的列
        'Partner': ['RAMPUP', 'DeepLeaper', 'ByteC'] * (n_records // 3) + ['RAMPUP'] * (n_records % 3),
        'Offer Name': ['Shopee ID (Media Buyers) - CPS', 'TikTok Shop ID - CPS'] * (n_records // 2) + ['Shopee ID (Media Buyers) - CPS'] * (n_records % 2),
        'Conversion ID': [f'CONV_{i:06d}' for i in range(n_records)],
        'Conversion Date': dates,
        'Status': ['approved', 'pending', 'rejected'] * (n_records // 3) + ['approved'] * (n_records % 3),
        'Sale Amount': np.random.uniform(10, 1000, n_records),
        'Currency': ['USD', 'IDR', 'MYR'] * (n_records // 3) + ['USD'] * (n_records % 3),
        'Platform': ['involve_asia'] * n_records
    }
    
    df = pd.DataFrame(data)
    return df

def main():
    """主函数"""
    # 确保input目录存在
    input_dir = Path("input")
    input_dir.mkdir(exist_ok=True)
    
    # 创建示例数据
    df = create_sample_data()
    
    # 保存到Excel文件
    output_file = input_dir / "sample_conversion_data.xlsx"
    df.to_excel(output_file, index=False, engine='openpyxl')
    
    print(f"✅ 示例数据已创建: {output_file}")
    print(f"📊 数据统计:")
    print(f"  - 记录数: {len(df)}")
    print(f"  - 列数: {len(df.columns)}")
    print(f"  - 列名: {list(df.columns)}")

if __name__ == "__main__":
    main() 