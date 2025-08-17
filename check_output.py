#!/usr/bin/env python3
import pandas as pd

df = pd.read_excel('output/test_leadsamdn_direct_output.xlsx')
print(f'📊 输出文件包含 {len(df)} 行, {len(df.columns)} 列')
print(f'📝 统一字段: {list(df.columns)}')
print(f'📊 Partner分布: {df["Partner"].value_counts().to_dict()}')
print(f'💰 总金额: ${df["USD Sale Amount"].sum():.6f}')
print(f'🎯 状态分布: {df["Status"].value_counts().to_dict()}')

# 检查reporter_agent兼容性
reporter_fields = ['USD Sale Amount', 'Advertiser', 'Conversion ID', 'Status', 'Partner', 'Datetime Conversion']
for field in reporter_fields:
    if field in df.columns:
        print(f'✅ {field}: 存在')
    else:
        print(f'❌ {field}: 缺失')