#!/usr/bin/env python3
"""
Platform Detector - 平台識別器
支持基於文件名和數據內容的平台自動識別
"""

import os
import re
import logging
from typing import Dict, List, Optional, Any
import pandas as pd

class PlatformDetector:
    """平台識別器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 平台識別規則
        self.platform_rules = {
            "involve_asia": {
                "filename_patterns": [
                    r"_ia_", r"_IA_", r"involve_asia", r"Involve Asia",
                    r"publisher-conversion-report.*_IA_", r"_IA_MB\.csv", r"ia_bm", r"IA_BM"
                ],
                "column_patterns": [
                    "Advertiser Name", "Campaign Name", "Offer Name",
                    "Sale Amount (USD)", "Conversion Date", "Publisher ID"
                ],
                "keywords": ["involve", "asia", "ia_bm", "ia_mb"]
            },
            "shopee": {
                "filename_patterns": [
                    r"_shopee_", r"_Shopee_", r"shopee", r"Shopee",
                    r"shopee.*\.csv", r"shopee.*\.xlsx"
                ],
                "column_patterns": [
                    "Campaign Name", "Ad Group Name", "Product Name",
                    "Revenue", "Date", "Publisher ID"
                ],
                "keywords": ["shopee", "campaign", "ad group"]
            },
            "tiktok_shop": {
                "filename_patterns": [
                    r"_tiktok_", r"_TikTok_", r"tiktok", r"TikTok",
                    r"tiktok.*\.csv", r"tiktok.*\.xlsx"
                ],
                "column_patterns": [
                    "Advertiser Name", "Campaign Name", "Product Name",
                    "Revenue", "Date", "Publisher ID"
                ],
                "keywords": ["tiktok", "tiktok shop"]
            },
            "access_trade": {
                "filename_patterns": [
                    r"_at_", r"_AT_", r"access_trade", r"Access Trade",
                    r"access_trade.*\.csv", r"access_trade.*\.xlsx",
                    r"at_report.*\.csv", r"at_report.*\.xlsx",
                    r"at_data.*\.csv", r"at_data.*\.xlsx",
                    r"report_at.*\.csv", r"report_at.*\.xlsx"
                ],
                "column_patterns": [
                    "Site", "Campaign Name", "Product ID", "Total Price",
                    "Conversion Time", "aff_sub", "Transaction ID", "Status",
                    "Reward", "Conversion ID", "Click Time", "Confirmation Time"
                ],
                "keywords": ["access", "trade", "site", "campaign name", "total price"]
            },
            "linkshare": {
                "filename_patterns": [
                    r"_ls_", r"_LS_", r"linkshare", r"LinkShare",
                    r"ls_bm", r"LS_BM", r"ls_mb", r"LS_MB",
                    r".*_LS_MB\.csv", r".*_LS_BM\.csv"
                ],
                "column_patterns": [
                    "Order ID", "Product Name", "SKU", "Product ID",
                    "Price", "Quantity", "Shop name", "Creator username",
                    "Commission", "Time order created", "Platform"
                ],
                "keywords": ["linkshare", "order id", "creator username", "shop name"]
            }
        }
    
    def detect_from_filename(self, filename: str) -> Optional[str]:
        """
        基於文件名識別平台
        
        Args:
            filename: 文件名
            
        Returns:
            str: 識別出的平台名稱，如果無法識別則返回None
        """
        filename_lower = filename.lower()
        
        for platform, rules in self.platform_rules.items():
            for pattern in rules["filename_patterns"]:
                if re.search(pattern, filename_lower, re.IGNORECASE):
                    self.logger.info(f"基於文件名識別出平台: {platform} (匹配模式: {pattern})")
                    return platform
        
        # 特殊處理：基於文件名的其他規則
        if "_bm" in filename_lower or "_mb" in filename_lower:
            if "ia" in filename_lower:
                return "involve_asia"
            elif "at" in filename_lower:
                return "access_trade"
            elif "ls" in filename_lower:
                return "linkshare"
        
        self.logger.warning(f"無法從文件名識別平台: {filename}")
        return None
    
    def detect_from_content(self, df: pd.DataFrame) -> Optional[str]:
        """
        基於數據內容識別平台
        
        Args:
            df: DataFrame
            
        Returns:
            str: 識別出的平台名稱，如果無法識別則返回None
        """
        columns = [col.lower() for col in df.columns]
        
        # 計算每個平台的匹配分數
        platform_scores = {}
        
        for platform, rules in self.platform_rules.items():
            score = 0
            
            # 檢查列名匹配
            for pattern in rules["column_patterns"]:
                pattern_lower = pattern.lower()
                for col in columns:
                    if pattern_lower in col or col in pattern_lower:
                        score += 2  # 列名匹配權重較高
            
            # 檢查關鍵字匹配
            for keyword in rules["keywords"]:
                keyword_lower = keyword.lower()
                for col in columns:
                    if keyword_lower in col:
                        score += 1
            
            # 檢查數據內容特徵
            score += self._analyze_data_content(df, platform)
            
            if score > 0:
                platform_scores[platform] = score
        
        if platform_scores:
            # 選擇分數最高的平台
            best_platform = max(platform_scores, key=platform_scores.get)
            self.logger.info(f"基於內容識別出平台: {best_platform} (分數: {platform_scores[best_platform]})")
            return best_platform
        
        self.logger.warning("無法從數據內容識別平台")
        return None
    
    def _analyze_data_content(self, df: pd.DataFrame, platform: str) -> int:
        """
        分析數據內容特徵
        
        Args:
            df: DataFrame
            platform: 平台名稱
            
        Returns:
            int: 特徵分數
        """
        score = 0
        
        try:
            # 檢查數據類型特徵
            if platform == "involve_asia":
                # Involve Asia通常有金額欄位
                amount_columns = [col for col in df.columns if "amount" in col.lower() or "sale" in col.lower()]
                if amount_columns:
                    score += 1
                
                # 檢查是否有日期欄位
                date_columns = [col for col in df.columns if "date" in col.lower()]
                if date_columns:
                    score += 1
            
            elif platform == "shopee":
                # Shopee通常有Revenue欄位
                revenue_columns = [col for col in df.columns if "revenue" in col.lower()]
                if revenue_columns:
                    score += 2
                
                # 檢查是否有Product相關欄位
                product_columns = [col for col in df.columns if "product" in col.lower()]
                if product_columns:
                    score += 1
            
            elif platform == "tiktok_shop":
                # TikTok Shop特徵
                tiktok_columns = [col for col in df.columns if "tiktok" in col.lower()]
                if tiktok_columns:
                    score += 2
            
            elif platform == "access_trade":
                # Access Trade通常有Commission欄位
                commission_columns = [col for col in df.columns if "commission" in col.lower()]
                if commission_columns:
                    score += 2
            
            # 移除基本分數，只有真正匹配的欄位才會給分
            
        except Exception as e:
            self.logger.error(f"分析數據內容時出錯: {e}")
        
        return score
    
    def detect_platform(self, file_path: str = None, df: pd.DataFrame = None) -> Optional[str]:
        """
        綜合平台識別（優先文件名，其次數據內容）
        
        Args:
            file_path: 文件路徑
            df: DataFrame
            
        Returns:
            str: 識別出的平台名稱
        """
        detected_platform = None
        
        # 首先嘗試基於文件名識別
        if file_path:
            filename = os.path.basename(file_path)
            detected_platform = self.detect_from_filename(filename)
            if detected_platform:
                return detected_platform
        
        # 如果文件名無法識別，嘗試基於數據內容
        if df is not None:
            detected_platform = self.detect_from_content(df)
            if detected_platform:
                return detected_platform
        
        # 如果都無法識別，返回默認平台
        self.logger.warning("無法識別平台，使用默認平台: involve_asia")
        return "involve_asia"
    
    def get_platform_info(self, platform: str) -> Dict[str, Any]:
        """
        獲取平台信息
        
        Args:
            platform: 平台名稱
            
        Returns:
            Dict: 平台信息
        """
        if platform not in self.platform_rules:
            return {}
        
        rules = self.platform_rules[platform]
        return {
            "platform": platform,
            "filename_patterns": rules["filename_patterns"],
            "column_patterns": rules["column_patterns"],
            "keywords": rules["keywords"]
        }
    
    def get_all_platforms(self) -> List[str]:
        """獲取所有支持的平台列表"""
        return list(self.platform_rules.keys())
    
    def add_platform_rules(self, platform: str, rules: Dict[str, Any]):
        """
        添加新的平台識別規則
        
        Args:
            platform: 平台名稱
            rules: 識別規則
        """
        self.platform_rules[platform] = rules
        self.logger.info(f"已添加平台識別規則: {platform}")
    
    def validate_platform_detection(self, file_path: str, expected_platform: str) -> bool:
        """
        驗證平台識別是否正確
        
        Args:
            file_path: 文件路徑
            expected_platform: 期望的平台
            
        Returns:
            bool: 識別是否正確
        """
        detected_platform = self.detect_from_filename(os.path.basename(file_path))
        is_correct = detected_platform == expected_platform
        
        if is_correct:
            self.logger.info(f"平台識別正確: {detected_platform}")
        else:
            self.logger.warning(f"平台識別錯誤: 期望 {expected_platform}, 實際 {detected_platform}")
        
        return is_correct 