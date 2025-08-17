#!/usr/bin/env python3
"""
直接测试LeadsADN数据处理器
"""

import sys
import os
sys.path.append('.')

from agents.data_dmp_agent.leads_adn_data_processor import LeadsADNDataProcessor
import pandas as pd

def main():
    # 读取数据
    file_path = 'input/ConversionReportd32c74e604ba3649_20250816_leads_adn.csv'
    df = pd.read_csv(file_path, encoding='utf-8-sig')
    print(f'✅ 读取数据: {len(df)} 行, {len(df.columns)} 列')
    
    # 显示前几行数据来验证
    print(f'📊 字段列表: {list(df.columns)}')
    print(f'📄 前3行数据:')
    print(df.head(3)[['Conv. Time', 'Affiliate', 'Advertiser', 'Revenue', 'Cost', 'Conv. Status']])
    
    # 处理数据
    processor = LeadsADNDataProcessor()
    processed_df, info = processor.process_data(df, file_path)
    print(f'✅ 处理完成: {len(processed_df)} 行, {len(processed_df.columns)} 列')
    
    # 检查关键字段
    key_fields = ['Partner', 'USD Sale Amount', 'Advertiser', 'Conversion ID', 'Status']
    for field in key_fields:
        if field in processed_df.columns:
            print(f'✅ {field}: 存在')
        else:
            print(f'❌ {field}: 缺失')
    
    # 检查Partner提取
    if 'Partner' in processed_df.columns:
        partner_counts = processed_df['Partner'].value_counts()
        print(f'📊 Partner分布: {partner_counts.to_dict()}')
    
    # 检查金额
    if 'USD Sale Amount' in processed_df.columns:
        total_amount = processed_df['USD Sale Amount'].sum()
        print(f'💰 总金额: ${total_amount:.6f}')
        print(f'💰 前5条记录的金额: {processed_df["USD Sale Amount"].head().tolist()}')
    
    # 保存测试结果
    output_path = 'output/test_leadsamdn_direct_output.xlsx'
    os.makedirs('output', exist_ok=True)
    processed_df.to_excel(output_path, index=False)
    print(f'💾 结果已保存到: {output_path}')

if __name__ == "__main__":
    main()
