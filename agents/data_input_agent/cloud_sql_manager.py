#!/usr/bin/env python3
"""
Cloud SQL管理器和查询功能
"""

import mysql.connector
import pandas as pd
from datetime import datetime
import json
import os
from pathlib import Path


class CloudSQLManager:
    """Cloud SQL管理器"""
    
    def __init__(self, config=None):
        """初始化数据库连接"""
        self.config = config or self._get_default_config()
        self.connection = None
        self.cursor = None
    
    def _get_default_config(self):
        """获取默认配置"""
        return {
            'host': os.getenv('CLOUD_SQL_HOST', 'localhost'),
            'user': os.getenv('CLOUD_SQL_USER', 'root'),
            'password': os.getenv('CLOUD_SQL_PASSWORD', ''),
            'database': os.getenv('CLOUD_SQL_DATABASE', 'bytec_network'),
            'port': int(os.getenv('CLOUD_SQL_PORT', 3306))
        }
    
    def connect(self):
        """连接到数据库"""
        try:
            self.connection = mysql.connector.connect(**self.config)
            self.cursor = self.connection.cursor()
            print(f"✅ 成功连接到Cloud SQL: {self.config['host']}:{self.config['port']}")
            return True
        except Exception as e:
            print(f"❌ 连接Cloud SQL失败: {e}")
            return False
    
    def disconnect(self):
        """断开数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        print("🔌 已断开Cloud SQL连接")
    
    def create_table_if_not_exists(self):
        """创建数据表（如果不存在）"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS conversion_data (
            id INT AUTO_INCREMENT PRIMARY KEY,
            conversion_id BIGINT NOT NULL,
            order_id VARCHAR(255),
            sale_amount_usd DECIMAL(10,2),
            publisher_sub_id_1 VARCHAR(255),
            status VARCHAR(50),
            conversion_date DATETIME,
            click_date DATETIME,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_conversion_id (conversion_id),
            INDEX idx_conversion_date (conversion_date),
            INDEX idx_click_date (click_date),
            INDEX idx_status (status),
            INDEX idx_publisher (publisher_sub_id_1)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        
        try:
            self.cursor.execute(create_table_sql)
            self.connection.commit()
            print("✅ 数据表创建/验证成功")
            return True
        except Exception as e:
            print(f"❌ 创建数据表失败: {e}")
            return False
    
    def insert_data(self, df):
        """插入数据到Cloud SQL"""
        if not self.connection:
            print("❌ 数据库未连接")
            return False
        
        # 准备插入数据
        insert_sql = """
        INSERT INTO conversion_data 
        (conversion_id, order_id, sale_amount_usd, publisher_sub_id_1, status, conversion_date, click_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        # 转换数据
        data_to_insert = []
        for _, row in df.iterrows():
            # 处理日期格式
            conversion_date = self._parse_datetime(row.get('Conversion Date', ''))
            click_date = self._parse_datetime(row.get('Click Date', ''))
            
            data_to_insert.append((
                row.get('Conversion ID'),
                row.get('Order ID'),
                row.get('Sale Amount (USD)', 0.0),
                row.get('Publisher Sub ID 1', ''),
                row.get('Status', ''),
                conversion_date,
                click_date
            ))
        
        try:
            # 批量插入
            self.cursor.executemany(insert_sql, data_to_insert)
            self.connection.commit()
            print(f"✅ 成功插入 {len(data_to_insert)} 条记录到Cloud SQL")
            return True
        except Exception as e:
            print(f"❌ 插入数据失败: {e}")
            self.connection.rollback()
            return False
    
    def _parse_datetime(self, date_str):
        """解析日期时间字符串"""
        if pd.isna(date_str) or not date_str:
            return None
        
        try:
            # 尝试多种日期格式
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y/%m/%d %H:%M:%S']:
                try:
                    return datetime.strptime(str(date_str), fmt)
                except ValueError:
                    continue
            return None
        except:
            return None
    
    def query_july_24_data(self):
        """查询7/24数据"""
        if not self.connection:
            print("❌ 数据库未连接")
            return None
        
        query = """
        SELECT 
            COUNT(*) as total_records,
            COUNT(CASE WHEN DATE(click_date) = '2025-07-24' THEN 1 END) as july_24_clicks,
            COUNT(CASE WHEN DATE(conversion_date) = '2025-07-24' THEN 1 END) as july_24_conversions,
            SUM(CASE WHEN DATE(conversion_date) = '2025-07-24' THEN sale_amount_usd ELSE 0 END) as july_24_revenue,
            COUNT(CASE WHEN DATE(click_date) = '2025-07-24' OR DATE(conversion_date) = '2025-07-24' THEN 1 END) as july_24_total
        FROM conversion_data
        WHERE DATE(click_date) = '2025-07-24' 
           OR DATE(conversion_date) = '2025-07-24';
        """
        
        try:
            self.cursor.execute(query)
            result = self.cursor.fetchone()
            
            if result:
                return {
                    'total_records': result[0],
                    'july_24_clicks': result[1],
                    'july_24_conversions': result[2],
                    'july_24_revenue': float(result[3]) if result[3] else 0.0,
                    'july_24_total': result[4]
                }
            else:
                return None
        except Exception as e:
            print(f"❌ 查询7/24数据失败: {e}")
            return None
    
    def get_data_summary(self):
        """获取数据摘要"""
        if not self.connection:
            print("❌ 数据库未连接")
            return None
        
        query = """
        SELECT 
            COUNT(*) as total_records,
            COUNT(DISTINCT conversion_id) as unique_conversions,
            COUNT(DISTINCT publisher_sub_id_1) as unique_publishers,
            SUM(sale_amount_usd) as total_revenue,
            AVG(sale_amount_usd) as avg_revenue,
            MIN(conversion_date) as earliest_date,
            MAX(conversion_date) as latest_date,
            COUNT(CASE WHEN status = 'Pending' THEN 1 END) as pending_count,
            COUNT(CASE WHEN status = 'Approved' THEN 1 END) as approved_count
        FROM conversion_data;
        """
        
        try:
            self.cursor.execute(query)
            result = self.cursor.fetchone()
            
            if result:
                return {
                    'total_records': result[0],
                    'unique_conversions': result[1],
                    'unique_publishers': result[2],
                    'total_revenue': float(result[3]) if result[3] else 0.0,
                    'avg_revenue': float(result[4]) if result[4] else 0.0,
                    'earliest_date': result[5],
                    'latest_date': result[6],
                    'pending_count': result[7],
                    'approved_count': result[8]
                }
            else:
                return None
        except Exception as e:
            print(f"❌ 获取数据摘要失败: {e}")
            return None


def check_july_24_availability():
    """检查7/24数据可用性"""
    print("🔍 检查7/24数据在Cloud SQL中的可用性")
    print("=" * 60)
    
    # 创建管理器
    manager = CloudSQLManager()
    
    # 连接数据库
    if not manager.connect():
        print("❌ 无法连接到Cloud SQL，请检查配置")
        return
    
    try:
        # 创建表
        manager.create_table_if_not_exists()
        
        # 查询7/24数据
        july_24_data = manager.query_july_24_data()
        
        if july_24_data:
            print("\n📊 7/24数据统计:")
            print(f"  • 总记录数: {july_24_data['total_records']}")
            print(f"  • 7/24点击数: {july_24_data['july_24_clicks']}")
            print(f"  • 7/24转化数: {july_24_data['july_24_conversions']}")
            print(f"  • 7/24收入: ${july_24_data['july_24_revenue']:.2f}")
            print(f"  • 7/24总记录: {july_24_data['july_24_total']}")
            
            if july_24_data['july_24_total'] > 0:
                print("✅ 7/24数据在Cloud SQL中可查询")
            else:
                print("❌ 7/24数据在Cloud SQL中不存在")
        else:
            print("❌ 无法查询7/24数据")
        
        # 获取数据摘要
        summary = manager.get_data_summary()
        if summary:
            print("\n📈 数据库摘要:")
            print(f"  • 总记录数: {summary['total_records']}")
            print(f"  • 唯一转化数: {summary['unique_conversions']}")
            print(f"  • 合作伙伴数: {summary['unique_publishers']}")
            print(f"  • 总收入: ${summary['total_revenue']:.2f}")
            print(f"  • 平均收入: ${summary['avg_revenue']:.2f}")
            print(f"  • 日期范围: {summary['earliest_date']} 到 {summary['latest_date']}")
            print(f"  • Pending状态: {summary['pending_count']}")
            print(f"  • Approved状态: {summary['approved_count']}")
    
    finally:
        manager.disconnect()


def insert_sample_data():
    """插入示例数据到Cloud SQL"""
    print("📥 插入示例数据到Cloud SQL")
    print("=" * 50)
    
    # 读取处理后的数据
    try:
        # 查找最新的处理文件
        output_dir = Path("output")
        excel_files = list(output_dir.glob("Processed_*.xlsx"))
        
        if not excel_files:
            print("❌ 未找到处理后的Excel文件")
            return
        
        latest_file = max(excel_files, key=lambda x: x.stat().st_mtime)
        print(f"📁 使用文件: {latest_file.name}")
        
        df = pd.read_excel(latest_file)
        print(f"✅ 读取数据: {len(df)} 行")
        
        # 创建管理器并插入数据
        manager = CloudSQLManager()
        if manager.connect():
            try:
                manager.create_table_if_not_exists()
                if manager.insert_data(df):
                    print("✅ 数据插入成功")
                    
                    # 查询插入结果
                    summary = manager.get_data_summary()
                    if summary:
                        print(f"📊 数据库当前状态: {summary['total_records']} 条记录")
                else:
                    print("❌ 数据插入失败")
            finally:
                manager.disconnect()
        else:
            print("❌ 无法连接到Cloud SQL")
    
    except Exception as e:
        print(f"❌ 插入数据失败: {e}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "check":
            check_july_24_availability()
        elif sys.argv[1] == "insert":
            insert_sample_data()
        else:
            print("用法: python cloud_sql_manager.py [check|insert]")
    else:
        print("🔍 检查7/24数据可用性...")
        check_july_24_availability() 