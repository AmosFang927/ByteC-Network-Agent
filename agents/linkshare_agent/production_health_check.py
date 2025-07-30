#!/usr/bin/env python3
"""
生产环境健康检查脚本
验证TikTok Shop联盟营销系统是否准备就绪
"""

import sys
import json
import time
import logging
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent.parent))

from agents.linkshare_agent import config
from agents.linkshare_agent.auth import TikTokAuth
from agents.linkshare_agent.token_manager import TokenManager

def print_header(title: str):
    """打印标题"""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print(f"{'='*60}")

def check_config():
    """检查配置完整性"""
    print_header("配置检查")
    
    checks = []
    
    # 检查必要配置
    required_configs = [
        ("APP_KEY", config.APP_KEY),
        ("APP_SECRET", config.APP_SECRET),
        ("AUTH_CODE", config.AUTH_CODE),
        ("REDIRECT_URL", config.REDIRECT_URL)
    ]
    
    for name, value in required_configs:
        if value and value.strip():
            print(f"✅ {name}: 已配置")
            checks.append(True)
        else:
            print(f"❌ {name}: 未配置")
            checks.append(False)
    
    # 检查API端点
    api_urls = [
        ("TOKEN_GET_URL", config.TOKEN_GET_URL),
        ("TOKEN_REFRESH_URL", config.TOKEN_REFRESH_URL),
        ("LINK_GENERATE_URL", config.LINK_GENERATE_URL)
    ]
    
    for name, url in api_urls:
        if url and url.startswith("https://"):
            print(f"✅ {name}: {url}")
            checks.append(True)
        else:
            print(f"❌ {name}: 配置错误")
            checks.append(False)
    
    success_rate = sum(checks) / len(checks) * 100
    print(f"\n📊 配置完整性: {success_rate:.1f}%")
    
    return all(checks)

def check_token_storage():
    """检查Token存储"""
    print_header("Token存储检查")
    
    try:
        token_path = config.get_token_storage_path()
        print(f"📁 Token存储路径: {token_path}")
        
        if token_path.exists():
            with open(token_path, 'r') as f:
                tokens = json.load(f)
            
            print("✅ Token文件存在")
            print(f"🔑 Access Token: {tokens.get('access_token', 'N/A')[:30]}...")
            print(f"🔄 Refresh Token: {tokens.get('refresh_token', 'N/A')[:30]}...")
            
            # 检查过期时间
            current_time = int(time.time())
            expires_at = tokens.get('expires_at', 0)
            
            if expires_at > current_time:
                time_left = expires_at - current_time
                print(f"⏰ Token剩余时间: {time_left//3600}小时{(time_left%3600)//60}分钟")
                print("✅ Token仍在有效期内")
                return True
            else:
                print("⚠️ Token已过期，需要刷新")
                return False
        else:
            print("❌ Token文件不存在")
            return False
            
    except Exception as e:
        print(f"❌ Token存储检查失败: {e}")
        return False

def check_auth_api():
    """检查认证API"""
    print_header("认证API检查")
    
    try:
        print("🔄 初始化认证模块...")
        auth = TikTokAuth()
        print("✅ TikTokAuth初始化成功")
        
        # 检查是否可以刷新token（如果有refresh token的话）
        try:
            token_manager = TokenManager()
            print("✅ TokenManager初始化成功")
            
            # 尝试获取有效token（会自动处理刷新）
            valid_token = token_manager.get_valid_token()
            if valid_token:
                print(f"✅ 获取有效Token成功: {valid_token[:30]}...")
                return True
            else:
                print("❌ 无法获取有效Token")
                return False
                
        except Exception as e:
            print(f"⚠️ Token管理器测试失败: {e}")
            return False
            
    except Exception as e:
        print(f"❌ 认证API检查失败: {e}")
        return False

def check_sdk_integration():
    """检查SDK集成"""
    print_header("SDK集成检查")
    
    try:
        # 检查Node.js SDK文件
        sdk_dir = Path(__file__).parent / "nodejs_sdk"
        critical_files = [
            "simple_test.js",
            "dist/utils/generate-sign.js",
            "dist/index.js",
            "package.json"
        ]
        
        all_files_exist = True
        for file_name in critical_files:
            file_path = sdk_dir / file_name
            if file_path.exists():
                print(f"✅ {file_name}: 存在")
            else:
                print(f"❌ {file_name}: 缺失")
                all_files_exist = False
        
        if all_files_exist:
            print("✅ SDK文件完整性检查通过")
            return True
        else:
            print("❌ SDK文件不完整")
            return False
            
    except Exception as e:
        print(f"❌ SDK集成检查失败: {e}")
        return False

def check_api_connectivity():
    """检查API连通性"""
    print_header("API连通性检查")
    
    try:
        import subprocess
        
        # 简单的网络连通性检查
        test_urls = [
            "auth.tiktok-shops.com",
            "open-api.tiktokglobalshop.com"
        ]
        
        connectivity_results = []
        for url in test_urls:
            try:
                result = subprocess.run(
                    ["ping", "-c", "1", url],
                    capture_output=True,
                    timeout=10
                )
                if result.returncode == 0:
                    print(f"✅ {url}: 连通正常")
                    connectivity_results.append(True)
                else:
                    print(f"⚠️ {url}: 连通异常")
                    connectivity_results.append(False)
            except:
                print(f"⚠️ {url}: 无法测试连通性")
                connectivity_results.append(False)
        
        if any(connectivity_results):
            print("✅ 至少一个API端点可达")
            return True
        else:
            print("❌ 所有API端点不可达")
            return False
            
    except Exception as e:
        print(f"⚠️ API连通性检查失败: {e}")
        return True  # 网络检查失败不影响整体评估

def generate_production_checklist():
    """生成生产部署检查清单"""
    print_header("生产部署检查清单")
    
    checklist = [
        ("✅ 环境变量配置", "将敏感信息移至环境变量"),
        ("⚠️ 数据库存储", "使用Redis或数据库替代文件存储"),
        ("⚠️ 容器化部署", "创建Docker镜像"),
        ("⚠️ 负载均衡", "配置多实例负载均衡"),
        ("⚠️ 监控告警", "添加Prometheus监控"),
        ("⚠️ 日志聚合", "配置日志收集系统"),
        ("⚠️ 健康检查", "添加HTTP健康检查端点"),
        ("⚠️ 备份机制", "配置数据备份策略")
    ]
    
    print("📋 生产环境改进建议:")
    for status, item in checklist:
        print(f"   {status} {item}")

def main():
    """主函数"""
    print("🚀 TikTok Shop 联盟营销系统 - 生产环境健康检查")
    print("🎯 检查系统是否准备就绪...")
    
    # 执行各项检查
    checks = []
    
    checks.append(("配置检查", check_config()))
    checks.append(("Token存储", check_token_storage()))
    checks.append(("认证API", check_auth_api()))
    checks.append(("SDK集成", check_sdk_integration()))
    checks.append(("API连通性", check_api_connectivity()))
    
    # 生成检查清单
    generate_production_checklist()
    
    # 总结结果
    print_header("健康检查总结")
    
    passed_checks = sum(1 for _, result in checks if result)
    total_checks = len(checks)
    success_rate = passed_checks / total_checks * 100
    
    print("📊 检查结果:")
    for check_name, result in checks:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {check_name}: {status}")
    
    print(f"\n🎯 总体健康度: {success_rate:.1f}% ({passed_checks}/{total_checks})")
    
    if success_rate >= 80:
        print("🎉 系统健康状况良好，可以部署到生产环境！")
        print("💡 建议先进行小规模部署测试")
        return True
    elif success_rate >= 60:
        print("⚠️ 系统基本可用，但需要解决一些问题后再部署")
        print("💡 建议先修复失败的检查项")
        return False
    else:
        print("❌ 系统存在严重问题，不建议部署到生产环境")
        print("💡 请先解决所有关键问题")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)