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
