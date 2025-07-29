"""
Token 管理模組
處理 Token 存儲、自動刷新、過期檢查等功能
參考 Airbyte 實現: https://airbyte.com/blog/implementing-access-token-refreshes-in-python
"""

import json
import time
import logging
import shutil
from pathlib import Path
from typing import Dict, Optional, Tuple
from . import config
from .auth import TikTokAuth

# 設置日誌
logger = logging.getLogger(__name__)

class TokenManager:
    """Token 管理類 - 參考 Airbyte 的 token refresh 實現"""
    
    def __init__(self):
        """初始化 Token 管理器"""
        self.token_file = config.get_token_storage_path()
        self.auth = TikTokAuth()
        self._cached_tokens = None
        self._last_check_time = 0
        self._cache_duration = 60  # 緩存60秒，類似 Airbyte 的實現
        
        # 確保存儲目錄存在
        self._create_token_storage_dir()
        
        logger.info(f"🔧 TokenManager 初始化完成 - 存儲路徑: {self.token_file}")
        
    def get_valid_token(self) -> str:
        """
        獲取有效的 access_token，自動處理刷新
        參考 Airbyte 的實現: 每次調用前檢查 token 有效性
        
        Returns:
            有效的 access_token
            
        Raises:
            Exception: 當無法獲取有效 token 時
        """
        logger.info("🔍 檢查 Token 有效性...")
        
        # 檢查緩存 (類似 Airbyte 的 session state 機制)
        current_time = time.time()
        if (self._cached_tokens and 
            current_time - self._last_check_time < self._cache_duration):
            logger.debug("📦 使用緩存的 Token")
            return self._cached_tokens['access_token']
        
        # 加載存儲的 tokens
        token_data = self.load_tokens()
        
        if not token_data:
            logger.warning("⚠️  未找到存儲的 Token，需要首次獲取")
            raise Exception("❌ 未找到有效 Token，請先使用 'get-token' 命令獲取")
        
        # 檢查是否需要刷新 (類似 Airbyte 每 120 秒檢查的邏輯)
        if self.is_token_expired(token_data):
            logger.info("⏰ Token 即將過期，開始刷新...")
            token_data = self._refresh_token_automatically(token_data)
        
        # 更新緩存
        self._cached_tokens = token_data
        self._last_check_time = current_time
        
        access_token = token_data.get('access_token')
        if not access_token:
            raise Exception("❌ Token 數據中缺少 access_token")
        
        logger.info(f"✅ 獲取有效 Token: {access_token[:20]}...")
        return access_token
        
    def is_token_expired(self, token_data: Dict) -> bool:
        """
        檢查 Token 是否過期 - 參考 Airbyte 的提前刷新策略
        
        Args:
            token_data: Token 數據字典
            
        Returns:
            True 如果 token 已過期或即將過期
        """
        if not token_data:
            return True
            
        # 檢查是否有過期時間信息
        expires_at = token_data.get('expires_at')
        if not expires_at:
            # 如果沒有過期時間，檢查獲取時間
            fetched_at = token_data.get('fetched_at')
            if fetched_at:
                expires_at = fetched_at + config.TOKEN_EXPIRE_TIME
            else:
                logger.warning("⚠️  Token 數據缺少時間信息，假設已過期")
                return True
        
        current_time = int(time.time())
        # 提前刷新 (類似 Airbyte 提前 60 秒刷新的策略)
        buffer_time = config.TOKEN_REFRESH_BUFFER
        
        is_expired = (current_time + buffer_time) >= expires_at
        
        if is_expired:
            remaining_time = expires_at - current_time
            logger.info(f"⏰ Token 將在 {remaining_time} 秒後過期，需要刷新")
        else:
            remaining_time = expires_at - current_time
            logger.debug(f"✅ Token 仍有效，剩餘 {remaining_time} 秒")
            
        return is_expired
        
    def save_tokens(self, token_data: Dict) -> None:
        """
        保存 Token 到配置文件
        
        Args:
            token_data: 包含 access_token、refresh_token 等的字典
        """
        logger.info("💾 保存 Token 到配置文件...")
        
        if not token_data:
            raise ValueError("❌ Token 數據不能為空")
        
        try:
            # 備份現有文件
            if self.token_file.exists():
                self._backup_tokens_file()
            
            # 添加保存時間戳
            save_data = token_data.copy()
            save_data['saved_at'] = int(time.time())
            
            # 寫入文件
            with open(self.token_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
            
            # 設置文件權限 (僅所有者可讀寫)
            self.token_file.chmod(0o600)
            
            logger.info(f"✅ Token 已保存到: {self.token_file}")
            logger.info(f"🔑 Access Token: {token_data.get('access_token', '')[:20]}...")
            logger.info(f"🔄 Refresh Token: {token_data.get('refresh_token', '')[:20]}...")
            
            # 更新配置文件中的 token 變量 (可選)
            self._update_config_tokens(token_data)
            
            # 清除緩存，強制下次重新加載
            self._cached_tokens = None
            
        except Exception as e:
            logger.error(f"❌ 保存 Token 失敗: {str(e)}")
            raise
        
    def load_tokens(self) -> Optional[Dict]:
        """
        從配置文件加載 Token
        
        Returns:
            Token 數據字典，如果文件不存在則返回 None
        """
        logger.info("📂 從配置文件加載 Token...")
        
        if not self.token_file.exists():
            logger.info("📝 Token 文件不存在")
            return None
        
        try:
            with open(self.token_file, 'r', encoding='utf-8') as f:
                token_data = json.load(f)
            
            # 驗證數據結構
            if not isinstance(token_data, dict):
                logger.error("❌ Token 文件格式無效")
                return None
            
            logger.info("✅ Token 加載成功")
            logger.debug(f"📊 Token 數據包含字段: {list(token_data.keys())}")
            
            return token_data
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Token 文件 JSON 格式錯誤: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"❌ 加載 Token 失敗: {str(e)}")
            return None
        
    def refresh_token_if_needed(self) -> bool:
        """
        如果需要則刷新 Token
        
        Returns:
            True 如果 token 被刷新
        """
        logger.info("🔄 檢查是否需要刷新 Token...")
        
        token_data = self.load_tokens()
        if not token_data:
            logger.warning("⚠️  未找到 Token 數據，無法刷新")
            return False
        
        if not self.is_token_expired(token_data):
            logger.info("✅ Token 仍然有效，無需刷新")
            return False
        
        try:
            self._refresh_token_automatically(token_data)
            return True
        except Exception as e:
            logger.error(f"❌ 自動刷新 Token 失敗: {str(e)}")
            return False
        
    def get_token_info(self) -> Dict:
        """
        獲取當前 Token 信息
        
        Returns:
            Token 信息字典
        """
        token_data = self.load_tokens()
        
        if not token_data:
            return {
                "status": "未找到 Token",
                "access_token": None,
                "refresh_token": None,
                "expires_at": None,
                "is_expired": True
            }
        
        current_time = int(time.time())
        expires_at = token_data.get('expires_at')
        is_expired = self.is_token_expired(token_data)
        
        info = {
            "status": "過期" if is_expired else "有效",
            "access_token": token_data.get('access_token'),
            "refresh_token": token_data.get('refresh_token'),
            "open_id": token_data.get('open_id'),
            "seller_name": token_data.get('seller_name'),
            "seller_base_region": token_data.get('seller_base_region'),
            "fetched_at": token_data.get('fetched_at'),
            "expires_at": expires_at,
            "saved_at": token_data.get('saved_at'),
            "is_expired": is_expired,
            "current_time": current_time
        }
        
        if expires_at:
            info["remaining_seconds"] = max(0, expires_at - current_time)
        
        return info
        
    def _refresh_token_automatically(self, token_data: Dict) -> Dict:
        """
        自動刷新 Token
        
        Args:
            token_data: 當前 Token 數據
            
        Returns:
            刷新後的 Token 數據
        """
        refresh_token = token_data.get('refresh_token')
        if not refresh_token:
            raise Exception("❌ 缺少 refresh_token，無法自動刷新")
        
        # 使用 auth 類刷新 token
        new_token_data = self.auth.refresh_access_token(refresh_token)
        
        # 保存新的 token
        self.save_tokens(new_token_data)
        
        logger.info("✅ Token 自動刷新完成")
        return new_token_data
        
    def _create_token_storage_dir(self) -> None:
        """創建 Token 存儲目錄"""
        self.token_file.parent.mkdir(parents=True, exist_ok=True)
        
    def _backup_tokens_file(self) -> None:
        """備份 Token 文件"""
        if not self.token_file.exists():
            return
            
        backup_file = self.token_file.with_suffix('.conf.backup')
        shutil.copy2(self.token_file, backup_file)
        logger.debug(f"📦 Token 文件已備份到: {backup_file}")
        
    def _update_config_tokens(self, token_data: Dict) -> None:
        """
        更新配置文件中的 token 變量 (可選功能)
        
        Args:
            token_data: Token 數據
        """
        try:
            # 這裡可以選擇是否更新配置文件中的 token 變量
            # 出於安全考慮，通常不建議將 token 寫入源代碼配置文件
            logger.debug("🔧 跳過配置文件 token 更新 (出於安全考慮)")
            
        except Exception as e:
            logger.warning(f"⚠️  更新配置文件 token 失敗: {str(e)}")
            
    def clear_tokens(self) -> bool:
        """
        清除存儲的 Token
        
        Returns:
            True 如果清除成功
        """
        try:
            if self.token_file.exists():
                self._backup_tokens_file()
                self.token_file.unlink()
                logger.info("🗑️  Token 文件已刪除")
            
            self._cached_tokens = None
            self._last_check_time = 0
            
            logger.info("✅ Token 清除完成")
            return True
            
        except Exception as e:
            logger.error(f"❌ 清除 Token 失敗: {str(e)}")
            return False
            
    def validate_storage_permissions(self) -> bool:
        """
        驗證存儲路徑權限
        
        Returns:
            True 如果權限正確
        """
        try:
            # 檢查目錄是否可寫
            test_file = self.token_file.parent / "test_write.tmp"
            test_file.write_text("test")
            test_file.unlink()
            
            # 檢查現有文件權限
            if self.token_file.exists():
                file_stat = self.token_file.stat()
                # 檢查是否僅所有者可讀寫 (0o600)
                permissions = oct(file_stat.st_mode)[-3:]
                if permissions != "600":
                    logger.warning(f"⚠️  Token 文件權限不安全: {permissions}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 權限驗證失敗: {str(e)}")
            return False 