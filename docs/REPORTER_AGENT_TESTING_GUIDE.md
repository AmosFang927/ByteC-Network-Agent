# Reporter-Agent 测试指南

## 📋 概述

本指南介绍了为 Reporter-Agent 创建的完整测试系统，包括CLI工具、整合测试、Dashboard手动触发功能和Cloud Scheduler设置。

## 🛠️ 测试工具概览

### 1. CLI 测试工具
**文件**: `scripts/test_reporter_agent_cli.py`  
**功能**: 命令行测试工具，支持完整的Reporter-Agent功能测试

#### 支持的参数
- `--partner`: Partner名称 (ByteC, DeepLeaper, RAMPUP, all)
- `--date-range`: 日期范围 ("2 days ago", "1 week ago", "2025-01-20,2025-01-21")
- `--self-email`: 发送报告到自己的邮箱 (AmosFang927@gmail.com)
- `--format`: 输出格式 (json, excel, feishu, email, all)
- `--dry-run`: 测试模式，不实际发送/上传
- `--verbose`: 详细输出

#### 使用示例
```bash
# 基本测试
python scripts/test_reporter_agent_cli.py --partner ByteC --date-range "2 days ago" --self-email

# 测试特定Partner和日期范围
python scripts/test_reporter_agent_cli.py --partner DeepLeaper --date-range "2025-01-20,2025-01-21"

# 测试所有Partner
python scripts/test_reporter_agent_cli.py --partner all --date-range "1 week ago"

# 干运行模式
python scripts/test_reporter_agent_cli.py --partner RAMPUP --dry-run --verbose
```

### 2. 整合测试
**文件**: `agents/reporter_agent/integration_test.py`  
**功能**: 完整的Reporter-Agent功能整合测试

#### 测试覆盖范围
- 单个Partner报告生成
- 所有Partner报告生成
- 佣金计算功能
- 输出格式功能（JSON、Excel、飞书、邮件）
- 定时报告功能

#### 运行测试
```bash
python agents/reporter_agent/integration_test.py
```

### 3. Dashboard 手动触发
**文件**: `agents/dashboard_agent/manual_trigger.py`  
**功能**: 为ByteC-Performance-Dashboard提供手动触发API

#### API 端点
- `POST /manual-trigger`: 手动触发报告生成
- `GET /task-status/{task_id}`: 查看任务状态
- `GET /available-partners`: 获取可用Partner列表
- `GET /active-tasks`: 获取活动任务列表
- `POST /quick-trigger`: 快速触发（预设参数）

#### 使用示例
```python
# 手动触发示例
request_data = {
    "partner_name": "ByteC",
    "start_date": "2025-01-22",
    "end_date": "2025-01-22",
    "output_formats": ["excel", "feishu", "email"],
    "send_self_email": True,
    "dry_run": False
}

# 发送POST请求到 /api/manual-trigger
```

### 4. Cloud Scheduler 设置
**文件**: `deployment/gcp/setup_reporter_scheduler.sh`  
**功能**: 自动设置Google Cloud Scheduler定时任务

#### 配置参数
- **任务名称**: Reporter-Agent-8am-All
- **执行时间**: 每日上午8点
- **时区**: GMT+8 (Asia/Singapore)
- **区域**: asia-southeast1
- **参数**: 所有Partner, 2天前数据

#### 使用方法
```bash
# 设置定时任务
./deployment/gcp/setup_reporter_scheduler.sh

# 监控任务状态
./monitor_scheduler.sh

# 管理任务
./manage_scheduler.sh [status|start|stop|run|logs|delete]
```

## 🔧 数据流程测试

### 完整数据流程
1. **Data-DMP-Agent**: 获取转化数据
2. **Commission Calculator**: 计算佣金（90% + 10% margin）
3. **Data-Output-Agent**: 处理输出
   - JSON 文件生成
   - Excel 文件生成
   - 飞书上传
   - 邮件发送

### 测试数据
系统使用模拟数据进行测试，包括：
- 不同Partner的转化记录
- 多种Offer类型
- 不同的销售金额
- 佣金计算结果

## 📊 测试场景

### 1. 单Partner测试
```bash
# 测试ByteC Partner
python scripts/test_reporter_agent_cli.py --partner ByteC --self-email

# 测试DeepLeaper Partner
python scripts/test_reporter_agent_cli.py --partner DeepLeaper --self-email

# 测试RAMPUP Partner
python scripts/test_reporter_agent_cli.py --partner RAMPUP --self-email
```

### 2. 多Partner测试
```bash
# 测试所有Partner
python scripts/test_reporter_agent_cli.py --partner all --dry-run
```

### 3. 日期范围测试
```bash
# 相对日期测试
python scripts/test_reporter_agent_cli.py --partner ByteC --date-range "2 days ago"
python scripts/test_reporter_agent_cli.py --partner ByteC --date-range "1 week ago"

# 绝对日期测试
python scripts/test_reporter_agent_cli.py --partner ByteC --date-range "2025-01-20,2025-01-21"
```

### 4. 输出格式测试
```bash
# 测试单个格式
python scripts/test_reporter_agent_cli.py --partner ByteC --format json
python scripts/test_reporter_agent_cli.py --partner ByteC --format excel

# 测试所有格式
python scripts/test_reporter_agent_cli.py --partner ByteC --format all
```

## 📧 邮件配置

### 自发邮件功能
- 使用 `--self-email` 参数
- 邮件发送到: `AmosFang927@gmail.com`
- 包含Excel附件
- HTML格式的邮件内容

### Partner默认邮件
- 根据config.py中的Partner配置
- 自动选择对应的收件人列表
- 支持多个收件人

## 🚀 Cloud Scheduler 集成

### 定时任务配置
- **Cron表达式**: `0 8 * * *` (每日8点)
- **时区**: Asia/Singapore (GMT+8)
- **服务账户**: reporter-agent-scheduler@solar-idea-463423-h8.iam.gserviceaccount.com
- **目标URL**: https://api.bytec.com/api/reporter/scheduled-report

### 监控和管理
```bash
# 查看任务状态
./manage_scheduler.sh status

# 手动触发任务
./manage_scheduler.sh run

# 查看执行日志
./manage_scheduler.sh logs

# 暂停/恢复任务
./manage_scheduler.sh stop
./manage_scheduler.sh start
```

## 🔍 故障排查

### 常见问题
1. **模块导入错误**: 确保项目根目录在Python路径中
2. **API连接错误**: 检查网络连接和API配置
3. **邮件发送失败**: 检查SMTP配置和邮件权限
4. **飞书上传失败**: 检查飞书API配置

### 调试技巧
- 使用 `--verbose` 参数获取详细日志
- 使用 `--dry-run` 参数进行安全测试
- 检查output目录下的生成文件
- 查看Cloud Scheduler执行日志

## 📈 性能监控

### 执行时间估算
- 单个Partner: 约30秒
- 所有Partner: 约2-5分钟
- 影响因素: 数据量、输出格式、网络速度

### 资源使用
- CPU: 中等使用率
- 内存: 适中（处理DataFrame时会增加）
- 网络: 上传文件时较高

## 📝 测试报告

### 测试完成标准
- ✅ 所有输出格式正常生成
- ✅ 邮件发送成功
- ✅ 飞书上传成功
- ✅ 佣金计算正确
- ✅ 数据完整性验证通过

### 测试记录
运行完整测试后，系统会生成包含以下信息的测试报告：
- 测试成功率
- 各个功能模块的测试结果
- 错误日志（如有）
- 性能统计信息

## 🎯 下一步计划

1. **真实数据集成**: 替换模拟数据为真实的Data-DMP-Agent数据
2. **性能优化**: 优化大数据量处理性能
3. **监控告警**: 添加失败时的告警机制
4. **UI界面**: 完善Dashboard的用户界面
5. **自动化测试**: 集成到CI/CD流程中

---

**维护者**: Amos Fang  
**最后更新**: 2025-01-24  
**版本**: 1.0.0 