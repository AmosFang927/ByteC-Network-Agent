#!/usr/bin/env python3
"""
直接调用 Node.js SDK 签名算法的 Python 模块
"""

import subprocess
import json
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

class SDKSignature:
    """使用 Node.js SDK 的签名生成类"""
    
    def __init__(self):
        """初始化签名生成器"""
        self.sdk_path = Path(__file__).parent / "nodejs_sdk"
        self.sign_script = self.sdk_path / "generate-sign.js"
        
        # 创建签名脚本
        self._create_sign_script()
        
        logger.info(f"🔧 SDKSignature 初始化完成 - SDK路径: {self.sdk_path}")
        
    def _create_sign_script(self):
        """创建调用SDK签名的Node.js脚本"""
        script_content = """
import { generateSign } from './dist/utils/generate-sign.js';

// 从命令行参数获取数据
const requestOptionStr = process.argv[2];
const appSecret = process.argv[3];

try {
    const requestOption = JSON.parse(requestOptionStr);
    const signature = generateSign(requestOption, appSecret);
    console.log(JSON.stringify({ success: true, signature }));
} catch (error) {
    console.log(JSON.stringify({ 
        success: false, 
        error: error.message 
    }));
}
"""
        
        with open(self.sign_script, 'w', encoding='utf-8') as f:
            f.write(script_content)
            
        logger.info(f"📝 签名脚本已创建: {self.sign_script}")
        
    def generate_signature(self, request_option: Dict[str, Any], app_secret: str) -> str:
        """
        使用 Node.js SDK 生成签名
        
        Args:
            request_option: 请求选项字典
            app_secret: App Secret
            
        Returns:
            签名字符串
            
        Raises:
            Exception: 当签名生成失败时
        """
        try:
            logger.info("🔐 使用 Node.js SDK 生成签名...")
            
            # 准备请求数据
            request_data = {
                "uri": request_option.get("uri", ""),
                "qs": request_option.get("qs", {}),
                "headers": request_option.get("headers", {}),
                "body": request_option.get("body", {})
            }
            
            # 调用 Node.js 脚本
            cmd = [
                "node", 
                str(self.sign_script),
                json.dumps(request_data),
                app_secret
            ]
            
            logger.debug(f"🚀 执行命令: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.sdk_path,
                timeout=30
            )
            
            if result.returncode != 0:
                raise Exception(f"Node.js 脚本执行失败: {result.stderr}")
                
            # 解析结果
            response = json.loads(result.stdout)
            
            if not response.get("success"):
                raise Exception(f"签名生成失败: {response.get('error', '未知错误')}")
                
            signature = response.get("signature")
            if not signature:
                raise Exception("未获取到签名")
                
            logger.info(f"✅ SDK 签名生成成功: {signature[:16]}...")
            return signature
            
        except subprocess.TimeoutExpired:
            raise Exception("Node.js 脚本执行超时")
        except json.JSONDecodeError as e:
            raise Exception(f"解析 Node.js 输出失败: {e}")
        except Exception as e:
            logger.error(f"❌ SDK 签名生成失败: {e}")
            raise

def generate_sign_sdk_style(request_option: Dict[str, Any], app_secret: str) -> str:
    """
    使用 SDK 风格的签名生成 - 直接调用 Node.js SDK
    
    Args:
        request_option: 请求选项字典
        app_secret: App Secret
        
    Returns:
        签名字符串
    """
    sdk_signer = SDKSignature()
    return sdk_signer.generate_signature(request_option, app_secret) 