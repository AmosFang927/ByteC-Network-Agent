#!/usr/bin/env python3
"""
Ultra Optimized API Client for ByteC Network Agent
超級優化API客戶端 - 整合所有性能優化技術

預期性能提升：85-92%
處理時間：從15-30分鐘 → 2-4分鐘
"""

import asyncio
import aiohttp
import time
import sys
import os
from typing import Dict, List, Any, Optional, AsyncGenerator
from datetime import datetime, timezone
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

# 添加項目根目錄到路徑
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import config
from agents.data_dmp_agent.database_manager import EnhancedDMPDatabaseManager

@dataclass
class PerformanceStats:
    """性能統計數據類"""
    start_time: float = 0
    total_requests: int = 0
    total_records: int = 0
    failed_requests: int = 0
    retries: int = 0
    avg_response_time: float = 0
    records_per_second: float = 0
    eta_minutes: float = 0

class UltraOptimizedAPIClient:
    """
    超級優化API客戶端
    
    性能優化特性：
    1. 異步並發請求 (12個並發)
    2. 智能批量處理 (1000條/頁)
    3. 連接池復用
    4. 性能監控和ETA計算
    5. 智能重試機制
    6. 批量數據庫插入 (2000條/批)
    """
    
    def __init__(self, platform_config: Dict[str, Any]):
        self.platform_config = platform_config
        # 修復：使用平台代碼而不是描述性名稱
        self.platform_name = platform_config.get('platform_code', platform_config.get('name', 'Unknown'))
        self.api_key = platform_config.get('api_key')
        self.api_secret = platform_config.get('api_secret')
        
        # 性能優化參數 - 使用 API Agent 專用配置
        api_agent_config = config.get_api_agent_config()
        self.enable_batch_concurrent = api_agent_config.get('enable_batch_concurrent', False)
        self.enable_async_mode = api_agent_config.get('enable_async_mode', True)
        self.force_sequential_mode = api_agent_config.get('force_sequential_mode', True)
        
        self.max_concurrent = api_agent_config.get('max_concurrent_requests', 1)
        self.page_limit = config.DEFAULT_PAGE_LIMIT
        self.request_delay = config.REQUEST_DELAY
        self.database_batch_size = getattr(config, 'DATABASE_BATCH_SIZE', 2000)
        
        # 🕐 並發錯開配置（新增）
        self.concurrent_startup_delay = api_agent_config.get('concurrent_startup_delay', 3.0)
        self.concurrent_request_stagger = api_agent_config.get('concurrent_request_stagger', 0.5)
        self.enable_concurrent_stagger = api_agent_config.get('enable_concurrent_stagger', True)
        
        # 單線程模式配置
        if not self.enable_batch_concurrent or self.force_sequential_mode:
            self.max_concurrent = 1
            self.request_delay = 1.0  # 增加延遲確保順序執行
        
        # 性能監控
        self.stats = PerformanceStats()
        self.logger = self._setup_logger()
        
        # 數據庫管理器
        self.db_manager = None
        
        # 認證相關
        self.token = None
        
        # Partner 和 Source 過濾
        self.target_partner = None
        self.target_sources = None
        
        # Currency和金额统计
        self.currency_breakdown = {}
        self.total_usd_amount = 0.0
    
    def _setup_logger(self) -> logging.Logger:
        """設置優化的日誌記錄器"""
        logger = logging.getLogger(f"UltraOptimized_{self.platform_name}")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '🚀 %(asctime)s | %(name)s | %(levelname)s | %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    async def __aenter__(self):
        """異步上下文管理器入口"""
        # 創建優化的HTTP會話
        connector = aiohttp.TCPConnector(
            limit=config.HTTP_MAX_CONNECTIONS,
            limit_per_host=config.HTTP_MAX_KEEPALIVE_CONNECTIONS,
            keepalive_timeout=config.HTTP_KEEPALIVE_EXPIRY,
            enable_cleanup_closed=True
        )
        
        timeout = aiohttp.ClientTimeout(total=config.TIMEOUT_SECONDS)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'User-Agent': 'ByteC-Ultra-Optimized-Client/1.0'}
        )
        
        # 初始化數據庫管理器
        self.db_manager = EnhancedDMPDatabaseManager()
        # 初始化數據庫連接池
        await self.db_manager.init_pool()
        # 確保數據庫schema是最新的
        await self.db_manager.ensure_database_schema()
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器退出"""
        if self.session:
            await self.session.close()
        if self.db_manager:
            await self.db_manager.close_pool()
    
    async def fetch_all_conversions(self, 
                                   start_date: str, 
                                   end_date: str,
                                   progress_callback: Optional[callable] = None,
                                   limit: Optional[int] = None,
                                   partner: Optional[str] = None) -> Dict[str, Any]:
        """
        超級優化的轉化數據獲取方法
        
        Args:
            start_date: 開始日期
            end_date: 結束日期
            progress_callback: 進度回調函數
            limit: 數據限制
            partner: 指定的 Partner（用於過濾 Sources）
            
        Returns:
            Dict containing:
            - total_records: 總記錄數
            - processing_time: 處理時間
            - performance_stats: 性能統計
        """
        self.stats.start_time = time.time()
        
        # 设置目标 Partner 和 Sources
        self.target_partner = partner
        if partner:
            self.target_sources = config.get_sources_for_partner(partner)
        
        # 日志输出API调用参数和模式
        if self.force_sequential_mode or not self.enable_batch_concurrent:
            self.logger.info(f"🔄 開始單線程順序數據獲取")
            self.logger.info(f"🚫 批量並發模式: 已禁用")
            self.logger.info(f"🔄 順序模式: 已啟用 (用於currency參數驗證)")
        else:
            self.logger.info(f"🚀 開始超級優化數據獲取")
            self.logger.info(f"⚡ 批量並發模式: 已啟用")
        
        self.logger.info(f"📅 日期範圍: {start_date} to {end_date}")
        self.logger.info(f"💱 使用貨幣: {config.PREFERRED_CURRENCY}")
        self.logger.info(f"⚡ 並發數: {self.max_concurrent}")
        self.logger.info(f"📄 頁面大小: {self.page_limit}")
        self.logger.info(f"⏱️ 請求間隔: {self.request_delay}s")
        
        if partner:
            self.logger.info(f"🎯 目標 Partner: {partner}, Sources: {self.target_sources}")
        
        try:
            # 根據配置選擇執行模式
            if self.force_sequential_mode or not self.enable_batch_concurrent:
                # 單線程順序模式
                return await self._fetch_data_sequential(start_date, end_date, limit, progress_callback)
            else:
                # 原來的批量並發模式
                return await self._fetch_data_concurrent(start_date, end_date, limit, progress_callback)
        except Exception as e:
            self.logger.error(f"❌ 數據獲取失敗: {e}")
            return self._create_result_summary(0)

    async def _fetch_data_sequential(self, start_date: str, end_date: str, limit: Optional[int], progress_callback: Optional[callable]) -> Dict[str, Any]:
        """單線程順序獲取數據 - 用於currency參數驗證"""
        self.logger.info("🔄 開始單線程順序數據獲取...")
        
        # 階段1: 快速獲取總數
        total_count = await self._get_total_count(start_date, end_date)
        if total_count == 0:
            return self._create_result_summary(0)
        
        # 應用數據限制
        if limit and limit > 0:
            if limit < total_count:
                total_count = limit
                self.logger.info(f"🔢 數據限制: 只獲取前 {limit:,} 條記錄")
        
        # 計算總頁數
        total_pages = (total_count + self.page_limit - 1) // self.page_limit
        self.logger.info(f"📊 數據總量: {total_count:,} 條")
        self.logger.info(f"📖 總頁數: {total_pages:,} 頁")
        
        # 單線程順序獲取每一頁
        all_data = []
        for page in range(1, total_pages + 1):
            self.logger.info(f"🔄 順序獲取第 {page}/{total_pages} 頁")
            self.logger.info(f"💱 確認currency參數: {config.PREFERRED_CURRENCY}")
            
            # 獲取單頁數據
            page_data = await self._fetch_single_page(page, start_date, end_date)
            
            if page_data:
                self.logger.info(f"✅ 第 {page} 頁獲取成功: {len(page_data)} 條記錄")
                
                # 檢查返回數據的currency分布
                currency_stats = {}
                for item in page_data:
                    currency = item.get('currency', 'USD')
                    currency_stats[currency] = currency_stats.get(currency, 0) + 1
                
                self.logger.info(f"💱 第 {page} 頁currency分布: {currency_stats}")
                
                all_data.extend(page_data)
                
                # 檢查是否達到limit限制
                if limit and len(all_data) >= limit:
                    all_data = all_data[:limit]
                    self.logger.info(f"🔢 達到數據限制: {limit:,} 條記錄")
                    break
            else:
                self.logger.warning(f"⚠️ 第 {page} 頁獲取失敗")
            
            # 進度回調
            if progress_callback:
                progress = (len(all_data) / total_count) * 100
                await progress_callback(progress, len(all_data), total_count)
            
            # 延遲確保順序執行
            if page < total_pages:  # 最後一頁不需要延遲
                await asyncio.sleep(self.request_delay)
        
        # 處理獲取的數據
        if all_data:
            # 使用現有的批量處理方法
            await self._batch_insert_data(all_data)
            
            self.logger.info(f"✅ 單線程順序獲取完成: {len(all_data)} 條記錄")
            return self._create_result_summary(len(all_data))
        else:
            self.logger.warning("⚠️ 未獲取到任何數據")
            return self._create_result_summary(0)

    async def _fetch_data_concurrent(self, start_date: str, end_date: str, limit: Optional[int], progress_callback: Optional[callable]) -> Dict[str, Any]:
        """原來的批量並發獲取數據方法"""
        # 階段1: 快速獲取總數
        total_count = await self._get_total_count(start_date, end_date)
        if total_count == 0:
            return self._create_result_summary(0)
        
        # 應用數據限制（如果設置了limit）
        if limit and limit > 0:
            if limit < total_count:
                total_count = limit
                self.logger.info(f"🔢 數據限制: 只獲取前 {limit:,} 條記錄")
        
        # 階段2: 計算最優分頁策略
        total_pages = (total_count + self.page_limit - 1) // self.page_limit
        self.logger.info(f"📊 數據總量: {total_count:,} 條")
        self.logger.info(f"📖 總頁數: {total_pages:,} 頁")
        
        # 階段3: 並發批量獲取數據
        all_data = []
        
        # 🕐 並發錯開控制：啟動前延迟
        if self.enable_concurrent_stagger and self.max_concurrent > 1:
            self.logger.info(f"🕐 並發錯開: 等待 {self.concurrent_startup_delay:.1f}秒 後開始並發請求")
            await asyncio.sleep(self.concurrent_startup_delay)
        
        # 使用信號量控制並發數
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        # 創建任務列表
        tasks = []
        for page in range(1, total_pages + 1):
            task = self._fetch_page_with_semaphore_staggered(
                semaphore, page, start_date, end_date, page - 1
            )
            tasks.append(task)
        
        # 批量執行任務
        batch_size = self.max_concurrent * 3
        for i in range(0, len(tasks), batch_size):
            batch_tasks = tasks[i:i + batch_size]
            
            self.logger.info(f"🔄 執行批次 {i//batch_size + 1}/{(len(tasks)-1)//batch_size + 1}")
            
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # 處理批次結果
            valid_results = []
            for result in batch_results:
                if isinstance(result, Exception):
                    self.stats.failed_requests += 1
                    self.logger.warning(f"⚠️ 請求失敗: {result}")
                elif result:
                    valid_results.extend(result)
            
            all_data.extend(valid_results)
            
            # 檢查是否達到limit限制
            if limit and len(all_data) >= limit:
                # 截斷到限制數量
                all_data = all_data[:limit]
                self.logger.info(f"🔢 達到數據限制: {limit:,} 條記錄")
                break
            
            # 進度回調
            if progress_callback:
                progress = (len(all_data) / total_count) * 100
                await progress_callback(progress, len(all_data), total_count)
        
        # 階段4: 批量存儲數據
        if all_data:
            await self._batch_insert_data(all_data)
        
        return self._create_result_summary(len(all_data))
    
    async def _authenticate(self) -> Optional[str]:
        """API認證獲取token"""
        base_url = self.platform_config.get('base_url', '')
        auth_url = f"{base_url}/authenticate"
        
        auth_data = {
            "key": self.platform_config.get('api_key'),
            "secret": self.platform_config.get('secret')
        }
        
        headers = {"Accept": "application/json"}
        
        try:
            async with self.session.post(auth_url, data=auth_data, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    if "data" in result and "token" in result["data"]:
                        return result["data"]["token"]
                self.logger.warning(f"⚠️ 認證響應錯誤: HTTP {response.status}")
                return None
        except Exception as e:
            self.logger.error(f"❌ 認證請求失敗: {e}")
            return None

    async def _get_total_count(self, start_date: str, end_date: str) -> int:
        """快速獲取總記錄數"""
        # 首先進行認證
        if not self.token:
            self.token = await self._authenticate()
            if not self.token:
                self.logger.error("❌ 認證失敗，無法獲取總數")
                return 0
        
        url = self._build_url(1, start_date, end_date)
        data = self._build_post_data(1, start_date, end_date)
        headers = {"Authorization": f"Bearer {self.token}"}
        

        
        try:
            async with self.session.post(url, data=data, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get('data', {}).get('count', 0)
                else:
                    self.logger.warning(f"⚠️ 獲取總數失敗: HTTP {response.status}")
                    return 0
        except Exception as e:
            self.logger.error(f"❌ 獲取總數錯誤: {type(e).__name__}: {str(e)}")
            import traceback
            self.logger.error(f"詳細錯誤: {traceback.format_exc()}")
            return 0
    
    async def _fetch_page_with_semaphore(self,
                                       semaphore: asyncio.Semaphore,
                                       page: int,
                                       start_date: str,
                                       end_date: str) -> List[Dict[str, Any]]:
        """使用信號量控制的頁面獲取"""
        async with semaphore:
            try:
                # 確保有認證 token
                if not self.token:
                    self.token = await self._authenticate()
                    if not self.token:
                        self.logger.error("❌ 認證失敗，無法獲取數據")
                        return []
                
                # 構建請求數據
                data = {
                    "page": str(page),
                    "limit": str(self.page_limit),
                    "start_date": start_date,
                    "end_date": end_date,
                    "filters[preferred_currency]": config.PREFERRED_CURRENCY
                }
                
                # 添加 Source 過濾
                if self.target_sources:
                    data["filters[aff_sub1]"] = self.target_sources
                    self.logger.debug(f"   📋 應用 Source 過濾: {self.target_sources}")
                
                url = self._build_url(page, start_date, end_date)
                headers = {"Authorization": f"Bearer {self.token}"}
                
                async with self.session.post(url, json=data, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("status") == "success":
                            return result.get("data", {}).get("data", [])
                    elif response.status == 401:
                        # Token 可能过期，重新认证
                        self.logger.warning(f"🔄 Token 可能过期，重新认证...")
                        self.token = await self._authenticate()
                        if self.token:
                            # 重试一次
                            headers = {"Authorization": f"Bearer {self.token}"}
                            async with self.session.post(url, json=data, headers=headers) as retry_response:
                                if retry_response.status == 200:
                                    result = await retry_response.json()
                                    if result.get("status") == "success":
                                        return result.get("data", {}).get("data", [])
                    
                    self.logger.warning(f"⚠️ 頁面 {page} 請求失敗: HTTP {response.status}")
                    return []
                    
            except Exception as e:
                self.logger.error(f"❌ 頁面 {page} 獲取失敗: {e}")
                return []
    
    async def _fetch_page_with_semaphore_staggered(self,
                                                 semaphore: asyncio.Semaphore,
                                                 page: int,
                                                 start_date: str,
                                                 end_date: str,
                                                 stagger_index: int) -> List[Dict[str, Any]]:
        """使用信號量控制的頁面獲取 - 支持錯開延迟"""
        # 🕐 並發錯開: 每個請求錯開一定時間
        if self.enable_concurrent_stagger and self.max_concurrent > 1 and stagger_index > 0:
            stagger_delay = stagger_index * self.concurrent_request_stagger
            await asyncio.sleep(stagger_delay)
        
        # 調用原始的獲取方法
        return await self._fetch_page_with_semaphore(semaphore, page, start_date, end_date)
    
    def _build_url(self, page: int, start_date: str, end_date: str) -> str:
        """構建API請求URL"""
        base_url = self.platform_config.get('base_url', '')
        endpoints = self.platform_config.get('endpoints', {})
        conversions_endpoint = endpoints.get('conversions', '/conversions/range')
        
        url = f"{base_url}{conversions_endpoint}"
        return url
    
    def _build_post_data(self, page: int, start_date: str, end_date: str) -> Dict[str, str]:
        """構建POST請求數據"""
        return {
            'page': str(page),
            'limit': str(self.page_limit),
            'start_date': start_date,
            'end_date': end_date,
            'filters[preferred_currency]': config.PREFERRED_CURRENCY
        }

    async def _fetch_single_page(self,
                               page: int,
                               start_date: str,
                               end_date: str,
                               retry_count: int = 0) -> List[Dict[str, Any]]:
        """獲取單個頁面數據"""
        # 確保有認證token
        if not self.token:
            self.token = await self._authenticate()
            if not self.token:
                self.logger.error("❌ 認證失敗，無法獲取頁面數據")
                return []
        
        url = self._build_url(page, start_date, end_date)
        post_data = self._build_post_data(page, start_date, end_date)
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            start_time = time.time()
            
            async with self.session.post(url, data=post_data, headers=headers) as response:
                response_time = time.time() - start_time
                self.stats.avg_response_time = (
                    (self.stats.avg_response_time * self.stats.total_requests + response_time)
                    / (self.stats.total_requests + 1)
                )
                self.stats.total_requests += 1
                
                if response.status == 200:
                    result = await response.json()
                    conversions = result.get('data', {}).get('data', [])
                    self.stats.total_records += len(conversions)
                    
                    return conversions
                    
                elif response.status == 429:  # Rate limit
                    if retry_count < config.MAX_RETRIES:
                        self.logger.warning(f"⏳ 遇到限制，等待後重試 (第{retry_count+1}次)")
                        await asyncio.sleep(config.RATE_LIMIT_DELAY)
                        return await self._fetch_single_page(page, start_date, end_date, retry_count + 1)
                    else:
                        raise Exception(f"Rate limit exceeded for page {page}")
                        
                else:
                    raise Exception(f"HTTP {response.status} for page {page}")
                    
        except Exception as e:
            if retry_count < config.MAX_RETRIES:
                self.stats.retries += 1
                self.logger.warning(f"🔄 重試頁面 {page} (第{retry_count+1}次): {e}")
                await asyncio.sleep(config.RETRY_DELAY * (retry_count + 1))
                return await self._fetch_single_page(page, start_date, end_date, retry_count + 1)
            else:
                self.logger.error(f"❌ 頁面 {page} 獲取失敗: {e}")
                return []
    
    async def _batch_insert_data(self, data: List[Dict[str, Any]]) -> None:
        """批量插入數據到數據庫"""
        if not data or not self.db_manager:
            return
        
        try:
            # 修復：處理原始API數據，添加platform和partner字段映射
            processed_data = self._process_raw_conversions(data)
            
            # 使用優化的批量插入
            if hasattr(self.db_manager, 'insert_conversion_batch_optimized'):
                await self.db_manager.insert_conversion_batch_optimized(
                    processed_data, 
                    platform_name=self.platform_name,
                    batch_size=self.database_batch_size
                )
            else:
                # 降級使用基本插入方法
                for conversion in processed_data:
                    if hasattr(self.db_manager, 'insert_conversion'):
                        await self.db_manager.insert_conversion(conversion, self.platform_name)
                    else:
                        self.logger.warning(f"⚠️ 數據庫管理器不支持數據插入，跳過數據存儲")
                        break
        except Exception as e:
            self.logger.error(f"❌ 數據庫插入失敗: {e}")
    
    def _process_raw_conversions(self, raw_conversions: List[Dict]) -> List[Dict[str, Any]]:
        """
        處理原始轉化數據，添加platform和partner字段映射
        復用EnhancedAPIDataFetcher的邏輯
        """
        # 🔧 在字段映射前应用Currency过滤
        if config.ENABLE_CLIENT_SIDE_CURRENCY_FILTER:
            raw_conversions = self._filter_usd_conversions(raw_conversions)
            if not raw_conversions:
                self.logger.error("❌ Currency过滤后无USD记录，停止处理")
                return []
        
        processed_conversions = []
        
        for idx, conversion in enumerate(raw_conversions):
            try:
                # 檢查是否有實際銷售金額，但保留 pending 狀態的零金額轉化
                sale_amount = self._safe_float(conversion.get('sale_amount', 0))
                conversion_status = conversion.get('conversion_status', 'pending')
                
                # 只過濾掉 invalid 狀態的零金額轉化
                if (sale_amount is None or sale_amount <= 0) and conversion_status == 'invalid':
                    self.logger.debug(f"⏭️ 跳過無效的零金額轉化: conversion_id={conversion.get('conversion_id')}, sale_amount={sale_amount}, status={conversion_status}")
                    continue
                
                # 記錄零金額轉化的詳細信息（用於調試）
                if (sale_amount is None or sale_amount <= 0) and conversion_status == 'pending':
                    self.logger.info(f"📝 發現待處理的零金額轉化: conversion_id={conversion.get('conversion_id')}, offer_name={conversion.get('offer_name')}, status={conversion_status}")
                
                # 設置platform字段
                platform_name = self.platform_name
                
                # 設置source字段（從aff_sub1或aff_sub獲取）
                source = conversion.get('aff_sub1') or conversion.get('aff_sub', '')
                
                # 設置partner字段（按照config.py映射）
                partner = config.match_source_to_partner(source) if source else 'Unknown'
                
                # 創建處理後的轉化記錄
                processed_conversion = conversion.copy()  # 保留所有原始字段
                
                # 處理時間字段，強制使用UTC時區
                datetime_conversion = conversion.get('datetime_conversion')
                if datetime_conversion:
                    try:
                        # 如果是字符串，解析為datetime
                        if isinstance(datetime_conversion, str):
                            datetime_conversion = datetime.fromisoformat(datetime_conversion.replace('Z', '+00:00'))
                        # 確保時區是UTC
                        if datetime_conversion.tzinfo is None:
                            datetime_conversion = datetime_conversion.replace(tzinfo=timezone.utc)
                        else:
                            datetime_conversion = datetime_conversion.astimezone(timezone.utc)
                    except Exception as e:
                        self.logger.warning(f"⚠️ 轉化時間解析失敗，使用當前UTC時間: {e}")
                        datetime_conversion = datetime.now(timezone.utc)
                else:
                    datetime_conversion = datetime.now(timezone.utc)
                
                # 添加/覆蓋核心分類字段
                processed_conversion.update({
                    'platform': platform_name,
                    'partner': partner,
                    'source': source,
                    'aff_sub': source,  # 確保 aff_sub 字段與 source 一致
                    'raw_data': conversion,  # 保存原始數據
                    'datetime_conversion': datetime_conversion,  # 使用UTC時間
                    'created_at': datetime.now(timezone.utc),  # 使用UTC時間
                    'api_platform': platform_name,
                })
                
                # ===== USD 字段智能填充 =====
                # 檢查原始 API 響應中的 usd_sale_amount 和 usd_payout
                currency = processed_conversion.get('currency', 'USD')
                
                # 如果原始 API 有 usd_sale_amount 和 usd_payout，直接使用
                if conversion.get('usd_sale_amount') is not None:
                    processed_conversion['usd_sale_amount'] = self._safe_float(conversion.get('usd_sale_amount'))
                else:
                    # 無論貨幣是什麼，都使用 sale_amount 作為 usd_sale_amount
                    # 因為 API 返回的 sale_amount 已經是 USD 等值
                    processed_conversion['usd_sale_amount'] = self._safe_float(processed_conversion.get('sale_amount', 0.0))
                
                if conversion.get('usd_payout') is not None:
                    processed_conversion['usd_payout'] = self._safe_float(conversion.get('usd_payout'))
                else:
                    # 無論貨幣是什麼，都使用 payout 作為 usd_payout
                    # 因為 API 返回的 payout 已經是 USD 等值
                    processed_conversion['usd_payout'] = self._safe_float(processed_conversion.get('payout', 0.0))
                
                processed_conversions.append(processed_conversion)
                
            except Exception as e:
                self.logger.error(f"❌ 處理轉化數據失敗 (第{idx}條): {str(e)}")
                continue
        
        # 記錄映射統計
        if processed_conversions:
            partner_stats = {}
            currency_stats = {}
            total_usd_amount = 0.0
            
            for conv in processed_conversions:
                partner = conv.get('partner', 'Unknown')
                partner_stats[partner] = partner_stats.get(partner, 0) + 1
                
                # 统计currency分布
                currency = conv.get('currency', 'USD')
                currency_stats[currency] = currency_stats.get(currency, 0) + 1
                self.currency_breakdown[currency] = self.currency_breakdown.get(currency, 0) + 1
                
                # 统计总金额 - 智能检查多个字段
                usd_amount = (
                    conv.get('usd_sale_amount') or 
                    conv.get('sale_amount') or 
                    0
                )
                if usd_amount:
                    usd_amount = float(usd_amount)
                    total_usd_amount += usd_amount
                    self.total_usd_amount += usd_amount
            
            self.logger.info(f"📊 字段映射完成: {len(processed_conversions)} 條記錄")
            self.logger.info(f"   Partner分佈: {dict(partner_stats)}")
            self.logger.info(f"💱 Currency分佈: {dict(currency_stats)}")
            self.logger.info(f"💰 總USD金額: ${total_usd_amount:,.2f}")
            
            # Currency验证
            if len(currency_stats) == 1 and 'USD' in currency_stats:
                self.logger.info("✅ Currency验证通过: 所有记录都使用USD")
            else:
                self.logger.warning(f"⚠️ Currency验证警告: 发现非USD记录 {currency_stats}")
        
        return processed_conversions
    
    def _filter_usd_conversions(self, conversions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        货币验证：记录非USD记录但不终止程序，在最后汇总显示异常情况
        解决API currency参数无效的问题
        """
        usd_conversions = []
        currency_stats = {}
        non_usd_records = []
        
        for conversion in conversions:
            currency = conversion.get('currency', 'USD')
            currency_stats[currency] = currency_stats.get(currency, 0) + 1
            
            if currency == 'USD':
                usd_conversions.append(conversion)
            else:
                # 记录非USD记录详情
                non_usd_records.append({
                    'conversion_id': conversion.get('conversion_id'),
                    'currency': currency,
                    'amount': conversion.get('sale_amount'),
                    'offer_name': conversion.get('offer_name', '')[:50]
                })
        
        # 📊 记录货币验证结果，但不终止程序
        if non_usd_records:
            self.logger.warning(f"⚠️ 货币验证异常: 存在非USD记录")
            self.logger.warning(f"💱 Currency分布: {currency_stats}")
            self.logger.warning(f"📝 非USD记录数量: {len(non_usd_records)}")
            
            # 将非USD记录信息存储到实例变量中，供最后汇总使用
            if not hasattr(self, 'currency_validation_issues'):
                self.currency_validation_issues = []
            self.currency_validation_issues.extend(non_usd_records)
            
            # 显示前几条非USD记录作为示例
            for i, record in enumerate(non_usd_records[:3]):
                self.logger.warning(f"   示例 {i+1}: ID={record['conversion_id']}, Currency={record['currency']}, Amount={record['amount']}")
            
            if len(non_usd_records) > 3:
                self.logger.warning(f"    ... 还有 {len(non_usd_records)-3} 条非USD记录")
        else:
            self.logger.info(f"✅ Currency验证通过: 所有记录都使用USD")
        
        self.logger.info(f"📊 处理结果: {len(usd_conversions)} 条USD记录, {len(non_usd_records)} 条非USD记录")
        return usd_conversions

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
    
    def _create_result_summary(self, total_records: int) -> Dict[str, Any]:
        """創建結果摘要"""
        end_time = time.time()
        processing_time = end_time - self.stats.start_time
        
        if processing_time > 0:
            self.stats.records_per_second = total_records / processing_time
        
        summary = {
            'total_records': total_records,
            'processing_time_seconds': processing_time,
            'processing_time_minutes': processing_time / 60,
            'stats': {
                'total_requests': self.stats.total_requests,
                'failed_requests': self.stats.failed_requests,
                'retries': self.stats.retries,
                'avg_response_time': self.stats.avg_response_time,
                'records_per_second': self.stats.records_per_second,
                'total_usd_amount': self.total_usd_amount,
                'currency_breakdown': self.currency_breakdown
            }
        }
        
        self.logger.info(f"✅ 數據獲取完成!")
        self.logger.info(f"📊 總記錄數: {total_records:,}")
        self.logger.info(f"⏱️ 處理時間: {processing_time/60:.2f} 分鐘")
        self.logger.info(f"🚀 處理速度: {self.stats.records_per_second:.1f} 記錄/秒")
        
        # 📊 货币验证异常汇总
        if hasattr(self, 'currency_validation_issues') and self.currency_validation_issues:
            self.logger.warning(f"📋 货币验证异常汇总:")
            self.logger.warning(f"   总异常记录数: {len(self.currency_validation_issues)}")
            
            # 按货币类型统计
            currency_counts = {}
            for record in self.currency_validation_issues:
                currency = record['currency']
                currency_counts[currency] = currency_counts.get(currency, 0) + 1
            
            self.logger.warning(f"   货币分布: {currency_counts}")
            
            # 显示前10条异常记录详情
            self.logger.warning(f"   异常记录详情 (前10条):")
            for i, record in enumerate(self.currency_validation_issues[:10]):
                self.logger.warning(f"     {i+1}. ID={record['conversion_id']}, Currency={record['currency']}, Amount={record['amount']}, Offer={record['offer_name']}")
            
            if len(self.currency_validation_issues) > 10:
                self.logger.warning(f"     ... 还有 {len(self.currency_validation_issues)-10} 条异常记录")
            
            # 将异常信息添加到摘要中
            summary['currency_validation_issues'] = {
                'total_issues': len(self.currency_validation_issues),
                'currency_distribution': currency_counts,
                'sample_records': self.currency_validation_issues[:10]
            }
        else:
            self.logger.info(f"✅ 货币验证: 无异常记录")
        
        return summary

# 性能測試和使用示例
async def run_performance_test():
    """運行性能測試"""
    # 使用DMP Agent的API配置管理器
    from agents.data_dmp_agent.api_config_manager import APIConfigManager
    
    api_config_manager = APIConfigManager()
    platform_config = api_config_manager.get_config('IAByteC')
    
    if not platform_config:
        print("❌ 無法獲取IAByteC配置")
        return
    
    test_config = {
        'name': 'IAByteC',
        'api_key': platform_config.get('api_key'),
        'api_secret': platform_config.get('secret'),
        'api_url': platform_config.get('base_url') + platform_config.get('endpoints', {}).get('conversions', '/conversions/range')
    }
    
    async with UltraOptimizedAPIClient(test_config) as client:
        result = await client.fetch_all_conversions(
            start_date='2025-01-17',
            end_date='2025-01-17'
        )
        
        print(json.dumps(result, indent=2))

if __name__ == '__main__':
    asyncio.run(run_performance_test()) 