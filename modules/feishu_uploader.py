#!/usr/bin/env python3
"""
飞书上传模块
负责将Excel文件上传到飞书Sheet
"""

import requests
import os
import json
import ssl
from datetime import datetime
from utils.logger import print_step
import config
import urllib3

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    import lark_oapi as lark
    from lark_oapi.api.drive.v1 import *
    LARK_SDK_AVAILABLE = True
except ImportError:
    LARK_SDK_AVAILABLE = False
    print("警告: lark_oapi SDK未安装，将使用REST API方式")

class FeishuUploader:
    """飞书文件上传器"""
    
    def __init__(self, access_token=None):
        self.app_id = config.FEISHU_APP_ID
        self.app_secret = config.FEISHU_APP_SECRET
        self.auth_url = config.FEISHU_AUTH_URL
        self.access_token = access_token  # 如果提供了就直接使用
        self.upload_url = config.FEISHU_UPLOAD_URL
        self.parent_node = config.FEISHU_PARENT_NODE
        self.file_type = config.FEISHU_FILE_TYPE
    
    def authenticate(self):
        """
        使用app_id和app_secret获取tenant_access_token
        
        Returns:
            bool: 认证是否成功
        """
        print_step("飞书认证", "正在获取tenant_access_token...")
        
        try:
            headers = {
                'Content-Type': 'application/json; charset=utf-8'
            }
            
            payload = {
                "app_id": self.app_id,
                "app_secret": self.app_secret
            }
            
            # 改進SSL處理 - 先嘗試正常SSL驗證
            try:
                response = requests.post(
                    self.auth_url,
                    headers=headers,
                    json=payload,
                    timeout=30,
                    verify=True,  # 啟用SSL驗證
                    allow_redirects=True
                )
            except requests.exceptions.SSLError as ssl_error:
                print_step("SSL警告", f"⚠️ 認證SSL驗證失敗，嘗試不驗證SSL: {str(ssl_error)}")
                response = requests.post(
                    self.auth_url,
                    headers=headers,
                    json=payload,
                    timeout=30,
                    verify=False,  # 禁用SSL驗證
                    allow_redirects=True
                )
            except requests.exceptions.RequestException as req_error:
                print_step("認證請求錯誤", f"❌ 認證請求失敗: {str(req_error)}")
                raise req_error
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    self.access_token = result['tenant_access_token']
                    token_preview = self.access_token[:8] + "..." if len(self.access_token) > 8 else self.access_token
                    print_step("认证成功", f"✅ 获得tenant_access_token: {token_preview}")
                    return True
                else:
                    error_msg = result.get('msg', '未知错误')
                    print_step("认证失败", f"❌ 飞书认证失败: {error_msg}")
                    return False
            else:
                print_step("认证失败", f"❌ HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            print_step("认证异常", f"❌ 认证过程发生异常: {str(e)}")
            return False
    
    def upload_files(self, file_paths):
        """
        批量上传文件到飞书
        
        Args:
            file_paths: 文件路径列表或单个文件路径
        
        Returns:
            dict: 上传结果摘要
        """
        print_step("飞书上传开始", "开始批量上传Excel文件到飞书Sheet")
        
        # 步骤1: 自动认证获取access_token
        if not self.access_token or self.access_token == "your_feishu_access_token_here":
            if not self.authenticate():
                return {
                    'success': False,
                    'uploaded_files': [],
                    'failed_files': [],
                    'error': '飞书认证失败'
                }
        
        # 确保file_paths是列表
        if isinstance(file_paths, str):
            file_paths = [file_paths]
        
        # 过滤存在的文件
        existing_files = [f for f in file_paths if os.path.exists(f)]
        missing_files = [f for f in file_paths if not os.path.exists(f)]
        
        if missing_files:
            print_step("文件检查", f"以下文件不存在，跳过上传: {missing_files}")
        
        if not existing_files:
            print_step("上传错误", "没有可用的文件进行上传")
            return {
                'success': False,
                'uploaded_files': [],
                'failed_files': [],
                'error': '没有可用的文件'
            }
        
        print_step("文件检查", f"准备上传 {len(existing_files)} 个文件")
        
        # 逐个上传文件
        uploaded_files = []
        failed_files = []
        
        for file_path in existing_files:
            result = self._upload_single_file(file_path)
            if result['success']:
                uploaded_files.append(result)
            else:
                failed_files.append({
                    'file': file_path,
                    'error': result['error']
                })
        
        # 生成总结
        summary = {
            'success': len(failed_files) == 0,
            'uploaded_files': uploaded_files,
            'failed_files': failed_files,
            'total_files': len(existing_files),
            'success_count': len(uploaded_files),
            'failed_count': len(failed_files)
        }
        
        self._print_upload_summary(summary)
        return summary
    
    def _upload_single_file(self, file_path):
        """
        上传单个文件到飞书
        
        Args:
            file_path: 文件路径
        
        Returns:
            dict: 单个文件上传结果
        """
        filename = os.path.basename(file_path)
        print_step("文件上传", f"正在上传: {filename}")
        
        try:
            # 获取文件大小
            file_size = os.path.getsize(file_path)
            file_size_mb = file_size / (1024 * 1024)  # 转换为MB
            
            # 检查文件大小限制（飞书API限制约20MB）
            max_size_mb = config.FEISHU_MAX_FILE_SIZE_MB
            if file_size_mb > max_size_mb:
                error_msg = f"文件大小 {file_size_mb:.1f}MB 超过飞书上传限制 {max_size_mb}MB"
                print_step("上传失败", f"❌ {filename} 上传失败: {error_msg}")
                return {
                    'success': False,
                    'filename': filename,
                    'file_path': file_path,
                    'error': error_msg
                }
            
            # 准备请求头
            headers = {
                'Authorization': f'Bearer {self.access_token}'
            }
            
            # 重新获取精确的文件大小
            with open(file_path, 'rb') as f:
                file_content = f.read()
                actual_file_size = len(file_content)
                
                files = {
                    'file': (filename, file_content, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                }
                
                data = {
                    'file_name': filename,
                    'parent_type': 'explorer', 
                    'parent_node': self.parent_node,
                    'size': str(actual_file_size)
                }
                
                # 发送请求 - 多層SSL處理和重試機制
                ssl_attempts = [
                    {"verify": True, "description": "標準SSL驗證", "timeout": 30},
                    {"verify": False, "description": "禁用SSL驗證", "timeout": 45},
                    {"verify": False, "description": "禁用SSL驗證+長超時", "timeout": 90},
                ]
                
                for attempt_num, ssl_config in enumerate(ssl_attempts, 1):
                    try:
                        print_step("上傳嘗試", f"🔄 第{attempt_num}次嘗試: {ssl_config['description']}")
                        
                        # 創建新的session
                        import time
                        for retry in range(3):  # 每個SSL配置重試3次
                            try:
                                if retry > 0:
                                    print_step("重試", f"🔄 第{retry+1}次重試...")
                                    time.sleep(min(retry * 2, 5))  # 漸進式等待，最多5秒
                                
                                # 直接使用requests.post，避免session變量問題
                                response = requests.post(
                                    self.upload_url,
                                    headers=headers,
                                    data=data,
                                    files=files,
                                    timeout=ssl_config['timeout'],
                                    verify=ssl_config['verify'],
                                    allow_redirects=True,
                                    stream=False
                                )
                                
                                # 檢查響應
                                if response.status_code == 200:
                                    result = response.json()
                                    if result.get('code') == 0:
                                        file_token = result['data']['file_token']
                                        print_step("上传成功", f"✅ {filename} 上传成功，文件ID: {file_token}")
                                        return {
                                            'success': True,
                                            'file_token': file_token,
                                            'file_url': f"https://docs.feishu.cn/sheets/{file_token}",
                                            'filename': filename,
                                            'file_path': file_path
                                        }
                                    else:
                                        print_step("API錯誤", f"❌ 飛書API返回錯誤: {result}")
                                        continue  # 重試
                                else:
                                    print_step("HTTP錯誤", f"❌ HTTP {response.status_code}: {response.text[:200]}")
                                    continue  # 重試
                                    
                            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                                print_step("超時重試", f"⏰ 請求超時，準備重試...")
                                if retry == 2:  # 最後一次重試，退出內層循環
                                    break
                                continue
                        
                            except requests.exceptions.SSLError as e:
                                error_msg = str(e)
                                print_step("SSL錯誤", f"⚠️ {ssl_config['description']}失敗: {error_msg}")
                                if retry == 2:  # 最後一次重試，退出內層循環
                                    break
                            continue
                            
                    except Exception as e:
                        print_step("配置失敗", f"⚠️ {ssl_config['description']}配置失敗: {e}")
                        continue  # 嘗試下一個SSL配置
                
                # 所有配置都失敗了
                print_step("上傳異常", f"❌ 所有SSL配置都失敗了")
                raise Exception("所有上傳配置都失敗")
            

                
        except Exception as e:
            error_msg = f"上传异常: {str(e)}"
            print_step("上传异常", f"❌ {filename} 上传异常: {error_msg}")
            return {
                'success': False,
                'filename': filename,
                'file_path': file_path,
                'error': error_msg
            }
    
    def _print_upload_summary(self, summary):
        """打印上传结果摘要"""
        print_step("上传摘要", "飞书文件上传结果:")
        
        print(f"📊 上传统计:")
        print(f"   - 总文件数: {summary['total_files']}")
        print(f"   - 成功上传: {summary['success_count']}")
        print(f"   - 上传失败: {summary['failed_count']}")
        print(f"   - 整体状态: {'✅ 全部成功' if summary['success'] else '❌ 部分失败'}")
        
        if summary['uploaded_files']:
            print(f"📄 成功上传的文件:")
            for file_info in summary['uploaded_files']:
                print(f"   ✅ {file_info['filename']}")
                if file_info.get('file_token'):
                    print(f"      - 文件ID: {file_info['file_token']}")
                if file_info.get('url'):
                    print(f"      - 访问链接: {file_info['url']}")
        
        if summary['failed_files']:
            print(f"❌ 上传失败的文件:")
            for file_info in summary['failed_files']:
                print(f"   ❌ {os.path.basename(file_info['file'])}: {file_info['error']}")

    def test_connection(self):
        """测试飞书API连接"""
        print_step("连接测试", "正在测试飞书API连接...")
        
        # 步骤1: 测试认证
        if not self.access_token or self.access_token == "your_feishu_access_token_here":
            print_step("认证测试", "正在测试飞书认证...")
            if not self.authenticate():
                return False
        
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            # 使用获取文件夹信息的API测试连接
            test_url = "https://open.feishu.cn/open-apis/drive/v1/files"
            response = requests.get(
                test_url,
                headers=headers,
                params={'parent_token': self.parent_node},
                timeout=30,
                verify=False,  # 禁用SSL驗證以解決SSL問題
                allow_redirects=True
            )
            
            if response.status_code == 200:
                print_step("连接测试", "✅ 飞书API连接正常")
                return True
            else:
                print_step("连接测试", f"❌ 飞书API连接失败: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print_step("连接测试", f"❌ 飞书API连接异常: {str(e)}")
            return False

# 便捷函数
def upload_to_feishu(file_paths, access_token=None):
    """
    便捷的上传函数
    
    Args:
        file_paths: 文件路径列表或单个文件路径
        access_token: 飞书访问令牌
    
    Returns:
        dict: 上传结果摘要
    """
    uploader = FeishuUploader(access_token)
    return uploader.upload_files(file_paths)

def test_feishu_connection(access_token=None):
    """
    测试飞书连接的便捷函数
    
    Args:
        access_token: 飞书访问令牌
    
    Returns:
        bool: 连接是否成功
    """
    uploader = FeishuUploader(access_token)
    return uploader.test_connection() 