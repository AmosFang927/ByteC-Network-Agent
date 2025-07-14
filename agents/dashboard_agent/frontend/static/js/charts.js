/**
 * ByteC Performance Dashboard - 图表辅助文件
 * 使用Chart.js生成各种图表
 */

const Charts = {
    // 默认配置
    defaultConfig: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: true,
                position: 'top'
            },
            tooltip: {
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                titleColor: '#fff',
                bodyColor: '#fff',
                borderColor: 'rgba(255, 255, 255, 0.1)',
                borderWidth: 1
            }
        },
        interaction: {
            intersect: false,
            mode: 'index'
        }
    },
    
    // 颜色配置
    colors: {
        primary: '#007bff',
        secondary: '#6c757d',
        success: '#28a745',
        danger: '#dc3545',
        warning: '#ffc107',
        info: '#17a2b8',
        light: '#f8f9fa',
        dark: '#343a40'
    },
    
    // 创建每日趋势图
    createDailyTrendChart: function(canvasId, data) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        
        const labels = data.map(item => moment(item.date).format('MM-DD'));
        const conversions = data.map(item => item.conversions || 0);
        const sales = data.map(item => item.total_sales || 0);
        
        return new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: '转化数',
                    data: conversions,
                    borderColor: this.colors.primary,
                    backgroundColor: this.colors.primary + '20',
                    fill: false,
                    tension: 0.4,
                    yAxisID: 'y'
                }, {
                    label: '销售额 ($)',
                    data: sales,
                    borderColor: this.colors.success,
                    backgroundColor: this.colors.success + '20',
                    fill: false,
                    tension: 0.4,
                    yAxisID: 'y1'
                }]
            },
            options: {
                ...this.defaultConfig,
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: '转化数'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: '销售额 ($)'
                        },
                        grid: {
                            drawOnChartArea: false,
                        },
                    }
                },
                plugins: {
                    ...this.defaultConfig.plugins,
                    title: {
                        display: true,
                        text: '每日转化趋势'
                    }
                }
            }
        });
    },
    
    // 创建小时分布图
    createHourlyDistributionChart: function(canvasId, data) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        
        // 创建24小时的完整数据
        const hourlyData = Array.from({length: 24}, (_, i) => {
            const hourData = data.find(item => parseInt(item.hour) === i);
            return {
                hour: i,
                conversions: hourData ? hourData.conversions : 0
            };
        });
        
        const labels = hourlyData.map(item => item.hour + ':00');
        const conversions = hourlyData.map(item => item.conversions);
        
        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: '转化数',
                    data: conversions,
                    backgroundColor: this.colors.info + '80',
                    borderColor: this.colors.info,
                    borderWidth: 1
                }]
            },
            options: {
                ...this.defaultConfig,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: '转化数'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: '小时'
                        }
                    }
                },
                plugins: {
                    ...this.defaultConfig.plugins,
                    title: {
                        display: true,
                        text: '24小时转化分布'
                    }
                }
            }
        });
    },
    
    // 创建合作伙伴表现图
    createPartnerPerformanceChart: function(canvasId, data) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        
        const labels = data.map(item => item.partner_name || item.name);
        const conversions = data.map(item => item.conversions || 0);
        
        return new Chart(ctx, {
            type: 'horizontalBar',
            data: {
                labels: labels,
                datasets: [{
                    label: '转化数',
                    data: conversions,
                    backgroundColor: this.colors.warning + '80',
                    borderColor: this.colors.warning,
                    borderWidth: 1
                }]
            },
            options: {
                ...this.defaultConfig,
                indexAxis: 'y',
                scales: {
                    x: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: '转化数'
                        }
                    }
                },
                plugins: {
                    ...this.defaultConfig.plugins,
                    title: {
                        display: true,
                        text: '合作伙伴表现'
                    }
                }
            }
        });
    },
    
    // 创建公司表现饼图
    createCompanyPieChart: function(canvasId, data) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        
        const labels = data.map(item => item.company);
        const conversions = data.map(item => item.conversions || 0);
        
        const colors = [
            this.colors.primary,
            this.colors.success,
            this.colors.warning,
            this.colors.danger,
            this.colors.info,
            this.colors.secondary
        ];
        
        return new Chart(ctx, {
            type: 'pie',
            data: {
                labels: labels,
                datasets: [{
                    data: conversions,
                    backgroundColor: colors.map(color => color + '80'),
                    borderColor: colors,
                    borderWidth: 2
                }]
            },
            options: {
                ...this.defaultConfig,
                plugins: {
                    ...this.defaultConfig.plugins,
                    title: {
                        display: true,
                        text: '公司转化分布'
                    }
                }
            }
        });
    },
    
    // 创建地区分布图
    createRegionChart: function(canvasId, data) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        
        const labels = data.map(item => item.region);
        const conversions = data.map(item => item.conversions || 0);
        const sales = data.map(item => item.total_sales || 0);
        
        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: '转化数',
                    data: conversions,
                    backgroundColor: this.colors.primary + '80',
                    borderColor: this.colors.primary,
                    borderWidth: 1,
                    yAxisID: 'y'
                }, {
                    label: '销售额 ($)',
                    data: sales,
                    backgroundColor: this.colors.success + '80',
                    borderColor: this.colors.success,
                    borderWidth: 1,
                    yAxisID: 'y1'
                }]
            },
            options: {
                ...this.defaultConfig,
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: '转化数'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: '销售额 ($)'
                        },
                        grid: {
                            drawOnChartArea: false,
                        },
                    }
                },
                plugins: {
                    ...this.defaultConfig.plugins,
                    title: {
                        display: true,
                        text: '地区表现对比'
                    }
                }
            }
        });
    },
    
    // 创建产品表现图
    createOfferPerformanceChart: function(canvasId, data) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        
        // 取前10个产品
        const topData = data.slice(0, 10);
        const labels = topData.map(item => {
            const name = item.offer_name || '';
            return name.length > 20 ? name.substring(0, 20) + '...' : name;
        });
        const conversions = topData.map(item => item.conversions || 0);
        const sales = topData.map(item => item.total_sales || 0);
        
        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: '转化数',
                    data: conversions,
                    backgroundColor: this.colors.danger + '80',
                    borderColor: this.colors.danger,
                    borderWidth: 1
                }]
            },
            options: {
                ...this.defaultConfig,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: '转化数'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: '产品名称'
                        },
                        ticks: {
                            maxRotation: 45,
                            minRotation: 45
                        }
                    }
                },
                plugins: {
                    ...this.defaultConfig.plugins,
                    title: {
                        display: true,
                        text: '产品表现 (前10名)'
                    }
                }
            }
        });
    },
    
    // 创建转化漏斗图
    createConversionFunnelChart: function(canvasId, data) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        
        // 模拟漏斗数据
        const funnelData = [
            { stage: '访问', count: data.visits || 10000 },
            { stage: '点击', count: data.clicks || 5000 },
            { stage: '转化', count: data.conversions || 500 },
            { stage: '付费', count: data.paid || 300 }
        ];
        
        const labels = funnelData.map(item => item.stage);
        const counts = funnelData.map(item => item.count);
        
        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: '数量',
                    data: counts,
                    backgroundColor: [
                        this.colors.primary + '80',
                        this.colors.info + '80',
                        this.colors.success + '80',
                        this.colors.warning + '80'
                    ],
                    borderColor: [
                        this.colors.primary,
                        this.colors.info,
                        this.colors.success,
                        this.colors.warning
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                ...this.defaultConfig,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: '数量'
                        }
                    }
                },
                plugins: {
                    ...this.defaultConfig.plugins,
                    title: {
                        display: true,
                        text: '转化漏斗'
                    }
                }
            }
        });
    },
    
    // 销毁图表
    destroyChart: function(chart) {
        if (chart && typeof chart.destroy === 'function') {
            chart.destroy();
        }
    },
    
    // 更新图表数据
    updateChartData: function(chart, newData) {
        if (chart && chart.data) {
            chart.data.datasets[0].data = newData;
            chart.update();
        }
    },
    
    // 导出图表为图片
    exportChartAsImage: function(chart, filename = 'chart.png') {
        if (chart && chart.canvas) {
            const link = document.createElement('a');
            link.download = filename;
            link.href = chart.canvas.toDataURL('image/png');
            link.click();
        }
    }
}; 