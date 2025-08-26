#!/usr/bin/env python3
"""
系统时间同步脚本
修复 macOS 系统时间问题，解决 Google JWT 认证
"""

import os
import subprocess
import logging
from datetime import datetime, timezone

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_system_time():
    """检查系统时间"""
    try:
        current_time = datetime.now(timezone.utc)
        logger.info(f"📅 当前系统时间 (UTC): {current_time}")
        
        # 检查年份是否正常
        if current_time.year > 2024:
            logger.warning(f"⚠️ 系统时间异常: {current_time.year} 年")
            return False
        else:
            logger.info("✅ 系统时间正常")
            return True
            
    except Exception as e:
        logger.error(f"❌ 时间检查失败: {e}")
        return False

def sync_time_macos():
    """同步 macOS 系统时间"""
    try:
        logger.info("🔄 尝试同步 macOS 系统时间...")
        
        # 方法1: 使用 sntp 同步时间
        try:
            logger.info("📡 使用 sntp 同步时间...")
            result = subprocess.run(['sudo', 'sntp', '-sS', 'time.apple.com'], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                logger.info("✅ sntp 时间同步成功")
                return True
            else:
                logger.warning(f"⚠️ sntp 同步失败: {result.stderr}")
        except Exception as e:
            logger.warning(f"⚠️ sntp 同步异常: {e}")
        
        # 方法2: 使用 systemsetup 启用网络时间
        try:
            logger.info("⚙️ 启用网络时间同步...")
            result = subprocess.run(['sudo', 'systemsetup', '-setusingnetworktime', 'on'], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                logger.info("✅ 网络时间同步已启用")
                
                # 设置时间服务器
                result = subprocess.run(['sudo', 'systemsetup', '-setnetworktimeserver', 'time.apple.com'], 
                                      capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    logger.info("✅ 时间服务器设置成功")
                    return True
            else:
                logger.warning(f"⚠️ 网络时间设置失败: {result.stderr}")
        except Exception as e:
            logger.warning(f"⚠️ 网络时间设置异常: {e}")
        
        return False
        
    except Exception as e:
        logger.error(f"❌ 时间同步失败: {e}")
        return False

def manual_time_instructions():
    """提供手动时间同步说明"""
    print("\n📋 手动时间同步说明:")
    print("=" * 40)
    print("1. 打开 系统偏好设置 > 日期与时间")
    print("2. 点击左下角的锁图标，输入管理员密码")
    print("3. 勾选 '自动设置日期与时间'")
    print("4. 确保时间服务器设置为: time.apple.com")
    print("5. 或者在终端运行以下命令:")
    print("   sudo sntp -sS time.apple.com")
    print("   sudo systemsetup -setusingnetworktime on")
    print("\n⚠️ 注意: 需要管理员权限")

def create_time_sync_script():
    """创建时间同步脚本"""
    script_content = '''#!/bin/bash
# macOS 时间同步脚本

echo "🔄 开始同步系统时间..."

# 方法1: 使用 sntp
echo "📡 使用 sntp 同步时间..."
sudo sntp -sS time.apple.com
if [ $? -eq 0 ]; then
    echo "✅ sntp 时间同步成功"
else
    echo "⚠️ sntp 同步失败，尝试其他方法..."
    
    # 方法2: 启用网络时间
    echo "⚙️ 启用网络时间同步..."
    sudo systemsetup -setusingnetworktime on
    sudo systemsetup -setnetworktimeserver time.apple.com
    
    if [ $? -eq 0 ]; then
        echo "✅ 网络时间同步设置成功"
    else
        echo "❌ 时间同步失败"
        exit 1
    fi
fi

echo "📅 当前系统时间:"
date

echo "✅ 时间同步完成"
'''
    
    script_file = "sync_time_macos.sh"
    with open(script_file, 'w') as f:
        f.write(script_content)
    
    # 设置执行权限
    os.chmod(script_file, 0o755)
    
    logger.info(f"✅ 创建时间同步脚本: {script_file}")
    return script_file

def main():
    """主函数"""
    print("🕐 macOS 系统时间同步工具")
    print("=" * 40)
    
    # 检查当前时间
    if check_system_time():
        print("✅ 系统时间正常，无需同步")
        return
    
    print("\n⚠️ 检测到系统时间异常，需要同步")
    
    # 创建同步脚本
    script_file = create_time_sync_script()
    
    # 提供说明
    manual_time_instructions()
    
    print(f"\n💡 自动同步脚本已创建: {script_file}")
    print("运行命令: ./sync_time_macos.sh")
    
    # 尝试自动同步（需要 sudo 权限）
    try:
        print("\n🔄 尝试自动同步时间...")
        if sync_time_macos():
            print("✅ 时间同步成功！")
            
            # 重新检查时间
            if check_system_time():
                print("✅ 系统时间已修复")
            else:
                print("⚠️ 时间可能仍有问题，请手动检查")
        else:
            print("❌ 自动同步失败，请手动同步时间")
            
    except Exception as e:
        print(f"❌ 自动同步异常: {e}")
        print("💡 请手动运行同步脚本或按照说明操作")

if __name__ == "__main__":
    main()

