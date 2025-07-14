# Postback-Agent

ByteC Network Agent - Postback Data Processing System

## 📋 概述

Postback-Agent 是 ByteC Network Agent 系统的一个核心模块，专门负责处理来自各种联盟营销平台的转化回传数据。

## 🚀 运行方式

### 1. 直接运行模块
```bash
python -m agents.postback_agent.main
```

### 2. 使用运行脚本
```bash
python run_postback_agent.py
```

### 3. 直接运行主文件
```bash
cd agents/postback_agent
python main.py
```

## 📡 API 端点

### 健康检查
```bash
GET /health
```

### Involve Asia 端点
```bash
GET /involve/event?conversion_id=xxx&click_id=xxx&usd_payout=xxx
POST /involve/event
```

### 通用 Postback 端点
```bash
GET /postback/?conversion_id=xxx&aff_sub=xxx&usd_payout=xxx
```

### 统计信息
```bash
GET /stats
GET /records?limit=10
```

## 🔧 配置

### 环境变量
- `HOST`: 监听地址 (默认: 0.0.0.0)
- `PORT`: 监听端口 (默认: 8080)

### 日志配置
日志级别设置为 INFO，包含详细的请求处理信息。

## 📊 功能特性

- **多平台支持**: 支持 Involve Asia 等多个联盟营销平台
- **实时处理**: 毫秒级的转化数据处理
- **内存存储**: 临时存储转化记录供查询
- **健康检查**: 完整的健康检查和监控端点
- **统计功能**: 实时统计处理数据

## 🌐 部署

### 本地开发
```bash
# 启动服务
python -m agents.postback_agent.main

# 访问 API 文档
open http://localhost:8080/docs
```

### 生产环境
服务默认监听 0.0.0.0:8080，适合容器化部署。

## 📝 测试

### 测试转化数据
```bash
curl "http://localhost:8080/involve/event?conversion_id=test123&click_id=click123&usd_payout=10.5"
```

### 查看统计信息
```bash
curl "http://localhost:8080/stats"
```

## 🔗 相关文件

- `main.py`: 主应用文件
- `postback_receiver.py`: 旧版本的路由文件（已废弃）
- `../../run_postback_agent.py`: 运行脚本

## 📄 版本信息

- **版本**: 1.0.0
- **框架**: FastAPI
- **Python**: 3.8+ 