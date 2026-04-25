import React from 'react';
import { useTranslation } from 'react-i18next';
import ReactECharts from 'echarts-for-react';
import { formatNumber } from '../../utils/format';

/**
 * KPIChart — renders a chart object returned from the backend KPI service.
 * مخطط بياني من بيانات مؤشر الأداء
 *
 * Props:
 *   chart.type     — line | bar | pie | area | stacked_bar | donut
 *   chart.title    — chart title
 *   chart.title_ar — Arabic title
 *   chart.labels   — x-axis labels
 *   chart.datasets — [{ name, name_ar, data, color }]
 *   chart.height   — optional px height (default 300)
 *   currency       — currency label
 */

const KPIChart = ({ chart, currency = '', height: propHeight }) => {
    const { i18n } = useTranslation();
    const isRTL = i18n.dir() === 'rtl';

    if (!chart || !chart.datasets) return null;

    const title = isRTL ? (chart.title_ar || chart.title) : (chart.title || chart.title_ar);
    const h = propHeight || chart.height || 300;
    const type = chart.type || 'line';

    // Build ECharts option based on chart type
    const buildOption = () => {
        const labels = chart.labels || [];
        const datasets = chart.datasets || [];

        const baseTooltip = {
            trigger: type === 'pie' || type === 'donut' ? 'item' : 'axis',
            axisPointer: { type: 'cross', label: { backgroundColor: '#6a7985' } },
            textStyle: { direction: isRTL ? 'rtl' : 'ltr' },
            formatter: type === 'pie' || type === 'donut' ? undefined : (params) => {
                if (!params || params.length === 0) return '';
                let result = `<div style="text-align:${isRTL ? 'right' : 'left'}"><b>${params[0].axisValue}</b><br/>`;
                params.forEach(p => {
                    result += `${p.marker} ${p.seriesName}: <b>${formatNumber(p.value || 0)} ${currency}</b><br/>`;
                });
                return result + '</div>';
            },
        };

        // Pie / Donut
        if (type === 'pie' || type === 'donut') {
            const data = datasets[0]?.data?.map((v, i) => ({
                name: labels[i] || `Item ${i}`,
                value: v,
            })) || [];

            return {
                tooltip: { ...baseTooltip, trigger: 'item' },
                legend: { bottom: 0, type: 'scroll' },
                series: [{
                    type: 'pie',
                    radius: type === 'donut' ? ['45%', '72%'] : '72%',
                    center: ['50%', '45%'],
                    data,
                    label: { show: true, formatter: '{b}: {d}%' },
                    emphasis: { itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0,0,0,.2)' } },
                }],
            };
        }

        // Line / Bar / Area / Stacked bar
        const series = datasets.map(ds => {
            const seriesName = isRTL ? (ds.name_ar || ds.name) : (ds.name || ds.name_ar);
            const base = {
                name: seriesName,
                data: ds.data || [],
                itemStyle: ds.color ? { color: ds.color } : undefined,
                emphasis: { focus: 'series' },
            };

            if (type === 'bar' || type === 'stacked_bar') {
                return { ...base, type: 'bar', stack: type === 'stacked_bar' ? 'total' : undefined, barMaxWidth: 40 };
            }
            if (type === 'area') {
                return {
                    ...base, type: 'line', smooth: true,
                    areaStyle: { opacity: 0.3 },
                    lineStyle: { width: 2.5 },
                    showSymbol: false,
                };
            }
            // default: line
            return { ...base, type: 'line', smooth: true, lineStyle: { width: 2.5 }, showSymbol: false };
        });

        return {
            tooltip: baseTooltip,
            legend: {
                data: series.map(s => s.name),
                bottom: 0,
                type: 'scroll',
            },
            grid: { left: '3%', right: '4%', bottom: '14%', top: '5%', containLabel: true },
            xAxis: {
                type: 'category',
                data: labels,
                axisLine: { lineStyle: { color: '#E5E7EB' } },
                axisLabel: { color: '#6B7280', rotate: labels.length > 12 ? 45 : 0 },
            },
            yAxis: {
                type: 'value',
                axisLine: { show: false },
                axisTick: { show: false },
                splitLine: { lineStyle: { color: '#F3F4F6' } },
                axisLabel: {
                    color: '#6B7280',
                    formatter: v => v >= 1000000 ? `${(v / 1000000).toFixed(1)}M`
                        : v >= 1000 ? `${(v / 1000).toFixed(1)}k` : v,
                },
            },
            series,
        };
    };

    return (
        <div style={{ width: '100%' }}>
            {title && (
                <div style={{
                    fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary, #64748b)',
                    marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.04em',
                }}>
                    {title}
                </div>
            )}
            <ReactECharts
                option={buildOption()}
                style={{ height: h, width: '100%' }}
                opts={{ renderer: 'svg' }}
                notMerge
            />
        </div>
    );
};

export default KPIChart;
