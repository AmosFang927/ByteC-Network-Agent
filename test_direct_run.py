#!/usr/bin/env python3
"""
直接運行Reporter Agent的測試腳本
"""

import os
import sys
import asyncio
from datetime import datetime

# 添加當前目錄到路徑
sys.path.insert(0, '/Users/amosfang/ByteC-Network-Agent')

# 直接導入模塊
from reporter_agent.core.report_generator import ReportGenerator

async def main():
    """直接運行報表生成"""
    print("🚀 開始直接運行Reporter Agent", flush=True)
    
    try:
        # 創建報表生成器
        print("📊 創建報表生成器...", flush=True)
        generator = ReportGenerator()
        
        # 設置參數
        partner_name = "DeepLeaper"
        start_date = datetime(2025, 7, 11)
        end_date = datetime(2025, 7, 12, 23, 59, 59)
        
        print(f"📅 參數設置完成:", flush=True)
        print(f"   Partner: {partner_name}", flush=True)
        print(f"   開始日期: {start_date}", flush=True)
        print(f"   結束日期: {end_date}", flush=True)
        
        # 生成報表
        print("🔄 開始生成報表...", flush=True)
        result = await generator.generate_partner_report(
            partner_name=partner_name,
            start_date=start_date,
            end_date=end_date,
            send_email=True,
            upload_feishu=True,
            self_email=True
        )
        
        # 輸出結果
        print("📊 報表生成完成！", flush=True)
        print(f"結果: {result}", flush=True)
        
        # 清理資源
        await generator.cleanup()
        
    except Exception as e:
        print(f"❌ 錯誤: {e}", flush=True)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 