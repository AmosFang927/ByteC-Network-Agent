# Search Affiliate Orders API 部署指南

## 概述

本指南将帮助您部署和配置Search Affiliate Orders API。该API是TikTok Shop联盟营销系统的核心组件，提供了完整的联盟订单查询功能。

## 系统要求

### 硬件要求
- CPU: 1核心以上
- 内存: 512MB以上
- 存储: 100MB可用空间
- 网络: 稳定的互联网连接

### 软件要求
- Python 3.7+
- Node.js 14+
- pip (Python包管理器)
- npm (Node.js包管理器)

## 安装步骤

### 1. 环境准备

#### 检查Python版本
```bash
python3 --version
# 应该显示 3.7 或更高版本
```

#### 检查Node.js版本
```bash
node --version
# 应该显示 14 或更高版本
```

#### 检查npm版本
```bash
npm --version
# 应该显示 6 或更高版本
```

### 2. 项目设置

#### 克隆项目
```bash
git clone <repository-url>
cd ByteC-Network-Agent-main
```

#### 创建虚拟环境
```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
# Linux/Mac:
source venv/bin/activate
# Windows:
# venv\Scripts\activate
```

#### 安装Python依赖
```bash
pip install requests
```

### 3. 配置设置

#### 编辑配置文件
编辑 `agents/linkshare_agent/config.py` 文件：

```python
# TikTok Shop API 配置
APP_KEY = "your_app_key_here"
APP_SECRET = "your_app_secret_here"
REDIRECT_URL = "your_redirect_url_here"
AUTH_CODE = "your_auth_code_here"

# API 版本
APP_VERSION = "202501"

# 请求超时设置
REQUEST_TIMEOUT = 30
CONNECT_TIMEOUT = 10
```

#### 获取TikTok Shop API凭证

1. **访问TikTok Shop Partner Center**
   - 登录 [TikTok Shop Partner Center](https://partner.tiktokshop.com/)

2. **创建应用**
   - 在Partner Center中创建新应用
   - 获取 `APP_KEY` 和 `APP_SECRET`

3. **配置重定向URL**
   - 设置 `REDIRECT_URL` 为您的回调地址

4. **获取授权码**
   - 访问授权URL: `https://shop.tiktok.com/alliance/creator/auth?app_key={app_key}&state={state_id}`
   - 完成授权流程
   - 从回调中获取 `AUTH_CODE`

### 4. Node.js SDK设置

#### 进入Node.js SDK目录
```bash
cd agents/linkshare_agent/nodejs_sdk
```

#### 安装Node.js依赖
```bash
npm install
```

#### 构建SDK
```bash
npm run build
```

## 验证安装

### 1. 运行配置验证
```bash
cd agents/linkshare_agent
python -c "from config import validate_config; validate_config(); print('✅ 配置验证通过')"
```

### 2. 运行集成测试
```bash
python test_integration.py
```

### 3. 运行综合测试
```bash
python test_comprehensive.py
```

## 部署选项

### 选项1: 本地部署

#### 直接运行
```bash
# 激活虚拟环境
source venv/bin/activate

# 运行测试
python test_search_orders.py

# 使用API
python -c "
from search_affiliate_orders import search_affiliate_orders
result = search_affiliate_orders(page_size=10)
print(result)
"
```

#### 作为服务运行
创建服务文件 `search_orders_service.py`:

```python
#!/usr/bin/env python3
"""
Search Affiliate Orders API 服务
"""

import logging
from agents.linkshare_agent.search_affiliate_orders import SearchAffiliateOrdersAPI

def main():
    """主服务函数"""
    logging.basicConfig(level=logging.INFO)
    api = SearchAffiliateOrdersAPI()
    
    # 示例：搜索订单
    result = api.search_orders(page_size=20)
    print(f"搜索结果: {result}")

if __name__ == "__main__":
    main()
```

运行服务：
```bash
python search_orders_service.py
```

### 选项2: Docker部署

#### 创建Dockerfile
```dockerfile
FROM python:3.9-slim

# 安装Node.js
RUN apt-get update && apt-get install -y \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_16.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY . .

# 安装Python依赖
RUN pip install requests

# 安装Node.js依赖
WORKDIR /app/agents/linkshare_agent/nodejs_sdk
RUN npm install
RUN npm run build

# 返回主目录
WORKDIR /app

# 暴露端口（如果需要）
EXPOSE 8000

# 启动命令
CMD ["python", "agents/linkshare_agent/test_search_orders.py"]
```

#### 构建和运行Docker容器
```bash
# 构建镜像
docker build -t search-affiliate-orders-api .

# 运行容器
docker run -it search-affiliate-orders-api
```

### 选项3: 云部署

#### Google Cloud Run

1. **创建Dockerfile** (如上所示)

2. **创建cloudbuild.yaml**
```yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/search-affiliate-orders-api', '.']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/search-affiliate-orders-api']
  - name: 'gcr.io/cloud-builders/gcloud'
    args:
      - 'run'
      - 'deploy'
      - 'search-affiliate-orders-api'
      - '--image'
      - 'gcr.io/$PROJECT_ID/search-affiliate-orders-api'
      - '--region'
      - 'asia-southeast1'
      - '--platform'
      - 'managed'
```

3. **部署到Cloud Run**
```bash
gcloud builds submit --config cloudbuild.yaml
```

#### AWS Lambda

1. **创建requirements.txt**
```
requests==2.31.0
```

2. **创建lambda_function.py**
```python
import json
from agents.linkshare_agent.search_affiliate_orders import search_affiliate_orders

def lambda_handler(event, context):
    """AWS Lambda处理函数"""
    try:
        # 从事件中获取参数
        params = event.get('queryStringParameters', {}) or {}
        
        # 调用API
        result = search_affiliate_orders(
            page_size=int(params.get('page_size', 20)),
            campaign_id=params.get('campaign_id')
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps(result),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        }
```

## 监控和维护

### 日志监控

#### 设置日志轮转
```bash
# 创建日志目录
mkdir -p /var/log/search-affiliate-orders

# 配置logrotate
sudo tee /etc/logrotate.d/search-affiliate-orders << EOF
/var/log/search-affiliate-orders/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 www-data www-data
}
EOF
```

#### 监控脚本
创建 `monitor.py`:

```python
#!/usr/bin/env python3
"""
监控脚本
"""

import time
import logging
from agents.linkshare_agent.search_affiliate_orders import SearchAffiliateOrdersAPI

def monitor_api():
    """监控API状态"""
    api = SearchAffiliateOrdersAPI()
    
    while True:
        try:
            # 测试API连接
            result = api.get_category_assets()
            
            if result.get("success"):
                logging.info("✅ API运行正常")
            else:
                logging.error(f"❌ API错误: {result.get('error')}")
                
        except Exception as e:
            logging.error(f"❌ 监控错误: {e}")
        
        time.sleep(300)  # 每5分钟检查一次

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('/var/log/search-affiliate-orders/monitor.log'),
            logging.StreamHandler()
        ]
    )
    monitor_api()
```

### 性能监控

#### 创建性能测试脚本
```python
#!/usr/bin/env python3
"""
性能测试脚本
"""

import time
import statistics
from agents.linkshare_agent.search_affiliate_orders import search_affiliate_orders

def performance_test():
    """性能测试"""
    times = []
    
    for i in range(10):
        start_time = time.time()
        
        try:
            result = search_affiliate_orders(page_size=10)
            if result.get("success"):
                end_time = time.time()
                times.append(end_time - start_time)
                print(f"测试 {i+1}: {times[-1]:.2f}秒")
            else:
                print(f"测试 {i+1}: 失败 - {result.get('error')}")
        except Exception as e:
            print(f"测试 {i+1}: 异常 - {e}")
    
    if times:
        print(f"\n性能统计:")
        print(f"平均响应时间: {statistics.mean(times):.2f}秒")
        print(f"最小响应时间: {min(times):.2f}秒")
        print(f"最大响应时间: {max(times):.2f}秒")
        print(f"标准差: {statistics.stdev(times):.2f}秒")

if __name__ == "__main__":
    performance_test()
```

## 故障排除

### 常见问题

#### 1. 配置错误
```
❌ 配置验证失败: 缺少必要配置: APP_KEY
```
**解决方案**: 检查 `config.py` 中的所有必要配置项

#### 2. Token错误
```
❌ Token错误: 未找到有效 Token，请先使用 'get-token' 命令获取
```
**解决方案**: 
1. 检查 `AUTH_CODE` 是否有效
2. 重新获取Token

#### 3. Node.js错误
```
❌ Node.js脚本执行失败: module not found
```
**解决方案**:
1. 确保Node.js版本正确
2. 重新安装依赖: `npm install`
3. 重新构建SDK: `npm run build`

#### 4. 网络错误
```
❌ 网络错误: Connection timeout
```
**解决方案**:
1. 检查网络连接
2. 检查防火墙设置
3. 验证API端点可访问性

### 调试技巧

#### 启用调试日志
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### 检查Token状态
```python
from agents.linkshare_agent.token_manager import TokenManager
token_manager = TokenManager()
token_info = token_manager.get_token_info()
print(token_info)
```

#### 测试Node.js脚本
```bash
cd agents/linkshare_agent/nodejs_sdk
node test_sdk.js
```

## 安全考虑

### 1. 凭证管理
- 不要在代码中硬编码API凭证
- 使用环境变量或密钥管理服务
- 定期轮换API凭证

### 2. 网络安全
- 使用HTTPS进行API通信
- 实施适当的防火墙规则
- 监控异常访问模式

### 3. 日志安全
- 不要在日志中记录敏感信息
- 实施日志访问控制
- 定期审查日志文件

## 扩展和定制

### 添加新的错误处理
```python
# 在 search_affiliate_orders.py 中添加新的错误类型
class ErrorType(Enum):
    # ... 现有错误类型 ...
    CUSTOM_ERROR = "custom_error"

# 添加新的错误处理方法
def _handle_custom_error(self, error: Exception) -> Dict[str, Any]:
    """处理自定义错误"""
    logger.error(f"❌ 自定义错误: {error}")
    return {
        "success": False,
        "error": f"自定义错误: {str(error)}",
        "error_type": ErrorType.CUSTOM_ERROR.value
    }
```

### 添加新的测试
```python
# 在 test_comprehensive.py 中添加新测试
def test_custom_functionality():
    """测试自定义功能"""
    # 实现测试逻辑
    pass
```

## 支持和维护

### 获取帮助
1. 查看详细文档: `SEARCH_AFFILIATE_ORDERS_USAGE.md`
2. 运行测试套件诊断问题
3. 检查日志文件获取错误信息
4. 提交Issue描述问题

### 定期维护
1. 更新依赖包
2. 检查API版本兼容性
3. 监控性能指标
4. 备份配置和Token数据

---

**版本**: 1.0.0  
**最后更新**: 2025-01-27  
**维护者**: ByteC Network 