#!/usr/bin/env python3
"""
同步数据库管理器
專門為 Flask 應用設計的同步版本
"""

import os
import psycopg2
import psycopg2.pool
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Optional, Any
import logging
from datetime import datetime, timedelta, date

# 配置日志
logger = logging.getLogger(__name__)

class SyncDatabaseManager:
    """同步版数据库管理器 - Flask 專用"""
    
    def __init__(self):
        self.db_config = {
            "host": os.getenv("DB_HOST", "34.124.206.16"),
            "port": int(os.getenv("DB_PORT", "5432")),
            "database": os.getenv("DB_NAME", "postback_db"),
            "user": os.getenv("DB_USER", "postback_admin"),
            "password": os.getenv("DB_PASSWORD", "ByteC2024PostBack_CloudSQL")
        }
        
        # 連接池配置
        self.pool = None
        self.pool_initialized = False
        
    def init_pool(self):
        """初始化同步数据库连接池"""
        if self.pool_initialized:
            return
            
        try:
            logger.info("🚀 初始化同步數據庫連接池...")
            
            # 創建連接字符串
            dsn = f"host={self.db_config['host']} " \
                  f"port={self.db_config['port']} " \
                  f"dbname={self.db_config['database']} " \
                  f"user={self.db_config['user']} " \
                  f"password={self.db_config['password']}"
            
            self.pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=5,      # 最小5個連接
                maxconn=50,     # 最大50個連接
                dsn=dsn
            )
            self.pool_initialized = True
            logger.info(f"✅ 同步數據庫連接池初始化成功 (5-50 連接)")
        except Exception as e:
            logger.error(f"❌ 數據庫連接池初始化失敗: {e}")
            raise
        
    def get_connection(self):
        """获取数据库连接"""
        if not self.pool_initialized:
            self.init_pool()
            
        try:
            if self.pool:
                return self.pool.getconn()
            else:
                conn = psycopg2.connect(
                    host=self.db_config["host"],
                    port=self.db_config["port"],
                    database=self.db_config["database"],
                    user=self.db_config["user"],
                    password=self.db_config["password"],
                    connect_timeout=30
                )
                return conn
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            raise
    
    def release_connection(self, conn):
        """釋放數據庫連接"""
        try:
            if self.pool:
                self.pool.putconn(conn)
            else:
                conn.close()
        except Exception as e:
            logger.error(f"釋放連接失敗: {e}")
    
    def close_pool(self):
        """關閉連接池"""
        if self.pool:
            self.pool.closeall()
            logger.info("✅ 數據庫連接池已關閉")

    # =============================================================================
    # 基础数据查询
    # =============================================================================
    
    def get_partners(self) -> List[Dict[str, Any]]:
        """获取所有活跃的合作伙伴"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            query = """
                SELECT id, partner_code, partner_name, is_active, created_at
                FROM partners
                WHERE is_active = true
                ORDER BY partner_name
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            cursor.close()
            
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"获取合作伙伴失败: {e}")
            return []
        finally:
            if conn:
                self.release_connection(conn)

    def get_summary_metrics(self, start_date: str, end_date: str, partner_id: Optional[int] = None) -> Dict[str, Any]:
        """获取总览指标"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            partner_filter = ""
            params = [start_date, end_date]
            if partner_id:
                partner_filter = "AND partner_id = %s"
                params.append(partner_id)
            
            query = f"""
                SELECT 
                    COUNT(*) as total_conversions,
                    SUM(COALESCE(usd_payout, payout, 0)) as total_commission,
                    AVG(COALESCE(usd_payout, payout, 0)) as avg_commission,
                    COUNT(DISTINCT aff_sub) as unique_affiliates
                FROM conversions 
                WHERE event_time::date BETWEEN %s AND %s
                {partner_filter}
            """
            
            cursor.execute(query, params)
            result = cursor.fetchone()
            cursor.close()
            
            if result:
                return dict(result)
            return {
                'total_conversions': 0,
                'total_commission': 0.0,
                'avg_commission': 0.0,
                'unique_affiliates': 0
            }
        except Exception as e:
            logger.error(f"获取总览指标失败: {e}")
            return {
                'total_conversions': 0,
                'total_commission': 0.0,
                'avg_commission': 0.0,
                'unique_affiliates': 0
            }
        finally:
            if conn:
                self.release_connection(conn)

    def get_daily_trend(self, start_date: str, end_date: str, partner_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取每日趋势数据"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            partner_filter = ""
            params = [start_date, end_date]
            if partner_id:
                partner_filter = "AND partner_id = %s"
                params.append(partner_id)
            
            query = f"""
                SELECT 
                    event_time::date as date,
                    COUNT(*) as conversions,
                    SUM(COALESCE(usd_payout, payout, 0)) as commission
                FROM conversions 
                WHERE event_time::date BETWEEN %s AND %s
                {partner_filter}
                GROUP BY event_time::date
                ORDER BY date
            """
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            cursor.close()
            
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"获取每日趋势失败: {e}")
            return []
        finally:
            if conn:
                self.release_connection(conn)

    def get_conversion_report_data(self, start_date: str, end_date: str, 
                                 partner_id: Optional[int] = None, 
                                 page: int = 1, limit: int = 100) -> Dict[str, Any]:
        """获取转换报告数据"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            offset = (page - 1) * limit
            partner_filter = ""
            params = [start_date, end_date, limit, offset]
            if partner_id:
                partner_filter = "AND c.partner_id = %s"
                params.insert(2, partner_id)
            
            # 獲取總數 - 修復日期字段
            count_query = f"""
                SELECT COUNT(*) as total
                FROM conversions c
                WHERE c.event_time::date BETWEEN %s AND %s
                {partner_filter}
            """
            count_params = params[:-2] if partner_id else [start_date, end_date]
            if partner_id:
                count_params.append(partner_id)
            cursor.execute(count_query, count_params)
            total_count = cursor.fetchone()['total']
            
            # 獲取數據 - 修復字段映射
            query = f"""
                SELECT 
                    c.id,
                    c.order_id,
                    c.aff_sub,
                    COALESCE(c.usd_payout, c.payout, 0) as commission_amount,
                    COALESCE(c.conversion_status, 'pending') as status,
                    c.event_time,
                    p.partner_name
                FROM conversions c
                LEFT JOIN partners p ON c.partner_id = p.id
                WHERE c.event_time::date BETWEEN %s AND %s
                {partner_filter}
                ORDER BY c.event_time DESC
                LIMIT %s OFFSET %s
            """
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            cursor.close()
            
            return {
                'conversions': [dict(row) for row in rows],
                'total_count': total_count,
                'page': page,
                'limit': limit
            }
        except Exception as e:
            logger.error(f"获取转换报告数据失败: {e}")
            return {
                'conversions': [],
                'total_count': 0,
                'page': page,
                'limit': limit
            }
        finally:
            if conn:
                self.release_connection(conn)

    def get_filter_options(self) -> Dict[str, Any]:
        """获取过滤器选项"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # 獲取合作夥伴
            partners_query = """
                SELECT id, partner_name
                FROM partners
                WHERE is_active = true
                ORDER BY partner_name
            """
            cursor.execute(partners_query)
            partners = [dict(row) for row in cursor.fetchall()]
            
            cursor.close()
            
            return {
                'partners': partners,
                'statuses': [
                    {'id': 'confirmed', 'name': '已確認'},
                    {'id': 'pending', 'name': '待確認'},
                    {'id': 'rejected', 'name': '已拒絕'},
                    {'id': 'approved', 'name': '已批准'}
                ]
            }
        except Exception as e:
            logger.error(f"获取过滤器选项失败: {e}")
            return {'partners': [], 'statuses': []}
        finally:
            if conn:
                self.release_connection(conn) 