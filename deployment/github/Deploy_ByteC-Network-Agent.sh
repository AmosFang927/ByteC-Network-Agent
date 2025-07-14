#!/bin/bash

# =============================================
# ByteC Network Agent - GitHub部署脚本
# 代码推送和版本管理
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
GITHUB_REPO="ByteC-Network-Agent"
GITHUB_USER="amosfang"
MAIN_BRANCH="main"
DEVELOPMENT_BRANCH="development"

# 生成时间戳
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
VERSION=$(date +%Y.%m.%d)

# 显示部署信息
echo -e "${CYAN}🚀 ByteC Network Agent - GitHub部署${NC}"
echo -e "${CYAN}============================================${NC}"
echo -e "${BLUE}📋 项目信息:${NC}"
echo -e "   • GitHub仓库: ${GITHUB_USER}/${GITHUB_REPO}"
echo -e "   • 主分支: ${MAIN_BRANCH}"
echo -e "   • 开发分支: ${DEVELOPMENT_BRANCH}"
echo -e "   • 版本: ${VERSION}"
echo -e "   • 时间戳: ${TIMESTAMP}"
echo -e "${CYAN}============================================${NC}"

# 检查环境
echo -e "${YELLOW}1. 检查部署环境...${NC}"

# 检查必要工具
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Git 未安装${NC}"
    exit 1
fi

if ! command -v gh &> /dev/null; then
    echo -e "${YELLOW}⚠️ GitHub CLI 未安装，将使用标准git命令${NC}"
    USE_GH_CLI=false
else
    USE_GH_CLI=true
fi

echo -e "${GREEN}✅ 环境检查通过${NC}"

# 检查Git仓库状态
echo -e "${YELLOW}2. 检查Git仓库状态...${NC}"
if [ ! -d ".git" ]; then
    echo -e "${RED}❌ 当前目录不是Git仓库${NC}"
    exit 1
fi

# 检查是否有未提交的更改
if ! git diff --quiet; then
    echo -e "${YELLOW}⚠️ 发现未提交的更改${NC}"
    git status --short
    echo -e "${YELLOW}是否继续？(y/n)${NC}"
    read -r CONTINUE
    if [[ ! "$CONTINUE" =~ ^[Yy]$ ]]; then
        echo -e "${RED}❌ 部署已取消${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✅ Git仓库状态检查完成${NC}"

# 创建.gitignore文件
echo -e "${YELLOW}3. 更新.gitignore文件...${NC}"
cat > .gitignore << 'EOF'
# Python缓存
__pycache__/
*.py[cod]
*$py.class
*.so

# 分布式包
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# 虚拟环境
venv/
env/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# 日志文件
*.log
logs/

# 数据库文件
*.db
*.sqlite
*.sqlite3

# 缓存和临时文件
cache/
temp/
tmp/
.cache/
.tmp/

# 输出文件
output/
charts/

# 系统文件
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# 配置文件（包含敏感信息）
*.env
*.env.local
*.env.production
config.local.*

# 测试相关
.coverage
.pytest_cache/
.tox/
.coverage.*
htmlcov/
.nyc_output

# 文档构建
docs/_build/
site/

# 运行时文件
*.pid
*.seed
*.pid.lock

# 备份文件
*.backup
*.bak
*.orig

# 证书文件
*.pem
*.key
*.crt
*.p12
*.jks

# Docker相关
.dockerignore

# 特定项目文件
cloud-sql-proxy*
pandasai_deployment_info.txt
enhanced_dashboard_deployment_info.txt
rector_monitor_server.pid
last_rector_count.txt
EOF

echo -e "${GREEN}✅ .gitignore文件更新完成${NC}"

# 添加所有更改到暂存区
echo -e "${YELLOW}4. 添加文件到暂存区...${NC}"
git add .
echo -e "${GREEN}✅ 文件添加完成${NC}"

# 提交更改
echo -e "${YELLOW}5. 提交更改...${NC}"
COMMIT_MESSAGE="🚀 重构: 模块化架构升级 v${VERSION}

✨ 新增功能:
- 模块化架构：8个独立Agent模块
- 统一部署脚本：GitHub + GCP自动化
- 数据源集成：多源数据统一处理
- 佣金计算：90% + 10% margin自动计算
- 前后端分离：Dashboard Agent重构

📁 新架构:
- agents/: 8个Agent模块
- shared/: 共享模块和工具
- deployment/: 部署脚本
- docs/: 项目文档

🔧 优化:
- 精简50%+冗余代码
- 统一导入路径
- 改进错误处理
- 增强日志记录

🗃️ 清理:
- 移除测试文件
- 清理临时文件
- 删除重复代码
- 优化目录结构

Time: ${TIMESTAMP}"

git commit -m "${COMMIT_MESSAGE}"
echo -e "${GREEN}✅ 提交完成${NC}"

# 创建标签
echo -e "${YELLOW}6. 创建版本标签...${NC}"
git tag -a "v${VERSION}" -m "Release v${VERSION} - 模块化架构升级"
echo -e "${GREEN}✅ 版本标签创建完成${NC}"

# 推送到远程仓库
echo -e "${YELLOW}7. 推送到远程仓库...${NC}"
git push origin ${MAIN_BRANCH}
git push origin "v${VERSION}"
echo -e "${GREEN}✅ 推送完成${NC}"

# 创建GitHub Release（如果安装了GitHub CLI）
if [ "$USE_GH_CLI" = true ]; then
    echo -e "${YELLOW}8. 创建GitHub Release...${NC}"
    gh release create "v${VERSION}" \
        --title "ByteC Network Agent v${VERSION}" \
        --notes "## 🚀 重构: 模块化架构升级

### ✨ 新增功能
- **模块化架构**: 8个独立Agent模块
- **统一部署**: GitHub + GCP自动化部署
- **数据源集成**: 多源数据统一处理
- **佣金计算**: 90% + 10% margin自动计算
- **前后端分离**: Dashboard Agent重构

### 📁 新架构
- \`agents/\`: 8个Agent模块
- \`shared/\`: 共享模块和工具
- \`deployment/\`: 部署脚本
- \`docs/\`: 项目文档

### 🔧 优化改进
- 精简50%+冗余代码
- 统一导入路径
- 改进错误处理
- 增强日志记录

### 🗃️ 清理工作
- 移除测试文件
- 清理临时文件
- 删除重复代码
- 优化目录结构

### 📋 部署说明
\`\`\`bash
# 主程序部署
./deployment/gcp/Deploy_ByteC-Network-Agent.sh

# 前端Dashboard部署
./deployment/gcp/Deploy_ByteC-Performance-Dashboard-Agent.sh

# 数据库配置
./deployment/gcp/ByteC-DMP-Agent.sh
\`\`\`

### 🔗 服务地址
- **主程序**: https://api.bytec.com
- **Dashboard**: https://dashboard.bytec.com
- **数据库**: asia-southeast1 (新加坡)

Time: ${TIMESTAMP}" \
        --latest
    echo -e "${GREEN}✅ GitHub Release创建完成${NC}"
else
    echo -e "${YELLOW}⚠️ GitHub CLI未安装，请手动创建Release${NC}"
fi

# 部署完成
echo -e "${CYAN}🎉 GitHub部署完成！${NC}"
echo -e "${CYAN}============================================${NC}"
echo -e "${GREEN}📊 部署信息:${NC}"
echo -e "   • 仓库: https://github.com/${GITHUB_USER}/${GITHUB_REPO}"
echo -e "   • 版本: v${VERSION}"
echo -e "   • 提交: $(git rev-parse --short HEAD)"
echo -e "   • 分支: ${MAIN_BRANCH}"
echo -e "   • 标签: v${VERSION}"
echo -e "${CYAN}============================================${NC}"

echo -e "${BLUE}📋 管理命令:${NC}"
echo -e "   • 查看提交: git log --oneline -10"
echo -e "   • 查看标签: git tag -l"
echo -e "   • 查看状态: git status"
echo -e "   • 查看分支: git branch -a"

echo -e "${CYAN}============================================${NC}"
echo -e "${GREEN}✅ ByteC Network Agent GitHub部署完成！${NC}"

# 下一步操作提示
echo -e "${BLUE}🔄 下一步操作:${NC}"
echo -e "   1. 执行GCP部署脚本"
echo -e "   2. 配置CI/CD Pipeline"
echo -e "   3. 设置监控和告警"
echo -e "   4. 更新文档" 