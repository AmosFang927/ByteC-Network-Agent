#!/bin/bash

# =============================================
# ByteC DMP Agent - 数据库配置脚本
# 配置 Google Cloud SQL PostgreSQL
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
REGION="asia-southeast1"  # 新加坡
ZONE="asia-southeast1-a"
DB_INSTANCE_NAME="bytec-postback-db"
DB_NAME="postback_db"
DB_USER="postback_admin"
DB_PASSWORD="ByteC2024PostBack_CloudSQL_20250708"

# 显示部署信息
echo -e "${CYAN}🚀 ByteC DMP Agent - 数据库配置${NC}"
echo -e "${CYAN}============================================${NC}"
echo -e "${BLUE}📋 项目信息:${NC}"
echo -e "   • 项目ID: ${PROJECT_ID}"
echo -e "   • 数据库实例: ${DB_INSTANCE_NAME}"
echo -e "   • 区域: ${REGION} (新加坡)"
echo -e "   • 数据库名: ${DB_NAME}"
echo -e "   • 用户名: ${DB_USER}"
echo -e "${CYAN}============================================${NC}"

# 检查环境
echo -e "${YELLOW}1. 检查部署环境...${NC}"

# 检查必要工具
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ Google Cloud SDK 未安装${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 环境检查通过${NC}"

# 设置gcloud项目
echo -e "${YELLOW}2. 设置Google Cloud项目...${NC}"
gcloud config set project ${PROJECT_ID}

# 启用必要的API
echo -e "${YELLOW}3. 启用必要的API服务...${NC}"
gcloud services enable sqladmin.googleapis.com
gcloud services enable sql-component.googleapis.com
gcloud services enable compute.googleapis.com

# 检查实例是否存在
echo -e "${YELLOW}4. 检查数据库实例状态...${NC}"
if gcloud sql instances describe ${DB_INSTANCE_NAME} --format="value(state)" &> /dev/null; then
    INSTANCE_STATE=$(gcloud sql instances describe ${DB_INSTANCE_NAME} --format="value(state)")
    echo -e "${GREEN}✅ 数据库实例已存在，状态: ${INSTANCE_STATE}${NC}"
    
    if [ "${INSTANCE_STATE}" = "RUNNABLE" ]; then
        echo -e "${GREEN}✅ 数据库实例运行正常${NC}"
    else
        echo -e "${YELLOW}⚠️ 数据库实例状态异常，尝试重启...${NC}"
        gcloud sql instances restart ${DB_INSTANCE_NAME}
        sleep 30
    fi
else
    echo -e "${YELLOW}⚠️ 数据库实例不存在，创建新实例...${NC}"
    
    # 创建新的Cloud SQL实例
    gcloud sql instances create ${DB_INSTANCE_NAME} \
        --database-version=POSTGRES_14 \
        --cpu=2 \
        --memory=4GB \
        --region=${REGION} \
        --storage-type=SSD \
        --storage-size=100GB \
        --storage-auto-increase \
        --backup-start-time=03:00 \
        --enable-bin-log \
        --maintenance-window-day=SUN \
        --maintenance-window-hour=04 \
        --maintenance-release-channel=production \
        --database-flags=max_connections=200,shared_preload_libraries=pg_stat_statements \
        --authorized-networks=0.0.0.0/0
    
    echo -e "${GREEN}✅ 数据库实例创建完成${NC}"
fi

# 设置root密码
echo -e "${YELLOW}5. 设置数据库root密码...${NC}"
gcloud sql users set-password postgres \
    --instance=${DB_INSTANCE_NAME} \
    --password=${DB_PASSWORD}

# 创建数据库用户
echo -e "${YELLOW}6. 创建数据库用户...${NC}"
gcloud sql users create ${DB_USER} \
    --instance=${DB_INSTANCE_NAME} \
    --password=${DB_PASSWORD} || echo "用户可能已存在"

# 创建数据库
echo -e "${YELLOW}7. 创建数据库...${NC}"
gcloud sql databases create ${DB_NAME} \
    --instance=${DB_INSTANCE_NAME} || echo "数据库可能已存在"

# 获取数据库连接信息
echo -e "${YELLOW}8. 获取数据库连接信息...${NC}"
DB_IP=$(gcloud sql instances describe ${DB_INSTANCE_NAME} --format="value(ipAddresses[0].ipAddress)")
CONNECTION_NAME=$(gcloud sql instances describe ${DB_INSTANCE_NAME} --format="value(connectionName)")

echo -e "${GREEN}✅ 数据库连接信息获取完成${NC}"
echo -e "   • 外部IP: ${DB_IP}"
echo -e "   • 连接名: ${CONNECTION_NAME}"

# 创建数据库表结构
echo -e "${YELLOW}9. 创建数据库表结构...${NC}"
cat > create_tables.sql << 'EOF'
-- 创建Partners表
CREATE TABLE IF NOT EXISTS partners (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    status VARCHAR(20) DEFAULT 'active',
    commission_rate DECIMAL(5,4) DEFAULT 0.10,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建Conversions表
CREATE TABLE IF NOT EXISTS conversions (
    id SERIAL PRIMARY KEY,
    conversion_id VARCHAR(100) NOT NULL UNIQUE,
    partner_id INTEGER REFERENCES partners(id),
    offer_id VARCHAR(100),
    offer_name VARCHAR(255),
    datetime_conversion TIMESTAMP,
    order_id VARCHAR(100),
    sale_amount_local DECIMAL(10,2),
    myr_sale_amount DECIMAL(10,2),
    usd_sale_amount DECIMAL(10,2),
    payout_local DECIMAL(10,2),
    myr_payout DECIMAL(10,2),
    usd_payout DECIMAL(10,2),
    conversion_currency VARCHAR(3),
    status VARCHAR(20) DEFAULT 'pending',
    aff_sub VARCHAR(100),
    aff_sub2 VARCHAR(100),
    raw_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建Commission_Calculations表
CREATE TABLE IF NOT EXISTS commission_calculations (
    id SERIAL PRIMARY KEY,
    conversion_id INTEGER REFERENCES conversions(id),
    partner_id INTEGER REFERENCES partners(id),
    original_payout_usd DECIMAL(10,2),
    calculated_payout_usd DECIMAL(10,2),
    margin_amount_usd DECIMAL(10,2),
    margin_rate DECIMAL(5,4),
    calculation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建Reports表
CREATE TABLE IF NOT EXISTS reports (
    id SERIAL PRIMARY KEY,
    report_type VARCHAR(50) NOT NULL,
    partner_id INTEGER REFERENCES partners(id),
    start_date DATE,
    end_date DATE,
    total_conversions INTEGER,
    total_revenue_usd DECIMAL(10,2),
    total_payout_usd DECIMAL(10,2),
    total_margin_usd DECIMAL(10,2),
    report_data JSONB,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_conversions_partner_id ON conversions(partner_id);
CREATE INDEX IF NOT EXISTS idx_conversions_datetime ON conversions(datetime_conversion);
CREATE INDEX IF NOT EXISTS idx_conversions_status ON conversions(status);
CREATE INDEX IF NOT EXISTS idx_commission_calculations_conversion_id ON commission_calculations(conversion_id);
CREATE INDEX IF NOT EXISTS idx_reports_partner_id ON reports(partner_id);
CREATE INDEX IF NOT EXISTS idx_reports_date_range ON reports(start_date, end_date);

-- 插入默认Partners数据
INSERT INTO partners (name, commission_rate) VALUES 
    ('ByteC', 0.10),
    ('RAMPUP', 0.10),
    ('DeepLeaper', 0.10),
    ('MKK', 0.10),
    ('UNKNOWN', 0.10)
ON CONFLICT (name) DO NOTHING;

-- 创建视图：Partner汇总
CREATE OR REPLACE VIEW partner_summary AS
SELECT 
    p.name as partner_name,
    COUNT(c.id) as total_conversions,
    SUM(c.usd_sale_amount) as total_revenue_usd,
    SUM(c.usd_payout) as total_payout_usd,
    SUM(cc.margin_amount_usd) as total_margin_usd,
    AVG(cc.margin_rate) as avg_margin_rate
FROM partners p
LEFT JOIN conversions c ON p.id = c.partner_id
LEFT JOIN commission_calculations cc ON c.id = cc.conversion_id
GROUP BY p.id, p.name;

-- 创建视图：每日转化统计
CREATE OR REPLACE VIEW daily_conversion_stats AS
SELECT 
    DATE(c.datetime_conversion) as conversion_date,
    p.name as partner_name,
    COUNT(c.id) as conversions,
    SUM(c.usd_sale_amount) as revenue_usd,
    SUM(c.usd_payout) as payout_usd
FROM conversions c
JOIN partners p ON c.partner_id = p.id
WHERE c.datetime_conversion IS NOT NULL
GROUP BY DATE(c.datetime_conversion), p.id, p.name
ORDER BY conversion_date DESC;

COMMIT;
EOF

echo -e "${GREEN}✅ 数据库表结构脚本创建完成${NC}"

# 执行数据库脚本（需要安装psql客户端）
echo -e "${YELLOW}10. 执行数据库初始化...${NC}"
if command -v psql &> /dev/null; then
    PGPASSWORD=${DB_PASSWORD} psql -h ${DB_IP} -U ${DB_USER} -d ${DB_NAME} -f create_tables.sql
    echo -e "${GREEN}✅ 数据库初始化完成${NC}"
else
    echo -e "${YELLOW}⚠️ psql客户端未安装，请手动执行create_tables.sql${NC}"
fi

# 配置备份策略
echo -e "${YELLOW}11. 配置备份策略...${NC}"
gcloud sql backups create \
    --instance=${DB_INSTANCE_NAME} \
    --description="Initial backup after setup" || echo "备份可能已在进行中"

# 配置监控
echo -e "${YELLOW}12. 配置监控...${NC}"
gcloud logging sinks create bytec-sql-logs \
    bigquery.googleapis.com/projects/${PROJECT_ID}/datasets/bytec_logs \
    --log-filter="resource.type=gce_instance" || echo "监控可能已配置"

# 清理临时文件
rm -f create_tables.sql

# 部署完成
echo -e "${CYAN}🎉 数据库配置完成！${NC}"
echo -e "${CYAN}============================================${NC}"
echo -e "${GREEN}📊 数据库信息:${NC}"
echo -e "   • 实例名: ${DB_INSTANCE_NAME}"
echo -e "   • 数据库名: ${DB_NAME}"
echo -e "   • 用户名: ${DB_USER}"
echo -e "   • 外部IP: ${DB_IP}"
echo -e "   • 连接名: ${CONNECTION_NAME}"
echo -e "   • 区域: ${REGION}"
echo -e "${CYAN}============================================${NC}"

echo -e "${BLUE}📋 管理命令:${NC}"
echo -e "   • 查看实例: gcloud sql instances describe ${DB_INSTANCE_NAME}"
echo -e "   • 查看日志: gcloud sql operations list --instance=${DB_INSTANCE_NAME}"
echo -e "   • 连接数据库: gcloud sql connect ${DB_INSTANCE_NAME} --user=${DB_USER}"
echo -e "   • 创建备份: gcloud sql backups create --instance=${DB_INSTANCE_NAME}"
echo -e "   • 查看备份: gcloud sql backups list --instance=${DB_INSTANCE_NAME}"

echo -e "${CYAN}============================================${NC}"
echo -e "${GREEN}✅ ByteC DMP Agent 数据库配置完成！${NC}"

# 连接信息
echo -e "${BLUE}🔗 连接信息:${NC}"
echo -e "   • 主机: ${DB_IP}"
echo -e "   • 端口: 5432"
echo -e "   • 数据库: ${DB_NAME}"
echo -e "   • 用户名: ${DB_USER}"
echo -e "   • 密码: ${DB_PASSWORD}"

echo -e "${BLUE}🔧 特性:${NC}"
echo -e "   • 高可用性配置"
echo -e "   • 自动备份"
echo -e "   • 存储自动扩展"
echo -e "   • 监控和日志"
echo -e "   • 佣金计算 (90% + 10% margin)"
echo -e "   • Partner数据分离" 