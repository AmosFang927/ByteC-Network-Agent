#!/usr/bin/env python3
"""
Google Sheets 连接问题全面诊断工具
专门解决 JWT 时间同步问题
"""

import os
import json
import time
import logging
import subprocess
from datetime import datetime, timezone
from typing import Dict, Any, List

try:
    import gspread
    from google.oauth2.service_account import Credentials
    from google.auth.exceptions import RefreshError
    from google.auth.transport.requests import Request
    GOOGLE_SHEETS_AVAILABLE = True
except ImportError:
    GOOGLE_SHEETS_AVAILABLE = False
    print("❌ Google Sheets API 不可用，请安装依赖: pip install gspread google-auth")
    exit(1)

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GoogleSheetsFullDiagnosis:
    """Google Sheets 连接问题全面诊断"""
    
    def __init__(self, credentials_file: str = "solar-idea-463423-h8-bd12ec2c5361.json"):
        self.credentials_file = credentials_file
        self.logger = logging.getLogger(__name__)
        self.spreadsheet_id = "1SaHZ0igiuMBm2gHFD5JSs1hkltphdXqRAlbaZ9nEUf0"
    
    def check_system_environment(self) -> Dict[str, Any]:
        """检查系统环境"""
        print("🔍 检查系统环境...")
        
        env_info = {}
        
        # 1. 检查系统时间
        current_time = datetime.now(timezone.utc)
        env_info['system_time'] = {
            'utc': current_time.isoformat(),
            'local': datetime.now().isoformat(),
            'year': current_time.year,
            'is_abnormal': current_time.year > 2024
        }
        
        # 2. 检查网络连接
        try:
            result = subprocess.run(['ping', '-c', '1', 'google.com'], 
                                  capture_output=True, text=True, timeout=10)
            env_info['network'] = {'connected': result.returncode == 0}
        except Exception as e:
            env_info['network'] = {'connected': False, 'error': str(e)}
        
        # 3. 检查凭证文件
        env_info['credentials'] = self._check_credentials_file()
        
        return env_info
    
    def _check_credentials_file(self) -> Dict[str, Any]:
        """检查凭证文件"""
        if not os.path.exists(self.credentials_file):
            return {'exists': False, 'error': 'File not found'}
        
        try:
            with open(self.credentials_file, 'r') as f:
                creds_data = json.load(f)
            
            required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
            missing_fields = [field for field in required_fields if field not in creds_data]
            
            return {
                'exists': True,
                'valid_format': len(missing_fields) == 0,
                'missing_fields': missing_fields,
                'project_id': creds_data.get('project_id', 'unknown'),
                'client_email': creds_data.get('client_email', 'unknown')
            }
        except Exception as e:
            return {'exists': True, 'valid_format': False, 'error': str(e)}
    
    def test_jwt_creation(self) -> Dict[str, Any]:
        """测试 JWT 凭证创建"""
        print("🔐 测试 JWT 凭证创建...")
        
        results = {}
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets.readonly',
            'https://www.googleapis.com/auth/drive.readonly'
        ]
        
        # 方法1: 标准 Credentials.from_service_account_file
        try:
            start_time = time.time()
            credentials = Credentials.from_service_account_file(
                self.credentials_file, 
                scopes=scopes
            )
            results['method1_standard'] = {
                'success': True,
                'time_taken': time.time() - start_time,
                'token_expiry': credentials.expiry.isoformat() if credentials.expiry else None
            }
        except Exception as e:
            results['method1_standard'] = {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
        
        # 方法2: 手动创建 Credentials
        try:
            start_time = time.time()
            with open(self.credentials_file, 'r') as f:
                creds_data = json.load(f)
            
            credentials = Credentials.from_service_account_info(creds_data, scopes=scopes)
            results['method2_manual'] = {
                'success': True,
                'time_taken': time.time() - start_time,
                'token_expiry': credentials.expiry.isoformat() if credentials.expiry else None
            }
        except Exception as e:
            results['method2_manual'] = {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
        
        # 方法3: gspread.service_account
        try:
            start_time = time.time()
            client = gspread.service_account(filename=self.credentials_file)
            results['method3_gspread'] = {
                'success': True,
                'time_taken': time.time() - start_time,
                'client_type': type(client).__name__
            }
        except Exception as e:
            results['method3_gspread'] = {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
        
        return results
    
    def test_token_refresh(self) -> Dict[str, Any]:
        """测试 Token 刷新"""
        print("🔄 测试 Token 刷新...")
        
        results = {}
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets.readonly',
            'https://www.googleapis.com/auth/drive.readonly'
        ]
        
        try:
            # 创建凭证
            credentials = Credentials.from_service_account_file(
                self.credentials_file, 
                scopes=scopes
            )
            
            # 创建请求对象
            request = Request()
            
            # 尝试刷新 Token
            for attempt in range(3):
                try:
                    start_time = time.time()
                    credentials.refresh(request)
                    results[f'refresh_attempt_{attempt + 1}'] = {
                        'success': True,
                        'time_taken': time.time() - start_time,
                        'token_expiry': credentials.expiry.isoformat() if credentials.expiry else None
                    }
                    break
                except RefreshError as e:
                    results[f'refresh_attempt_{attempt + 1}'] = {
                        'success': False,
                        'error': str(e),
                        'error_type': 'RefreshError',
                        'is_jwt_error': 'Invalid JWT Signature' in str(e)
                    }
                    if attempt < 2:
                        time.sleep(2)  # 等待后重试
                except Exception as e:
                    results[f'refresh_attempt_{attempt + 1}'] = {
                        'success': False,
                        'error': str(e),
                        'error_type': type(e).__name__
                    }
                    break
        
        except Exception as e:
            results['setup_error'] = {
                'error': str(e),
                'error_type': type(e).__name__
            }
        
        return results
    
    def test_google_sheets_connection(self) -> Dict[str, Any]:
        """测试 Google Sheets 连接"""
        print("📊 测试 Google Sheets 连接...")
        
        results = {}
        
        # 测试多种连接方法
        methods = [
            ('gspread.service_account', lambda: gspread.service_account(filename=self.credentials_file)),
            ('gspread.oauth', lambda: gspread.oauth()),
            ('manual_credentials', self._create_manual_client),
        ]
        
        for method_name, method_func in methods:
            try:
                start_time = time.time()
                client = method_func()
                
                # 尝试连接到 Spreadsheet
                spreadsheet = client.open_by_key(self.spreadsheet_id)
                
                results[method_name] = {
                    'success': True,
                    'time_taken': time.time() - start_time,
                    'spreadsheet_title': spreadsheet.title,
                    'worksheets': [ws.title for ws in spreadsheet.worksheets()]
                }
                
                # 如果成功，尝试读取数据
                try:
                    worksheet = spreadsheet.get_worksheet(0)
                    if worksheet:
                        data = worksheet.get('A1:C3')
                        results[method_name]['sample_data'] = data
                except Exception as read_error:
                    results[method_name]['read_error'] = str(read_error)
                
                break  # 如果成功，停止尝试其他方法
                
            except Exception as e:
                results[method_name] = {
                    'success': False,
                    'error': str(e),
                    'error_type': type(e).__name__,
                    'is_jwt_error': 'Invalid JWT Signature' in str(e)
                }
        
        return results
    
    def _create_manual_client(self):
        """手动创建 Google Sheets 客户端"""
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets.readonly',
            'https://www.googleapis.com/auth/drive.readonly'
        ]
        
        credentials = Credentials.from_service_account_file(
            self.credentials_file, 
            scopes=scopes
        )
        
        return gspread.authorize(credentials)
    
    def suggest_fixes(self, diagnosis_results: Dict[str, Any]) -> List[str]:
        """根据诊断结果建议修复方案"""
        suggestions = []
        
        env_info = diagnosis_results.get('environment', {})
        jwt_results = diagnosis_results.get('jwt_creation', {})
        refresh_results = diagnosis_results.get('token_refresh', {})
        connection_results = diagnosis_results.get('google_sheets_connection', {})
        
        # 检查系统时间
        if env_info.get('system_time', {}).get('is_abnormal', False):
            suggestions.append("🕐 系统时间异常（显示为2025年），需要同步系统时间：")
            suggestions.append("   - macOS: sudo sntp -sS time.apple.com")
            suggestions.append("   - 或通过系统偏好设置 > 日期与时间 > 自动设置")
        
        # 检查网络连接
        if not env_info.get('network', {}).get('connected', False):
            suggestions.append("🌐 网络连接问题，请检查网络连接")
        
        # 检查凭证文件
        creds_info = env_info.get('credentials', {})
        if not creds_info.get('exists', False):
            suggestions.append("📁 凭证文件不存在，请确保 solar-idea-463423-h8-bd12ec2c5361.json 在当前目录")
        elif not creds_info.get('valid_format', False):
            suggestions.append("📁 凭证文件格式有问题，请重新下载 Service Account 密钥")
        
        # 检查 JWT 错误
        jwt_errors = []
        for method, result in jwt_results.items():
            if not result.get('success', False) and 'JWT' in result.get('error', ''):
                jwt_errors.append(method)
        
        if jwt_errors:
            suggestions.append("🔐 JWT 签名错误，可能的解决方案：")
            suggestions.append("   - 重新生成 Service Account 密钥")
            suggestions.append("   - 确保 Service Account 有正确的权限")
            suggestions.append("   - 检查 Google Cloud Project 的状态")
        
        # 检查连接结果
        if all(not result.get('success', False) for result in connection_results.values()):
            suggestions.append("📊 所有连接方法都失败，建议：")
            suggestions.append("   - 检查 Google Sheets API 是否已启用")
            suggestions.append("   - 确认 Service Account 有访问目标 Spreadsheet 的权限")
        
        if not suggestions:
            suggestions.append("✅ 未发现明显问题，连接应该正常工作")
        
        return suggestions
    
    def run_full_diagnosis(self) -> Dict[str, Any]:
        """运行完整诊断"""
        print("🔧 开始 Google Sheets 连接问题全面诊断")
        print("=" * 60)
        
        diagnosis_results = {}
        
        # 1. 环境检查
        diagnosis_results['environment'] = self.check_system_environment()
        
        # 2. JWT 凭证创建测试
        diagnosis_results['jwt_creation'] = self.test_jwt_creation()
        
        # 3. Token 刷新测试
        diagnosis_results['token_refresh'] = self.test_token_refresh()
        
        # 4. Google Sheets 连接测试
        diagnosis_results['google_sheets_connection'] = self.test_google_sheets_connection()
        
        # 5. 建议修复方案
        diagnosis_results['suggestions'] = self.suggest_fixes(diagnosis_results)
        
        return diagnosis_results
    
    def print_diagnosis_report(self, results: Dict[str, Any]):
        """打印诊断报告"""
        print("\n" + "=" * 60)
        print("📋 Google Sheets 连接诊断报告")
        print("=" * 60)
        
        # 环境信息
        env_info = results.get('environment', {})
        print("\n🔍 系统环境:")
        system_time = env_info.get('system_time', {})
        print(f"   📅 系统时间: {system_time.get('utc', 'unknown')}")
        if system_time.get('is_abnormal', False):
            print("   ⚠️  系统时间异常！")
        else:
            print("   ✅ 系统时间正常")
        
        network = env_info.get('network', {})
        print(f"   🌐 网络连接: {'✅ 正常' if network.get('connected', False) else '❌ 异常'}")
        
        creds = env_info.get('credentials', {})
        print(f"   📁 凭证文件: {'✅ 正常' if creds.get('valid_format', False) else '❌ 异常'}")
        
        # JWT 创建结果
        print("\n🔐 JWT 凭证创建测试:")
        jwt_results = results.get('jwt_creation', {})
        for method, result in jwt_results.items():
            status = "✅ 成功" if result.get('success', False) else "❌ 失败"
            print(f"   {method}: {status}")
            if not result.get('success', False):
                print(f"      错误: {result.get('error', 'unknown')}")
        
        # Token 刷新结果
        print("\n🔄 Token 刷新测试:")
        refresh_results = results.get('token_refresh', {})
        for attempt, result in refresh_results.items():
            status = "✅ 成功" if result.get('success', False) else "❌ 失败"
            print(f"   {attempt}: {status}")
            if not result.get('success', False) and result.get('is_jwt_error', False):
                print("      ⚠️  JWT 签名错误")
        
        # Google Sheets 连接结果
        print("\n📊 Google Sheets 连接测试:")
        connection_results = results.get('google_sheets_connection', {})
        for method, result in connection_results.items():
            status = "✅ 成功" if result.get('success', False) else "❌ 失败"
            print(f"   {method}: {status}")
            if result.get('success', False):
                print(f"      表格: {result.get('spreadsheet_title', 'unknown')}")
                print(f"      工作表: {result.get('worksheets', [])}")
        
        # 修复建议
        print("\n💡 修复建议:")
        suggestions = results.get('suggestions', [])
        for suggestion in suggestions:
            print(f"   {suggestion}")

def main():
    """主函数"""
    diagnosis = GoogleSheetsFullDiagnosis()
    results = diagnosis.run_full_diagnosis()
    diagnosis.print_diagnosis_report(results)
    
    # 保存诊断结果
    with open('google_sheets_diagnosis_report.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n📄 详细诊断结果已保存到: google_sheets_diagnosis_report.json")

if __name__ == "__main__":
    main()
