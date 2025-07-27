#!/bin/bash

# 微信啟動器設置腳本
# WeChat Launcher Setup Script
# 作者: ByteC Network Agent
# 用途: 設置微信分身啟動器為登入時自動執行

# 配置變量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAUNCHER_SCRIPT="$SCRIPT_DIR/wechat_multi_clone_launcher.sh"
AGENT_NAME="com.bytec.wechatlauncher"
AGENT_PLIST="$HOME/Library/LaunchAgents/$AGENT_NAME.plist"

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日誌函數
log_message() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 檢查腳本是否存在
check_script_exists() {
    if [ ! -f "$LAUNCHER_SCRIPT" ]; then
        log_error "啟動腳本不存在: $LAUNCHER_SCRIPT"
        return 1
    fi
    
    # 設置執行權限
    chmod +x "$LAUNCHER_SCRIPT"
    log_success "啟動腳本權限已設置"
    return 0
}

# 創建 LaunchAgent plist 文件
create_launch_agent() {
    log_message "創建 LaunchAgent 配置文件..."
    
    cat > "$AGENT_PLIST" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$AGENT_NAME</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>$LAUNCHER_SCRIPT</string>
    </array>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>KeepAlive</key>
    <false/>
    
    <key>StandardOutPath</key>
    <string>$HOME/wechat_launcher_stdout.log</string>
    
    <key>StandardErrorPath</key>
    <string>$HOME/wechat_launcher_stderr.log</string>
    
    <key>WorkingDirectory</key>
    <string>$HOME</string>
    
    <key>ProcessType</key>
    <string>Background</string>
    
    <key>ThrottleInterval</key>
    <integer>10</integer>
</dict>
</plist>
EOF
    
    if [ $? -eq 0 ]; then
        log_success "LaunchAgent 配置文件已創建"
        return 0
    else
        log_error "創建 LaunchAgent 配置文件失敗"
        return 1
    fi
}

# 載入 LaunchAgent
load_launch_agent() {
    log_message "載入 LaunchAgent..."
    
    # 先卸載可能存在的舊版本
    launchctl unload "$AGENT_PLIST" 2>/dev/null
    
    # 載入新的 LaunchAgent
    if launchctl load "$AGENT_PLIST"; then
        log_success "LaunchAgent 已成功載入"
        return 0
    else
        log_error "載入 LaunchAgent 失敗"
        return 1
    fi
}

# 測試腳本
test_script() {
    log_message "測試啟動腳本..."
    
    if "$LAUNCHER_SCRIPT" --help > /dev/null 2>&1; then
        log_success "啟動腳本測試通過"
        return 0
    else
        log_error "啟動腳本測試失敗"
        return 1
    fi
}

# 顯示狀態
show_status() {
    log_message "檢查當前狀態..."
    
    echo ""
    echo "📋 配置信息:"
    echo "  啟動腳本: $LAUNCHER_SCRIPT"
    echo "  LaunchAgent: $AGENT_PLIST"
    echo "  日誌文件: $HOME/wechat_multi_clone_launcher.log"
    echo ""
    
    # 檢查 LaunchAgent 是否已載入
    if launchctl list | grep -q "$AGENT_NAME"; then
        log_success "LaunchAgent 已載入並運行中"
    else
        log_warning "LaunchAgent 未載入"
    fi
    
    # 檢查腳本是否存在
    if [ -f "$LAUNCHER_SCRIPT" ]; then
        log_success "啟動腳本存在"
    else
        log_error "啟動腳本不存在"
    fi
}

# 卸載 LaunchAgent
unload_agent() {
    log_message "卸載 LaunchAgent..."
    
    if launchctl unload "$AGENT_PLIST" 2>/dev/null; then
        log_success "LaunchAgent 已卸載"
    else
        log_warning "LaunchAgent 卸載失敗或未載入"
    fi
    
    if [ -f "$AGENT_PLIST" ]; then
        rm "$AGENT_PLIST"
        log_success "LaunchAgent 配置文件已刪除"
    fi
}

# 顯示幫助信息
show_help() {
    echo "微信啟動器設置腳本"
    echo "用法: $0 [選項]"
    echo ""
    echo "選項:"
    echo "  install    安裝並設置登入時自動啟動"
    echo "  uninstall  卸載並移除自動啟動"
    echo "  status     顯示當前狀態"
    echo "  test       測試啟動腳本"
    echo "  help       顯示此幫助信息"
    echo ""
    echo "示例:"
    echo "  $0 install   安裝自動啟動"
    echo "  $0 status    檢查狀態"
    echo "  $0 uninstall 卸載自動啟動"
}

# 主函數
main() {
    case "${1:-}" in
        install)
            log_message "開始安裝微信啟動器..."
            
            if ! check_script_exists; then
                exit 1
            fi
            
            if ! create_launch_agent; then
                exit 1
            fi
            
            if ! load_launch_agent; then
                exit 1
            fi
            
            log_success "安裝完成！微信分身將在下次登入時自動啟動"
            echo ""
            echo "💡 提示:"
            echo "  - 可以運行 '$0 status' 檢查狀態"
            echo "  - 可以運行 '$0 test' 測試腳本"
            echo "  - 日誌文件位置: $HOME/wechat_multi_clone_launcher.log"
            ;;
            
        uninstall)
            log_message "開始卸載微信啟動器..."
            unload_agent
            log_success "卸載完成"
            ;;
            
        status)
            show_status
            ;;
            
        test)
            test_script
            ;;
            
        help|--help|-h)
            show_help
            ;;
            
        "")
            log_error "請指定操作選項"
            echo ""
            show_help
            exit 1
            ;;
            
        *)
            log_error "未知選項: $1"
            show_help
            exit 1
            ;;
    esac
}

# 執行主函數
main "$@" 