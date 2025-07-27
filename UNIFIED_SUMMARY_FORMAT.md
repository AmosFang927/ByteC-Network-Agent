# 统一Summary格式文档

## 概述

为了确保邮件和报表的Summary格式一致，我们创建了统一的Summary格式化器。该格式化器提供了一致的格式，包括状态统计、金额计算和来源信息。

## 格式规范

### 标准Summary格式

```
Partner: DeepLeaper
Date Range: 2025-07-27 至 2025-07-27
Total Conversions (All Status): 6 条
✅ Total Conversions (Pending/Approved): 4 条
✅ Total Sale Amount (USD) (Pending/Approved): $750.00
⚠️ Total Conversions (Invalid/Rejected): 2 条
⚠️ Total Sale Amount (USD) (Invalid/Rejected): $125.00
Sources: source1, source2, source3, source4
```

### 状态分类

- **有效状态**: `pending`, `approved` - 显示为绿色✅
- **无效状态**: `invalid`, `rejected`, `cancelled`, `canceled`, `failed`, `decline` - 显示为红色⚠️

## 使用方法

### 1. 基本使用

```python
from shared.utils.summary_formatter import generate_unified_summary

# 生成统一Summary
summary = generate_unified_summary(
    partner_name="DeepLeaper",
    start_date="2025-07-27",
    end_date="2025-07-27",
    df=df,  # 可选：pandas DataFrame
    total_records=100,  # 备用：总记录数
    total_amount=1000.0,  # 备用：总金额
    sources=["source1", "source2"]  # 来源列表
)
```

### 2. 显示格式

```python
from shared.utils.summary_formatter import format_summary_for_display

# 格式化为显示文本
display_text = format_summary_for_display(summary)
print(display_text)
```

### 3. 邮件格式

```python
from shared.utils.summary_formatter import format_summary_for_email

# 格式化为邮件模板变量
email_vars = format_summary_for_email(summary)
```

## 返回的Summary字典结构

```python
{
    'partner_name': 'DeepLeaper',
    'date_range': '2025-07-27 至 2025-07-27',
    'total_all_conversions': 6,
    'pending_approved_count': 4,
    'pending_approved_amount': '$750.00',
    'pending_approved_amount_numeric': 750.0,
    'invalid_rejected_count': 2,
    'invalid_rejected_amount': '$125.00',
    'invalid_rejected_amount_numeric': 125.0,
    'sources_list': 'source1, source2, source3, source4',
    'sources': ['source1', 'source2', 'source3', 'source4'],
    'sources_count': 4,
    'total_records': 4,  # 兼容性字段：有效记录数
    'total_amount': 750.0,  # 兼容性字段：有效金额
    'total_amount_formatted': '$750.00'  # 兼容性字段：格式化金额
}
```

## 集成到现有系统

### 1. 邮件发送器

邮件发送器已更新为使用统一Summary格式化器：

- `agents/data_output_agent/email_sender.py` 中的 `_prepare_partner_email_data` 方法
- 使用 `generate_unified_summary` 生成统一格式
- 邮件模板变量自动替换

### 2. 报表生成器

报表生成器已更新为使用统一Summary格式化器：

- `agents/reporter_agent/core/report_generator.py` 中的 `_add_summary_header` 方法
- Excel文件中的Summary部分使用统一格式
- 保持与邮件格式一致

### 3. 邮件模板

邮件模板已更新为使用统一格式：

- `templates/email_template.html` 使用 `{{date_range}}` 变量
- 金额格式统一为 `{{pending_approved_amount}}` 和 `{{invalid_rejected_amount}}`
- 移除了重复的美元符号

## 错误处理

统一Summary格式化器包含完善的错误处理：

1. **DataFrame读取失败**: 使用备用数据
2. **状态列缺失**: 使用备用统计
3. **金额解析失败**: 返回默认值
4. **异常情况**: 返回安全的默认Summary

## 测试

运行测试脚本验证功能：

```bash
python test_unified_summary.py
```

## 优势

1. **格式一致性**: 邮件和报表使用相同的Summary格式
2. **状态统计准确**: 统一的状态分类逻辑
3. **金额计算精确**: 统一的货币解析和格式化
4. **错误处理完善**: 多种异常情况的处理
5. **向后兼容**: 保持与现有系统的兼容性
6. **易于维护**: 集中化的Summary生成逻辑

## 更新日志

- **2025-07-27**: 创建统一Summary格式化器
- 更新邮件发送器和报表生成器
- 统一邮件模板格式
- 添加完整的错误处理
- 创建测试脚本和文档 