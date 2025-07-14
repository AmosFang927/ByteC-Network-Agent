/**
 * ByteC Performance Dashboard - 核心JavaScript文件
 * 包含通用功能和工具函数
 */

// 全局Dashboard对象
const Dashboard = {
    // 配置
    config: {
        dateFormat: 'YYYY-MM-DD',
        apiTimeout: 30000,
        refreshInterval: 30000
    },
    
    // 状态管理
    state: {
        currentDateRange: null,
        currentPartner: null,
        autoRefresh: false,
        refreshTimer: null
    },
    
    // 初始化
    init: function() {
        this.setupDateRangePicker();
        this.setupEventHandlers();
        this.loadFilters();
        this.updateCurrentPage();
    },
    
    // 设置日期范围选择器
    setupDateRangePicker: function() {
        const today = moment();
        const weekAgo = moment().subtract(7, 'days');
        
        $('#daterange').daterangepicker({
            startDate: weekAgo,
            endDate: today,
            maxDate: today,
            ranges: {
                '今天': [today, today],
                '昨天': [moment().subtract(1, 'days'), moment().subtract(1, 'days')],
                '最近7天': [moment().subtract(6, 'days'), today],
                '最近30天': [moment().subtract(29, 'days'), today],
                '本月': [moment().startOf('month'), today],
                '上月': [moment().subtract(1, 'month').startOf('month'), moment().subtract(1, 'month').endOf('month')]
            },
            locale: {
                format: 'YYYY-MM-DD',
                separator: ' 至 ',
                applyLabel: '确定',
                cancelLabel: '取消',
                fromLabel: '从',
                toLabel: '到',
                customRangeLabel: '自定义范围',
                weekLabel: '周',
                daysOfWeek: ['日', '一', '二', '三', '四', '五', '六'],
                monthNames: ['一月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '十一月', '十二月']
            }
        });
        
        // 设置初始值
        this.state.currentDateRange = {
            start: weekAgo.format(this.config.dateFormat),
            end: today.format(this.config.dateFormat)
        };
    },
    
    // 设置事件处理器
    setupEventHandlers: function() {
        // 日期范围变化
        $('#daterange').on('apply.daterangepicker', (ev, picker) => {
            this.state.currentDateRange = {
                start: picker.startDate.format(this.config.dateFormat),
                end: picker.endDate.format(this.config.dateFormat)
            };
            this.refreshCurrentPage();
        });
        
        // 导出按钮
        $('#exportBtn').on('click', () => {
            this.showExportModal();
        });
        
        // 刷新按钮
        $('#refreshBtn').on('click', () => {
            this.refreshCurrentPage();
        });
        
        // 确认导出
        $('#confirmExport').on('click', () => {
            this.performExport();
        });
        
        // 自动刷新切换
        $(document).on('change', '#autoRefreshToggle', (e) => {
            this.toggleAutoRefresh(e.target.checked);
        });
    },
    
    // 加载过滤器选项
    loadFilters: function() {
        $.ajax({
            url: '/api/enhanced/filters',
            timeout: this.config.apiTimeout,
            success: (response) => {
                if (response.status === 'success') {
                    this.populateFilters(response.data);
                }
            },
            error: (xhr) => {
                console.error('加载过滤器失败:', xhr);
            }
        });
    },
    
    // 填充过滤器选项
    populateFilters: function(data) {
        // 填充合作伙伴下拉框
        const partnerSelects = $('#partnerFilter, #exportPartner');
        partnerSelects.empty();
        
        if (data.partners && data.partners.length > 0) {
            data.partners.forEach(partner => {
                partnerSelects.append(`<option value="${partner.partner_name}">${partner.partner_name} (${partner.conversion_count})</option>`);
            });
        }
    },
    
    // 获取当前日期范围参数
    getDateRangeParams: function() {
        const range = this.state.currentDateRange;
        return {
            start_date: range.start,
            end_date: range.end
        };
    },
    
    // 显示加载动画
    showLoading: function() {
        $('#loadingOverlay').addClass('show');
    },
    
    // 隐藏加载动画
    hideLoading: function() {
        $('#loadingOverlay').removeClass('show');
    },
    
    // 显示错误信息
    showError: function(message) {
        this.showAlert(message, 'danger');
    },
    
    // 显示成功信息
    showSuccess: function(message) {
        this.showAlert(message, 'success');
    },
    
    // 显示警告信息
    showWarning: function(message) {
        this.showAlert(message, 'warning');
    },
    
    // 显示提示信息
    showAlert: function(message, type = 'info') {
        const alertHtml = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        // 移除现有的提示
        $('.alert').remove();
        
        // 添加新的提示
        $('main').prepend(alertHtml);
        
        // 自动关闭
        setTimeout(() => {
            $('.alert').alert('close');
        }, 5000);
    },
    
    // 显示导出模态框
    showExportModal: function() {
        const range = this.state.currentDateRange;
        $('#exportStartDate').val(range.start);
        $('#exportEndDate').val(range.end);
        $('#exportModal').modal('show');
    },
    
    // 执行导出
    performExport: function() {
        const formData = {
            start_date: $('#exportStartDate').val(),
            end_date: $('#exportEndDate').val(),
            partner: $('#exportPartner').val() || 'all',
            upload_feishu: $('#uploadFeishu').prop('checked'),
            send_email: $('#sendEmail').prop('checked')
        };
        
        // 验证日期
        if (!formData.start_date || !formData.end_date) {
            this.showError('请选择有效的日期范围');
            return;
        }
        
        if (moment(formData.start_date).isAfter(moment(formData.end_date))) {
            this.showError('开始日期不能晚于结束日期');
            return;
        }
        
        // 显示加载状态
        const exportBtn = $('#confirmExport');
        const originalText = exportBtn.html();
        exportBtn.html('<i class="fas fa-spinner fa-spin me-1"></i>导出中...').prop('disabled', true);
        
        $.ajax({
            url: '/api/export/report',
            method: 'POST',
            data: JSON.stringify(formData),
            contentType: 'application/json',
            timeout: 1800000, // 30分钟超时
            success: (response) => {
                exportBtn.html(originalText).prop('disabled', false);
                $('#exportModal').modal('hide');
                
                if (response.status === 'success') {
                    this.showSuccess('报告导出成功！');
                } else {
                    this.showError('导出失败: ' + response.message);
                }
            },
            error: (xhr) => {
                exportBtn.html(originalText).prop('disabled', false);
                
                if (xhr.status === 500) {
                    this.showError('服务器错误，请稍后重试');
                } else if (xhr.status === 408) {
                    this.showError('导出超时，请缩小日期范围后重试');
                } else {
                    this.showError('导出失败，请检查网络连接');
                }
            }
        });
    },
    
    // 切换自动刷新
    toggleAutoRefresh: function(enabled) {
        this.state.autoRefresh = enabled;
        
        if (enabled) {
            this.state.refreshTimer = setInterval(() => {
                this.refreshCurrentPage();
            }, this.config.refreshInterval);
            this.showSuccess('自动刷新已启用');
        } else {
            if (this.state.refreshTimer) {
                clearInterval(this.state.refreshTimer);
                this.state.refreshTimer = null;
            }
            this.showSuccess('自动刷新已禁用');
        }
    },
    
    // 刷新当前页面数据
    refreshCurrentPage: function() {
        const currentPath = window.location.pathname;
        
        if (typeof SummaryDashboard !== 'undefined' && SummaryDashboard.loadData) {
            SummaryDashboard.loadData();
        } else if (typeof CompanyDashboard !== 'undefined' && CompanyDashboard.loadData) {
            CompanyDashboard.loadData();
        } else if (typeof OfferDashboard !== 'undefined' && OfferDashboard.loadData) {
            OfferDashboard.loadData();
        } else if (typeof PartnerDashboard !== 'undefined' && PartnerDashboard.loadData) {
            PartnerDashboard.loadData();
        } else if (typeof ConversionDashboard !== 'undefined' && ConversionDashboard.loadData) {
            ConversionDashboard.loadData();
        }
    },
    
    // 更新当前页面状态
    updateCurrentPage: function() {
        const currentPath = window.location.pathname;
        
        // 高亮当前页面导航
        $('.navbar-nav .nav-link').removeClass('active');
        $(`.navbar-nav .nav-link[href="${currentPath}"]`).addClass('active');
        
        // 如果在首页，高亮总览
        if (currentPath === '/') {
            $('.navbar-nav .nav-link[href="/summary"]').addClass('active');
        }
    },
    
    // 格式化数字
    formatNumber: function(num) {
        return new Intl.NumberFormat('zh-CN').format(num || 0);
    },
    
    // 格式化货币
    formatCurrency: function(amount) {
        return new Intl.NumberFormat('zh-CN', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 2
        }).format(amount || 0);
    },
    
    // 格式化百分比
    formatPercent: function(value) {
        return new Intl.NumberFormat('zh-CN', {
            style: 'percent',
            minimumFractionDigits: 2
        }).format(value || 0);
    },
    
    // 格式化日期
    formatDate: function(date) {
        return moment(date).format('YYYY-MM-DD');
    },
    
    // 格式化日期时间
    formatDateTime: function(datetime) {
        return moment(datetime).format('YYYY-MM-DD HH:mm:ss');
    },
    
    // 获取相对时间
    getRelativeTime: function(datetime) {
        return moment(datetime).fromNow();
    },
    
    // 颜色辅助函数
    getStatusColor: function(status) {
        const colors = {
            'active': '#28a745',
            'inactive': '#dc3545',
            'pending': '#ffc107',
            'success': '#28a745',
            'warning': '#ffc107',
            'danger': '#dc3545',
            'info': '#17a2b8'
        };
        return colors[status] || '#6c757d';
    },
    
    // 防抖函数
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    // 节流函数
    throttle: function(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
};

// 页面加载完成后初始化
$(document).ready(function() {
    Dashboard.init();
});

// 防止页面卸载时的内存泄漏
$(window).on('beforeunload', function() {
    if (Dashboard.state.refreshTimer) {
        clearInterval(Dashboard.state.refreshTimer);
    }
}); 