#!/bin/bash

# 同时运行多个微信实例的脚本

echo "🚀 启动多个微信实例..."

# 创建不同的数据目录
mkdir -p ~/WeChat1_Data
mkdir -p ~/WeChat2_Data

# 启动第一个微信（使用原始数据目录）
echo "📱 启动第一个微信..."
open -n "/Applications/WeChat.app" &
sleep 3

# 启动第二个微信（使用不同的数据目录）
echo "📱 启动第二个微信..."
HOME=~/WeChat2_Data open -n "/Applications/WeChat2.app" &
sleep 3

# 检查进程状态
echo "🔍 检查微信进程状态..."
ps aux | grep -i wechat | grep -v grep | grep "WeChat$"

echo "✅ 微信启动完成！"
echo "💡 提示：如果只看到一个微信窗口，请尝试手动打开第二个微信应用程序" 