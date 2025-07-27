#!/usr/bin/env python3
"""
DMP-Agent主程序
整合API數據獲取、數據處理和Google Cloud SQL存儲
支持 --days-ago 和 --platform 參數
"""

import sys
import os
import argparse
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# 添加父目錄到Python路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# 導入配置模組
import config

# 嘗試相對導入，失敗則使用絕對導入
try:
    from .database_manager import EnhancedDMPDatabaseManager
    from .api_config_manager import APIConfigManager
except ImportError:
    from agents.data_dmp_agent.database_manager import EnhancedDMPDatabaseManager
    from agents.data_dmp_agent.api_config_manager import APIConfigManager

# API數據獲取器從api_agent導入
try:
    from agents.api_agent.api_data_fetcher import EnhancedAPIDataFetcher as APIDataFetcher
except ImportError:
    # 如果沒有增強版本，創建一個簡單的替代
    class APIDataFetcher:
        def get_available_platforms(self):
            return ["IAByteC", "IATestByteC"]
        
        async def test_platform_connection(self, platform):
            return True

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('dmp_agent.log')
    ]
)
logger = logging.getLogger(__name__)

class DMPAgent:
    """DMP代理主類"""
    
    def __init__(self):
        self.db_manager = EnhancedDMPDatabaseManager()
        self.api_fetcher = APIDataFetcher()
        self.config_manager = APIConfigManager()
        self.stats = {
            'total_fetched': 0,
            'total_processed': 0,
            'total_stored': 0,
            'errors': []
        }
    
    async def initialize(self, skip_db_check: bool = False):
        """初始化DMP代理"""
        logger.info("🚀 正在初始化DMP-Agent...")
        
        try:
            # 初始化數據庫連接
            await self.db_manager.init_pool()
            
            # 如果跳過數據庫檢查（如file模式），則不執行健康檢查
            if skip_db_check:
                logger.info("📁 文件模式: 跳過數據庫健康檢查")
                logger.info("✅ DMP-Agent初始化成功 (文件模式)")
                return
            
            # 檢查數據庫健康狀態
            health = await self.db_manager.health_check()
            if health.get('status') != 'healthy':
                raise Exception(f"數據庫不健康: {health.get('error', 'Unknown')}")
            
            logger.info("✅ DMP-Agent初始化成功")
            logger.info(f"   - 數據庫連接: {health.get('conversions_count', 0)} 條轉化記錄")
            logger.info(f"   - 合作夥伴: {health.get('partners_count', 0)} 個")
            logger.info(f"   - 平台: {health.get('platforms_count', 0)} 個")
            
        except Exception as e:
            logger.error(f"❌ DMP-Agent初始化失敗: {e}")
            raise
    
    async def cleanup(self, skip_db_cleanup: bool = False):
        """清理資源"""
        logger.info("🧹 正在清理DMP-Agent資源...")
        
        if skip_db_cleanup:
            logger.info("📁 文件模式: 跳過數據庫連接清理")
        else:
            await self.db_manager.close_pool()
            
        logger.info("✅ DMP-Agent資源清理完成")
    
    async def process_platform_data(self, platform: str, days_ago: int = 1, passthrough: bool = False, data_source: str = 'api', start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """處理特定平台的數據"""
        logger.info(f"🔄 開始處理平台數據: {platform} (days_ago={days_ago}, data_source={data_source})")
        if passthrough:
            logger.info("🔄 Passthrough模式: 啟用 - 數據不會插入Cloud SQL")
        if start_date and end_date:
            logger.info(f"📅 日期範圍: {start_date} to {end_date}")
        
        try:
            # 步驟1: 驗證平台配置（在file模式下跳過）
            if data_source == 'file':
                logger.info("📁 文件模式: 跳過平台配置驗證")
            else:
                if not self.config_manager.validate_config(platform):
                    error_msg = f"平台配置無效: {platform}"
                    logger.error(f"❌ {error_msg}")
                    self.stats['errors'].append(error_msg)
                    return {'success': False, 'error': error_msg}
            
            # 步驟2: 根據數據來源獲取轉化數據
            if data_source == 'api':
                logger.info(f"📥 正在從API獲取轉化數據...")
                conversions = await self.api_fetcher.fetch_conversions(platform, days_ago)
                
                if not conversions:
                    logger.warning(f"⚠️ 沒有獲取到轉化數據: {platform}")
                    return {
                        'success': True,
                        'platform': platform,
                        'days_ago': days_ago,
                        'fetched_count': 0,
                        'stored_count': 0,
                        'message': '沒有新的轉化數據'
                    }
                
                self.stats['total_fetched'] += len(conversions)
                logger.info(f"✅ 成功獲取 {len(conversions)} 條轉化數據")
                
            elif data_source == 'file':
                logger.info(f"📁 處理現有數據文件模式 (由Data Input Agent調用)")
                # 創建示例數據以演示流程，實際應該從文件獲取
                conversions = await self._load_data_from_files()
                
                if not conversions:
                    logger.info(f"ℹ️ 文件模式: 沒有新數據需要處理")
                    return {
                        'success': True,
                        'platform': platform,
                        'days_ago': days_ago,
                        'fetched_count': 0,
                        'stored_count': 0,
                        'message': '文件模式: 沒有新數據需要處理',
                        'data_source': data_source
                    }
                
                self.stats['total_fetched'] += len(conversions)
                logger.info(f"✅ 文件模式: 成功處理 {len(conversions)} 條轉化數據")
            
            else:
                raise ValueError(f"不支持的數據來源: {data_source}")
            
            # 步驟3: 💰 重點Mockup數據處理
            logger.info("=" * 60)
            logger.info("💰 步驟3: 開始Mockup數據處理 (重點步驟)")
            logger.info("=" * 60)
            
            # 🔍 Mockup處理前的詳細統計
            original_count = len(conversions)
            original_total_sale = sum(conv.get('usd_sale_amount', 0) for conv in conversions)
            original_total_payout = sum(conv.get('usd_payout', 0) for conv in conversions)
            original_avg_sale = original_total_sale / original_count if original_count > 0 else 0
            original_avg_payout = original_total_payout / original_count if original_count > 0 else 0
            
            logger.info("🎯 Mockup處理前統計:")
            logger.info(f"   📊 總轉化數: {original_count:,} 條")
            logger.info(f"   💰 總銷售額: ${original_total_sale:,.2f} USD")
            logger.info(f"   💸 總佣金: ${original_total_payout:,.2f} USD")
            logger.info(f"   📈 平均銷售額: ${original_avg_sale:,.2f} USD")
            logger.info(f"   📈 平均佣金: ${original_avg_payout:,.2f} USD")
            if original_total_sale > 0:
                commission_rate = (original_total_payout / original_total_sale) * 100
                logger.info(f"   📋 平均佣金率: {commission_rate:.2f}%")
            
            # 應用Mockup調整
            processed_conversions = await self._apply_mockup_processing(conversions, platform)
            
            # 🎯 Mockup處理後的詳細統計
            adjusted_count = len(processed_conversions)
            adjusted_total_sale = sum(conv.get('usd_sale_amount', 0) for conv in processed_conversions)
            adjusted_total_payout = sum(conv.get('usd_payout', 0) for conv in processed_conversions)
            adjusted_avg_sale = adjusted_total_sale / adjusted_count if adjusted_count > 0 else 0
            adjusted_avg_payout = adjusted_total_payout / adjusted_count if adjusted_count > 0 else 0
            
            logger.info("")
            logger.info("🚀 Mockup處理後統計:")
            logger.info(f"   📊 總轉化數: {adjusted_count:,} 條")
            logger.info(f"   💰 總銷售額: ${adjusted_total_sale:,.2f} USD")
            logger.info(f"   💸 總佣金: ${adjusted_total_payout:,.2f} USD")
            logger.info(f"   📈 平均銷售額: ${adjusted_avg_sale:,.2f} USD")
            logger.info(f"   📈 平均佣金: ${adjusted_avg_payout:,.2f} USD")
            if adjusted_total_sale > 0:
                commission_rate = (adjusted_total_payout / adjusted_total_sale) * 100
                logger.info(f"   📋 平均佣金率: {commission_rate:.2f}%")
            
            logger.info("")
            logger.info("🔄 Mockup調整變化:")
            sale_change = adjusted_total_sale - original_total_sale
            payout_change = adjusted_total_payout - original_total_payout
            sale_change_pct = ((adjusted_total_sale - original_total_sale) / original_total_sale * 100) if original_total_sale > 0 else 0
            payout_change_pct = ((adjusted_total_payout - original_total_payout) / original_total_payout * 100) if original_total_payout > 0 else 0
            
            logger.info(f"   💰 銷售額變化: ${sale_change:+,.2f} USD ({sale_change_pct:+.1f}%)")
            logger.info(f"   💸 佣金變化: ${payout_change:+,.2f} USD ({payout_change_pct:+.1f}%)")
            logger.info("=" * 60)
            
            # 步驟4: 存儲到數據庫（使用高性能優化批量插入） - 根據passthrough模式決定是否執行
            stored_ids = []
            output_file_path = None
            
            if passthrough:
                logger.info("🔄 Passthrough模式: 跳過Cloud SQL存儲，生成標準化temp excel文件")
                
                # 生成標準化temp excel文件
                try:
                    import pandas as pd
                    from datetime import datetime
                    import os
                    import re
                    
                    # 導入配置
                    import config
                    
                    # 創建輸出目錄
                    output_dir = "output"
                    os.makedirs(output_dir, exist_ok=True)
                    
                    # 生成文件名
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    if platform:
                        output_filename = f"DMP_temp_{platform}_{timestamp}.xlsx"
                    else:
                        output_filename = f"DMP_temp_file_import_{timestamp}.xlsx"
                    output_file_path = os.path.join(output_dir, output_filename)
                    
                    # 步驟1: 轉換數據為DataFrame
                    df = pd.DataFrame(processed_conversions)
                    logger.info(f"📊 原始數據: {len(df)} 行, {len(df.columns)} 列")
                    
                    # 步驟2: 智能標準化欄位名稱 (只對實際存在的欄位進行映射)
                    column_mapping = config.get_dmp_column_mapping()
                    
                    # 只對實際存在於DataFrame中的欄位進行映射
                    applicable_mapping = {old_name: new_name 
                                        for old_name, new_name in column_mapping.items() 
                                        if old_name in df.columns}
                    
                    if applicable_mapping:
                        df = df.rename(columns=applicable_mapping)
                        logger.info(f"🔄 已應用欄位名稱標準化: {list(applicable_mapping.keys())} → {list(applicable_mapping.values())}")
                    else:
                        logger.info("🔄 無需欄位名稱標準化 (數據可能已是標準格式)")
                    
                    # 步驟3: 確保標準欄位存在並填充預設值
                    standard_columns = config.get_standard_report_columns()
                    default_values = config.get_column_default_values()
                    
                    for col in standard_columns:
                        if col in ['Partner', 'Source']:
                            continue  # 這兩個欄位稍後單獨處理
                        if col not in df.columns:
                            df[col] = default_values.get(col, '')
                            logger.info(f"➕ 添加缺失欄位: {col}")
                    
                    # 步驟4: 添加Source欄位 (根據數據來源動態選擇)
                    # Passthrough模式：數據來自temp excel，使用標準化後的列名
                    # Non-passthrough模式：數據來自Cloud SQL，使用原始列名
                    if 'Publisher Sub ID 1' in df.columns and not df['Publisher Sub ID 1'].isna().all():
                        # Passthrough模式：從temp excel讀取
                        df['Source'] = df['Publisher Sub ID 1'].fillna('')
                        logger.info("📍 Source設置：使用 Publisher Sub ID 1 (Passthrough模式)")
                    elif 'Aff Sub1' in df.columns and not df['Aff Sub1'].isna().all():
                        # Non-passthrough模式：從Cloud SQL讀取  
                        df['Source'] = df['Aff Sub1'].fillna('')
                        logger.info("📍 Source設置：使用 Aff Sub1 (Cloud SQL模式)")
                    elif 'Aff Sub' in df.columns:
                        # 備用選項
                        df['Source'] = df['Aff Sub'].fillna('')
                        logger.info("📍 Source設置：使用 Aff Sub (備用)")
                    else:
                        df['Source'] = 'Unknown'
                        logger.warning("⚠️ Source設置：無可用源欄位，設為 Unknown")
                    
                    # 步驟5: 添加Partner分組欄位
                    def classify_partner(source_value):
                        """根據PARTNER_SOURCES_MAPPING將source分類到對應的Partner"""
                        if pd.isna(source_value) or str(source_value).strip() == '':
                            return 'Unknown'
                        
                        source_str = str(source_value).strip()
                        
                        # 🔍 先檢查具體的Partner (排除ByteC的通配符匹配)
                        for partner_name, partner_config in config.PARTNER_SOURCES_MAPPING.items():
                            # 跳過ByteC，最後處理
                            if partner_name == 'ByteC':
                                continue
                                
                            pattern = partner_config.get('pattern', '')
                            if pattern and re.match(pattern, source_str, re.IGNORECASE):
                                return partner_name
                                
                            # 如果沒有pattern，檢查sources列表
                            sources = partner_config.get('sources', [])
                            for config_source in sources:
                                if config_source == 'ALL':  # 跳過通配符
                                    continue
                                if source_str.upper().startswith(config_source.upper()):
                                    return partner_name
                        
                        # 🔍 如果沒有匹配到具體Partner，默認歸類為ByteC
                        return 'ByteC'
                    
                    df['Partner'] = df['Source'].apply(classify_partner)
                    
                    # 步驟6: 確保數值欄位類型正確
                    numeric_columns = config.get_numeric_columns()
                    for col in numeric_columns:
                        if col in df.columns:
                            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                    
                    # 步驟7: 重新排列欄位順序，只保留標準欄位
                    final_columns = []
                    for col in standard_columns:
                        if col in df.columns:
                            final_columns.append(col)
                    
                    df = df[final_columns]
                    
                    # 步驟8: 保存標準化的Excel文件
                    df.to_excel(output_file_path, index=False)
                    
                    # 記錄統計信息
                    partner_stats = df['Partner'].value_counts().to_dict()
                    
                    logger.info("📁 Passthrough模式 - 標準化輸出文件信息:")
                    logger.info(f"   📄 輸出文件: {output_file_path}")
                    logger.info(f"   📊 標準化後數據: {len(df):,} 行, {len(df.columns)} 列")
                    logger.info(f"   📋 標準欄位: {list(df.columns)}")
                    logger.info(f"   👥 Partner分布: {partner_stats}")
                    logger.info(f"   💾 文件大小: {os.path.getsize(output_file_path)} bytes")
                    logger.info(f"   🕒 生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    logger.info(f"   🎯 用途: 供Reporter Agent --import 使用")
                    
                    stored_ids = [f"passthrough_{i}" for i in range(len(processed_conversions))]  # 模擬stored_ids用於統計
                    
                except Exception as e:
                    logger.error(f"❌ 生成標準化temp excel文件失敗: {e}")
                    import traceback
                    logger.error(f"錯誤詳情: {traceback.format_exc()}")
                    output_file_path = None
                    stored_ids = [f"passthrough_{i}" for i in range(len(processed_conversions))]
            else:
                logger.info(f"💾 正在存儲轉化數據到Google Cloud SQL（高性能模式）...")
                stored_ids = await self.db_manager.insert_conversion_batch_optimized(processed_conversions, platform)
                
            self.stats['total_stored'] += len(stored_ids)
            if passthrough:
                logger.info(f"✅ Passthrough模式: 處理了 {len(stored_ids)} 條轉化數據（未存儲）")
            else:
                logger.info(f"✅ 成功存儲 {len(stored_ids)} 條轉化數據")
            
            # 步驟4: 生成結果統計
            result = {
                'success': True,
                'platform': platform,
                'days_ago': days_ago,
                'fetched_count': len(conversions),
                'stored_count': len(stored_ids),
                'passthrough_mode': passthrough,  # 🔄 Phase 2: 添加passthrough模式標識
                'output_file_path': output_file_path,  # 添加输出文件路径
                'date_range': self.config_manager.get_date_range(days_ago),
                'processing_time': datetime.now().isoformat(),
                'start_date': start_date,  # 添加日期參數
                'end_date': end_date  # 添加日期參數
            }
            
            # 計算金額統計（使用處理後的數據）
            total_amount = sum(conv.get('usd_sale_amount', 0) for conv in processed_conversions)
            total_payout = sum(conv.get('usd_payout', 0) for conv in processed_conversions)
            
            result['amount_stats'] = {
                'total_sale_amount': total_amount,
                'total_payout': total_payout,
                'average_sale_amount': total_amount / len(processed_conversions) if processed_conversions else 0
            }
            
            # 🔍 DMP Agent執行後重點匯總
            logger.info("=" * 60)
            logger.info("🎯 DMP Agent 執行完成 - 重點匯總")
            logger.info("=" * 60)
            logger.info(f"✅ 平台: {platform}")
            logger.info(f"📊 數據概覽:")
            logger.info(f"   - 原始獲取: {len(conversions):,} 條記錄")
            logger.info(f"   - 最終處理: {len(stored_ids):,} 條記錄")
            if passthrough:
                logger.info(f"   - 存儲模式: Passthrough (數據已處理但未存入Cloud SQL)")
            else:
                logger.info(f"   - 存儲模式: 標準 (數據已存入Cloud SQL)")
            
            logger.info(f"💰 金額統計:")
            logger.info(f"   - 總銷售額: ${total_amount:,.2f} USD")
            logger.info(f"   - 總佣金: ${total_payout:,.2f} USD")
            if total_amount > 0:
                commission_rate = (total_payout / total_amount) * 100
                logger.info(f"   - 佣金率: {commission_rate:.2f}%")
                logger.info(f"   - 平均交易額: ${total_amount / len(processed_conversions):,.2f} USD")
            
            logger.info(f"🔧 處理參數:")
            logger.info(f"   - 處理時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"   - Passthrough模式: {'啟用' if passthrough else '關閉'}")
            logger.info(f"   - 數據源: {data_source}")
            
            # 🔍 輸出文件信息 (Passthrough模式)
            if passthrough and output_file_path:
                logger.info(f"📁 輸出文件信息:")
                logger.info(f"   - 📄 輸出文件路徑: {output_file_path}")
                try:
                    import os
                    file_size = os.path.getsize(output_file_path)
                    logger.info(f"   - 💾 文件大小: {file_size:,} bytes")
                    logger.info(f"   - 🎯 後續用途: Reporter Agent --import 參數")
                except:
                    pass
            
            logger.info("=" * 60)
            
            return result
            
        except Exception as e:
            error_msg = f"處理平台數據失敗: {platform} - {str(e)}"
            logger.error(f"❌ {error_msg}")
            self.stats['errors'].append(error_msg)
            return {'success': False, 'platform': platform, 'error': error_msg}
    
    async def get_platform_stats(self, platform: str = None, days_ago: int = 1) -> Dict[str, Any]:
        """獲取平台統計信息"""
        logger.info(f"📊 獲取平台統計: {platform or 'ALL'} (days_ago={days_ago})")
        
        try:
            stats = await self.db_manager.get_conversion_stats(platform, days_ago)
            return stats
        except Exception as e:
            logger.error(f"❌ 獲取平台統計失敗: {e}")
            return {'error': str(e)}
    
    def print_final_summary(self):
        """打印最終統計摘要"""
        logger.info("📋 DMP-Agent執行摘要:")
        logger.info(f"   - 總獲取數量: {self.stats['total_fetched']} 條記錄")
        logger.info(f"   - 總存儲數量: {self.stats['total_stored']} 條記錄")
        
        if self.stats['errors']:
            logger.error(f"   - 錯誤數量: {len(self.stats['errors'])}")
            for error in self.stats['errors']:
                logger.error(f"     * {error}")
        else:
            logger.info("   - 沒有錯誤")
        
        logger.info("=" * 60)
    
    # 查詢功能相關方法
    def parse_date_arguments(self, args) -> tuple:
        """解析日期參數"""
        if args.start_date and args.end_date:
            start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
            end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
            days_ago = None
        elif args.days_ago:
            # --days-ago 2 表示2天前的單日數據
            target_date = datetime.now() - timedelta(days=args.days_ago)
            start_date = target_date
            end_date = target_date
            days_ago = args.days_ago
        else:
            # 默認查詢昨天的數據
            yesterday = datetime.now() - timedelta(days=1)
            start_date = yesterday
            end_date = yesterday
            days_ago = 1
        
        return start_date, end_date, days_ago
    
    async def _apply_mockup_processing(self, conversions: List[Dict], platform: str) -> List[Dict]:
        """
        應用Mockup數據處理
        
        Args:
            conversions: 原始轉化數據列表
            platform: 平台名稱
            
        Returns:
            List[Dict]: 處理後的轉化數據列表
        """
        try:
            # 從config獲取mockup倍數
            import config
            mockup_multiplier = getattr(config, 'MOCKUP_MULTIPLIER', 0.9)
            
            logger.info(f"🔄 正在應用Mockup處理 (倍數: {mockup_multiplier})")
            
            processed_conversions = []
            original_total = 0
            adjusted_total = 0
            
            for conv in conversions:
                # 創建處理後的轉化數據副本
                processed_conv = conv.copy()
                
                # 處理usd_sale_amount
                original_amount = conv.get('usd_sale_amount', 0)
                if original_amount:
                    adjusted_amount = round(original_amount * mockup_multiplier, 2)
                    processed_conv['usd_sale_amount'] = adjusted_amount
                    original_total += original_amount
                    adjusted_total += adjusted_amount
                
                # 處理usd_payout（如果存在）
                original_payout = conv.get('usd_payout', 0)
                if original_payout:
                    adjusted_payout = round(original_payout * mockup_multiplier, 2)
                    processed_conv['usd_payout'] = adjusted_payout
                
                # 添加mockup處理標記
                processed_conv['mockup_applied'] = True
                processed_conv['mockup_multiplier'] = mockup_multiplier
                processed_conv['original_usd_sale_amount'] = original_amount
                
                processed_conversions.append(processed_conv)
            
            # 詳細日志
            logger.info(f"📊 Mockup處理統計:")
            logger.info(f"   - 處理記錄數: {len(processed_conversions)}")
            logger.info(f"   - 原始總金額: ${original_total:,.2f} USD")
            logger.info(f"   - 調整後總金額: ${adjusted_total:,.2f} USD")
            logger.info(f"   - 調整倍數: {mockup_multiplier}")
            logger.info(f"   - 金額變化: ${adjusted_total - original_total:+,.2f} USD")
            
            return processed_conversions
            
        except Exception as e:
            logger.error(f"❌ Mockup處理失敗: {e}")
            # 如果處理失敗，返回原始數據
            logger.warning("⚠️ 使用原始數據繼續處理")
            return conversions
    
    async def _load_data_from_files(self) -> List[Dict]:
        """
        從文件加載數據 (當data_source='file'時使用)
        這個方法在Data Input Agent調用DMP Agent時使用
        """
        try:
            import pandas as pd
            import os
            import glob
            from datetime import datetime
            
            logger.info("📁 開始從Data Input Agent輸出文件加載數據...")
            
            # 查找最新的Passthrough輸出文件
            output_dir = "output"
            pattern = os.path.join(output_dir, "Passthrough_*.xlsx")
            files = glob.glob(pattern)
            
            if not files:
                logger.warning("⚠️ 未找到Data Input Agent輸出文件")
                return []
            
            # 選擇最新的文件
            latest_file = max(files, key=os.path.getctime)
            logger.info(f"📄 找到輸入文件: {latest_file}")
            
            # 檢查文件狀態
            file_size = os.path.getsize(latest_file)
            logger.info(f"💾 文件大小: {file_size:,} bytes")
            
            # 讀取Excel文件
            df = pd.read_excel(latest_file)
            logger.info(f"📊 成功讀取數據: {len(df):,} 行, {len(df.columns)} 列")
            
            # 轉換為DMP Agent所需的格式
            conversions = []
            for _, row in df.iterrows():
                conversion = {
                    'conversion_id': row.get('Conversion ID'),
                    'order_id': row.get('Order ID'),
                    'conversion_date': row.get('Conversion Date'),
                    'sale_amount': row.get('Sale Amount (USD)', 0),
                    'usd_sale_amount': row.get('Sale Amount (USD)', 0),
                    'usd_payout': row.get('Payout (USD)', 0),
                    'status': row.get('Status', 'Pending'),
                    'aff_sub': row.get('Publisher Sub ID 1', ''),
                    'aff_sub1': row.get('Publisher Sub ID 1', ''),
                    'aff_sub2': row.get('Publisher Sub ID 2', ''),
                    'aff_sub3': row.get('Publisher Sub ID 3', ''),
                    'aff_sub4': row.get('Publisher Sub ID 4', ''),
                    'aff_sub5': row.get('Publisher Sub ID 5', ''),
                    'adv_sub1': row.get('Advertiser Sub ID 1', ''),
                    'adv_sub2': row.get('Advertiser Sub ID 2', ''),
                    'adv_sub3': row.get('Advertiser Sub ID 3', ''),
                    'adv_sub4': row.get('Advertiser Sub ID 4', ''),
                    'adv_sub5': row.get('Advertiser Sub ID 5', ''),
                    'advertiser': row.get('Advertiser', ''),  # 修復：從Data Input Agent的Advertiser欄位讀取
                    'advertiser_name': row.get('Advertiser Name', ''),
                    'campaign_name': row.get('Campaign Name', ''),
                    'tracking_id': row.get('Tracking ID', ''),
                    'platform': 'FileImport',  # 標記為文件導入
                    'data_source': 'file'
                }
                conversions.append(conversion)
            
            logger.info(f"✅ 數據轉換完成: {len(conversions):,} 條轉化記錄")
            logger.info(f"📊 數據總金額: ${sum(c.get('usd_sale_amount', 0) for c in conversions):,.2f} USD")
            
            return conversions
            
        except Exception as e:
            logger.error(f"❌ 文件加載失敗: {e}")
            logger.error(f"🔍 錯誤詳情: {str(e)}")
            return []
    
    def get_mockup_multiplier(self, partner_name: str) -> tuple:
        """獲取partner的mockup乘數"""
        try:
            import sys
            sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            from config import PARTNER_SOURCES_MAPPING
            
            if partner_name == "ByteC":
                return True, 1.0
            elif partner_name in ["DeepLeaper", "RAMPUP", "MKK", "MP"]:
                return True, 0.9
            else:
                return False, 1.0
        except ImportError:
            return False, 1.0
    
    def get_partner_mapping_info(self, partner_name: str) -> Dict[str, Any]:
        """獲取partner的映射信息"""
        try:
            import sys
            sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            from config import PARTNER_SOURCES_MAPPING, get_pattern_for_partner, get_sources_for_partner
            
            partner_config = PARTNER_SOURCES_MAPPING.get(partner_name, {})
            pattern = get_pattern_for_partner(partner_name)
            sources = get_sources_for_partner(partner_name)
            
            if pattern:
                mapping_logic = f"aff_sub LIKE '{pattern.replace('.*', '%')}'"
            elif sources and sources != ["ALL"]:
                source_list = ', '.join([f"'{s}'" for s in sources])
                mapping_logic = f"aff_sub IN ({source_list})"
            else:
                mapping_logic = "所有數據"
            
            return {
                'pattern': pattern,
                'sources': sources,
                'mapping_logic': mapping_logic,
                'email_enabled': partner_config.get('email_enabled', False),
                'platform': partner_config.get('platform', 'Unknown')
            }
        except ImportError:
            return {
                'pattern': '',
                'sources': [],
                'mapping_logic': '無法獲取映射信息',
                'email_enabled': False,
                'platform': 'Unknown'
            }
    
    def format_currency(self, amount: float) -> str:
        """格式化貨幣顯示"""
        if amount is None or amount == 0:
            return "$0.00 USD"
        return f"${amount:,.2f} USD"
    
    def format_percentage(self, rate: float) -> str:
        """格式化百分比顯示"""
        if rate is None or rate == 0:
            return "0.00%"
        return f"{rate:.2f}%"
    
    def map_source_to_correct_partner(self, source_name):
        """將 source 映射到正確的 partner"""
        import re
        
        if not source_name:
            return 'Unknown'
        
        # DeepLeaper 映射規則（根據 config.py）
        if re.match(r'^(OPPO|VIVO|OEM2|OEM3)', source_name):
            return 'DeepLeaper'
        
        # RAMPUP 映射規則
        if re.match(r'^(RAMPUP|RPID)', source_name):
            return 'RAMPUP'
        
        # MKK 映射規則
        if re.match(r'^MKK', source_name):
            return 'MKK'
        
        # MP 映射規則  
        if re.match(r'^MP', source_name):
            return 'MP'
        
        # ByteC 特殊處理
        if source_name in ['ByteC', 'Amos']:
            return 'ByteC'
        
        # 其他情況保持原值
        return source_name

    def remap_partner_data(self, partner_breakdown: List[Dict], source_stats: List[Dict]) -> tuple:
        """重新映射 partner 數據"""
        from collections import defaultdict
        
        # 重新映射 partner_breakdown
        mapped_partners = defaultdict(lambda: defaultdict(lambda: {'count': 0, 'amount': 0.0}))
        
        for row in partner_breakdown:
            original_partner = row.get('partner', '')
            platform = row.get('platform', '')
            count = row.get('conversion_count', 0)
            amount = float(row.get('total_amount', 0)) if row.get('total_amount') else 0.0
            
            # 使用原始 partner 名稱作為 source 來確定正確的 partner
            correct_partner = self.map_source_to_correct_partner(original_partner)
            
            mapped_partners[correct_partner][platform]['count'] += count
            mapped_partners[correct_partner][platform]['amount'] += amount
        
        # 轉換回列表格式
        corrected_breakdown = []
        for partner, platforms in mapped_partners.items():
            for platform, data in platforms.items():
                if data['count'] > 0:
                    corrected_breakdown.append({
                        'partner': partner,
                        'platform': platform,
                        'conversion_count': data['count'],
                        'total_amount': data['amount']
                    })
        
        # 按轉化數排序
        corrected_breakdown.sort(key=lambda x: x['conversion_count'], reverse=True)
        
        # 重新映射 source_stats 中的 partner
        corrected_sources = []
        for row in source_stats:
            source = row.get('source', '')
            original_partner = row.get('partner', '')
            count = row.get('conversion_count', 0)
            amount = float(row.get('total_amount', 0)) if row.get('total_amount') else 0.0
            
            # 使用 source 來確定正確的 partner
            correct_partner = self.map_source_to_correct_partner(source)
            
            corrected_sources.append({
                'source': source,
                'partner': correct_partner,
                'conversion_count': count,
                'total_amount': amount
            })
        
        return corrected_breakdown, corrected_sources
    
    async def query_stats_enhanced(self, partner_filter: str = None, days_ago: int = 1, 
                                   start_date: datetime = None, end_date: datetime = None) -> Dict[str, Any]:
        """增強的統計查詢 - 支持數據來源分離"""
        try:
            async with self.db_manager.pool.acquire() as conn:
                await conn.execute("SET statement_timeout = '300s'")
                
                # 獲取查詢表名（默認從API表查詢）
                query_table = self.db_manager.get_query_table()
                
                # 構建日期條件
                if start_date and end_date:
                    # 使用指定的日期範圍
                    date_condition = "DATE(datetime_conversion) >= $1 AND DATE(datetime_conversion) <= $2"
                    date_params = [start_date.date(), end_date.date()]
                    param_offset = 2
                else:
                    # 使用 days_ago
                    date_condition = "DATE(datetime_conversion) = CURRENT_DATE - INTERVAL '$1 days'"
                    date_params = [days_ago]
                    param_offset = 1
                
                # 基礎統計查詢
                basic_query = f"""
                SELECT 
                    COUNT(*) as total_conversions,
                    SUM(COALESCE(usd_sale_amount, 0)) as total_sale_amount,
                    COUNT(DISTINCT partner) as unique_partners,
                    COUNT(DISTINCT platform) as unique_platforms
                FROM {query_table}
                WHERE {date_condition}
                """
                
                basic_stats = await conn.fetchrow(basic_query, *date_params)
                
                # Partner 統計 - 使用新的分表查詢方法
                if start_date and end_date:
                    partner_stats = await self.db_manager.query_partner_stats_by_date_range(
                        start_date=start_date.strftime('%Y-%m-%d'),
                        end_date=end_date.strftime('%Y-%m-%d'),
                        partner_filter=partner_filter
                    )
                    source_stats = await self.db_manager.query_source_stats_by_date_range(
                        start_date=start_date.strftime('%Y-%m-%d'),
                        end_date=end_date.strftime('%Y-%m-%d'),
                        partner_filter=partner_filter
                    )
                else:
                    partner_stats = await self.db_manager.query_partner_stats_by_date(
                        days_ago=days_ago, 
                        partner_filter=partner_filter
                    )
                    source_stats = await self.db_manager.query_source_stats_by_date(
                        days_ago=days_ago,
                        partner_filter=partner_filter  
                    )
                
                # 數據後處理和映射修正
                corrected_partners, corrected_sources = self.remap_partner_data(partner_stats, source_stats)
                
                logger.info(f"✅ 數據查詢完成: 從表 {query_table} 查詢 {days_ago} 天前數據")
                
                return {
                    'query_info': {
                        'partner_filter': partner_filter,
                        'days_ago': days_ago,
                        'query_time': datetime.now().isoformat(),
                        'query_table': query_table,  # 添加查詢表信息
                        'data_source_separation_enabled': config.should_use_separate_tables()
                    },
                    'basic_stats': dict(basic_stats) if basic_stats else {},
                    'partner_breakdown': corrected_partners,  # 使用修正後的數據
                    'top_sources': corrected_sources,         # 使用修正後的數據
                }
                
        except Exception as e:
            import traceback
            error_msg = f"{str(e)}\n{traceback.format_exc()}"
            logger.error(f"❌ 查詢失敗: {error_msg}")
            return {
                'error': error_msg,
                'query_info': {
                    'partner_filter': partner_filter,
                    'days_ago': days_ago,
                    'query_time': datetime.now().isoformat(),
                    'query_table': 'unknown',
                    'data_source_separation_enabled': config.should_use_separate_tables()
                }
            }
    
    def generate_source_distribution(self, source_stats: List[Dict], partner_name: str) -> List[Dict]:
        """生成source分布信息"""
        partner_sources = [s for s in source_stats if s.get('partner') == partner_name]
        sorted_sources = sorted(partner_sources, key=lambda x: x.get('conversion_count', 0), reverse=True)[:5]
        return sorted_sources
    
    def print_partner_report(self, stats: Dict[str, Any], start_date: datetime, end_date: datetime):
        """打印partner報告"""
        basic_stats = stats.get('basic_stats', {})
        partner_breakdown = stats.get('partner_breakdown', [])
        source_stats = stats.get('top_sources', [])
        
        total_conversions = basic_stats.get('total_conversions', 0)
        total_amount = float(basic_stats.get('total_usd_amount', 0)) if basic_stats.get('total_usd_amount') else 0
        total_payout = float(basic_stats.get('total_usd_payout', 0)) if basic_stats.get('total_usd_payout') else 0
        avg_commission_rate = (total_payout / total_amount * 100) if total_amount > 0 else 0
        
        print(f"\n{'='*80}")
        print(f" Partner 統計報告 ({start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')})")
        print(f"{'='*80}")
        
        print(f"\n🔍 查詢參數:")
        print(f"   - 日期範圍: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
        print(f"   - Partner: {stats.get('query_info', {}).get('partner_filter', 'ALL')}")
        print(f"   - 查詢表: {stats.get('query_info', {}).get('query_table', 'conversions')}")
        print(f"   - 數據來源分離: {'啟用' if stats.get('query_info', {}).get('data_source_separation_enabled', False) else '禁用'}")
        print(f"   - 總記錄數: {total_conversions:,} 條")
        
        # 添加 Partner-Platform 摘要
        print(f"\n🎯 Partner-Platform 摘要:")
        print(f"{'='*80}")
        for i, partner_data in enumerate(partner_breakdown, 1):
            partner_name = partner_data.get('partner', 'Unknown')
            platform = partner_data.get('platform', 'Unknown')
            conversion_count = partner_data.get('conversion_count', 0)
            total_amount = float(partner_data.get('total_amount', 0)) if partner_data.get('total_amount') else 0
            
            print(f"{partner_name} ({platform}): {conversion_count:,} 條轉化，{self.format_currency(total_amount)}")
        
        print(f"\n📈 Partner 詳細統計:")
        print(f"{'='*80}")
        
        for i, partner_data in enumerate(partner_breakdown, 1):
            partner_name = partner_data.get('partner', 'Unknown')
            conversion_count = partner_data.get('conversion_count', 0)
            total_amount = float(partner_data.get('total_amount', 0)) if partner_data.get('total_amount') else 0
            platform = partner_data.get('platform', 'Unknown')
            
            commission_rate = 0.5
            commission_amount = float(total_amount) * (commission_rate / 100)
            
            has_mockup, mockup_multiplier = self.get_mockup_multiplier(partner_name)
            mapping_info = self.get_partner_mapping_info(partner_name)
            
            print(f"\n{i}. {partner_name} (Platform: {platform})")
            print(f"   📊 轉化數: {conversion_count:,} 條，銷售額: {self.format_currency(total_amount)}")
            print(f"   📡 數據來源平台: {platform}")
            print(f"   💰 佣金: {self.format_currency(commission_amount)} (佣金率: {self.format_percentage(commission_rate)})")
            print(f"   🔧 Mockup: {'是' if has_mockup else '否'} (乘數: {mockup_multiplier})")
            print(f"   📋 數據欄位: usd_sale_amount, usd_payout")
            
            print(f"   \n   Source 映射情況:")
            print(f"      映射邏輯: {mapping_info['mapping_logic']} → {partner_name}")
            
            source_distribution = self.generate_source_distribution(source_stats, partner_name)
            if source_distribution:
                print(f"      📊 Source 分布:")
                for source_data in source_distribution:
                    source_name = source_data.get('source', 'Unknown')
                    source_count = source_data.get('conversion_count', 0)
                    source_amount = float(source_data.get('total_amount', 0)) if source_data.get('total_amount') else 0
                    print(f"         - {source_name}: {source_count:,} 條 ({self.format_currency(source_amount)})")
            else:
                print(f"      📊 Source 分布: 無數據")
        
        # 映射邏輯總覽
        print(f"\n📊 映射邏輯總覽:")
        print(f"{'='*80}")
        print(f" Partner 映射規則:")
        
        try:
            import sys
            sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            from config import PARTNER_SOURCES_MAPPING
            for partner_name, config in PARTNER_SOURCES_MAPPING.items():
                pattern = config.get('pattern', '')
                if pattern:
                    display_pattern = pattern.replace('.*', '%')
                    print(f"   - {partner_name}: aff_sub LIKE '{display_pattern}'")
                else:
                    sources = config.get('sources', [])
                    if sources and sources != ["ALL"]:
                        print(f"   - {partner_name}: aff_sub IN ({', '.join(sources)})")
                    else:
                        print(f"   - {partner_name}: 所有數據")
        except ImportError:
            print("   - 無法載入映射配置")
        
        print(f"\n 總計:")
        print(f"   📊 總轉化數: {total_conversions:,} 條")
        print(f"   總銷售額: {self.format_currency(total_amount)}")
        print(f"   💸 總佣金: {self.format_currency(total_payout)}")
        print(f"   平均佣金率: {self.format_percentage(avg_commission_rate)}")
        print(f"{'='*80}")
    
    async def run_query_mode(self, args):
        """執行查詢模式"""
        logger.info("📊 DMP-Agent 查詢模式")
        
        # 解析日期參數
        start_date, end_date, days_ago = self.parse_date_arguments(args)
        
        # 過濾掉 "ALL" 參數
        partner_filter = args.partner
        if partner_filter and partner_filter.upper() == "ALL":
            partner_filter = None
        
        logger.info(f"   日期範圍: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
        logger.info(f"   Partner過濾: {partner_filter or 'ALL'}")
        
        # 執行查詢
        stats = await self.query_stats_enhanced(
            partner_filter=partner_filter,
            days_ago=days_ago,
            start_date=start_date,
            end_date=end_date
        )
        
        if 'error' in stats:
            raise Exception(f"查詢失敗: {stats['error']}")
        
        # 打印報告
        self.print_partner_report(stats, start_date, end_date)

    async def run_delete_mode(self, args):
        """執行數據刪除模式"""
        logger.info("🗑️ DMP-Agent 數據刪除模式")
        
        # 解析日期參數
        start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
        end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
        
        logger.info(f"   刪除日期範圍: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
        
        # 安全確認
        print(f"\n{'='*80}")
        print(f"⚠️  危險操作警告")
        print(f"{'='*80}")
        print(f"您即將刪除以下日期範圍的所有轉化數據:")
        print(f"   日期範圍: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
        print(f"   影響表格: conversions, conversions_api, conversions_postback (如果存在)")
        print(f"\n⚠️  此操作不可逆轉！")
        
        # 先查詢將要刪除的記錄數
        count_results = await self.db_manager.get_conversion_count_by_date_range(
            args.start_date, args.end_date
        )
        
        total_to_delete = sum(count for count in count_results.values() if count > 0)
        
        print(f"\n📊 將要刪除的記錄統計:")
        for table_name, count in count_results.items():
            if count > 0:
                print(f"   - {table_name}: {count:,} 條記錄")
            elif count == 0:
                print(f"   - {table_name}: 無記錄")
            else:
                print(f"   - {table_name}: 查詢失敗")
        
        print(f"\n📋 總計將刪除: {total_to_delete:,} 條記錄")
        
        if total_to_delete == 0:
            logger.info("✅ 沒有需要刪除的記錄，操作結束")
            return
        
        # 用戶確認
        print(f"\n{'='*80}")
        confirm = input("請輸入 'DELETE' 來確認刪除操作 (其他任何輸入將取消): ")
        
        if confirm != 'DELETE':
            logger.info("❌ 用戶取消刪除操作")
            return
        
        # 執行刪除
        logger.info("🚀 開始執行刪除操作...")
        
        try:
            deletion_results = await self.db_manager.delete_conversions_by_date_range(
                args.start_date, args.end_date
            )
            
            # 打印刪除結果
            print(f"\n📊 刪除操作結果:")
            print(f"{'='*80}")
            
            total_deleted = 0
            for table_name, count in deletion_results.items():
                if count > 0:
                    print(f"✅ {table_name}: 成功刪除 {count:,} 條記錄")
                    total_deleted += count
                elif count == 0:
                    print(f"📋 {table_name}: 無記錄需要刪除")
                else:
                    print(f"❌ {table_name}: 刪除失敗")
            
            print(f"\n🎯 總計成功刪除: {total_deleted:,} 條記錄")
            logger.info(f"✅ 數據刪除操作完成: 刪除了 {total_deleted:,} 條記錄")
            
        except Exception as e:
            logger.error(f"❌ 刪除操作失敗: {str(e)}")
            print(f"\n❌ 刪除操作失敗: {str(e)}")
            raise

async def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description='DMP-Agent: 數據管理平台代理',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
  # 數據獲取模式
  python agents/data_dmp_agent/main.py --days-ago 2 --platform IAByteC
  
  # 查詢統計模式
  python agents/data_dmp_agent/main.py --query --days-ago 2 --partner ALL
  python agents/data_dmp_agent/main.py --query --start-date 2025-07-17 --end-date 2025-07-17
  python agents/data_dmp_agent/main.py --query --days-ago 1 --partner DeepLeaper
  
  # 數據刪除模式 (危險操作)
  python agents/data_dmp_agent/main.py --delete --start-date 2025-07-17 --end-date 2025-07-17
  python agents/data_dmp_agent/main.py --delete --start-date 2025-07-15 --end-date 2025-07-20
  
  # Passthrough模式和文件數據源
  python agents/data_dmp_agent/main.py --days-ago 2 --passthrough --data-source file --self-email
        """
    )
    
    # 模式選擇
    parser.add_argument('--query', action='store_true',
                       help='查詢統計模式（不獲取新數據，只查詢現有數據）')
    parser.add_argument('--delete', action='store_true',
                       help='數據刪除模式（危險操作：刪除指定日期範圍的所有轉化數據）')
    
    # 日期參數
    parser.add_argument('--start-date', type=str,
                       help='開始日期 (YYYY-MM-DD)，查詢模式時需配合 --end-date，刪除模式時必須提供')
    parser.add_argument('--end-date', type=str,
                       help='結束日期 (YYYY-MM-DD)，查詢模式時需配合 --start-date，刪除模式時必須提供')
    parser.add_argument('--days-ago', type=int, default=1,
                       help='獲取/查詢多少天前的數據 (默認: 1，不適用於刪除模式)')
    
    # 平台和合作夥伴參數
    parser.add_argument('--platform', type=str, default='IAByteC',
                       help='API平台名稱 (默認: IAByteC)')
    parser.add_argument('--partner', type=str,
                       help='指定partner名稱 (例如: DeepLeaper, RAMPUP, ALL)')
    
    # 功能參數
    parser.add_argument('--test-connection', action='store_true',
                       help='測試平台連接')
    parser.add_argument('--list-platforms', action='store_true',
                       help='列出可用平台')
    parser.add_argument('--stats-only', action='store_true',
                       help='只顯示統計信息，不獲取新數據')
    
    # 🔄 Phase 2: 新增參數 (Additive Only - 保持向後兼容性)
    parser.add_argument('--passthrough', action='store_true',
                       help='Passthrough模式: 不插入Cloud SQL，仅处理和转发数据')
    parser.add_argument('--data-source', choices=['api', 'file'], default='api',
                       help='数据来源: api=从API获取数据, file=处理现有数据文件 (默认: api)')
    parser.add_argument('--self-email', action='store_true',
                       help='发送邮件给自己（从Data Input Agent传递的参数）')
    
    args = parser.parse_args()
    
    # 參數驗證
    if args.delete:
        # 刪除模式需要同時提供開始和結束日期
        if not args.start_date or not args.end_date:
            parser.error("刪除模式需要同時提供 --start-date 和 --end-date")
        
        # 驗證日期格式
        try:
            start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
            end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
            if start_date > end_date:
                parser.error("開始日期不能晚於結束日期")
        except ValueError:
            parser.error("日期格式錯誤，請使用 YYYY-MM-DD 格式")
    elif args.query:
        # 查詢模式的日期驗證
        if args.start_date and not args.end_date:
            parser.error("查詢模式中 --start-date 需要配合 --end-date 使用")
        if args.end_date and not args.start_date:
            parser.error("查詢模式中 --end-date 需要配合 --start-date 使用")
    else:
        # 數據獲取模式的日期驗證
        if args.start_date and not args.end_date:
            parser.error("--start-date 需要配合 --end-date 使用")
        if args.end_date and not args.start_date:
            parser.error("--end-date 需要配合 --start-date 使用")
    
    # 創建DMP代理實例
    agent = DMPAgent()
    
    try:
        # 初始化 - 在file模式下跳過數據庫健康檢查
        skip_db_check = (args.data_source == 'file')
        await agent.initialize(skip_db_check=skip_db_check)
        
        # 處理不同的命令
        if args.list_platforms:
            platforms = agent.api_fetcher.get_available_platforms()
            logger.info(f"可用平台: {platforms}")
            return

        if args.test_connection:
            result = await agent.api_fetcher.test_platform_connection(args.platform)
            if result:
                logger.info(f"✅ 平台連接測試成功: {args.platform}")
            else:
                logger.error(f"❌ 平台連接測試失敗: {args.platform}")
            return

        if args.stats_only:
            stats = await agent.get_platform_stats(args.platform, args.days_ago)
            logger.info(f"📊 平台統計: {stats}")
            return

        if args.query:
            # 查詢統計模式
            await agent.run_query_mode(args)
            return

        if args.delete:
            # 數據刪除模式
            await agent.run_delete_mode(args)
            return
        
        # 主要處理流程
        logger.info("=" * 60)
        logger.info("🚀 DMP-Agent 數據處理流程")
        logger.info("=" * 60)
        
        # 🔍 显示数据源和调用信息
        if args.data_source == 'file':
            logger.info("📊 数据源: Data Input Agent → DMP Agent")
            logger.info("🔗 调用方式: Agent间调用 (--data-source file)")
        else:
            logger.info("📊 数据源: 直接调用 DMP Agent")
            logger.info("🔗 调用方式: 独立运行 (--data-source api)")
        
        logger.info(f"⚙️ 处理参数:")
        if args.data_source == 'file':
            # 文件模式，不显示平台参数
            logger.info(f"   - 数据源: 文件导入模式")
            logger.info(f"   - 天數: {args.days_ago} 天前")
        else:
            # API模式，显示平台参数
            logger.info(f"   - 平台: {args.platform}")
            logger.info(f"   - 天數: {args.days_ago} 天前")
        
        # 顯示日期範圍參數
        if args.start_date and args.end_date:
            logger.info(f"   - 開始日期: {args.start_date}")
            logger.info(f"   - 結束日期: {args.end_date}")
        
        logger.info(f"   - 数据源: {args.data_source}")
        
        if hasattr(args, 'partner') and args.partner:
            logger.info(f"   - Partner: {args.partner}")
        
        # 🔄 Phase 2: 顯示新功能參數狀態
        if args.passthrough:
            logger.info("🔄 Passthrough模式: 啟用 - 數據不會插入Cloud SQL")
        
        if args.self_email:
            logger.info("📧 Self-email模式: 啟用 - 參數已從Data Input Agent傳遞")
        
        logger.info("=" * 60)
        
        # 處理平台數據
        result = await agent.process_platform_data(args.platform, args.days_ago, args.passthrough, args.data_source, args.start_date, args.end_date)
        
        # 打印結果
        if result['success']:
            logger.info("✅ 數據處理成功完成")
            logger.info(f"   - 獲取記錄: {result['fetched_count']} 條")
            if result.get('passthrough_mode'):
                logger.info(f"   - 處理記錄: {result['stored_count']} 條 (Passthrough模式)")
            else:
                logger.info(f"   - 存儲記錄: {result['stored_count']} 條")
            
            if 'amount_stats' in result:
                amount_stats = result['amount_stats']
                logger.info(f"   - 總銷售金額: ${amount_stats['total_sale_amount']:,.2f} USD")
                logger.info(f"   - 總佣金金額: ${amount_stats['total_payout']:,.2f} USD")
                logger.info(f"   - 平均銷售金額: ${amount_stats['average_sale_amount']:,.2f} USD")
        else:
            logger.error("❌ 數據處理失敗")
            logger.error(f"   - 錯誤: {result.get('error', 'Unknown')}")
        
        # 打印最終摘要
        agent.print_final_summary()
        
    except Exception as e:
        logger.error(f"❌ DMP-Agent執行失敗: {e}")
        raise
    finally:
        # 清理資源 - 在file模式下跳過數據庫清理
        skip_db_cleanup = (args.data_source == 'file')
        await agent.cleanup(skip_db_cleanup=skip_db_cleanup)

if __name__ == "__main__":
    asyncio.run(main()) 