# Search Affiliate Orders API

## 概述

Search Affiliate Orders API 是TikTok Shop联盟营销系统的核心组件，提供了完整的联盟订单查询功能。该API支持分页查询、时间范围过滤、活动过滤等功能，并完全集成到现有的配置和token管理系统中。

## 功能特性

- ✅ **自动获取categoryAssetCipher**: 无需手动提供，API会自动获取
- ✅ **分页查询**: 支持pageSize和pageToken参数
- ✅ **时间范围过滤**: 支持createTimeGe和createTimeLt参数
- ✅ **活动过滤**: 支持campaignId参数
- ✅ **完整参数验证**: 自动验证所有输入参数
- ✅ **详细日志记录**: 完整的操作日志和错误信息
- ✅ **错误处理**: 完善的错误处理和异常捕获
- ✅ **配置集成**: 完全集成到现有配置系统
- ✅ **Token管理集成**: 自动使用现有token管理机制
- ✅ **统一错误码映射**: 使用统一的API错误码处理
- ✅ **错误类型分类**: 详细的错误类型枚举和处理
- ✅ **错误恢复机制**: 支持错误后的恢复和重试

## 快速开始

### 安装依赖

确保已安装以下依赖：
- Python 3.7+
- Node.js 14+
- 有效的TikTok Shop API凭证

### 基本使用

```python
from agents.linkshare_agent.search_affiliate_orders import search_affiliate_orders

# 基本搜索，使用默认参数
result = search_affiliate_orders(page_size=20)

if result.get("success"):
    orders = result.get("orders", [])
    total_count = result.get("totalCount", 0)
    print(f"找到 {total_count} 条订单，当前页 {len(orders)} 条")
else:
    print(f"搜索失败: {result.get('error')}")
```

### 带时间范围搜索

```python
import time

# 搜索最近7天的订单
current_time = int(time.time())
seven_days_ago = current_time - (7 * 24 * 60 * 60)

result = search_affiliate_orders(
    page_size=50,
    create_time_ge=seven_days_ago,
    create_time_lt=current_time
)
```

### 带活动过滤搜索

```python
result = search_affiliate_orders(
    page_size=20,
    campaign_id="your_campaign_id"
)
```

## API 文档

### 主要函数

#### `search_affiliate_orders()`

搜索联盟订单的主要函数。

**参数:**
- `page_size` (int, 可选): 分页大小，默认20，范围1-100
- `page_token` (str, 可选): 分页token，用于获取下一页
- `create_time_ge` (int, 可选): 创建时间起始（Unix timestamp）
- `create_time_lt` (int, 可选): 创建时间结束（Unix timestamp）
- `campaign_id` (str, 可选): 活动ID过滤
- `category_asset_cipher` (str, 可选): 合作伙伴标识符（自动获取）

**返回:**
```python
{
    "success": bool,           # 操作是否成功
    "orders": [               # 订单列表
        {
            "orderId": str,    # 订单ID
            "status": str,     # 订单状态
            "amount": float,   # 订单金额
            # ... 其他订单字段
        }
    ],
    "totalCount": int,        # 总订单数
    "nextPageToken": str,     # 下一页token
    "error": str,            # 错误信息（如果失败）
    "error_code": int,       # 错误码（如果失败）
    "error_type": str,       # 错误类型（如果失败）
    "httpStatus": int        # HTTP状态码
}
```

#### `get_category_assets()`

获取categoryAssetCipher的函数。

**返回:**
```python
{
    "success": bool,
    "availableCiphers": [
        {
            "categoryId": int,
            "categoryName": str,
            "targetMarket": str,
            "cipher": str
        }
    ],
    "defaultCipher": str
}
```

### 错误类型

API定义了详细的错误类型枚举：

```python
from agents.linkshare_agent.search_affiliate_orders import ErrorType

# 错误类型包括：
# VALIDATION_ERROR: 参数验证错误
# NETWORK_ERROR: 网络错误
# API_ERROR: API业务逻辑错误
# TOKEN_ERROR: Token相关错误
# TIMEOUT_ERROR: 请求超时错误
# JSON_ERROR: JSON解析错误
# UNKNOWN_ERROR: 未知错误
```

## 测试

### 运行所有测试

```bash
cd agents/linkshare_agent

# 运行功能测试
python test_search_orders.py

# 运行集成测试
python test_integration.py

# 运行错误处理测试
python test_error_handling.py

# 运行综合测试
python test_comprehensive.py
```

### 测试覆盖

1. **功能测试** (`test_search_orders.py`)
   - 获取Category Assets测试
   - 基本订单搜索测试
   - 带过滤条件的订单搜索测试
   - 参数验证测试

2. **集成测试** (`test_integration.py`)
   - 配置集成测试
   - Token管理器集成测试
   - API类集成测试
   - 错误处理集成测试
   - 日志集成测试
   - Node.js脚本集成测试
   - 端到端集成测试

3. **错误处理测试** (`test_error_handling.py`)
   - 参数验证错误测试
   - 错误类型枚举测试
   - 错误处理方法测试
   - API错误处理测试
   - Node.js脚本执行错误测试
   - 日志输出测试
   - 错误响应格式测试
   - 错误恢复测试

4. **综合测试** (`test_comprehensive.py`)
   - API初始化测试
   - 参数验证功能测试
   - 错误类型枚举测试
   - 错误处理方法测试
   - API错误处理测试
   - Node.js脚本执行测试
   - 时间戳格式化测试
   - 便捷函数测试
   - 错误恢复测试
   - 日志集成测试
   - 配置集成测试
   - Token管理器集成测试

## 配置

### 必需配置

确保以下配置在 `config.py` 中正确设置：

```python
APP_KEY = "your_app_key"
APP_SECRET = "your_app_secret"
REDIRECT_URL = "your_redirect_url"
AUTH_CODE = "your_auth_code"
REQUEST_TIMEOUT = 30
```

### 环境要求

- Python 3.7+
- Node.js 14+
- 有效的TikTok Shop API凭证
- 网络连接到TikTok Shop API

## 错误处理

### 错误处理示例

```python
try:
    result = search_affiliate_orders(page_size=20)
    
    if result.get("success"):
        # 处理成功结果
        orders = result.get("orders", [])
        print(f"找到 {len(orders)} 条订单")
    else:
        # 处理错误
        error_msg = result.get("error", "未知错误")
        error_code = result.get("error_code", -1)
        error_type = result.get("error_type", "unknown_error")
        
        print(f"搜索失败: {error_msg}")
        print(f"错误码: {error_code}")
        print(f"错误类型: {error_type}")
        
        # 根据错误类型进行不同处理
        if error_type == "token_error":
            print("需要重新获取Token")
        elif error_type == "validation_error":
            print("请检查输入参数")
        elif error_type == "network_error":
            print("请检查网络连接")
        
except Exception as e:
    print(f"发生异常: {e}")
```

### 错误恢复机制

```python
def search_with_retry(max_retries=3, **kwargs):
    """带重试的搜索函数"""
    for attempt in range(max_retries):
        try:
            result = search_affiliate_orders(**kwargs)
            
            if result.get("success"):
                return result
            
            # 根据错误类型决定是否重试
            error_type = result.get("error_type")
            if error_type in ["network_error", "timeout_error"]:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数退避
                    continue
            
            return result
            
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise
    
    return {"success": False, "error": "重试次数已用完", "error_type": "unknown_error"}
```

## 日志记录

### 日志级别

API提供不同级别的日志记录：

- `DEBUG`: 详细的调试信息，包括参数、请求体等
- `INFO`: 主要操作信息，如开始搜索、获取Token等
- `WARNING`: 警告信息，如参数验证失败等
- `ERROR`: 错误信息，包括各种错误详情

### 日志配置

```python
import logging

# 设置日志级别
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
```

## 性能优化

### 建议

1. **合理设置page_size**: 建议使用20-50之间的值
2. **使用时间范围过滤**: 减少不必要的数据传输
3. **缓存categoryAssetCipher**: 避免重复获取
4. **错误重试**: 对于网络错误，可以实现重试机制
5. **Token缓存**: 利用现有的token缓存机制
6. **日志级别**: 生产环境使用INFO级别，开发环境使用DEBUG级别

## 文件结构

```
agents/linkshare_agent/
├── search_affiliate_orders.py          # 主API文件
├── get_category_assets.js              # 获取category assets的Node.js脚本
├── search_affiliate_orders.js          # 搜索订单的Node.js脚本
├── test_search_orders.py               # 功能测试
├── test_integration.py                 # 集成测试
├── test_error_handling.py              # 错误处理测试
├── test_comprehensive.py               # 综合测试
├── SEARCH_AFFILIATE_ORDERS_USAGE.md    # 详细使用文档
└── README.md                           # 本文件
```

## 更新日志

### v1.0.0 (初始版本)
- 支持基本订单搜索功能
- 支持分页查询、时间过滤、活动过滤
- 自动获取categoryAssetCipher
- 完整的参数验证和错误处理

### v1.1.0 (集成版本)
- 完全集成到现有配置和token管理系统
- 统一的错误码映射
- 完整的集成测试套件
- 详细的集成文档

### v1.2.0 (错误处理增强版本)
- 详细的错误类型分类
- 完善的错误恢复机制
- 统一的日志格式和级别
- 完整的错误处理测试套件

## 贡献

欢迎提交Issue和Pull Request来改进这个API。

## 许可证

本项目遵循MIT许可证。

## 支持

如果您遇到问题或有任何疑问，请：

1. 查看详细的使用文档：`SEARCH_AFFILIATE_ORDERS_USAGE.md`
2. 运行测试套件来诊断问题
3. 检查日志输出来获取详细信息
4. 提交Issue描述问题

## 相关链接

- [TikTok Shop API 文档](https://partner.tiktokshop.com/docv2/)
- [项目主页](https://github.com/your-repo/bytec-network-agent)
- [详细使用文档](SEARCH_AFFILIATE_ORDERS_USAGE.md) 