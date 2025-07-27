#!/usr/bin/env python3
"""
Involve Asia API 模块
负责从Involve Asia获取conversion数据
增强版本：包含资源监控、重试机制和跳过机制
"""

import requests
import json
import time
import psutil
import threading
import os
import sys
import socket
from datetime import datetime
from utils.logger import print_step
import config

class ResourceMonitor:
    """系统资源监控器"""
    
    def __init__(self):
        self.start_time = time.time()
        self.initial_memory = self.get_memory_usage()
        
    def get_memory_usage(self):
        """获取内存使用情况"""
        try:
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            return {
                'rss': memory_info.rss / 1024 / 1024,  # MB
                'vms': memory_info.vms / 1024 / 1024,  # MB
                'percent': process.memory_percent()
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_cpu_usage(self):
        """获取CPU使用情况"""
        try:
            process = psutil.Process(os.getpid())
            cpu_percent = process.cpu_percent(interval=1)
            system_cpu = psutil.cpu_percent(interval=1)
            return {
                'process_cpu': cpu_percent,
                'system_cpu': system_cpu,
                'cpu_count': psutil.cpu_count()
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_network_info(self):
        """获取网络连接信息"""
        try:
            connections = psutil.net_connections(kind='inet')
            established = len([c for c in connections if c.status == 'ESTABLISHED'])
            return {
                'total_connections': len(connections),
                'established_connections': established,
                'network_io': psutil.net_io_counters()._asdict()
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_disk_usage(self):
        """获取磁盘使用情况"""
        try:
            disk_usage = psutil.disk_usage('/')
            return {
                'total': disk_usage.total / 1024 / 1024 / 1024,  # GB
                'used': disk_usage.used / 1024 / 1024 / 1024,   # GB
                'free': disk_usage.free / 1024 / 1024 / 1024,   # GB
                'percent': (disk_usage.used / disk_usage.total) * 100
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_json_files_info(self, output_dir=None):
        """获取JSON文件大小信息"""
        if output_dir is None:
            output_dir = config.OUTPUT_DIR
        
        json_files = []
        total_size = 0
        
        try:
            if os.path.exists(output_dir):
                for file in os.listdir(output_dir):
                    if file.endswith('.json'):
                        file_path = os.path.join(output_dir, file)
                        file_size = os.path.getsize(file_path) / 1024 / 1024  # MB
                        json_files.append({
                            'name': file,
                            'size_mb': file_size,
                            'modified': datetime.fromtimestamp(os.path.getmtime(file_path))
                        })
                        total_size += file_size
            
            return {
                'files': json_files,
                'total_size_mb': total_size,
                'count': len(json_files)
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_runtime_info(self):
        """获取运行时间信息"""
        runtime = time.time() - self.start_time
        return {
            'runtime_seconds': runtime,
            'runtime_formatted': f"{int(runtime//3600)}h {int((runtime%3600)//60)}m {int(runtime%60)}s"
        }
    
    def check_connectivity(self, host='8.8.8.8', port=53, timeout=5):
        """检查网络连接"""
        try:
            socket.setdefaulttimeout(timeout)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
            return True
        except socket.error:
            return False
    
    def print_resource_status(self, prefix="", show_details=True):
        """打印完整的资源使用状态"""
        print(f"\n{'='*60}")
        print(f"🔍 {prefix} 系统资源监控报告")
        print(f"{'='*60}")
        
        # 运行时间
        runtime = self.get_runtime_info()
        print(f"⏱️  运行时间: {runtime['runtime_formatted']}")
        
        # 内存使用
        memory = self.get_memory_usage()
        if 'error' not in memory:
            print(f"💾 内存使用: {memory['rss']:.1f}MB (RSS), {memory['vms']:.1f}MB (VMS), {memory['percent']:.1f}%")
        else:
            print(f"💾 内存使用: 获取失败 - {memory['error']}")
        
        # CPU使用
        cpu = self.get_cpu_usage()
        if 'error' not in cpu:
            print(f"⚡ CPU使用: 进程 {cpu['process_cpu']:.1f}%, 系统 {cpu['system_cpu']:.1f}% (共{cpu['cpu_count']}核)")
        else:
            print(f"⚡ CPU使用: 获取失败 - {cpu['error']}")
        
        # 网络信息
        network = self.get_network_info()
        if 'error' not in network:
            print(f"🌐 网络连接: {network['established_connections']}/{network['total_connections']} (已建立/总数)")
            connectivity = self.check_connectivity()
            print(f"🌐 网络连通性: {'✅ 正常' if connectivity else '❌ 异常'}")
        else:
            print(f"🌐 网络信息: 获取失败 - {network['error']}")
        
        # 磁盘使用
        disk = self.get_disk_usage()
        if 'error' not in disk:
            print(f"💿 磁盘使用: {disk['used']:.1f}GB/{disk['total']:.1f}GB ({disk['percent']:.1f}%)")
        else:
            print(f"💿 磁盘使用: 获取失败 - {disk['error']}")
        
        # JSON文件信息
        json_info = self.get_json_files_info()
        if 'error' not in json_info:
            print(f"📄 JSON文件: {json_info['count']} 个文件, 总大小 {json_info['total_size_mb']:.1f}MB")
            if show_details and json_info['files']:
                print("   详细信息:")
                for file in json_info['files'][-3:]:  # 显示最新的3个文件
                    print(f"     - {file['name']}: {file['size_mb']:.1f}MB")
        else:
            print(f"📄 JSON文件: 获取失败 - {json_info['error']}")
        
        print(f"{'='*60}\n")

class InvolveAsiaAPI:
    """Involve Asia API客户端 - 增强版"""
    
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
        
        # 请求超时设置
        self.request_timeout = config.REQUEST_TIMEOUT
        self.max_retries = config.MAX_RETRIES
        self.request_delay = config.REQUEST_DELAY
        
        # 性能优化设置
        self.enable_fast_mode = config.ENABLE_FAST_MODE
        self.reduce_logging = config.REDUCE_LOGGING_IN_PRODUCTION
        self.optimize_for_cloud = config.OPTIMIZE_FOR_CLOUD_RUN
    
    def authenticate(self):
        """执行API认证"""
        print_step("认证步骤", "正在执行API认证...")
        
        headers = {"Accept": "application/json"}
        data = {
            "secret": self.api_secret,
            "key": self.api_key
        }
        
        try:
            response = requests.post(
                self.auth_url, 
                headers=headers, 
                data=data, 
                timeout=self.request_timeout
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
                
        except requests.exceptions.RequestException as e:
            print_step("认证失败", f"请求错误: {str(e)}")
            return False
        except json.JSONDecodeError as e:
            print_step("认证失败", f"JSON解析错误: {str(e)}")
            return False
    
    def _make_request_with_timeout(self, url, headers, data, timeout):
        """使用超时机制发送请求"""
        class RequestResult:
            def __init__(self):
                self.response = None
                self.exception = None
                self.completed = False
        
        result = RequestResult()
        
        def make_request():
            try:
                result.response = requests.post(url, headers=headers, data=data, timeout=timeout)
                result.completed = True
            except Exception as e:
                result.exception = e
                result.completed = True
        
        thread = threading.Thread(target=make_request)
        thread.daemon = True
        thread.start()
        
        # 等待请求完成或超时
        thread.join(timeout + 5)  # 额外5秒缓冲
        
        if not result.completed:
            print_step("请求超时", f"请求超时 ({timeout}s)，可能遇到网络问题")
            # 显示资源状态
            self.resource_monitor.print_resource_status("请求超时时")
            raise requests.exceptions.Timeout(f"Request timed out after {timeout}s")
        
        if result.exception:
            raise result.exception
        
        return result.response
    
    def _handle_page_request(self, page, headers, data, api_label=""):
        """处理单页请求，包含重试和跳过机制"""
        max_retries = 5  # 用户要求的最大重试次数
        retry_count = 0
        page_success = False
        
        while retry_count <= max_retries and not page_success:
            try:
                if retry_count > 0:
                    wait_time = min(60, 10 * retry_count)  # 增量等待时间，最多60秒
                    print(f"   �� 第 {retry_count} 次重试，等待 {wait_time} 秒...")
                    time.sleep(wait_time)
                
                # 使用增强的请求方法
                response = self._make_request_with_timeout(
                    self.conversions_url, 
                    headers, 
                    data, 
                    self.request_timeout
                )
                
                # 处理429错误(频率限制)
                if response.status_code == 429:
                    retry_count += 1
                    print(f"   ⚠️  遇到频率限制，等待{config.RATE_LIMIT_DELAY}秒后重试...")
                    time.sleep(config.RATE_LIMIT_DELAY)
                    continue
                
                response.raise_for_status()
                result = response.json()
                
                if "data" not in result:
                    print_step("数据获取失败", f"响应中没有data字段: {result}")
                    retry_count += 1
                    continue
                
                # 请求成功
                page_success = True
                return result, True
                
            except requests.exceptions.Timeout as e:
                retry_count += 1
                print_step("请求超时", f"第{page}页请求超时（第{retry_count}次重试）: {str(e)}")
                if retry_count <= max_retries:
                    # 显示资源状态
                    self.resource_monitor.print_resource_status(f"第{page}页超时重试{retry_count}")
                
            except requests.exceptions.RequestException as e:
                retry_count += 1
                print_step("网络错误", f"第{page}页请求错误（第{retry_count}次重试）: {str(e)}")
                if retry_count <= max_retries:
                    # 显示资源状态
                    self.resource_monitor.print_resource_status(f"第{page}页网络错误重试{retry_count}")
                
            except json.JSONDecodeError as e:
                retry_count += 1
                print_step("解析错误", f"第{page}页JSON解析错误（第{retry_count}次重试）: {str(e)}")
                if retry_count <= max_retries:
                    # 显示资源状态
                    self.resource_monitor.print_resource_status(f"第{page}页解析错误重试{retry_count}")
            
            except Exception as e:
                retry_count += 1
                print_step("未知错误", f"第{page}页未知错误（第{retry_count}次重试）: {str(e)}")
                if retry_count <= max_retries:
                    # 显示资源状态
                    self.resource_monitor.print_resource_status(f"第{page}页未知错误重试{retry_count}")
        
        # 重试次数用完，返回失败
        return None, False
    
    def get_conversions(self, start_date, end_date, currency=None, api_name=None, limit=None, partner=None):
        """获取指定日期范围的所有conversion数据 - 增强版"""
        if not self.token:
            print_step("数据获取失败", "没有有效的认证token")
            return None
        
        currency = currency or config.PREFERRED_CURRENCY
        api_label = f"[{api_name}] " if api_name else ""
        limit_info = f" (限制: {limit})" if limit else ""
        print_step("数据获取", f"{api_label}正在获取转换数据 ({start_date} 到 {end_date}){limit_info}")
        
        # 显示初始资源状态
        self.resource_monitor.print_resource_status(f"{api_label}数据获取开始")
        
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.token}"
        }
        
        all_conversions = []
        page = 1
        total_count = 0
        total_pages = 0
        pages_fetched = 0
        skipped_pages = []
        data_complete = False
        
        # 決定每頁的限制數量
        # 如果用戶指定了limit且小於DEFAULT_PAGE_LIMIT，使用用戶指定的limit
        # 否則使用DEFAULT_PAGE_LIMIT進行分頁
        page_limit = config.DEFAULT_PAGE_LIMIT
        if limit and limit < config.DEFAULT_PAGE_LIMIT:
            page_limit = limit
        
        # 获取 Partner 的 Sources
        sources = []
        if partner:
            sources = config.get_sources_for_partner(partner)
            print_step("Source过滤", f"为 {partner} 获取数据，Sources: {sources}")
        
        while not data_complete:
            # 檢查是否已達到限制
            if limit and len(all_conversions) >= limit:
                print(f"   [限制達到] 已獲取 {len(all_conversions)} 條記錄，達到限制 {limit}")
                data_complete = True
                break
            
            page_label = f"{api_label}🔄 正在获取第 {page} 页数据..." if api_name else f"\n🔄 正在获取第 {page} 页数据..."
            print(page_label)
            
            # 构建请求数据
            data = {
                "page": str(page),
                "limit": str(page_limit),
                "start_date": start_date,
                "end_date": end_date,
                "filters[preferred_currency]": currency
            }
            
            # 添加 Source 过滤
            if sources:
                data["filters[aff_sub1]"] = sources
                print(f"   📋 应用 Source 过滤: {sources}")
            
            # 使用增强的请求处理方法
            result, success = self._handle_page_request(page, headers, data, api_label)
            
            if success and result:
                data_obj = result["data"]
                
                # 获取分页信息
                if isinstance(data_obj, dict):
                    page_data = data_obj.get("data", [])
                    current_page = data_obj.get("page", page)
                    limit_returned = data_obj.get("limit", page_limit)
                    total_count = data_obj.get("count", 0)
                    next_page = data_obj.get("nextPage")
                    
                    # 计算总页数
                    if total_count > 0:
                        total_pages = (total_count + page_limit - 1) // page_limit
                    
                    pages_fetched += 1
                    api_current_total = len(all_conversions) + len(page_data)
                    
                    print(f"   {api_label}📊 第 {current_page} 页: 获取到 {len(page_data)} 条记录")
                    print(f"   {api_label}📈 进度: {current_page}/{total_pages} 页 ({api_current_total}/{total_count} 条)")
                    
                    # 添加到总数据中
                    all_conversions.extend(page_data)
                    
                    # 如果設置了總限制，並且即將超過，則截斷數據
                    if limit and len(all_conversions) > limit:
                        excess_count = len(all_conversions) - limit
                        all_conversions = all_conversions[:limit]
                        print(f"   {api_label}✂️ 截斷多餘數據: 移除 {excess_count} 條記錄")
                        data_complete = True
                        break
                    
                    # 判断是否还有下一页
                    has_next_page = next_page and next_page > current_page and len(page_data) > 0
                    
                    if not has_next_page:
                        print(f"   {api_label}✅ 已获取完所有数据！")
                        data_complete = True
                        break
                    
                    # 额外安全检查
                    if total_pages > 0 and current_page >= total_pages:
                        print(f"   {api_label}✅ 已达到最大页数！")
                        data_complete = True
                        break
                    
                    page = next_page
                    
                else:
                    # 旧格式兼容
                    page_data = result["data"] if isinstance(result["data"], list) else []
                    all_conversions.extend(page_data)
                    pages_fetched += 1
                    
                    # 如果設置了總限制，並且即將超過，則截斷數據
                    if limit and len(all_conversions) > limit:
                        excess_count = len(all_conversions) - limit
                        all_conversions = all_conversions[:limit]
                        print(f"   {api_label}✂️ 截斷多餘數據: 移除 {excess_count} 條記錄")
                        data_complete = True
                        break
                    
                    if len(page_data) < page_limit:
                        data_complete = True
                        break
                    page += 1
                
                # 添加延迟避免请求过快
                time.sleep(self.request_delay)
                
            else:
                # 页面获取失败，记录跳过的页面
                skipped_pages.append(page)
                self.skipped_pages.append(page)
                
                print_step("页面跳过", f"❌ 第{page}页重试{self.max_retries}次后仍失败，跳过该页面继续获取下一页")
                
                # 显示跳过时的资源状态
                self.resource_monitor.print_resource_status(f"第{page}页跳过")
                
                # 继续下一页
                page += 1
                
                # 安全检查：如果跳过的页面太多，可能需要停止
                if len(skipped_pages) > 10:  # 如果跳过超过10页，停止获取
                    print_step("获取终止", f"❌ 跳过页面过多({len(skipped_pages)}页)，终止数据获取")
                    break
        
        # 显示最终资源状态
        self.resource_monitor.print_resource_status(f"{api_label}数据获取完成")
        
        if all_conversions:
            # 构造完整结果
            result = {
                "status": "success",
                "message": "Success",
                "data": {
                    "page": 1,
                    "limit": config.DEFAULT_PAGE_LIMIT,
                    "count": total_count,
                    "total_pages": total_pages,
                    "pages_fetched": pages_fetched,
                    "skipped_pages": skipped_pages,
                    "current_page_count": len(all_conversions),
                    "data": all_conversions
                }
            }
            
            success_msg = f"{api_label}成功获取数据: {len(all_conversions)} 条转换记录，共 {pages_fetched} 页"
            if skipped_pages:
                success_msg += f"，跳过 {len(skipped_pages)} 页: {skipped_pages}"
            
            print_step("数据获取成功", success_msg)
            return result
        else:
            print_step("数据获取失败", f"{api_label}没有获取到任何数据")
            return None
    
    def get_conversions_default_range(self, currency=None):
        """使用默认日期范围获取数据"""
        start_date, end_date = config.get_default_date_range()
        return self.get_conversions(start_date, end_date, currency)
    
    def save_to_json(self, data, filename=None):
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
    
    def get_skipped_pages_summary(self):
        """获取跳过页面的摘要信息"""
        if not self.skipped_pages:
            return "没有跳过任何页面"
        
        return f"跳过了 {len(self.skipped_pages)} 个页面: {self.skipped_pages}"
    
    def print_final_summary(self):
        """打印最终摘要报告"""
        print(f"\n{'='*60}")
        print("📋 API数据获取摘要报告")
        print(f"{'='*60}")
        
        # 运行时间
        runtime = self.resource_monitor.get_runtime_info()
        print(f"⏱️  总运行时间: {runtime['runtime_formatted']}")
        
        # 跳过页面信息
        if self.skipped_pages:
            print(f"⚠️  跳过页面: {len(self.skipped_pages)} 个页面 - {self.skipped_pages}")
        else:
            print("✅ 跳过页面: 无")
        
        # 最终资源状态
        self.resource_monitor.print_resource_status("最终状态", show_details=True)
        
        print(f"{'='*60}\n") 