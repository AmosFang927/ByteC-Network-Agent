#!/bin/bash

# Reporter-Agent 簡化本地測試部署
set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Reporter-Agent 本地測試部署${NC}"
echo "=============================================="

# 返回到專案根目錄
cd ../../..

echo -e "${YELLOW}1. 檢查當前目錄和文件...${NC}"
echo "當前目錄: $(pwd)"
echo "檢查關鍵文件:"
echo "  ✓ 主程序: $(test -f agents/reporter_agent/optimized_main.py && echo '存在' || echo '不存在')"
echo "  ✓ CLI工具: $(test -f agents/reporter_agent/optimized_cli.py && echo '存在' || echo '不存在')"
echo "  ✓ 配置: $(test -f agents/reporter_agent/requirements.txt && echo '存在' || echo '不存在')"

# 檢查gcloud認證
echo -e "${YELLOW}2. 檢查gcloud認證...${NC}"
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "."; then
    echo -e "${RED}❌ 請先運行 gcloud auth login${NC}"
    exit 1
fi

# 設置項目
echo -e "${YELLOW}3. 設置Google Cloud項目...${NC}"
PROJECT_ID="solar-idea-463423-h8"
SERVICE_NAME="reporter-agent-optimized"
REGION="asia-southeast1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

gcloud config set project $PROJECT_ID

# 創建簡化Dockerfile
echo -e "${YELLOW}4. 創建Dockerfile...${NC}"
cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# 環境變數
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    gcc g++ curl \
    && rm -rf /var/lib/apt/lists/*

# 複製專案文件
COPY . .

# 安裝依賴
RUN pip install --no-cache-dir -r agents/reporter_agent/requirements.txt && \
    pip install --no-cache-dir redis aioredis

# 設置權限
RUN chmod +x agents/reporter_agent/optimized_main.py

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

EXPOSE 8080

# 啟動命令
CMD ["python", "-m", "agents.reporter_agent.optimized_main", "api", "--host", "0.0.0.0", "--port", "8080"]
EOF

# 構建並推送鏡像
echo -e "${YELLOW}5. 構建Docker鏡像...${NC}"
gcloud builds submit --tag $IMAGE_NAME --timeout=1200s .

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Docker鏡像構建失敗${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker鏡像構建成功${NC}"

# 部署到Cloud Run
echo -e "${YELLOW}6. 部署到Cloud Run...${NC}"
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --memory 4Gi \
    --cpu 2 \
    --timeout 1800 \
    --max-instances 20 \
    --concurrency 1000 \
    --min-instances 1 \
    --set-env-vars="PYTHONPATH=/app,ENVIRONMENT=production,REDIS_ENABLED=false" \
    --quiet

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Cloud Run部署失敗${NC}"
    exit 1
fi

# 獲取服務URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")

echo -e "${GREEN}✅ 部署成功！${NC}"
echo ""
echo "=============================================="
echo -e "${GREEN}🎉 部署完成信息${NC}"
echo "=============================================="
echo -e "${BLUE}服務URL: $SERVICE_URL${NC}"
echo -e "${BLUE}健康檢查: $SERVICE_URL/health${NC}"
echo -e "${BLUE}Partners列表: $SERVICE_URL/partners${NC}"
echo ""
echo -e "${YELLOW}📋 測試命令:${NC}"
echo "  curl '$SERVICE_URL/health'"
echo "  curl '$SERVICE_URL/test?records=100'"
echo "  curl '$SERVICE_URL/trigger?partner=ByteC&days=1'"
echo ""

# 立即測試部署
echo -e "${YELLOW}7. 執行部署後測試...${NC}"
echo "等待服務啟動 (10秒)..."
sleep 10

echo "測試健康檢查..."
if curl -f "$SERVICE_URL/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 健康檢查通過${NC}"
else
    echo -e "${RED}❌ 健康檢查失敗${NC}"
fi

echo "測試性能..."
if curl -f "$SERVICE_URL/test?records=100" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 性能測試通過${NC}"
else
    echo -e "${RED}❌ 性能測試失敗${NC}"
fi

# 清理臨時文件
rm -f Dockerfile

echo -e "${GREEN}✅ 簡化部署完成！${NC}" 