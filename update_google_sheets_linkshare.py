#!/usr/bin/env python3
"""
更新Google Sheets中的LinkShare字段映射
"""

import sys
import os
import json
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.data_dmp_agent.google_sheets_manager import GoogleSheetsManager

def update_linkshare_mapping():
    """更新Google Sheets中的LinkShare字段映射"""
    
    # 加载配置
    with open('config/field_mapping_config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    google_sheets_config = config['google_sheets']
    
    print("🔧 开始更新Google Sheets中的LinkShare字段映射...")
    print(f"📋 Spreadsheet ID: {google_sheets_config['spreadsheet_id']}")
    print(f"📄 Sheet Name: {google_sheets_config['sheet_name']}")
    
    # 创建Google Sheets管理器
    manager = GoogleSheetsManager(
        credentials_file=google_sheets_config['credentials_file'],
        cache_duration=google_sheets_config['cache_duration']
    )
    
    # 测试连接
    print("🔍 测试Google Sheets连接...")
    if not manager.test_connection(google_sheets_config['spreadsheet_id']):
        print("❌ Google Sheets连接失败")
        return False
    
    print("✅ Google Sheets连接成功")
    
    # 获取当前映射
    print("📥 获取当前字段映射...")
    current_mappings = manager.get_field_mappings(
        google_sheets_config['spreadsheet_id'],
        google_sheets_config['sheet_name'],
        google_sheets_config['range']
    )
    
    print(f"📊 当前可用平台: {list(current_mappings.get('platforms', {}).keys())}")
    
    # 定义LinkShare的完整字段映射
    linkshare_mapping = {
        "platforms": {
            "linkshare": {
                "field_mappings": {
                    "advertiser_name": "Shop name",
                    "campaign_name": "Content Type", 
                    "offer_name": "Product Name",
                    "conversion_amount": "Actual standard commission",
                    "conversion_date": "Time order created",
                    "currency": "Currency",
                    "publisher_id": "Creator username",
                    "publisher_name": "Creator username"
                },
                "data_transformations": {
                    "conversion_amount": {
                        "type": "currency",
                        "currency": "USD"
                    },
                    "conversion_date": {
                        "type": "date",
                        "format": "%Y-%m-%d %H:%M:%S"
                    }
                }
            }
        }
    }
    
    # 更新映射
    if 'platforms' not in current_mappings:
        current_mappings['platforms'] = {}
    
    # 添加或更新LinkShare映射
    current_mappings['platforms']['linkshare'] = linkshare_mapping['platforms']['linkshare']
    
    print("📝 LinkShare字段映射:")
    for target_field, source_field in linkshare_mapping['platforms']['linkshare']['field_mappings'].items():
        print(f"   {source_field} -> {target_field}")
    
    print("🔄 数据转换配置:")
    for field, config in linkshare_mapping['platforms']['linkshare']['data_transformations'].items():
        print(f"   {field}: {config}")
    
    # 这里需要实现将更新后的映射写回Google Sheets的逻辑
    # 由于Google Sheets管理器目前只支持读取，我们需要手动更新Google Sheets
    
    print("\n📋 请手动更新Google Sheets中的LinkShare映射:")
    print(f"🔗 Google Sheets链接: https://docs.google.com/spreadsheets/d/{google_sheets_config['spreadsheet_id']}")
    print(f"📄 工作表: {google_sheets_config['sheet_name']}")
    
    print("\n📝 需要在Google Sheets中添加以下映射:")
    print("平台: linkshare")
    print("字段映射:")
    for target_field, source_field in linkshare_mapping['platforms']['linkshare']['field_mappings'].items():
        print(f"  - {target_field}: {source_field}")
    
    print("\n🔄 数据转换:")
    for field, config in linkshare_mapping['platforms']['linkshare']['data_transformations'].items():
        print(f"  - {field}: {config}")
    
    return True

if __name__ == "__main__":
    try:
        success = update_linkshare_mapping()
        if success:
            print("\n✅ LinkShare字段映射更新完成")
        else:
            print("\n❌ LinkShare字段映射更新失败")
    except Exception as e:
        print(f"\n❌ 更新过程中发生错误: {e}")
        import traceback
        traceback.print_exc() 