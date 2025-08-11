# Search Affiliate Orders API 使用文档

## 概述

Search Affiliate Orders API 提供了查询TikTok Shop联盟订单数据的功能。该API支持分页查询、时间范围过滤、活动过滤等功能，并完全集成到现有的配置和token管理系统中。

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

## 系统集成

### 配置集成

API完全集成到现有的`config.py`配置系统中：

- 使用统一的APP_KEY、APP_SECRET配置
- 使用统一的REQUEST_TIMEOUT配置
- 使用统一的API_ERROR_CODES错误码映射
- 使用统一的日志配置

### Token管理集成

API自动使用现有的TokenManager：

- 自动获取有效的access token
- 自动处理token过期和刷新
- 使用现有的token存储机制
- 支持token缓存和验证

### 日志集成

API使用统一的日志系统：

- 使用统一的日志格式
- 支持不同的日志级别
- 集成到现有的日志配置中

## 快速开始

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

### 数据可视化输出

```python
from agents.linkshare_agent.data_visualizer import export_orders_to_csv, create_orders_report
from agents.linkshare_agent.excel_visualizer import export_orders_to_excel

# 导出到CSV
csv_file = export_orders_to_csv(result, "output")

# 导出到Excel（需要安装pandas和openpyxl）
try:
    excel_file = export_orders_to_excel(result, "output")
    print(f"Excel文件: {excel_file}")
except ImportError:
    print("请安装Excel依赖: pip install pandas openpyxl")

# 多格式导出
output_files = create_orders_report(result, "output", ['csv', 'json'])
print(f"输出文件: {output_files}")
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

### 分页查询

```python
# 第一页
result1 = search_affiliate_orders(page_size=10)

if result1.get("success"):
    next_page_token = result1.get("nextPageToken")
    
    # 第二页
    if next_page_token:
        result2 = search_affiliate_orders(
            page_size=10,
            page_token=next_page_token
        )
```

## API 参数说明

### search_affiliate_orders() 参数

| 参数名 | 类型 | 必需 | 默认值 | 说明 |
|--------|------|------|--------|------|
| page_size | int | 否 | 20 | 分页大小，范围1-100 |
| page_token | str | 否 | None | 分页token，用于获取下一页 |
| create_time_ge | int | 否 | None | 创建时间起始（Unix timestamp） |
| create_time_lt | int | 否 | None | 创建时间结束（Unix timestamp） |
| campaign_id | str | 否 | None | 活动ID过滤 |
| category_asset_cipher | str | 否 | None | 合作伙伴标识符（自动获取） |

### 返回结果格式

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

## 高级使用

### 获取Category Assets

```python
from agents.linkshare_agent.search_affiliate_orders import get_category_assets

# 获取所有可用的category assets
result = get_category_assets()

if result.get("success"):
    available_ciphers = result.get("availableCiphers", [])
    for cipher_info in available_ciphers:
        print(f"Category: {cipher_info['categoryName']}")
        print(f"Target Market: {cipher_info['targetMarket']}")
        print(f"Cipher: {cipher_info['cipher']}")
```

### 使用API类

```python
from agents.linkshare_agent.search_affiliate_orders import SearchAffiliateOrdersAPI

# 创建API实例
api = SearchAffiliateOrdersAPI()

# 获取category assets
category_result = api.get_category_assets()

# 搜索订单
orders_result = api.search_orders(
    page_size=20,
    create_time_ge=1640995200,  # 2022-01-01
    create_time_lt=1641081600    # 2022-01-02
)
```

## 错误处理

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

### 常见错误类型

1. **参数验证错误**
   ```python
   # page_size超出范围
   result = search_affiliate_orders(page_size=0)  # 错误
   # 返回: {"success": False, "error": "参数验证错误: page_size必须在1-100范围内", "error_type": "validation_error"}
   ```

2. **时间范围错误**
   ```python
   # 开始时间大于结束时间
   result = search_affiliate_orders(
       create_time_ge=1641081600,  # 2022-01-02
       create_time_lt=1640995200    # 2022-01-01
   )  # 错误
   ```

3. **API错误码**
   ```python
   # 使用统一的错误码映射
   # 40001: 参数错误
   # 40003: 签名错误
   # 50000: 内部服务错误
   # 98001004: 参数无效 (可能是 auth_code 过期)
   ```

4. **Token错误**
   ```python
   # Token过期或无效
   # 返回: {"success": False, "error": "Token错误: ...", "error_type": "token_error"}
   ```

5. **网络错误**
   ```python
   # 网络连接失败
   # 返回: {"success": False, "error": "网络错误: ...", "error_type": "network_error"}
   ```

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

### 日志格式

使用统一的日志格式：
```
%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

### 日志示例

```python
# 设置日志级别
import logging
logging.basicConfig(level=logging.INFO)

# 执行搜索
result = search_affiliate_orders(page_size=20)

# 日志输出示例：
# 2024-01-01 10:00:00,123 - agents.linkshare_agent.search_affiliate_orders - INFO - 🔍 开始搜索联盟订单...
# 2024-01-01 10:00:00,124 - agents.linkshare_agent.search_affiliate_orders - INFO - 📋 搜索参数:
# 2024-01-01 10:00:00,125 - agents.linkshare_agent.search_affiliate_orders - INFO -    分页大小: 20
# 2024-01-01 10:00:00,126 - agents.linkshare_agent.search_affiliate_orders - INFO - 🔑 获取到access token: abc123...
# 2024-01-01 10:00:00,127 - agents.linkshare_agent.search_affiliate_orders - INFO - 📡 执行Node.js脚本: search_affiliate_orders.js
# 2024-01-01 10:00:01,234 - agents.linkshare_agent.search_affiliate_orders - INFO - ✅ 订单搜索成功
# 2024-01-01 10:00:01,235 - agents.linkshare_agent.search_affiliate_orders - INFO - 📊 搜索结果: 总数 100, 当前页 20 条订单
```

### 错误日志示例

```python
# 错误情况下的日志输出：
# 2024-01-01 10:00:00,123 - agents.linkshare_agent.search_affiliate_orders - ERROR - ❌ 参数验证错误: page_size必须在1-100范围内
# 2024-01-01 10:00:00,124 - agents.linkshare_agent.search_affiliate_orders - ERROR - ❌ API错误 40001: 参数错误
# 2024-01-01 10:00:00,125 - agents.linkshare_agent.search_affiliate_orders - ERROR - ❌ 请求超时: ...
```

## 测试

### 运行功能测试

```bash
cd agents/linkshare_agent
python test_search_orders.py
```

### 运行集成测试

```bash
cd agents/linkshare_agent
python test_integration.py
```

### 运行错误处理测试

```bash
cd agents/linkshare_agent
python test_error_handling.py
```

### 测试内容

1. **功能测试**
   - 获取Category Assets测试
   - 基本订单搜索测试
   - 带过滤条件的订单搜索测试
   - 参数验证测试

2. **集成测试**
   - 配置集成测试
   - Token管理器集成测试
   - API类集成测试
   - 错误处理集成测试
   - 日志集成测试
   - Node.js脚本集成测试
   - 端到端集成测试

3. **错误处理测试**
   - 参数验证错误测试
   - 错误类型枚举测试
   - 错误处理方法测试
   - API错误处理测试
   - Node.js脚本执行错误测试
   - 日志输出测试
   - 错误响应格式测试
   - 错误恢复测试

## 配置要求

### 必需配置

确保以下配置在 `config.py` 中正确设置：

- `APP_KEY`: TikTok Shop应用密钥
- `APP_SECRET`: TikTok Shop应用密钥
- `REDIRECT_URL`: 重定向URL
- `AUTH_CODE`: 授权码
- `REQUEST_TIMEOUT`: 请求超时时间（秒）

### Token管理

API会自动使用现有的token管理机制：

- 自动获取有效的access token
- 自动处理token过期和刷新
- 使用现有的token存储机制
- 支持token缓存和验证

### 环境要求

- Python 3.7+
- Node.js 14+
- 有效的TikTok Shop API凭证
- 网络连接到TikTok Shop API

## 性能优化

### 建议

1. **合理设置page_size**: 建议使用20-50之间的值
2. **使用时间范围过滤**: 减少不必要的数据传输
3. **缓存categoryAssetCipher**: 避免重复获取
4. **错误重试**: 对于网络错误，可以实现重试机制
5. **Token缓存**: 利用现有的token缓存机制
6. **日志级别**: 生产环境使用INFO级别，开发环境使用DEBUG级别

### 示例：带重试的搜索

```python
import time

def search_orders_with_retry(max_retries=3, **kwargs):
    for attempt in range(max_retries):
        try:
            result = search_affiliate_orders(**kwargs)
            if result.get("success"):
                return result
            elif result.get("error_type") in ["network_error", "timeout_error"]:
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

## 集成检查

### 运行集成检查

```python
from agents.linkshare_agent.test_integration import main as run_integration_tests

# 运行所有集成测试
success = run_integration_tests()
if success:
    print("✅ 所有集成测试通过")
else:
    print("❌ 部分集成测试失败")
```

### 检查项目

1. **配置验证**: 检查所有必要配置项
2. **Token管理**: 验证token管理器功能
3. **API类**: 测试API类创建和参数验证
4. **错误处理**: 验证错误处理机制
5. **日志系统**: 检查日志配置和输出
6. **Node.js脚本**: 验证脚本文件存在
7. **端到端**: 测试完整的功能流程

## 注意事项

1. **API限制**: 注意TikTok Shop API的调用频率限制
2. **数据量**: 大量数据查询时注意内存使用
3. **时间格式**: 时间戳使用Unix timestamp格式
4. **错误处理**: 始终检查返回结果的success字段
5. **日志级别**: 生产环境建议使用INFO级别
6. **配置验证**: 确保所有必要配置项都已正确设置
7. **Token管理**: 确保token已正确初始化和管理
8. **网络连接**: 确保能够访问TikTok Shop API
9. **错误类型**: 根据error_type字段进行不同的错误处理
10. **日志记录**: 合理设置日志级别，避免过多调试信息

## 数据可视化

### 概述

Search Affiliate Orders API 提供了完整的数据可视化功能，支持将API响应数据转换为CSV、JSON和Excel格式，方便数据分析和报表生成。

### 支持格式

1. **CSV格式**: 适合数据导入和分析
2. **JSON格式**: 保留完整的数据结构
3. **Excel格式**: 包含多个工作表，支持图表和格式化

### 基本使用

```python
from agents.linkshare_agent.data_visualizer import export_orders_to_csv, create_orders_report
from agents.linkshare_agent.excel_visualizer import export_orders_to_excel

# 获取订单数据
result = search_affiliate_orders(page_size=20)

if result.get("success"):
    # 导出到CSV
    csv_file = export_orders_to_csv(result, "output")
    print(f"CSV文件: {csv_file}")
    
    # 导出到Excel（需要安装pandas和openpyxl）
    try:
        excel_file = export_orders_to_excel(result, "output")
        print(f"Excel文件: {excel_file}")
    except ImportError:
        print("请安装Excel依赖: pip install pandas openpyxl")
    
    # 多格式导出
    output_files = create_orders_report(result, "output", ['csv', 'json'])
    print(f"输出文件: {output_files}")
```

### CSV输出格式

CSV文件包含以下字段：

| 字段名 | 描述 | 示例 |
|--------|------|------|
| 订单ID | 订单唯一标识 | ORDER_001 |
| 订单状态 | 订单当前状态 | COMPLETED |
| 创建时间 | 订单创建时间 | 2025-01-27 10:30:00 |
| 更新时间 | 订单最后更新时间 | 2025-01-27 11:45:00 |
| 订单金额 | 订单总金额 | 100.50 |
| 佣金金额 | 佣金金额 | 10.05 |
| 佣金率 | 佣金比例 | 10.00% |
| 产品ID | 产品唯一标识 | PROD_001 |
| 产品名称 | 产品名称 | 测试产品 |
| 产品价格 | 产品单价 | 50.25 |
| 产品数量 | 购买数量 | 2 |
| 活动ID | 活动唯一标识 | CAMP_001 |
| 活动名称 | 活动名称 | 测试活动 |
| 用户ID | 用户唯一标识 | USER_001 |
| 用户名 | 用户名称 | 测试用户 |
| 订单来源 | 订单来源平台 | TIKTOK_SHOP |
| 支付方式 | 支付方式 | CREDIT_CARD |
| 备注 | 订单备注 | 测试订单 |

### Excel输出格式

Excel文件包含三个工作表：

1. **订单详情**: 包含所有订单的详细数据
2. **数据汇总**: 包含统计信息和分布数据
3. **数据图表**: 包含图表数据，可用于生成图表

#### 数据汇总包含：

- **基础统计**: 总订单数、总金额、总佣金、平均佣金率
- **状态分布**: 各订单状态的数量统计
- **活动分布**: 各活动的订单数量统计
- **时间分布**: 按日期的订单数量统计

### 高级用法

#### 自定义输出目录

```python
# 指定自定义输出目录
csv_file = export_orders_to_csv(result, "custom_output_dir")
```

#### 批量处理

```python
# 处理多个时间范围的数据
time_ranges = [
    (1640995200, 1641081600),  # 2022-01-01 到 2022-01-02
    (1641081600, 1641168000),  # 2022-01-02 到 2022-01-03
]

for start_time, end_time in time_ranges:
    result = search_affiliate_orders(
        create_time_ge=start_time,
        create_time_lt=end_time
    )
    
    if result.get("success"):
        csv_file = export_orders_to_csv(result, f"output/range_{start_time}_{end_time}")
        print(f"导出完成: {csv_file}")
```

#### 数据过滤

```python
# 只导出特定状态的订单
if result.get("success"):
    orders = result.get("orders", [])
    completed_orders = [order for order in orders if order.get("status") == "COMPLETED"]
    
    # 创建过滤后的响应
    filtered_result = {
        "success": True,
        "orders": completed_orders,
        "totalCount": len(completed_orders)
    }
    
    csv_file = export_orders_to_csv(filtered_result, "output")
```

### 错误处理

```python
try:
    csv_file = export_orders_to_csv(result, "output")
    print(f"导出成功: {csv_file}")
except ValueError as e:
    print(f"导出失败: {e}")
except Exception as e:
    print(f"未知错误: {e}")
```

### 性能优化

1. **合理设置page_size**: 避免一次性处理过多数据
2. **使用时间范围**: 减少不必要的数据传输
3. **分批处理**: 大量数据时考虑分批导出
4. **文件管理**: 定期清理临时文件

### 测试数据可视化

```bash
# 运行数据可视化测试
python test_visualization.py
```

测试包括：
- CSV导出功能测试
- JSON导出功能测试
- Excel导出功能测试
- 便捷函数测试
- 多格式导出测试
- 错误处理测试
- 数据格式化测试
- 文件管理测试

## 更新日志

- **v1.0.0**: 初始版本，支持基本订单搜索功能
- 支持分页查询、时间过滤、活动过滤
- 自动获取categoryAssetCipher
- 完整的参数验证和错误处理
- **v1.1.0**: 完全集成到现有配置和token管理系统
- 统一的错误码映射
- 完整的集成测试套件
- 详细的集成文档
- **v1.2.0**: 增强错误处理和日志记录
- 详细的错误类型分类
- 完善的错误恢复机制
- 统一的日志格式和级别
- 完整的错误处理测试套件
- **v1.3.0**: 数据可视化功能
- 支持CSV、JSON、Excel格式导出
- 完整的数据格式化和汇总功能
- 多工作表Excel输出
- 完整的数据可视化测试套件 