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
import pandas as pd
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
    from .platform_detector import PlatformDetector
    from .field_mapping_manager import FieldMappingManager
    from .at_bm_data_processor import ATBMDataProcessor
    from .dn_bm_data_processor import DNBMDataProcessor
except ImportError:
    from agents.data_dmp_agent.database_manager import EnhancedDMPDatabaseManager
    from agents.data_dmp_agent.api_config_manager import APIConfigManager
    from agents.data_dmp_agent.platform_detector import PlatformDetector
    from agents.data_dmp_agent.field_mapping_manager import FieldMappingManager
    from agents.data_dmp_agent.at_bm_data_processor import ATBMDataProcessor
    from agents.data_dmp_agent.dn_bm_data_processor import DNBMDataProcessor

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
        
        # 初始化新的组件
        self.platform_detector = PlatformDetector()
        self.field_mapping_manager = FieldMappingManager()
        self.at_bm_processor = ATBMDataProcessor()
        self.dn_bm_processor = DNBMDataProcessor()
        
        # 初始化修正後數據存儲
        self._corrected_data = None
        
        self.stats = {
            'total_fetched': 0,
            'total_processed': 0,
            'total_stored': 0,
            'errors': []
        }
    
    def get_files_from_folder(self, folder_path: str) -> List[str]:
        """從指定資料夾獲取所有Excel/CSV檔案"""
        from pathlib import Path
        
        folder = Path(folder_path)
        if not folder.exists():
            logger.error(f"資料夾不存在: {folder_path}")
            return []
        
        if not folder.is_dir():
            logger.error(f"路徑不是資料夾: {folder_path}")
            return []
        
        excel_files = []
        for ext in ['*.xlsx', '*.xls', '*.csv']:
            excel_files.extend(folder.glob(ext))
        
        # 按檔案名排序
        excel_files.sort(key=lambda x: x.name)
        
        file_list = [str(f) for f in excel_files]
        logger.info(f"📁 從資料夾 {folder_path} 找到 {len(file_list)} 個檔案")
        for file in file_list:
            logger.info(f"   - {Path(file).name}")
        
        return file_list
    
    def detect_platform_from_filename(self, filename: str) -> str:
        """從檔案名檢測平台類型"""
        # 使用新的PlatformDetector
        detected_platform = self.platform_detector.detect_from_filename(filename)
        
        if detected_platform:
            # 映射到内部平台标识符
            platform_mapping = {
                'access_trade': 'AT_BM',
                'involve_asia': 'IA_BM',
                'shopee': 'SHOPEE',
                'tiktok_shop': 'TIKTOK_SHOP',
                'linkshare': 'LS_BM',  # 更新為 LS_BM
                'dn_bm': 'DN_BM'  # 新增 DN_BM
            }
            return platform_mapping.get(detected_platform, detected_platform.upper())
        
        # 回退到原有的检测逻辑
        filename_lower = filename.lower()
        
        if '_at_bm' in filename_lower:
            return 'AT_BM'
        elif '_ia_bm' in filename_lower:
            return 'IA_BM'
        elif '_ls_bm' in filename_lower:
            return 'LS_BM'
        elif '_dn_bm' in filename_lower:
            return 'DN_BM'  # 新增 DN_BM 檢測
        elif '_ia_ot' in filename_lower:
            return 'IA_OT'
        elif '_ia_mb' in filename_lower:
            return 'IA_MB'  # 修復：添加 IA_MB 檢測
        else:
            return 'UNKNOWN'
    
    def detect_platform_from_content(self, df) -> str:
        """從檔案內容檢測平台類型"""
        try:
            # 使用新的PlatformDetector
            detected_platform = self.platform_detector.detect_from_content(df)
            
            if detected_platform:
                # 映射到内部平台标识符
                platform_mapping = {
                    'access_trade': 'AT_BM',
                    'involve_asia': 'IA_BM',
                    'shopee': 'SHOPEE',
                    'tiktok_shop': 'TIKTOK_SHOP',
                    'linkshare': 'LS_BM'
                }
                return platform_mapping.get(detected_platform, detected_platform.upper())
            
            # 回退到原有的检测逻辑
            columns = [col.lower() for col in df.columns]
            
            # 檢查是否有 IA_OT 特有的欄位
            if any('advertiser' in col for col in columns) and any('conversion date' in col for col in columns):
                return 'IA_OT'
            
            # 檢查是否有 IA_BM 特有的欄位
            if any('campaign name' in col for col in columns) and any('conversion time' in col for col in columns):
                return 'AT_BM'
            
            # 檢查是否有 IA_MB 特有的欄位
            if any('product id' in col for col in columns) and any('total price' in col for col in columns):
                return 'IA_MB'
            
            return 'UNKNOWN'
        except Exception as e:
            logger.warning(f"內容檢測失敗: {e}")
            return 'UNKNOWN'
    
    def _fix_csv_column_mismatch(self, df: pd.DataFrame, file_path: str) -> pd.DataFrame:
        """
        修正CSV文件中列數不匹配導致的數據錯位問題
        
        Args:
            df: pandas讀取的DataFrame
            file_path: CSV文件路徑
            
        Returns:
            修正後的DataFrame
        """
        try:
            # 檢查是否是特定的問題文件
            if 'AT_BM' in file_path and 'ID-async-report-exporter' in file_path:
                logger.warning("🔧 檢測到AT_BM文件的列數不匹配問題，正在修正...")
                
                # 直接讀取CSV文件來獲取正確的數據
                with open(file_path, 'r', encoding='utf-8') as f:
                    header_line = f.readline().strip()
                    data_lines = []
                    for line in f:
                        data_lines.append(line.strip())
                
                # 解析字段名稱
                fields = [field.strip('"') for field in header_line.split(',')]
                
                # 找到關鍵字段的位置
                conv_id_idx = fields.index('Conversion ID') if 'Conversion ID' in fields else None
                reward_idx = fields.index('Reward') if 'Reward' in fields else None
                
                if conv_id_idx is not None and reward_idx is not None:
                    # 提取正確的數據
                    corrected_data = []
                    for line in data_lines:
                        if line.strip():  # 跳過空行
                            values = [val.strip('"') for val in line.split(',')]
                            if len(values) > max(conv_id_idx, reward_idx):
                                corrected_data.append(values)
                    
                    if corrected_data:
                        # 重建DataFrame，確保列數匹配
                        max_cols = max(len(row) for row in corrected_data)
                        
                        # 調整字段名稱數量以匹配數據列數
                        if len(fields) < max_cols:
                            fields.extend([f'extra_col_{i}' for i in range(len(fields), max_cols)])
                        elif len(fields) > max_cols:
                            fields = fields[:max_cols]
                        
                        # 確保每行數據列數一致
                        for i, row in enumerate(corrected_data):
                            if len(row) < max_cols:
                                corrected_data[i].extend([''] * (max_cols - len(row)))
                            elif len(row) > max_cols:
                                corrected_data[i] = row[:max_cols]
                        
                        # 創建新的DataFrame
                        corrected_df = pd.DataFrame(corrected_data, columns=fields)
                        
                        # 轉換數值列（Product ID應保持為字符串）
                        for col in corrected_df.columns:
                            if col in ['Conversion ID', 'Reward', 'Total Price']:
                                try:
                                    corrected_df[col] = pd.to_numeric(corrected_df[col], errors='coerce')
                                except:
                                    pass
                        
                        logger.info(f"✅ AT_BM文件列數不匹配問題已修正")
                        logger.info(f"   修正後Conversion ID: {corrected_df['Conversion ID'].head(3).tolist()}")
                        logger.info(f"   修正後Reward: {corrected_df['Reward'].head(3).tolist()}")
                        
                        # 存儲修正後的數據供AT_BM處理器使用
                        self._corrected_data = corrected_df
                        
                        return corrected_df
            
            # 如果不是問題文件或修正失敗，返回原始DataFrame
            return df
            
        except Exception as e:
            logger.warning(f"CSV文件修正失敗，使用原始數據: {e}")
            return df
    
    def _apply_generic_unified_mapping(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        通用統一字段映射 - 適用於所有平台的通用轉換
        當特定平台配置不可用時使用
        """
        logger.info("🔄 開始應用通用統一字段映射...")
        
        # 通用字段映射規則
        generic_mappings = {
            # 核心字段映射
            'conversion_id': 'Conversion ID',
            'partner': 'Partner', 
            'platform': 'Platform',
            'order_id': 'Order ID',
            'status': 'Status',
            'conversion_status': 'Status',
            
            # 金額字段 - 修复：原始IDR金额映射到Local Sale Amount，USD金额单独处理
            'sale_amount': 'Local Sale Amount',
            'local_sale_amount': 'Local Sale Amount',
            'usd_sale_amount': 'USD Sale Amount',
            'usd_payout': 'Local Reward',
            'payout': 'Local Reward',
            
            # 時間字段
            'conversion_date': 'Datetime Conversion',
            'datetime_conversion': 'Datetime Conversion',
            'created_at': 'Datetime Conversion',
            
            # 追蹤字段
            'aff_sub': 'Publisher Sub ID 1',
            'aff_sub1': 'Publisher Sub ID 1', 
            'aff_sub2': 'Publisher Sub ID 2',
            'aff_sub3': 'Publisher Sub ID 3',
            
            # 廣告字段
            'advertiser': 'Advertiser',
            'advertiser_name': 'Advertiser',
            'campaign_name': 'Campaign Name',
            
            # 其他字段
            'tracking_id': 'Click ID',
            'click_id': 'Click ID'
        }
        
        # 創建新的DataFrame
        unified_df = pd.DataFrame()
        
        # 應用映射
        for original_col, unified_col in generic_mappings.items():
            if original_col in df.columns:
                unified_df[unified_col] = df[original_col]
                logger.debug(f"映射: {original_col} -> {unified_col}")
        
        # 添加缺失的必需統一字段（使用默認值）
        # 这是最小化的核心字段集，基于Google Sheets中的unified fields，已移除 Local Sale Amount 和 Order ID
        required_unified_fields = [
            'Conversion ID', 'Partner', 'Platform', 'Status',
            'USD Sale Amount', 'Datetime Conversion',
            'Advertiser', 'Campaign Name'
        ]
        
        for field in required_unified_fields:
            if field not in unified_df.columns:
                # 根據字段類型設置默認值
                if field in ['USD Sale Amount']:
                    unified_df[field] = 0.0
                elif field in ['Conversion ID']:
                    unified_df[field] = df.get('conversion_id', 'N/A')
                elif field == 'Partner':
                    unified_df[field] = df.get('partner', 'Unknown')
                elif field == 'Platform':
                    unified_df[field] = df.get('platform', 'Unknown')
                else:
                    unified_df[field] = ''
                logger.debug(f"添加缺失字段: {field}")
        
        # 添加貨幣轉換字段
        try:
            from .currency_converter import currency_converter
            
            # USD Sale Amount <- sale_amount IDR轉USD (Local Sale Amount 已从输出中移除)
            if 'sale_amount' in unified_df.columns:
                unified_df['USD Sale Amount'] = unified_df['sale_amount'].apply(
                    lambda x: currency_converter.convert_idr_to_usd(float(x)) if pd.notna(x) and x != '' else 0.0
                )
                logger.debug("添加USD Sale Amount字段")
            
            # USD Reward <- Local Reward IDR轉USD  
            if 'Local Reward' in unified_df.columns:
                unified_df['USD Reward'] = unified_df['Local Reward'].apply(
                    lambda x: currency_converter.convert_idr_to_usd(float(x)) if pd.notna(x) and x != '' else 0.0
                )
                logger.debug("添加USD Reward字段")
                
        except Exception as e:
            logger.warning(f"貨幣轉換失敗: {e}")
        
        # 確保數據行數一致
        if len(df) > 0 and len(unified_df) == 0:
            # 如果沒有成功映射任何字段，至少保留基本結構
            unified_df = pd.DataFrame(index=df.index)
            for field in required_unified_fields:
                unified_df[field] = 'N/A'
        
        logger.info(f"✅ 通用統一字段映射完成: {len(unified_df.columns)} 個統一字段，{len(unified_df)} 條記錄")
        return unified_df
    
    async def process_file_data(self, file_path: str, platform: str = None, passthrough: bool = False) -> Dict[str, Any]:
        """處理單個檔案數據"""
        from pathlib import Path
        
        logger.info(f"🔄 開始處理檔案: {file_path}")
        
        # 如果沒有指定平台，從檔案名檢測
        if not platform:
            platform = self.detect_platform_from_filename(Path(file_path).name)
            logger.info(f"🔍 從檔案名檢測到平台: {platform}")
            
            # 如果檔案名檢測失敗，嘗試從內容檢測
            if platform == 'UNKNOWN':
                logger.info("🔄 檔案名檢測失敗，嘗試從內容檢測平台...")
                # 先讀取文件以進行內容檢測
                import pandas as pd
                file_extension = Path(file_path).suffix.lower()
                if file_extension in ['.xlsx', '.xls']:
                    df = pd.read_excel(file_path)
                elif file_extension == '.csv':
                    encodings = ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252', 'gbk']
                    df = None
                    for encoding in encodings:
                        try:
                            df = pd.read_csv(file_path, encoding=encoding)
                            break
                        except (UnicodeDecodeError, UnicodeError):
                            continue
                    if df is None:
                        raise ValueError("無法讀取CSV檔案，嘗試了多種編碼格式都失敗")
                else:
                    raise ValueError(f"不支援的檔案格式: {file_extension}")
                
                platform = self.detect_platform_from_content(df)
                logger.info(f"🔍 從內容檢測到平台: {platform}")
        
        result = {
            'file_path': file_path,
            'platform': platform,
            'success': False,
            'records_count': 0,
            'processed_data': None
        }
        
        try:
            # 根據平台直接創建相應的處理器
            if platform == 'AT_BM':
                processor = ATBMDataProcessor()
                processor_result = processor.process_at_bm_file(file_path)
                
                if processor_result['success']:
                    result.update({
                        'success': True,
                        'records_count': processor_result['records_processed'],
                        'processed_data': processor_result.get('output_file'),
                        'stats': processor_result.get('stats', {}),
                        'mapping_info': processor_result.get('mapping_info', {})
                    })
                    # 保存最新的AT_BM輸出文件路徑（用於passthrough模式）
                    self._current_at_bm_output_file = processor_result.get('output_file')
                    return result
                else:
                    result.update({
                        'success': False,
                        'error': processor_result.get('error', 'AT_BM processing failed'),
                        'stats': processor_result.get('stats', {})
                    })
                    return result
                    
            elif platform == 'DN_BM':
                try:
                    from .dn_bm_data_processor import DNBMDataProcessor
                except ImportError:
                    from agents.data_dmp_agent.dn_bm_data_processor import DNBMDataProcessor
                    
                processor = DNBMDataProcessor()
                processor_result = processor.process_dn_bm_file(file_path)
                
                if processor_result['success']:
                    result.update({
                        'success': True,
                        'records_count': processor_result['records_processed'],
                        'processed_data': processor_result.get('output_file'),
                        'stats': processor_result.get('stats', {}),
                        'mapping_info': processor_result.get('mapping_info', {})
                    })
                    # 保存DN_BM輸出文件路徑
                    self._current_dn_bm_output_file = processor_result.get('output_file')
                    return result
                else:
                    result.update({
                        'success': False,
                        'error': processor_result.get('error', 'DN_BM processing failed'),
                        'stats': processor_result.get('stats', {})
                    })
                    return result
                    
            elif platform == 'LS_BM':
                try:
                    from .ls_bm_data_processor import LSBMDataProcessor
                except ImportError:
                    from agents.data_dmp_agent.ls_bm_data_processor import LSBMDataProcessor
                    
                processor = LSBMDataProcessor()
                processor_result = processor.process_ls_bm_file(file_path)
                
                if processor_result['success']:
                    result.update({
                        'success': True,
                        'records_count': processor_result['records_processed'],
                        'processed_data': processor_result.get('output_file'),
                        'stats': processor_result.get('stats', {}),
                        'mapping_info': processor_result.get('mapping_info', {})
                    })
                    # 保存LS_BM輸出文件路徑
                    self._current_ls_bm_output_file = processor_result.get('output_file')
                    return result
                else:
                    result.update({
                        'success': False,
                        'error': processor_result.get('error', 'LS_BM processing failed'),
                        'stats': processor_result.get('stats', {})
                    })
                    return result
                    
            elif platform == 'leads_adn':
                logger.info("🎯 使用专门的LeadsADN数据处理器...")
                
                try:
                    from .leads_adn_data_processor import LeadsADNDataProcessor
                except ImportError:
                    from agents.data_dmp_agent.leads_adn_data_processor import LeadsADNDataProcessor
                    
                # 读取数据
                import pandas as pd
                file_extension = Path(file_path).suffix.lower()
                if file_extension in ['.xlsx', '.xls']:
                    df = pd.read_excel(file_path)
                elif file_extension == '.csv':
                    # 尝试不同编码
                    encodings = ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']
                    df = None
                    for encoding in encodings:
                        try:
                            df = pd.read_csv(file_path, encoding=encoding)
                            logger.info(f"✅ 成功使用 {encoding} 编码读取LeadsADN文件")
                            break
                        except UnicodeDecodeError:
                            continue
                    if df is None:
                        raise ValueError("无法读取CSV文件，尝试了多种编码")
                else:
                    raise ValueError(f"不支持的文件格式: {file_extension}")
                
                logger.info(f"📊 LeadsADN数据读取完成: {len(df)} 行, {len(df.columns)} 列")
                
                # 处理数据
                processor = LeadsADNDataProcessor()
                processed_df, processing_info = processor.process_data(df, file_path)
                
                # 生成输出文件
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_basename = Path(file_path).stem
                output_filename = f"LeadsADN_{file_basename}_{timestamp}.xlsx"
                output_path = Path("output") / output_filename
                output_path.parent.mkdir(exist_ok=True)
                
                # 保存处理后的数据
                processed_df.to_excel(output_path, index=False)
                logger.info(f"✅ LeadsADN处理完成，输出文件: {output_path}")
                
                result.update({
                    'success': True,
                    'records_count': len(processed_df),
                    'processed_data': str(output_path),
                    'stats': processing_info,
                    'mapping_info': processing_info.get('mapping_info', {})
                })
                # 保存LeadsADN输出文件路径
                self._current_leads_adn_output_file = str(output_path)
                return result
            
            # 如果不是特定平台處理器，則使用通用處理邏輯
            # 讀取檔案（如果還沒有讀取過）
            import pandas as pd
            
            # 檢查是否已經在平台檢測時讀取了文件
            if 'df' not in locals():
                file_extension = Path(file_path).suffix.lower()
                if file_extension in ['.xlsx', '.xls']:
                    df = pd.read_excel(file_path)
                elif file_extension == '.csv':
                    # 嘗試不同編碼
                    encodings = ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252', 'gbk']
                    df = None
                    for encoding in encodings:
                        try:
                            df = pd.read_csv(file_path, encoding=encoding)
                            logger.info(f"成功使用 {encoding} 編碼讀取CSV檔案")
                            break
                        except (UnicodeDecodeError, UnicodeError):
                            continue
                    
                    if df is None:
                        raise ValueError("無法讀取CSV檔案，嘗試了多種編碼格式都失敗")
                    
                    # 🔧 特殊修正：檢查並修正CSV列數不匹配導致的數據錯位問題
                    df = self._fix_csv_column_mismatch(df, file_path)
                else:
                    raise ValueError(f"不支援的檔案格式: {file_extension}")
                
                logger.info(f"📊 成功讀取數據，共 {len(df)} 行，{len(df.columns)} 列")
            
            # 如果指定了強制平台，覆蓋檢測結果
            if hasattr(self, 'force_platform') and self.force_platform:
                platform = self.force_platform
                logger.info(f"🔧 使用強制指定平台: {platform}")
            
            # 🎯 AT_BM特殊處理分支
            if platform == 'AT_BM' and self.at_bm_processor.is_at_bm_file(Path(file_path).name):
                logger.info("🚀 使用專門的AT_BM數據處理器...")
                
                try:
                    # 🔧 特殊處理：如果已經修正了CSV數據，創建臨時文件給AT_BM處理器使用
                    temp_file_path = file_path
                    if hasattr(self, '_corrected_data') and self._corrected_data is not None:
                        logger.info("🔧 使用修正後的數據創建臨時文件供AT_BM處理器使用")
                        import tempfile
                        temp_fd, temp_file_path = tempfile.mkstemp(suffix='.csv', prefix='corrected_at_bm_')
                        try:
                            self._corrected_data.to_csv(temp_file_path, index=False, encoding='utf-8')
                            logger.info(f"✅ 臨時修正文件已創建: {temp_file_path}")
                        except:
                            os.close(temp_fd)
                            temp_file_path = file_path
                        else:
                            os.close(temp_fd)
                    
                    # 使用AT_BM數據處理器進行專門處理
                    at_bm_result = self.at_bm_processor.process_at_bm_file(
                        temp_file_path, 
                        output_dir="output"
                    )
                    
                    # 清理臨時文件
                    if temp_file_path != file_path and os.path.exists(temp_file_path):
                        try:
                            os.unlink(temp_file_path)
                            logger.info("✅ 臨時文件已清理")
                        except:
                            pass
                    
                    if at_bm_result['success']:
                        logger.info("✅ AT_BM專門處理完成")
                        
                        # 保存AT_BM處理結果文件路徑供passthrough使用
                        self._current_at_bm_output_file = at_bm_result['output_file']
                        logger.info(f"📁 設置AT_BM處理結果文件: {self._current_at_bm_output_file}")
                        
                        # 讀取處理後的數據
                        processed_df = pd.read_csv(at_bm_result['output_file'], encoding='utf-8-sig')
                        
                        # 應用mockup處理
                        processed_data = await self._apply_mockup_processing(
                            processed_df.to_dict('records'), 
                            platform
                        )
                        
                        result['success'] = True
                        result['records_count'] = len(processed_df)
                        result['processed_data'] = processed_data
                        result['at_bm_processing'] = at_bm_result
                        result['output_file'] = at_bm_result['output_file']
                        
                        logger.info(f"✅ AT_BM檔案處理完成: {file_path}")
                        logger.info(f"📄 輸出檔案: {at_bm_result['output_file']}")
                        return result
                        
                    else:
                        logger.error(f"❌ AT_BM專門處理失敗: {at_bm_result.get('error', 'Unknown error')}")
                        # 继续使用通用处理流程
                        
                except Exception as e:
                    logger.error(f"❌ AT_BM專門處理器異常: {e}")
                    # 继续使用通用处理流程
            
            # 使用字段映射管理器進行數據轉換
            try:
                # 將内部平台标识符映射回字段映射管理器使用的标识符
                platform_mapping = {
                    'AT_BM': 'access_trade',
                    'IA_BM': 'involve_asia',
                    'IA_MB': 'involve_asia',
                    'IA_OT': 'involve_asia',
                    'SHOPEE': 'shopee',
                    'TIKTOK_SHOP': 'tiktok_shop',
                    'LS_MB': 'linkshare',
                    'LS_BM': 'linkshare'
                }
                
                mapping_platform = platform_mapping.get(platform, platform.lower())
                
                # 使用字段映射管理器進行映射
                mapped_df, mapping_info = self.field_mapping_manager.map_dataframe_columns(df, mapping_platform)
                
                if not mapped_df.empty:
                    logger.info(f"✅ 使用字段映射管理器成功映射 {len(mapping_info['mapped_columns'])} 個欄位")
                    logger.info(f"📋 映射欄位: {[m['source'] + ' -> ' + m['target'] for m in mapping_info['mapped_columns']]}")
                    if mapping_info['unmapped_columns']:
                        logger.warning(f"⚠️ 未映射欄位: {mapping_info['unmapped_columns']}")
                    
                    # 使用映射後的DataFrame
                    df = mapped_df
                else:
                    logger.warning(f"⚠️ 字段映射失敗，使用原有轉換邏輯")
                    # 回退到原有的轉換邏輯
                    if platform == 'AT_BM':
                        df = await self._convert_at_bm_to_ia_bm(df)
                    elif platform in ['IA_BM', 'IA_MB', 'IA_OT']:
                        logger.info(f"✅ {platform} 格式已經是標準格式，無需轉換")
                    elif platform == 'leads_adn':
                        logger.info(f"✅ {platform} 數據已由專門處理器處理，無需額外轉換")
                    else:
                        logger.warning(f"⚠️ 未知平台 {platform}，使用原始格式")
                        
            except Exception as e:
                logger.error(f"❌ 字段映射失敗: {e}")
                # 回退到原有的轉換邏輯
                if platform == 'AT_BM':
                    df = await self._convert_at_bm_to_ia_bm(df)
                elif platform in ['IA_BM', 'IA_MB', 'IA_OT']:
                    logger.info(f"✅ {platform} 格式已經是標準格式，無需轉換")
                elif platform == 'leads_adn':
                    logger.info(f"✅ {platform} 數據已由專門處理器處理，無需額外轉換")
                else:
                    logger.warning(f"⚠️ 未知平台 {platform}，使用原始格式")
            
            # 轉換為字典格式並添加 Partner 欄位
            records = df.to_dict('records')
            
            # 為每個記錄添加 Partner 欄位
            for record in records:
                # 優先使用文件中已有的 Partner 欄位，如果沒有則根據 Source 重新分類
                partner = record.get('Partner')
                if not partner or partner == 'Unknown':
                    # 根據 Publisher Sub ID 1 重新分類 Partner
                    source = record.get('Publisher Sub ID 1', '')
                    if source:
                        partner = self._classify_partner_by_source(source)
                    else:
                        partner = 'Unknown'
                        
                record['partner'] = partner
            
            # 應用 mockup 處理
            processed_data = await self._apply_mockup_processing(records, platform)
            
            # 最終驗證和摘要
            await self._generate_final_mockup_summary(processed_data, platform)
            
            # 🔧 更新 Passthrough 文件（如果存在）
            await self._update_passthrough_file_with_mockup(processed_data, file_path)
            
            result['success'] = True
            result['records_count'] = len(df)
            result['processed_data'] = processed_data
            
            logger.info(f"✅ 檔案處理完成: {file_path}")
            
        except Exception as e:
            error_msg = f"檔案處理失敗: {file_path} - {str(e)}"
            logger.error(f"❌ {error_msg}")
            result['error'] = str(e)
        
        return result
    
    async def _convert_at_bm_to_ia_bm(self, df):
        """將 AT_BM 格式轉換為 IA_BM 格式（使用動態匯率）"""
        logger.info("🔄 開始 AT_BM 到 IA_BM 格式轉換...")
        
        # 欄位映射 - 基于实际AT_BM数据结构（Campaign ID包含Shopee NON KOL）
        column_mapping = {
            'Campaign Name': 'Advertiser',  # Campaign Name(Shopee ID NON KOL) -> Advertiser 
            'Conversion ID': 'Conversion ID',  # Conversion ID -> Conversion ID (保持不变)
            'Conversion Time': 'Datetime Conversion',  # 修正时间字段名
            'Product ID': 'Product ID',  # Product ID保持不变
            'Total Price': 'Local Sale Amount',  # Total Price -> Local Sale Amount
            'aff_sub': 'Publisher Sub ID 1',    # aff_sub(OEM信息) -> Publisher Sub ID 1
            'Category ID': 'Category ID',  # Category ID保持不变
            'Customer Type': 'Customer Type',  # Customer Type保持不变
            'Status': 'Status'  # Status保持不变
        }
        
        # 重命名欄位
        df = df.rename(columns=column_mapping)
        
        # 新增 Sale Amount (USD) 欄位 - 印尼盾轉美元（使用動態匯率）
        if 'Local Sale Amount' in df.columns:
            try:
                # 動態獲取匯率
                exchange_rate = await self._get_usd_idr_exchange_rate()
                df['Sale Amount (USD)'] = (df['Local Sale Amount'] / exchange_rate).round(2)
                logger.info(f"💱 已添加 USD 金額欄位，使用動態匯率: 1 USD = {exchange_rate} IDR")
            except Exception as e:
                logger.error(f"❌ 獲取匯率失敗: {e}")
                # 使用預設匯率作為備用
                default_rate = 15000
                df['Sale Amount (USD)'] = (df['Local Sale Amount'] / default_rate).round(2)
                logger.info(f"💱 使用預設匯率: 1 USD = {default_rate} IDR")
        
        logger.info("✅ AT_BM 格式轉換完成")
        return df
    
    async def _get_usd_idr_exchange_rate(self) -> float:
        """動態獲取 USD/IDR 匯率"""
        import aiohttp
        import asyncio
        
        # 使用多個免費匯率API作為備用
        api_endpoints = [
            {
                'url': 'https://api.exchangerate-api.com/v4/latest/USD',
                'parser': lambda data: data['rates']['IDR']
            },
            {
                'url': 'https://api.fxratesapi.com/latest?base=USD&symbols=IDR',
                'parser': lambda data: data['rates']['IDR']
            },
            {
                'url': 'https://open.er-api.com/v6/latest/USD',
                'parser': lambda data: data['rates']['IDR']
            }
        ]
        
        # 預設匯率（作為備用）
        default_rate = 15000.0
        
        for api in api_endpoints:
            try:
                logger.info(f"🌐 嘗試從 API 獲取匯率: {api['url']}")
                
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                    async with session.get(api['url']) as response:
                        if response.status == 200:
                            data = await response.json()
                            rate = api['parser'](data)
                            
                            if rate and isinstance(rate, (int, float)) and rate > 0:
                                logger.info(f"✅ 成功獲取匯率: 1 USD = {rate} IDR")
                                return float(rate)
                            else:
                                logger.warning(f"⚠️ API 返回無效匯率: {rate}")
                                continue
                        else:
                            logger.warning(f"⚠️ API 請求失敗: HTTP {response.status}")
                            continue
                            
            except asyncio.TimeoutError:
                logger.warning(f"⚠️ API 請求超時: {api['url']}")
                continue
            except Exception as e:
                logger.warning(f"⚠️ API 請求異常: {api['url']} - {str(e)}")
                continue
        
        # 如果所有API都失敗，使用預設匯率
        logger.warning(f"⚠️ 所有匯率API都失敗，使用預設匯率: 1 USD = {default_rate} IDR")
        return default_rate
    
    def _generate_merged_filename(self, file_paths: List[str]) -> str:
        """生成合併檔案名稱"""
        from pathlib import Path
        from datetime import datetime
        
        # 獲取第一個檔案名作為基礎
        first_file = Path(file_paths[0]).stem
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 生成合併檔案名
        merged_filename = f"{first_file}_merged_{current_time}.csv"
        
        logger.info(f"📝 生成合併檔案名: {merged_filename}")
        return merged_filename
    
    def _save_merged_file(self, data: List[Dict], filename: str):
        """保存合併檔案"""
        import pandas as pd
        from pathlib import Path
        
        try:
            # 轉換為 DataFrame
            df = pd.DataFrame(data)
            
            # 確保輸出目錄存在
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            
            # 保存檔案
            output_path = output_dir / filename
            df.to_csv(output_path, index=False, encoding='utf-8')
            
            logger.info(f"💾 合併檔案已保存: {output_path}")
            logger.info(f"📊 檔案包含 {len(df)} 行數據，{len(df.columns)} 個欄位")
            
        except Exception as e:
            error_msg = f"保存合併檔案失敗: {str(e)}"
            logger.error(f"❌ {error_msg}")
            raise Exception(error_msg)
    
    async def process_multiple_files(self, file_paths: List[str], passthrough: bool = False) -> List[Dict[str, Any]]:
        """處理多個檔案"""
        from pathlib import Path
        
        logger.info(f"🚀 開始批量處理 {len(file_paths)} 個檔案")
        
        results = []
        for file_path in file_paths:
            # 檢測平台
            platform = self.detect_platform_from_filename(file_path)
            logger.info(f"📋 檔案: {Path(file_path).name} -> 平台: {platform}")
            
            # 處理檔案
            result = await self.process_file_data(file_path, platform, passthrough)
            results.append(result)
        
        # 合併所有數據
        all_data = []
        for result in results:
            if result['success'] and result['processed_data']:
                all_data.extend(result['processed_data'])
        
        logger.info(f"📊 合併完成，總共 {len(all_data)} 條記錄")
        
        # 生成合併檔案名稱
        merged_filename = self._generate_merged_filename(file_paths)
        
        # 保存合併檔案
        if all_data and not passthrough:
            self._save_merged_file(all_data, merged_filename)
        
        # 🎯 Passthrough模式特殊處理：為AT_BM和LS_BM文件生成Reporter Agent格式的DMP temp文件並更新Passthrough文件
        if passthrough and len(file_paths) == 1:
            file_path = file_paths[0]
            platform = self.detect_platform_from_filename(file_path)
            
            if platform and 'AT_BM' in platform:
                logger.info("🎯 AT_BM Passthrough模式: 生成Reporter Agent格式的DMP temp文件...")
                
                # 查找最新的AT_BM處理結果文件
                at_bm_processed_file = None
                if hasattr(self, '_current_at_bm_output_file') and self._current_at_bm_output_file:
                    at_bm_processed_file = self._current_at_bm_output_file
                    logger.info(f"🔍 找到AT_BM處理結果文件: {at_bm_processed_file}")
                
                if at_bm_processed_file and os.path.exists(at_bm_processed_file):
                    await self._generate_reporter_format_temp_file(at_bm_processed_file, platform, all_data)
                else:
                    logger.warning("⚠️ 未找到AT_BM處理結果文件，跳過Reporter格式轉換")
            
            elif platform and 'DN_BM' in platform:
                logger.info("🎯 DN_BM Passthrough模式: 更新Passthrough文件並生成DMP temp文件...")
                
                # 查找最新的DN_BM處理結果文件
                dn_bm_processed_file = None
                if hasattr(self, '_current_dn_bm_output_file') and self._current_dn_bm_output_file:
                    dn_bm_processed_file = self._current_dn_bm_output_file
                    logger.info(f"🔍 找到DN_BM處理結果文件: {dn_bm_processed_file}")
                
                if dn_bm_processed_file and os.path.exists(dn_bm_processed_file):
                    await self._update_passthrough_file_with_dn_bm_data(file_path, dn_bm_processed_file)
                else:
                    logger.warning("⚠️ 未找到DN_BM處理結果文件，跳過Passthrough文件更新")
                    
            elif platform and 'LS_BM' in platform:
                logger.info("🎯 LS_BM Passthrough模式: 更新Passthrough文件並生成DMP temp文件...")
                
                # 查找最新的LS_BM處理結果文件
                ls_bm_processed_file = None
                if hasattr(self, '_current_ls_bm_output_file') and self._current_ls_bm_output_file:
                    ls_bm_processed_file = self._current_ls_bm_output_file
                    logger.info(f"🔍 找到LS_BM處理結果文件: {ls_bm_processed_file}")
                
                if ls_bm_processed_file and os.path.exists(ls_bm_processed_file):
                    await self._update_passthrough_file_with_ls_bm_data(file_path, ls_bm_processed_file)
                else:
                    logger.warning("⚠️ 未找到LS_BM處理結果文件，跳過Passthrough文件更新")
                    
            elif platform and 'leads_adn' in platform:
                logger.info("🎯 LeadsADN Passthrough模式: 更新Passthrough文件並生成DMP temp文件...")
                
                # 查找最新的LeadsADN處理結果文件
                leads_adn_processed_file = None
                if hasattr(self, '_current_leads_adn_output_file') and self._current_leads_adn_output_file:
                    leads_adn_processed_file = self._current_leads_adn_output_file
                    logger.info(f"🔍 找到LeadsADN處理結果文件: {leads_adn_processed_file}")
                
                if leads_adn_processed_file and os.path.exists(leads_adn_processed_file):
                    await self._update_passthrough_file_with_leads_adn_data(file_path, leads_adn_processed_file)
                else:
                    logger.warning("⚠️ 未找到LeadsADN處理結果文件，跳過Passthrough文件更新")
        
        return {
            'individual_results': results,
            'merged_data': all_data,
            'total_records': len(all_data),
            'merged_filename': merged_filename
        }
    
    async def _generate_reporter_format_temp_file(self, at_bm_processed_file: str, platform: str, processed_conversions: List[Dict]) -> str:
        """
        為Reporter Agent生成正確格式的DMP temp文件
        
        Args:
            at_bm_processed_file: AT_BM處理器輸出的文件路徑
            platform: 平台名稱
            processed_conversions: 處理後的轉化數據
            
        Returns:
            生成的DMP temp文件路徑
        """
        try:
            import pandas as pd
            from datetime import datetime
            
            logger.info("🔄 開始生成Reporter Agent格式的DMP temp文件...")
            
            # 讀取AT_BM處理器的輸出
            df = pd.read_csv(at_bm_processed_file, encoding='utf-8-sig')
            logger.info(f"📊 讀取AT_BM文件: {len(df)} 行, {len(df.columns)} 列")
            
            # 添加Reporter Agent期望的關鍵字段
            if 'Partner' not in df.columns:
                # 根據Source映射到正確的Partner
                import sys
                import os
                sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                import config
                
                df['Partner'] = df.get('Publisher Sub ID 1', 'Unknown').apply(
                    lambda source: config.match_source_to_partner(source) if pd.notna(source) else 'AT_BM'
                )
                logger.info("✅ 添加Partner字段: 基於Source映射")
                
                # 統計Partner分佈
                partner_dist = df['Partner'].value_counts().to_dict()
                logger.info(f"📊 Partner分佈: {partner_dist}")
            
            if 'Source' not in df.columns:
                # 使用Publisher Sub ID 1作為Source，如果沒有則使用默認值
                df['Source'] = df.get('Publisher Sub ID 1', 'AT_BM_Source')
                logger.info("✅ 添加Source字段: 基於Publisher Sub ID 1")
            
            if 'USD Payout' not in df.columns and 'Local Reward' in df.columns:
                # 將Local Reward轉換為USD Payout (IDR to USD)
                try:
                    from .currency_converter import currency_converter
                    df['USD Payout'] = df['Local Reward'].apply(
                        lambda x: currency_converter.convert_idr_to_usd(float(x)) if pd.notna(x) and x != '' else 0.0
                    )
                    logger.info("✅ 添加USD Payout字段: 基於Local Reward IDR轉USD")
                except Exception as e:
                    logger.warning(f"⚠️ 貨幣轉換失敗，使用固定匯率: {e}")
                    df['USD Payout'] = (df['Local Reward'] / 15000).round(2)
            
            # 確保Status字段存在
            if 'Status' not in df.columns:
                df['Status'] = 'PENDING'
                logger.info("✅ 添加Status字段: PENDING")
            
            # 💰 計算mockup前的總金額
            original_total_usd = df['USD Sale Amount'].sum()
            logger.info(f"💰 Mockup前總USD Sale Amount: ${original_total_usd:,.2f}")
            
            # 應用mockup調整
            logger.info("🔄 對Reporter格式數據應用Mockup調整...")
            unified_conversions = df.to_dict('records')
            
            # 轉換為內部格式以應用mockup
            internal_conversions = []
            for conv in unified_conversions:
                internal_conv = {
                    'conversion_id': conv.get('Conversion ID', conv.get('conversion_id')),
                    'usd_sale_amount': conv.get('USD Sale Amount', conv.get('sale_amount', 0)),
                    'usd_payout': conv.get('USD Payout', conv.get('payout', 0)),
                    'partner': conv.get('Partner', conv.get('partner', 'AT_BM')),
                    'platform': 'AT_BM',
                    # 保留所有原始字段
                    **conv
                }
                internal_conversions.append(internal_conv)
            
            # 應用mockup調整
            adjusted_conversions = await self._apply_mockup_processing(internal_conversions, platform)
            
            # 重新建立DataFrame，保持Reporter Agent期望格式
            df = pd.DataFrame(adjusted_conversions)
            
            # 💰 計算mockup後的總金額
            adjusted_total_usd = df['USD Sale Amount'].sum()
            logger.info(f"💰 Mockup後總USD Sale Amount: ${adjusted_total_usd:,.2f}")
            
            # 💰 計算並顯示mockup影響匯總
            difference = adjusted_total_usd - original_total_usd
            percentage_change = (difference / original_total_usd * 100) if original_total_usd > 0 else 0
            logger.info(f"💰 Mockup影響匯總:")
            logger.info(f"   - 原始金額: ${original_total_usd:,.2f}")
            logger.info(f"   - 調整後金額: ${adjusted_total_usd:,.2f}")
            logger.info(f"   - 差額: ${difference:,.2f} ({percentage_change:+.2f}%)")
            
            # 按Partner統計mockup影響
            if 'Partner' in df.columns:
                partner_stats = df.groupby('Partner')['USD Sale Amount'].sum()
                logger.info(f"💰 按Partner的金額分佈:")
                for partner, amount in partner_stats.items():
                    count = len(df[df['Partner'] == partner])
                    logger.info(f"   - {partner}: ${amount:,.2f} ({count:,} 條記錄)")
            
            # 確保Reporter Agent期望的關鍵字段存在
            reporter_field_mapping = {
                'conversion_id': 'Conversion ID',
                'partner': 'Partner', 
                'platform': 'Platform',
                'usd_sale_amount': 'USD Sale Amount',
                'usd_payout': 'USD Payout'
            }
            
            for internal_field, unified_field in reporter_field_mapping.items():
                if internal_field in df.columns and unified_field not in df.columns:
                    df[unified_field] = df[internal_field]
            
            # 確保Source字段存在
            if 'Source' not in df.columns:
                df['Source'] = df.get('Publisher Sub ID 1', 'AT_BM_Source')
            
            # 移除不需要呈現的字段
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            import config
            
            # 獲取需要移除的字段列表
            columns_to_remove = config.DMP_PASSTHROUGH_REMOVE_COLUMNS
            existing_columns_to_remove = [col for col in columns_to_remove if col in df.columns]
            
            if existing_columns_to_remove:
                df = df.drop(columns=existing_columns_to_remove)
                logger.info(f"🗑️ 移除不需要呈現的字段: {existing_columns_to_remove}")
            
            logger.info(f"📊 清理後最終欄位數: {len(df.columns)}")
            logger.info(f"📋 最終欄位: {list(df.columns)}")
            
            # 生成DMP temp文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file_path = f"output/DMP_temp_ByteC_{timestamp}.xlsx"
            
            with pd.ExcelWriter(output_file_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Data', index=False)
            
            logger.info(f"✅ Reporter格式DMP temp文件生成完成: {output_file_path}")
            logger.info(f"📊 最終格式: {len(df)} 行, {len(df.columns)} 列")
            
            # 驗證Reporter Agent期望的關鍵字段
            required_fields = ['Partner', 'Source', 'USD Sale Amount', 'Status']
            missing_fields = [field for field in required_fields if field not in df.columns]
            if missing_fields:
                logger.warning(f"⚠️ 缺少Reporter期望字段: {missing_fields}")
            else:
                logger.info("✅ 所有Reporter期望字段都已存在")
            
            return output_file_path
            
        except Exception as e:
            logger.error(f"❌ 生成Reporter格式DMP temp文件失敗: {e}")
            import traceback
            logger.error(f"錯誤詳情: {traceback.format_exc()}")
            return None
    
    async def _update_passthrough_file_with_ls_bm_data(self, original_csv_path: str, ls_bm_processed_file: str):
        """
        使用LS_BM處理後的數據更新對應的Passthrough文件
        
        Args:
            original_csv_path: 原始CSV文件路徑
            ls_bm_processed_file: LS_BM處理結果文件路徑
        """
        try:
            import pandas as pd
            import glob
            import os
            from pathlib import Path
            
            logger.info("🔄 開始更新Passthrough文件，使用LS_BM處理後的數據...")
            
            # 從原始CSV文件名推導對應的Passthrough Excel文件
            csv_name = os.path.basename(original_csv_path)
            base_name = csv_name.replace('.csv', '')
            
            # 查找對應的Passthrough Excel文件
            passthrough_pattern = f"output/Passthrough_{base_name}_*.xlsx"
            passthrough_files = glob.glob(passthrough_pattern)
            
            if not passthrough_files:
                logger.warning(f"⚠️ 未找到對應的Passthrough文件，模式: {passthrough_pattern}")
                return
            
            # 使用最新的文件
            passthrough_file = max(passthrough_files, key=os.path.getmtime)
            logger.info(f"🔄 找到對應的Passthrough文件: {passthrough_file}")
            
            # 讀取LS_BM處理後的數據
            if ls_bm_processed_file.endswith('.csv'):
                processed_df = pd.read_csv(ls_bm_processed_file, encoding='utf-8-sig')
            else:
                processed_df = pd.read_excel(ls_bm_processed_file)
            
            logger.info(f"📊 讀取LS_BM處理後數據: {len(processed_df)} 條記錄, {len(processed_df.columns)} 列")
            logger.info(f"📋 LS_BM處理後欄位: {list(processed_df.columns)}")
            
            # 檢查必要字段
            if 'Partner' in processed_df.columns:
                partner_stats = processed_df['Partner'].value_counts()
                logger.info(f"📊 Partner統計: {partner_stats.to_dict()}")
            
            if 'Source' in processed_df.columns:
                source_stats = processed_df['Source'].value_counts()
                logger.info(f"📊 Source統計: {source_stats.head().to_dict()}")
            
            # 備份原始Passthrough文件
            backup_path = passthrough_file.replace('.xlsx', '_backup.xlsx')
            import shutil
            shutil.copy2(passthrough_file, backup_path)
            logger.info(f"💾 已備份原始Passthrough文件到: {backup_path}")
            
            # 將LS_BM處理後的數據寫入Passthrough文件
            # 確保Conversion ID保持為字符串格式以保持精度
            if 'Conversion ID' in processed_df.columns:
                processed_df['Conversion ID'] = processed_df['Conversion ID'].astype(str)
                logger.info("✅ 已確保Conversion ID保持為字符串格式")
            
            with pd.ExcelWriter(passthrough_file, engine='openpyxl') as writer:
                processed_df.to_excel(writer, sheet_name='Data', index=False)
            
            logger.info(f"✅ 成功更新Passthrough文件，現在包含LS_BM處理後的數據")
            logger.info(f"🎯 Reporter Agent將讀取到正確的Partner和Source字段")
            
        except Exception as e:
            logger.error(f"❌ 更新Passthrough文件失敗: {e}")
            import traceback
            logger.error(f"錯誤詳情: {traceback.format_exc()}")
    
    async def _update_passthrough_file_with_dn_bm_data(self, original_csv_path: str, dn_bm_processed_file: str):
        """
        使用DN_BM處理後的數據更新對應的Passthrough文件
        
        Args:
            original_csv_path: 原始CSV文件路徑
            dn_bm_processed_file: DN_BM處理結果文件路徑
        """
        try:
            import pandas as pd
            import glob
            import os
            from pathlib import Path
            
            logger.info(f"🔄 開始更新DN_BM Passthrough文件...")
            logger.info(f"📂 原始文件: {original_csv_path}")
            logger.info(f"📂 處理結果文件: {dn_bm_processed_file}")
            
            # 構建Passthrough文件名模式
            file_basename = Path(original_csv_path).stem
            passthrough_pattern = f"output/Passthrough_{file_basename}_*.xlsx"
            passthrough_files = glob.glob(passthrough_pattern)
            
            if not passthrough_files:
                logger.warning(f"⚠️ 未找到對應的Passthrough文件: {passthrough_pattern}")
                return
            
            # 使用最新的Passthrough文件
            passthrough_file = max(passthrough_files, key=os.path.getctime)
            logger.info(f"📄 找到Passthrough文件: {passthrough_file}")
            
            # 讀取DN_BM處理後的數據
            processed_df = pd.read_csv(dn_bm_processed_file)
            logger.info(f"📊 讀取DN_BM處理數據: {len(processed_df)} 條記錄, {len(processed_df.columns)} 個字段")
            
            # 寫入Passthrough Excel文件
            with pd.ExcelWriter(passthrough_file, engine='openpyxl', mode='w') as writer:
                processed_df.to_excel(writer, sheet_name='Data', index=False)
            
            logger.info(f"✅ 成功更新DN_BM Passthrough文件，現在包含unified fields")
            logger.info(f"🎯 Reporter Agent將讀取到正確的DN_BM字段映射")
            
        except Exception as e:
            logger.error(f"❌ 更新DN_BM Passthrough文件失敗: {e}")
            import traceback
            logger.error(f"錯誤詳情: {traceback.format_exc()}")

    async def _update_passthrough_file_with_leads_adn_data(self, original_csv_path: str, leads_adn_processed_file: str):
        """
        使用LeadsADN處理後的數據更新對應的Passthrough文件
        
        Args:
            original_csv_path: 原始CSV文件路徑
            leads_adn_processed_file: LeadsADN處理結果文件路徑
        """
        try:
            import pandas as pd
            import glob
            import os
            from pathlib import Path
            
            logger.info(f"🔄 開始更新LeadsADN Passthrough文件...")
            logger.info(f"📂 原始文件: {original_csv_path}")
            logger.info(f"📂 處理結果文件: {leads_adn_processed_file}")
            
            # 構建Passthrough文件名模式
            file_basename = Path(original_csv_path).stem
            passthrough_pattern = f"output/Passthrough_{file_basename}_*.xlsx"
            passthrough_files = glob.glob(passthrough_pattern)
            
            if not passthrough_files:
                logger.warning(f"⚠️ 未找到對應的Passthrough文件: {passthrough_pattern}")
                return
            
            # 使用最新的Passthrough文件
            passthrough_file = max(passthrough_files, key=os.path.getctime)
            logger.info(f"📄 找到Passthrough文件: {passthrough_file}")
            
            # 讀取LeadsADN處理後的數據
            processed_df = pd.read_excel(leads_adn_processed_file)
            logger.info(f"📊 讀取LeadsADN處理數據: {len(processed_df)} 行, {len(processed_df.columns)} 列")
            
            # 檢查必要字段
            required_fields = ['Partner', 'USD Sale Amount', 'Advertiser', 'Status']
            missing_fields = [field for field in required_fields if field not in processed_df.columns]
            if missing_fields:
                logger.warning(f"⚠️ LeadsADN數據缺少關鍵字段: {missing_fields}")
            
            # 備份原始Passthrough文件
            backup_path = passthrough_file.replace('.xlsx', '_backup.xlsx')
            import shutil
            shutil.copy2(passthrough_file, backup_path)
            logger.info(f"💾 已備份原始Passthrough文件到: {backup_path}")
            
            # 將LeadsADN處理後的數據寫入Passthrough文件
            # 確保Conversion ID保持為字符串格式以保持精度
            if 'Conversion ID' in processed_df.columns:
                processed_df['Conversion ID'] = processed_df['Conversion ID'].astype(str)
                logger.info("✅ 已確保Conversion ID保持為字符串格式")
            
            with pd.ExcelWriter(passthrough_file, engine='openpyxl') as writer:
                processed_df.to_excel(writer, sheet_name='Data', index=False)
            
            logger.info(f"✅ 成功更新Passthrough文件，現在包含LeadsADN處理後的數據")
            logger.info(f"🎯 Reporter Agent將讀取到正確的Partner和Source字段")
            
        except Exception as e:
            logger.error(f"❌ 更新LeadsADN Passthrough文件失敗: {e}")
            import traceback
            logger.error(f"錯誤詳情: {traceback.format_exc()}")
    
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
            
            # 步驟2.5: 🎯 Partner映射處理 (修復FTK Mockup問题)
            logger.info("=" * 60)
            logger.info("🎯 步驟2.5: Partner映射處理")
            logger.info("=" * 60)
            
            # 為每個轉化數據正確設置partner字段
            import config
            for conv in conversions:
                # 如果沒有partner字段或partner為空，根據aff_sub1進行映射
                aff_sub1 = conv.get('aff_sub1', '')
                if not conv.get('partner') or conv.get('partner') == platform:
                    if aff_sub1:
                        mapped_partner = config.match_source_to_partner(aff_sub1)
                        conv['partner'] = mapped_partner
                        logger.debug(f"映射: {aff_sub1} → Partner: {mapped_partner}")
                    else:
                        conv['partner'] = platform  # 保持原有默認行為
            
            # 統計Partner分佈
            partner_counts = {}
            for conv in conversions:
                partner = conv.get('partner', 'Unknown')
                partner_counts[partner] = partner_counts.get(partner, 0) + 1
            
            logger.info(f"📊 Partner分佈: {partner_counts}")
            
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
            
            # 步驟4: 數據存儲或文件生成
            if passthrough:
                logger.info("📁 Passthrough模式: 生成標準化temp excel文件...")
                
                try:
                    import pandas as pd
                    
                    # 🎯 檢查是否有at_bm_processed文件（統一字段格式）
                    at_bm_processed_file = None
                    if hasattr(self, '_current_at_bm_output_file') and self._current_at_bm_output_file:
                        at_bm_processed_file = self._current_at_bm_output_file
                        logger.info(f"🔍 找到AT_BM處理結果文件: {at_bm_processed_file}")
                    
                    if at_bm_processed_file and os.path.exists(at_bm_processed_file):
                        # ✅ 直接使用AT_BM處理器的統一字段格式結果並轉換為Reporter Agent期望格式
                        logger.info("🎯 使用AT_BM處理器結果並轉換為Reporter Agent格式...")
                        df = pd.read_csv(at_bm_processed_file, encoding='utf-8-sig')
                        
                        # 🔧 轉換為Reporter Agent期望的字段格式
                        logger.info("🔄 轉換為Reporter Agent期望的字段格式...")
                        
                        # 添加Reporter Agent期望的關鍵字段
                        if 'Partner' not in df.columns:
                            df['Partner'] = 'AT_BM'  # 設置Partner為AT_BM
                        
                        if 'Source' not in df.columns:
                            # 使用Publisher Sub ID 1作為Source，如果沒有則使用默認值
                            df['Source'] = df.get('Publisher Sub ID 1', 'AT_BM_Source')
                        
                        if 'USD Sale Amount' not in df.columns:
                            # 將Local Sale Amount轉換為USD Sale Amount (IDR to USD)
                            if 'Local Sale Amount' in df.columns:
                                try:
                                    # 使用動態貨幣轉換
                                    from .currency_converter import currency_converter
                                    df['USD Sale Amount'] = df['Local Sale Amount'].apply(
                                        lambda x: currency_converter.convert_idr_to_usd(float(x)) if pd.notna(x) and x != '' else 0.0
                                    )
                                    logger.info("✅ 成功轉換Local Sale Amount為USD Sale Amount")
                                except Exception as e:
                                    logger.warning(f"⚠️ 貨幣轉換失敗，使用默認匯率: {e}")
                                    # 使用固定匯率作為備用 (1 USD = 15000 IDR)
                                    df['USD Sale Amount'] = (df['Local Sale Amount'] / 15000).round(2)
                            else:
                                df['USD Sale Amount'] = 0.0
                        
                        if 'USD Payout' not in df.columns:
                            # 將Local Reward轉換為USD Payout (IDR to USD)
                            if 'Local Reward' in df.columns:
                                try:
                                    from .currency_converter import currency_converter
                                    df['USD Payout'] = df['Local Reward'].apply(
                                        lambda x: currency_converter.convert_idr_to_usd(float(x)) if pd.notna(x) and x != '' else 0.0
                                    )
                                    logger.info("✅ 成功轉換Local Reward為USD Payout")
                                except Exception as e:
                                    logger.warning(f"⚠️ 貨幣轉換失敗，使用默認匯率: {e}")
                                    df['USD Payout'] = (df['Local Reward'] / 15000).round(2)
                            else:
                                df['USD Payout'] = 0.0
                        
                        # 確保Status字段存在
                        if 'Status' not in df.columns:
                            df['Status'] = 'PENDING'
                        
                        # 應用mockup調整
                        logger.info("🔄 對Reporter格式數據應用Mockup調整...")
                        unified_conversions = df.to_dict('records')
                        
                        # 轉換為內部格式以應用mockup
                        internal_conversions = []
                        for conv in unified_conversions:
                            internal_conv = {
                                'conversion_id': conv.get('Conversion ID', conv.get('conversion_id')),
                                'usd_sale_amount': conv.get('USD Sale Amount', conv.get('sale_amount', 0)),
                                'usd_payout': conv.get('USD Payout', conv.get('payout', 0)),
                                'partner': conv.get('Partner', conv.get('partner', 'AT_BM')),
                                'platform': conv.get('Platform', 'AT_BM'),
                                # 保留所有原始字段
                                **conv
                            }
                            internal_conversions.append(internal_conv)
                        
                        # 應用mockup調整
                        adjusted_conversions = await self._apply_mockup_processing(internal_conversions, platform)
                        
                        # 重新建立DataFrame，保持Reporter Agent期望格式
                        df = pd.DataFrame(adjusted_conversions)
                        
                        # 確保Reporter Agent期望的關鍵字段存在
                        reporter_field_mapping = {
                            'conversion_id': 'Conversion ID',
                            'partner': 'Partner', 
                            'platform': 'Platform',
                            'usd_sale_amount': 'USD Sale Amount',
                            'usd_payout': 'USD Payout'
                        }
                        
                        for internal_field, unified_field in reporter_field_mapping.items():
                            if internal_field in df.columns:
                                # 🔧 強制使用 mockup 調整後的值，覆蓋原始值
                                if internal_field == 'usd_sale_amount' and unified_field == 'USD Sale Amount':
                                    logger.info(f"🔄 強制使用 mockup 調整後的金額: {internal_field} -> {unified_field}")
                                    df[unified_field] = df[internal_field]
                                elif unified_field not in df.columns:
                                    df[unified_field] = df[internal_field]
                        
                        # 確保Source字段存在
                        if 'Source' not in df.columns:
                            df['Source'] = df.get('Publisher Sub ID 1', 'AT_BM_Source')
                        
                        logger.info(f"✅ AT_BM轉Reporter格式完成，欄位數: {len(df.columns)}")
                        logger.info(f"📋 Reporter期望字段: {list(df.columns)}")
                        
                        # 驗證Reporter Agent期望的關鍵字段
                        required_fields = ['Partner', 'Source', 'USD Sale Amount', 'Status']
                        missing_fields = [field for field in required_fields if field not in df.columns]
                        if missing_fields:
                            logger.warning(f"⚠️ 缺少Reporter期望字段: {missing_fields}")
                        else:
                            logger.info("✅ 所有Reporter期望字段都已存在")
                    
                    else:
                        # 🔄 回退到原始邏輯：從processed_conversions重新映射
                        logger.warning("⚠️ 未找到AT_BM處理結果，使用原始映射邏輯...")
                        raw_df = pd.DataFrame(processed_conversions)
                        
                        logger.info(f"📊 從processed_conversions創建原始DataFrame，欄位數: {len(raw_df.columns)}")
                        logger.info(f"📋 原始字段: {list(raw_df.columns)}")
                        logger.info(f"📊 數據行數: {len(raw_df)}")
                        
                        # 應用統一字段映射
                        from agents.data_dmp_agent.field_mapping_manager import FieldMappingManager
                        from agents.data_dmp_agent.unified_field_mapper import UnifiedFieldMapper
                        
                        # 使用正確的平台映射
                        platform_mapping = {
                            'AT_BM': 'access_trade',
                            'IA_BM': 'involve_asia',
                            'IA_MB': 'involve_asia',
                            'IA_OT': 'involve_asia',
                            'SHOPEE': 'shopee',
                            'TIKTOK_SHOP': 'tiktok_shop',
                            'LS_MB': 'linkshare',
                            'LS_BM': 'linkshare'
                        }
                        mapping_platform = platform_mapping.get(platform, platform.lower())
                        logger.info(f"🔄 Platform映射: {platform} -> {mapping_platform}")
                        
                        field_manager = FieldMappingManager()
                        mapping_info = field_manager.get_platform_mapping_info(mapping_platform)
                        
                        if mapping_info and mapping_info.get('field_mappings'):
                            logger.info(f"🔄 應用統一字段映射到passthrough數據...")
                            unified_mapper = UnifiedFieldMapper()
                            df = unified_mapper.map_dataframe_to_unified_fields(
                                raw_df, mapping_info['field_mappings']
                            )
                            logger.info(f"✅ 統一字段映射完成，新欄位數: {len(df.columns)}")
                            logger.info(f"📋 統一字段: {list(df.columns)}")
                        else:
                            logger.warning(f"⚠️ 無法獲取字段映射配置 ({mapping_platform})，使用通用統一字段映射...")
                            # 🎯 通用統一字段映射 - 適用於所有平台
                            df = self._apply_generic_unified_mapping(raw_df)
                            logger.info(f"✅ 通用統一字段映射完成，新欄位數: {len(df.columns)}")
                            logger.info(f"📋 統一字段: {list(df.columns)}")
                    
                    logger.info(f"📊 passthrough模式：最終數據格式，數據行數: {len(df)}")
                    
                    # 步驟5: 保存標準化的Excel文件
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    
                    # 🔧 使用主要Partner名稱而不是platform名稱 (修復文件名匹配問題)
                    if partner_counts:
                        # 使用數據最多的Partner作為文件名
                        main_partner = max(partner_counts.items(), key=lambda x: x[1])[0]
                        if main_partner != platform:  # 只有當不是API平台名稱時才使用Partner名稱
                            output_file_path = f"output/DMP_temp_{main_partner}_{timestamp}.xlsx"
                            logger.info(f"📁 使用主要Partner名稱生成文件: {main_partner} (數據量: {partner_counts[main_partner]})")
                        else:
                            output_file_path = f"output/DMP_temp_{platform}_{timestamp}.xlsx"
                    else:
                        output_file_path = f"output/DMP_temp_{platform}_{timestamp}.xlsx"
                    
                    with pd.ExcelWriter(output_file_path, engine='openpyxl') as writer:
                        df.to_excel(writer, sheet_name='Data', index=False)
                    
                    # 🔧 Passthrough 模式：查找並更新對應的 Passthrough Excel 文件
                    try:
                        import glob
                        import os
                        
                        # 從 CSV 文件名推導對應的 Passthrough Excel 文件
                        if file_path and file_path.endswith('.csv'):
                            # 提取文件名基礎部分
                            csv_name = os.path.basename(file_path)
                            base_name = csv_name.replace('.csv', '')
                            
                            # 查找對應的 Passthrough Excel 文件
                            passthrough_pattern = f"output/Passthrough_{base_name}_*.xlsx"
                            passthrough_files = glob.glob(passthrough_pattern)
                            
                            if passthrough_files:
                                # 使用最新的文件
                                passthrough_file = max(passthrough_files, key=os.path.getmtime)
                                
                                logger.info(f"🔄 找到對應的 Passthrough 文件: {passthrough_file}")
                                logger.info(f"📊 準備用 mockup 調整後的數據覆蓋原始金額")
                                
                                # 備份原始文件
                                backup_path = passthrough_file.replace('.xlsx', '_backup.xlsx')
                                import shutil
                                shutil.copy2(passthrough_file, backup_path)
                                logger.info(f"💾 已備份原始文件到: {backup_path}")
                                
                                # 用 mockup 調整後的數據覆蓋原始 Passthrough 文件
                                with pd.ExcelWriter(passthrough_file, engine='openpyxl') as writer:
                                    df.to_excel(writer, sheet_name='Data', index=False)
                                
                                logger.info(f"✅ 成功更新 Passthrough 文件，現在包含 mockup 調整後的金額")
                                logger.info(f"🎯 Reporter Agent 現在將讀取到正確的 mockup 後金額")
                                
                            else:
                                logger.warning(f"⚠️ 未找到對應的 Passthrough 文件，模式: {passthrough_pattern}")
                        
                    except Exception as e:
                        logger.error(f"❌ 更新 Passthrough 文件失敗: {e}")
                        logger.warning(f"⚠️ 將繼續使用 DMP_temp 文件: {output_file_path}")
                    
                    # 記錄統計信息
                    if 'Partner' in df.columns:
                        partner_stats = df['Partner'].value_counts().to_dict()
                        logger.info(f"📊 Partner統計: {partner_stats}")
                    elif 'partner' in df.columns:
                        partner_stats = df['partner'].value_counts().to_dict()
                        logger.info(f"📊 partner統計: {partner_stats}")
                    else:
                        logger.warning("⚠️ 無法找到Partner/partner字段進行統計")
                    
                    stored_ids = [f"passthrough_{i}" for i in range(len(processed_conversions))]
                    
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
            
            # DMP Agent執行後重點匯總已移除
            
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
    
    async def _generate_final_mockup_summary(self, processed_data: List[Dict], platform: str):
        """
        生成最終的 Mockup 處理摘要和配置驗證報告
        
        Args:
            processed_data: 處理後的數據
            platform: 平台名稱
        """
        try:
            from config import get_partner_mockup_multiplier
            
            logger.info("🎯 ================ 最終 Mockup 處理摘要 ================")
            
            # 統計處理結果
            total_records = len(processed_data)
            total_original = sum(float(record.get('original_usd_sale_amount', 0)) for record in processed_data)
            total_adjusted = sum(float(record.get('USD Sale Amount', 0)) or float(record.get('usd_sale_amount', 0)) for record in processed_data)
            
            # 按 Partner 分組統計
            partner_summary = {}
            for record in processed_data:
                partner = record.get('partner', record.get('Partner', 'Unknown'))
                if partner not in partner_summary:
                    partner_summary[partner] = {
                        'count': 0,
                        'original_total': 0,
                        'adjusted_total': 0,
                        'actual_multiplier': 0,
                        'expected_multiplier': get_partner_mockup_multiplier(partner.upper() if partner else 'Unknown')
                    }
                
                partner_summary[partner]['count'] += 1
                partner_summary[partner]['original_total'] += float(record.get('original_usd_sale_amount', 0))
                partner_summary[partner]['adjusted_total'] += float(record.get('USD Sale Amount', 0)) or float(record.get('usd_sale_amount', 0))
                partner_summary[partner]['actual_multiplier'] = float(record.get('mockup_multiplier', 1.0))
            
            # 輸出最終摘要
            logger.info(f"📊 處理總覽:")
            logger.info(f"   💾 總記錄數: {total_records:,}")
            logger.info(f"   💰 原始總金額: ${total_original:,.2f} USD")
            logger.info(f"   💰 調整後總金額: ${total_adjusted:,.2f} USD")
            logger.info(f"   📈 總金額變化: ${total_adjusted - total_original:+,.2f} USD")
            if total_original > 0:
                total_change_pct = ((total_adjusted - total_original) / total_original) * 100
                logger.info(f"   📈 總變化百分比: {total_change_pct:+.2f}%")
            
            logger.info(f"📋 Partner 明細摘要:")
            
            # 配置不一致警告標記
            has_config_mismatch = False
            
            for partner, summary in partner_summary.items():
                if summary['count'] > 0:
                    original = summary['original_total']
                    adjusted = summary['adjusted_total']
                    actual_mult = summary['actual_multiplier']
                    expected_mult = summary['expected_multiplier']
                    
                    change = adjusted - original
                    change_pct = ((adjusted - original) / original * 100) if original > 0 else 0
                    
                    # 檢查配置一致性
                    is_consistent = abs(actual_mult - expected_mult) <= 0.001
                    consistency_icon = "✅" if is_consistent else "⚠️"
                    
                    if not is_consistent:
                        has_config_mismatch = True
                    
                    logger.info(f"   {consistency_icon} {partner}:")
                    logger.info(f"      📊 記錄數: {summary['count']:,}")
                    logger.info(f"      💰 原始金額: ${original:,.2f} USD")
                    logger.info(f"      💰 調整後金額: ${adjusted:,.2f} USD")
                    logger.info(f"      📈 金額變化: ${change:+,.2f} USD ({change_pct:+.2f}%)")
                    logger.info(f"      ⚙️  實際倍數: {actual_mult:.3f}")
                    logger.info(f"      ⚙️  配置倍數: {expected_mult:.3f}")
                    
                    if not is_consistent:
                        logger.warning(f"         🔥 配置不一致! 實際 ({actual_mult:.3f}) ≠ 預期 ({expected_mult:.3f})")
            
            # 顯示當前所有 Partner 的配置
            logger.info(f"🔧 當前配置驗證 (config.py):")
            all_configured_partners = ['RAMPUP', 'DeepLeaper', 'FTK', 'MP', 'MKK', 'TestPartner', 'ByteC']
            for partner in all_configured_partners:
                configured_mult = get_partner_mockup_multiplier(partner)
                logger.info(f"   📋 {partner}: {configured_mult:.1f} ({configured_mult*100:.0f}%)")
            
            # 最終警告和建議
            if has_config_mismatch:
                logger.error("🚨 !!!! 嚴重警告: Mockup 配置與實際處理不一致 !!!!")
                logger.error("📋 請立即檢查以下問題:")
                logger.error("   1. config.py 中的 PARTNER_SOURCES_MAPPING 配置")
                logger.error("   2. Partner 名稱的大小寫匹配")
                logger.error("   3. 數據中的 Partner 字段值是否正確")
                logger.error("   4. DMP Agent 的 Partner 分類邏輯")
                logger.error("💡 建議: 檢查上述標記為 ⚠️ 的 Partner 配置")
            else:
                logger.info("✅ 🎉 Mockup 配置驗證完全通過! 所有 Partner 處理正確!")
            
            logger.info("🎯 ============= Mockup 處理摘要結束 =============")
            
        except Exception as e:
            logger.error(f"❌ 最終摘要生成失敗: {e}")
    
    async def _update_passthrough_file_with_mockup(self, processed_data: List[Dict], csv_file_path: str):
        """
        更新對應的 Passthrough Excel 文件，用 mockup 調整後的數據覆蓋原始金額
        
        Args:
            processed_data: mockup 處理後的數據
            csv_file_path: 原始 CSV 文件路徑
        """
        try:
            import glob
            import os
            import pandas as pd
            
            if not csv_file_path or not csv_file_path.endswith('.csv'):
                logger.warning(f"⚠️ 非 CSV 文件，跳過 Passthrough 更新: {csv_file_path}")
                return
            
            # 從 CSV 文件名推導對應的 Passthrough Excel 文件
            csv_name = os.path.basename(csv_file_path)
            base_name = csv_name.replace('.csv', '')
            
            # 查找對應的 Passthrough Excel 文件
            passthrough_pattern = f"output/Passthrough_{base_name}_*.xlsx"
            passthrough_files = glob.glob(passthrough_pattern)
            
            if not passthrough_files:
                logger.warning(f"⚠️ 未找到對應的 Passthrough 文件，模式: {passthrough_pattern}")
                return
            
            # 使用最新的文件
            passthrough_file = max(passthrough_files, key=os.path.getmtime)
            
            logger.info(f"🔄 找到對應的 Passthrough 文件: {passthrough_file}")
            logger.info(f"📊 準備用 mockup 調整後的數據更新 Passthrough 文件")
            
            # 將 processed_data 轉換為 DataFrame
            updated_df = pd.DataFrame(processed_data)
            
            # 🔧 處理非法字符以避免 Excel 寫入錯誤
            def clean_excel_text(value):
                """清理 Excel 不支持的字符"""
                if pd.isna(value) or not isinstance(value, str):
                    return value
                # 移除 Excel 不支持的控制字符
                import re
                # 保留常見字符，移除控制字符
                cleaned = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', str(value))
                # 限制長度以避免 Excel 限制
                return cleaned[:32000] if len(cleaned) > 32000 else cleaned
            
            # 清理所有文本字段
            for column in updated_df.columns:
                if updated_df[column].dtype == 'object':
                    updated_df[column] = updated_df[column].apply(clean_excel_text)
            
            logger.info(f"🧹 已清理 Excel 非法字符")
            
            # 確保必要的欄位存在並調整欄位名稱以匹配 Passthrough 格式
            column_mapping = {
                'conversion_id': 'Conversion ID',
                'datetime_conversion': 'Datetime Conversion',  # 🔧 修復：保持統一的日期欄位名稱
                'Datetime Conversion': 'Datetime Conversion',   # 🔧 確保已存在的欄位不被改名
                'Conversion Date': 'Datetime Conversion',       # 🔧 舊格式兼容性
                'usd_sale_amount': 'Sale Amount (USD)',
                'USD Sale Amount': 'Sale Amount (USD)',  # 額外映射
                'sale_amount': 'Sale Amount (USD)',      # 額外映射
                'advertiser': 'Advertiser',
                'order_id': 'Order ID',
                'status': 'Status',
                'publisher_sub_id_1': 'Publisher Sub ID 1',
                'publisher_sub_id_2': 'Publisher Sub ID 2',
                'publisher_sub_id_3': 'Publisher Sub ID 3',
                'publisher_sub_id_4': 'Publisher Sub ID 4',
                'publisher_sub_id_5': 'Publisher Sub ID 5',
                'advertiser_sub_id_2': 'Advertiser Sub ID 2',
                'advertiser_sub_id_3': 'Advertiser Sub ID 3',
                'advertiser_sub_id_4': 'Advertiser Sub ID 4',
                'advertiser_sub_id_5': 'Advertiser Sub ID 5',
                'partner': 'Partner',
                'platform': 'Platform'
            }
            
            # 重命名欄位以匹配 Passthrough 格式
            logger.info(f"🔍 處理前欄位: {list(updated_df.columns)}")
            
            mapped_columns = []
            for old_col, new_col in column_mapping.items():
                if old_col in updated_df.columns:
                    if new_col not in updated_df.columns:
                        updated_df[new_col] = updated_df[old_col]
                        mapped_columns.append(f"{old_col} -> {new_col}")
                    else:
                        # 如果目標欄位已存在，確保使用正確的值
                        if old_col == 'usd_sale_amount' and new_col == 'Sale Amount (USD)':
                            updated_df[new_col] = updated_df[old_col]  # 強制使用 mockup 後的值
                            mapped_columns.append(f"{old_col} -> {new_col} (強制覆蓋)")
            
            logger.info(f"🔄 欄位映射: {mapped_columns}")
            logger.info(f"🔍 處理後欄位: {list(updated_df.columns)}")
            
            # 檢查關鍵金額欄位
            if 'Sale Amount (USD)' in updated_df.columns:
                sample_amounts = updated_df['Sale Amount (USD)'].head(3).tolist()
                logger.info(f"💰 金額樣本 (前3筆): {sample_amounts}")
            else:
                logger.warning(f"⚠️ 未找到 Sale Amount (USD) 欄位！")
            
            # 確保 Source 欄位存在
            if 'Source' not in updated_df.columns and 'Publisher Sub ID 1' in updated_df.columns:
                updated_df['Source'] = updated_df['Publisher Sub ID 1']
            
            # 備份原始文件
            backup_path = passthrough_file.replace('.xlsx', '_backup.xlsx')
            import shutil
            shutil.copy2(passthrough_file, backup_path)
            logger.info(f"💾 已備份原始文件到: {backup_path}")
            
            # 選擇 Passthrough 格式需要的欄位
            passthrough_columns = [
                'Conversion ID', 'Datetime Conversion', 'Advertiser', 'Order ID', 
                'Sale Amount (USD)', 'Publisher Sub ID 1', 'Status', 
                'Publisher Sub ID 2', 'Publisher Sub ID 3', 'Publisher Sub ID 4', 
                'Publisher Sub ID 5', 'Advertiser Sub ID 2', 'Advertiser Sub ID 3', 
                'Advertiser Sub ID 4', 'Advertiser Sub ID 5', 'Partner', 'Source'
            ]
            
            # 只保留存在的欄位
            available_columns = [col for col in passthrough_columns if col in updated_df.columns]
            final_df = updated_df[available_columns].copy()
            
            logger.info(f"📋 更新欄位: {available_columns}")
            
            # 用 mockup 調整後的數據覆蓋原始 Passthrough 文件
            with pd.ExcelWriter(passthrough_file, engine='openpyxl') as writer:
                final_df.to_excel(writer, sheet_name='Data', index=False)
            
            logger.info(f"✅ 成功更新 Passthrough 文件，現在包含 mockup 調整後的金額")
            logger.info(f"🎯 Reporter Agent 現在將讀取到正確的 mockup 後金額")
            
            # 驗證更新
            verify_df = pd.read_excel(passthrough_file, sheet_name='Data')
            if 'Partner' in verify_df.columns and 'Sale Amount (USD)' in verify_df.columns:
                rampup_data = verify_df[verify_df['Partner'] == 'RAMPUP']
                if len(rampup_data) > 0:
                    rampup_total = rampup_data['Sale Amount (USD)'].sum()
                    logger.info(f"✅ 驗證：更新後 RAMPUP 總金額 = ${rampup_total:,.2f}")
            
        except Exception as e:
            logger.error(f"❌ 更新 Passthrough 文件失敗: {e}")
            import traceback
            logger.error(f"錯誤詳情: {traceback.format_exc()}")

    def _classify_partner_by_source(self, source: str) -> str:
        """根據 source 值分類 Partner"""
        if pd.isna(source) or str(source).strip() == '':
            return 'Unknown'
        
        source_str = str(source).strip()
        
        # 使用 config.py 中的 PARTNER_SOURCES_MAPPING 進行分類
        import re
        import config
        
        for partner_name, partner_config in config.PARTNER_SOURCES_MAPPING.items():
            pattern = partner_config.get('pattern', '')
            if pattern:
                try:
                    if re.search(pattern, source_str):
                        return partner_name
                except re.error:
                    continue
        
        return 'Unknown'
    
    async def _apply_mockup_processing(self, conversions: List[Dict], platform: str) -> List[Dict]:
        """
        應用Mockup數據處理 - 根據Partner特定配置
        
        Args:
            conversions: 原始轉化數據列表
            platform: 平台名稱
            
        Returns:
            List[Dict]: 處理後的轉化數據列表
        """
        try:
            # 從config獲取Partner特定的mockup倍數
            import config
            from config import get_partner_mockup_multiplier
            
            logger.info(f"🔄 正在應用Mockup處理...")
            
            processed_conversions = []
            original_total = 0
            adjusted_total = 0
            partner_multipliers = {}  # 記錄每個Partner使用的倍數
            partner_stats = {}  # 記錄每個Partner的統計
            
            for conv in conversions:
                # 創建處理後的轉化數據副本
                processed_conv = conv.copy()
                
                # 獲取Partner信息 - 支持大小寫不敏感
                partner = conv.get('Partner') or conv.get('partner', platform)
                
                # 根據Partner獲取特定的mockup倍數
                if partner and partner.upper() in ['RAMPUP', 'DEEPLEAPER', 'TESTPARTNER', 'MKK', 'MP', 'FTK', 'BYTEC']:
                    mockup_multiplier = get_partner_mockup_multiplier(partner.upper())
                    partner_multipliers[partner] = mockup_multiplier
                else:
                    # 如果無法確定Partner，使用默認倍數
                    mockup_multiplier = getattr(config, 'MOCKUP_MULTIPLIER', 0.9)
                    partner_multipliers[partner] = mockup_multiplier
                
                # 初始化Partner統計
                if partner not in partner_stats:
                    partner_stats[partner] = {
                        'original_amount': 0,
                        'adjusted_amount': 0,
                        'count': 0
                    }
                
                # 處理金額欄位 - 支持多種欄位名稱（包括映射後的字段名）
                amount_fields = [
                    'usd_sale_amount', 'conversion_amount', 'sale_amount', 'Sale Amount (USD)',
                    'USD Sale Amount',  # 字段映射後的名稱
                    'Local Sale Amount', 'amount', 'Amount'  # 其他可能的名稱
                ]
                original_amount = 0
                amount_field_used = None
                
                for field in amount_fields:
                    if field in conv and conv[field] is not None:
                        # 確保金額不為 None 且可以轉換為數字
                        try:
                            amount_value = float(conv[field])
                            if amount_value >= 0:  # 允許 0 金額，只排除負數
                                original_amount = amount_value
                                amount_field_used = field
                                break
                        except (ValueError, TypeError):
                            continue
                
                if original_amount:
                    adjusted_amount = round(original_amount * mockup_multiplier, 2)
                    # 更新所有相關的欄位
                    for field in amount_fields:
                        if field in processed_conv:
                            processed_conv[field] = adjusted_amount
                    
                    original_total += original_amount
                    adjusted_total += adjusted_amount
                    
                    # 更新Partner統計
                    partner_stats[partner]['original_amount'] += original_amount
                    partner_stats[partner]['adjusted_amount'] += adjusted_amount
                    partner_stats[partner]['count'] += 1
                    
                    logger.debug(f"Mockup處理: {partner} - {amount_field_used}: ${original_amount} -> ${adjusted_amount} (倍數: {mockup_multiplier})")
                
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
            
            # 詳細日志 - 增強版本
            logger.info(f"📊 Mockup處理統計:")
            logger.info(f"   - 處理記錄數: {len(processed_conversions)}")
            logger.info(f"   - 原始總金額: ${original_total:,.2f} USD")
            logger.info(f"   - 調整後總金額: ${adjusted_total:,.2f} USD")
            logger.info(f"   - 金額變化: ${adjusted_total - original_total:+,.2f} USD")
            if original_total > 0:
                change_percentage = ((adjusted_total - original_total) / original_total) * 100
                logger.info(f"   - 金額變化百分比: {change_percentage:+.2f}%")
            logger.info(f"   - Partner倍數分布: {partner_multipliers}")
            
            # 打印每個Partner的詳細統計 - 增強版本
            logger.info("📊 Partner詳細統計 (Mockup前後金額):")
            for partner, stats in partner_stats.items():
                if stats['count'] > 0:
                    original = stats['original_amount']
                    adjusted = stats['adjusted_amount']
                    multiplier = partner_multipliers.get(partner, 1.0)
                    change = adjusted - original
                    change_pct = ((adjusted - original) / original * 100) if original > 0 else 0
                    
                    # 驗證配置一致性
                    expected_multiplier = get_partner_mockup_multiplier(partner.upper() if partner else 'Unknown')
                    
                    logger.info(f"   💰 {partner}:")
                    logger.info(f"      📈 原始金額: ${original:,.2f} USD")
                    logger.info(f"      📈 調整後金額: ${adjusted:,.2f} USD")
                    logger.info(f"      📊 金額變化: ${change:+,.2f} USD ({change_pct:+.2f}%)")
                    logger.info(f"      ⚙️  實際倍數: {multiplier}")
                    logger.info(f"      ⚙️  預期倍數: {expected_multiplier} (來自 config.py)")
                    logger.info(f"      📋 記錄數: {stats['count']}")
                    
                    # ⚠️ 配置一致性警告
                    if abs(multiplier - expected_multiplier) > 0.001:  # 允許微小的浮點誤差
                        logger.warning(f"⚠️  警告: Partner '{partner}' 的實際 mockup 倍數 ({multiplier}) 與 config.py 配置 ({expected_multiplier}) 不一致！")
                        logger.warning(f"      請檢查 config.py 中的 PARTNER_SOURCES_MAPPING['{partner}']['mockup_multiplier'] 配置")
            
            # 輸出 Mockup 配置總結
            logger.info("🔧 當前 Mockup 配置 (來自 config.py):")
            all_partners = ['RAMPUP', 'DeepLeaper', 'FTK', 'MP', 'MKK', 'TestPartner', 'ByteC']
            for p in all_partners:
                expected_mult = get_partner_mockup_multiplier(p)
                logger.info(f"   📊 {p}: {expected_mult} ({expected_mult*100:.0f}%)")
            
            # 最終警告檢查
            config_mismatch_detected = False
            for partner, multiplier in partner_multipliers.items():
                expected_multiplier = get_partner_mockup_multiplier(partner.upper() if partner else 'Unknown')
                if abs(multiplier - expected_multiplier) > 0.001:
                    config_mismatch_detected = True
                    break
            
            if config_mismatch_detected:
                logger.error("🚨 嚴重警告: 檢測到 Mockup 配置不一致!")
                logger.error("    - 實際使用的倍數與 config.py 配置不符")
                logger.error("    - 請檢查上述詳細統計中標記為 ⚠️ 警告 的 Partner")
                logger.error("    - 確保所有 Partner 的 mockup_multiplier 配置正確")
            else:
                logger.info("✅ Mockup 配置一致性檢查通過")
            
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
            import re
            
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
            
            # 檢測平台並應用字段映射
            platform = self.detect_platform_from_filename(latest_file)
            if platform == 'UNKNOWN':
                platform = self.detect_platform_from_content(df)
            
            logger.info(f"🔍 檢測到平台: {platform}")
            
            # 使用字段映射管理器進行數據轉換
            try:
                # 將内部平台标识符映射回字段映射管理器使用的标识符
                platform_mapping = {
                    'AT_BM': 'access_trade',
                    'IA_BM': 'involve_asia',
                    'IA_MB': 'involve_asia',
                    'IA_OT': 'involve_asia',
                    'SHOPEE': 'shopee',
                    'TIKTOK_SHOP': 'tiktok_shop',
                    'LS_MB': 'linkshare',
                    'LS_BM': 'linkshare'
                }
                
                mapping_platform = platform_mapping.get(platform, platform.lower())
                
                # 使用字段映射管理器進行映射
                mapped_df, mapping_info = self.field_mapping_manager.map_dataframe_columns(df, mapping_platform)
                
                if not mapped_df.empty:
                    logger.info(f"✅ 使用字段映射管理器成功映射 {len(mapping_info['mapped_columns'])} 個欄位")
                    logger.info(f"📋 映射欄位: {[m['source'] + ' -> ' + m['target'] for m in mapping_info['mapped_columns']]}")
                    if mapping_info['unmapped_columns']:
                        logger.warning(f"⚠️ 未映射欄位: {mapping_info['unmapped_columns']}")
                    
                    # 使用映射後的DataFrame
                    df = mapped_df
                else:
                    logger.warning(f"⚠️ 字段映射失敗，使用原始數據")
                    
            except Exception as e:
                logger.error(f"❌ 字段映射失敗: {e}")
                logger.info("📋 使用原始數據格式")
            
            # 轉換為DMP Agent所需的格式
            conversions = []
            for _, row in df.iterrows():
                # 獲取Source信息
                source = row.get('Publisher Sub ID 1', '')
                
                # 根據Source分類Partner
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
                
                # 優先使用文件中已有的 Partner 欄位，如果不存在則重新計算
                partner = row.get('Partner', classify_partner(source))
                
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
                    'advertiser': row.get('Advertiser', ''),
                    'advertiser_name': row.get('Advertiser Name', ''),
                    'campaign_name': row.get('Campaign Name', ''),
                    'tracking_id': row.get('Tracking ID', ''),
                    'platform': 'FileImport',  # 標記為文件導入
                    'data_source': 'file',
                    'partner': partner  # 添加Partner信息
                }
                conversions.append(conversion)
            
            # 統計Partner分布
            partner_stats = {}
            for conv in conversions:
                partner = conv.get('partner', 'Unknown')
                partner_stats[partner] = partner_stats.get(partner, 0) + 1
            
            logger.info(f"✅ 數據轉換完成: {len(conversions):,} 條轉化記錄")
            logger.info(f"📊 數據總金額: ${sum(c.get('usd_sale_amount', 0) for c in conversions):,.2f} USD")
            logger.info(f"📊 Partner分布: {partner_stats}")
            
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
        
        # 處理多partners參數
        partner_filter = None
        partner_list = []
        if args.partner:
            if args.partner.upper() == "ALL":
                partner_filter = None
                logger.info("🎯 處理所有Partners (ALL)")
            else:
                # 解析逗號分隔的partners
                partner_list = [p.strip() for p in args.partner.split(',') if p.strip()]
                if len(partner_list) == 1:
                    partner_filter = partner_list[0]
                    logger.info(f"🎯 處理單個Partner: {partner_filter}")
                else:
                    partner_filter = args.partner  # 保持原始字符串格式
                    logger.info(f"🎯 處理多個Partners: {', '.join(partner_list)}")
        
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
  python agents/data_dmp_agent/main.py --query --days-ago 1 --partner DeepLeaper,RAMPUP
  
  # 數據刪除模式 (危險操作)
  python agents/data_dmp_agent/main.py --delete --start-date 2025-07-17 --end-date 2025-07-17
  python agents/data_dmp_agent/main.py --delete --start-date 2025-07-15 --end-date 2025-07-20
  
  # Passthrough模式和文件數據源
  python agents/data_dmp_agent/main.py --days-ago 2 --passthrough --data-source file --self-email
  
  # 🔄 Phase 2: 檔案處理模式
  python agents/data_dmp_agent/main.py --import file1.csv,file2.xlsx --passthrough
  python agents/data_dmp_agent/main.py --import-folder input --passthrough
  python agents/data_dmp_agent/main.py --import-folder input --force-platform IA_OT --passthrough
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
                       help='指定partner名稱 (支持逗号分隔多个partners，例如: DeepLeaper,RAMPUP 或 ALL)')
    
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
    
    # 🔄 Phase 2: 多檔案處理參數
    parser.add_argument('--import', dest='import_files', type=str,
                       help='要處理的檔案列表（逗號分隔）')
    parser.add_argument('--import-folder', dest='import_folder', type=str,
                       help='處理指定資料夾下的所有檔案')
    parser.add_argument('--force-platform', dest='force_platform', type=str,
                       help='強制指定平台類型 (AT_BM, IA_BM, IA_OT, IA_MB)')
    
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
        
        # 🔄 Phase 2: 檔案處理模式
        if args.import_files or args.import_folder:
            logger.info("=" * 60)
            logger.info("🚀 DMP-Agent 檔案處理流程")
            logger.info("=" * 60)
            
            file_paths = []
            
            if args.import_files:
                # 處理多檔案參數
                file_paths = [f.strip() for f in args.import_files.split(',')]
                logger.info(f"📁 處理檔案列表: {len(file_paths)} 個檔案")
                for file_path in file_paths:
                    logger.info(f"   - {file_path}")
            
            elif args.import_folder:
                # 處理資料夾參數
                logger.info(f"📁 處理資料夾: {args.import_folder}")
                file_paths = agent.get_files_from_folder(args.import_folder)
                
                if not file_paths:
                    logger.error(f"❌ 資料夾 {args.import_folder} 中沒有找到可處理的檔案")
                    return
            
            # 設置強制平台（如果指定）
            if args.force_platform:
                agent.force_platform = args.force_platform
                logger.info(f"🔧 強制指定平台: {args.force_platform}")
            
            # 處理檔案 - 默认启用 passthrough
            result = await agent.process_multiple_files(file_paths, True)
            
            # 打印結果
            success_count = sum(1 for r in result['individual_results'] if r['success'])
            logger.info(f"✅ 檔案處理完成: {success_count}/{len(file_paths)} 成功")
            logger.info(f"📊 合併後總記錄數: {result['total_records']} 條")
            
            if result['merged_filename']:
                logger.info(f"📁 合併檔案: {result['merged_filename']}")
            
            logger.info("🔄 Passthrough模式: 數據不會插入Cloud SQL")
            
            return
        
        # 主要處理流程 (API 模式)
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
        
        # 🔄 Phase 2: 顯示新功能參數狀態
        logger.info("🔄 Passthrough模式: 啟用 - 數據不會插入Cloud SQL")
        
        if args.self_email:
            logger.info("📧 Self-email模式: 啟用 - 參數已從Data Input Agent傳遞")
        
        logger.info("=" * 60)
        
        # 處理平台數據 - 默认启用 passthrough
        result = await agent.process_platform_data(args.platform, args.days_ago, True, args.data_source, args.start_date, args.end_date)
        
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