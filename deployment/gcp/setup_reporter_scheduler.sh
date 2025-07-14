#!/bin/bash
# Google Cloud Scheduler设置脚本 - Reporter-Agent-8am-All
# 服务器位置：新加坡 (asia-southeast1)
# 时区：GMT+8
# 触发时间：每日上午8点
# 参数：--partner all --date-range "2 days ago"

set -e

# 配置变量
PROJECT_ID="solar-idea-463423-h8"
REGION="asia-southeast1"
TIMEZONE="Asia/Singapore"
JOB_NAME="Reporter-Agent-8am-All"
SERVICE_NAME="bytec-network-agent"
SERVICE_URL="https://api.bytec.com"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印函数
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_step() {
    echo -e "${BLUE}🔧 $1${NC}"
}

# 主标题
echo "================================================="
echo "🚀 Google Cloud Scheduler 设置脚本"
echo "================================================="
echo "项目: $PROJECT_ID"
echo "区域: $REGION"
echo "时区: $TIMEZONE"
echo "任务名称: $JOB_NAME"
echo "服务URL: $SERVICE_URL"
echo "================================================="

# 检查是否已登录gcloud
print_step "检查gcloud认证状态..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
    print_error "未登录gcloud，请先运行: gcloud auth login"
    exit 1
fi
print_success "gcloud认证正常"

# 设置项目
print_step "设置项目..."
gcloud config set project $PROJECT_ID
print_success "项目设置为: $PROJECT_ID"

# 启用必要的API
print_step "启用Cloud Scheduler API..."
gcloud services enable cloudscheduler.googleapis.com
print_success "Cloud Scheduler API已启用"

print_step "启用Cloud Run API..."
gcloud services enable run.googleapis.com
print_success "Cloud Run API已启用"

# 检查服务是否存在
print_step "检查Cloud Run服务状态..."
if gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(metadata.name)" 2>/dev/null | grep -q $SERVICE_NAME; then
    print_success "Cloud Run服务 $SERVICE_NAME 已存在"
    
    # 获取服务URL
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")
    print_info "服务URL: $SERVICE_URL"
else
    print_error "Cloud Run服务 $SERVICE_NAME 不存在，请先部署服务"
    exit 1
fi

# 删除现有的调度任务（如果存在）
print_step "检查现有调度任务..."
if gcloud scheduler jobs describe $JOB_NAME --location=$REGION 2>/dev/null; then
    print_warning "发现现有调度任务，正在删除..."
    gcloud scheduler jobs delete $JOB_NAME --location=$REGION --quiet
    print_success "现有调度任务已删除"
fi

# 创建服务账户（如果不存在）
SERVICE_ACCOUNT_NAME="reporter-agent-scheduler"
SERVICE_ACCOUNT_EMAIL="$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com"

print_step "检查服务账户..."
if ! gcloud iam service-accounts describe $SERVICE_ACCOUNT_EMAIL 2>/dev/null; then
    print_step "创建服务账户..."
    gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
        --display-name="Reporter Agent Scheduler" \
        --description="Service account for Reporter Agent scheduled tasks"
    print_success "服务账户已创建: $SERVICE_ACCOUNT_EMAIL"
else
    print_success "服务账户已存在: $SERVICE_ACCOUNT_EMAIL"
fi

# 为服务账户分配权限
print_step "分配服务账户权限..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/run.invoker"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/cloudscheduler.jobRunner"

print_success "服务账户权限已分配"

# 创建调度任务
print_step "创建调度任务..."

# 准备HTTP请求的载荷
cat > /tmp/scheduler_payload.json << EOF
{
    "partner_name": "all",
    "start_date": "auto",
    "end_date": "auto",
    "output_formats": ["excel", "feishu", "email"],
    "send_self_email": false,
    "dry_run": false,
    "days_ago": 2
}
EOF

# 创建Cloud Scheduler任务
gcloud scheduler jobs create http $JOB_NAME \
    --location=$REGION \
    --schedule="0 8 * * *" \
    --time-zone=$TIMEZONE \
    --uri="$SERVICE_URL/api/reporter/scheduled-report" \
    --http-method=POST \
    --headers="Content-Type=application/json" \
    --message-body-from-file=/tmp/scheduler_payload.json \
    --oidc-service-account-email=$SERVICE_ACCOUNT_EMAIL \
    --oidc-token-audience="$SERVICE_URL" \
    --description="Reporter Agent daily scheduled report generation - All partners, 2 days ago data, runs daily at 8 AM SGT"

print_success "调度任务创建成功！"

# 清理临时文件
rm -f /tmp/scheduler_payload.json

# 验证调度任务
print_step "验证调度任务..."
gcloud scheduler jobs describe $JOB_NAME --location=$REGION --format="table(
    name,
    schedule,
    timeZone,
    httpTarget.uri,
    state
)"

print_success "调度任务验证完成"

# 创建监控脚本
print_step "创建监控脚本..."
cat > monitor_scheduler.sh << 'EOF'
#!/bin/bash
# Reporter Agent Scheduler监控脚本

PROJECT_ID="solar-idea-463423-h8"
REGION="asia-southeast1"
JOB_NAME="Reporter-Agent-8am-All"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

echo "================================================="
echo "📊 Reporter Agent Scheduler 监控面板"
echo "================================================="

# 检查任务状态
print_info "检查调度任务状态..."
gcloud scheduler jobs describe $JOB_NAME --location=$REGION --format="table(
    name,
    schedule,
    timeZone,
    state,
    lastAttemptTime,
    nextRunTime
)"

echo ""
print_info "最近执行历史..."
gcloud scheduler jobs list --location=$REGION --filter="name:$JOB_NAME" --format="table(
    name,
    schedule,
    state,
    lastAttemptTime,
    nextRunTime
)"

echo ""
print_info "查看执行日志..."
gcloud logging read "
    resource.type=cloud_scheduler_job AND
    resource.labels.job_id=$JOB_NAME AND
    resource.labels.location=$REGION
" --limit=5 --format="table(timestamp, severity, textPayload)"

echo ""
print_info "手动触发测试..."
read -p "是否要手动触发一次测试? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_info "正在手动触发调度任务..."
    gcloud scheduler jobs run $JOB_NAME --location=$REGION
    print_success "手动触发完成，请查看日志检查执行结果"
fi

echo ""
print_info "使用以下命令查看实时日志:"
echo "gcloud logging tail \"resource.type=cloud_scheduler_job AND resource.labels.job_id=$JOB_NAME\""
EOF

chmod +x monitor_scheduler.sh
print_success "监控脚本已创建: monitor_scheduler.sh"

# 创建管理脚本
print_step "创建管理脚本..."
cat > manage_scheduler.sh << 'EOF'
#!/bin/bash
# Reporter Agent Scheduler管理脚本

PROJECT_ID="solar-idea-463423-h8"
REGION="asia-southeast1"
JOB_NAME="Reporter-Agent-8am-All"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

show_help() {
    echo "Reporter Agent Scheduler 管理脚本"
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  status    - 查看任务状态"
    echo "  start     - 启动任务"
    echo "  stop      - 停止任务"
    echo "  run       - 手动触发任务"
    echo "  logs      - 查看日志"
    echo "  delete    - 删除任务"
    echo "  help      - 显示帮助"
}

case "$1" in
    status)
        print_info "查看任务状态..."
        gcloud scheduler jobs describe $JOB_NAME --location=$REGION
        ;;
    start)
        print_info "启动任务..."
        gcloud scheduler jobs resume $JOB_NAME --location=$REGION
        print_success "任务已启动"
        ;;
    stop)
        print_info "停止任务..."
        gcloud scheduler jobs pause $JOB_NAME --location=$REGION
        print_success "任务已停止"
        ;;
    run)
        print_info "手动触发任务..."
        gcloud scheduler jobs run $JOB_NAME --location=$REGION
        print_success "任务已触发"
        ;;
    logs)
        print_info "查看任务日志..."
        gcloud logging read "
            resource.type=cloud_scheduler_job AND
            resource.labels.job_id=$JOB_NAME AND
            resource.labels.location=$REGION
        " --limit=10 --format="table(timestamp, severity, textPayload)"
        ;;
    delete)
        print_warning "确定要删除调度任务吗？"
        read -p "输入 'yes' 确认删除: " -r
        if [[ $REPLY == "yes" ]]; then
            gcloud scheduler jobs delete $JOB_NAME --location=$REGION --quiet
            print_success "任务已删除"
        else
            print_info "取消删除"
        fi
        ;;
    help|*)
        show_help
        ;;
esac
EOF

chmod +x manage_scheduler.sh
print_success "管理脚本已创建: manage_scheduler.sh"

# 完成信息
echo ""
echo "================================================="
echo "🎉 Cloud Scheduler 设置完成！"
echo "================================================="
echo "任务名称: $JOB_NAME"
echo "执行时间: 每日上午8点 (GMT+8)"
echo "时区: $TIMEZONE"
echo "参数: 所有Partner, 2天前数据"
echo "输出格式: Excel + 飞书 + 邮件"
echo ""
echo "管理命令:"
echo "  ./monitor_scheduler.sh   - 监控任务状态"
echo "  ./manage_scheduler.sh    - 管理任务"
echo ""
echo "下次执行时间:"
gcloud scheduler jobs describe $JOB_NAME --location=$REGION --format="value(nextRunTime)"
echo ""
print_success "设置完成！调度任务将在每日上午8点自动执行。" 