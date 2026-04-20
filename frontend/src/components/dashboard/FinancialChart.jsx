import React from 'react';
import { useTranslation } from 'react-i18next';
import ReactECharts from 'echarts-for-react';
import { formatNumber } from '../../utils/format';

const FinancialChart = ({ data, loading, currency = '' }) => {
    const { t, i18n } = useTranslation();
    const isRTL = i18n.dir() === 'rtl';

    const option = {
        animation: !loading,
        tooltip: {
            trigger: 'axis',
            axisPointer: { type: 'cross', label: { backgroundColor: '#6a7985' } },
            formatter: (params) => {
                if (!params || params.length === 0) return '';
                let result = `<div style="text-align: ${isRTL ? 'right' : 'left'}"><b>${params[0].axisValue}</b><br/>`;
                params.forEach(param => {
                    const value = formatNumber(param.value || 0);
                    result += `${param.marker} ${param.seriesName}: <b>${value} ${currency}</b><br/>`;
                });
                result += '</div>';
                return result;
            }
        },
        legend: {
            data: [t('dashboard.sales'), t('dashboard.expenses')],
            bottom: 0
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '10%',
            top: '5%',
            containLabel: true
        },
        xAxis: [
            {
                type: 'category',
                boundaryGap: false,
                data: (data || []).map(d => d.date ? new Date(d.date).toLocaleDateString(i18n.language) : ''),
                axisLine: { lineStyle: { color: '#E5E7EB' } },
                axisLabel: { color: '#6B7280' }
            }
        ],
        yAxis: [
            {
                type: 'value',
                axisLine: { show: false },
                axisTick: { show: false },
                splitLine: { lineStyle: { color: '#F3F4F6' } },
                axisLabel: {
                    color: '#6B7280',
                    formatter: (value) => {
                        if (value >= 1000) return `${(value / 1000).toFixed(1)}k`;
                        return value;
                    }
                }
            }
        ],
        series: [
            {
                name: t('dashboard.sales'),
                type: 'line',
                smooth: true,
                lineStyle: { width: 3, color: '#3B82F6' },
                showSymbol: false,
                areaStyle: {
                    opacity: 0.8,
                    color: {
                        type: 'linear',
                        x: 0, y: 0, x2: 0, y2: 1,
                        colorStops: [{ offset: 0, color: 'rgba(59, 130, 246, 0.4)' }, { offset: 1, color: 'rgba(59, 130, 246, 0.05)' }]
                    }
                },
                emphasis: { focus: 'series' },
                data: (data || []).map(d => d.sales || 0)
            },
            {
                name: t('dashboard.expenses'),
                type: 'line',
                smooth: true,
                lineStyle: { width: 3, color: '#EF4444' },
                showSymbol: false,
                areaStyle: {
                    opacity: 0.8,
                    color: {
                        type: 'linear',
                        x: 0, y: 0, x2: 0, y2: 1,
                        colorStops: [{ offset: 0, color: 'rgba(239, 68, 68, 0.4)' }, { offset: 1, color: 'rgba(239, 68, 68, 0.05)' }]
                    }
                },
                emphasis: { focus: 'series' },
                data: (data || []).map(d => d.expenses || 0)
            }
        ]
    };

    return (
        <div className="card h-full">
            <h3 className="text-lg font-bold text-slate-800 mb-6 flex items-center gap-2">
                <span className="p-1.5 rounded-lg bg-blue-50 text-blue-600">📊</span>
                {t('dashboard.financial_overview')}
            </h3>
            <div className="relative" style={{ height: '350px' }}>
                {loading && (
                    <div className="absolute inset-0 bg-white/50 z-10 flex items-center justify-center rounded-lg">
                        <div className="h-full w-full bg-slate-50 animate-pulse rounded-lg flex items-center justify-center">
                            <span className="text-slate-400 text-sm">{t('common.loading')}...</span>
                        </div>
                    </div>
                )}
                <ReactECharts
                    option={option}
                    style={{ height: '100%', width: '100%' }}
                    notMerge={true}
                    lazyUpdate={true}
                />
            </div>
        </div>
    );
};

export default FinancialChart;
