#!/usr/bin/env python3
"""
测试绕过时间检查的 Google Sheets 连接
"""

import logging
from agents.data_dmp_agent.google_sheets_manager_bypass import GoogleSheetsManagerBypass

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_google_sheets_bypass():
    """测试绕过版本的 Google Sheets 管理器"""
    print("🔧 测试绕过时间检查的 Google Sheets 连接")
    print("=" * 50)
    
    try:
        # 初始化管理器
        manager = GoogleSheetsManagerBypass(
            credentials_file="solar-idea-463423-h8-bd12ec2c5361.json",
            cache_duration=300
        )
        
        # 测试连接
        spreadsheet_id = "1SaHZ0igiuMBm2gHFD5JSs1hkltphdXqRAlbaZ9nEUf0"
        
        print(f"📊 测试连接到 Google Sheets: {spreadsheet_id}")
        
        if manager.test_connection(spreadsheet_id):
            print("✅ Google Sheets 连接成功！")
            
            # 测试读取字段映射
            print("\n📋 测试读取字段映射...")
            mappings = manager.get_field_mappings(
                spreadsheet_id=spreadsheet_id,
                sheet_name="Data_Input_Mapping",
                range_name="A1:Z1000"
            )
            
            if mappings and "platforms" in mappings:
                print(f"✅ 成功读取字段映射！")
                print(f"📊 可用平台: {list(mappings['platforms'].keys())}")
                
                # 检查是否有 DN_BM 配置
                if "dn_bm" in mappings["platforms"]:
                    print("✅ 找到 DN_BM 平台配置！")
                    dn_bm_config = mappings["platforms"]["dn_bm"]
                    print(f"📋 DN_BM 字段映射数量: {len(dn_bm_config.get('field_mappings', {}))}")
                else:
                    print("⚠️ 未找到 DN_BM 平台配置")
                    
            else:
                print("⚠️ 字段映射为空或格式不正确")
                
        else:
            print("❌ Google Sheets 连接失败")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        logger.error(f"测试异常: {e}")

if __name__ == "__main__":
    test_google_sheets_bypass()


