#!/usr/bin/env python3
"""
ByteC Performance Dashboard API Server
前后端分离架构的后端API服务
"""

import os
import sys
import json
import subprocess
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, render_template, send_file
from flask_cors import CORS
import asyncio
import logging

# 添加项目根目录到路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

from agents.dashboard_agent.backend.database_manager import DatabaseManager
from agents.dashboard_agent.backend.dashboard_service import DashboardService
from agents.dashboard_agent.config import Config

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__, 
            template_folder='../frontend/templates',
            static_folder='../frontend/static')
CORS(app)

# 禁用静态文件缓存
@app.after_request
def after_request(response):
    if request.endpoint == 'static':
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response

# 初始化服务
db_manager = DatabaseManager()
dashboard_service = DashboardService(db_manager)

# =============================================================================
# Jinja2 模板过滤器
# =============================================================================

@app.template_filter('get_status_class')
def get_status_class(status):
    """根据状态返回Bootstrap CSS类名"""
    status_map = {
        'confirmed': 'success',
        'pending': 'warning', 
        'rejected': 'danger',
        'cancelled': 'secondary'
    }
    return status_map.get(status.lower(), 'secondary')

# =============================================================================
# 前端页面路由
# =============================================================================

@app.route('/')
def index():
    """首页重定向到summary"""
    return render_template('summary.html')

@app.route('/summary')
def summary_page():
    """总览页面"""
    return render_template('summary.html')

@app.route('/company')
def company_page():
    """公司级别页面"""
    return render_template('company.html')

@app.route('/offer')
def offer_page():
    """产品级别页面"""
    return render_template('offer.html')

@app.route('/partner')
def partner_page():
    """合作伙伴级别页面"""
    return render_template('partner.html')

@app.route('/conversion')
def conversion_page():
    """转化报告页面 - 客户端渲染"""
    try:
        # 不在服务器端预加载数据，让前端通过增强版API加载
        # 这样可以避免服务器端的空值处理问题，并提供更好的用户体验
        
        # 只渲染基础页面，数据由前端JavaScript异步加载
        return render_template('conversion.html')
                             
    except Exception as e:
        logger.error(f"渲染转化页面失败: {e}")
        # 如果页面渲染失败，返回基础错误页面
        return render_template('conversion.html', 
                             error_message=f"页面加载失败: {str(e)}")

# =============================================================================
# API端点
# =============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    })

@app.route('/api/summary', methods=['GET'])
def get_summary():
    """获取总览数据"""
    try:
        # 获取查询参数
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        partner_id = request.args.get('partner_id', type=int)
        
        # 默认时间范围（最近7天）
        if not start_date or not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        # 获取总览数据
        summary_data = asyncio.run(dashboard_service.get_summary_data(
            start_date, end_date, partner_id
        ))
        
        return jsonify({
            "status": "success",
            "data": summary_data,
            "filters": {
                "start_date": start_date,
                "end_date": end_date,
                "partner_id": partner_id
            }
        })
    except Exception as e:
        logger.error(f"获取总览数据失败: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/company-level', methods=['GET'])
def get_company_level():
    """获取公司级别数据"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not start_date or not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        company_data = asyncio.run(dashboard_service.get_company_level_data(
            start_date, end_date
        ))
        
        return jsonify({
            "status": "success", 
            "data": company_data,
            "filters": {"start_date": start_date, "end_date": end_date}
        })
    except Exception as e:
        logger.error(f"获取公司级别数据失败: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/offer-level', methods=['GET'])
def get_offer_level():
    """获取产品级别数据"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        partner_id = request.args.get('partner_id', type=int)
        
        if not start_date or not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        offer_data = asyncio.run(dashboard_service.get_offer_level_data(
            start_date, end_date, partner_id
        ))
        
        return jsonify({
            "status": "success",
            "data": offer_data,
            "filters": {
                "start_date": start_date,
                "end_date": end_date,
                "partner_id": partner_id
            }
        })
    except Exception as e:
        logger.error(f"获取产品级别数据失败: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/partner-level', methods=['GET'])
def get_partner_level():
    """获取合作伙伴级别数据"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not start_date or not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        partner_data = asyncio.run(dashboard_service.get_partner_level_data(
            start_date, end_date
        ))
        
        return jsonify({
            "status": "success",
            "data": partner_data,
            "filters": {"start_date": start_date, "end_date": end_date}
        })
    except Exception as e:
        logger.error(f"获取合作伙伴级别数据失败: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/conversion-report', methods=['GET'])
def get_conversion_report():
    """获取转化报告详细数据"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        partner_id = request.args.get('partner_id', type=int)
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 100, type=int)  # 修改默认值为100
        
        if not start_date or not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        conversion_data = asyncio.run(dashboard_service.get_conversion_report_data(
            start_date, end_date, partner_id, page, limit
        ))
        
        return jsonify({
            "status": "success",
            "data": conversion_data,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": conversion_data.get('total', 0)
            },
            "filters": {
                "start_date": start_date,
                "end_date": end_date,
                "partner_id": partner_id
            }
        })
    except Exception as e:
        logger.error(f"获取转化报告数据失败: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/conversions/detailed', methods=['GET'])
def get_conversions_detailed():
    """获取转化详细数据 - 兼容前端调用"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        partner_id = request.args.get('partner_id', type=int)
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 100, type=int)
        
        if not start_date or not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        conversion_data = asyncio.run(dashboard_service.get_conversion_report_data(
            start_date, end_date, partner_id, page, limit
        ))
        
        return jsonify({
            "status": "success",
            "data": {
                "records": conversion_data.get('records', []),
                "summary": conversion_data.get('summary', {}),
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": conversion_data.get('total', 0),
                    "pages": (conversion_data.get('total', 0) + limit - 1) // limit
                }
            }
        })
    except Exception as e:
        logger.error(f"获取转化详细数据失败: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/filters', methods=['GET'])
def get_filters():
    """获取过滤器选项"""
    try:
        filters = asyncio.run(dashboard_service.get_filter_options())
        return jsonify({"status": "success", "data": filters})
    except Exception as e:
        logger.error(f"获取过滤器选项失败: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# =============================================================================
# 增强版API端点 - 使用新的数据库字段结构
# =============================================================================

@app.route('/api/enhanced/conversion-report', methods=['GET'])
def get_enhanced_conversion_report():
    """获取增强版转化报告详细数据 - 使用新的数据库字段"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        partner_name = request.args.get('partner_name')  # 使用partner_name替代partner_id
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 100, type=int)
        
        # 默认日期范围
        if not start_date or not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        conversion_data = asyncio.run(dashboard_service.get_enhanced_conversion_report_data(
            start_date, end_date, partner_name, page, limit
        ))
        
        return jsonify({
            "status": "success",
            "data": conversion_data,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": conversion_data.get('total', 0),
                "pages": conversion_data.get('pages', 0)
            },
            "filters": {
                "start_date": start_date,
                "end_date": end_date,
                "partner_name": partner_name
            },
            "stats": {
                "total_conversions": conversion_data.get('total', 0),
                "total_sale_amount": conversion_data.get('total_sale_amount', 0),
                "avg_commission_rate": conversion_data.get('avg_commission_rate', 0)
            }
        })
    except Exception as e:
        logger.error(f"获取增强版转化报告数据失败: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/enhanced/filters', methods=['GET'])
def get_enhanced_filters():
    """获取增强版过滤器选项 - 基于新的数据库字段"""
    try:
        filters = asyncio.run(dashboard_service.get_enhanced_filter_options())
        return jsonify({"status": "success", "data": filters})
    except Exception as e:
        logger.error(f"获取增强版过滤器选项失败: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# =============================================================================
# 数据导出功能 (集成reporter-agent)
# =============================================================================

@app.route('/api/export/detailed-report', methods=['POST'])
def export_detailed_report():
    """从详细数据页面导出完整报告（执行reporter-agent）"""
    try:
        data = request.get_json()
        
        # 获取参数
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        partner_id = data.get('partner_id')
        upload_feishu = data.get('upload_feishu', True)
        send_email = data.get('send_email', True)
        
        # 验证参数
        if not start_date or not end_date:
            return jsonify({
                "status": "error",
                "message": "start_date and end_date are required"
            }), 400
        
        # 构建reporter-agent命令
        cmd = [
            "python", "-m", "agents.reporter_agent.main", "generate",
            "--start-date", start_date,
            "--end-date", end_date
        ]
        
        # 如果指定了partner，添加partner参数
        if partner_id:
            # 需要根据partner_id获取partner_name
            partners = asyncio.run(dashboard_service.get_filter_options()).get('partners', [])
            partner_name = None
            for partner in partners:
                if partner.get('id') == partner_id:
                    partner_name = partner.get('partner_name')
                    break
            
            if partner_name:
                cmd.extend(["--partner", partner_name])
        
        if not upload_feishu:
            cmd.append("--no-feishu")
        
        if not send_email:
            cmd.append("--no-email")
        
        # 执行命令
        logger.info(f"执行详细数据导出命令: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=1800  # 30分钟超时
        )
        
        if result.returncode == 0:
            return jsonify({
                "status": "success",
                "message": "详细报告导出成功",
                "details": {
                    "start_date": start_date,
                    "end_date": end_date,
                    "partner_id": partner_id,
                    "upload_feishu": upload_feishu,
                    "send_email": send_email
                }
            })
        else:
            return jsonify({
                "status": "error",
                "message": "详细报告导出失败",
                "details": result.stderr
            }), 500
            
    except subprocess.TimeoutExpired:
        return jsonify({
            "status": "error",
            "message": "详细报告导出超时"
        }), 500
    except Exception as e:
        logger.error(f"导出详细报告失败: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/export/report', methods=['POST'])
def export_report():
    """导出报告（执行reporter-agent）"""
    try:
        data = request.get_json()
        
        # 获取参数
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        partner = data.get('partner', 'all')
        upload_feishu = data.get('upload_feishu', True)
        send_email = data.get('send_email', True)
        
        # 验证参数
        if not start_date or not end_date:
            return jsonify({
                "status": "error",
                "message": "start_date and end_date are required"
            }), 400
        
        # 构建reporter-agent命令
        cmd = [
            "python", f"{project_root}/agents/reporter_agent/main.py",
            "--start-date", start_date,
            "--end-date", end_date,
            "--partner", partner
        ]
        
        if upload_feishu:
            cmd.append("--upload-feishu")
        
        if send_email:
            cmd.append("--send-email")
        
        # 执行命令
        logger.info(f"执行导出命令: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=1800  # 30分钟超时
        )
        
        if result.returncode == 0:
            return jsonify({
                "status": "success",
                "message": "报告导出成功",
                "details": {
                    "start_date": start_date,
                    "end_date": end_date,
                    "partner": partner,
                    "upload_feishu": upload_feishu,
                    "send_email": send_email
                }
            })
        else:
            return jsonify({
                "status": "error",
                "message": "报告导出失败",
                "details": result.stderr
            }), 500
            
    except subprocess.TimeoutExpired:
        return jsonify({
            "status": "error",
            "message": "报告导出超时"
        }), 500
    except Exception as e:
        logger.error(f"导出报告失败: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/export/status', methods=['GET'])
def export_status():
    """获取导出状态"""
    # 这里可以实现异步任务状态查询
    return jsonify({
        "status": "success",
        "message": "Export status endpoint ready"
    })

@app.route('/api/export-report', methods=['POST'])
def export_report_via_agent():
    """调用reporter-agent生成报告"""
    try:
        data = request.get_json()
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        partner_name = data.get('partner_name', 'ALL')
        
        if not start_date or not end_date:
            return jsonify({'success': False, 'error': '缺少日期参数'}), 400
        
        logger.info(f"开始生成报告 - Partner: {partner_name}, 日期: {start_date} 到 {end_date}")
        
        # 构建reporter-agent命令
        cmd = [
            'python', 
            os.path.join(project_root, 'agents/reporter_agent/main.py'),
            'generate',
            '--partner', partner_name,
            '--start-date', start_date,
            '--end-date', end_date,
            '--no-email'  # 暂时禁用邮件发送，避免测试时发送邮件
            # 不使用--no-feishu，保持飞书上传功能
        ]
        
        logger.info(f"执行命令: {' '.join(cmd)}")
        
        # 执行reporter-agent命令
        process = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=300,  # 5分钟超时
            cwd=project_root
        )
        
        if process.returncode == 0:
            # 解析输出获取结果信息
            output = process.stdout
            logger.info(f"Reporter-agent执行成功: {output}")
            
            # 简单解析输出中的统计信息（如果需要更精确，可以修改reporter-agent返回JSON）
            total_records = "0"
            total_amount = "0.00"
            
            # 尝试从输出中提取数字
            for line in output.split('\n'):
                if 'total_records' in line.lower() or '总记录数' in line:
                    import re
                    numbers = re.findall(r'[\d,]+', line)
                    if numbers:
                        total_records = numbers[-1].replace(',', '')
                if 'total_amount' in line.lower() or '总金额' in line:
                    import re
                    amounts = re.findall(r'\$?([\d,]+\.?\d*)', line)
                    if amounts:
                        total_amount = amounts[-1].replace(',', '')
            
            return jsonify({
                'success': True,
                'partner_name': partner_name,
                'start_date': start_date,
                'end_date': end_date,
                'total_records': total_records,
                'total_amount': total_amount,
                'message': '报告生成成功并已上传到飞书'
            })
        else:
            error_msg = process.stderr or '未知错误'
            logger.error(f"Reporter-agent执行失败: {error_msg}")
            return jsonify({
                'success': False,
                'error': f'报告生成失败: {error_msg}'
            }), 500
            
    except subprocess.TimeoutExpired:
        logger.error("Reporter-agent执行超时")
        return jsonify({
            'success': False,
            'error': '报告生成超时，请稍后重试'
        }), 500
    except Exception as e:
        logger.error(f"导出报告时发生错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'服务器内部错误: {str(e)}'
        }), 500

# =============================================================================
# 数据钻取功能
# =============================================================================

@app.route('/api/drill/<data_type>', methods=['GET'])
def drill_data(data_type):
    """数据钻取"""
    try:
        # 获取钻取参数
        filter_key = request.args.get('filter_key')
        filter_value = request.args.get('filter_value')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not filter_key or not filter_value:
            return jsonify({
                "status": "error",
                "message": "filter_key and filter_value are required"
            }), 400
        
        # 获取钻取数据
        drill_result = asyncio.run(dashboard_service.drill_data(
            data_type, filter_key, filter_value, start_date, end_date
        ))
        
        return jsonify({
            "status": "success",
            "data": drill_result,
            "drill_info": {
                "data_type": data_type,
                "filter_key": filter_key,
                "filter_value": filter_value,
                "start_date": start_date,
                "end_date": end_date
            }
        })
    except Exception as e:
        logger.error(f"数据钻取失败: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# =============================================================================
# 错误处理
# =============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({"status": "error", "message": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"status": "error", "message": "Internal server error"}), 500

# =============================================================================
# 启动服务器
# =============================================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    logger.info(f"启动ByteC Performance Dashboard API服务器")
    logger.info(f"端口: {port}")
    logger.info(f"调试模式: {debug}")
    
    app.run(host='0.0.0.0', port=port, debug=debug, threaded=True) 