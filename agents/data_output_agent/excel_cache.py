"""
Excel 緩存機制模組
提供高效的 Excel 文件讀取和緩存功能
"""

import time
import os
import pandas as pd
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class ExcelCache:
    """Excel 文件緩存管理器"""
    
    def __init__(self, cache_ttl: int = 300):
        """
        初始化 Excel 緩存
        
        Args:
            cache_ttl: 緩存生存時間（秒），默認 5 分鐘
        """
        self._cache: Dict[str, Dict[str, pd.DataFrame]] = {}
        self._cache_timestamps: Dict[str, float] = {}
        self._cache_ttl = cache_ttl
        self._cache_stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0
        }
    
    def get_sheets_data(self, file_path: str) -> Dict[str, pd.DataFrame]:
        """
        獲取 Excel 文件的所有 sheets 數據
        
        Args:
            file_path: Excel 文件路徑
            
        Returns:
            字典，key 為 sheet 名稱，value 為 DataFrame
        """
        if not file_path or not os.path.exists(file_path):
            import traceback
            tb = traceback.format_stack()
            logger.warning(f"Excel 文件不存在: {file_path}\n调用栈:\n{''.join(tb)}")
            return {}
        
        # 檢查緩存
        if self._is_cache_valid(file_path):
            self._cache_stats['hits'] += 1
            logger.debug(f"Excel 緩存命中: {os.path.basename(file_path)}")
            return self._cache[file_path]
        
        # 緩存未命中，重新讀取
        self._cache_stats['misses'] += 1
        logger.debug(f"Excel 緩存未命中，讀取文件: {os.path.basename(file_path)}")
        
        sheets_data = self._read_all_sheets(file_path)
        
        # 更新緩存
        self._cache[file_path] = sheets_data
        self._cache_timestamps[file_path] = time.time()
        
        return sheets_data
    
    def get_sheet_data(self, file_path: str, sheet_name: str) -> Optional[pd.DataFrame]:
        """
        獲取單個 sheet 的數據
        
        Args:
            file_path: Excel 文件路徑
            sheet_name: Sheet 名稱
            
        Returns:
            DataFrame 或 None
        """
        sheets_data = self.get_sheets_data(file_path)
        return sheets_data.get(sheet_name)
    
    def _is_cache_valid(self, file_path: str) -> bool:
        """檢查緩存是否有效"""
        if file_path not in self._cache:
            return False
        
        current_time = time.time()
        cache_time = self._cache_timestamps.get(file_path, 0)
        
        return (current_time - cache_time) < self._cache_ttl
    
    def _read_all_sheets(self, file_path: str) -> Dict[str, pd.DataFrame]:
        """
        一次性讀取 Excel 文件的所有 sheets
        
        Args:
            file_path: Excel 文件路徑
            
        Returns:
            字典，key 為 sheet 名稱，value 為 DataFrame
        """
        sheets_data = {}
        
        try:
            # 使用 ExcelFile 一次性讀取所有 sheets 信息
            with pd.ExcelFile(file_path) as excel_file:
                for sheet_name in excel_file.sheet_names:
                    try:
                        df = pd.read_excel(file_path, sheet_name=sheet_name)
                        sheets_data[sheet_name] = df
                        logger.debug(f"成功讀取 Sheet '{sheet_name}': {len(df)} 行")
                    except Exception as e:
                        logger.warning(f"讀取 Sheet '{sheet_name}' 失敗: {str(e)}")
                        sheets_data[sheet_name] = pd.DataFrame()
            
            logger.info(f"成功讀取 Excel 文件: {os.path.basename(file_path)}, {len(sheets_data)} 個 sheets")
            
        except Exception as e:
            logger.error(f"讀取 Excel 文件失敗 {os.path.basename(file_path)}: {str(e)}")
            sheets_data = {}
        
        return sheets_data
    
    def clear_cache(self, file_path: Optional[str] = None):
        """
        清除緩存
        
        Args:
            file_path: 特定文件路徑，如果為 None 則清除所有緩存
        """
        if file_path:
            if file_path in self._cache:
                del self._cache[file_path]
                del self._cache_timestamps[file_path]
                self._cache_stats['evictions'] += 1
                logger.debug(f"清除緩存: {os.path.basename(file_path)}")
        else:
            evicted_count = len(self._cache)
            self._cache.clear()
            self._cache_timestamps.clear()
            self._cache_stats['evictions'] += evicted_count
            logger.debug("清除所有緩存")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """獲取緩存統計信息"""
        total_requests = self._cache_stats['hits'] + self._cache_stats['misses']
        hit_rate = (self._cache_stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'hits': self._cache_stats['hits'],
            'misses': self._cache_stats['misses'],
            'evictions': self._cache_stats['evictions'],
            'total_requests': total_requests,
            'hit_rate_percent': round(hit_rate, 2),
            'cached_files': len(self._cache)
        }
    
    def cleanup_expired_cache(self):
        """清理過期的緩存項目"""
        current_time = time.time()
        expired_files = []
        
        for file_path, cache_time in self._cache_timestamps.items():
            if (current_time - cache_time) >= self._cache_ttl:
                expired_files.append(file_path)
        
        for file_path in expired_files:
            self.clear_cache(file_path)
        
        if expired_files:
            logger.debug(f"清理 {len(expired_files)} 個過期緩存項目")


# 全局緩存實例
_global_excel_cache = None


def get_excel_cache() -> ExcelCache:
    """獲取全局 Excel 緩存實例"""
    global _global_excel_cache
    if _global_excel_cache is None:
        _global_excel_cache = ExcelCache()
    return _global_excel_cache


def reset_excel_cache():
    """重置全局 Excel 緩存（主要用於測試）"""
    global _global_excel_cache
    _global_excel_cache = None 