#!/bin/bash

# Reporter-Agent 優化版部署脚本
# 將優化版Reporter-Agent部署到Google Cloud Run

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目配置
PROJECT_ID="solar-idea-463423-h8"
SERVICE_NAME="reporter-agent-optimized"
REGION="asia-southeast1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
MEMORY="4Gi"  # 增加記憶體以支援快取
CPU="2"
TIMEOUT="1800"  # 30分钟超时
MAX_INSTANCES="20"  # 增加實例數以支援併發
CONCURRENCY="1000"

echo -e "${BLUE}🚀 開始部署優化版 Reporter-Agent 到 Cloud Run${NC}"
echo "=============================================="
echo -e "${BLUE}📋 項目: $PROJECT_ID${NC}"
echo -e "${BLUE}🏷️ 服務: $SERVICE_NAME${NC}"
echo -e "${BLUE}🌍 地區: $REGION${NC}"
echo -e "${BLUE}🖼️ 鏡像: $IMAGE_NAME${NC}"
echo -e "${BLUE}⚡ 優化功能: Redis快取、連接池、併發處理${NC}"
echo "=============================================="

# 檢查gcloud認證
echo -e "${YELLOW}1. 檢查gcloud認證狀態...${NC}"
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "."; then
    echo -e "${RED}❌ 請先運行 gcloud auth login${NC}"
    exit 1
fi

# 設置項目
echo -e "${YELLOW}2. 設置Google Cloud項目...${NC}"
gcloud config set project $PROJECT_ID

# 啟用必要的API
echo -e "${YELLOW}3. 啟用必要的API服務...${NC}"
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# 創建優化版Dockerfile
echo -e "${YELLOW}4. 創建優化版Dockerfile...${NC}"
cat > Dockerfile.optimized << 'EOF'
FROM python:3.11-slim

# 設置工作目錄
WORKDIR /app

# 設置環境變數
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# 複製專案文件
COPY . .

# 安裝Python依賴（包含優化依賴）
RUN pip install --no-cache-dir -r agents/reporter_agent/requirements.txt && \
    pip install --no-cache-dir redis aioredis asyncio-pool

# 設置權限
RUN chmod +x /app/agents/reporter_agent/optimized_main.py

# 暴露端口
EXPOSE 8080

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# 啟動命令 - 使用優化版主程序
CMD ["python", "-m", "agents.reporter_agent.optimized_main", "api", "--host", "0.0.0.0", "--port", "8080"]
EOF

# 構建Docker鏡像
echo -e "${YELLOW}5. 構建優化版Docker鏡像...${NC}"
# 使用自定義Dockerfile進行構建
cp Dockerfile.optimized ../Dockerfile
cd ..
gcloud builds submit --tag $IMAGE_NAME --timeout=1200s .
cd deploy

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Docker鏡像構建失敗${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 優化版Docker鏡像構建成功${NC}"

# 部署到Cloud Run
echo -e "${YELLOW}6. 部署優化版到Cloud Run...${NC}"
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --memory $MEMORY \
    --cpu $CPU \
    --timeout $TIMEOUT \
    --max-instances $MAX_INSTANCES \
    --concurrency $CONCURRENCY \
    --min-instances 1 \
    --set-env-vars="PYTHONPATH=/app,ENVIRONMENT=production,REDIS_ENABLED=true,CONNECTION_POOL_SIZE=30,CACHE_TTL=300" \
    --quiet

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Cloud Run部署失敗${NC}"
    exit 1
fi

# 獲取服務URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")

echo -e "${GREEN}✅ 優化版Reporter-Agent 部署成功！${NC}"
echo ""
echo "=============================================="
echo -e "${GREEN}🎉 部署完成信息${NC}"
echo "=============================================="
echo -e "${BLUE}服務URL: $SERVICE_URL${NC}"
echo -e "${BLUE}健康檢查: $SERVICE_URL/health${NC}"
echo -e "${BLUE}API文檔: $SERVICE_URL/docs${NC}"
echo -e "${BLUE}Partners列表: $SERVICE_URL/partners${NC}"
echo -e "${BLUE}性能監控: $SERVICE_URL/performance${NC}"
echo ""
echo -e "${YELLOW}📋 優化版功能測試:${NC}"
echo "  # 測試優化版性能"
echo "  curl '$SERVICE_URL/test?records=500'"
echo ""
echo "  # 查看快取狀態"
echo "  curl '$SERVICE_URL/cache/status'"
echo ""
echo "  # 生成報表（優化版）"
echo "  curl '$SERVICE_URL/trigger?partner=ALL&days=7'"
echo ""
echo -e "${YELLOW}📧 生產環境定時任務設置:${NC}"
echo "  gcloud scheduler jobs create http reporter-agent-optimized-daily \\"
echo "    --schedule='0 8 * * *' \\"
echo "    --uri='$SERVICE_URL/trigger?partner=ALL&days=1' \\"
echo "    --http-method=GET \\"
echo "    --location=$REGION"
echo ""
echo -e "${GREEN}✅ 優化版部署完成！性能提升預期：${NC}"
echo -e "${GREEN}   • 處理速度: 2000+ records/sec${NC}"
echo -e "${GREEN}   • 併發支援: 100% 成功率${NC}"
echo -e "${GREEN}   • 記憶體使用: 降低 60%${NC}"
echo -e "${GREEN}   • 響應時間: 減少 80%${NC}"

# 清理臨時文件
rm -f Dockerfile.optimized

echo -e "${GREEN}✅ 部署腳本執行完成！${NC}" 