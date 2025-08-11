#!/usr/bin/env python3
"""
更新Google Sheets字段映射的工具腳本
"""

import sys
import logging
from agents.data_dmp_agent.google_sheets_manager_writable import GoogleSheetsManagerWritable

def update_mapping():
    """更新Google Sheets中的字段映射"""
    
    # 配置日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    print('📝 更新Google Sheets字段映射')
    print('=' * 60)
    
    try:
        # 初始化可寫入的Google Sheets管理器
        print('🔧 初始化Google Sheets管理器...')
        manager = GoogleSheetsManagerWritable()
        
        # 測試連接
        print('🔗 測試Google Sheets連接...')
        if not manager.test_connection():
            print('❌ Google Sheets連接失敗')
            return False
        
        print('✅ Google Sheets連接成功')
        
        # 配置信息
        spreadsheet_id = '1SaHZ0igiuMBm2gHFD5JSs1hkltphdXqRAlbaZ9nEUf0'
        sheet_name = 'Data_Input_Mapping'
        platform = 'access_trade'
        unified_field = 'Datetime Conversion'
        new_raw_field = 'Conversion Time'
        
        print(f'📊 更新配置:')
        print(f'   工作表ID: {spreadsheet_id}')
        print(f'   工作表名稱: {sheet_name}')
        print(f'   平台: {platform}')
        print(f'   統一字段: {unified_field}')
        print(f'   新原始字段: {new_raw_field}')
        
        # 執行更新
        print(f'\n🔄 更新字段映射...')
        success = manager.update_field_mapping(
            spreadsheet_id=spreadsheet_id,
            sheet_name=sheet_name,
            platform=platform,
            unified_field=unified_field,
            new_raw_field=new_raw_field
        )
        
        if success:
            print('✅ 字段映射更新成功！')
            
            # 驗證更新
            print('\n🔍 驗證更新結果...')
            data = manager.get_field_mappings(spreadsheet_id, sheet_name)
            
            if data and 'platforms' in data and platform in data['platforms']:
                platform_config = data['platforms'][platform]
                field_mappings = platform_config.get('field_mappings', {})
                
                current_mapping = field_mappings.get(unified_field, '未找到')
                print(f'   當前映射: {unified_field} -> {current_mapping}')
                
                if current_mapping == new_raw_field:
                    print('   ✅ 驗證成功！映射已正確更新')
                else:
                    print(f'   ❌ 驗證失敗，預期: {new_raw_field}，實際: {current_mapping}')
            else:
                print('   ❌ 無法驗證更新結果')
        else:
            print('❌ 字段映射更新失敗')
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"更新過程中發生錯誤: {e}")
        return False

def show_current_mappings():
    """顯示當前的字段映射"""
    
    print('📊 當前Google Sheets字段映射')
    print('=' * 60)
    
    try:
        manager = GoogleSheetsManagerWritable()
        
        spreadsheet_id = '1SaHZ0igiuMBm2gHFD5JSs1hkltphdXqRAlbaZ9nEUf0'
        sheet_name = 'Data_Input_Mapping'
        
        data = manager.get_field_mappings(spreadsheet_id, sheet_name)
        
        if data and 'platforms' in data:
            for platform, config in data['platforms'].items():
                print(f'\n📋 平台: {platform}')
                field_mappings = config.get('field_mappings', {})
                
                for unified_field, raw_field in field_mappings.items():
                    if 'datetime' in unified_field.lower() or 'conversion' in unified_field.lower():
                        print(f'   🎯 {unified_field} -> {raw_field}')
                    else:
                        print(f'      {unified_field} -> {raw_field}')
        else:
            print('❌ 無法獲取字段映射')
            
    except Exception as e:
        print(f'❌ 獲取映射失敗: {e}')

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'show':
        show_current_mappings()
    else:
        print('🚀 開始更新Google Sheets字段映射...')
        
        # 先顯示當前映射
        print('\n📊 更新前的狀態:')
        show_current_mappings()
        
        # 執行更新
        print('\n' + '='*60)
        success = update_mapping()
        
        # 顯示更新後的映射
        print('\n📊 更新後的狀態:')
        show_current_mappings()
        
        if success:
            print('\n🎉 Google Sheets字段映射更新完成！')
        else:
            print('\n❌ Google Sheets字段映射更新失敗')
            sys.exit(1)