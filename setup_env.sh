#!/bin/bash

# ByteC Network Agent - 环境设置脚本
# 作用: 统一处理Python环境、依赖包安装、环境变量设置
# 使用方法: source setup_env.sh

echo "🚀 ByteC Network Agent - 环境设置开始..."

# 1. 设置项目根目录
export BYTEC_ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="$BYTEC_ROOT_DIR:$PYTHONPATH"

echo "📁 项目根目录: $BYTEC_ROOT_DIR"

# 2. 检查Python版本
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        echo "❌ 错误: 未找到Python解释器"
        return 1
    fi
    
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
    echo "🐍 Python版本: $PYTHON_VERSION"
    
    # 检查Python版本是否 >= 3.8
    if [[ "$(echo "$PYTHON_VERSION" | cut -d'.' -f1)" -lt 3 ]] || [[ "$(echo "$PYTHON_VERSION" | cut -d'.' -f2)" -lt 8 ]]; then
        echo "❌ 错误: 需要Python 3.8+，当前版本: $PYTHON_VERSION"
        return 1
    fi
    
    export PYTHON_CMD
    return 0
}

# 3. 检查并创建虚拟环境
setup_venv() {
    local venv_dir="$BYTEC_ROOT_DIR/venv"
    
    if [[ ! -d "$venv_dir" ]]; then
        echo "📦 创建虚拟环境..."
        $PYTHON_CMD -m venv "$venv_dir"
    fi
    
    # 激活虚拟环境
    source "$venv_dir/bin/activate"
    echo "✅ 虚拟环境已激活: $venv_dir"
    
    # 升级pip
    pip install --upgrade pip > /dev/null 2>&1
}

# 4. 安装依赖包
install_dependencies() {
    echo "📚 检查并安装依赖包..."
    
    # 主要依赖
    if [[ -f "$BYTEC_ROOT_DIR/requirements.txt" ]]; then
        pip install -r "$BYTEC_ROOT_DIR/requirements.txt" > /dev/null 2>&1
        echo "✅ 主要依赖已安装 (requirements.txt)"
    fi
    
    # 报表代理特殊依赖
    local reporter_deps=(
        "openpyxl>=3.1.0"
        "aiohttp>=3.8.0"
        "aiofiles>=23.0.0"
        "asyncio-throttle>=1.0.0"
    )
    
    for dep in "${reporter_deps[@]}"; do
        pip install "$dep" > /dev/null 2>&1
    done
    
    echo "✅ 报表代理依赖已安装"
}

# 5. 设置环境变量
setup_env_vars() {
    echo "🔧 设置环境变量..."
    
    # 项目配置
    export BYTEC_ENV="${BYTEC_ENV:-development}"
    export BYTEC_LOG_LEVEL="${BYTEC_LOG_LEVEL:-INFO}"
    export BYTEC_TIMEZONE="${BYTEC_TIMEZONE:-Asia/Singapore}"
    
    # 数据库配置
    if [[ -f "$BYTEC_ROOT_DIR/config.local.env" ]]; then
        source "$BYTEC_ROOT_DIR/config.local.env"
        echo "✅ 本地环境配置已加载"
    fi
    
    # Google Cloud 配置
    export GOOGLE_CLOUD_PROJECT="${GOOGLE_CLOUD_PROJECT:-solar-idea-463423-h8}"
    export GOOGLE_CLOUD_REGION="${GOOGLE_CLOUD_REGION:-asia-southeast1}"
    
    # 服务配置
    export BYTEC_API_BASE_URL="${BYTEC_API_BASE_URL:-https://api.bytec.com}"
    export BYTEC_DASHBOARD_URL="${BYTEC_DASHBOARD_URL:-https://dashboard.bytec.com}"
    
    echo "✅ 环境变量已设置"
}

# 6. 验证环境
verify_environment() {
    echo "🔍 验证环境配置..."
    
    # 检查关键模块
    local modules=("fastapi" "pandas" "sqlalchemy" "asyncpg")
    for module in "${modules[@]}"; do
        if ! $PYTHON_CMD -c "import $module" 2>/dev/null; then
            echo "❌ 模块缺失: $module"
            return 1
        fi
    done
    
    # 检查项目结构
    local required_dirs=("agents" "scripts" "deployment")
    for dir in "${required_dirs[@]}"; do
        if [[ ! -d "$BYTEC_ROOT_DIR/$dir" ]]; then
            echo "❌ 目录缺失: $dir"
            return 1
        fi
    done
    
    echo "✅ 环境验证通过"
}

# 7. 创建便捷命令
create_aliases() {
    echo "🎯 创建便捷命令..."
    
    # CLI 测试命令
    alias bytec-test-cli="$PYTHON_CMD $BYTEC_ROOT_DIR/scripts/test_reporter_agent_cli.py"
    alias bytec-test-integration="$PYTHON_CMD $BYTEC_ROOT_DIR/agents/reporter_agent/integration_test.py"
    
    # 服务启动命令
    alias bytec-start-api="$PYTHON_CMD $BYTEC_ROOT_DIR/main.py"
    alias bytec-start-dashboard="$PYTHON_CMD $BYTEC_ROOT_DIR/agents/dashboard_agent/manual_trigger.py"
    
    # 数据库命令
    alias bytec-db-cli="$PYTHON_CMD $BYTEC_ROOT_DIR/db_cli.py"
    alias bytec-db-check="$PYTHON_CMD $BYTEC_ROOT_DIR/check_database_data.py"
    
    echo "✅ 便捷命令已创建"
}

# 8. 显示使用帮助
show_usage() {
    echo ""
    echo "🎉 ByteC Network Agent 环境设置完成!"
    echo ""
    echo "📋 可用命令:"
    echo "  bytec-test-cli [参数]           - 运行CLI测试工具"
    echo "  bytec-test-integration         - 运行集成测试"
    echo "  bytec-start-api                - 启动API服务"
    echo "  bytec-start-dashboard          - 启动Dashboard服务"
    echo "  bytec-db-cli                   - 数据库CLI工具"
    echo "  bytec-db-check                 - 检查数据库数据"
    echo ""
    echo "📖 使用示例:"
    echo "  bytec-test-cli --partner ByteC --date-range 2024-01-01,2024-01-31"
    echo "  bytec-test-cli --partner all --format json,excel,email"
    echo ""
    echo "🔧 环境信息:"
    echo "  Python: $PYTHON_CMD"
    echo "  项目根目录: $BYTEC_ROOT_DIR"
    echo "  环境: $BYTEC_ENV"
    echo "  时区: $BYTEC_TIMEZONE"
    echo ""
}

# 主执行流程
main() {
    if ! check_python; then
        return 1
    fi
    
    if ! setup_venv; then
        return 1
    fi
    
    if ! install_dependencies; then
        return 1
    fi
    
    setup_env_vars
    
    if ! verify_environment; then
        return 1
    fi
    
    create_aliases
    show_usage
    
    echo "✅ 环境设置完成! 现在可以运行测试和服务了。"
}

# 检查是否被source执行
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "❌ 请使用 'source setup_env.sh' 来执行此脚本"
    exit 1
fi

# 执行主函数
main 