#!/usr/bin/env python3
"""
簡化版 Streamlit Dashboard
用於 ByteC Network Agent 數據可視化
"""

import os
import sys
import asyncio
import asyncpg
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional
import logging
import threading
import concurrent.futures

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 添加項目根目錄到 Python 路徑
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

# 數據庫配置
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "34.124.206.16"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "database": os.getenv("DB_NAME", "postback_db"),
    "user": os.getenv("DB_USER", "postback_admin"),
    "password": os.getenv("DB_PASSWORD", "ByteC2024PostBack_CloudSQL")
}

class DatabaseManager:
    def __init__(self):
        self.cache = {}
        self.cache_timeout = 300  # 5分鐘緩存
    
    async def get_connection(self):
        """獲取數據庫連接"""
        return await asyncpg.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            database=DB_CONFIG["database"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"]
        )
    
    async def test_connection(self):
        """測試數據庫連接"""
        try:
            conn = await self.get_connection()
            await conn.fetchrow("SELECT 1")
            await conn.close()
            return True
        except Exception as e:
            logger.error(f"數據庫連接測試失敗: {e}")
            return False
    
    async def get_partners(self):
        """獲取合作夥伴列表"""
        try:
            conn = await self.get_connection()
            query = "SELECT id, partner_name, partner_code FROM partners WHERE is_active = true"
            rows = await conn.fetch(query)
            await conn.close()
            return [{"id": row["id"], "name": row["partner_name"], "code": row["partner_code"]} for row in rows]
        except Exception as e:
            logger.error(f"獲取合作夥伴失敗: {e}")
            return []
    
    async def get_conversions_summary(self, days: int = 7, partner_id: Optional[int] = None):
        """獲取轉化數據摘要"""
        try:
            conn = await self.get_connection()
            where_clause = "WHERE created_at >= NOW() - INTERVAL '%s days'" % days
            if partner_id:
                where_clause += f" AND partner_id = {partner_id}"
            
            query = f"""
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as conversions,
                SUM(COALESCE(sale_amount, usd_sale_amount, 0)) as total_sales,
                SUM(COALESCE(payout, usd_payout, 0)) as total_payout
            FROM conversions
            {where_clause}
            GROUP BY DATE(created_at)
            ORDER BY date DESC
            """
            rows = await conn.fetch(query)
            await conn.close()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"獲取轉化摘要失敗: {e}")
            return []
    
    async def get_hourly_trends(self, days: int = 7, partner_id: Optional[int] = None):
        """獲取小時趨勢數據"""
        try:
            conn = await self.get_connection()
            where_clause = "WHERE created_at >= NOW() - INTERVAL '%s days'" % days
            if partner_id:
                where_clause += f" AND partner_id = {partner_id}"
            
            query = f"""
            SELECT 
                EXTRACT(HOUR FROM created_at) as hour,
                COUNT(*) as conversions,
                SUM(COALESCE(sale_amount, usd_sale_amount, 0)) as total_sales
            FROM conversions
            {where_clause}
            GROUP BY EXTRACT(HOUR FROM created_at)
            ORDER BY hour
            """
            rows = await conn.fetch(query)
            await conn.close()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"獲取小時趨勢失敗: {e}")
            return []
    
    async def get_partner_performance(self, days: int = 7):
        """獲取合作夥伴表現數據"""
        try:
            conn = await self.get_connection()
            query = f"""
            SELECT 
                p.partner_name,
                p.partner_code,
                COUNT(c.id) as conversions,
                SUM(COALESCE(c.sale_amount, c.usd_sale_amount, 0)) as total_sales,
                SUM(COALESCE(c.payout, c.usd_payout, 0)) as total_payout
            FROM partners p
            LEFT JOIN conversions c ON p.id = c.partner_id 
                AND c.created_at >= NOW() - INTERVAL '{days} days'
            WHERE p.is_active = true
            GROUP BY p.id, p.partner_name, p.partner_code
            ORDER BY total_sales DESC
            LIMIT 10
            """
            rows = await conn.fetch(query)
            await conn.close()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"獲取合作夥伴表現失敗: {e}")
            return []

class ChartGenerator:
    @staticmethod
    def create_daily_trend_chart(data: List[Dict]) -> go.Figure:
        """創建每日趨勢圖表"""
        if not data:
            return go.Figure().add_annotation(
                text="暫無數據",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
        
        df = pd.DataFrame(data)
        
        fig = go.Figure()
        
        # 添加轉化數量線
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['conversions'],
            mode='lines+markers',
            name='轉化數量',
            line=dict(color='#1f77b4', width=2),
            yaxis='y'
        ))
        
        # 添加銷售額線
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['total_sales'],
            mode='lines+markers',
            name='銷售額 ($)',
            line=dict(color='#ff7f0e', width=2),
            yaxis='y2'
        ))
        
        fig.update_layout(
            title='每日轉化趨勢',
            xaxis_title='日期',
            yaxis=dict(title='轉化數量', side='left'),
            yaxis2=dict(title='銷售額 ($)', side='right', overlaying='y'),
            height=400,
            hovermode='x unified'
        )
        
        return fig
    
    @staticmethod
    def create_hourly_trend_chart(data: List[Dict]) -> go.Figure:
        """創建小時趨勢圖表"""
        if not data:
            return go.Figure().add_annotation(
                text="暫無數據",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
        
        df = pd.DataFrame(data)
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=df['hour'],
            y=df['conversions'],
            name='轉化數量',
            marker_color='#1f77b4'
        ))
        
        fig.update_layout(
            title='24小時轉化分佈',
            xaxis_title='小時',
            yaxis_title='轉化數量',
            height=400,
            xaxis=dict(tickmode='linear', tick0=0, dtick=1)
        )
        
        return fig
    
    @staticmethod
    def create_partner_performance_chart(data: List[Dict]) -> go.Figure:
        """創建合作夥伴表現圖表"""
        if not data:
            return go.Figure().add_annotation(
                text="暫無數據",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
        
        df = pd.DataFrame(data)
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=df['partner_name'],
            y=df['total_sales'],
            name='銷售額',
            marker_color='#2ca02c'
        ))
        
        fig.update_layout(
            title='合作夥伴表現 (前10名)',
            xaxis_title='合作夥伴',
            yaxis_title='銷售額 (USD)',
            height=400,
            xaxis_tickangle=-45
        )
        
        return fig

def run_async(coro):
    """運行異步函數"""
    try:
        # 在新的線程中運行異步代碼
        def run_in_thread():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(coro)
            finally:
                loop.close()
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_in_thread)
            return future.result(timeout=30)
    except Exception as e:
        logger.error(f"異步執行失敗: {e}")
        return None

def main():
    """主應用程序"""
    st.set_page_config(
        page_title="ByteC Network Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 頁面標題
    st.title("📊 ByteC Network Agent Dashboard")
    st.markdown("### 實時數據可視化平台")
    
    # 初始化數據庫管理器
    db_manager = DatabaseManager()
    
    # 測試數據庫連接
    if not run_async(db_manager.test_connection()):
        st.error("❌ 數據庫連接失敗，請檢查配置")
        return
    
    # 側邊欄配置
    st.sidebar.header("📝 配置選項")
    
    # 獲取合作夥伴列表
    partners = run_async(db_manager.get_partners())
    partner_options = {"全部": None}
    if partners:
        partner_options.update({p["name"]: p["id"] for p in partners})
    
    selected_partner = st.sidebar.selectbox(
        "選擇合作夥伴",
        options=list(partner_options.keys()),
        index=0
    )
    
    days = st.sidebar.selectbox(
        "時間範圍",
        options=[1, 3, 7, 14, 30],
        index=2,
        format_func=lambda x: f"過去 {x} 天"
    )
    
    # 自動刷新
    auto_refresh = st.sidebar.checkbox("自動刷新 (30秒)", value=False)
    if auto_refresh:
        st.rerun()
    
    # 手動刷新按鈕
    if st.sidebar.button("🔄 手動刷新"):
        st.rerun()
    
    # 主要內容區域
    partner_id = partner_options[selected_partner]
    
    # 獲取數據
    with st.spinner("正在加載數據..."):
        daily_data = run_async(db_manager.get_conversions_summary(days, partner_id))
        hourly_data = run_async(db_manager.get_hourly_trends(days, partner_id))
        partner_data = run_async(db_manager.get_partner_performance(days))
    
    # 創建圖表
    col1, col2 = st.columns(2)
    
    with col1:
        st.plotly_chart(
            ChartGenerator.create_daily_trend_chart(daily_data),
            use_container_width=True
        )
    
    with col2:
        st.plotly_chart(
            ChartGenerator.create_hourly_trend_chart(hourly_data),
            use_container_width=True
        )
    
    # 合作夥伴表現圖表
    st.plotly_chart(
        ChartGenerator.create_partner_performance_chart(partner_data),
        use_container_width=True
    )
    
    # 數據摘要
    if daily_data:
        total_conversions = sum(row['conversions'] for row in daily_data)
        total_sales = sum(row['total_sales'] for row in daily_data)
        total_payout = sum(row['total_payout'] for row in daily_data)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("總轉化數", f"{total_conversions:,}")
        
        with col2:
            st.metric("總銷售額", f"${total_sales:,.2f}")
        
        with col3:
            st.metric("總支出", f"${total_payout:,.2f}")
    
    # 頁腳
    st.markdown("---")
    st.markdown("**ByteC Network Agent Dashboard** | 實時數據更新")

if __name__ == "__main__":
    main() 