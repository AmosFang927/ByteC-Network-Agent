#!/usr/bin/env python3
"""
测试修复后的AT_BM处理器
"""

import sys
import os
import asyncio

# 添加项目路径
sys.path.append('/Users/amosfang/ByteC-Network-Agent-main')

async def test_fixed_at_bm_processor():
    """测试修复后的AT_BM处理器"""
    
    print("🧪 测试修复后的AT_BM处理器")
    print()
    
    try:
        from agents.data_dmp_agent.at_bm_data_processor import ATBMDataProcessor
        
        # 初始化处理器
        processor = ATBMDataProcessor()
        
        # 测试文件
        file_path = 'input/ID-async-report-exporter-publisher_conversion-report-id-2025-08-12-18nRimTm4Z1hBMXZ_0805-0810_DeepLeaper_AT_BM.csv'
        
        print(f"📁 测试文件: {file_path}")
        
        # 使用处理器处理文件
        result = processor.process_at_bm_file(file_path)
        
        if result.get('success'):
            print("✅ AT_BM处理成功!")
            print(f"📊 处理记录数: {result.get('records_count', 0)}")
            
            # 检查输出文件
            output_file = result.get('output_file')
            if output_file and os.path.exists(output_file):
                print(f"📁 输出文件: {output_file}")
                
                # 读取输出文件验证结果
                import pandas as pd
                output_df = pd.read_csv(output_file, encoding='utf-8-sig')
                
                print(f"📊 输出数据: {len(output_df)} 行，{len(output_df.columns)} 列")
                
                # 检查关键字段
                if 'Local Sale Amount' in output_df.columns:
                    local_sale_total = output_df['Local Sale Amount'].sum()
                    print(f"💰 Local Sale Amount总和: {local_sale_total:,.0f} IDR")
                    
                    # 货币转换
                    usd_amount = local_sale_total / 15400
                    adjusted_usd = usd_amount * 0.7
                    print(f"💱 USD转换: ${usd_amount:,.2f}")
                    print(f"🔧 DeepLeaper调整: ${adjusted_usd:,.2f}")
                    
                    if local_sale_total > 5000000000:  # 大于50亿IDR
                        print("✅ 修复成功！获得了正确的销售金额")
                    else:
                        print("❌ 销售金额仍然不正确")
                
                # 显示前几行
                print(f"\n📋 输出数据前3行:")
                print(output_df.head(3).to_string())
                
            else:
                print("❌ 未找到输出文件")
        else:
            print(f"❌ AT_BM处理失败: {result.get('error', 'Unknown error')}")
        
        return result
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    asyncio.run(test_fixed_at_bm_processor())

