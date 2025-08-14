#!/usr/bin/env python3
import pandas as pd

# 分析第二个文件
file_path = 'output/Passthrough_all_00010101000000_00010101000000_395162191all_00010101000000_00010101000000_395162191_LS_BM_20250812_084805.xlsx'
df = pd.read_excel(file_path, sheet_name='Data')
print(f'文件: {file_path}')
print(f'数据行数: {len(df)}')
print(f'USD Sale Amount总和: ${df["USD Sale Amount"].sum():,.2f}')
print(f'Partner分布:')
print(df['Partner'].value_counts())
print(f'Status分布:')
print(df['Status'].value_counts())
