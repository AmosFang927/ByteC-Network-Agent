#!/usr/bin/env python3
"""
Gmail SMTP 测试工具
用于诊断Gmail邮件发送问题
"""

import smtplib
import ssl
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import logging
import sys
import os

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

class GmailSMTPTester:
    """Gmail SMTP 测试器"""
    
    def __init__(self):
        # Gmail SMTP 配置
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = "GaryBu0801@gmail.com"
        self.sender_password = "kxvx hdng fgsf stwr"  # 应用专用密码
        
    def test_basic_connection(self):
        """测试基本SMTP连接"""
        logger.info("🔍 测试1: 基本SMTP连接")
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30) as server:
                server.set_debuglevel(1)  # 启用详细调试
                logger.info("✅ SMTP连接成功")
                return True
        except Exception as e:
            logger.error(f"❌ SMTP连接失败: {e}")
            return False
    
    def test_tls_handshake(self):
        """测试TLS握手"""
        logger.info("🔍 测试2: TLS握手")
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30) as server:
                server.set_debuglevel(1)
                server.starttls()
                logger.info("✅ TLS握手成功")
                return True
        except Exception as e:
            logger.error(f"❌ TLS握手失败: {e}")
            return False
    
    def test_authentication(self):
        """测试身份验证"""
        logger.info("🔍 测试3: 身份验证")
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30) as server:
                server.set_debuglevel(1)
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                logger.info("✅ 身份验证成功")
                return True
        except Exception as e:
            logger.error(f"❌ 身份验证失败: {e}")
            return False
    
    def test_simple_email(self):
        """测试发送简单邮件"""
        logger.info("🔍 测试4: 发送简单邮件")
        try:
            msg = MIMEText("这是一个SMTP测试邮件", "plain", "utf-8")
            msg["From"] = self.sender_email
            msg["To"] = self.sender_email  # 发给自己
            msg["Subject"] = "SMTP测试邮件"
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30) as server:
                server.set_debuglevel(1)
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
                logger.info("✅ 简单邮件发送成功")
                return True
        except Exception as e:
            logger.error(f"❌ 简单邮件发送失败: {e}")
            return False
    
    def test_multipart_email(self):
        """测试发送多部分邮件"""
        logger.info("🔍 测试5: 发送多部分邮件")
        try:
            msg = MIMEMultipart()
            msg["From"] = self.sender_email
            msg["To"] = self.sender_email
            msg["Subject"] = "SMTP多部分测试邮件"
            
            # 添加文本内容
            body = "这是一个多部分SMTP测试邮件"
            msg.attach(MIMEText(body, "plain", "utf-8"))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30) as server:
                server.set_debuglevel(1)
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
                logger.info("✅ 多部分邮件发送成功")
                return True
        except Exception as e:
            logger.error(f"❌ 多部分邮件发送失败: {e}")
            return False
    
    def test_with_attachment(self):
        """测试发送带附件的邮件"""
        logger.info("🔍 测试6: 发送带附件邮件")
        try:
            msg = MIMEMultipart()
            msg["From"] = self.sender_email
            msg["To"] = self.sender_email
            msg["Subject"] = "SMTP附件测试邮件"
            
            # 添加文本内容
            body = "这是一个带附件的SMTP测试邮件"
            msg.attach(MIMEText(body, "plain", "utf-8"))
            
            # 创建一个小的测试文件作为附件
            test_content = "这是一个测试附件内容\n测试时间: " + time.strftime("%Y-%m-%d %H:%M:%S")
            attachment = MIMEApplication(test_content.encode('utf-8'))
            attachment.add_header('Content-Disposition', 'attachment', filename='test.txt')
            msg.attach(attachment)
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=60) as server:
                server.set_debuglevel(1)
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
                logger.info("✅ 带附件邮件发送成功")
                return True
        except Exception as e:
            logger.error(f"❌ 带附件邮件发送失败: {e}")
            return False
    
    def test_connection_stability(self, duration=60):
        """测试连接稳定性"""
        logger.info(f"🔍 测试7: 连接稳定性测试 ({duration}秒)")
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30) as server:
                server.set_debuglevel(0)  # 关闭详细调试避免过多输出
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                
                start_time = time.time()
                while time.time() - start_time < duration:
                    # 发送NOOP命令保持连接
                    server.noop()
                    logger.info(f"⏱️  连接保持正常 ({int(time.time() - start_time)}秒)")
                    time.sleep(10)
                
                logger.info("✅ 连接稳定性测试通过")
                return True
        except Exception as e:
            logger.error(f"❌ 连接稳定性测试失败: {e}")
            return False
    
    def test_ssl_context(self):
        """测试不同的SSL上下文"""
        logger.info("🔍 测试8: SSL上下文测试")
        
        # 测试默认SSL上下文
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30) as server:
                server.starttls(context=context)
                server.login(self.sender_email, self.sender_password)
                logger.info("✅ 默认SSL上下文测试通过")
        except Exception as e:
            logger.error(f"❌ 默认SSL上下文测试失败: {e}")
        
        # 测试不验证证书的SSL上下文
        try:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30) as server:
                server.starttls(context=context)
                server.login(self.sender_email, self.sender_password)
                logger.info("✅ 不验证证书SSL上下文测试通过")
                return True
        except Exception as e:
            logger.error(f"❌ 不验证证书SSL上下文测试失败: {e}")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        logger.info("🚀 开始Gmail SMTP诊断测试")
        logger.info("=" * 60)
        
        results = {}
        
        # 基本测试
        results['basic_connection'] = self.test_basic_connection()
        results['tls_handshake'] = self.test_tls_handshake()
        results['authentication'] = self.test_authentication()
        results['simple_email'] = self.test_simple_email()
        results['multipart_email'] = self.test_multipart_email()
        results['with_attachment'] = self.test_with_attachment()
        results['ssl_context'] = self.test_ssl_context()
        
        # 如果基本功能正常，测试连接稳定性
        if results['simple_email']:
            results['connection_stability'] = self.test_connection_stability(30)
        
        # 打印测试结果摘要
        logger.info("=" * 60)
        logger.info("📊 测试结果摘要:")
        for test_name, result in results.items():
            status = "✅ 通过" if result else "❌ 失败"
            logger.info(f"   {test_name}: {status}")
        
        # 计算通过率
        passed = sum(1 for r in results.values() if r)
        total = len(results)
        pass_rate = (passed / total) * 100
        
        logger.info(f"📈 总体通过率: {passed}/{total} ({pass_rate:.1f}%)")
        
        if pass_rate < 50:
            logger.error("❌ SMTP服务存在严重问题，建议检查网络和Gmail设置")
        elif pass_rate < 80:
            logger.warning("⚠️ SMTP服务部分功能异常，可能存在网络不稳定问题")
        else:
            logger.info("✅ SMTP服务基本正常")
        
        return results

def main():
    """主函数"""
    tester = GmailSMTPTester()
    results = tester.run_all_tests()
    
    # 如果所有基本测试都通过，提供使用建议
    if results.get('simple_email') and results.get('multipart_email'):
        logger.info("\n💡 建议:")
        logger.info("   - 基本SMTP功能正常，可以尝试增加重试机制")
        logger.info("   - 考虑使用更短的超时时间和更多的重试次数")
        logger.info("   - 在发送大附件时使用更长的超时时间")

if __name__ == "__main__":
    main() 