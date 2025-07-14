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

# 導入我們創建的 AI 代理
from agents.company_agent.main import CompanyManagerAgent
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
        
        # 初始化 AI 代理
        company_agent = CompanyManagerAgent(WHODB_CONFIG)
        await company_agent.initialize()
        
        logger.info("✅ 所有服務初始化完成")
        
    except Exception as e:
        logger.error(f"❌ 服務初始化失敗: {str(e)}")
        raise

def run_async(coroutine):
    """運行異步函數的輔助函數"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coroutine)
    finally:
        loop.close()

@app.route('/')
def index():
    """主頁面"""
    return render_template('company_ai_chat.html')

@app.route('/api/company-ai-query', methods=['POST'])
def company_ai_query():
    """處理公司 AI 查詢"""
    try:
        # 獲取請求數據
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({
                'success': False,
                'error': '缺少查詢參數'
            }), 400
        
        user_query = data['query']
        user_id = data.get('user_id', 'default')
        
        logger.info(f"📝 收到用戶查詢: {user_query}")
        
        # 處理查詢
        result = run_async(company_agent.process_user_query(user_query, user_id))
        
        logger.info(f"✅ 查詢處理完成: {result['success']}")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"❌ API 查詢失敗: {str(e)}")
        logger.error(traceback.format_exc())
        
        return jsonify({
            'success': False,
            'error': f'查詢處理失敗: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/financial-dashboard', methods=['GET'])
def financial_dashboard():
    """獲取財務儀表板數據"""
    try:
        # 獲取查詢參數
        time_range = request.args.get('time_range', 'week')
        
        logger.info(f"📊 獲取儀表板數據: {time_range}")
        
        # 獲取儀表板數據
        result = run_async(company_agent.get_financial_dashboard_data(time_range))
        
        logger.info(f"✅ 儀表板數據獲取完成: {result['success']}")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"❌ 儀表板數據獲取失敗: {str(e)}")
        logger.error(traceback.format_exc())
        
        return jsonify({
            'success': False,
            'error': f'儀表板數據獲取失敗: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/conversation-history', methods=['GET'])
def conversation_history():
    """獲取對話歷史"""
    try:
        user_id = request.args.get('user_id', 'default')
        
        logger.info(f"📜 獲取對話歷史: {user_id}")
        
        # 獲取對話歷史
        result = run_async(company_agent.get_conversation_history(user_id))
        
        return jsonify({
            'success': True,
            'data': result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ 對話歷史獲取失敗: {str(e)}")
        logger.error(traceback.format_exc())
        
        return jsonify({
            'success': False,
            'error': f'對話歷史獲取失敗: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/whodb-query', methods=['POST'])
def whodb_query():
    """直接執行 whodb 查詢"""
    try:
        # 獲取請求數據
        data = request.get_json()
        
        if not data or 'sql' not in data:
            return jsonify({
                'success': False,
                'error': '缺少 SQL 查詢參數'
            }), 400
        
        sql_query = data['sql']
        
        logger.info(f"🔍 執行 whodb 查詢: {sql_query}")
        
        # 直接執行 SQL 查詢
        result = run_async(company_agent.whodb_client.execute_query(sql_query))
        
        return jsonify({
            'success': True,
            'data': result,
            'sql_query': sql_query,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ whodb 查詢失敗: {str(e)}")
        logger.error(traceback.format_exc())
        
        return jsonify({
            'success': False,
            'error': f'whodb 查詢失敗: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/table-schema', methods=['GET'])
def table_schema():
    """獲取表結構"""
    try:
        table_name = request.args.get('table_name', 'conversions')
        
        logger.info(f"🔍 獲取表結構: {table_name}")
        
        # 獲取表結構
        result = run_async(company_agent.whodb_client.get_table_schema(table_name))
        
        return jsonify({
            'success': True,
            'data': result,
            'table_name': table_name,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ 表結構獲取失敗: {str(e)}")
        logger.error(traceback.format_exc())
        
        return jsonify({
            'success': False,
            'error': f'表結構獲取失敗: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康檢查端點"""
    try:
        # 檢查服務狀態
        health_status = {
            'api_status': 'healthy',
            'database_status': 'connected' if db_manager else 'disconnected',
            'whodb_status': 'connected' if company_agent and company_agent.whodb_client else 'disconnected',
            'ai_agent_status': 'active' if company_agent else 'inactive',
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'data': health_status
        })
        
    except Exception as e:
        logger.error(f"❌ 健康檢查失敗: {str(e)}")
        
        return jsonify({
            'success': False,
            'error': f'健康檢查失敗: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/analytics', methods=['GET'])
def analytics():
    """分析數據端點"""
    try:
        # 獲取分析類型
        analysis_type = request.args.get('type', 'overview')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        logger.info(f"📈 獲取分析數據: {analysis_type}")
        
        # 根據分析類型獲取不同的數據
        if analysis_type == 'overview':
            result = run_async(dashboard_service.get_summary_data(start_date, end_date))
        elif analysis_type == 'company':
            result = run_async(dashboard_service.get_company_level_data(start_date, end_date))
        elif analysis_type == 'partner':
            result = run_async(dashboard_service.get_partner_level_data(start_date, end_date))
        else:
            result = run_async(dashboard_service.get_summary_data(start_date, end_date))
        
        return jsonify({
            'success': True,
            'data': result,
            'analysis_type': analysis_type,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ 分析數據獲取失敗: {str(e)}")
        logger.error(traceback.format_exc())
        
        return jsonify({
            'success': False,
            'error': f'分析數據獲取失敗: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.errorhandler(404)
def not_found(error):
    """404 錯誤處理"""
    return jsonify({
        'success': False,
        'error': '端點未找到',
        'timestamp': datetime.now().isoformat()
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """500 錯誤處理"""
    return jsonify({
        'success': False,
        'error': '內部服務器錯誤',
        'timestamp': datetime.now().isoformat()
    }), 500

def create_app():
    """創建並配置 Flask 應用"""
    # 設置模板路徑
    app.template_folder = 'templates'
    
    # 初始化服務
    run_async(initialize_services())
    
    return app

if __name__ == '__main__':
    try:
        # 創建應用
        app = create_app()
        
        # 啟動服務
        logger.info("🚀 啟動公司財務AI助手API服務...")
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            threaded=True
        )
        
    except Exception as e:
        logger.error(f"❌ 服務啟動失敗: {str(e)}")
        logger.error(traceback.format_exc())
    
    finally:
        # 清理資源
        if company_agent:
            run_async(company_agent.close())
        
        logger.info("👋 服務已關閉") 