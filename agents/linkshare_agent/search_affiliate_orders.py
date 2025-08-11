#!/usr/bin/env python3
"""
TikTok Shop 联盟营销 - Search Affiliate Orders API
支持查询联盟订单数据
"""

import sys
import json
import logging
import subprocess
import time
import traceback
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from datetime import datetime, timezone
from enum import Enum

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent.parent))

from agents.linkshare_agent import config
from agents.linkshare_agent.token_manager import TokenManager

# 使用统一的日志配置
logger = logging.getLogger(__name__)

class ErrorType(Enum):
    """错误类型枚举"""
    VALIDATION_ERROR = "validation_error"
    NETWORK_ERROR = "network_error"
    API_ERROR = "api_error"
    TOKEN_ERROR = "token_error"
    TIMEOUT_ERROR = "timeout_error"
    JSON_ERROR = "json_error"
    UNKNOWN_ERROR = "unknown_error"

class SearchAffiliateOrdersAPI:
    """Search Affiliate Orders API 主类"""
    
    def __init__(self):
        """初始化API类"""
        self.token_manager = TokenManager()
        self.nodejs_script_dir = Path(__file__).parent
        
        # 验证配置
        try:
            config.validate_config()
            logger.info(f"🔧 SearchAffiliateOrdersAPI 初始化完成")
        except ValueError as e:
            logger.error(f"❌ 配置验证失败: {e}")
            raise
    
    def _validate_page_size(self, page_size: int) -> bool:
        """验证page_size参数"""
        if not isinstance(page_size, int):
            raise ValueError("page_size必须是整数")
        if not (1 <= page_size <= 100):
            raise ValueError("page_size必须在1-100范围内")
        return True
    
    def _validate_timestamp(self, timestamp: Union[int, float], param_name: str) -> bool:
        """验证时间戳参数"""
        if timestamp is None:
            return True
        
        if not isinstance(timestamp, (int, float)):
            raise ValueError(f"{param_name}必须是数字类型")
        
        # 检查时间戳是否合理（不能是未来时间，也不能太早）
        current_time = int(time.time())
        if timestamp > current_time:
            raise ValueError(f"{param_name}不能是未来时间")
        if timestamp < 0:
            raise ValueError(f"{param_name}不能是负数")
        
        return True
    
    def _validate_campaign_id(self, campaign_id: Optional[str]) -> bool:
        """验证campaign_id参数"""
        if campaign_id is not None and not isinstance(campaign_id, str):
            raise ValueError("campaign_id必须是字符串")
        return True
    
    def _validate_category_asset_cipher(self, category_asset_cipher: Optional[str]) -> bool:
        """验证category_asset_cipher参数"""
        if category_asset_cipher is not None and not isinstance(category_asset_cipher, str):
            raise ValueError("category_asset_cipher必须是字符串")
        return True
    
    def _validate_page_token(self, page_token: Optional[str]) -> bool:
        """验证page_token参数"""
        if page_token is not None and not isinstance(page_token, str):
            raise ValueError("page_token必须是字符串")
        return True
    
    def _validate_all_parameters(self, 
                               page_size: int,
                               page_token: Optional[str],
                               create_time_ge: Optional[int],
                               create_time_lt: Optional[int],
                               campaign_id: Optional[str],
                               category_asset_cipher: Optional[str]) -> None:
        """验证所有参数"""
        logger.debug("🔍 开始参数验证...")
        
        try:
            self._validate_page_size(page_size)
            self._validate_page_token(page_token)
            self._validate_timestamp(create_time_ge, "create_time_ge")
            self._validate_timestamp(create_time_lt, "create_time_lt")
            self._validate_campaign_id(campaign_id)
            self._validate_category_asset_cipher(category_asset_cipher)
            
            # 验证时间范围逻辑
            if create_time_ge is not None and create_time_lt is not None:
                if create_time_ge >= create_time_lt:
                    raise ValueError("create_time_ge必须小于create_time_lt")
            
            logger.debug("✅ 所有参数验证通过")
            
        except Exception as e:
            logger.error(f"❌ 参数验证失败: {e}")
            raise
    
    def _format_timestamp_for_display(self, timestamp: Optional[int]) -> str:
        """格式化时间戳用于显示"""
        if timestamp is None:
            return "N/A"
        try:
            dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        except:
            return str(timestamp)
    
    def _handle_api_error(self, error_code: int, error_message: str) -> Dict[str, Any]:
        """处理API错误，使用统一的错误码映射"""
        error_description = config.API_ERROR_CODES.get(error_code, error_message)
        logger.error(f"❌ API错误 {error_code}: {error_description}")
        return {
            "success": False,
            "error": f"API错误 {error_code}: {error_description}",
            "error_code": error_code,
            "error_message": error_message,
            "error_type": ErrorType.API_ERROR.value
        }
    
    def _handle_validation_error(self, error: Exception) -> Dict[str, Any]:
        """处理参数验证错误"""
        logger.error(f"❌ 参数验证错误: {error}")
        return {
            "success": False,
            "error": f"参数验证错误: {str(error)}",
            "error_type": ErrorType.VALIDATION_ERROR.value
        }
    
    def _handle_network_error(self, error: Exception) -> Dict[str, Any]:
        """处理网络错误"""
        logger.error(f"❌ 网络错误: {error}")
        return {
            "success": False,
            "error": f"网络错误: {str(error)}",
            "error_type": ErrorType.NETWORK_ERROR.value
        }
    
    def _handle_timeout_error(self, error: Exception) -> Dict[str, Any]:
        """处理超时错误"""
        logger.error(f"❌ 请求超时: {error}")
        return {
            "success": False,
            "error": f"请求超时: {str(error)}",
            "error_type": ErrorType.TIMEOUT_ERROR.value
        }
    
    def _handle_json_error(self, error: Exception) -> Dict[str, Any]:
        """处理JSON解析错误"""
        logger.error(f"❌ JSON解析错误: {error}")
        return {
            "success": False,
            "error": f"JSON解析错误: {str(error)}",
            "error_type": ErrorType.JSON_ERROR.value
        }
    
    def _handle_token_error(self, error: Exception) -> Dict[str, Any]:
        """处理Token相关错误"""
        logger.error(f"❌ Token错误: {error}")
        return {
            "success": False,
            "error": f"Token错误: {str(error)}",
            "error_type": ErrorType.TOKEN_ERROR.value
        }
    
    def _handle_unknown_error(self, error: Exception) -> Dict[str, Any]:
        """处理未知错误"""
        logger.error(f"❌ 未知错误: {error}")
        logger.debug(f"错误详情: {traceback.format_exc()}")
        return {
            "success": False,
            "error": f"未知错误: {str(error)}",
            "error_type": ErrorType.UNKNOWN_ERROR.value
        }
    
    def _execute_nodejs_script(self, script_name: str, *args) -> Dict[str, Any]:
        """
        执行Node.js脚本的通用方法
        
        Args:
            script_name: 脚本文件名
            *args: 脚本参数
            
        Returns:
            执行结果字典
        """
        script_path = self.nodejs_script_dir / script_name
        
        if not script_path.exists():
            logger.error(f"❌ Node.js脚本不存在: {script_path}")
            return {
                "success": False,
                "error": f"Node.js脚本不存在: {script_name}",
                "error_type": ErrorType.UNKNOWN_ERROR.value
            }
        
        cmd = ['node', str(script_path)] + list(args)
        
        logger.info(f"📡 执行Node.js脚本: {script_name}")
        logger.debug(f"命令: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=config.REQUEST_TIMEOUT
            )
            
            logger.info(f"📊 Node.js脚本执行完成，返回码: {result.returncode}")
            
            if result.returncode != 0:
                logger.error(f"❌ Node.js脚本执行失败: {result.stderr}")
                return {
                    "success": False,
                    "error": f"Node.js脚本执行失败: {result.stderr}",
                    "error_type": ErrorType.UNKNOWN_ERROR.value
                }
            
            # 解析输出
            output_lines = result.stdout.strip().split('\n')
            final_result_line = None
            
            for line in output_lines:
                if line.startswith('FINAL_RESULT:'):
                    final_result_line = line.replace('FINAL_RESULT:', '')
                    break
            
            if not final_result_line:
                logger.error("❌ 未找到FINAL_RESULT输出")
                return {
                    "success": False,
                    "error": "未找到FINAL_RESULT输出",
                    "error_type": ErrorType.UNKNOWN_ERROR.value
                }
            
            # 解析JSON结果
            try:
                result_data = json.loads(final_result_line)
                return result_data
            except json.JSONDecodeError as e:
                return self._handle_json_error(e)
                
        except subprocess.TimeoutExpired as e:
            return self._handle_timeout_error(e)
        except Exception as e:
            return self._handle_unknown_error(e)
    
    def get_category_assets(self) -> Dict[str, Any]:
        """
        获取categoryAssetCipher
        
        Returns:
            包含category assets信息的字典
        """
        logger.info("🔍 开始获取Category Assets...")
        
        try:
            # 获取access token
            access_token = self.token_manager.get_valid_token()
            logger.info(f"🔑 获取到access token: {access_token[:30]}...")
            
            # 执行Node.js脚本
            result = self._execute_nodejs_script(
                'get_category_assets.js',
                config.APP_KEY,
                config.APP_SECRET,
                access_token
            )
            
            if not result.get("success"):
                return result
            
            # 检查业务逻辑错误
            if not result.get("success"):
                error_code = result.get("code", -1)
                error_message = result.get("error", "未知错误")
                return self._handle_api_error(error_code, error_message)
            
            logger.info("✅ Category Assets获取成功")
            
            # 记录获取到的category assets信息
            available_ciphers = result.get("availableCiphers", [])
            logger.info(f"📋 获取到 {len(available_ciphers)} 个Category Assets")
            for i, cipher_info in enumerate(available_ciphers):
                logger.info(f"   {i+1}. Category ID: {cipher_info.get('categoryId')}")
                logger.info(f"      Category Name: {cipher_info.get('categoryName')}")
                logger.info(f"      Target Market: {cipher_info.get('targetMarket')}")
            
            return result
                
        except Exception as e:
            if "token" in str(e).lower():
                return self._handle_token_error(e)
            else:
                return self._handle_unknown_error(e)
    
    def search_orders(self, 
                     page_size: int = 20,
                     page_token: Optional[str] = None,
                     create_time_ge: Optional[int] = None,
                     create_time_lt: Optional[int] = None,
                     campaign_id: Optional[str] = None,
                     category_asset_cipher: Optional[str] = None) -> Dict[str, Any]:
        """
        搜索联盟订单
        
        Args:
            page_size: 分页大小，默认20，范围1-100
            page_token: 分页token
            create_time_ge: 创建时间起始（Unix timestamp）
            create_time_lt: 创建时间结束（Unix timestamp）
            campaign_id: 活动ID过滤
            category_asset_cipher: 合作伙伴标识符（如果未提供会自动获取）
            
        Returns:
            包含订单搜索结果的字典
        """
        logger.info("🔍 开始搜索联盟订单...")
        
        try:
            # 参数验证
            self._validate_all_parameters(
                page_size=page_size,
                page_token=page_token,
                create_time_ge=create_time_ge,
                create_time_lt=create_time_lt,
                campaign_id=campaign_id,
                category_asset_cipher=category_asset_cipher
            )
            
            # 记录搜索参数
            logger.info("📋 搜索参数:")
            logger.info(f"   分页大小: {page_size}")
            logger.info(f"   分页Token: {page_token or 'N/A'}")
            logger.info(f"   创建时间起始: {self._format_timestamp_for_display(create_time_ge)}")
            logger.info(f"   创建时间结束: {self._format_timestamp_for_display(create_time_lt)}")
            logger.info(f"   活动ID: {campaign_id or 'N/A'}")
            logger.info(f"   Category Asset Cipher: {category_asset_cipher[:30] + '...' if category_asset_cipher else 'N/A'}")
            
            # 如果没有提供category_asset_cipher，自动获取
            if not category_asset_cipher:
                logger.info("🔍 自动获取categoryAssetCipher...")
                category_result = self.get_category_assets()
                
                if not category_result.get("success"):
                    return category_result
                
                # 使用第一个可用的cipher
                available_ciphers = category_result.get("availableCiphers", [])
                if not available_ciphers:
                    return {
                        "success": False,
                        "error": "没有可用的categoryAssetCipher",
                        "error_type": ErrorType.API_ERROR.value
                    }
                
                category_asset_cipher = available_ciphers[0]["cipher"]
                logger.info(f"✅ 使用categoryAssetCipher: {category_asset_cipher[:30]}...")
            
            # 获取access token
            access_token = self.token_manager.get_valid_token()
            logger.info(f"🔑 获取到access token: {access_token[:30]}...")
            
            # 构建请求体
            request_body = {}
            if create_time_ge is not None:
                request_body["createTimeGe"] = create_time_ge
            if create_time_lt is not None:
                request_body["createTimeLt"] = create_time_lt
            if campaign_id is not None:
                request_body["campaignId"] = campaign_id
            
            logger.debug(f"请求体: {json.dumps(request_body, indent=2)}")
            
            # 执行Node.js脚本
            result = self._execute_nodejs_script(
                'search_affiliate_orders.js',
                config.APP_KEY,
                config.APP_SECRET,
                access_token,
                json.dumps(request_body),
                category_asset_cipher,
                str(page_size),
                page_token or ""
            )
            
            if not result.get("success"):
                return result
            
            # 检查业务逻辑错误
            if not result.get("success"):
                error_code = result.get("code", -1)
                error_message = result.get("error", "未知错误")
                return self._handle_api_error(error_code, error_message)
            
            logger.info("✅ 订单搜索成功")
            
            # 记录搜索结果统计
            orders = result.get("orders", [])
            total_count = result.get("totalCount", 0)
            next_page_token = result.get("nextPageToken")
            
            logger.info(f"📊 搜索结果: 总数 {total_count}, 当前页 {len(orders)} 条订单")
            if next_page_token:
                logger.info(f"📄 下一页Token: {next_page_token}")
            
            return result
                
        except ValueError as e:
            return self._handle_validation_error(e)
        except Exception as e:
            if "token" in str(e).lower():
                return self._handle_token_error(e)
            else:
                return self._handle_unknown_error(e)

# 便捷函数
def search_affiliate_orders(page_size: int = 20,
                          page_token: Optional[str] = None,
                          create_time_ge: Optional[int] = None,
                          create_time_lt: Optional[int] = None,
                          campaign_id: Optional[str] = None,
                          category_asset_cipher: Optional[str] = None) -> Dict[str, Any]:
    """
    搜索联盟订单的便捷函数
    
    Args:
        page_size: 分页大小，默认20，范围1-100
        page_token: 分页token
        create_time_ge: 创建时间起始（Unix timestamp）
        create_time_lt: 创建时间结束（Unix timestamp）
        campaign_id: 活动ID过滤
        category_asset_cipher: 合作伙伴标识符（如果未提供会自动获取）
        
    Returns:
        包含订单搜索结果的字典
    """
    api = SearchAffiliateOrdersAPI()
    return api.search_orders(
        page_size=page_size,
        page_token=page_token,
        create_time_ge=create_time_ge,
        create_time_lt=create_time_lt,
        campaign_id=campaign_id,
        category_asset_cipher=category_asset_cipher
    )

def get_category_assets() -> Dict[str, Any]:
    """
    获取categoryAssetCipher的便捷函数
    
    Returns:
        包含category assets信息的字典
    """
    api = SearchAffiliateOrdersAPI()
    return api.get_category_assets() 