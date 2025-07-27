
# Cloud SQL查询脚本示例
import mysql.connector
from datetime import datetime

def check_july_24_data():
    # 数据库连接配置
    config = {
        'host': 'your-cloud-sql-host',
        'user': 'your-username',
        'password': 'your-password',
        'database': 'your-database'
    }
    
    try:
        # 连接数据库
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        
        # 查询7/24数据
        query = '''
        SELECT 
            COUNT(*) as total_records,
            COUNT(CASE WHEN DATE(click_date) = '2025-07-24' THEN 1 END) as july_24_clicks,
            COUNT(CASE WHEN DATE(conversion_date) = '2025-07-24' THEN 1 END) as july_24_conversions,
            SUM(CASE WHEN DATE(conversion_date) = '2025-07-24' THEN sale_amount_usd ELSE 0 END) as july_24_revenue
        FROM conversion_data
        WHERE DATE(click_date) = '2025-07-24' 
           OR DATE(conversion_date) = '2025-07-24';
        '''
        
        cursor.execute(query)
        result = cursor.fetchone()
        
        print(f"7/24数据统计:")
        print(f"  • 总记录数: {result[0]}")
        print(f"  • 7/24点击数: {result[1]}")
        print(f"  • 7/24转化数: {result[2]}")
        print(f"  • 7/24收入: ${result[3]:.2f}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"查询失败: {e}")

if __name__ == "__main__":
    check_july_24_data()
