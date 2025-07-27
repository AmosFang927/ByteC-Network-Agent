# Data Input Agent - 电商转化数据导入处理器

## 功能概述

Data Input Agent 是一个专门用于处理电商转化数据Excel文件的导入工具。它支持数据读取、分析、处理和输出，可以自动移除不需要的列，应用数据处理逻辑，并输出处理后的Excel文件。

## 主要功能

1. **Excel文件读取** - 支持读取Excel格式的转化数据
2. **pandasai数据分析** - 使用AI分析数据特点和统计信息
3. **数据清洗处理** - 移除指定列，应用mockup处理，标准化数据
4. **多种输出模式** - 支持直接输出Excel或插入Cloud SQL

## 使用方法

### 基本用法

```bash
# 导入数据并插入Cloud SQL
python agents/data_input_agent/data_importer.py --import sample_conversion_data.xlsx

# 导入数据但只输出Excel（passthrough模式）
python agents/data_input_agent/data_importer.py --import sample_conversion_data.xlsx --passthrough
```

### 参数说明

- `--import {filename}` - 指定要导入的Excel文件名（必需）
- `--passthrough` - 启用passthrough模式，不插入Cloud SQL，只输出Excel文件

## 文件结构

```
agents/data_input_agent/
├── __init__.py              # 模块初始化文件
├── data_importer.py         # 主要的数据导入处理器
├── create_sample_data.py    # 创建示例数据的脚本
└── README.md               # 使用说明文档

input/                      # 输入文件目录
├── sample_conversion_data.xlsx  # 示例数据文件

output/                     # 输出文件目录
├── Processed_*.xlsx        # 处理后的数据文件
└── Passthrough_*.xlsx      # passthrough模式的输出文件
```

## 配置项

在 `config.py` 中可以配置以下参数：

### 数据移除配置
```python
INPUT_DATA_REMOVE_COLUMNS = [
    "Click ID",
    "Click Date", 
    "Recorded On",
    # ... 更多要移除的列
]
```

### 处理配置
```python
INPUT_DATA_ENABLE_PANDASAI_ANALYSIS = True  # 是否启用pandasai分析
INPUT_DATA_ENABLE_MOCKUP = True             # 是否启用mockup处理
INPUT_DATA_MOCKUP_MULTIPLIER = 0.9         # mockup倍数
```

### 文件配置
```python
INPUT_DATA_DIR = "input"                    # 输入目录
INPUT_DATA_OUTPUT_DIR = "output"           # 输出目录
INPUT_DATA_OUTPUT_TEMPLATE = "Processed_{original_filename}_{timestamp}.xlsx"
```

## 数据处理逻辑

### 1. 列移除
根据配置的 `INPUT_DATA_REMOVE_COLUMNS` 列表，自动移除不需要的列。

### 2. Mockup处理
对金额相关列（包含'amount'或'payout'的列）应用配置的倍数处理。

### 3. 数据清洗
- 处理缺失值
- 标准化日期列
- 标准化Partner/Source列（转为大写）

### 4. 数据分析
使用pandasai进行智能数据分析，提供数据统计和特点分析。

## 示例

### 创建示例数据
```bash
python agents/data_input_agent/create_sample_data.py
```

### 处理数据
```bash
# 正常模式
python agents/data_input_agent/data_importer.py --import sample_conversion_data.xlsx

# Passthrough模式
python agents/data_input_agent/data_importer.py --import sample_conversion_data.xlsx --passthrough
```

## 输出文件

### 正常模式
- 文件名格式：`Processed_{原文件名}_{时间戳}.xlsx`
- 位置：`output/` 目录
- 内容：处理后的数据 + 插入Cloud SQL

### Passthrough模式
- 文件名格式：`Passthrough_{原文件名}_{时间戳}.xlsx`
- 位置：`output/` 目录
- 内容：仅处理后的数据，不插入Cloud SQL

## 依赖项

- pandas
- openpyxl
- numpy
- pandasai (可选，用于AI数据分析)

## 注意事项

1. 确保输入文件放在 `input/` 目录下
2. 输出文件会自动保存到 `output/` 目录
3. Cloud SQL插入功能需要根据实际环境配置
4. pandasai功能需要配置OpenAI API key才能使用AI分析

## 扩展功能

- Cloud SQL插入逻辑需要参考api-agent和dmp-agent的实现
- 可以添加更多的数据处理规则
- 可以扩展支持更多的文件格式 