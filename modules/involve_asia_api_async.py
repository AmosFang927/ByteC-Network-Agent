#!/usr/bin/env python3
"""
Involve Asia API 异步模块
使用 httpx 和 asyncio 实现高性能异步数据获取
支持并发分页请求，显著提升API调用性能
"""

import httpx
import asyncio
import json
import time
import os
import sys
from datetime import datetime
from typing import Optional, Dict, List, Tuple, Any
from utils.logger import print_step
import config

# 重用现有的ResourceMonitor类
from modules.involve_asia_api import ResourceMonitor

class AsyncInvolveAsiaAPI:
    """Involve Asia API异步客户端"""
    
    def __init__(self, api_secret=None, api_key=None):
        # 使用配置文件中的值或传入的值
        self.api_secret = api_secret or config.INVOLVE_ASIA_API_SECRET
        self.api_key = api_key or config.INVOLVE_ASIA_API_KEY
        
        # API端点
        self.auth_url = config.INVOLVE_ASIA_AUTH_URL
        self.conversions_url = config.INVOLVE_ASIA_CONVERSIONS_URL
        
        # 认证token
        self.token = None
        
        # 资源监控器
        self.resource_monitor = ResourceMonitor()
        
        # 跳过的页面记录
        self.skipped_pages = []
        
        # 请求配置 - 针对超时问题优化
        self.request_timeout = getattr(config, 'REQUEST_TIMEOUT', 45)  # 增加单个请求超时
        self.max_retries = getattr(config, 'MAX_RETRY_ATTEMPTS', 3)  # 减少重试次数，加快失败恢复
        self.request_delay = getattr(config, 'REQUEST_DELAY', 0.2)  # 减少请求间隔，提高速度
        
        # 并发配置
        self.max_concurrent_requests = getattr(config, 'MAX_CONCURRENT_REQUESTS', 5)
        self.semaphore = None
        
        # HTTP客户端配置
        self.client_config = {
            'timeout': httpx.Timeout(self.request_timeout),
            'limits': httpx.Limits(
                max_keepalive_connections=10,
                max_connections=20,
                keepalive_expiry=30
            ),
            'follow_redirects': True
        }
    
    async def authenticate(self) -> bool:
        """执行API认证"""
        print_step("异步认证", "正在执行API认证...")
        
        headers = {"Accept": "application/json"}
        data = {
            "secret": self.api_secret,
            "key": self.api_key
        }
        
        try:
            async with httpx.AsyncClient(**self.client_config) as client:
                response = await client.post(
                    self.auth_url,
                    headers=headers,
                    data=data
                )
                response.raise_for_status()
                
                result = response.json()
                
                if "data" in result and "token" in result["data"]:
                    self.token = result["data"]["token"]
                    token_preview = self.token[:8] + "..." if len(self.token) > 8 else self.token
                    print_step("认证成功", f"获得Token: {token_preview}")
                    return True
                else:
                    print_step("认证失败", f"响应结构不符合预期: {result}")
                    return False
                    
        except httpx.RequestError as e:
            print_step("认证失败", f"请求错误: {str(e)}")
            return False
        except json.JSONDecodeError as e:
            print_step("认证失败", f"JSON解析错误: {str(e)}")
            return False
        except Exception as e:
            print_step("认证失败", f"未知错误: {str(e)}")
            return False
    
    async def _make_single_request(self, client: httpx.AsyncClient, page: int, 
                                 start_date: str, end_date: str, currency: str,
                                 api_label: str = "") -> Tuple[Optional[Dict], bool, int]:
        """发送单个页面请求"""
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.token}"
        }
        
        data = {
            "page": str(page),
            "limit": str(config.DEFAULT_PAGE_LIMIT),
            "start_date": start_date,
            "end_date": end_date,
            "filters[preferred_currency]": currency
        }
        
        max_retries = self.max_retries
        retry_count = 0
        
        while retry_count <= max_retries:
            try:
                if retry_count > 0:
                    wait_time = min(60, 10 * retry_count)
                    print(f"   🔄 第{page}页第{retry_count}次重试，等待{wait_time}秒...")
                    await asyncio.sleep(wait_time)
                
                # 使用信号量控制并发数量
                async with self.semaphore:
                    response = await client.post(
                        self.conversions_url,
                        headers=headers,
                        data=data
                    )
                    
                    # 处理429错误(频率限制)
                    if response.status_code == 429:
                        retry_count += 1
                        print(f"   ⚠️  第{page}页遇到频率限制，等待{config.RATE_LIMIT_DELAY}秒后重试...")
                        await asyncio.sleep(config.RATE_LIMIT_DELAY)
                        continue
                    
                    response.raise_for_status()
                    result = response.json()
                    
                    if "data" not in result:
                        print_step("数据获取失败", f"第{page}页响应中没有data字段: {result}")
                        retry_count += 1
                        continue
                    
                    # 请求成功
                    return result, True, page
                    
            except httpx.TimeoutException as e:
                retry_count += 1
                print_step("请求超时", f"第{page}页请求超时（第{retry_count}次重试）: {str(e)}")
                if retry_count <= max_retries:
                    self.resource_monitor.print_resource_status(f"第{page}页超时重试{retry_count}")
                
            except httpx.RequestError as e:
                retry_count += 1
                print_step("网络错误", f"第{page}页请求错误（第{retry_count}次重试）: {str(e)}")
                if retry_count <= max_retries:
                    self.resource_monitor.print_resource_status(f"第{page}页网络错误重试{retry_count}")
                
            except json.JSONDecodeError as e:
                retry_count += 1
                print_step("解析错误", f"第{page}页JSON解析错误（第{retry_count}次重试）: {str(e)}")
                if retry_count <= max_retries:
                    self.resource_monitor.print_resource_status(f"第{page}页解析错误重试{retry_count}")
            
            except Exception as e:
                retry_count += 1
                print_step("未知错误", f"第{page}页未知错误（第{retry_count}次重试）: {str(e)}")
                if retry_count <= max_retries:
                    self.resource_monitor.print_resource_status(f"第{page}页未知错误重试{retry_count}")
            
            # 添加重试延迟
            if retry_count <= max_retries:
                await asyncio.sleep(self.request_delay)
        
        # 重试次数用完，返回失败
        return None, False, page
    
    async def _fetch_pages_concurrently(self, pages: List[int], start_date: str, 
                                      end_date: str, currency: str, api_label: str = "") -> List[Tuple]:
        """并发获取多个页面"""
        print_step("并发请求", f"{api_label}开始并发获取 {len(pages)} 页数据...")
        
        # 创建信号量控制并发数量
        self.semaphore = asyncio.Semaphore(self.max_concurrent_requests)
        
        async with httpx.AsyncClient(**self.client_config) as client:
            # 创建所有页面的请求任务
            tasks = [
                self._make_single_request(client, page, start_date, end_date, currency, api_label)
                for page in pages
            ]
            
            # 并发执行所有请求
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理结果
            successful_results = []
            failed_pages = []
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    failed_pages.append(pages[i])
                    print_step("页面异常", f"第{pages[i]}页发生异常: {str(result)}")
                elif result[1]:  # 成功
                    successful_results.append(result)
                else:  # 失败
                    failed_pages.append(result[2])
            
            if failed_pages:
                self.skipped_pages.extend(failed_pages)
                print_step("页面跳过", f"跳过失败页面: {failed_pages}")
            
            print_step("并发完成", f"{api_label}并发请求完成，成功: {len(successful_results)}, 失败: {len(failed_pages)}")
            return successful_results
    
    async def get_conversions_async(self, start_date: str, end_date: str, 
                                  currency: Optional[str] = None, api_name: Optional[str] = None) -> Optional[Dict]:
        """异步获取指定日期范围的所有conversion数据"""
        if not self.token:
            print_step("数据获取失败", "没有有效的认证token")
            return None
        
        currency = currency or config.PREFERRED_CURRENCY
        api_label = f"[{api_name}] " if api_name else ""
        print_step("异步数据获取", f"{api_label}开始异步获取转换数据 ({start_date} 到 {end_date})")
        
        # 显示初始资源状态
        self.resource_monitor.print_resource_status(f"{api_label}异步数据获取开始")
        
        all_conversions = []
        total_count = 0
        total_pages = 0
        pages_fetched = 0
        
        # 步骤1: 获取第一页以确定总页数
        print_step("获取元数据", f"{api_label}获取第一页以确定总页数...")
        
        first_page_results = await self._fetch_pages_concurrently(
            [1], start_date, end_date, currency, api_label
        )
        
        if not first_page_results:
            print_step("数据获取失败", f"{api_label}无法获取第一页数据")
            return None
        
        first_result, _, _ = first_page_results[0]
        data_obj = first_result["data"]
        
        if isinstance(data_obj, dict):
            first_page_data = data_obj.get("data", [])
            limit = data_obj.get("limit", config.DEFAULT_PAGE_LIMIT)
            total_count = data_obj.get("count", 0)
            
            # 计算总页数
            if total_count > 0:
                total_pages = (total_count + limit - 1) // limit
            
            all_conversions.extend(first_page_data)
            pages_fetched = 1
            
            print_step("元数据获取", f"{api_label}总记录数: {total_count}, 总页数: {total_pages}")
            
            # 检查记录数限制
            if config.MAX_RECORDS_LIMIT is not None and total_count > config.MAX_RECORDS_LIMIT:
                actual_pages = (config.MAX_RECORDS_LIMIT + limit - 1) // limit
                total_pages = min(total_pages, actual_pages)
                print_step("记录限制", f"{api_label}应用记录数限制，调整页数到: {total_pages}")
        else:
            # 旧格式兼容处理
            first_page_data = first_result["data"] if isinstance(first_result["data"], list) else []
            all_conversions.extend(first_page_data)
            pages_fetched = 1
            total_pages = 10  # 默认假设有更多页面
        
        # 步骤2: 如果有更多页面，并发获取
        if total_pages > 1:
            remaining_pages = list(range(2, min(total_pages + 1, 1001)))  # 最多获取1000页避免无限请求
            
            # 检查记录数限制
            if config.MAX_RECORDS_LIMIT is not None:
                max_pages = (config.MAX_RECORDS_LIMIT + limit - 1) // limit
                remaining_pages = [p for p in remaining_pages if p <= max_pages]
            
            if remaining_pages:
                print_step("并发策略", f"{api_label}将并发获取剩余 {len(remaining_pages)} 页数据")
                
                # 分批并发处理，避免一次性发送太多请求
                batch_size = min(self.max_concurrent_requests * 2, 10)  # 每批最多10页
                
                for i in range(0, len(remaining_pages), batch_size):
                    batch_pages = remaining_pages[i:i + batch_size]
                    print_step("批次处理", f"{api_label}处理第 {i//batch_size + 1} 批，页面: {batch_pages}")
                    
                    batch_results = await self._fetch_pages_concurrently(
                        batch_pages, start_date, end_date, currency, api_label
                    )
                    
                    # 处理批次结果
                    for result, success, page in batch_results:
                        if success and result:
                            data_obj = result["data"]
                            
                            if isinstance(data_obj, dict):
                                page_data = data_obj.get("data", [])
                                all_conversions.extend(page_data)
                                pages_fetched += 1
                                
                                print(f"   {api_label}📊 第 {page} 页: 获取到 {len(page_data)} 条记录")
                            else:
                                # 旧格式兼容
                                page_data = result["data"] if isinstance(result["data"], list) else []
                                all_conversions.extend(page_data)
                                pages_fetched += 1
                    
                    # 检查记录数限制
                    if config.MAX_RECORDS_LIMIT is not None and len(all_conversions) >= config.MAX_RECORDS_LIMIT:
                        all_conversions = all_conversions[:config.MAX_RECORDS_LIMIT]
                        print_step("记录限制", f"{api_label}已达到记录数限制 ({config.MAX_RECORDS_LIMIT} 条)，停止获取")
                        break
                    
                    # 批次间添加短暂延迟
                    if i + batch_size < len(remaining_pages):
                        await asyncio.sleep(self.request_delay)
        
        # 显示最终资源状态
        self.resource_monitor.print_resource_status(f"{api_label}异步数据获取完成")
        
        if all_conversions:
            # 构造完整结果
            result = {
                "status": "success",
                "message": "Success",
                "data": {
                    "page": 1,
                    "limit": config.DEFAULT_PAGE_LIMIT,
                    "count": total_count or len(all_conversions),
                    "total_pages": total_pages,
                    "pages_fetched": pages_fetched,
                    "skipped_pages": self.skipped_pages,
                    "current_page_count": len(all_conversions),
                    "data": all_conversions,
                    "async_mode": True,
                    "concurrent_requests": self.max_concurrent_requests
                }
            }
            
            success_msg = f"{api_label}异步获取成功: {len(all_conversions)} 条转换记录，共 {pages_fetched} 页"
            if self.skipped_pages:
                success_msg += f"，跳过 {len(self.skipped_pages)} 页: {self.skipped_pages}"
            
            print_step("异步获取成功", success_msg)
            return result
        else:
            print_step("数据获取失败", f"{api_label}没有获取到任何数据")
            return None
    
    def get_conversions(self, start_date: str, end_date: str, 
                       currency: Optional[str] = None, api_name: Optional[str] = None) -> Optional[Dict]:
        """同步包装器，运行异步获取函数"""
        return asyncio.run(self.get_conversions_async(start_date, end_date, currency, api_name))
    
    async def get_conversions_default_range_async(self, currency: Optional[str] = None) -> Optional[Dict]:
        """使用默认日期范围异步获取数据"""
        start_date, end_date = config.get_default_date_range()
        return await self.get_conversions_async(start_date, end_date, currency)
    
    def get_conversions_default_range(self, currency: Optional[str] = None) -> Optional[Dict]:
        """使用默认日期范围获取数据的同步包装器"""
        return asyncio.run(self.get_conversions_default_range_async(currency))
    
    def save_to_json(self, data: Dict, filename: Optional[str] = None) -> Optional[str]:
        """保存数据到JSON文件"""
        if not data:
            print_step("保存失败", "没有数据可保存")
            return None
        
        # 确保输出目录存在
        config.ensure_output_dirs()
        
        if not filename:
            filename = config.get_json_filename()
        
        filepath = os.path.join(config.OUTPUT_DIR, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print_step("JSON保存成功", f"数据已保存到: {filepath}")
            return filepath
            
        except Exception as e:
            print_step("JSON保存失败", f"保存失败: {str(e)}")
            return None
    
    def get_skipped_pages_summary(self) -> str:
        """获取跳过页面的摘要信息"""
        if not self.skipped_pages:
            return "没有跳过任何页面"
        
        return f"跳过了 {len(self.skipped_pages)} 个页面: {self.skipped_pages}"
    
    def print_final_summary(self):
        """打印最终摘要报告"""
        print(f"\n{'='*60}")
        print("📋 异步API数据获取摘要报告")
        print(f"{'='*60}")
        
        # 运行时间
        runtime = self.resource_monitor.get_runtime_info()
        print(f"⏱️  总运行时间: {runtime['runtime_formatted']}")
        
        # 异步配置信息
        print(f"🚀 异步配置: 最大并发请求数 {self.max_concurrent_requests}")
        
        # 跳过页面信息
        if self.skipped_pages:
            print(f"⚠️  跳过页面: {len(self.skipped_pages)} 个页面 - {self.skipped_pages}")
        else:
            print("✅ 跳过页面: 无")
        
        # 最终资源状态
        self.resource_monitor.print_resource_status("最终状态", show_details=True)
        
        print(f"{'='*60}\n")

# 便捷函数，用于向后兼容
def get_conversions_async(start_date: str, end_date: str, 
                         api_secret: Optional[str] = None, api_key: Optional[str] = None,
                         currency: Optional[str] = None, api_name: Optional[str] = None) -> Optional[Dict]:
    """
    便捷的异步conversion数据获取函数
    
    Args:
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        api_secret: API Secret，默认使用配置文件中的值
        api_key: API Key，默认使用配置文件中的值
        currency: 货币类型，默认使用配置文件中的值
        api_name: API名称，用于日志标识
    
    Returns:
        dict: conversion数据，如果失败返回None
    """
    api = AsyncInvolveAsiaAPI(api_secret, api_key)
    
    # 异步认证和获取数据
    async def fetch_data():
        if await api.authenticate():
            return await api.get_conversions_async(start_date, end_date, currency, api_name)
        return None
    
    return asyncio.run(fetch_data())

# 性能测试函数
def compare_sync_vs_async_performance(start_date: str, end_date: str, 
                                    test_pages: int = 5) -> Dict[str, Any]:
    """
    比较同步vs异步性能
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        test_pages: 测试页数
    
    Returns:
        dict: 性能比较结果
    """
    print_step("性能测试", f"开始比较同步vs异步性能 (测试{test_pages}页)")
    
    # 限制测试范围避免过多API调用
    original_limit = getattr(config, 'MAX_RECORDS_LIMIT', None)
    config.MAX_RECORDS_LIMIT = test_pages * config.DEFAULT_PAGE_LIMIT
    
    try:
        # 测试异步版本
        print_step("异步测试", "测试异步API性能...")
        async_start = time.time()
        async_api = AsyncInvolveAsiaAPI()
        
        async def test_async():
            if await async_api.authenticate():
                return await async_api.get_conversions_async(start_date, end_date, currency=config.PREFERRED_CURRENCY)
            return None
        
        async_result = asyncio.run(test_async())
        async_time = time.time() - async_start
        
        # 测试同步版本（导入原始模块）
        print_step("同步测试", "测试同步API性能...")
        from modules.involve_asia_api import InvolveAsiaAPI
        
        sync_start = time.time()
        sync_api = InvolveAsiaAPI()
        sync_result = None
        
        if sync_api.authenticate():
            sync_result = sync_api.get_conversions(start_date, end_date, currency=config.PREFERRED_CURRENCY)
        
        sync_time = time.time() - sync_start
        
        # 计算性能提升
        performance_ratio = sync_time / async_time if async_time > 0 else 0
        time_saved = sync_time - async_time
        
        result = {
            "async_time": async_time,
            "sync_time": sync_time,
            "performance_ratio": performance_ratio,
            "time_saved_seconds": time_saved,
            "async_records": len(async_result.get("data", {}).get("data", [])) if async_result else 0,
            "sync_records": len(sync_result.get("data", {}).get("data", [])) if sync_result else 0,
            "async_success": async_result is not None,
            "sync_success": sync_result is not None
        }
        
        print_step("性能测试结果", 
                  f"异步: {async_time:.2f}s, 同步: {sync_time:.2f}s, "
                  f"性能提升: {performance_ratio:.2f}x, 节省时间: {time_saved:.2f}s")
        
        return result
        
    finally:
        # 恢复原始设置
        config.MAX_RECORDS_LIMIT = original_limit

# 导出主要类和函数
__all__ = [
    'AsyncInvolveAsiaAPI',
    'get_conversions_async', 
    'compare_sync_vs_async_performance'
] 