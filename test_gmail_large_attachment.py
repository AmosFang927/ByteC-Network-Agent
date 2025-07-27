#!/usr/bin/env python3
"""
Gmail 大附件測試工具
測試與實際email_sender相同的配置
"""

import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import logging
import sys

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_large_attachment():
    """測試發送大附件郵件"""
    # Gmail配置（與config.py一致）
    sender_email = "GaryBu0801@gmail.com"
    sender_password = "kxvx hdng fgsf stwr"
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    
    # 收件人（測試用）
    recipients = ["GaryBu0801@gmail.com", "AmosFang927@gmail.com"]
    
    try:
        # 查找測試用的Excel文件
        test_file = None
        for root, dirs, files in os.walk("output"):
            for file in files:
                if file.endswith('.xlsx') and 'DeepLeaper' in file:
                    test_file = os.path.join(root, file)
                    break
            if test_file:
                break
        
        if not test_file:
            logger.error("未找到測試用的Excel文件")
            return False
        
        file_size = os.path.getsize(test_file) / (1024 * 1024)  # MB
        logger.info(f"測試文件: {test_file} ({file_size:.1f}MB)")
        
        # 創建郵件（模擬email_sender的方式）
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = ", ".join(recipients)
        msg['Subject'] = "Gmail大附件測試"
        
        # 添加正文
        body = """
        <html>
        <body>
        <h2>Gmail大附件測試</h2>
        <p>這是一個測試大附件發送的郵件。</p>
        <ul>
        <li>發送方式: 與email_sender相同</li>
        <li>附件大小: {:.1f}MB</li>
        <li>測試目的: 驗證Gmail SMTP配置</li>
        </ul>
        </body>
        </html>
        """.format(file_size)
        
        msg.attach(MIMEText(body, 'html'))
        
        # 添加附件（與email_sender相同的方式）
        logger.info("正在添加附件...")
        with open(test_file, "rb") as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
        
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename= {os.path.basename(test_file)}'
        )
        msg.attach(part)
        
        logger.info(f"郵件總大小: {len(msg.as_string()) / (1024 * 1024):.1f}MB")
        
        # 發送郵件（使用send_message方法）
        logger.info("開始發送郵件...")
        with smtplib.SMTP(smtp_server, smtp_port, timeout=180) as server:
            logger.info("連接SMTP服務器...")
            
            logger.info("啟動TLS...")
            server.starttls()
            
            logger.info("登錄認證...")
            server.login(sender_email, sender_password)
            
            logger.info(f"發送郵件給 {len(recipients)} 個收件人...")
            # 使用send_message方法（與修復後的email_sender一致）
            server.send_message(msg, sender_email, recipients)
            
        logger.info("✅ 大附件郵件發送成功！")
        return True
        
    except Exception as e:
        logger.error(f"❌ 大附件郵件發送失敗: {e}")
        return False

def test_without_attachment():
    """測試不帶附件的郵件"""
    sender_email = "GaryBu0801@gmail.com"
    sender_password = "kxvx hdng fgsf stwr"
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    recipients = ["GaryBu0801@gmail.com", "AmosFang927@gmail.com"]
    
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = ", ".join(recipients)
        msg['Subject'] = "Gmail無附件測試"
        
        body = "<h2>無附件測試</h2><p>這是一個不帶附件的測試郵件。</p>"
        msg.attach(MIMEText(body, 'html'))
        
        with smtplib.SMTP(smtp_server, smtp_port, timeout=30) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg, sender_email, recipients)
            
        logger.info("✅ 無附件郵件發送成功！")
        return True
        
    except Exception as e:
        logger.error(f"❌ 無附件郵件發送失敗: {e}")
        return False

def main():
    """主函數"""
    logger.info("🚀 開始Gmail大附件測試")
    
    # 先測試無附件郵件
    logger.info("=" * 50)
    logger.info("測試1: 無附件郵件")
    no_attachment_result = test_without_attachment()
    
    # 再測試大附件郵件
    logger.info("=" * 50)
    logger.info("測試2: 大附件郵件")
    large_attachment_result = test_large_attachment()
    
    # 總結
    logger.info("=" * 50)
    logger.info("📊 測試結果總結:")
    logger.info(f"   無附件郵件: {'✅ 成功' if no_attachment_result else '❌ 失敗'}")
    logger.info(f"   大附件郵件: {'✅ 成功' if large_attachment_result else '❌ 失敗'}")
    
    if no_attachment_result and not large_attachment_result:
        logger.warning("⚠️  結論: Gmail SMTP配置正確，但大附件發送有問題")
        logger.info("💡 建議: 考慮將大附件拆分或使用其他文件傳輸方式")
    elif no_attachment_result and large_attachment_result:
        logger.info("✅ 結論: Gmail SMTP完全正常，包括大附件發送")
    else:
        logger.error("❌ 結論: Gmail SMTP配置存在問題")

if __name__ == "__main__":
    main() 