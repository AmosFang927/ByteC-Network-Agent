#!/usr/bin/env python3
"""
公司財務AI助手 API 端點
Company Finance AI Assistant API Endpoints
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import traceback
import sys
import os
import importlib.util

# 添加項目根目錄到Python路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
company_agent_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(os.path.dirname(company_agent_dir))

# 確保不會導入根目錄的main.py
if company_agent_dir not in sys.path:
    sys.path.insert(0, company_agent_dir)

# 導入我們創建的 AI 代理
try:
    # 直接從company-agent目錄導入main.py
    import importlib.util
    main_file_path = os.path.join(company_agent_dir, "main.py")
    
    if not os.path.exists(main_file_path):
        raise ImportError(f"找不到主程式文件: {main_file_path}")
    
    spec = importlib.util.spec_from_file_location("company_main", main_file_path)
    company_main = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(company_main)
    CompanyManagerAgent = company_main.CompanyManagerAgent
    
    print("✅ CompanyManagerAgent 導入成功")
    
except Exception as e:
    print(f"❌ 導入失敗: {e}")
    raise ImportError(f"無法導入CompanyManagerAgent: {e}")

# 添加project_root到sys.path以導入其他模組
if project_root not in sys.path:
    sys.path.append(project_root)

from agents.dashboard_agent.backend.database_manager import DatabaseManager
from agents.dashboard_agent.backend.dashboard_service import DashboardService

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 創建 Flask 應用
app = Flask(__name__)
CORS(app)

# 全局變量
company_agent = None
db_manager = None
dashboard_service = None

# whodb 配置
WHODB_CONFIG = {
    'base_url': 'http://localhost:8080',  # 您的 whodb 地址
    'username': 'admin',  # whodb 用戶名
    'password': 'password'  # whodb 密碼
}

async def initialize_services():
    """初始化服務"""
    global company_agent, db_manager, dashboard_service
    
    try:
        # 初始化數據庫管理器
        db_manager = DatabaseManager()
        await db_manager.init_pool()
        
        # 初始化 dashboard 服務
        dashboard_service = DashboardService(db_manager)
        
        # 初始化 company 代理
        company_agent = CompanyManagerAgent(WHODB_CONFIG)
        await company_agent.initialize()
        
        logger.info("所有服務初始化完成")
        return True
        
    except Exception as e:
        logger.error(f"服務初始化失敗: {e}")
        return False

def run_async(coroutine):
    """運行異步函數的輔助函數"""
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coroutine)
    except RuntimeError:
        # 如果沒有事件循環，創建新的
        return asyncio.run(coroutine)

@app.route('/')
def index():
    """首頁 - 渲染公司AI聊天界面"""
    return render_template('company_ai_chat.html')

@app.route('/api/company-ai-query', methods=['POST'])
def company_ai_query():
    """處理公司AI查詢"""
    try:
        data = request.get_json()
        user_query = data.get('query', '')
        user_id = data.get('user_id', 'default')
        
        if not user_query:
            return jsonify({
                'success': False,
                'error': '查詢內容不能為空'
            }), 400
        
        # 如果代理未初始化，先初始化
        if not company_agent:
            if not run_async(initialize_services()):
                return jsonify({
                    'success': False,
                    'error': '服務初始化失敗'
                }), 500
        
        # 處理查詢
        result = run_async(company_agent.process_user_query(user_query, user_id))
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"查詢處理錯誤: {e}")
        return jsonify({
            'success': False,
            'error': f'查詢處理失敗: {str(e)}'
        }), 500

@app.route('/api/financial-dashboard', methods=['GET'])
def financial_dashboard():
    """獲取財務儀表板數據"""
    try:
        time_range = request.args.get('time_range', 'week')
        
        if not company_agent:
            if not run_async(initialize_services()):
                return jsonify({
                    'success': False,
                    'error': '服務初始化失敗'
                }), 500
        
        # 獲取儀表板數據
        dashboard_data = run_async(company_agent.get_financial_dashboard_data(time_range))
        
        return jsonify(dashboard_data)
        
    except Exception as e:
        logger.error(f"獲取儀表板數據錯誤: {e}")
        return jsonify({
            'success': False,
            'error': f'獲取儀表板數據失敗: {str(e)}'
        }), 500

@app.route('/api/conversation-history', methods=['GET'])
def conversation_history():
    """獲取對話歷史"""
    try:
        user_id = request.args.get('user_id', 'default')
        
        if not company_agent:
            return jsonify([])
        
        # 獲取對話歷史
        history = run_async(company_agent.get_conversation_history(user_id))
        
        # 轉換為前端需要的格式
        formatted_history = []
        for entry in history:
            formatted_history.append({
                'role': 'user',
                'content': entry['user_query'],
                'timestamp': entry['timestamp']
            })
            formatted_history.append({
                'role': 'assistant',
                'content': entry['ai_response'],
                'sql_query': entry.get('sql_query'),
                'data': entry.get('results', {}).get('raw_data'),
                'timestamp': entry['timestamp']
            })
        
        return jsonify(formatted_history)
        
    except Exception as e:
        logger.error(f"獲取對話歷史錯誤: {e}")
        return jsonify([])

@app.route('/api/whodb-query', methods=['POST'])
def whodb_query():
    """直接執行 whodb 查詢"""
    try:
        data = request.get_json()
        sql_query = data.get('sql', '')
        
        if not sql_query:
            return jsonify({
                'success': False,
                'error': 'SQL查詢不能為空'
            }), 400
        
        if not company_agent:
            if not run_async(initialize_services()):
                return jsonify({
                    'success': False,
                    'error': '服務初始化失敗'
                }), 500
        
        # 執行查詢
        result = run_async(company_agent.whodb_client.execute_query(sql_query))
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"WhoDB查詢錯誤: {e}")
        return jsonify({
            'success': False,
            'error': f'查詢失敗: {str(e)}'
        }), 500

@app.route('/api/table-schema', methods=['GET'])
def table_schema():
    """獲取表結構"""
    try:
        table_name = request.args.get('table')
        
        if not table_name:
            return jsonify({
                'success': False,
                'error': '表名不能為空'
            }), 400
        
        if not company_agent:
            if not run_async(initialize_services()):
                return jsonify({
                    'success': False,
                    'error': '服務初始化失敗'
                }), 500
        
        # 獲取表結構
        schema = run_async(company_agent.whodb_client.get_table_schema(table_name))
        
        return jsonify(schema)
        
    except Exception as e:
        logger.error(f"獲取表結構錯誤: {e}")
        return jsonify({
            'success': False,
            'error': f'獲取表結構失敗: {str(e)}'
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康檢查端點"""
    try:
        # 強制初始化服務（如果還沒初始化）
        if not company_agent:
            run_async(initialize_services())
        
        status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'services': {
                'company_agent': company_agent is not None,
                'database_manager': db_manager is not None,
                'dashboard_service': dashboard_service is not None
            }
        }
        
        # 檢查 whodb 連接 - 實際測試連接
        whodb_status = False
        if company_agent and company_agent.whodb_client:
            try:
                # 簡單測試 - 檢查 session 是否存在
                whodb_status = company_agent.whodb_client.session is not None
            except:
                whodb_status = False
        status['whodb_connected'] = whodb_status
        
        # 檢查數據庫連接 - 實際測試連接
        db_status = False
        if db_manager:
            try:
                db_status = run_async(db_manager.test_connection())
            except:
                db_status = False
        status['database_connected'] = db_status
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"健康檢查錯誤: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/analytics', methods=['GET'])
def analytics():
    """獲取分析數據"""
    try:
        if not company_agent:
            return jsonify({
                'success': False,
                'error': '服務未初始化'
            }), 500
        
        # 獲取分析數據
        analytics_data = {
            'total_queries': len(company_agent.conversation_history),
            'recent_queries': [
                {
                    'query': entry['user_query'],
                    'timestamp': entry['timestamp'],
                    'success': True
                }
                for entry in company_agent.conversation_history[-10:]
            ],
            'popular_query_types': {
                'revenue': sum(1 for entry in company_agent.conversation_history if '收入' in entry['user_query']),
                'conversion': sum(1 for entry in company_agent.conversation_history if '轉化' in entry['user_query']),
                'partner': sum(1 for entry in company_agent.conversation_history if '合作夥伴' in entry['user_query'])
            }
        }
        
        return jsonify(analytics_data)
        
    except Exception as e:
        logger.error(f"獲取分析數據錯誤: {e}")
        return jsonify({
            'success': False,
            'error': f'獲取分析數據失敗: {str(e)}'
        }), 500

@app.errorhandler(404)
def not_found(error):
    """404錯誤處理"""
    return jsonify({
        'success': False,
        'error': '端點不存在'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """500錯誤處理"""
    return jsonify({
        'success': False,
        'error': '內部伺服器錯誤'
    }), 500

def create_app():
    """創建並配置Flask應用"""
    # 初始化服務
    run_async(initialize_services())
    return app

if __name__ == '__main__':
    # 開發模式運行
    app.run(
        host='0.0.0.0',
        port=5001,  # 改為5001避免與AirPlay衝突
        debug=True,
        threaded=True
    ) 