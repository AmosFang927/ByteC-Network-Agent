#!/usr/bin/env python3
"""
公司財務AI助手 - Streamlit 版本
Company Finance AI Assistant - Streamlit Version
"""

import streamlit as st
import requests
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import asyncio
from typing import Dict, List, Any, Optional
import sys
import os

# 添加項目根目錄到Python路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
company_agent_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(os.path.dirname(company_agent_dir))
sys.path.append(project_root)
sys.path.append(company_agent_dir)

# 導入配置
def load_config():
    """加載配置文件"""
    # 獲取當前文件目錄
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 獲取company-agent目錄
    company_agent_dir = os.path.dirname(current_dir)
    # 獲取config目錄
    config_dir = os.path.join(company_agent_dir, 'config')
    
    # 檢查config目錄是否存在
    if os.path.exists(config_dir):
        sys.path.insert(0, config_dir)
        try:
            from streamlit_config import StreamlitConfig
            return StreamlitConfig()
        except ImportError:
            pass
    
    # 嘗試相對導入
    try:
        sys.path.insert(0, company_agent_dir)
        from config.streamlit_config import StreamlitConfig
        return StreamlitConfig()
    except ImportError:
        pass
    
    # 創建默認配置
    class DefaultConfig:
        APP_TITLE = "公司財務AI助手"
        APP_ICON = "💰"
        PAGE_LAYOUT = "wide"
        SIDEBAR_STATE = "expanded"
        API_BASE_URL = "http://localhost:5001"
        API_TIMEOUT = 30
        HEALTH_CHECK_TIMEOUT = 5
        QUICK_QUERIES = [
            "今天的收入是多少？",
            "本月毛利率怎麼樣？",
            "哪個合作夥伴表現最好？",
            "現金流狀況如何？"
        ]
        CUSTOM_CSS = ""
        
        def get_api_url(self, endpoint: str) -> str:
            """獲取API URL"""
            return f"{self.API_BASE_URL}{endpoint}"
    
    return DefaultConfig()

# 加載配置
config = load_config()

# 設置頁面配置
st.set_page_config(
    page_title=config.APP_TITLE,
    page_icon=config.APP_ICON,
    layout=config.PAGE_LAYOUT,
    initial_sidebar_state=config.SIDEBAR_STATE
)

# 自定義CSS樣式
st.markdown(config.CUSTOM_CSS, unsafe_allow_html=True)

def init_session_state():
    """初始化 session state"""
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    if 'current_query' not in st.session_state:
        st.session_state.current_query = ""
    if 'dashboard_data' not in st.session_state:
        st.session_state.dashboard_data = None
    if 'system_health' not in st.session_state:
        st.session_state.system_health = {}

def check_system_health():
    """檢查系統健康狀態"""
    try:
        response = requests.get(
            config.get_api_url("/api/health"), 
            timeout=config.HEALTH_CHECK_TIMEOUT
        )
        if response.status_code == 200:
            st.session_state.system_health = response.json()
            return True
        return False
    except Exception as e:
        st.session_state.system_health = {"error": str(e)}
        return False

def send_ai_query(query: str) -> Dict[str, Any]:
    """發送AI查詢到後端"""
    try:
        response = requests.post(
            config.get_api_url("/api/company-ai-query"),
            json={"query": query},
            timeout=config.API_TIMEOUT
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"success": False, "error": f"API錯誤: {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_financial_dashboard():
    """獲取財務儀表板數據"""
    try:
        response = requests.get(
            config.get_api_url("/api/financial-dashboard"), 
            timeout=config.API_TIMEOUT
        )
        if response.status_code == 200:
            return response.json()
        # 如果API無法連接，返回預設數據
        return config.DEFAULT_DASHBOARD_DATA
    except Exception as e:
        st.warning(f"無法連接到API，使用預設數據: {e}")
        return config.DEFAULT_DASHBOARD_DATA

def get_conversation_history():
    """獲取對話歷史"""
    try:
        response = requests.get(
            config.get_api_url("/api/conversation-history"), 
            timeout=config.API_TIMEOUT
        )
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"獲取對話歷史失敗: {e}")
        return []

def render_sidebar():
    """渲染側邊欄"""
    with st.sidebar:
        st.title("🏢 公司財務AI助手")
        st.markdown("---")
        
        # 系統狀態
        st.subheader("🔧 系統狀態")
        if check_system_health():
            health = st.session_state.system_health
            if health.get("status") == "healthy":
                st.success("✅ 系統運行正常")
            else:
                st.warning("⚠️ 系統狀態異常")
                
            # 顯示詳細狀態
            if "whodb_connected" in health:
                status = "🟢 已連接" if health["whodb_connected"] else "🔴 連接失敗"
                st.text(f"WhoDB: {status}")
                
            if "database_connected" in health:
                status = "🟢 已連接" if health["database_connected"] else "🔴 連接失敗"
                st.text(f"數據庫: {status}")
        else:
            st.error("❌ 系統連接失敗")
        
        st.markdown("---")
        
        # 快速查詢按鈕
        st.subheader("⚡ 快速查詢")
        
        for query in config.QUICK_QUERIES:
            if st.button(query, key=f"quick_{query}"):
                st.session_state.current_query = query
                st.rerun()
        
        st.markdown("---")
        
        # 操作按鈕
        st.subheader("🔧 操作")
        if st.button("🗑️ 清除對話歷史"):
            st.session_state.conversation_history = []
            st.success("對話歷史已清除")
            
        if st.button("🔄 重新加載儀表板"):
            st.session_state.dashboard_data = None
            st.rerun()

def render_financial_dashboard():
    """渲染財務儀表板"""
    st.subheader("📊 財務儀表板")
    
    if st.session_state.dashboard_data is None:
        with st.spinner("加載儀表板數據..."):
            st.session_state.dashboard_data = get_financial_dashboard()
    
    if st.session_state.dashboard_data:
        data = st.session_state.dashboard_data
        
        # 指標卡片
        col1, col2, col3, col4 = st.columns(4)
        
        metrics = [
            ('total_revenue', col1, 'revenue_growth'),
            ('gross_margin', col2, 'margin_change'),
            ('total_conversions', col3, 'conversion_growth'),
            ('cash_flow', col4, 'cash_flow_change')
        ]
        
        for metric_key, col, delta_key in metrics:
            metric_config = config.METRICS_CONFIG[metric_key]
            with col:
                value = data.get(metric_key, 0)
                delta = data.get(delta_key, 0)
                
                if metric_key == 'total_conversions':
                    formatted_value = metric_config['format'].format(int(value))
                else:
                    formatted_value = metric_config['format'].format(value)
                
                st.metric(
                    metric_config['label'],
                    formatted_value,
                    delta=metric_config['delta_format'].format(delta)
                )
        
        # 圖表
        if "revenue_trend" in data:
            st.subheader("📈 收入趨勢")
            trend_data = data["revenue_trend"]
            df = pd.DataFrame(trend_data)
            fig = px.line(df, x="date", y="revenue", title="收入趨勢圖")
            st.plotly_chart(fig, use_container_width=config.CHART_CONFIG['use_container_width'])
        
        if "partner_performance" in data:
            st.subheader("🤝 合作夥伴表現")
            partner_data = data["partner_performance"]
            df = pd.DataFrame(partner_data)
            fig = px.bar(df, x="partner", y="revenue", title="合作夥伴收入排名")
            st.plotly_chart(fig, use_container_width=config.CHART_CONFIG['use_container_width'])
    
    else:
        st.error("無法加載儀表板數據")

def render_chat_interface():
    """渲染聊天界面"""
    st.subheader("💬 AI 對話助手")
    
    # 聊天容器
    chat_container = st.container()
    
    with chat_container:
        # 顯示對話歷史
        for i, message in enumerate(st.session_state.conversation_history):
            if message["role"] == "user":
                with st.chat_message("user"):
                    st.write(message["content"])
            else:
                with st.chat_message("assistant"):
                    if "sql_query" in message:
                        st.code(message["sql_query"], language="sql")
                    st.write(message["content"])
                    if "data" in message and message["data"]:
                        st.json(message["data"])
    
    # 輸入框
    user_input = st.chat_input("輸入您的財務問題...")
    
    # 處理快速查詢
    if st.session_state.current_query:
        user_input = st.session_state.current_query
        st.session_state.current_query = ""
    
    if user_input:
        # 添加用戶消息
        st.session_state.conversation_history.append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now().isoformat()
        })
        
        # 顯示用戶消息
        with st.chat_message("user"):
            st.write(user_input)
        
        # 發送AI查詢
        with st.chat_message("assistant"):
            with st.spinner("正在分析..."):
                response = send_ai_query(user_input)
                
                if response.get("success"):
                    # 顯示SQL查詢（如果有）
                    if "sql_query" in response:
                        st.code(response["sql_query"], language="sql")
                    
                    # 顯示AI回應
                    ai_response = response.get("response", "查詢完成")
                    st.write(ai_response)
                    
                    # 顯示數據（如果有）
                    if "data" in response and response["data"]:
                        st.json(response["data"])
                        
                        # 如果是數值數據，嘗試創建圖表
                        try:
                            if isinstance(response["data"], list) and len(response["data"]) > 0:
                                df = pd.DataFrame(response["data"])
                                if len(df.columns) >= 2:
                                    numeric_cols = df.select_dtypes(include=['number']).columns
                                    if len(numeric_cols) > 0:
                                        fig = px.bar(df, x=df.columns[0], y=numeric_cols[0])
                                        st.plotly_chart(fig, use_container_width=True)
                        except:
                            pass
                    
                    # 添加AI回應到歷史
                    st.session_state.conversation_history.append({
                        "role": "assistant",
                        "content": ai_response,
                        "sql_query": response.get("sql_query"),
                        "data": response.get("data"),
                        "timestamp": datetime.now().isoformat()
                    })
                    
                else:
                    error_msg = f"查詢失敗: {response.get('error', '未知錯誤')}"
                    st.error(error_msg)
                    
                    # 添加錯誤信息到歷史
                    st.session_state.conversation_history.append({
                        "role": "assistant",
                        "content": error_msg,
                        "timestamp": datetime.now().isoformat()
                    })
        
        # 重新運行以更新界面
        st.rerun()

def render_analytics_section():
    """渲染分析部分"""
    st.subheader("📊 深度分析")
    
    tab1, tab2, tab3 = st.tabs(["📈 財務分析", "🤝 合作夥伴", "💹 趨勢預測"])
    
    with tab1:
        st.write("### 財務指標分析")
        
        # 模擬一些財務數據
        metrics_data = {
            "指標": ["收入", "支出", "毛利", "淨利", "現金流"],
            "當前值": [120000, 80000, 40000, 30000, 25000],
            "上月值": [110000, 75000, 35000, 28000, 22000],
            "增長率": [9.1, 6.7, 14.3, 7.1, 13.6]
        }
        
        df = pd.DataFrame(metrics_data)
        st.dataframe(df, use_container_width=True)
        
        # 創建增長率圖表
        fig = px.bar(df, x="指標", y="增長率", title="財務指標增長率")
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.write("### 合作夥伴表現")
        
        # 模擬合作夥伴數據
        partner_data = {
            "合作夥伴": ["ByteC", "InvolveAsia", "MKK", "DeepLeaper"],
            "收入": [50000, 35000, 25000, 10000],
            "轉化數": [1200, 800, 600, 200],
            "ROI": [2.5, 1.8, 1.2, 0.8]
        }
        
        df = pd.DataFrame(partner_data)
        st.dataframe(df, use_container_width=True)
        
        # 創建餅圖
        fig = px.pie(df, values="收入", names="合作夥伴", title="合作夥伴收入分布")
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.write("### 趨勢預測")
        
        # 模擬趨勢數據
        import numpy as np
        dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
        base_revenue = 4000
        trend_data = {
            "日期": dates,
            "實際收入": base_revenue + np.random.normal(0, 500, 30).cumsum(),
            "預測收入": base_revenue + np.random.normal(100, 200, 30).cumsum()
        }
        
        df = pd.DataFrame(trend_data)
        fig = px.line(df, x="日期", y=["實際收入", "預測收入"], title="收入趨勢與預測")
        st.plotly_chart(fig, use_container_width=True)

def main():
    """主函數"""
    # 初始化
    init_session_state()
    
    # 渲染側邊欄
    render_sidebar()
    
    # 主內容區域
    st.title("🏢 公司財務AI助手")
    st.markdown("基於 WhoDB 和 AI 技術的智能財務分析系統")
    
    # 主要內容標籤
    tab1, tab2, tab3 = st.tabs(["💬 AI對話", "📊 財務儀表板", "📈 深度分析"])
    
    with tab1:
        render_chat_interface()
    
    with tab2:
        render_financial_dashboard()
    
    with tab3:
        render_analytics_section()
    
    # 底部信息
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.9em;">
        🚀 ByteC Network Agent | 🤖 AI-Powered Financial Analysis | 📊 Real-time Dashboard
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 