#!/usr/bin/env python3
"""
Reporter Agent 調試版本 - 帶有詳細日誌輸出
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
import traceback

# 設置詳細的日誌配置
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# 添加當前目錄到路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def log_with_flush(message):
    """帶有強制flush的日誌函數"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}", flush=True)

async def debug_generate_report():
    """調試版本的報表生成"""
    log_with_flush("🚀 開始調試Reporter Agent")
    
    try:
        log_with_flush("📦 導入模塊...")
        from reporter_agent.core.report_generator import ReportGenerator
        log_with_flush("✅ 模塊導入成功")
        
        log_with_flush("🔧 創建報表生成器...")
        generator = ReportGenerator()
        log_with_flush("✅ 報表生成器創建成功")
        
        # 設置參數
        partner_name = "DeepLeaper"
        start_date = datetime(2025, 7, 11)
        end_date = datetime(2025, 7, 12, 23, 59, 59)
        
        log_with_flush(f"📅 參數設置:")
        log_with_flush(f"   Partner: {partner_name}")
        log_with_flush(f"   開始日期: {start_date}")
        log_with_flush(f"   結束日期: {end_date}")
        
        log_with_flush("🔄 開始生成報表...")
        
        # 逐步執行報表生成
        result = await generator.generate_partner_report(
            partner_name=partner_name,
            start_date=start_date,
            end_date=end_date,
            send_email=True,
            upload_feishu=True,
            self_email=True
        )
        
        log_with_flush("📊 報表生成完成！")
        log_with_flush(f"成功: {result.get('success', False)}")
        
        if result.get('success'):
            log_with_flush(f"總記錄數: {result.get('total_records', 0)}")
            log_with_flush(f"總金額: ${result.get('total_amount', 0):.2f}")
            log_with_flush(f"生成文件數: {len(result.get('excel_files', []))}")
            
            for file_path in result.get('excel_files', []):
                log_with_flush(f"   📄 {os.path.basename(file_path)}")
        else:
            log_with_flush(f"❌ 生成失敗: {result.get('error', '未知錯誤')}")
        
        log_with_flush("🧹 清理資源...")
        await generator.cleanup()
        log_with_flush("✅ 清理完成")
        
    except Exception as e:
        log_with_flush(f"❌ 發生錯誤: {str(e)}")
        log_with_flush("📋 錯誤詳情:")
        traceback.print_exc()

if __name__ == "__main__":
    log_with_flush("🎯 開始執行調試程序")
    asyncio.run(debug_generate_report())
    log_with_flush("✨ 程序執行完成") 