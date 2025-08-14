#!/bin/bash
# Google Sheets JWT时间同步脚本

echo "🕐 Google Sheets JWT时间同步工具"
echo "================================="

echo "当前系统时间:"
date

echo ""
echo "同步网络时间..."

# macOS时间同步
if command -v sntp >/dev/null 2>&1; then
    echo "使用sntp同步时间..."
    sudo sntp -sS time.apple.com
    if [ $? -eq 0 ]; then
        echo "✅ 时间同步成功"
    else
        echo "❌ 时间同步失败"
    fi
else
    echo "⚠️ sntp命令不可用"
fi

echo ""
echo "同步后系统时间:"
date

echo ""
echo "💡 如果问题仍然存在，请:"
echo "1. 检查网络连接"
echo "2. 手动设置正确的系统时间"
echo "3. 重新生成Google服务账号密钥"
