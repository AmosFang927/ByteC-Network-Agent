#!/bin/bash

echo "🚀 开始安装 RAG 知识库系统..."

# 检查是否已安装 Ollama
if ! command -v ollama &> /dev/null; then
    echo "📦 安装 Ollama..."
    curl -fsSL https://ollama.ai/install.sh | sh
else
    echo "✅ Ollama 已安装"
fi

# 创建 Python 虚拟环境
echo "🐍 创建 Python 虚拟环境..."
python3 -m venv venv
source venv/bin/activate

# 安装 Python 依赖
echo "📚 安装 Python 依赖..."
pip install --upgrade pip
pip install -r requirements.txt

# 下载模型
echo "🤖 下载 deepseek 模型..."
ollama pull deepseek-coder:6.7b

echo "📥 下载 nomic-embed-text 模型..."
ollama pull nomic-embed-text

echo "✅ 安装完成！"
echo "📝 使用说明："
echo "1. 启动服务: python main.py"
echo "2. 访问 Web 界面: http://localhost:8501" 