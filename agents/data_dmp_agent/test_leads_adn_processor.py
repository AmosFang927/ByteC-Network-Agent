#!/usr/bin/env python3
"""
LeadsADN数据处理器测试脚本
用于测试LeadsADN平台数据处理功能
"""

import sys
import os
import pandas as pd
from datetime import datetime
import json

# 添加路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

def create_sample_leads_adn_data():
    """创建示例LeadsADN数据"""
    sample_data = {
        'Transaction ID': ['TXN001', 'TXN002', 'TXN003', 'TXN004'],
        'Merchant': ['MerchantA', 'MerchantB', 'MerchantA', 'MerchantC'],
        'Conversion Time': [
            '2024-01-15 10:30:00',
            '2024-01-15 11:45:00', 
            '2024-01-15 14:20:00',
            '2024-01-15 16:10:00'
        ],
        'Sale Amount': [150.00, 250.50, 89.99, 320.75],
        'Commission': [15.00, 25.05, 8.99, 32.08],
        'Status': ['Approved', 'Pending', 'Approved', 'Rejected'],
        'Affiliate': ['(3)FTK', '(1)ByteC', '(3)FTK', '(2)MP'],
        'Sub ID 1': ['sub001', 'sub002', 'sub003', 'sub004'],
        'Sub ID 2': ['', 'extra001', '', 'extra002'],
        'Category': ['Electronics', 'Clothing', 'Electronics', 'Books'],
        'Product ID': ['PROD001', 'PROD002', 'PROD003', 'PROD004'],
        'Product': ['Smartphone', 'T-Shirt', 'Headphones', 'Novel'],
        'Campaign': ['Winter Sale', 'Summer Collection', 'Tech Week', 'Book Fair'],
        'Click Time': [
            '2024-01-15 10:25:00',
            '2024-01-15 11:40:00',
            '2024-01-15 14:15:00', 
            '2024-01-15 16:05:00'
        ],
        'Customer Type': ['New', 'Returning', 'New', 'Returning']
    }
    
    return pd.DataFrame(sample_data)

def test_platform_detection():
    """测试平台检测功能"""
    print("🔍 测试平台检测功能...")
    
    try:
        from agents.data_dmp_agent.platform_detector import PlatformDetector
        
        detector = PlatformDetector()
        
        # 测试文件名检测
        test_files = [
            'leads_adn_report_20240115.csv',
            'LeadsADN_conversion_data.xlsx',
            'LEADSAMDN_20240115.csv',
            'publisher-conversion-report.csv'  # 非LeadsADN文件
        ]
        
        for filename in test_files:
            detected = detector.detect_from_filename(filename)
            print(f"   📄 {filename} -> {detected}")
        
        # 测试内容检测
        sample_df = create_sample_leads_adn_data()
        detected_platform = detector.detect_from_content(sample_df)
        print(f"   📊 内容检测结果: {detected_platform}")
        
        print("✅ 平台检测测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 平台检测测试失败: {e}")
        return False

def test_data_processing():
    """测试数据处理功能"""
    print("\n🔄 测试数据处理功能...")
    
    try:
        from agents.data_dmp_agent.leads_adn_data_processor import LeadsADNDataProcessor
        
        # 创建示例数据
        sample_df = create_sample_leads_adn_data()
        print(f"   📊 原始数据: {len(sample_df)} 行, {len(sample_df.columns)} 列")
        print(f"   📝 原始列名: {list(sample_df.columns)}")
        
        # 处理数据
        processor = LeadsADNDataProcessor()
        processed_df, processing_info = processor.process_data(sample_df, "test_leads_adn.csv")
        
        print(f"   ✅ 处理后数据: {len(processed_df)} 行, {len(processed_df.columns)} 列")
        print(f"   📝 统一字段: {list(processed_df.columns)}")
        
        # 检查关键字段
        required_fields = ['USD Sale Amount', 'Advertiser', 'Conversion ID', 'Status', 'Partner']
        missing_fields = []
        for field in required_fields:
            if field not in processed_df.columns:
                missing_fields.append(field)
            else:
                print(f"   ✅ {field}: 存在")
        
        if missing_fields:
            print(f"   ⚠️ 缺少关键字段: {missing_fields}")
        
        # 检查Partner提取
        if 'Partner' in processed_df.columns:
            partner_distribution = processed_df['Partner'].value_counts()
            print(f"   📊 Partner分布: {partner_distribution.to_dict()}")
        
        # 显示处理信息
        print(f"   📈 处理统计: {json.dumps(processing_info, indent=2, default=str)}")
        
        print("✅ 数据处理测试完成")
        return True, processed_df
        
    except Exception as e:
        print(f"❌ 数据处理测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def test_output_compatibility():
    """测试输出与reporter_agent的兼容性"""
    print("\n🔗 测试与reporter_agent的兼容性...")
    
    try:
        # 获取处理后的数据
        success, processed_df = test_data_processing()
        if not success or processed_df is None:
            print("❌ 无法获取处理后的数据")
            return False
        
        # 检查reporter_agent所需的关键字段
        reporter_required_fields = [
            'USD Sale Amount',  # 金额字段
            'Advertiser',       # 广告主
            'Conversion ID',    # 转换ID
            'Status',          # 状态
            'Partner',         # Partner（从affiliate提取）
            'Datetime Conversion'  # 转换时间
        ]
        
        compatibility_score = 0
        total_fields = len(reporter_required_fields)
        
        for field in reporter_required_fields:
            if field in processed_df.columns:
                compatibility_score += 1
                # 检查数据质量
                non_null_count = processed_df[field].notna().sum()
                print(f"   ✅ {field}: 存在 ({non_null_count}/{len(processed_df)} 非空)")
            else:
                print(f"   ❌ {field}: 缺失")
        
        compatibility_percentage = (compatibility_score / total_fields) * 100
        print(f"   📊 兼容性评分: {compatibility_percentage:.1f}% ({compatibility_score}/{total_fields})")
        
        # 测试数据类型
        print("\n   🔍 数据类型检查:")
        for field in processed_df.columns:
            dtype = processed_df[field].dtype
            sample_value = processed_df[field].iloc[0] if len(processed_df) > 0 else None
            print(f"     - {field}: {dtype} (示例: {sample_value})")
        
        if compatibility_percentage >= 100:
            print("✅ 完全兼容reporter_agent")
            return True
        else:
            print(f"⚠️ 部分兼容reporter_agent ({compatibility_percentage:.1f}%)")
            return False
        
    except Exception as e:
        print(f"❌ 兼容性测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 LeadsADN数据处理器测试开始")
    print("=" * 60)
    
    # 运行所有测试
    tests = [
        ("平台检测", test_platform_detection),
        ("数据处理", lambda: test_data_processing()[0]),
        ("输出兼容性", test_output_compatibility)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}测试异常: {e}")
            results.append((test_name, False))
    
    # 输出总结
    print("\n" + "=" * 60)
    print("📊 测试结果总结:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    success_rate = (passed / total) * 100 if total > 0 else 0
    print(f"\n🎯 总体成功率: {success_rate:.1f}% ({passed}/{total})")
    
    if success_rate == 100:
        print("🎉 所有测试通过！LeadsADN支持已成功实现")
    else:
        print("⚠️ 部分测试失败，需要进一步优化")
    
    return success_rate == 100

if __name__ == "__main__":
    main()
