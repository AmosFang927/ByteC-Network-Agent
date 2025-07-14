#!/usr/bin/env python3
"""
数据库管理器
提供统一的数据库连接和数据访问接口
"""

import os
import asyncio
import asyncpg
from typing import List, Dict, Optional, Any
import logging
from datetime import datetime, timedelta, date

# 配置日志
logger = logging.getLogger(__name__)

class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        self.db_config = {
            "host": os.getenv("DB_HOST", "34.124.206.16"),
            "port": int(os.getenv("DB_PORT", "5432")),
            "database": os.getenv("DB_NAME", "postback_db"),
            "user": os.getenv("DB_USER", "postback_admin"),
            "password": os.getenv("DB_PASSWORD", "ByteC2024PostBack_CloudSQL")
        }
        
    async def get_connection(self) -> asyncpg.Connection:
        """获取数据库连接"""
        try:
            conn = await asyncpg.connect(
                host=self.db_config["host"],
                port=self.db_config["port"],
                database=self.db_config["database"],
                user=self.db_config["user"],
                password=self.db_config["password"],
                command_timeout=30
            )
            return conn
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            raise
    
    async def init_pool(self):
        """初始化数据库连接池（兼容性方法）"""
        # 这个方法用于兼容性，实际连接在get_connection方法中处理
        logger.info("✅ DatabaseManager 初始化完成")
        
    async def test_connection(self) -> bool:
        """测试数据库连接"""
        try:
            conn = await self.get_connection()
            await conn.fetchval("SELECT 1")
            await conn.close()
            return True
        except Exception as e:
            logger.error(f"数据库连接测试失败: {e}")
            return False
    
    def _parse_date(self, date_str: str) -> date:
        """将字符串日期转换为date对象"""
        try:
            if isinstance(date_str, str):
                return datetime.strptime(date_str, '%Y-%m-%d').date()
            elif isinstance(date_str, date):
                return date_str
            elif isinstance(date_str, datetime):
                return date_str.date()
            else:
                raise ValueError(f"无法解析日期格式: {date_str}")
        except Exception as e:
            logger.error(f"日期解析失败: {e}")
            raise ValueError(f"日期格式错误: {date_str}，期望格式: YYYY-MM-DD")
    
    # =============================================================================
    # 基础数据查询
    # =============================================================================
    
    async def get_partners(self) -> List[Dict[str, Any]]:
        """获取所有活跃的合作伙伴"""
        try:
            conn = await self.get_connection()
            query = """
                SELECT id, partner_code, partner_name, is_active, created_at
                FROM partners
                WHERE is_active = true
                ORDER BY partner_name
            """
            rows = await conn.fetch(query)
            await conn.close()
            
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"获取合作伙伴失败: {e}")
            return []

    async def get_effective_partners(self) -> List[Dict[str, Any]]:
        """基于实际数据获取有效的合作伙伴选项"""
        try:
            conn = await self.get_connection()
            
            # 基于aff_sub模式统计实际的partner分布
            query = """
                SELECT 
                    CASE 
                        WHEN aff_sub LIKE 'RAMPUP_%' OR aff_sub LIKE 'RPID%' THEN 3
                        WHEN aff_sub LIKE 'OEM%' THEN 1
                        WHEN aff_sub LIKE 'DeepLeaper%' THEN 2
                        WHEN aff_sub LIKE 'MKK%' THEN 6
                        ELSE partner_id
                    END as effective_partner_id,
                    CASE 
                        WHEN aff_sub LIKE 'RAMPUP_%' OR aff_sub LIKE 'RPID%' THEN 'RAMPUP'
                        WHEN aff_sub LIKE 'OEM%' THEN 'ByteC'
                        WHEN aff_sub LIKE 'DeepLeaper%' THEN 'DeepLeaper'
                        WHEN aff_sub LIKE 'MKK%' THEN 'MKK'
                        ELSE 'Other'
                    END as effective_partner_name,
                    COUNT(*) as conversion_count
                FROM conversions
                WHERE aff_sub IS NOT NULL 
                AND event_time >= (CURRENT_DATE - INTERVAL '30 days')
                GROUP BY 1, 2
                HAVING COUNT(*) > 0
                ORDER BY conversion_count DESC
            """
            
            rows = await conn.fetch(query)
            await conn.close()
            
            # 转换为标准格式
            partners = []
            for row in rows:
                partners.append({
                    'id': row['effective_partner_id'],
                    'partner_code': row['effective_partner_name'],
                    'partner_name': row['effective_partner_name'],
                    'is_active': True,
                    'conversion_count': row['conversion_count']
                })
            
            return partners
        except Exception as e:
            logger.error(f"获取有效合作伙伴失败: {e}")
            return []
    
    async def get_platforms(self) -> List[Dict[str, Any]]:
        """获取所有平台"""
        try:
            conn = await self.get_connection()
            query = """
                SELECT id, platform_name, platform_code, is_active
                FROM platforms
                WHERE is_active = true
                ORDER BY platform_name
            """
            rows = await conn.fetch(query)
            await conn.close()
            
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"获取平台失败: {e}")
            return []
    
    # =============================================================================
    # 总览数据
    # =============================================================================
    
    async def get_summary_metrics(self, start_date: str, end_date: str, partner_id: Optional[int] = None) -> Dict[str, Any]:
        """获取总览指标"""
        try:
            conn = await self.get_connection()
            
            # 确保日期格式正确
            from datetime import datetime
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            # 构建查询条件
            where_conditions = [
                "event_time >= $1::date",
                "event_time < ($2::date + INTERVAL '1 day')"
            ]
            params = [start_date, end_date]
            
            if partner_id:
                where_conditions.append(f"partner_id = ${len(params) + 1}")
                params.append(partner_id)
            
            query = f"""
                SELECT 
                    COUNT(*) as total_conversions,
                    SUM(COALESCE(usd_sale_amount, 0)) as total_sales,
                    SUM(COALESCE(usd_payout, 0)) as total_payout,
                    AVG(COALESCE(usd_sale_amount, 0)) as avg_sale_amount,
                    COUNT(DISTINCT partner_id) as unique_partners,
                    COUNT(DISTINCT offer_name) as unique_offers,
                    COUNT(DISTINCT aff_sub) as unique_sub_ids
                FROM conversions
                WHERE {' AND '.join(where_conditions)}
            """
            
            row = await conn.fetchrow(query, *params)
            await conn.close()
            
            return dict(row) if row else {}
        except Exception as e:
            logger.error(f"获取总览指标失败: {e}")
            return {}
    
    async def get_daily_trend(self, start_date: str, end_date: str, partner_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取每日趋势数据"""
        try:
            conn = await self.get_connection()
            
            # 确保日期格式正确
            from datetime import datetime
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            where_conditions = [
                "event_time >= $1::date",
                "event_time < ($2::date + INTERVAL '1 day')"
            ]
            params = [start_date, end_date]
            
            if partner_id:
                where_conditions.append(f"partner_id = ${len(params) + 1}")
                params.append(partner_id)
            
            query = f"""
                SELECT 
                    DATE(event_time) as date,
                    COUNT(*) as conversions,
                    SUM(COALESCE(usd_sale_amount, 0)) as total_sales,
                    SUM(COALESCE(usd_payout, 0)) as total_payout,
                    AVG(COALESCE(usd_sale_amount, 0)) as avg_sale_amount
                FROM conversions
                WHERE {' AND '.join(where_conditions)}
                GROUP BY DATE(event_time)
                ORDER BY date
            """
            
            rows = await conn.fetch(query, *params)
            await conn.close()
            
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"获取每日趋势失败: {e}")
            return []
    
    async def get_hourly_trend(self, start_date: str, end_date: str, partner_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取小时趋势数据"""
        try:
            conn = await self.get_connection()
            
            # 确保日期格式正确
            from datetime import datetime
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            where_conditions = [
                "event_time >= $1::date",
                "event_time < ($2::date + INTERVAL '1 day')"
            ]
            params = [start_date, end_date]
            
            if partner_id:
                where_conditions.append(f"partner_id = ${len(params) + 1}")
                params.append(partner_id)
            
            query = f"""
                SELECT 
                    EXTRACT(HOUR FROM event_time) as hour,
                    COUNT(*) as conversions,
                    SUM(COALESCE(usd_sale_amount, 0)) as total_sales,
                    SUM(COALESCE(usd_payout, 0)) as total_payout
                FROM conversions
                WHERE {' AND '.join(where_conditions)}
                GROUP BY EXTRACT(HOUR FROM event_time)
                ORDER BY hour
            """
            
            rows = await conn.fetch(query, *params)
            await conn.close()
            
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"获取小时趋势失败: {e}")
            return []
    
    # =============================================================================
    # 公司级别数据
    # =============================================================================
    
    async def get_company_performance(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """获取公司级别表现数据"""
        try:
            conn = await self.get_connection()
            
            # 通过offer_name推断公司/地区
            query = """
                SELECT 
                    CASE 
                        WHEN offer_name LIKE '%Shopee%' THEN 'Shopee'
                        WHEN offer_name LIKE '%Lazada%' THEN 'Lazada'
                        WHEN offer_name LIKE '%Grab%' THEN 'Grab'
                        WHEN offer_name LIKE '%TikTok%' THEN 'TikTok'
                        WHEN offer_name LIKE '%Tokopedia%' THEN 'Tokopedia'
                        WHEN offer_name LIKE '%Blibli%' THEN 'Blibli'
                        ELSE 'Others'
                    END as company,
                    COUNT(*) as conversions,
                    SUM(COALESCE(usd_sale_amount, 0)) as total_sales,
                    SUM(COALESCE(usd_payout, 0)) as total_payout,
                    AVG(COALESCE(usd_sale_amount, 0)) as avg_sale_amount,
                    COUNT(DISTINCT offer_name) as unique_offers
                FROM conversions
                WHERE event_time >= $1::date
                    AND event_time < $2::date + INTERVAL '1 day'
                GROUP BY CASE 
                    WHEN offer_name LIKE '%Shopee%' THEN 'Shopee'
                    WHEN offer_name LIKE '%Lazada%' THEN 'Lazada'
                    WHEN offer_name LIKE '%Grab%' THEN 'Grab'
                    WHEN offer_name LIKE '%TikTok%' THEN 'TikTok'
                    WHEN offer_name LIKE '%Tokopedia%' THEN 'Tokopedia'
                    WHEN offer_name LIKE '%Blibli%' THEN 'Blibli'
                    ELSE 'Others'
                END
                ORDER BY conversions DESC
            """
            
            rows = await conn.fetch(query, start_date, end_date)
            await conn.close()
            
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"获取公司级别数据失败: {e}")
            return []
    
    async def get_region_performance(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """获取地区级别表现数据"""
        try:
            conn = await self.get_connection()
            
            query = """
                SELECT 
                    CASE 
                        WHEN offer_name LIKE '%MY%' THEN 'Malaysia'
                        WHEN offer_name LIKE '%ID%' THEN 'Indonesia'
                        WHEN offer_name LIKE '%TH%' THEN 'Thailand'
                        WHEN offer_name LIKE '%SG%' THEN 'Singapore'
                        WHEN offer_name LIKE '%PH%' THEN 'Philippines'
                        WHEN offer_name LIKE '%VN%' THEN 'Vietnam'
                        ELSE 'Others'
                    END as region,
                    COUNT(*) as conversions,
                    SUM(COALESCE(usd_sale_amount, 0)) as total_sales,
                    SUM(COALESCE(usd_payout, 0)) as total_payout,
                    AVG(COALESCE(usd_sale_amount, 0)) as avg_sale_amount
                FROM conversions
                WHERE event_time >= $1::date
                    AND event_time < $2::date + INTERVAL '1 day'
                GROUP BY CASE 
                    WHEN offer_name LIKE '%MY%' THEN 'Malaysia'
                    WHEN offer_name LIKE '%ID%' THEN 'Indonesia'
                    WHEN offer_name LIKE '%TH%' THEN 'Thailand'
                    WHEN offer_name LIKE '%SG%' THEN 'Singapore'
                    WHEN offer_name LIKE '%PH%' THEN 'Philippines'
                    WHEN offer_name LIKE '%VN%' THEN 'Vietnam'
                    ELSE 'Others'
                END
                ORDER BY conversions DESC
            """
            
            rows = await conn.fetch(query, start_date, end_date)
            await conn.close()
            
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"获取地区级别数据失败: {e}")
            return []
    
    # =============================================================================
    # 产品级别数据
    # =============================================================================
    
    async def get_offer_performance(self, start_date: str, end_date: str, partner_id: Optional[int] = None, offer_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取产品级别表现数据"""
        try:
            conn = await self.get_connection()
            
            where_conditions = [
                "event_time >= $1::date",
                "event_time < ($2::date + INTERVAL '1 day')"
            ]
            params = [start_date, end_date]
            
            if partner_id:
                where_conditions.append(f"partner_id = ${len(params) + 1}")
                params.append(partner_id)
            
            if offer_name:
                where_conditions.append(f"offer_name = ${len(params) + 1}")
                params.append(offer_name)
            
            query = f"""
                SELECT 
                    offer_name,
                    COUNT(*) as conversions,
                    SUM(COALESCE(usd_sale_amount, 0)) as total_sales,
                    SUM(COALESCE(usd_payout, 0)) as total_payout,
                    AVG(COALESCE(usd_sale_amount, 0)) as avg_sale_amount,
                    COUNT(DISTINCT aff_sub) as unique_sub_ids,
                    MIN(event_time) as first_conversion,
                    MAX(event_time) as last_conversion
                FROM conversions
                WHERE {' AND '.join(where_conditions)}
                    AND offer_name IS NOT NULL
                GROUP BY offer_name
                ORDER BY conversions DESC
                LIMIT 50
            """
            
            rows = await conn.fetch(query, *params)
            await conn.close()
            
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"获取产品级别数据失败: {e}")
            return []
    
    # =============================================================================
    # 合作伙伴级别数据
    # =============================================================================
    
    async def get_partner_performance(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """获取合作伙伴级别表现数据"""
        try:
            conn = await self.get_connection()
            
            query = """
                SELECT 
                    p.partner_name,
                    p.partner_code,
                    COUNT(c.id) as conversions,
                    SUM(COALESCE(c.usd_sale_amount, 0)) as total_sales,
                    SUM(COALESCE(c.usd_payout, 0)) as total_payout,
                    AVG(COALESCE(c.usd_sale_amount, 0)) as avg_sale_amount,
                    COUNT(DISTINCT c.offer_name) as unique_offers,
                    COUNT(DISTINCT c.aff_sub) as unique_sub_ids
                FROM partners p
                LEFT JOIN conversions c ON p.id = c.partner_id
                    AND c.event_time >= $1::date
                    AND c.event_time < $2::date + INTERVAL '1 day'
                WHERE p.is_active = true
                GROUP BY p.id, p.partner_name, p.partner_code
                ORDER BY conversions DESC
            """
            
            rows = await conn.fetch(query, start_date, end_date)
            await conn.close()
            
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"获取合作伙伴级别数据失败: {e}")
            return []
    
    async def get_sub_id_performance(self, start_date: str, end_date: str, partner_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取Sub ID表现数据"""
        try:
            conn = await self.get_connection()
            
            where_conditions = [
                "event_time >= $1::date",
                "event_time < ($2::date + INTERVAL '1 day')",
                "aff_sub IS NOT NULL",
                "aff_sub != ''"
            ]
            params = [start_date, end_date]
            
            if partner_id:
                where_conditions.append(f"partner_id = ${len(params) + 1}")
                params.append(partner_id)
            
            query = f"""
                SELECT 
                    aff_sub as sub_id,
                    partner_id,
                    COUNT(*) as conversions,
                    SUM(COALESCE(usd_sale_amount, 0)) as total_sales,
                    SUM(COALESCE(usd_payout, 0)) as total_payout,
                    AVG(COALESCE(usd_sale_amount, 0)) as avg_sale_amount,
                    COUNT(DISTINCT offer_name) as unique_offers,
                    MIN(event_time) as first_conversion,
                    MAX(event_time) as last_conversion
                FROM conversions
                WHERE {' AND '.join(where_conditions)}
                GROUP BY aff_sub, partner_id
                ORDER BY conversions DESC
                LIMIT 100
            """
            
            rows = await conn.fetch(query, *params)
            await conn.close()
            
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"获取Sub ID表现数据失败: {e}")
            return []
    
    # =============================================================================
    # 转化报告数据
    # =============================================================================
    
    async def get_conversion_details(self, start_date: str, end_date: str, partner_id: Optional[int] = None, 
                                   page: int = 1, limit: int = 50) -> Dict[str, Any]:
        """获取转化报告详细数据"""
        try:
            conn = await self.get_connection()
            
            # 计算偏移量
            offset = (page - 1) * limit
            
            where_conditions = [
                "c.event_time >= $1::date",
                "c.event_time < ($2::date + INTERVAL '1 day')"
            ]
            params = [start_date, end_date]
            
            if partner_id:
                # 基于partner名称来过滤，而不是partner_id
                if partner_id == 1:  # ByteC
                    where_conditions.append("c.aff_sub LIKE 'OEM%'")
                elif partner_id == 3:  # RAMPUP  
                    where_conditions.append("(c.aff_sub LIKE 'RAMPUP_%' OR c.aff_sub LIKE 'RPID%')")
                elif partner_id == 2:  # DeepLeaper
                    where_conditions.append("c.aff_sub LIKE 'DeepLeaper%'")
                elif partner_id == 6:  # MKK
                    where_conditions.append("c.aff_sub LIKE 'MKK%'")
                else:
                    # 回退到原来的partner_id过滤
                    where_conditions.append(f"c.partner_id = ${len(params) + 1}")
                    params.append(partner_id)
            
            # 获取总数
            count_query = f"""
                SELECT COUNT(*) as total
                FROM conversions c
                WHERE {' AND '.join(where_conditions)}
            """
            
            total_row = await conn.fetchrow(count_query, *params)
            total = total_row['total'] if total_row else 0
            
            # 获取详细数据 - 包含所有字段
            data_query = f"""
                SELECT 
                    c.id,
                    c.conversion_id,
                    c.offer_name,
                    c.usd_sale_amount,
                    c.usd_payout,
                    c.aff_sub,
                    c.event_time,
                    c.created_at,
                    p.partner_name,
                    p.partner_code,
                    pl.platform_name,
                    -- 从raw_data中提取详细字段
                    c.raw_data->>'offer_id' as offer_id,
                    c.raw_data->>'order_id' as order_id,
                    c.raw_data->>'currency' as currency,
                    c.raw_data->>'status' as status,
                    c.raw_data->>'conversion_status' as conversion_status,
                    c.raw_data->>'aff_sub2' as aff_sub2,
                    c.raw_data->>'aff_sub3' as aff_sub3,
                    c.raw_data->>'aff_sub4' as aff_sub4,
                    c.raw_data->>'aff_sub5' as aff_sub5,
                    c.raw_data->'original_data'->>'adv_sub1' as adv_sub1,
                    c.raw_data->'original_data'->>'adv_sub2' as adv_sub2,
                    c.raw_data->'original_data'->>'adv_sub3' as adv_sub3,
                    c.raw_data->'original_data'->>'adv_sub4' as adv_sub4,
                    c.raw_data->'original_data'->>'adv_sub5' as adv_sub5,
                    c.raw_data->>'merchant_id' as merchant_id,
                    c.raw_data->>'datetime_conversion' as conversion_datetime,
                    c.raw_data->'original_data'->>'affiliate_remarks' as affiliate_remarks,
                    c.raw_data->'original_data'->>'base_payout' as base_payout,
                    c.raw_data->'original_data'->>'bonus_payout' as bonus_payout,
                    c.raw_data->>'sale_amount_local' as sale_amount_local,
                    c.raw_data->>'payout_local' as payout_local
                FROM conversions c
                LEFT JOIN partners p ON c.partner_id = p.id  
                LEFT JOIN platforms pl ON c.platform_id = pl.id
                WHERE {' AND '.join(where_conditions)}
                ORDER BY c.event_time DESC
                LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}
            """
            
            params.extend([limit, offset])
            rows = await conn.fetch(data_query, *params)
            await conn.close()
            
            return {
                "records": [dict(row) for row in rows],
                "total": total,
                "page": page,
                "limit": limit,
                "pages": (total + limit - 1) // limit
            }
        except Exception as e:
            logger.error(f"获取转化报告详细数据失败: {e}")
            return {"records": [], "total": 0, "page": page, "limit": limit, "pages": 0}
    
    async def get_detailed_conversions(self, start_date: str, end_date: str, partner_id: Optional[int] = None, 
                                     page: int = 1, limit: int = 100) -> Dict[str, Any]:  # 修改默认值为100
        """获取包含所有字段的详细转化数据"""
        try:
            conn = await self.get_connection()
            
            # 转换字符串日期为date对象
            start_date_obj = self._parse_date(start_date)
            end_date_obj = self._parse_date(end_date)
            
            # 计算偏移量
            offset = (page - 1) * limit
            
            where_conditions = [
                "c.event_time >= $1::date",
                "c.event_time < ($2::date + INTERVAL '1 day')"
            ]
            params = [start_date_obj, end_date_obj]
            
            if partner_id:
                # 基于partner名称来过滤，而不是partner_id
                if partner_id == 1:  # ByteC
                    where_conditions.append("c.aff_sub LIKE 'OEM%'")
                elif partner_id == 3:  # RAMPUP  
                    where_conditions.append("(c.aff_sub LIKE 'RAMPUP_%' OR c.aff_sub LIKE 'RPID%')")
                elif partner_id == 2:  # DeepLeaper
                    where_conditions.append("c.aff_sub LIKE 'DeepLeaper%'")
                elif partner_id == 6:  # MKK
                    where_conditions.append("c.aff_sub LIKE 'MKK%'")
                else:
                    # 回退到原来的partner_id过滤
                    where_conditions.append(f"c.partner_id = ${len(params) + 1}")
                    params.append(partner_id)
            
            # 获取总数
            count_query = f"""
                SELECT COUNT(*) as total
                FROM conversions c
                WHERE {' AND '.join(where_conditions)}
            """
            
            total_row = await conn.fetchrow(count_query, *params)
            total = total_row['total'] if total_row else 0
            
            # 获取详细数据 - 包含所有字段，使用英文名称
            data_query = f"""
                SELECT 
                    c.conversion_id as "Conversion ID",
                    c.event_time as "Conversion Time",
                    c.raw_data->>'offer_id' as "Offer ID",
                    c.offer_name as "Offer Name",
                    c.raw_data->>'order_id' as "Order ID",
                    CASE 
                        WHEN c.aff_sub LIKE 'RAMPUP_%' OR c.aff_sub LIKE 'RPID%' THEN 'RAMPUP'
                        WHEN c.aff_sub LIKE 'OEM%' THEN 'ByteC'
                        WHEN c.aff_sub LIKE 'DeepLeaper%' THEN 'DeepLeaper'
                        WHEN c.aff_sub LIKE 'MKK%' THEN 'MKK'
                        ELSE COALESCE(p.partner_name, 'Unknown')
                    END as "Partner",
                    c.aff_sub as "Source",
                    pl.platform_name as "Platform",
                    c.aff_sub as "Aff Sub 1",
                    c.raw_data->>'aff_sub2' as "Aff Sub 2",
                    c.raw_data->>'aff_sub3' as "Aff Sub 3", 
                    c.raw_data->>'aff_sub4' as "Aff Sub 4",
                    c.raw_data->>'aff_sub5' as "Aff Sub 5",
                    c.raw_data->'original_data'->>'adv_sub1' as "Adv Sub 1",
                    c.raw_data->'original_data'->>'adv_sub2' as "Adv Sub 2",
                    c.raw_data->'original_data'->>'adv_sub3' as "Adv Sub 3",
                    c.raw_data->'original_data'->>'adv_sub4' as "Adv Sub 4",
                    c.raw_data->'original_data'->>'adv_sub5' as "Adv Sub 5",
                    ROUND(c.usd_sale_amount::numeric, 2) as "Sale Amount (USD)",
                    ROUND(c.usd_payout::numeric, 2) as "Payout (USD)",
                    c.raw_data->>'currency' as "Currency",
                    c.raw_data->>'sale_amount_local' as "Sale Amount (Local)",
                    c.raw_data->>'payout_local' as "Payout (Local)",
                    c.raw_data->'original_data'->>'base_payout' as "Base Payout",
                    c.raw_data->'original_data'->>'bonus_payout' as "Bonus Payout",
                    c.raw_data->>'conversion_status' as "Status",
                    c.raw_data->>'merchant_id' as "Merchant ID",
                    c.raw_data->>'datetime_conversion' as "Datetime Conversion",
                    c.raw_data->'original_data'->>'affiliate_remarks' as "Affiliate Remarks",
                    c.created_at as "Created At"
                FROM conversions c
                LEFT JOIN partners p ON c.partner_id = p.id  
                LEFT JOIN platforms pl ON c.platform_id = pl.id
                WHERE {' AND '.join(where_conditions)}
                ORDER BY c.event_time DESC
                LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}
            """
            
            params.extend([limit, offset])
            rows = await conn.fetch(data_query, *params)
            await conn.close()
            
            return {
                "records": [dict(row) for row in rows],
                "total": total,
                "page": page,
                "limit": limit,
                "pages": (total + limit - 1) // limit
            }
        except Exception as e:
            logger.error(f"获取详细转化数据失败: {e}")
            return {"records": [], "total": 0, "page": page, "limit": limit, "pages": 0}
    
    async def get_enhanced_detailed_conversions(self, start_date: str, end_date: str, partner_name: Optional[str] = None, 
                                          page: int = 1, limit: int = 100) -> Dict[str, Any]:
        """获取增强版详细转化数据 - 仅返回用户要求的字段"""
        try:
            conn = await self.get_connection()
            
            # 转换字符串日期为date对象
            start_date_obj = self._parse_date(start_date)
            end_date_obj = self._parse_date(end_date)
            
            # 计算偏移量
            offset = (page - 1) * limit
            
            # 使用datetime_conversion字段进行日期过滤
            where_conditions = [
                "datetime_conversion >= $1::date",
                "datetime_conversion < ($2::date + INTERVAL '1 day')"
            ]
            params = [start_date_obj, end_date_obj]
            
            # 使用partner字段进行过滤
            if partner_name and partner_name != "All Partners":
                where_conditions.append(f"partner = ${len(params) + 1}")
                params.append(partner_name)
            
            # 获取总数和统计信息 - 使用COALESCE处理NULL值
            stats_query = f"""
                SELECT 
                    COUNT(*) as total_conversions,
                    COALESCE(SUM(COALESCE(usd_sale_amount, 0)), 0) as total_sale_amount,
                    COALESCE(AVG(COALESCE(commission_rate, 0)), 0) as avg_commission_rate
                FROM conversions
                WHERE {' AND '.join(where_conditions)}
            """
            
            stats_row = await conn.fetchrow(stats_query, *params)
            total_conversions = stats_row['total_conversions'] if stats_row else 0
            total_sale_amount = float(stats_row['total_sale_amount']) if stats_row and stats_row['total_sale_amount'] else 0
            avg_commission_rate = float(stats_row['avg_commission_rate']) if stats_row and stats_row['avg_commission_rate'] else 0
            
            # 获取详细数据 - 严格限制为11个核心字段
            data_query = f"""
                SELECT 
                    -- 11个核心字段 (Essential Fields View)
                    COALESCE(platform, '') as "platform",
                    COALESCE(partner, '') as "partner",
                    COALESCE(source, '') as "source",
                    COALESCE(conversion_id, '') as "conversion_id",
                    datetime_conversion as "datetime_conversion",
                    COALESCE(offer_name, '') as "offer_name",
                    COALESCE(usd_sale_amount, 0) as "usd_sale_amount",
                    COALESCE(usd_payout, 0) as "usd_payout",
                    COALESCE(aff_sub, '') as "sub_id",
                    COALESCE(aff_sub, '') as "media_id",
                    COALESCE(click_id, '') as "click_id"
                    -- 注意：deliberately excluding all other fields for performance
                FROM conversions
                WHERE {' AND '.join(where_conditions)}
                ORDER BY datetime_conversion DESC
                LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}
            """
            
            params.extend([limit, offset])
            rows = await conn.fetch(data_query, *params)
            await conn.close()
            
            return {
                "records": [dict(row) for row in rows],
                "total": total_conversions,
                "total_sale_amount": total_sale_amount,
                "avg_commission_rate": avg_commission_rate,
                "page": page,
                "limit": limit,
                "pages": (total_conversions + limit - 1) // limit if total_conversions > 0 else 0
            }
        except Exception as e:
            logger.error(f"获取增强版详细转化数据失败: {e}")
            return {
                "records": [], 
                "total": 0, 
                "total_sale_amount": 0,
                "avg_commission_rate": 0,
                "page": page, 
                "limit": limit, 
                "pages": 0
            }

    # =============================================================================
    # 数据钻取
    # =============================================================================
    
    async def drill_down_data(self, data_type: str, filter_key: str, filter_value: str, 
                            start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """数据钻取查询"""
        try:
            conn = await self.get_connection()
            
            # 根据数据类型构建钻取查询
            if data_type == "partner":
                query = """
                    SELECT 
                        c.offer_name,
                        COUNT(*) as conversions,
                        SUM(COALESCE(c.usd_sale_amount, 0)) as total_sales,
                        SUM(COALESCE(c.usd_payout, 0)) as total_payout
                    FROM conversions c
                    JOIN partners p ON c.partner_id = p.id
                    WHERE p.partner_name = $1
                        AND c.event_time >= $2::date
                        AND c.event_time < $3::date + INTERVAL '1 day'
                    GROUP BY c.offer_name
                    ORDER BY conversions DESC
                """
                params = [filter_value, start_date, end_date]
                
            elif data_type == "offer":
                query = """
                    SELECT 
                        DATE(c.event_time) as date,
                        COUNT(*) as conversions,
                        SUM(COALESCE(c.usd_sale_amount, 0)) as total_sales,
                        SUM(COALESCE(c.usd_payout, 0)) as total_payout
                    FROM conversions c
                    WHERE c.offer_name = $1
                        AND c.event_time >= $2::date
                        AND c.event_time < $3::date + INTERVAL '1 day'
                    GROUP BY DATE(c.event_time)
                    ORDER BY date
                """
                params = [filter_value, start_date, end_date]
                
            elif data_type == "sub_id":
                query = """
                    SELECT 
                        c.offer_name,
                        COUNT(*) as conversions,
                        SUM(COALESCE(c.usd_sale_amount, 0)) as total_sales,
                        SUM(COALESCE(c.usd_payout, 0)) as total_payout
                    FROM conversions c
                    WHERE c.aff_sub = $1
                        AND c.event_time >= $2::date
                        AND c.event_time < $3::date + INTERVAL '1 day'
                    GROUP BY c.offer_name
                    ORDER BY conversions DESC
                """
                params = [filter_value, start_date, end_date]
                
            else:
                return []
            
            rows = await conn.fetch(query, *params)
            await conn.close()
            
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"数据钻取失败: {e}")
            return [] 

    async def get_enhanced_partners(self) -> List[Dict[str, Any]]:
        """获取基于conversions表partner字段的合作伙伴列表"""
        try:
            conn = await self.get_connection()
            
            query = """
                SELECT DISTINCT 
                    partner as partner_name,
                    COUNT(*) as conversion_count
                FROM conversions 
                WHERE partner IS NOT NULL AND partner != ''
                GROUP BY partner
                ORDER BY conversion_count DESC
            """
            
            rows = await conn.fetch(query)
            await conn.close()
            
            # 添加"All Partners"选项
            partners = [{"partner_name": "All Partners", "conversion_count": 0}]
            partners.extend([{"partner_name": row["partner_name"], "conversion_count": row["conversion_count"]} for row in rows])
            
            return partners
        except Exception as e:
            logger.error(f"获取增强版合作伙伴列表失败: {e}")
            return [{"partner_name": "All Partners", "conversion_count": 0}] 