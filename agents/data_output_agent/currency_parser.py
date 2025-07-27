"""
向量化金額解析模組
提供高效的金額字符串解析功能，替代低效的 apply(parse_currency) 方法
"""

import pandas as pd
import numpy as np
import re
from typing import Union, List
import logging

logger = logging.getLogger(__name__)


class CurrencyParser:
    """向量化金額解析器"""
    
    def __init__(self):
        """初始化金額解析器"""
        # 預編譯正則表達式用於清理 - 支援更多格式
        self._currency_clean_pattern = re.compile(r'[\$,\s]+')  # 移除 $, 逗號, 空格
        self._non_numeric_pattern = re.compile(r'[^\d.-]+')     # 移除非數字字符（保留數字、點、負號）
        
        # 統計信息
        self._stats = {
            'parsed_count': 0,
            'error_count': 0,
            'null_count': 0
        }
    
    def parse_currency_series(self, series: pd.Series) -> pd.Series:
        """
        向量化解析金額 Series
        
        Args:
            series: 包含金額數據的 pandas Series
            
        Returns:
            解析後的數值 Series
        """
        if series.empty:
            return pd.Series(dtype=float)
        
        logger.debug(f"開始解析金額 Series，共 {len(series)} 個值")
        
        # 統計 null 值
        null_mask = series.isnull()
        null_count = null_mask.sum()
        self._stats['null_count'] += null_count
        
        # 處理 null 值：填充為 '0'
        cleaned_series = series.fillna('0')
        
        # 轉換為字符串（向量化操作）
        str_series = cleaned_series.astype(str)
        
        # 步驟1：移除常見的貨幣符號和空格
        step1 = str_series.str.replace(self._currency_clean_pattern, '', regex=True)
        
        # 步驟2：移除其他非數字字符（但保留數字、點、負號）
        step2 = step1.str.replace(self._non_numeric_pattern, '', regex=True)
        
        # 步驟3：標記無效的字符串（沒有數字的將變成空字符串）
        # 保留空字符串作為無效標記，等待 pd.to_numeric 處理
        
        # 向量化轉換為數值
        numeric_series = pd.to_numeric(step2, errors='coerce')
        
        # 處理轉換失敗的值：填充為 0
        error_mask = numeric_series.isnull()
        error_count = error_mask.sum()
        self._stats['error_count'] += error_count
        
        # 將 NaN 替換為 0.0
        result_series = numeric_series.fillna(0.0)
        
        # 統計成功解析的數量（排除原本的 null 值）
        success_count = len(result_series) - error_count - null_count
        self._stats['parsed_count'] += success_count
        
        if error_count > 0:
            logger.warning(f"金額解析完成：成功 {success_count}，失敗 {error_count}，空值 {null_count}")
        else:
            logger.debug(f"金額解析完成：成功 {success_count}，空值 {null_count}")
        
        return result_series
    
    def parse_currency_value(self, value: Union[str, float, int, None]) -> float:
        """
        解析單個金額值
        
        Args:
            value: 金額值
            
        Returns:
            解析後的數值
        """
        if pd.isna(value) or value is None:
            self._stats['null_count'] += 1
            return 0.0
        
        try:
            # 如果已經是數值，直接返回
            if isinstance(value, (int, float)):
                self._stats['parsed_count'] += 1
                return float(value)
            
            # 轉換為字符串並清理
            str_value = str(value)
            
            # 移除貨幣符號和空格
            cleaned_value = self._currency_clean_pattern.sub('', str_value)
            
            # 移除其他非數字字符
            final_value = self._non_numeric_pattern.sub('', cleaned_value)
            
            # 處理空字符串 - 標記為無效
            if not final_value:
                self._stats['error_count'] += 1
                return 0.0
            
            # 轉換為浮點數
            result = float(final_value)
            self._stats['parsed_count'] += 1
            return result
            
        except (ValueError, TypeError) as e:
            logger.warning(f"金額解析失敗: '{value}' -> {str(e)}")
            self._stats['error_count'] += 1
            return 0.0
    
    def parse_currency_list(self, values: List[Union[str, float, int, None]]) -> List[float]:
        """
        解析金額值列表
        
        Args:
            values: 金額值列表
            
        Returns:
            解析後的數值列表
        """
        if not values:
            return []
        
        # 轉換為 Series 進行向量化處理
        series = pd.Series(values)
        result_series = self.parse_currency_series(series)
        
        return result_series.tolist()
    
    def get_stats(self) -> dict:
        """獲取解析統計信息"""
        total_processed = self._stats['parsed_count'] + self._stats['error_count'] + self._stats['null_count']
        success_rate = (self._stats['parsed_count'] / total_processed * 100) if total_processed > 0 else 0
        
        return {
            'total_processed': total_processed,
            'parsed_count': self._stats['parsed_count'],
            'error_count': self._stats['error_count'],
            'null_count': self._stats['null_count'],
            'success_rate_percent': round(success_rate, 2)
        }
    
    def reset_stats(self):
        """重置統計信息"""
        self._stats = {
            'parsed_count': 0,
            'error_count': 0,
            'null_count': 0
        }


# 全局解析器實例
_global_currency_parser = None


def get_currency_parser() -> CurrencyParser:
    """獲取全局金額解析器實例"""
    global _global_currency_parser
    if _global_currency_parser is None:
        _global_currency_parser = CurrencyParser()
    return _global_currency_parser


def parse_currency_series(series: pd.Series) -> pd.Series:
    """
    便捷函數：向量化解析金額 Series
    
    Args:
        series: 包含金額數據的 pandas Series
        
    Returns:
        解析後的數值 Series
    """
    parser = get_currency_parser()
    return parser.parse_currency_series(series)


def parse_currency_value(value: Union[str, float, int, None]) -> float:
    """
    便捷函數：解析單個金額值
    
    Args:
        value: 金額值
        
    Returns:
        解析後的數值
    """
    parser = get_currency_parser()
    return parser.parse_currency_value(value)


def reset_currency_parser():
    """重置全局金額解析器（主要用於測試）"""
    global _global_currency_parser
    _global_currency_parser = None


# 向後兼容的函數別名
def parse_currency(value: Union[str, float, int, None]) -> float:
    """向後兼容的金額解析函數"""
    return parse_currency_value(value) 