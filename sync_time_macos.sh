#!/bin/bash
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
