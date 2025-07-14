#!/usr/bin/env python3
"""
公司報表管理AI對話系統 - 基於 whodb 整合
Company Manager Agent with whodb Integration
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import requests
import aiohttp
from dataclasses import dataclass
import sys
import os

# 添加項目根目錄到Python路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# 導入現有的數據庫和服務
from agents.dashboard_agent.backend.database_manager import DatabaseManager
from agents.dashboard_agent.backend.dashboard_service import DashboardService

# 配置日志
logger = logging.getLogger(__name__)

@dataclass
class FinancialMetrics:
    """財務指標數據類"""
    revenue: Decimal
    expenses: Decimal
    gross_profit: Decimal
    profit_margin: float
    cash_flow: Decimal
    period_start: datetime
    period_end: datetime

class WhoDBClient:
    """whodb 客戶端接口"""
    
    def __init__(self, base_url: str = "http://localhost:8080", 
                 username: str = None, password: str = None):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.session = None
    
    async def connect(self):
        """連接到whodb"""
        self.session = aiohttp.ClientSession()
        # 實現whodb認證邏輯
        if self.username and self.password:
            await self._authenticate()
    
    async def _authenticate(self):
        """處理whodb認證"""
        auth_data = {
            'username': self.username,
            'password': self.password
        }
        
        try:
            async with self.session.post(f"{self.base_url}/auth", json=auth_data) as response:
                if response.status == 200:
                    logger.info("WhoJDB認證成功")
                else:
                    logger.error(f"WhoJDB認證失敗: {response.status}")
        except Exception as e:
            logger.error(f"WhoJDB認證錯誤: {e}")
    
    async def execute_query(self, sql_query: str) -> Dict[str, Any]:
        """執行SQL查詢"""
        try:
            async with self.session.post(f"{self.base_url}/query", json={'sql': sql_query}) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        'success': True,
                        'data': result,
                        'row_count': len(result) if isinstance(result, list) else 1
                    }
                else:
                    return {
                        'success': False,
                        'error': f"查詢失敗: HTTP {response.status}"
                    }
        except Exception as e:
            return {
                'success': False,
                'error': f"查詢錯誤: {str(e)}"
            }
    
    async def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """獲取表結構"""
        # 實現獲取表結構的邏輯
        pass
    
    async def close(self):
        """關閉連接"""
        if self.session:
            await self.session.close()

class AIQueryParser:
    """AI查詢解析器"""
    
    def __init__(self):
        self.financial_keywords = {
            '收入': ['revenue', 'income', 'sales'],
            '支出': ['expense', 'cost', 'expenditure'],
            '利潤': ['profit', 'margin', 'earning'],
            '現金流': ['cash_flow', 'cashflow'],
            '轉化': ['conversion', 'convert'],
            '合作夥伴': ['partner', 'affiliate'],
            '今天': ['today', 'current_date'],
            '本月': ['this_month', 'current_month'],
            '最近': ['recent', 'latest']
        }
    
    def parse_query(self, user_query: str) -> Dict[str, Any]:
        """解析用戶查詢"""
        query_info = {
            'original_query': user_query,
            'metric_type': self._identify_metric_type(user_query),
            'time_range': self._extract_time_range(user_query),
            'filters': self._extract_filters(user_query)
        }
        
        # 生成SQL查詢
        sql_query = self._generate_sql_template(
            query_info['metric_type'],
            query_info['time_range'],
            query_info['filters']
        )
        
        query_info['sql_query'] = sql_query
        return query_info
    
    def _identify_metric_type(self, query: str) -> str:
        """識別查詢的指標類型"""
        if any(keyword in query for keyword in ['收入', '營收', 'revenue']):
            return 'revenue'
        elif any(keyword in query for keyword in ['轉化', 'conversion']):
            return 'conversion'
        elif any(keyword in query for keyword in ['合作夥伴', 'partner']):
            return 'partner'
        else:
            return 'general'
    
    def _extract_time_range(self, query: str) -> Dict[str, Any]:
        """提取時間範圍"""
        now = datetime.now()
        
        if '今天' in query or 'today' in query:
            return {
                'start_date': now.strftime('%Y-%m-%d'),
                'end_date': now.strftime('%Y-%m-%d'),
                'period': 'today'
            }
        elif '本月' in query or 'this_month' in query:
            start_of_month = now.replace(day=1)
            return {
                'start_date': start_of_month.strftime('%Y-%m-%d'),
                'end_date': now.strftime('%Y-%m-%d'),
                'period': 'this_month'
            }
        elif '最近' in query:
            if '7天' in query or '一週' in query:
                start_date = now - timedelta(days=7)
                return {
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': now.strftime('%Y-%m-%d'),
                    'period': '7_days'
                }
        
        # 預設返回今天
        return {
            'start_date': now.strftime('%Y-%m-%d'),
            'end_date': now.strftime('%Y-%m-%d'),
            'period': 'today'
        }
    
    def _extract_filters(self, query: str) -> Dict[str, Any]:
        """提取過濾條件"""
        filters = {}
        
        # 可以添加更多過濾邏輯
        return filters
    
    def _generate_sql_template(self, metric_type: str, time_range: Dict, filters: Dict) -> str:
        """生成SQL查詢模板"""
        base_table = "conversions"  # 假設主表名
        
        if metric_type == 'revenue':
            return f"""
            SELECT 
                DATE(conversion_time) as date,
                SUM(payout_amount) as revenue,
                COUNT(*) as conversion_count
            FROM {base_table}
            WHERE DATE(conversion_time) BETWEEN '{time_range['start_date']}' AND '{time_range['end_date']}'
            GROUP BY DATE(conversion_time)
            ORDER BY date DESC
            """
        elif metric_type == 'conversion':
            return f"""
            SELECT 
                COUNT(*) as total_conversions,
                SUM(payout_amount) as total_revenue,
                AVG(payout_amount) as avg_payout
            FROM {base_table}
            WHERE DATE(conversion_time) BETWEEN '{time_range['start_date']}' AND '{time_range['end_date']}'
            """
        elif metric_type == 'partner':
            return f"""
            SELECT 
                partner_name,
                COUNT(*) as conversions,
                SUM(payout_amount) as revenue,
                AVG(payout_amount) as avg_payout
            FROM {base_table}
            WHERE DATE(conversion_time) BETWEEN '{time_range['start_date']}' AND '{time_range['end_date']}'
            GROUP BY partner_name
            ORDER BY revenue DESC
            """
        else:
            return f"""
            SELECT 
                COUNT(*) as total_count,
                SUM(payout_amount) as total_amount
            FROM {base_table}
            WHERE DATE(conversion_time) BETWEEN '{time_range['start_date']}' AND '{time_range['end_date']}'
            """

class FinancialCalculator:
    """財務計算器"""
    
    def calculate_metrics(self, query_results: Dict[str, Any]) -> FinancialMetrics:
        """計算財務指標"""
        data = query_results.get('data', [])
        
        if not data:
            return FinancialMetrics(
                revenue=Decimal('0'),
                expenses=Decimal('0'),
                gross_profit=Decimal('0'),
                profit_margin=0.0,
                cash_flow=Decimal('0'),
                period_start=datetime.now(),
                period_end=datetime.now()
            )
        
        # 基本計算邏輯
        total_revenue = sum(Decimal(str(row.get('revenue', 0))) for row in data)
        total_expenses = total_revenue * Decimal('0.1')  # 假設10%的費用
        gross_profit = total_revenue - total_expenses
        profit_margin = float(gross_profit / total_revenue * 100) if total_revenue > 0 else 0.0
        
        return FinancialMetrics(
            revenue=total_revenue,
            expenses=total_expenses,
            gross_profit=gross_profit,
            profit_margin=profit_margin,
            cash_flow=gross_profit,
            period_start=datetime.now(),
            period_end=datetime.now()
        )
    
    def format_results_for_display(self, metrics: FinancialMetrics, query_results: Dict[str, Any]) -> Dict[str, Any]:
        """格式化結果供顯示"""
        return {
            'metrics': {
                'revenue': float(metrics.revenue),
                'expenses': float(metrics.expenses),
                'gross_profit': float(metrics.gross_profit),
                'profit_margin': metrics.profit_margin,
                'cash_flow': float(metrics.cash_flow)
            },
            'raw_data': query_results.get('data', []),
            'summary': f"總收入: ${metrics.revenue:,.2f}, 毛利率: {metrics.profit_margin:.1f}%"
        }

class CompanyManagerAgent:
    """公司管理代理"""
    
    def __init__(self, whodb_config: Dict[str, Any] = None):
        self.whodb_config = whodb_config or {
            'base_url': 'http://localhost:8080',
            'username': 'admin',
            'password': 'password'
        }
        self.whodb_client = WhoDBClient(**self.whodb_config)
        self.query_parser = AIQueryParser()
        self.financial_calculator = FinancialCalculator()
        self.conversation_history = []
        self.db_manager = None
        self.dashboard_service = None
    
    async def initialize(self):
        """初始化代理"""
        try:
            await self.whodb_client.connect()
            logger.info("✅ WhoDB 連接成功")
        except Exception as e:
            logger.warning(f"⚠️ WhoDB 連接失敗，將使用數據庫作為後備: {e}")
        
        # 初始化數據庫管理器
        self.db_manager = DatabaseManager()
        await self.db_manager.init_pool()
        
        # 初始化儀表板服務
        self.dashboard_service = DashboardService(self.db_manager)
    
    async def process_user_query(self, user_query: str, user_id: str = "default") -> Dict[str, Any]:
        """處理用戶查詢"""
        try:
            # 解析查詢
            query_info = self.query_parser.parse_query(user_query)
            
            # 執行SQL查詢
            query_results = await self.whodb_client.execute_query(query_info['sql_query'])
            
            if not query_results['success']:
                return {
                    'success': False,
                    'error': query_results['error'],
                    'sql_query': query_info['sql_query']
                }
            
            # 計算財務指標
            metrics = self.financial_calculator.calculate_metrics(query_results)
            
            # 格式化結果
            formatted_results = self.financial_calculator.format_results_for_display(metrics, query_results)
            
            # 生成AI回應
            ai_response = self._generate_ai_response(user_query, formatted_results)
            
            # 保存到對話歷史
            conversation_entry = {
                'user_id': user_id,
                'timestamp': datetime.now().isoformat(),
                'user_query': user_query,
                'sql_query': query_info['sql_query'],
                'results': formatted_results,
                'ai_response': ai_response
            }
            self.conversation_history.append(conversation_entry)
            
            return {
                'success': True,
                'response': ai_response,
                'sql_query': query_info['sql_query'],
                'data': formatted_results['raw_data'],
                'metrics': formatted_results['metrics'],
                'summary': formatted_results['summary']
            }
            
        except Exception as e:
            logger.error(f"查詢處理錯誤: {e}")
            return {
                'success': False,
                'error': f"查詢處理失敗: {str(e)}"
            }
    
    def _generate_ai_response(self, user_query: str, results: Dict[str, Any]) -> str:
        """生成AI回應"""
        metrics = results['metrics']
        
        if '收入' in user_query:
            return f"根據查詢結果，總收入為 ${metrics['revenue']:,.2f}，毛利率為 {metrics['profit_margin']:.1f}%"
        elif '轉化' in user_query:
            data_count = len(results['raw_data'])
            return f"查詢到 {data_count} 筆轉化記錄，總收入為 ${metrics['revenue']:,.2f}"
        elif '合作夥伴' in user_query:
            return f"合作夥伴分析結果已生成，總收入為 ${metrics['revenue']:,.2f}"
        else:
            return f"查詢完成，{results['summary']}"
    
    async def get_conversation_history(self, user_id: str = "default") -> List[Dict[str, Any]]:
        """獲取對話歷史"""
        return [
            entry for entry in self.conversation_history
            if entry['user_id'] == user_id
        ]
    
    async def get_financial_dashboard_data(self, time_range: str = "week") -> Dict[str, Any]:
        """獲取財務儀表板數據"""
        try:
            if self.dashboard_service:
                # 計算時間範圍
                end_date = datetime.now().date()
                if time_range == "week":
                    start_date = end_date - timedelta(days=7)
                elif time_range == "month":
                    start_date = end_date - timedelta(days=30)
                elif time_range == "quarter":
                    start_date = end_date - timedelta(days=90)
                else:
                    start_date = end_date - timedelta(days=7)
                
                # 調用正確的方法
                summary_data = await self.dashboard_service.get_summary_data(
                    start_date=start_date.isoformat(),
                    end_date=end_date.isoformat()
                )
                
                # 轉換為前端期望的格式
                return {
                    'total_revenue': summary_data.get('total_revenue', 0),
                    'revenue_growth': summary_data.get('revenue_growth', 0),
                    'gross_margin': summary_data.get('avg_payout_per_conversion', 0),
                    'margin_change': 0,  # 暫時沒有變化數據
                    'total_conversions': summary_data.get('total_conversions', 0),
                    'conversion_growth': summary_data.get('conversion_growth', 0),
                    'cash_flow': summary_data.get('total_revenue', 0),  # 使用收入作為現金流
                    'cash_flow_change': 12.4
                }
            else:
                # 返回模擬數據
                return {
                    'total_revenue': 125000,
                    'revenue_growth': 8.5,
                    'gross_margin': 42.3,
                    'margin_change': 2.1,
                    'total_conversions': 1250,
                    'conversion_growth': 15.8,
                    'cash_flow': 28000,
                    'cash_flow_change': 12.4
                }
        except Exception as e:
            logger.error(f"獲取儀表板數據失敗: {e}")
            return {}
    
    async def close(self):
        """關閉代理"""
        await self.whodb_client.close()
        if self.db_manager:
            await self.db_manager.close()

async def main():
    """測試主函數"""
    agent = CompanyManagerAgent()
    await agent.initialize()
    
    # 測試查詢
    result = await agent.process_user_query("今天的收入是多少？")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    await agent.close()

if __name__ == "__main__":
    asyncio.run(main()) 