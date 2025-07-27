#!/usr/bin/env python3
"""
DMP-Agent API數據獲取器 - 增強版本
整合現有的Involve Asia API邏輯，支持完整的轉化數據存儲
包含platform、partner、source映射，以及所有API參數的完整存儲
"""

import sys
import os
import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

# 添加父目錄到Python路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from agents.api_agent.involve_asia_client import InvolveAsiaAPI
from agents.data_dmp_agent.api_config_manager import APIConfigManager
import config

logger = logging.getLogger(__name__)

class EnhancedAPIDataFetcher:
    """
    增強版API數據獲取器
    支持完整的轉化數據處理和存儲，包括：
    - platform 映射
    - partner 映射（按照config.py）
    - source 直接從aff_sub獲取
    - 所有API參數的完整存儲
    """
    
    def __init__(self):
        self.config_manager = APIConfigManager()
        self.api_clients = {}
    
    def get_api_client(self, platform: str) -> Optional[InvolveAsiaAPI]:
        """獲取API客戶端"""
        if platform in self.api_clients:
            return self.api_clients[platform]
        
        config_data = self.config_manager.get_config(platform)
        if not config_data:
            logger.error(f"❌ 未找到平台配置: {platform}")
            return None
        
        if not self.config_manager.validate_config(platform):
            logger.error(f"❌ 平台配置無效: {platform}")
            return None
        
        # 創建API客戶端
        try:
            api_client = InvolveAsiaAPI(
                api_secret=config_data['secret'],
                api_key=config_data['api_key']
            )
            
            # 執行認證
            if not api_client.authenticate():
                logger.error(f"❌ API認證失敗: {platform}")
                return None
            
            self.api_clients[platform] = api_client
            logger.info(f"✅ 創建API客戶端並認證成功: {platform}")
            return api_client
        except Exception as e:
            logger.error(f"❌ 創建API客戶端失敗: {platform} - {e}")
            return None
    
    def process_raw_conversions(self, raw_conversions: List[Dict], platform: str) -> List[Dict[str, Any]]:
        """
        處理原始轉化數據 - 增強版本
        完整處理所有API參數，按照config.py進行映射
        
        Args:
            raw_conversions: API返回的原始轉化數據
            platform: 平台名稱 (如: IAByteC)
            
        Returns:
            處理後的轉化數據列表，包含完整的字段映射
        """
        processed_conversions = []
        
        logger.info(f"🔄 開始處理 {len(raw_conversions)} 條原始轉化數據...")
        
        # 統計API返回的原始貨幣分布
        raw_currency_stats = {}
        for conv in raw_conversions:
            curr = conv.get('currency', 'USD')
            raw_currency_stats[curr] = raw_currency_stats.get(curr, 0) + 1
        logger.info(f"📊 API返回原始貨幣分布: {raw_currency_stats}")
        
        for idx, conversion in enumerate(raw_conversions, 1):
            try:
                # 檢查是否有實際銷售金額，但保留 pending 狀態的零金額轉化
                sale_amount = self._safe_float(conversion.get('sale_amount', 0))
                conversion_status = conversion.get('conversion_status', 'pending')
                
                # 只過濾掉 invalid 狀態的零金額轉化
                if (sale_amount is None or sale_amount <= 0) and conversion_status == 'invalid':
                    logger.debug(f"⏭️ 跳過無效的零金額轉化: conversion_id={conversion.get('conversion_id')}, sale_amount={sale_amount}, status={conversion_status}")
                    continue
                
                # 記錄零金額轉化的詳細信息（用於調試）
                if (sale_amount is None or sale_amount <= 0) and conversion_status == 'pending':
                    logger.info(f"📝 發現待處理的零金額轉化: conversion_id={conversion.get('conversion_id')}, offer_name={conversion.get('offer_name')}, status={conversion_status}")
                
                # ===== 核心分類字段處理 =====
                # 1. Platform: 直接使用傳入的平台名稱
                platform_name = platform
                
                # 2. Source: 從aff_sub1或aff_sub直接獲取
                source = conversion.get('aff_sub1') or conversion.get('aff_sub', '')
                
                # 3. Partner: 按照config.py映射表對應
                partner = config.match_source_to_partner(source) if source else 'Unknown'
                
                # ===== 完整的字段映射 =====
                processed_conversion = {
                    # ===== 核心分類字段 =====
                    'platform': platform_name,
                    'partner': partner,
                    'source': source,
                    
                    # ===== 核心轉化字段 =====
                    'conversion_id': str(conversion.get('conversion_id', '')),
                    'offer_id': conversion.get('offer_id', ''),
                    'offer_name': conversion.get('offer_name', ''),
                    'order_id': conversion.get('order_id', ''),
                    
                    # ===== 時間字段 =====
                    'datetime_conversion': self._parse_datetime(conversion.get('datetime_conversion')),
                    'datetime_conversion_updated': self._parse_datetime(conversion.get('datetime_conversion_updated')),
                    'click_time': self._parse_datetime(conversion.get('click_time')),
                    
                    # ===== 完整的金額字段 =====
                    # API原始金額字段
                    'sale_amount': self._safe_float(conversion.get('sale_amount')),
                    'payout': self._safe_float(conversion.get('payout')),
                    'base_payout': self._safe_float(conversion.get('base_payout')),
                    'bonus_payout': self._safe_float(conversion.get('bonus_payout')),
                    
                    # ===== 貨幣字段 =====
                    'conversion_currency': conversion.get('conversion_currency', ''),
                    'currency': conversion.get('currency', 'USD'),
                    
                    # ===== 完整的廣告主自定義參數 =====
                    'adv_sub': conversion.get('adv_sub', ''),
                    'adv_sub1': conversion.get('adv_sub1', ''),
                    'adv_sub2': conversion.get('adv_sub2', ''),
                    'adv_sub3': conversion.get('adv_sub3', ''),
                    'adv_sub4': conversion.get('adv_sub4', ''),
                    'adv_sub5': conversion.get('adv_sub5', ''),
                    
                    # ===== 完整的發布商自定義參數 =====
                    'aff_sub': source,  # 確保 aff_sub 字段與 source 一致
                    'aff_sub1': conversion.get('aff_sub1', ''),
                    'aff_sub2': conversion.get('aff_sub2', ''),
                    'aff_sub3': conversion.get('aff_sub3', ''),
                    'aff_sub4': conversion.get('aff_sub4', ''),
                    'aff_sub5': conversion.get('aff_sub5', ''),
                    
                    # ===== 狀態字段 =====
                    'status': conversion.get('status', conversion.get('conversion_status', 'approved')),
                    'conversion_status': conversion.get('conversion_status', 'approved'),
                    'offer_status': conversion.get('offer_status', ''),
                    
                    # ===== 業務字段 =====
                    'merchant_id': conversion.get('merchant_id', ''),
                    'affiliate_remarks': conversion.get('affiliate_remarks', ''),
                    'click_id': conversion.get('click_id', ''),
                    
                    # ===== 佣金計算相關字段 =====
                    'commission_rate': self._safe_float(conversion.get('commission_rate')),
                    'avg_commission_rate': self._safe_float(conversion.get('avg_commission_rate')),
                    
                    # ===== 系統字段 =====
                    'tenant_id': conversion.get('tenant_id', 1),
                    'is_processed': False,
                    'is_duplicate': False,
                    
                    # ===== 原始數據保存 =====
                    'raw_data': conversion,  # 完整的原始API響應
                    'processed_at': datetime.now().isoformat(),
                    'api_platform': platform_name,  # 標記數據來源API
                }
                
                # ===== USD 字段智能填充 =====
                # 🔧 修復貨幣轉換邏輯：根據 API 規範正確處理
                currency = processed_conversion.get('currency', 'USD')
                sale_amount = processed_conversion.get('sale_amount', 0.0)
                payout_amount = processed_conversion.get('payout', 0.0)
                
                # 🚨 核心修復：檢查貨幣不匹配的情況
                # 如果API返回的currency不是USD，但我們請求的是USD，說明API的preferred_currency參數沒有生效
                if currency != 'USD':
                    logger.warning(f"⚠️ 貨幣轉換異常：請求USD但API返回{currency}, conversion_id={conversion.get('conversion_id')}")
                    logger.warning(f"⚠️ sale_amount={sale_amount} {currency}, 為避免錯誤放大，設為0等待修復")
                    # 設為0避免錯誤的大額數據
                    processed_conversion['usd_sale_amount'] = 0.0
                    processed_conversion['usd_payout'] = 0.0
                else:
                    # 如果貨幣是USD，檢查API是否提供了usd_sale_amount
                    api_usd_sale = conversion.get('usd_sale_amount')
                    api_usd_payout = conversion.get('usd_payout')
                    
                    if api_usd_sale is not None and api_usd_sale != '' and float(api_usd_sale or 0) > 0:
                        # API提供了有效的USD金額
                        processed_conversion['usd_sale_amount'] = self._safe_float(api_usd_sale)
                        logger.debug(f"✅ 使用API提供的usd_sale_amount: {processed_conversion['usd_sale_amount']}")
                    else:
                        # API沒有提供有效的USD金額，使用sale_amount
                        processed_conversion['usd_sale_amount'] = sale_amount
                        logger.debug(f"✅ 使用sale_amount作為usd_sale_amount: {sale_amount}")
                    
                    if api_usd_payout is not None and api_usd_payout != '' and float(api_usd_payout or 0) > 0:
                        # API提供了有效的USD佣金
                        processed_conversion['usd_payout'] = self._safe_float(api_usd_payout)
                        logger.debug(f"✅ 使用API提供的usd_payout: {processed_conversion['usd_payout']}")
                    else:
                        # API沒有提供有效的USD佣金，使用payout
                        processed_conversion['usd_payout'] = payout_amount
                        logger.debug(f"✅ 使用payout作為usd_payout: {payout_amount}")
                
                # 記錄映射結果
                if idx <= 5:  # 只記錄前5條的詳細映射信息
                    logger.info(f"   轉化 {idx}: source='{source}' -> partner='{partner}', conversion_id='{processed_conversion['conversion_id']}'")
                
                processed_conversions.append(processed_conversion)
                
            except Exception as e:
                logger.error(f"❌ 處理轉化數據失敗 (第{idx}條): {str(e)}")
                logger.error(f"   原始數據: {json.dumps(conversion, indent=2, ensure_ascii=False)}")
                continue
        
        # 統計映射結果
        partner_stats = {}
        for conv in processed_conversions:
            partner = conv['partner']
            if partner not in partner_stats:
                partner_stats[partner] = {'count': 0, 'sources': set()}
            partner_stats[partner]['count'] += 1
            partner_stats[partner]['sources'].add(conv['source'])
        
        logger.info(f"✅ 處理完成: {len(processed_conversions)}/{len(raw_conversions)} 條記錄")
        logger.info(f"📊 Partner映射統計:")
        for partner, stats in partner_stats.items():
            sources_list = list(stats['sources'])[:3]  # 只顯示前3個source
            sources_display = ', '.join(sources_list)
            if len(stats['sources']) > 3:
                sources_display += f"... (+{len(stats['sources'])-3} more)"
            logger.info(f"   - {partner}: {stats['count']} 條轉化, sources: {sources_display}")
        
        return processed_conversions
    
    def _parse_datetime(self, date_str: str) -> Optional[datetime]:
        """
        解析日期時間字符串 - 支持多種格式，並設置正確的時區
        
        Args:
            date_str: 日期時間字符串
            
        Returns:
            解析後的datetime對象（設置為UTC時區），失敗返回None
        """
        if not date_str:
            return None
        
        try:
            # 嘗試多種日期格式
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%d %H:%M:%S.%f',
                '%Y-%m-%dT%H:%M:%S.%f',
                '%Y-%m-%dT%H:%M:%S%z',
                '%Y-%m-%dT%H:%M:%SZ',
                '%Y-%m-%d'
            ]
            
            for fmt in formats:
                try:
                    parsed_dt = datetime.strptime(str(date_str), fmt)
                    
                    # 🔧 時區修復：如果解析的日期沒有時區信息，設置為UTC時區
                    # 這樣可以保持日期正確，避免後續時區轉換導致的日期偏移
                    if parsed_dt.tzinfo is None:
                        from datetime import timezone
                        parsed_dt = parsed_dt.replace(tzinfo=timezone.utc)
                        logger.info(f"🕒 _parse_datetime: 將API時間解釋為UTC → 原始: '{date_str}' 結果: {parsed_dt}")
                    
                    return parsed_dt
                except ValueError:
                    continue
            
            # 如果所有格式都失敗，記錄警告並返回None
            logger.warning(f"⚠️ 無法解析日期格式: {date_str}")
            return None
            
        except Exception as e:
            logger.error(f"❌ 解析日期時間失敗: {str(e)}")
            return None
    
    def _safe_float(self, value: Any) -> Optional[float]:
        """
        安全地轉換值為float
        
        Args:
            value: 要轉換的值
            
        Returns:
            轉換後的float值，失敗返回None
        """
        if value is None or value == '':
            return None
        
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    async def fetch_conversions(self, platform: str, days_ago: int = 1, limit: int = None) -> List[Dict[str, Any]]:
        """
        獲取轉化數據 - 增強版本
        
        Args:
            platform: 平台名稱
            days_ago: 天數前
            limit: 限制條數
            
        Returns:
            完整處理後的轉化數據列表
        """
        logger.info(f"🔍 開始獲取轉化數據: platform={platform}, days_ago={days_ago}, limit={limit}")
        
        # 獲取API客戶端
        api_client = self.get_api_client(platform)
        if not api_client:
            logger.error(f"❌ 無法獲取API客戶端: {platform}")
            return []
        
        # 獲取日期範圍
        start_date, end_date = self.config_manager.get_date_range(days_ago)
        logger.info(f"📅 查詢日期範圍: {start_date} 至 {end_date}")
        logger.info(f"💱 使用貨幣參數: {config.PREFERRED_CURRENCY}")
        logger.info(f"🎯 平台: {platform}, 數據限制: {limit if limit else '無限制'}")
        
        try:
            # 獲取原始轉化數據
            logger.info(f"🔄 開始API調用 - platform: {platform}, currency: {config.PREFERRED_CURRENCY}")
            api_response = api_client.get_conversions(
                start_date=start_date,
                end_date=end_date,
                currency=config.PREFERRED_CURRENCY,  # 使用配置的貨幣
                api_name=platform,
                limit=limit
            )
            logger.info(f"✅ API調用完成 - platform: {platform}")
            
            if not api_response or api_response.get("status") != "success":
                logger.warning(f"⚠️ API響應無效: {platform}")
                logger.warning(f"   響應狀態: {api_response.get('status') if api_response else 'None'}")
                return []
            
            # 提取實際的轉化數據
            raw_conversions = api_response.get("data", {}).get("data", [])
            
            if not raw_conversions:
                logger.warning(f"⚠️ 沒有獲取到轉化數據: {platform}")
                return []
            
            logger.info(f"✅ 獲取原始轉化數據: {len(raw_conversions)} 條記錄")
            
            # 處理數據 - 完整的字段映射和partner映射
            processed_conversions = self.process_raw_conversions(raw_conversions, platform)
            
            # 統計處理後的數據
            total_sale_amount = sum(conv.get('usd_sale_amount', 0) for conv in processed_conversions)
            currency_stats = {}
            for conv in processed_conversions:
                curr = conv.get('currency', 'USD')
                currency_stats[curr] = currency_stats.get(curr, 0) + 1
            
            logger.info(f"💰 處理後總金額: ${total_sale_amount:,.2f} USD")
            logger.info(f"💱 貨幣分布: {currency_stats}")
            logger.info(f"📊 轉化總數: {len(processed_conversions)} 條")
            
            # 應用限制
            if limit and len(processed_conversions) > limit:
                processed_conversions = processed_conversions[:limit]
                logger.info(f"🔢 應用數據限制: {len(processed_conversions)} 條記錄 (限制: {limit})")
            
            logger.info(f"🎯 完成轉化數據獲取: {len(processed_conversions)} 條記錄已完整處理")
            return processed_conversions
            
        except Exception as e:
            logger.error(f"❌ 獲取轉化數據失敗: {str(e)}")
            import traceback
            logger.error(f"   錯誤詳情: {traceback.format_exc()}")
            return []
    
    async def fetch_conversions_batch(self, platforms: List[str], days_ago: int = 1) -> Dict[str, List[Dict[str, Any]]]:
        """
        批量獲取多個平台的轉化數據
        
        Args:
            platforms: 平台名稱列表
            days_ago: 天數前
            
        Returns:
            按平台分組的轉化數據字典
        """
        logger.info(f"🚀 開始批量獲取多平台數據: {platforms}")
        
        results = {}
        total_conversions = 0
        
        for platform in platforms:
            logger.info(f"📡 處理平台: {platform}")
            conversions = await self.fetch_conversions(platform, days_ago)
            results[platform] = conversions
            total_conversions += len(conversions)
            logger.info(f"   ✅ {platform}: {len(conversions)} 條轉化")
        
        logger.info(f"🎉 批量獲取完成: {len(platforms)} 個平台, 總計 {total_conversions} 條轉化")
        return results
    
    def get_available_platforms(self) -> List[str]:
        """獲取可用平台列表"""
        return self.config_manager.get_available_platforms()
    
    async def test_platform_connection(self, platform: str) -> bool:
        """測試平台連接"""
        try:
            api_client = self.get_api_client(platform)
            return api_client is not None
        except Exception as e:
            logger.error(f"❌ 測試平台連接失敗: {platform} - {str(e)}")
            return False
    
    def get_conversion_summary(self, conversions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        生成轉化數據摘要統計
        
        Args:
            conversions: 轉化數據列表
            
        Returns:
            摘要統計信息
        """
        if not conversions:
            return {
                'total_conversions': 0,
                'total_partners': 0,
                'total_sources': 0,
                'partner_breakdown': {},
                'currency_breakdown': {},
                'platform_breakdown': {}
            }
        
        # 統計信息
        partners = set()
        sources = set()
        platforms = set()
        partner_breakdown = {}
        currency_breakdown = {}
        platform_breakdown = {}
        
        total_usd_amount = 0.0
        total_usd_payout = 0.0
        
        for conv in conversions:
            # 基本統計
            partner = conv.get('partner', 'Unknown')
            source = conv.get('source', '')
            platform = conv.get('platform', 'Unknown')
            
            partners.add(partner)
            sources.add(source)
            platforms.add(platform)
            
            # Partner分析
            if partner not in partner_breakdown:
                partner_breakdown[partner] = {
                    'count': 0,
                    'sources': set(),
                    'usd_amount': 0.0,
                    'usd_payout': 0.0
                }
            partner_breakdown[partner]['count'] += 1
            partner_breakdown[partner]['sources'].add(source)
            partner_breakdown[partner]['usd_amount'] += conv.get('usd_sale_amount') or 0.0
            partner_breakdown[partner]['usd_payout'] += conv.get('usd_payout') or 0.0
            
            # 貨幣分析
            currency = conv.get('currency', 'USD')
            if currency not in currency_breakdown:
                currency_breakdown[currency] = 0
            currency_breakdown[currency] += 1
            
            # 平台分析
            if platform not in platform_breakdown:
                platform_breakdown[platform] = 0
            platform_breakdown[platform] += 1
            
            # 總金額
            total_usd_amount += conv.get('usd_sale_amount') or 0.0
            total_usd_payout += conv.get('usd_payout') or 0.0
        
        # 轉換partner_breakdown中的set為list以便JSON序列化
        for partner_data in partner_breakdown.values():
            partner_data['sources'] = list(partner_data['sources'])
        
        return {
            'total_conversions': len(conversions),
            'total_partners': len(partners),
            'total_sources': len(sources),
            'total_platforms': len(platforms),
            'total_usd_amount': round(total_usd_amount, 2),
            'total_usd_payout': round(total_usd_payout, 2),
            'partner_breakdown': partner_breakdown,
            'currency_breakdown': currency_breakdown,
            'platform_breakdown': platform_breakdown,
            'partners_list': list(partners),
            'sources_list': list(sources),
            'platforms_list': list(platforms)
        }

# 保持向後兼容性的別名
APIDataFetcher = EnhancedAPIDataFetcher 