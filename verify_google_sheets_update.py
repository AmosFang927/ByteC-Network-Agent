#!/usr/bin/env python3
"""
驗證Google Sheets更新結果的腳本
"""

import time
from agents.data_dmp_agent.google_sheets_manager import GoogleSheetsManager

def verify_update():
    """驗證Google Sheets中的字段映射更新"""
    
    print('🔍 驗證Google Sheets字段映射更新')
    print('=' * 60)
    
    try:
        # 創建管理器並清除緩存
        manager = GoogleSheetsManager()
        manager.cache = {}
        manager.cache_timestamps = {}
        
        spreadsheet_id = '1SaHZ0igiuMBm2gHFD5JSs1hkltphdXqRAlbaZ9nEUf0'
        sheet_name = 'Data_Input_Mapping'
        
        print(f'📡 重新讀取Google Sheets...')
        print(f'   時間: {time.strftime("%Y-%m-%d %H:%M:%S")}')
        
        # 獲取最新數據
        data = manager.get_field_mappings(spreadsheet_id, sheet_name)
        
        if data and 'platforms' in data and 'access_trade' in data['platforms']:
            access_trade_config = data['platforms']['access_trade']
            field_mappings = access_trade_config.get('field_mappings', {})
            
            datetime_mapping = field_mappings.get('Datetime Conversion', '未找到')
            
            print(f'\\n📊 ACCESS_TRADE平台配置:')
            print(f'   Datetime Conversion -> {datetime_mapping}')
            
            if datetime_mapping == 'Conversion Time':
                print('   ✅ 更新成功！映射已正確設置為 Conversion Time')
                return True
            elif datetime_mapping == 'Status':
                print('   ❌ 更新未生效，仍然映射到 Status')
                print('   💡 可能需要等待幾秒鐘讓Google Sheets同步，然後重新運行此腳本')
                return False
            else:
                print(f'   ❓ 映射到未預期的字段: {datetime_mapping}')
                return False
        else:
            print('❌ 無法讀取ACCESS_TRADE平台配置')
            return False
            
    except Exception as e:
        print(f'❌ 驗證失敗: {e}')
        return False

def show_all_access_trade_mappings():
    """顯示ACCESS_TRADE的所有字段映射"""
    
    print('\\n📋 ACCESS_TRADE完整字段映射:')
    print('-' * 60)
    
    try:
        manager = GoogleSheetsManager()
        manager.cache = {}
        manager.cache_timestamps = {}
        
        spreadsheet_id = '1SaHZ0igiuMBm2gHFD5JSs1hkltphdXqRAlbaZ9nEUf0'
        sheet_name = 'Data_Input_Mapping'
        
        data = manager.get_field_mappings(spreadsheet_id, sheet_name)
        
        if data and 'platforms' in data and 'access_trade' in data['platforms']:
            access_trade_config = data['platforms']['access_trade']
            field_mappings = access_trade_config.get('field_mappings', {})
            data_transformations = access_trade_config.get('data_transformations', {})
            
            for unified_field, raw_field in field_mappings.items():
                transform = data_transformations.get(unified_field, {})
                transform_info = ''
                
                if transform:
                    transform_type = transform.get('type', '')
                    if transform_type:
                        transform_info = f' ({transform_type}'
                        if 'format' in transform:
                            transform_info += f', {transform["format"]}'
                        transform_info += ')'
                
                # 標記重要字段
                if unified_field == 'Datetime Conversion':
                    marker = '🎯'
                elif 'Conversion' in unified_field or 'Datetime' in unified_field:
                    marker = '⏰'
                elif unified_field in ['Advertiser', 'Local Sale Amount', 'Local Reward']:
                    marker = '💰'
                else:
                    marker = '  '
                
                print(f'{marker} {unified_field:<20} -> {raw_field}{transform_info}')
        
    except Exception as e:
        print(f'❌ 顯示映射失敗: {e}')

if __name__ == '__main__':
    # 執行驗證
    success = verify_update()
    
    # 顯示完整映射
    show_all_access_trade_mappings()
    
    print(f'\\n' + '='*60)
    if success:
        print('🎉 Google Sheets更新驗證成功！')
    else:
        print('⚠️  請檢查Google Sheets更新是否已保存，或稍後重新運行此腳本')
        print('\\n🔗 Google Sheets連結:')
        print('https://docs.google.com/spreadsheets/d/1SaHZ0igiuMBm2gHFD5JSs1hkltphdXqRAlbaZ9nEUf0/edit#gid=0')