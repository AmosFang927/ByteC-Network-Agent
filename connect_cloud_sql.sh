#!/bin/bash

# ByteC Network Agent - Google Cloud SQL 连接脚本
# 自动连接到 bytec-postback-db 实例

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 数据库连接配置
PROJECT_ID="solar-idea-463423-h8"
INSTANCE_NAME="bytec-postback-db"
DATABASE_NAME="postback_db"
DB_USER="postback_admin"
DB_PASSWORD="ByteC2024PostBack_CloudSQL"
CONNECTION_NAME="solar-idea-463423-h8:asia-southeast1:bytec-postback-db"

echo -e "${BLUE}🔗 连接到 Google Cloud SQL...${NC}"
echo -e "${BLUE}实例: $INSTANCE_NAME${NC}"
echo -e "${BLUE}数据库: $DATABASE_NAME${NC}"
echo -e "${BLUE}用户: $DB_USER${NC}"
echo ""

# 设置项目
gcloud config set project $PROJECT_ID

# 方法1: 使用 Cloud SQL Proxy
echo -e "${YELLOW}📋 可用连接方法:${NC}"
echo -e "${YELLOW}1. 使用 gcloud sql connect (推荐)${NC}"
echo -e "${YELLOW}2. 使用 psql 直接连接${NC}"
echo -e "${YELLOW}3. 使用 Cloud SQL Proxy${NC}"
echo ""

# 检查是否有 psql 客户端
if command -v psql &> /dev/null; then
    echo -e "${GREEN}✅ 检测到 psql 客户端${NC}"
    HAS_PSQL=true
else
    echo -e "${YELLOW}⚠️ 未检测到 psql 客户端，建议安装: brew install postgresql${NC}"
    HAS_PSQL=false
fi

# 获取实例 IP
INSTANCE_IP=$(gcloud sql instances describe $INSTANCE_NAME --format="value(ipAddresses[0].ipAddress)")
echo -e "${BLUE}实例 IP: $INSTANCE_IP${NC}"

# 创建临时密码文件
PGPASSFILE="/tmp/.pgpass_bytec"
echo "$INSTANCE_IP:5432:$DATABASE_NAME:$DB_USER:$DB_PASSWORD" > $PGPASSFILE
chmod 600 $PGPASSFILE

echo ""
echo -e "${GREEN}🚀 启动连接...${NC}"

# 使用 expect 来自动输入密码
if command -v expect &> /dev/null; then
    echo -e "${YELLOW}使用 expect 自动输入密码...${NC}"
    
    expect << EOF
spawn gcloud sql connect $INSTANCE_NAME --user=$DB_USER --database=$DATABASE_NAME
expect "Password:"
send "$DB_PASSWORD\r"
interact
EOF
    
elif [ "$HAS_PSQL" = true ]; then
    echo -e "${YELLOW}使用 psql 直接连接...${NC}"
    
    # 临时允许 IP 访问
    echo -e "${YELLOW}正在允许当前 IP 访问...${NC}"
    gcloud sql instances patch $INSTANCE_NAME --authorized-networks=0.0.0.0/0 --quiet
    
    # 等待配置生效
    sleep 10
    
    # 使用 psql 连接
    PGPASSWORD=$DB_PASSWORD psql -h $INSTANCE_IP -U $DB_USER -d $DATABASE_NAME -p 5432
    
else
    echo -e "${YELLOW}使用 gcloud sql connect (需要手动输入密码)...${NC}"
    echo -e "${YELLOW}密码: $DB_PASSWORD${NC}"
    echo ""
    
    gcloud sql connect $INSTANCE_NAME --user=$DB_USER --database=$DATABASE_NAME
fi

# 清理临时文件
rm -f $PGPASSFILE

echo -e "${GREEN}✅ 连接会话结束${NC}" 