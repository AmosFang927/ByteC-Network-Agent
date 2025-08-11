#!/usr/bin/env python3
"""
貨幣轉換器
支持IDR到USD的動態匯率轉換
"""

import logging
import requests
import time
from typing import Dict, Optional
from datetime import datetime, timedelta
import json
import os

logger = logging.getLogger(__name__)

class CurrencyConverter:
    """動態貨幣轉換器"""
    
    def __init__(self):
        self.cache_file = "currency_rates_cache.json"
        self.cache_duration = 3600  # 1小時緩存
        self.rates_cache = {}
        self.last_update = None
        
        # 加載緩存
        self._load_cache()
    
    def _load_cache(self):
        """加載匯率緩存"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    cache_data = json.load(f)
                    self.rates_cache = cache_data.get('rates', {})
                    if 'last_update' in cache_data:
                        self.last_update = datetime.fromisoformat(cache_data['last_update'])
                logger.info(f"✅ 貨幣匯率緩存已加載")
        except Exception as e:
            logger.warning(f"加載匯率緩存失敗: {e}")
    
    def _save_cache(self):
        """保存匯率緩存"""
        try:
            cache_data = {
                'rates': self.rates_cache,
                'last_update': self.last_update.isoformat() if self.last_update else None
            }
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            logger.info(f"✅ 貨幣匯率緩存已保存")
        except Exception as e:
            logger.warning(f"保存匯率緩存失敗: {e}")
    
    def _should_update_cache(self) -> bool:
        """檢查是否需要更新緩存"""
        if self.last_update is None:
            return True
        
        time_since_update = datetime.now() - self.last_update
        return time_since_update.total_seconds() > self.cache_duration
    
    def _fetch_exchange_rate(self, from_currency: str, to_currency: str) -> Optional[float]:
        """獲取匯率（使用免費API）"""
        try:
            # 使用免費的匯率API
            api_urls = [
                f"https://api.exchangerate-api.com/v4/latest/{from_currency}",
                f"https://api.fixer.io/latest?base={from_currency}&symbols={to_currency}",
                f"https://open.er-api.com/v6/latest/{from_currency}"
            ]
            
            for api_url in api_urls:
                try:
                    logger.info(f"嘗試獲取匯率: {from_currency} -> {to_currency}")
                    response = requests.get(api_url, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # 處理不同API的響應格式
                        if 'rates' in data and to_currency in data['rates']:
                            rate = float(data['rates'][to_currency])
                            logger.info(f"✅ 獲取匯率成功: 1 {from_currency} = {rate} {to_currency}")
                            return rate
                        
                except requests.RequestException as e:
                    logger.warning(f"API請求失敗: {e}")
                    continue
                except Exception as e:
                    logger.warning(f"解析匯率數據失敗: {e}")
                    continue
            
            # 如果所有API都失敗，使用默認匯率
            logger.warning(f"所有匯率API都失敗，使用默認匯率")
            return self._get_fallback_rate(from_currency, to_currency)
            
        except Exception as e:
            logger.error(f"獲取匯率失敗: {e}")
            return self._get_fallback_rate(from_currency, to_currency)
    
    def _get_fallback_rate(self, from_currency: str, to_currency: str) -> float:
        """獲取默認匯率（當API失敗時使用）"""
        # 提供一些常用的近似匯率作為備用
        fallback_rates = {
            'IDR_USD': 0.000065,  # 1 IDR ≈ 0.000065 USD (大約15,400 IDR = 1 USD)
            'USD_IDR': 15400.0,   # 1 USD ≈ 15,400 IDR
        }
        
        rate_key = f"{from_currency}_{to_currency}"
        if rate_key in fallback_rates:
            rate = fallback_rates[rate_key]
            logger.warning(f"使用默認匯率: 1 {from_currency} = {rate} {to_currency}")
            return rate
        
        # 如果沒有默認匯率，返回1.0
        logger.error(f"沒有可用的匯率數據: {from_currency} -> {to_currency}")
        return 1.0
    
    def get_exchange_rate(self, from_currency: str, to_currency: str) -> float:
        """獲取匯率"""
        rate_key = f"{from_currency}_{to_currency}"
        
        # 檢查緩存
        if not self._should_update_cache() and rate_key in self.rates_cache:
            return self.rates_cache[rate_key]
        
        # 獲取新匯率
        rate = self._fetch_exchange_rate(from_currency, to_currency)
        
        if rate:
            # 更新緩存
            self.rates_cache[rate_key] = rate
            self.last_update = datetime.now()
            self._save_cache()
        
        return rate or 1.0
    
    def convert_idr_to_usd(self, idr_amount: float) -> float:
        """將IDR轉換為USD"""
        try:
            if idr_amount is None or idr_amount == 0:
                return 0.0
            
            exchange_rate = self.get_exchange_rate('IDR', 'USD')
            usd_amount = idr_amount * exchange_rate
            
            logger.debug(f"貨幣轉換: {idr_amount:,.2f} IDR -> {usd_amount:.6f} USD (匯率: {exchange_rate})")
            return round(usd_amount, 6)  # 保留6位小數
            
        except Exception as e:
            logger.error(f"IDR到USD轉換失敗: {e}")
            return 0.0
    
    def convert_currency(self, amount: float, from_currency: str, to_currency: str) -> float:
        """通用貨幣轉換方法"""
        try:
            if amount is None or amount == 0:
                return 0.0
            
            if from_currency == to_currency:
                return amount
            
            exchange_rate = self.get_exchange_rate(from_currency, to_currency)
            converted_amount = amount * exchange_rate
            
            logger.debug(f"貨幣轉換: {amount:,.2f} {from_currency} -> {converted_amount:.6f} {to_currency}")
            return round(converted_amount, 6)
            
        except Exception as e:
            logger.error(f"貨幣轉換失敗: {e}")
            return 0.0

# 全局實例
currency_converter = CurrencyConverter()