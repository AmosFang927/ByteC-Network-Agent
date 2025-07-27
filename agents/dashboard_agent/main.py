#!/usr/bin/env python3
"""
ByteC Performance Dashboard 主启动文件
"""

import os
import sys
import logging

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from agents.dashboard_agent.backend.dashboard_server import app

def main():
    """主函数"""
    # 设置环境变量
    os.environ.setdefault('DB_HOST', '34.124.206.16')
    os.environ.setdefault('DB_PORT', '5432')
    os.environ.setdefault('DB_NAME', 'postback_db')
    os.environ.setdefault('DB_USER', 'postback_admin')
    os.environ.setdefault('DB_PASSWORD', 'ByteC2024PostBack_CloudSQL')
    
    # 启动Flask应用
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    print(f"🚀 启动ByteC Performance Dashboard")
    print(f"📊 访问地址: http://localhost:{port}")
    print(f"🔧 调试模式: {debug}")
    
    app.run(host='0.0.0.0', port=port, debug=debug, threaded=True)

if __name__ == '__main__':
    main() 