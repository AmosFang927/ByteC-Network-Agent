#!/usr/bin/env python3
"""
飛書上傳測試腳本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.feishu_uploader import FeishuUploader
import config

def test_feishu_upload():
    """測試飛書上傳功能"""
    print("🚀 開始測試飛書上傳功能...")
    
    # 檢查是否有可用的測試文件
    test_files = []
    output_dir = "output"
    
    if os.path.exists(output_dir):
        for file in os.listdir(output_dir):
            if file.endswith('.xlsx') and ('DeepLeaper' in file or 'RAMPUP' in file):
                test_files.append(os.path.join(output_dir, file))
    
    if not test_files:
        print("❌ 沒有找到測試文件，請先運行完整的數據處理流程")
        return
    
    print(f"📁 找到 {len(test_files)} 個測試文件:")
    for file in test_files:
        print(f"   - {file}")
    
    # 初始化飛書上傳器
    uploader = FeishuUploader()
    
    # 測試認證
    print("\n🔐 測試飛書認證...")
    if not uploader.authenticate():
        print("❌ 認證失敗")
        return
    
    # 測試連接
    print("\n🌐 測試飛書連接...")
    if not uploader.test_connection():
        print("❌ 連接測試失敗")
        return
    
    # 上傳文件
    print(f"\n📤 開始上傳 {len(test_files)} 個文件...")
    success_count = 0
    
    for file_path in test_files:
        print(f"\n📄 正在上傳: {os.path.basename(file_path)}")
        try:
            result = uploader._upload_single_file(file_path)
            if result:
                print(f"✅ 上傳成功: {os.path.basename(file_path)}")
                success_count += 1
            else:
                print(f"❌ 上傳失敗: {os.path.basename(file_path)}")
        except Exception as e:
            print(f"❌ 上傳異常: {os.path.basename(file_path)} - {str(e)}")
    
    print(f"\n📊 上傳結果: 成功 {success_count}/{len(test_files)} 個文件")
    
    if success_count == len(test_files):
        print("🎉 所有文件上傳成功！")
    elif success_count > 0:
        print("⚠️ 部分文件上傳成功")
    else:
        print("❌ 所有文件上傳失敗")

if __name__ == "__main__":
    test_feishu_upload() 