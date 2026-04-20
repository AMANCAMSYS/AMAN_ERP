import React from 'react';
import { useTranslation } from 'react-i18next';
import ReactECharts from 'echarts-for-react';

const TopProductsChart = ({ data, loading, currency = '' }) => {
    const { t } = useTranslation();

    const option = {
        animation: !loading,
        tooltip: {
            trigger: 'axis',
            axisPointer: { type: 'shadow' },
            formatter: (params) => {
                if (!params || params.length === 0) return '';
                const value = params[0].value ? params[0].value.toLocaleString() : '0';
                return `${params[0].name}<br/>${params[0].marker} <b>${value} ${currency}</b>`;
            }
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            top: '5%',
            containLabel: true
        },
        xAxis: {
            type: 'value',
            axisLine: { show: false },
            axisTick: { show: false },
            splitLine: { lineStyle: { color: '#F3F4F6' } },
            axisLabel: { color: '#6B7280' }
        },
        yAxis: {
            type: 'category',
            data: (data || []).map(item => item.name || ''),
            axisLine: { show: false },
            axisTick: { show: false },
            axisLabel: {
                color: '#374151',
                width: 100,
                overflow: 'truncate'
            }
        },
        series: [
            {
                name: t('dashboard.sales'),
                type: 'bar',
                data: (data || []).map((item, index) => ({
                    value: item.value || 0,
                    itemStyle: {
                        color: {
                            type: 'linear',
                            x: 0, y: 0, x2: 1, y2: 0,
                            colorStops: [
                                { offset: 0, color: ['#60A5FA', '#34D399', '#FBBF24', '#F87171', '#818CF8'][index % 5] },
                                { offset: 1, color: ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#6366F1'][index % 5] }
                            ]
                        },
                        borderRadius: [0, 4, 4, 0]
                    }
                })),
                barWidth: '60%',
                label: {
                    show: true,
                    position: 'right',
                    formatter: (params) => params.value >= 1000 ? `${(params.value / 1000).toFixed(1)}k` : params.value
                }
            }
        ]
    };

    return (
        <div className="card h-full">
            <h3 className="text-lg font-bold text-slate-800 mb-6 flex items-center gap-2">
                <span className="p-1.5 rounded-lg bg-emerald-50 text-emerald-600">🏆</span>
                {t('dashboard.top_products')}
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

export default TopProductsChart;
