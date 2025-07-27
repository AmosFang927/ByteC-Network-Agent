#!/bin/bash

# =============================================
# ByteC Network Agent Cloud Run 部署脚本
# =============================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 项目配置
PROJECT_ID="solar-idea-463423-h8"
SERVICE_NAME="bytec-network-agent"
REGION="asia-southeast1"  # 新加坡
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
CUSTOM_DOMAIN="analytics.bytec.com"

# 数据库配置
DB_HOST="34.124.206.16"
DB_PORT="5432"
DB_NAME="postback_db"
DB_USER="postback_admin"
DB_PASSWORD="ByteC2024PostBack_CloudSQL_20250708"

# 生成时间戳
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
IMAGE_TAG="${IMAGE_NAME}:${TIMESTAMP}"
LATEST_TAG="${IMAGE_NAME}:latest"

# 显示部署信息
echo -e "${CYAN}🚀 ByteC Network Agent Cloud Run 部署${NC}"
echo -e "${CYAN}============================================${NC}"
echo -e "${BLUE}📋 项目信息:${NC}"
echo -e "   • 项目ID: ${PROJECT_ID}"
echo -e "   • 服务名: ${SERVICE_NAME}"
echo -e "   • 区域: ${REGION} (新加坡)"
echo -e "   • 自定义域名: ${CUSTOM_DOMAIN}"
echo -e "   • 时间戳: ${TIMESTAMP}"
echo -e "${CYAN}============================================${NC}"

# 检查环境
echo -e "${YELLOW}1. 检查部署环境...${NC}"

# 检查必要工具
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ Google Cloud SDK 未安装${NC}"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker 未安装${NC}"
    exit 1
fi

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker 未运行，请先启动Docker${NC}"
    exit 1
fi

# 检查必要文件
if [ ! -f "pandasai_web_app.py" ]; then
    echo -e "${RED}❌ pandasai_web_app.py 文件不存在${NC}"
    exit 1
fi

if [ ! -f "Dockerfile.pandasai-webui" ]; then
    echo -e "${RED}❌ Dockerfile.pandasai-webui 文件不存在${NC}"
    exit 1
fi

if [ ! -f "pandasai_requirements.txt" ]; then
    echo -e "${RED}❌ pandasai_requirements.txt 文件不存在${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 环境检查通过${NC}"

# 设置项目
echo -e "${YELLOW}2. 设置Google Cloud项目...${NC}"
gcloud config set project ${PROJECT_ID}

# 启用必要的API
echo -e "${YELLOW}3. 启用必要的API...${NC}"
gcloud services enable cloudbuild.googleapis.com \
    containerregistry.googleapis.com \
    run.googleapis.com \
    cloudresourcemanager.googleapis.com

# 构建Docker镜像
echo -e "${YELLOW}4. 构建Docker镜像...${NC}"
echo -e "${BLUE}📦 构建镜像标签:${NC}"
echo -e "   • ${IMAGE_TAG}"
echo -e "   • ${LATEST_TAG}"

# 构建镜像 (指定linux/amd64平台以兼容Cloud Run)
docker build --platform linux/amd64 \
    -f Dockerfile.pandasai-webui \
    -t ${IMAGE_TAG} \
    -t ${LATEST_TAG} \
    --build-arg GIT_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown") \
    --build-arg BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ") \
    --build-arg VERSION=${TIMESTAMP} \
    .

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 镜像构建失败${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 镜像构建完成${NC}"

# 推送镜像到Google Container Registry
echo -e "${YELLOW}5. 推送镜像到GCR...${NC}"
docker push ${IMAGE_TAG}
docker push ${LATEST_TAG}

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 镜像推送失败${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 镜像推送完成${NC}"

# 部署到Cloud Run
echo -e "${YELLOW}6. 部署到Cloud Run...${NC}"
echo -e "${BLUE}🔧 配置参数:${NC}"
echo -e "   • 内存: 4Gi"
echo -e "   • CPU: 2 vCPU"
echo -e "   • 最大实例: 20"
echo -e "   • 最小实例: 1"
echo -e "   • 超时: 1800秒 (30分钟)"
echo -e "   • 并发: 10 (AI处理优化)"

gcloud run deploy ${SERVICE_NAME} \
    --image ${LATEST_TAG} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --memory 4Gi \
    --cpu 2 \
    --min-instances 1 \
    --max-instances 20 \
    --port 8080 \
    --timeout 1800 \
    --concurrency 10 \
    --set-env-vars="ENVIRONMENT=production,DB_HOST=${DB_HOST},DB_PORT=${DB_PORT},DB_NAME=${DB_NAME},DB_USER=${DB_USER},DB_PASSWORD=${DB_PASSWORD},GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_GENAI_API_KEY=${GOOGLE_GENAI_API_KEY}" \
    --labels "app=bytec-network-agent,component=web-ui,version=${TIMESTAMP},environment=production" \
    --quiet

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 部署失败${NC}"
    exit 1
fi

# 获取服务URL
echo -e "${YELLOW}7. 获取服务信息...${NC}"
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)')

echo -e "${GREEN}✅ 部署完成！${NC}"

# 配置自定义域名
echo -e "${YELLOW}8. 配置自定义域名...${NC}"
echo -e "${BLUE}🌐 配置域名: ${CUSTOM_DOMAIN}${NC}"

# 尝试创建域名映射
if gcloud run domain-mappings create \
    --service ${SERVICE_NAME} \
    --domain ${CUSTOM_DOMAIN} \
    --region ${REGION} \
    --quiet 2>/dev/null; then
    
    echo -e "${GREEN}✅ 域名映射创建成功${NC}"
    
    # 获取DNS记录信息
    DNS_RECORD=$(gcloud run domain-mappings describe ${CUSTOM_DOMAIN} --region ${REGION} --format 'value(status.resourceRecords[0].rrdata)')
    
    echo -e "${YELLOW}📝 DNS配置信息:${NC}"
    echo -e "   • 记录类型: CNAME"
    echo -e "   • 主机记录: analytics"
    echo -e "   • 记录值: ${DNS_RECORD}"
    
    FINAL_URL="https://${CUSTOM_DOMAIN}"
    
else
    echo -e "${YELLOW}⚠️ 域名映射创建失败或已存在${NC}"
    echo -e "${YELLOW}💡 请手动在DNS服务商配置:${NC}"
    echo -e "   • 记录类型: CNAME"
    echo -e "   • 主机记录: analytics"
    echo -e "   • 记录值: ghs.googlehosted.com"
    
    FINAL_URL=${SERVICE_URL}
fi

# 等待服务启动
echo -e "${YELLOW}9. 等待服务启动...${NC}"
sleep 30

# 健康检查
echo -e "${YELLOW}10. 健康检查...${NC}"
echo -e "${BLUE}🏥 检查服务健康状态...${NC}"

# 检查Streamlit健康端点
if curl -f -s "${SERVICE_URL}/_stcore/health" > /dev/null; then
    echo -e "${GREEN}✅ Streamlit健康检查通过${NC}"
else
    echo -e "${YELLOW}⚠️ Streamlit健康检查失败，可能仍在启动中${NC}"
fi

# 检查应用是否可访问
if curl -f -s "${SERVICE_URL}" > /dev/null; then
    echo -e "${GREEN}✅ 应用可访问${NC}"
else
    echo -e "${YELLOW}⚠️ 应用暂时不可访问，请稍后重试${NC}"
fi

# 显示部署结果
echo -e "\n${CYAN}🎉 ByteC Network Agent 部署完成！${NC}"
echo -e "${CYAN}============================================${NC}"
echo -e "${BLUE}📱 访问地址:${NC}"
echo -e "   • 主要地址: ${FINAL_URL}"
echo -e "   • 默认地址: ${SERVICE_URL}"
echo -e ""
echo -e "${BLUE}📋 功能特性:${NC}"
echo -e "   ✅ 自然语言查询 - 支持中文AI对话"
echo -e "   ✅ 实时数据分析 - PostBack转化数据"
echo -e "   ✅ 交互式图表 - Plotly可视化"
echo -e "   ✅ Partner筛选 - 多Partner支持"
echo -e "   ✅ 响应式设计 - 支持移动端"
echo -e ""
echo -e "${BLUE}🔧 管理命令:${NC}"
echo -e "   • 查看日志: gcloud run services logs read ${SERVICE_NAME} --region=${REGION}"
echo -e "   • 查看指标: gcloud run services describe ${SERVICE_NAME} --region=${REGION}"
echo -e "   • 更新服务: gcloud run services update ${SERVICE_NAME} --region=${REGION}"
echo -e "   • 删除服务: gcloud run services delete ${SERVICE_NAME} --region=${REGION}"
echo -e ""
echo -e "${BLUE}💡 使用指南:${NC}"
echo -e "   • 在查询框中输入中文问题，如'今天哪个offer表现最好？'"
echo -e "   • 使用侧边栏选择不同的Partner和时间范围"
echo -e "   • 查看实时图表和数据分析结果"
echo -e ""
echo -e "${BLUE}🌐 DNS配置（如果使用自定义域名）:${NC}"
echo -e "   • 域名: ${CUSTOM_DOMAIN}"
echo -e "   • 记录类型: CNAME"
echo -e "   • 主机记录: analytics"
echo -e "   • 记录值: ghs.googlehosted.com"
echo -e ""
echo -e "${BLUE}💰 成本估算:${NC}"
echo -e "   • 基础费用: 每月约 $30-50 (中等使用量)"
echo -e "   • 包含: 计算资源、网络流量、存储"
echo -e "   • 优化: 最小实例数为1，避免冷启动"
echo -e ""
echo -e "${PURPLE}🎯 部署信息:${NC}"
echo -e "   • 镜像: ${LATEST_TAG}"
echo -e "   • 时间戳: ${TIMESTAMP}"
echo -e "   • 区域: ${REGION}"
echo -e "   • 环境: 生产环境"
echo -e "${CYAN}============================================${NC}"

# 保存部署信息
cat > pandasai_deployment_info.txt << EOF
ByteC Network Agent 部署信息
==========================

部署时间: $(date)
项目ID: ${PROJECT_ID}
服务名称: ${SERVICE_NAME}
区域: ${REGION}
镜像: ${LATEST_TAG}
自定义域名: ${CUSTOM_DOMAIN}
服务URL: ${SERVICE_URL}
最终URL: ${FINAL_URL}

功能特性:
- 自然语言查询 (中文AI对话)
- 实时数据分析 (PostBack转化数据)
- 交互式图表 (Plotly可视化)
- Partner筛选 (多Partner支持)
- 响应式设计 (移动端支持)

管理命令:
- 查看日志: gcloud run services logs read ${SERVICE_NAME} --region=${REGION}
- 查看指标: gcloud run services describe ${SERVICE_NAME} --region=${REGION}
- 更新服务: gcloud run services update ${SERVICE_NAME} --region=${REGION}
- 删除服务: gcloud run services delete ${SERVICE_NAME} --region=${REGION}

DNS配置:
- 域名: ${CUSTOM_DOMAIN}
- 记录类型: CNAME
- 主机记录: analytics
- 记录值: ghs.googlehosted.com

部署镜像: ${LATEST_TAG}
部署时间戳: ${TIMESTAMP}
EOF

echo -e "${GREEN}✅ 部署信息已保存到 pandasai_deployment_info.txt${NC}"
echo -e "${CYAN}🚀 ByteC Network Agent 部署完成！${NC}" 