#!/usr/bin/env python3
"""
Excel字符清理工具
統一處理Excel不支持的字符，確保跨語言數據的正確顯示
"""

import re
import unicodedata
from typing import Any, List, Union


class ExcelCharacterCleaner:
    """Excel字符清理器 - 處理各種語言的特殊字符"""
    
    def __init__(self):
        """初始化字符清理器"""
        # 預編譯正則表達式以提高性能
        self.control_chars_pattern = re.compile(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]')
        self.zero_width_pattern = re.compile(r'[\u200B-\u200D\uFEFF]')
        self.multiple_underscore_pattern = re.compile(r'_+')
        
        # Excel工作表名稱不支持的字符
        self.sheet_invalid_chars = re.compile(r'[\\/:*?"<>|]')
    
    def is_acceptable_char(self, char: str) -> bool:
        """
        判斷字符是否為Excel可接受的字符
        
        保留以下字符範圍：
        - 基本ASCII可打印字符 (0x20-0x7E)
        - 拉丁字母擴展 (0x00A0-0x024F) - 包含越南語、法語等
        - 拉丁字母擴展額外部分 (0x1E00-0x1EFF) - 越南語專用重音符號
        - 中日韓表意文字 (0x4E00-0x9FFF)
        - 韓文字母 (0xAC00-0xD7AF)
        - 平假名和片假名 (0x3040-0x309F, 0x30A0-0x30FF)
        - 常用標點和符號 (0x2000-0x206F, 0x20A0-0x20CF, 0x2100-0x214F)
        """
        # 基本ASCII可打印字符
        if '\x20' <= char <= '\x7E':
            return True
        
        # 拉丁字母擴展 (包含越南語、法語、德語等)
        if '\u00A0' <= char <= '\u024F':
            return True
        
        # 拉丁字母擴展額外部分 (越南語專用重音符號)
        if '\u1E00' <= char <= '\u1EFF':
            return True
        
        # 中日韓表意文字
        if '\u4E00' <= char <= '\u9FFF':
            return True
        
        # 韓文字母
        if '\uAC00' <= char <= '\uD7AF':
            return True
        
        # 平假名和片假名
        if '\u3040' <= char <= '\u309F' or '\u30A0' <= char <= '\u30FF':
            return True
        
        # 常用標點符號
        if '\u2000' <= char <= '\u206F':  # 一般標點
            return True
        
        # 貨幣符號
        if '\u20A0' <= char <= '\u20CF':
            return True
        
        # 字母符號
        if '\u2100' <= char <= '\u214F':
            return True
        
        return False
    
    def clean_cell_value(self, value: Any) -> Any:
        """
        清理單個Excel單元格的值
        
        Args:
            value: 原始值 (可以是字符串、數字、None等)
            
        Returns:
            清理後的值
        """
        if value is None:
            return None
        
        if isinstance(value, (int, float)):
            return value
        
        # 轉換為字符串進行處理
        text = str(value)
        
        # 步驟1: 移除控制字符
        text = self.control_chars_pattern.sub('', text)
        
        # 步驟2: 移除零寬字符
        text = self.zero_width_pattern.sub('', text)
        
        # 步驟3: Unicode標準化 (NFD -> NFC)
        text = unicodedata.normalize('NFC', text)
        
        # 步驟4: 只保留可接受的字符
        cleaned_chars = []
        for char in text:
            if self.is_acceptable_char(char):
                cleaned_chars.append(char)
            else:
                cleaned_chars.append('_')
        
        text = ''.join(cleaned_chars)
        
        # 步驟5: 清理多餘的下劃線和空格
        text = self.multiple_underscore_pattern.sub('_', text)  # 多個下劃線合併為一個
        text = text.strip('_').strip()  # 移除首尾的下劃線和空格
        
        # 步驟6: 如果完全清空了，提供預設值
        if not text:
            text = "Unknown"
        
        return text
    
    def clean_row_data(self, row: Union[List[Any], tuple]) -> List[Any]:
        """
        清理Excel行數據
        
        Args:
            row: 行數據 (列表或元組)
            
        Returns:
            清理後的行數據
        """
        return [self.clean_cell_value(cell) for cell in row]
    
    def clean_sheet_name(self, name: str) -> str:
        """
        清理Excel工作表名稱
        
        Excel工作表名稱限制：
        - 不能超過31個字符
        - 不能包含: \\ / : * ? " < > |
        - 不能為空或只包含空格
        - 不能以單引號開頭或結尾
        
        Args:
            name: 原始工作表名稱
            
        Returns:
            清理後的工作表名稱
        """
        if not name or not str(name).strip():
            return "Unknown"
        
        # 轉換為字符串並去除前後空格
        clean_name = str(name).strip()
        
        # 先使用通用字符清理
        clean_name = self.clean_cell_value(clean_name)
        
        # 替換Excel工作表名稱不支持的字符
        clean_name = self.sheet_invalid_chars.sub('_', clean_name)
        
        # 限制長度為31個字符
        if len(clean_name) > 31:
            clean_name = clean_name[:31]
        
        # 確保不以單引號開頭或結尾
        clean_name = clean_name.strip("'")
        
        # 如果清理後為空，使用默認名稱
        if not clean_name:
            clean_name = "Unknown"
        
        return clean_name


# 全局實例，方便在整個項目中使用
excel_cleaner = ExcelCharacterCleaner()


def clean_for_excel(value: Any) -> Any:
    """便捷函數：清理單個值以用於Excel"""
    return excel_cleaner.clean_cell_value(value)


def clean_row_for_excel(row: Union[List[Any], tuple]) -> List[Any]:
    """便捷函數：清理行數據以用於Excel"""
    return excel_cleaner.clean_row_data(row)


def clean_sheet_name_for_excel(name: str) -> str:
    """便捷函數：清理工作表名稱以用於Excel"""
    return excel_cleaner.clean_sheet_name(name)


# 向後兼容的函數名
def _clean_row_data(row: Union[List[Any], tuple]) -> List[Any]:
    """向後兼容：舊的函數名"""
    return clean_row_for_excel(row)


def _clean_sheet_name(name: str) -> str:
    """向後兼容：舊的函數名"""
    return clean_sheet_name_for_excel(name)


if __name__ == "__main__":
    # 測試用例
    cleaner = ExcelCharacterCleaner()
    
    test_cases = [
        "Điện thoại iPhone 15 Pro Max",  # 越南語
        "複雜的中文產品名稱",  # 中文
        "Product with \x00\x08 control chars",  # 控制字符
        "Emoji: 🎉🚀💯",  # Emoji
        "Zero-width: \u200B\u200C test",  # 零寬字符
        "",  # 空字符串
        None,  # None值
    ]
    
    print("🧪 測試Excel字符清理器:")
    for i, test in enumerate(test_cases):
        cleaned = cleaner.clean_cell_value(test)
        print(f"{i+1}. 原始: {test!r}")
        print(f"   清理: {cleaned!r}")
        print() 