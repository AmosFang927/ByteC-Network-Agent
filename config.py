#!/usr/bin/env python3
"""
ByteC-Network-Agent 全局配置文件
包含API配置、文件配置、日志配置等
"""

# ByteC-Network-Agent 配置文件
# 版本: 2.0.1 - 修复邮件总金额计算bug (2025-06-20)
# 本次更新修复了Partner邮件中总金额只计算第一个sheet的问题
# 现在正确计算所有sheets的金额总和

import os
from datetime import datetime, timedelta

# =============================================================================
# API配置 - Involve Asia
# =============================================================================
INVOLVE_ASIA_API_SECRET = "Q524XgLnQmrIBiOK8ZD2qmgmQDPbuTqx13tBDWd6BT0="
INVOLVE_ASIA_API_KEY = "general"
INVOLVE_ASIA_BASE_URL = "https://api.involve.asia/api"
INVOLVE_ASIA_AUTH_URL = f"{INVOLVE_ASIA_BASE_URL}/authenticate"
INVOLVE_ASIA_CONVERSIONS_URL = f"{INVOLVE_ASIA_BASE_URL}/conversions/range"

# IATestByteC 平台配置 (測試環境)
# ⚠️ 注意: 這裡應該使用測試環境專用的 API 密鑰，不要與生產環境相同
# 請向 Involve Asia 申請測試環境專用的 API Secret
IATESTBYTEC_API_SECRET = "kr0RvhZ3fI9+M9M1noHPy32kmdMpM4MpVjSIyMsUj8E="  # 🔥 需要更換為測試環境密鑰
IATESTBYTEC_API_KEY = "general"
IATESTBYTEC_BASE_URL = "https://api.involve.asia/api"  # 測試環境可能有不同的端點
IATESTBYTEC_AUTH_URL = f"{IATESTBYTEC_BASE_URL}/authenticate"
IATESTBYTEC_CONVERSIONS_URL = f"{IATESTBYTEC_BASE_URL}/conversions/range"

# 其他平台配置（暫時為空，可以根據需要添加）
LISAIDWEBEYE_API_SECRET = "Q524XgLnQmrIBiOK8ZD2qmgmQDPbuTqx13tBDWd6BT0="  # 暫時使用 IAByteC 的 API_SECRET 進行測試
LISAIDWEBEYE_API_KEY = "general"

LISAIDBYTEC_API_SECRET = ""  # 如需使用請設置  
LISAIDBYTEC_API_KEY = "general"

# =============================================================================
# 业务配置
# =============================================================================
# 默认日期范围 (天数)
DEFAULT_DATE_RANGE = 1  # 默认获取1天数据

# 全局日期设置 (可直接修改这里设置固定日期)
# 使用方法：
# 1. 设置固定日期范围: DEFAULT_START_DATE = "2025-06-17", DEFAULT_END_DATE = "2025-06-17"
# 2. 只设置开始日期: DEFAULT_START_DATE = "2025-06-17", DEFAULT_END_DATE = None (会自动计算结束日期)
# 3. 只设置结束日期: DEFAULT_START_DATE = None, DEFAULT_END_DATE = "2025-06-17" (会自动计算开始日期)  
# 4. 使用动态日期: DEFAULT_START_DATE = None, DEFAULT_END_DATE = None (使用当前日期和DEFAULT_DATE_RANGE)
DEFAULT_START_DATE = None  # 使用动态计算（昨天）
DEFAULT_END_DATE = None    # 使用动态计算（昨天）

# 默认货币
PREFERRED_CURRENCY = "USD"

# API请求配置 - 优化为ByteC长时间任务
REQUEST_TIMEOUT = 30  # 增加到30秒，提升大数据量请求的稳定性
MAX_RETRY_ATTEMPTS = 5  # 增加重试次数，提升容错性
# REQUEST_DELAY 配置移至文件末尾"API代理配置"區段，避免重複定義
RATE_LIMIT_DELAY = 30  # 遇到429错误时的等待时间(秒)

# 增强版API配置 - 资源监控和错误处理
RESOURCE_MONITOR_ENABLED = True  # 启用资源监控
MAX_SKIPPED_PAGES = 10  # 最大跳过页面数，超过此数停止获取
CONNECTIVITY_CHECK_HOST = '8.8.8.8'  # 网络连通性检查主机
CONNECTIVITY_CHECK_PORT = 53  # 网络连通性检查端口
CONNECTIVITY_CHECK_TIMEOUT = 5  # 网络连通性检查超时(秒)
THREAD_TIMEOUT_BUFFER = 5  # 线程超时缓冲时间(秒)

# 分页配置
DEFAULT_PAGE_LIMIT = 100  # API最大支持100條/頁
MAX_RECORDS_LIMIT = None  # 最大记录数限制，None表示不限制，例如设置100表示最多获取100条记录

# Partner过滤配置
TARGET_PARTNER = None  # 指定要处理的Partner，None表示处理所有Partner，例如设置"RAMPUP"只处理RAMPUP

# =============================================================================
# Partner 和 Sources 映射配置
# =============================================================================
# Partner 到 Sources 的映射关系
# Partner 是逻辑概念，不会出现在 aff_sub1 字段中
# Sources 是 aff_sub1 字段的实际值
PARTNER_SOURCES_MAPPING = {
    "RAMPUP": {
        "sources": ["RAMPUP"],  # RAMPUP, RPIDxxx... 等以RAMPUP或RPID开头的
        "pattern": r"^(RAMPUP|RPID.*|AF.*|RPVN.*)",  # 正则表达式匹配模式 - 包含RAMPUP、RPID、AF和RPVN开头的Sources
        "email_enabled": True,  # 邮件发送开关
        #"email_recipients": ["amosfang927@gmail.com"]  # 收件人列表
        "email_recipients": ["max@rampupads.com", "offer@rampupads.com", "bill.zhang@rampupads.com"],
        "show_invalid_warning": False,  # RAMPUP所有轉化status應該沒有invalid，所以summary不用呈現⚠️ Invalid Conversion
        "mockup_multiplier": 0.7  # RAMPUP Partner 使用 70% 的 mockup 倍數
    },
    "FTK": {
        "sources": ["FTK"],  # FTK source
        "pattern": r"^FTK.*",  # 只要以FTK開頭一律歸為FTK（不再排除XIAOMI/VIVO/OPPO/OEM）
        "email_enabled": True,  # 邮件发送开关
        "email_recipients": ["AmosFang927@gmail.com"],  # 收件人列表（请修改为实际的FTK邮箱）
        "show_invalid_warning": True,  # FTK partner保持原有的invalid warning顯示邏輯
        "mockup_multiplier": 0.9  # FTK Partner 使用 90% 的 mockup 倍數
    },
    "DeepLeaper": {
        "sources": ["OPPO", "VIVO", "OEM1", "OEM2", "OEM3", "XIAOMI"],  # 包含OPPO、VIVO、OEM1、OEM2、OEM3、XIAOMI
        "pattern": r".*(OPPO|VIVO|OEM1|OEM2|OEM3|XIAOMI).*",  # 匹配包含OPPO、VIVO、OEM1、OEM2、OEM3、XIAOMI的所有Sources
        "email_enabled": True,  # 邮件发送开关
        "email_recipients": ["sunjiakuo@deepleaper.com", "deepleaper@gmail.com"],  # 收件人列表
        "show_invalid_warning": True,  # 其他partner保持原有的invalid warning顯示邏輯
        "mockup_multiplier": 0.7  # DeepLeaper Partner 使用 70% 的 mockup 倍數
    },
    "TestPartner": {
        "sources": ["TestPartner"],
        "pattern": r"^TestPartner.*",
        "email_enabled": False,  # 邮件发送开关
        "email_recipients": ["AmosFang927+TestPub@gmail.com"],  # 收件人列表
        "show_invalid_warning": True,  # 測試partner保持原有的invalid warning顯示邏輯
        "mockup_multiplier": 1.0  # TestPartner 使用 100% 的 mockup 倍數（不調整）
    },
    "MKK": {
        "sources": ["MKK"],  # MKK source
        "pattern": r"^MKK.*",  # 匹配以MKK开头的所有Sources
        "email_enabled": True,  # 邮件发送开关
        "email_recipients": ["AmosFang927@gmail.com"],  # 收件人列表（请修改为实际的MKK邮箱）
        "show_invalid_warning": True,  # MKK partner保持原有的invalid warning顯示邏輯
        "mockup_multiplier": 1.0  # MKK Partner 使用 100% 的 mockup 倍數（不調整）
    },
    "MP": {
        "sources": ["MP"],  # MP source
        "pattern": r"^MP$",  # 只匹配確切的MP，不匹配其他變體
        "email_enabled": True,  # 邮件发送开关
        "email_recipients": ["AmosFang927@gmail.com"],  # 收件人列表（请修改为实际的MP邮箱）
        "show_invalid_warning": True,  # MP partner保持原有的invalid warning顯示邏輯
        "mockup_multiplier": 0.9  # MP Partner 使用 90% 的 mockup 倍數
    },
    "ByteC": {
        "sources": ["ALL"],  # ByteC 处理所有数据，不限制 Sources
        "pattern": r".*",  # 匹配所有 Sources
        "email_enabled": True,  # 邮件发送开关
        "email_recipients": ["AmosFang927@gmail.com"],  # ByteC Loop邮箱（请修改为实际的 ByteC Loop 邮箱）
        "special_report": True,  # 标记为特殊报表格式
        "report_type": "bytec_summary",  # 特殊报表类型
        "show_invalid_warning": True,  # ByteC partner保持原有的invalid warning顯示邏輯
        "mockup_multiplier": 1.0  # ByteC Partner 使用 100% 的 mockup 倍數（不調整）
    }
}

# =============================================================================
# 文件配置
# =============================================================================
# 输出目录
OUTPUT_DIR = "output"
TEMP_DIR = "temp"

# 文件名模板
PARTNER_REPORT_TEMPLATE = "{partner}_ConversionReport_{start_date}_to_{end_date}.xlsx"
JSON_FILE_TEMPLATE = "conversions_{date}_{timestamp}.json"

# Excel配置
EXCEL_SHEET_NAME = "Conversion Report"

# AllPartners 报表控制配置
GENERATE_ALLPARTNERS_REPORT = False  # 是否生成AllPartners总汇总Excel文件（默认关闭）

# 数据处理配置
MOCKUP_MULTIPLIER = 0.9  # sale_amount调整倍数（默认90%）
REMOVE_COLUMNS = [
    "payout", 
    "base_payout", 
    "bonus_payout",
    "USD Payout",
    "Partner ID",
    "Platform ID",
    "Created At",
    "Source ID"
]  # 要移除的栏位

# DMP Agent passthrough模式下需要移除的字段（用於Reporter Agent）
DMP_PASSTHROUGH_REMOVE_COLUMNS = [
    "Platform",  # Reporter Agent 報表中不需要呈現 Platform 欄位
    "mockup_multiplier", 
    "mockup_applied",
    "USD Payout",
    "USD Reward", 
    "original_usd_sale_amount",
    "Local Reward"
    # 注意：不移除 "Local Sale Amount" 因为Reporter Agent需要它来转换为USD Sale Amount
]  # DMP Agent passthrough模式下要移除的栏位

# =============================================================================
# ByteC 报表配置
# =============================================================================
# ByteC 报表不移除 payout 相关字段，保留完整数据
BYTEC_REMOVE_COLUMNS = []  # ByteC 报表不移除任何栏位
BYTEC_MOCKUP_MULTIPLIER = 1.0  # ByteC 报表不调整金额，使用原始数据
BYTEC_REPORT_TEMPLATE = "ByteC_ConversionReport_{start_date}_to_{end_date}.xlsx"
BYTEC_SHEET_NAME_TEMPLATE = "{start_date} to {end_date}"  # Sheet 名称模板

# =============================================================================
# 佣金率配置 (ByteC 报表专用)
# =============================================================================

# 广告主佣金率配置 (Adv Commission Rate)
# 按平台(Platform)配置，所有平台都使用动态计算(Avg. Commission Rate)
ADV_COMMISSION_RATE_MAPPING = {
    "LisaidByteC": "dynamic",  # 使用Avg. Commission Rate字段值
    "IAByteC": "dynamic"  # 使用Avg. Commission Rate字段值
}

# 发布商佣金率配置 (Pub Commission Rate) 
# 按(Partner, Offer Name)组合配置，单位为百分比
PUB_COMMISSION_RATE_MAPPING = {
    # RAMPUP Partner配置
    ("RAMPUP", "Shopee ID (Media Buyers) - CPS"): 2.5,  # 您指定的2.5%
    ("RAMPUP", "Shopee PH - CPS"): 2.7,  # 您指定的2.7%
    
    # DeepLeaper Partner配置
    ("DeepLeaper", "TikTok Shop ID - CPS"): 1.0,  # 1.0表示1%
    ("DeepLeaper", "Shopee TH - CPS"): 2.0,  # 您示例中的2%
    ("DeepLeaper", "Shopee MY - CPS"): 2.0,  # 您示例中的2%
    ("DeepLeaper", "Shopee PH - CPS"): 2.5,  # 您示例中的2.5%
    ("DeepLeaper", "Shopee ID (Media Buyers) - CPS"): 1.5,  # 您示例中的3%
    ("DeepLeaper", "Shopee VN - CPS"): 3.0,  # 您示例中的3%
    
    # ByteC Partner配置
    ("ByteC", "Shopee ID (Media Buyers) - CPS"): 1.0,  # 默认1%
    
    # MKK Partner配置
    ("MKK", "Shopee ID (Media Buyers) - CPS"): 1.0,  # 默认1%
    ("MKK", "Shopee PH - CPS"): 1.0,  # 默认1%
    ("MKK", "Shopee TH - CPS"): 1.0,  # 默认1%
    ("MKK", "Shopee MY - CPS"): 1.0,  # 默认1%
    ("MKK", "Shopee VN - CPS"): 1.0,  # 默认1%
    ("MKK", "TikTok Shop ID - CPS"): 1.0,  # 默认1%
    
    # MP Partner配置
    ("MP", "Shopee ID (Media Buyers) - CPS"): 1.0,  # 默认1%
    ("MP", "Shopee PH - CPS"): 1.0,  # 默认1%
    ("MP", "Shopee TH - CPS"): 1.0,  # 默认1%
    ("MP", "Shopee MY - CPS"): 1.0,  # 默认1%
    ("MP", "Shopee VN - CPS"): 1.0,  # 默认1%
    ("MP", "TikTok Shop ID - CPS"): 1.0,  # 默认1%
    
    # 其他组合的默认值在get_pub_commission_rate函数中处理
}

# 默认发布商佣金率
DEFAULT_PUB_COMMISSION_RATE = 1.0  # 1%

# API Secret 到 Platform 名称的映射
API_SECRET_TO_PLATFORM = {
    # "boiTXnRgB2B3N7rCictjjti1ufNIzKksSURJHwqtC50=": "LisaidByteC",  # 暂时跳过 LisaidByteC
    "Q524XgLnQmrIBiOK8ZD2qmgmQDPbuTqx13tBDWd6BT0=": "involve_asia"  # IAByteC 映射到 involve_asia 平台
}

# API 到公司的映射关系
API_TO_COMPANY_MAPPING = {
    # "LisaidByteC": "ByteC",  # 暂时跳过 LisaidByteC
    "involve_asia": "ByteC",  # IAByteC 映射到 involve_asia 平台
    "LisaidWebeye": "Webeye"  # LISAIDWebeye 映射到 Webeye 平台
}

# 公司对应的API列表
COMPANY_APIS = {
    "ByteC": ["involve_asia"],  # IAByteC 映射到 involve_asia 平台
    "Webeye": ["LisaidWebeye"]  # LISAIDWebeye 映射到 Webeye 平台
}

# =============================================================================
# Partner 到 API 平台映射配置
# =============================================================================
# Partner 到 API 平台映射配置
# 支持单个API或多个API的配置
PARTNER_API_MAPPING = {
    "RAMPUP": ["involve_asia"],                  # RAMPUP 使用 involve_asia 平台
    "DeepLeaper": ["involve_asia"],              # DeepLeaper 使用 involve_asia 平台
    "ByteC": ["involve_asia"],                   # ByteC 使用 involve_asia 平台
    "TestPartner": ["involve_asia"],             # TestPartner 使用 involve_asia 平台
    "MKK": ["involve_asia"],                     # MKK 使用 involve_asia 平台
    "MP": ["involve_asia"]                       # MP 使用 involve_asia 平台
}

# 默认 API 平台（当 Partner 不在映射中时使用）
DEFAULT_API_PLATFORM = "involve_asia"

# 飞书上传配置
FEISHU_UPLOAD_URL = "https://open.feishu.cn/open-apis/drive/v1/files/upload_all"
FEISHU_MULTIPART_UPLOAD_URL = "https://open.feishu.cn/open-apis/drive/v1/files/upload_prepare"
FEISHU_ACCESS_TOKEN = "your_feishu_access_token_here"  # 自动获取，无需手动设置
FEISHU_PARENT_NODE = "Px2HfS7N8lRcF0d3A5Mcdjzynyc"  # 飞书文件夹节点ID
FEISHU_FILE_TYPE = "sheet"  # 文件类型
FEISHU_MAX_FILE_SIZE_MB = 50  # 飞书上传文件大小限制（MB）- 增加到50MB支持大文件
FEISHU_UPLOAD_ENABLED = True  # 啟用飛書上傳功能

# 飞书认证配置
FEISHU_APP_ID = "cli_a8cc16008c50d00d"
FEISHU_APP_SECRET = "IhAKg48rS0HvPbnGTWe28buXAo3Qs4bx"
FEISHU_AUTH_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"

# =============================================================================
# 邮件配置
# =============================================================================
EMAIL_SENDER = "GaryBu0801@gmail.com"
EMAIL_RECEIVERS = ["AmosFang927@gmail.com"]  # 默认收件人（备用）
EMAIL_PASSWORD = "kxvx hdng fgsf stwr"  # Gmail應用密碼
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ENABLE_TLS = True
EMAIL_INCLUDE_ATTACHMENTS = True  # 是否包含附件
EMAIL_INCLUDE_FEISHU_LINKS = False  # 是否包含飞书链接
EMAIL_SUBJECT_TEMPLATE = "Conversion Report - {date}"  # 邮件主题模板

# 邮件超时和重试配置
EMAIL_SMTP_TIMEOUT = 120  # SMTP连接超时时间(秒) - 增加到120秒处理大附件
EMAIL_MAX_RETRIES = 4     # 最大重试次数 - 增加重试次数
EMAIL_RETRY_DELAY = 10    # 初始重试延迟(秒) - 增加延迟给服务器恢复时间
EMAIL_RETRY_BACKOFF = 1.5 # 指数退避倍数 - 减少退避倍数，避免等待过久

# 邮件自动抄送配置
EMAIL_AUTO_CC = "AmosFang927@gmail.com"  # 自动抄送邮箱，设为None可禁用

# =============================================================================
# 🚀 邮件附件优化配置（階段1+階段2優化）
# =============================================================================

# 📎 附件壓縮配置
EMAIL_AUTO_COMPRESS_ATTACHMENTS = True  # 是否自動壓縮大附件
EMAIL_COMPRESS_THRESHOLD_MB = 5  # 附件壓縮閾值（MB），超過此大小自動壓縮

# ⏱️ 動態超時配置
EMAIL_DYNAMIC_TIMEOUT_ENABLED = True  # 是否啟用動態超時調整
EMAIL_SMALL_FILE_TIMEOUT = 120   # 小文件超時時間（<5MB）
EMAIL_MEDIUM_FILE_TIMEOUT = 600  # 中等文件超時時間（5-15MB）
EMAIL_LARGE_FILE_TIMEOUT = 600   # 大文件超時時間（>15MB）

# ☁️ 智能降級策略配置
EMAIL_SMART_FALLBACK_ENABLED = True  # 是否啟用智能降級策略
EMAIL_FALLBACK_SIZE_THRESHOLD_MB = 15  # 文件大小閾值（MB），超過此大小觸發降級
EMAIL_FALLBACK_RETRY_THRESHOLD = 2    # 重試次數閾值，超過此次數觸發降級

# 📧 郵件模式選擇（全局設置）
# 可選值:
# - "attachment"     : 總是嘗試發送附件（使用壓縮和重試優化）
# - "cloud_link"     : 總是使用雲端鏈接模式（無附件，提供飛書鏈接）
# - "smart_hybrid"   : 智能混合模式（先嘗試附件，失敗後降級到雲端鏈接）
EMAIL_DELIVERY_MODE = "attachment"  # 使用附件模式

# 雲端鏈接模式配置
EMAIL_CLOUD_LINK_PROVIDER = "feishu"  # 雲端提供商：feishu（飛書）
EMAIL_CLOUD_LINK_INCLUDE_DIRECT_LINKS = False  # 是否在郵件中包含直接下載鏈接（需要額外開發）

# Partner邮件配置（从PARTNER_SOURCES_MAPPING动态生成）
# 这些配置现在从 PARTNER_SOURCES_MAPPING 中的 email_enabled 和 email_recipients 字段获取
# 注意：实际的配置值将在模块加载完成后动态生成，这里只是占位符
PARTNER_EMAIL_ENABLED = {}  # 将在模块末尾动态生成
PARTNER_EMAIL_MAPPING = {}  # 将在模块末尾动态生成

# 保持向后兼容性的别名
PUB_EMAIL_ENABLED = PARTNER_EMAIL_ENABLED  # 兼容性别名
PUB_EMAIL_MAPPING = PARTNER_EMAIL_MAPPING   # 兼容性别名

# =============================================================================
# 定时任务配置
# =============================================================================
SCHEDULE_ENABLED = True
DAILY_REPORT_TIME = "12:00"  # 每日发送时间（24小时制）
TIMEZONE = "Asia/Shanghai"  # 时区设置

# =============================================================================
# 日志配置
# =============================================================================
LOG_LEVEL = "INFO"
LOG_FORMAT = "[{timestamp}] {level}: {message}"
LOG_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"

# =============================================================================
# 辅助函数
# =============================================================================
def get_partner_filename(partner_name, start_date, end_date):
    """生成Partner报告文件名"""
    return PARTNER_REPORT_TEMPLATE.format(
        partner=partner_name,
        start_date=start_date,
        end_date=end_date
    )

def get_sources_for_partner(partner_name):
    """获取Partner对应的Sources列表"""
    partner_config = PARTNER_SOURCES_MAPPING.get(partner_name, {})
    return partner_config.get('sources', [])

def get_pattern_for_partner(partner_name):
    """获取Partner对应的正则表达式模式"""
    partner_config = PARTNER_SOURCES_MAPPING.get(partner_name, {})
    return partner_config.get('pattern', '')

def match_source_to_partner(source_name):
    """將 Source 映射到對應的 Partner（大小寫不敏感）"""
    import re
    if not source_name:
        return source_name or 'Unknown'

    # 規範化大小寫
    src_lower = str(source_name).strip()

    for partner, config in PARTNER_SOURCES_MAPPING.items():
        # 先檢查 sources 列表（大小寫不敏感）
        sources_list = config.get('sources', [])
        if any(src_lower.lower() == s.lower() for s in sources_list):
            return partner

        # 再檢查正則表達式（大小寫不敏感）
        pattern = config.get('pattern', '')
        if pattern and re.match(pattern, src_lower, flags=re.IGNORECASE):
            return partner

    # 如果沒有匹配到，返回原始 source_name 作為 partner
    return source_name

def get_partner_email_config(partner_name):
    """获取Partner的邮件配置"""
    partner_config = PARTNER_SOURCES_MAPPING.get(partner_name, {})
    return {
        'enabled': partner_config.get('email_enabled', False),
        'recipients': partner_config.get('email_recipients', [])
    }

def get_all_partner_email_enabled():
    """获取所有Partner的邮件开关配置（向后兼容性）"""
    return {partner: config.get('email_enabled', False) 
            for partner, config in PARTNER_SOURCES_MAPPING.items()}

def get_all_partner_email_mapping():
    """获取所有Partner的收件人映射（向后兼容性）"""
    return {partner: config.get('email_recipients', []) 
            for partner, config in PARTNER_SOURCES_MAPPING.items()}

def get_target_partners():
    """获取要处理的Partner列表"""
    if TARGET_PARTNER is None:
        return list(PARTNER_SOURCES_MAPPING.keys())
    elif isinstance(TARGET_PARTNER, list):
        # 处理列表格式的TARGET_PARTNER
        valid_partners = []
        for partner in TARGET_PARTNER:
            if partner in PARTNER_SOURCES_MAPPING:
                valid_partners.append(partner)
            else:
                print(f"⚠️ 警告: 指定的Partner '{partner}' 不存在，跳过")
        
        if not valid_partners:
            print("⚠️ 警告: 所有指定的Partner都不存在，将处理所有Partner")
            return list(PARTNER_SOURCES_MAPPING.keys())
        return valid_partners
    elif TARGET_PARTNER in PARTNER_SOURCES_MAPPING:
        return [TARGET_PARTNER]
    else:
        print(f"⚠️ 警告: 指定的Partner '{TARGET_PARTNER}' 不存在，将处理所有Partner")
        return list(PARTNER_SOURCES_MAPPING.keys())

def is_partner_enabled(partner_name):
    """检查Partner是否在处理范围内"""
    if TARGET_PARTNER is None:
        return True
    elif isinstance(TARGET_PARTNER, list):
        return partner_name in TARGET_PARTNER
    else:
        return TARGET_PARTNER == partner_name

def get_default_date_range():
    """获取默认日期范围"""
    # 如果设置了全局日期，使用全局设置
    if DEFAULT_START_DATE and DEFAULT_END_DATE:
        return DEFAULT_START_DATE, DEFAULT_END_DATE
    
    # 如果只设置了结束日期，使用结束日期和默认范围计算开始日期
    if DEFAULT_END_DATE:
        end_date = datetime.strptime(DEFAULT_END_DATE, "%Y-%m-%d")
        start_date = end_date - timedelta(days=DEFAULT_DATE_RANGE)
        return start_date.strftime("%Y-%m-%d"), DEFAULT_END_DATE
    
    # 如果只设置了开始日期，使用开始日期和默认范围计算结束日期
    if DEFAULT_START_DATE:
        start_date = datetime.strptime(DEFAULT_START_DATE, "%Y-%m-%d")
        end_date = start_date + timedelta(days=DEFAULT_DATE_RANGE)
        return DEFAULT_START_DATE, end_date.strftime("%Y-%m-%d")
    
    # 都没设置，使用动态计算（昨天的数据）
    yesterday = datetime.now() - timedelta(days=1)
    return yesterday.strftime("%Y-%m-%d"), yesterday.strftime("%Y-%m-%d")

def get_output_filename(date_str=None):
    """生成输出文件名（兼容性保留）"""
    if date_str is None:
        # 使用默认日期范围的结束日期作为文件名日期
        start_date, end_date = get_default_date_range()
        return get_partner_filename("UnknownPartner", start_date, end_date)
    return get_partner_filename("UnknownPartner", date_str, date_str)

def get_json_filename():
    """生成JSON文件名"""
    date_str = datetime.now().strftime("%Y%m%d")
    timestamp = datetime.now().strftime("%H%M%S")
    return JSON_FILE_TEMPLATE.format(date=date_str, timestamp=timestamp)

def ensure_output_dirs():
    """确保输出目录存在"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)

# =============================================================================
# 环境变量支持
# =============================================================================
def get_env_config():
    """从环境变量获取配置（可选）"""
    return {
        'api_secret': os.getenv('INVOLVE_ASIA_API_SECRET', INVOLVE_ASIA_API_SECRET),
        'api_key': os.getenv('INVOLVE_ASIA_API_KEY', INVOLVE_ASIA_API_KEY),
        'preferred_currency': os.getenv('PREFERRED_CURRENCY', PREFERRED_CURRENCY)
    } 

# =============================================================================
# 动态配置生成（在所有函数定义完成后执行）
# =============================================================================
# 从 PARTNER_SOURCES_MAPPING 动态生成邮件配置
PARTNER_EMAIL_ENABLED.update(get_all_partner_email_enabled())
PARTNER_EMAIL_MAPPING.update(get_all_partner_email_mapping())

# 更新向后兼容性别名
PUB_EMAIL_ENABLED = PARTNER_EMAIL_ENABLED
PUB_EMAIL_MAPPING = PARTNER_EMAIL_MAPPING

def get_bytec_filename(start_date, end_date):
    """生成 ByteC 报告文件名"""
    return BYTEC_REPORT_TEMPLATE.format(
        start_date=start_date,
        end_date=end_date
    )

def is_bytec_partner(partner_name):
    """检查是否为 ByteC Partner"""
    return partner_name == "ByteC"

def is_special_report_partner(partner_name):
    """检查是否为特殊报表类型的 Partner"""
    partner_config = PARTNER_SOURCES_MAPPING.get(partner_name, {})
    return partner_config.get('special_report', False)

def get_partner_report_type(partner_name):
    """获取 Partner 的报表类型"""
    partner_config = PARTNER_SOURCES_MAPPING.get(partner_name, {})
    return partner_config.get('report_type', 'standard')

def get_partner_invalid_warning_config(partner_name):
    """获取 Partner 的 Invalid Conversion 警告配置"""
    partner_config = PARTNER_SOURCES_MAPPING.get(partner_name, {})
    return partner_config.get('show_invalid_warning', True)  # 默認顯示警告

def get_partner_mockup_multiplier(partner_name):
    """获取 Partner 的 mockup 倍数配置（大小寫不敏感）"""
    if not partner_name:
        return 1.0
    
    # 先嘗試直接匹配
    partner_config = PARTNER_SOURCES_MAPPING.get(partner_name, {})
    if 'mockup_multiplier' in partner_config:
        return partner_config.get('mockup_multiplier', 1.0)
    
    # 如果直接匹配失敗，嘗試大小寫不敏感匹配
    partner_name_lower = partner_name.lower()
    for config_key, config_data in PARTNER_SOURCES_MAPPING.items():
        if config_key.lower() == partner_name_lower:
            return config_data.get('mockup_multiplier', 1.0)
    
    # 如果都沒有匹配，返回默認值
    return 1.0  # 默認使用 100%（新加入的 partner 不調整）

def get_platform_from_api_secret(api_secret):
    """根据 API Secret 获取平台名称"""
    return API_SECRET_TO_PLATFORM.get(api_secret, "Unknown Platform")

def get_company_apis(company_name):
    """获取公司对应的所有API列表"""
    return COMPANY_APIS.get(company_name, [])

def get_api_company(api_name):
    """获取API对应的公司"""
    return API_TO_COMPANY_MAPPING.get(api_name, "Unknown")

def is_bytec_company_api(api_name):
    """检查API是否属于ByteC公司"""
    return get_api_company(api_name) == "ByteC"

def get_adv_commission_rate(platform_name, avg_commission_rate=None):
    """
    获取广告主佣金率 (Adv Commission Rate)
    
    Args:
        platform_name: 平台名称 (LisaidByteC, IAByteC等)
        avg_commission_rate: 当前记录的平均佣金率 (仅IAByteC平台需要)
    
    Returns:
        float: 广告主佣金率 (百分比)
    """
    if platform_name in ADV_COMMISSION_RATE_MAPPING:
        rate_config = ADV_COMMISSION_RATE_MAPPING[platform_name]
        if rate_config == "dynamic":
            # IAByteC使用动态值(Avg. Commission Rate)
            return avg_commission_rate if avg_commission_rate is not None else 0.0
        else:
            # LisaidByteC使用固定值
            return float(rate_config)
    else:
        # 未配置的平台使用默认值0%
        return 0.0

def get_partner_api_platforms(partner_name):
    """
    获取 Partner 对应的 API 平台列表
    
    Args:
        partner_name: Partner名称
    
    Returns:
        list: API 平台名称列表
    """
    apis = PARTNER_API_MAPPING.get(partner_name, [DEFAULT_API_PLATFORM])
    # 确保返回的是列表
    if isinstance(apis, str):
        return [apis]
    return apis

def get_partner_api_platform(partner_name):
    """
    获取 Partner 对应的主要 API 平台（第一个）
    保持向后兼容性
    
    Args:
        partner_name: Partner名称
    
    Returns:
        str: 主要 API 平台名称
    """
    apis = get_partner_api_platforms(partner_name)
    return apis[0] if apis else DEFAULT_API_PLATFORM

def get_required_apis_for_partners(partner_list):
    """
    根据 Partner 列表获取需要调用的所有 API 平台
    
    Args:
        partner_list: Partner名称列表
    
    Returns:
        list: 需要调用的 API 平台名称列表（去重）
    """
    if not partner_list:
        return [DEFAULT_API_PLATFORM]
    
    required_apis = set()
    for partner in partner_list:
        apis = get_partner_api_platforms(partner)
        required_apis.update(apis)
    
    return list(required_apis)

def get_preferred_api_for_partners(partner_list):
    """
    根据 Partner 列表获取优先使用的 API 平台
    如果需要多个API，返回第一个（为了向后兼容）
    
    Args:
        partner_list: Partner名称列表
    
    Returns:
        str: 推荐的 API 平台名称
    """
    required_apis = get_required_apis_for_partners(partner_list)
    return required_apis[0] if required_apis else DEFAULT_API_PLATFORM

def needs_multi_api_for_partners(partner_list):
    """
    检查指定的 Partner 列表是否需要调用多个 API
    
    Args:
        partner_list: Partner名称列表
    
    Returns:
        bool: 是否需要多个API
        list: 需要的API列表
    """
    required_apis = get_required_apis_for_partners(partner_list)
    return len(required_apis) > 1, required_apis

def get_pub_commission_rate(partner_name, offer_name):
    """
    获取发布商佣金率 (Pub Commission Rate)
    
    Args:
        partner_name: Partner名称
        offer_name: Offer名称
    
    Returns:
        float: 发布商佣金率 (百分比)
    """
    mapping_key = (partner_name, offer_name)
    if mapping_key in PUB_COMMISSION_RATE_MAPPING:
        return float(PUB_COMMISSION_RATE_MAPPING[mapping_key])
    else:
        # 未配置的组合使用默认值
        return float(DEFAULT_PUB_COMMISSION_RATE)

# =============================================================================
# 異步I/O配置
# =============================================================================

# =============================================================================
# ⚡ 智能模式切换配置 - 方案1优化
# =============================================================================

# 🧠 智能并发模式配置（新）
ENABLE_BATCH_CONCURRENT = True   # 默认启用高性能并发模式 (85-92%性能提升)
ENABLE_ASYNC_MODE = True          # 默认启用异步模式，提升I/O效率
FORCE_SEQUENTIAL_MODE = False     # 默认关闭强制顺序模式

# 💱 Currency验证模式配置（新）
CURRENCY_VERIFICATION_MODE = False  # 是否启用currency验证模式（单线程+验证）
# 当CURRENCY_VERIFICATION_MODE=True时，自动切换到单线程模式确保currency参数验证

# ⚡ 性能优化配置
MAX_CONCURRENT_REQUESTS = 12     # 最大并发请求数（当ENABLE_BATCH_CONCURRENT=True时生效）
CURRENCY_MODE_CONCURRENT = 1     # Currency验证模式下的并发数（确保验证准确性）

# =============================================================================
# API Agent 配置
# =============================================================================

# 🚀 API Agent 默认并发配置
API_AGENT_DEFAULT_CONCURRENT = 1  # API Agent 默认并发数 (1=单线程，推荐用于稳定性)
API_AGENT_ENABLE_BATCH_CONCURRENT = False  # API Agent 默认关闭批量并发模式
API_AGENT_FORCE_SEQUENTIAL_MODE = True     # API Agent 默认强制顺序模式
API_AGENT_ENABLE_ASYNC_MODE = True         # API Agent 默认启用异步模式

# 🔧 API Agent 性能配置
API_AGENT_MAX_CONCURRENT_REQUESTS = 1      # API Agent 最大并发请求数
API_AGENT_REQUEST_TIMEOUT = 30              # API Agent 请求超时时间(秒)
API_AGENT_MAX_RETRY_ATTEMPTS = 5           # API Agent 最大重试次数
API_AGENT_RATE_LIMIT_DELAY = 30            # API Agent 速率限制延迟(秒)

# 📊 API Agent 监控配置
API_AGENT_ENABLE_PERFORMANCE_MONITORING = True  # 启用性能监控
API_AGENT_ENABLE_PROGRESS_TRACKING = True       # 启用进度跟踪
API_AGENT_ENABLE_ETA_CALCULATION = True         # 启用ETA计算

# 🔄 API Agent 智能模式配置
API_AGENT_CURRENCY_VERIFICATION_MODE = False    # Currency验证模式
API_AGENT_ENABLE_CLIENT_SIDE_CURRENCY_FILTER = True  # 启用客户端货币过滤

# HTTP連接池配置
HTTP_MAX_KEEPALIVE_CONNECTIONS = 10
HTTP_MAX_CONNECTIONS = 20
HTTP_KEEPALIVE_EXPIRY = 30

# 異步批次處理配置 - 針對超時優化
ASYNC_BATCH_SIZE = 15  # 每批最多處理的頁面數，提高吞吐量

# 性能監控配置
ENABLE_ASYNC_PERFORMANCE_MONITORING = True

# 超時優化配置
ENABLE_FAST_MODE = True  # 啟用快速模式，減少延遲
REDUCE_LOGGING_IN_PRODUCTION = True  # 減少生產環境日誌輸出
OPTIMIZE_FOR_CLOUD_RUN = True  # Cloud Run優化模式

# =============================================================================
# 數據來源分離配置 (Data Source Separation)
# =============================================================================

# 數據來源表映射配置
DATA_SOURCE_TABLES = {
    'api': 'conversions_api',           # API 數據專用表
    'postback': 'conversions_postback', # Postback 數據專用表
    'unified': 'conversions_api'        # 統一視圖表 - 改為使用conversions_api
}

# 默認查詢來源 (API 優先)
DEFAULT_QUERY_SOURCE = 'api'  # 可選值: 'api', 'postback', 'unified'

# 平台到數據來源的映射
PLATFORM_DATA_SOURCE_MAPPING = {
    'IAByteC': 'api',        # Involve Asia ByteC API 數據
    'IATestByteC': 'api',    # Involve Asia Test ByteC API 數據
    'Event_Involve': 'postback',  # Involve Event Postback 數據
    'involve_asia': 'api'    # 通用 Involve Asia API 數據
}

# 是否啟用數據來源分離
ENABLE_DATA_SOURCE_SEPARATION = True

# 查詢來源優先級 (按優先級排序)
QUERY_SOURCE_PRIORITY = ['api', 'postback', 'unified']

# 是否支持多來源聯合查詢
ENABLE_MULTI_SOURCE_QUERY = False  # 暫時禁用，優先使用單一來源

# 數據遷移配置
DATA_MIGRATION_ENABLED = False  # 是否啟用現有數據遷移
MIGRATION_BATCH_SIZE = 1000      # 數據遷移批次大小

# =============================================================================
# Phase 2 & 3: 新功能Feature Flags (風險控制)
# =============================================================================

# 🔄 Passthrough模式控制
ENABLE_PASSTHROUGH_MODE = True              # 總開關：是否啟用passthrough功能
PASSTHROUGH_DEFAULT_ENABLED = False         # 默認是否啟用passthrough模式
PASSTHROUGH_SKIP_CLOUD_SQL = True          # passthrough模式是否跳過Cloud SQL插入
PASSTHROUGH_ENABLE_DATA_FORWARDING = True  # passthrough模式是否啟用數據轉發

# 🔗 Agent間調用控制
ENABLE_AGENT_INTER_CALLING = True          # 總開關：是否啟用agent間調用
AGENT_CALLING_DEFAULT_TIMEOUT = 600        # agent調用默認超時時間(秒)
AGENT_CALLING_MAX_RETRIES = 3              # agent調用最大重試次數

# 📊 Reporter Agent調用控制
ENABLE_REPORTER_AGENT_CALLING = True       # 是否啟用Reporter Agent調用
REPORTER_AGENT_AUTO_GENERATE = False       # 是否自動生成報告
REPORTER_AGENT_DEFAULT_FORMAT = 'json'     # 默認報告格式

# 📈 Data Input Agent擴展控制
ENABLE_DATA_INPUT_BATCH_PROCESSING = True  # 是否啟用批量文件處理
DATA_INPUT_MAX_BATCH_SIZE = 10             # 批量處理最大文件數
DATA_INPUT_ENABLE_ANALYSIS_ONLY = True     # 是否啟用僅分析模式

# 🛡️ 向後兼容性保護
MAINTAIN_BACKWARD_COMPATIBILITY = True     # 強制保持向後兼容性
LEGACY_MODE_SUPPORT = True                 # 是否支持舊版模式
FEATURE_FLAGS_VALIDATION = True            # 是否啟用feature flags驗證

def get_table_name_for_platform(platform_name):
    """根據平台名稱獲取對應的表名"""
    data_source = PLATFORM_DATA_SOURCE_MAPPING.get(platform_name, 'unified')
    return DATA_SOURCE_TABLES.get(data_source, 'conversions')

def get_table_name_for_source(data_source):
    """根據數據來源獲取表名"""
    return DATA_SOURCE_TABLES.get(data_source, 'conversions')

def get_default_query_table():
    """獲取默認查詢表名"""
    return DATA_SOURCE_TABLES.get(DEFAULT_QUERY_SOURCE, 'conversions_api')

def get_data_source_for_platform(platform_name):
    """根據平台名稱獲取數據來源類型"""
    return PLATFORM_DATA_SOURCE_MAPPING.get(platform_name, 'unified')

def should_use_separate_tables():
    """是否啟用數據來源分離"""
    return ENABLE_DATA_SOURCE_SEPARATION

def get_async_config():
    """獲取異步配置"""
    return {
        'max_concurrent_requests': MAX_CONCURRENT_REQUESTS if ENABLE_BATCH_CONCURRENT else 1,
        'http_max_keepalive_connections': HTTP_MAX_KEEPALIVE_CONNECTIONS,
        'http_max_connections': HTTP_MAX_CONNECTIONS,
        'http_keepalive_expiry': HTTP_KEEPALIVE_EXPIRY,
        'async_batch_size': ASYNC_BATCH_SIZE if ENABLE_BATCH_CONCURRENT else 1,
        'enable_performance_monitoring': ENABLE_ASYNC_PERFORMANCE_MONITORING,
        'enable_batch_concurrent': ENABLE_BATCH_CONCURRENT,
        'enable_async_mode': ENABLE_ASYNC_MODE,
        'force_sequential_mode': FORCE_SEQUENTIAL_MODE
    }

def get_api_agent_config():
    """獲取 API Agent 配置"""
    return {
        'default_concurrent': API_AGENT_DEFAULT_CONCURRENT,
        'enable_batch_concurrent': API_AGENT_ENABLE_BATCH_CONCURRENT,
        'force_sequential_mode': API_AGENT_FORCE_SEQUENTIAL_MODE,
        'enable_async_mode': API_AGENT_ENABLE_ASYNC_MODE,
        'max_concurrent_requests': API_AGENT_MAX_CONCURRENT_REQUESTS,
        'request_timeout': API_AGENT_REQUEST_TIMEOUT,
        'max_retry_attempts': API_AGENT_MAX_RETRY_ATTEMPTS,
        'rate_limit_delay': API_AGENT_RATE_LIMIT_DELAY,
        'enable_performance_monitoring': API_AGENT_ENABLE_PERFORMANCE_MONITORING,
        'enable_progress_tracking': API_AGENT_ENABLE_PROGRESS_TRACKING,
        'enable_eta_calculation': API_AGENT_ENABLE_ETA_CALCULATION,
        'currency_verification_mode': API_AGENT_CURRENCY_VERIFICATION_MODE,
        'enable_client_side_currency_filter': API_AGENT_ENABLE_CLIENT_SIDE_CURRENCY_FILTER
    }

def get_api_agent_concurrent_config():
    """獲取 API Agent 並發配置"""
    return {
        'concurrent': API_AGENT_DEFAULT_CONCURRENT,
        'enable_batch_concurrent': API_AGENT_ENABLE_BATCH_CONCURRENT,
        'force_sequential_mode': API_AGENT_FORCE_SEQUENTIAL_MODE,
        'max_concurrent_requests': API_AGENT_MAX_CONCURRENT_REQUESTS
    }

def should_use_async_api():
    """判断是否应该使用异步API"""
    # 默认启用异步API，除非明确禁用
    return os.getenv('USE_ASYNC_API', 'true').lower() in ('true', '1', 'yes')

def get_optimal_concurrent_requests(total_pages):
    """根据总页数获取最优并发数"""
    if total_pages <= 5:
        return min(total_pages, 3)
    elif total_pages <= 20:
        return min(total_pages // 2, MAX_CONCURRENT_REQUESTS)
    else:
        return MAX_CONCURRENT_REQUESTS

# =============================================================================
# API代理配置
# =============================================================================

# 自定义分页大小
# ⚡ 修正: API最大支持100條/頁 (遵循API限制)
DEFAULT_PAGE_LIMIT = 100  # API最大支持100條/頁

# 请求间隔配置
REQUEST_DELAY = 0.5  # 调整请求间隔

# =============================================================================
# 數據插入配置
# =============================================================================

# ⚡ 優化: 數據庫批量插入大小
DATABASE_BATCH_SIZE = 25   # 超级优化: 使用超小批次大小确保最高连接稳定性

# =============================================================================
# 性能監控配置
# =============================================================================

# ⚡ 優化: 啟用性能監控和統計
ENABLE_PERFORMANCE_STATS = True
ENABLE_PROGRESS_TRACKING = True
ENABLE_ETA_CALCULATION = True

# =============================================================================
# 錯誤處理配置
# =============================================================================

# ⚡ 優化: 提升重試機制
MAX_RETRIES = 5          # 增加重試次數
RETRY_DELAY = 2          # 重試間隔
TIMEOUT_SECONDS = 30     # 請求超時時間

# 客戶端貨幣過濾配置
ENABLE_CLIENT_SIDE_CURRENCY_FILTER = True  # 啟用客戶端USD過濾

# =============================================================================
# TikTok Shop API 配置
# =============================================================================

# TikTok Shop API 憑證
TIKTOK_APP_KEY = "6fadfj6jgv4nv"
TIKTOK_APP_SECRET = "0ea69aa1ca51e7e5173ad243125d448bb5ff3f28"

# TikTok Shop API 端點配置
TIKTOK_AUTH_URL = "https://auth.tiktok-shops.com/api/v2/token/get"
TIKTOK_TRACKING_LINK_URL = "https://open-api.tiktokglobalshop.com/affiliate_creator/202407/affiliate_sharing_links/generate"
TIKTOK_ORDERS_SEARCH_URL = "https://open-api.tiktokglobalshop.com/affiliate_creator/202410/affiliate_orders/search"

# TikTok Shop 默認配置
DEFAULT_CHANNEL = "OEM2_VIVO_PUSH"
DEFAULT_TAGS = ["111-WA-ABC", "222-CC-DD"]
DEFAULT_SHOP_REGION = "ID"  # Indonesia

# TikTok Shop 訂單狀態常量
ORDER_STATUS_UNPAID = "UNPAID"
ORDER_STATUS_AWAITING_SHIPMENT = "AWAITING_SHIPMENT"
ORDER_STATUS_AWAITING_COLLECTION = "AWAITING_COLLECTION"
ORDER_STATUS_IN_TRANSIT = "IN_TRANSIT"
ORDER_STATUS_DELIVERED = "DELIVERED"
ORDER_STATUS_COMPLETED = "COMPLETED"
ORDER_STATUS_CANCELLED = "CANCELLED"
ORDER_STATUS_SETTLED = "SETTLED"

# TikTok Shop 默認轉化報告設置
DEFAULT_PAGE_SIZE = 50
DEFAULT_ORDER_STATUSES = [ORDER_STATUS_SETTLED, ORDER_STATUS_COMPLETED]

# TikTok Shop 素材類型
MATERIAL_TYPE_PRODUCT = "1"    # Product scene
MATERIAL_TYPE_CAMPAIGN = "2"   # Campaign scene  
MATERIAL_TYPE_SHOWCASE = "3"   # Showcase scene
MATERIAL_TYPE_SHOP = "5"       # Shop scene

# TikTok Shop API 配置
TIKTOK_REQUEST_TIMEOUT = 30
TIKTOK_MAX_RETRY_ATTEMPTS = 3
TIKTOK_RATE_LIMIT_DELAY = 5

# TikTok Shop 授權配置
TIKTOK_MOCK_MODE = False  # 關閉模擬模式，使用真實 API
TIKTOK_DEFAULT_REFRESH_TOKEN = None  # 需要設置真實的 refresh_token
TIKTOK_AUTO_AUTH_PORT = 8081
ACCESS_TOKEN = "ACCESS_TOKEN"  # 將通過 refresh token 更新

# =============================================================================
# 输入数据处理配置
# =============================================================================

# 输入数据要移除的列
INPUT_DATA_REMOVE_COLUMNS = [
    "Click ID",
    "Click Date", 
    "Recorded On",
    "Click to Conversion Time",
    "Website/Property",
    "Campaign Name",
    "Sale Amount (Conversion Currency)",
    "Estimated Earnings (USD)",
    "Invoice No",
    "general.Base Payout",
    "general.Bonus Payout",
    "Remarks",
    "Click Origin Country",
    "Device Type",
    "Source",
    "Browser",
    "Ref URL",
    "User Agent"
]

# 输入数据文件配置
INPUT_DATA_DIR = "input"
INPUT_DATA_OUTPUT_DIR = "output"

# 输入数据处理配置
INPUT_DATA_ENABLE_PANDASAI_ANALYSIS = True  # 是否启用pandasai分析
INPUT_DATA_ENABLE_MOCKUP = False  # 是否启用mockup处理（禁用以避免與DMP Agent重複處理）
INPUT_DATA_MOCKUP_MULTIPLIER = 0.9  # mockup倍数

# Input Data Agent 默认参数配置
INPUT_DATA_AGENT_DEFAULT_PASSTHROUGH = True      # 默认启用passthrough模式
INPUT_DATA_AGENT_DEFAULT_DMP_FORWARD = True      # 默认启用dmp-forward
INPUT_DATA_AGENT_DEFAULT_REPORTER_AGENT = True   # 默认启用reporter-agent
INPUT_DATA_AGENT_DEFAULT_PARTNER = "ALL"         # 默认处理所有partner
INPUT_DATA_AGENT_DEFAULT_SELF_EMAIL = True       # 默认启用self-email
INPUT_DATA_AGENT_DEFAULT_DAYS_AGO = 2           # 默认days-ago参数

# Input Data Agent 可选参数配置
INPUT_DATA_AGENT_ENABLE_ANALYSIS_ONLY = False    # 是否启用仅分析模式
INPUT_DATA_AGENT_ENABLE_BATCH_PROCESSING = True  # 是否启用批量处理
INPUT_DATA_AGENT_MAX_BATCH_SIZE = 10             # 批量处理最大文件数

# 输入数据输出模板
INPUT_DATA_OUTPUT_TEMPLATE = "Processed_{original_filename}_{timestamp}.xlsx"

# =============================================================================
# Reporter Agent 標準欄位配置
# =============================================================================

# 標準報告欄位列表（Reporter Agent使用）
STANDARD_REPORT_COLUMNS = [
    'Conversion ID',
    'Datetime Conversion',
    'USD Sale Amount',
    'Advertiser',  # 添加缺失的 Advertiser 欄位
    'Publisher Sub ID 1',
    'Publisher Sub ID 2', 
    'Publisher Sub ID 3',
    'Publisher Sub ID 4',
    'Publisher Sub ID 5',
    'Advertiser Sub ID 1',
    'Advertiser Sub ID 2',
    'Advertiser Sub ID 3', 
    'Advertiser Sub ID 4',
    'Advertiser Sub ID 5',
    'Status',
    'Partner',  # DMP Agent添加的分組欄位
    'Source'    # DMP Agent添加的Source欄位（使用Publisher Sub ID 1的值）
]

# DMP Agent 輸出標準化列名映射
DMP_OUTPUT_COLUMN_MAPPING = {
    'conversion_id': 'Conversion ID',
    'conversion_date': 'Datetime Conversion',
    'usd_sale_amount': 'USD Sale Amount',
    'advertiser': 'Advertiser',  # 添加 Advertiser 欄位映射
    'aff_sub1': 'Publisher Sub ID 1',
    'aff_sub2': 'Publisher Sub ID 2',
    'aff_sub3': 'Publisher Sub ID 3', 
    'aff_sub4': 'Publisher Sub ID 4',
    'aff_sub5': 'Publisher Sub ID 5',
    'adv_sub1': 'Advertiser Sub ID 1',
    'adv_sub2': 'Advertiser Sub ID 2',
    'adv_sub3': 'Advertiser Sub ID 3',
    'adv_sub4': 'Advertiser Sub ID 4', 
    'adv_sub5': 'Advertiser Sub ID 5',
    'status': 'Status'
}

# Reporter Agent 數值欄位配置
NUMERIC_COLUMNS = ['Conversion ID', 'USD Sale Amount']

# Reporter Agent 預設值配置
COLUMN_DEFAULT_VALUES = {
    'Conversion ID': 0,
    'USD Sale Amount': 0.0,
    'Status': 'Pending',
    # Publisher Sub ID 1~5, Advertiser Sub ID 1~5 預設為空字符串
    'Publisher Sub ID 1': '',
    'Publisher Sub ID 2': '',
    'Publisher Sub ID 3': '',
    'Publisher Sub ID 4': '',
    'Publisher Sub ID 5': '',
    'Advertiser Sub ID 1': '',
    'Advertiser Sub ID 2': '',
    'Advertiser Sub ID 3': '',
    'Advertiser Sub ID 4': '',
    'Advertiser Sub ID 5': '',
    'Source': 'Unknown',
    'Partner': 'Unknown'
}

def get_standard_report_columns():
    """獲取標準報告欄位列表"""
    return STANDARD_REPORT_COLUMNS.copy()

def get_dmp_column_mapping():
    """獲取DMP輸出列名映射"""
    return DMP_OUTPUT_COLUMN_MAPPING.copy()

def get_numeric_columns():
    """獲取數值類型欄位列表"""
    return NUMERIC_COLUMNS.copy()

def get_column_default_values():
    """獲取欄位預設值配置"""
    return COLUMN_DEFAULT_VALUES.copy()

def get_currency_format_columns():
    """獲取需要貨幣格式化的欄位"""
    return ['USD Sale Amount', 'USD Payout']

def is_sub_field(column_name):
    """判斷是否為Sub欄位（aff_sub1~5, adv_sub1~5）"""
    return ('Sub' in column_name and 
            column_name != 'Aff Sub' and 
            any(column_name.startswith(prefix) for prefix in ['Aff Sub', 'Adv Sub']))

# =============================================================================
# Input Data Agent 默认配置辅助函数
# =============================================================================

def get_input_data_agent_default_args():
    """获取Input Data Agent的默认参数配置"""
    return {
        'passthrough': INPUT_DATA_AGENT_DEFAULT_PASSTHROUGH,
        'dmp_forward': INPUT_DATA_AGENT_DEFAULT_DMP_FORWARD,
        'reporter_agent': INPUT_DATA_AGENT_DEFAULT_REPORTER_AGENT,
        'partner': INPUT_DATA_AGENT_DEFAULT_PARTNER,
        'self_email': INPUT_DATA_AGENT_DEFAULT_SELF_EMAIL,
        'days_ago': INPUT_DATA_AGENT_DEFAULT_DAYS_AGO
    }

def get_input_data_agent_optional_args():
    """获取Input Data Agent的可选参数配置"""
    return {
        'analysis_only': INPUT_DATA_AGENT_ENABLE_ANALYSIS_ONLY,
        'batch_processing': INPUT_DATA_AGENT_ENABLE_BATCH_PROCESSING,
        'max_batch_size': INPUT_DATA_AGENT_MAX_BATCH_SIZE
    }

def should_enable_passthrough():
    """是否启用passthrough模式"""
    return INPUT_DATA_AGENT_DEFAULT_PASSTHROUGH

def should_enable_dmp_forward():
    """是否启用dmp-forward"""
    return INPUT_DATA_AGENT_DEFAULT_DMP_FORWARD

def should_enable_reporter_agent():
    """是否启用reporter-agent"""
    return INPUT_DATA_AGENT_DEFAULT_REPORTER_AGENT

def get_default_partner():
    """获取默认partner设置"""
    return INPUT_DATA_AGENT_DEFAULT_PARTNER

def should_enable_self_email():
    """是否启用self-email"""
    return INPUT_DATA_AGENT_DEFAULT_SELF_EMAIL

def get_default_days_ago():
    """获取默认days-ago参数"""
    return INPUT_DATA_AGENT_DEFAULT_DAYS_AGO

def build_input_data_agent_command_args(import_file=None, **kwargs):
    """
    构建Input Data Agent的命令行参数
    
    Args:
        import_file: 要导入的文件路径
        **kwargs: 其他参数覆盖默认值
    
    Returns:
        dict: 命令行参数字典
    """
    default_args = get_input_data_agent_default_args()
    
    # 合并默认参数和传入的参数
    args = default_args.copy()
    args.update(kwargs)
    
    # 构建命令行参数列表
    cmd_args = []
    
    if import_file:
        cmd_args.extend(['--import', import_file])
    
    if args.get('passthrough', False):
        cmd_args.append('--passthrough')
    
    if args.get('dmp_forward', False):
        cmd_args.append('--dmp-forward')
    
    if args.get('reporter_agent', False):
        cmd_args.append('--reporter-agent')
    
    if args.get('partner'):
        cmd_args.extend(['--partner', args['partner']])
    
    if args.get('self_email', False):
        cmd_args.append('--self-email')
    
    if args.get('days_ago'):
        cmd_args.extend(['--days-ago', str(args['days_ago'])])
    
    return cmd_args

# =============================================================================