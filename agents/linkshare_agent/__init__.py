"""
TikTok Shop 聯盟行銷 Agent
提供 TikTok Shop 聯盟連結生成、Token 管理等功能
"""

__version__ = "1.0.0"
__author__ = "ByteC Network"

from .auth import TikTokAuth
from .token_manager import TokenManager
from .link_generator import LinkGenerator

__all__ = [
    "TikTokAuth",
    "TokenManager", 
    "LinkGenerator"
] 