#!/bin/bash

# =============================================
# ByteC Performance Dashboard Agent - 前端部署脚本
# 部署到 Google Cloud Run
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
SERVICE_NAME="bytec-performance-dashboard"
REGION="asia-southeast1"  # 新加坡
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
CUSTOM_DOMAIN="dashboard.bytec.com"

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
echo -e "${CYAN}🚀 ByteC Performance Dashboard Agent - 前端部署${NC}"
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
if [ ! -d "agents/dashboard_agent" ]; then
    echo -e "${RED}❌ agents/dashboard_agent 目录不存在${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 环境检查通过${NC}"

# 设置gcloud项目
echo -e "${YELLOW}2. 设置Google Cloud项目...${NC}"
gcloud config set project ${PROJECT_ID}

# 启用必要的API
echo -e "${YELLOW}3. 启用必要的API服务...${NC}"
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# 创建Dashboard专用的requirements.txt
echo -e "${YELLOW}4. 创建Dashboard专用依赖文件...${NC}"
cat > dashboard_requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn==0.24.0
jinja2==3.1.2
python-multipart==0.0.6
asyncpg==0.29.0
pandas==2.1.3
plotly==5.17.0
pandasai==1.5.11
vertexai==1.38.1
google-cloud-aiplatform==1.38.1
requests==2.31.0
aiofiles==23.2.1
websockets==12.0
gunicorn==21.2.0
EOF

# 创建Dashboard专用Dockerfile
echo -e "${YELLOW}5. 创建Dashboard专用Dockerfile...${NC}"
cat > Dockerfile.dashboard << 'EOF'
# 使用官方Python运行时作为基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements文件
COPY dashboard_requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r dashboard_requirements.txt

# 复制项目文件
COPY agents/dashboard_agent/ .
COPY shared/ shared/
COPY config.py .

# 创建必要的目录
RUN mkdir -p /app/logs /app/temp /app/static

# 设置权限
RUN chmod +x backend/dashboard_server.py

# 暴露端口
EXPOSE 8080

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# 启动命令
CMD ["python", "backend/dashboard_server.py", "--port", "8080", "--host", "0.0.0.0"]
EOF

echo -e "${GREEN}✅ Dashboard Dockerfile创建完成${NC}"

# 构建Docker镜像
echo -e "${YELLOW}6. 构建Docker镜像...${NC}"
docker build -f Dockerfile.dashboard -t ${IMAGE_TAG} .
docker tag ${IMAGE_TAG} ${LATEST_TAG}

echo -e "${GREEN}✅ Docker镜像构建完成${NC}"

# 推送镜像到Container Registry
echo -e "${YELLOW}7. 推送镜像到Container Registry...${NC}"
gcloud auth configure-docker
docker push ${IMAGE_TAG}
docker push ${LATEST_TAG}

echo -e "${GREEN}✅ 镜像推送完成${NC}"

# 部署到Cloud Run
echo -e "${YELLOW}8. 部署到Cloud Run...${NC}"
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_TAG} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --set-env-vars="DB_HOST=${DB_HOST},DB_PORT=${DB_PORT},DB_NAME=${DB_NAME},DB_USER=${DB_USER},DB_PASSWORD=${DB_PASSWORD}" \
    --memory 4Gi \
    --cpu 2 \
    --concurrency 100 \
    --timeout 900s \
    --max-instances 5 \
    --min-instances 1

echo -e "${GREEN}✅ Cloud Run部署完成${NC}"

# 获取服务URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format="value(status.url)")

echo -e "${YELLOW}9. 配置自定义域名...${NC}"
# 设置域名映射
gcloud run domain-mappings create \
    --service ${SERVICE_NAME} \
    --domain ${CUSTOM_DOMAIN} \
    --region ${REGION} \
    --platform managed || echo "域名映射可能已存在"

# 健康检查
echo -e "${YELLOW}10. 执行健康检查...${NC}"
sleep 10
if curl -f "${SERVICE_URL}/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 服务健康检查通过${NC}"
else
    echo -e "${YELLOW}⚠️ 服务健康检查失败，请检查日志${NC}"
fi

# 清理本地镜像和临时文件
echo -e "${YELLOW}11. 清理本地镜像...${NC}"
docker rmi ${IMAGE_TAG} ${LATEST_TAG} || true
rm -f dashboard_requirements.txt Dockerfile.dashboard

# 部署完成
echo -e "${CYAN}🎉 部署完成！${NC}"
echo -e "${CYAN}============================================${NC}"
echo -e "${GREEN}📊 部署信息:${NC}"
echo -e "   • 服务URL: ${SERVICE_URL}"
echo -e "   • 自定义域名: https://${CUSTOM_DOMAIN}"
echo -e "   • 健康检查: ${SERVICE_URL}/health"
echo -e "   • 区域: ${REGION}"
echo -e "   • 镜像: ${IMAGE_TAG}"
echo -e "${CYAN}============================================${NC}"

echo -e "${BLUE}📋 管理命令:${NC}"
echo -e "   • 查看日志: gcloud run services logs read ${SERVICE_NAME} --region=${REGION}"
echo -e "   • 查看指标: gcloud run services describe ${SERVICE_NAME} --region=${REGION}"
echo -e "   • 更新服务: gcloud run services update ${SERVICE_NAME} --region=${REGION}"
echo -e "   • 删除服务: gcloud run services delete ${SERVICE_NAME} --region=${REGION}"

echo -e "${CYAN}============================================${NC}"
echo -e "${GREEN}✅ ByteC Performance Dashboard Agent 前端部署完成！${NC}"

# 功能特性说明
echo -e "${BLUE}🎯 功能特性:${NC}"
echo -e "   • 自然语言查询 (中文AI对话)"
echo -e "   • 实时数据分析 (PostBack转化数据)"
echo -e "   • 交互式图表 (Plotly可视化)"
echo -e "   • Partner筛选 (多Partner支持)"
echo -e "   • 响应式设计 (移动端支持)"
echo -e "   • 性能监控面板" 