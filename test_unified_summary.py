#!/usr/bin/env python3
"""
测试统一Summary格式化器
"""

import pandas as pd
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from shared.utils.summary_formatter import generate_unified_summary, format_summary_for_display, format_summary_for_email

def test_unified_summary():
    """测试统一Summary格式化器"""
    print("🧪 测试统一Summary格式化器")
    print("=" * 60)
    
    # 创建测试数据
    test_data = {
        'Status': ['pending', 'approved', 'invalid', 'rejected', 'pending', 'approved'],
        'USD Sale Amount': [100.0, 200.0, 50.0, 75.0, 150.0, 300.0],
        'Source': ['source1', 'source2', 'source3', 'source4', 'source1', 'source2']
    }
    
    df = pd.DataFrame(test_data)
    
    print("📊 测试数据:")
    print(df)
    print()
    
    # 测试生成统一Summary
    summary = generate_unified_summary(
        partner_name="DeepLeaper",
        start_date="2025-07-27",
        end_date="2025-07-27",
        df=df,
        sources=["source1", "source2", "source3", "source4"]
    )
    
    print("✅ 生成的统一Summary:")
    for key, value in summary.items():
        print(f"   {key}: {value}")
    print()
    
    # 测试显示格式
    display_text = format_summary_for_display(summary)
    print("📋 显示格式:")
    print(display_text)
    print()
    
    # 测试邮件格式
    email_vars = format_summary_for_email(summary)
    print("📧 邮件模板变量:")
    for key, value in email_vars.items():
        print(f"   {key}: {value}")
    print()
    
    # 测试无数据情况
    print("🔄 测试无数据情况:")
    empty_summary = generate_unified_summary(
        partner_name="TestPartner",
        start_date="2025-07-27",
        end_date="2025-07-27",
        df=None,
        total_records=0,
        total_amount=0.0,
        sources=[]
    )
    
    empty_display = format_summary_for_display(empty_summary)
    print(empty_display)
    print()
    
    print("✅ 测试完成!")

if __name__ == "__main__":
    test_unified_summary() 