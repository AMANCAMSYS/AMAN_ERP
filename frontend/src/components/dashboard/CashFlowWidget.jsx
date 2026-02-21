import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import api from '../../utils/api';
import ReactECharts from 'echarts-for-react';
import { formatNumber } from '../../utils/format';

const CashFlowWidget = ({ config = {}, currency = '' }) => {
    const { t, i18n } = useTranslation();
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(true);
    const days = config.days || 30;

    useEffect(() => {
        api.get('/dashboard/widgets/cash-flow', { params: { days } })
            .then(res => setData(res.data?.data || []))
            .catch(() => {})
            .finally(() => setLoading(false));
    }, [days]);

    if (loading) return <div className="animate-pulse h-[250px] bg-slate-100 rounded-lg" />;
    if (!data.length) return <div className="text-sm text-slate-400 text-center py-12">لا توجد بيانات</div>;

    const option = {
        tooltip: {
            trigger: 'axis',
            formatter: (params) => {
                if (!params?.length) return '';
                let html = `<div style="text-align: ${i18n.dir() === 'rtl' ? 'right' : 'left'}"><b>${params[0].axisValue}</b><br/>`;
                params.forEach(p => {
                    html += `${p.marker} ${p.seriesName}: <b>${formatNumber(p.value)} ${currency}</b><br/>`;
                });
                return html + '</div>';
            }
        },
        legend: { bottom: 0, textStyle: { fontSize: 11 } },
        grid: { left: '3%', right: '4%', bottom: '15%', top: '8%', containLabel: true },
        xAxis: {
            type: 'category',
            data: data.map(d => d.date ? new Date(d.date).toLocaleDateString(i18n.language, { month: 'short', day: 'numeric' }) : ''),
            axisLabel: { color: '#6B7280', fontSize: 10, interval: Math.floor(data.length / 8) },
            axisLine: { lineStyle: { color: '#E5E7EB' } }
        },
        yAxis: {
            type: 'value',
            axisLine: { show: false },
            splitLine: { lineStyle: { color: '#F3F4F6' } },
            axisLabel: { color: '#6B7280', formatter: v => v >= 1000 ? `${(v/1000).toFixed(0)}k` : v }
        },
        series: [
            {
                name: t('dashboard.inflow') || 'التدفق الداخل',
                type: 'bar',
                stack: 'flow',
                data: data.map(d => d.inflow || 0),
                itemStyle: { color: '#34D399', borderRadius: [2, 2, 0, 0] },
                barWidth: '60%'
            },
            {
                name: t('dashboard.outflow') || 'التدفق الخارج',
                type: 'bar',
                stack: 'flow',
                data: data.map(d => -(d.outflow || 0)),
                itemStyle: { color: '#F87171', borderRadius: [0, 0, 2, 2] },
                barWidth: '60%'
            },
            {
                name: t('dashboard.net_flow') || 'الصافي',
                type: 'line',
                smooth: true,
                data: data.map(d => d.net || 0),
                lineStyle: { width: 2, color: '#6366F1' },
                showSymbol: false,
                z: 10,
            }
        ]
    };

    return <ReactECharts option={option} style={{ height: '100%', minHeight: '250px' }} />;
};

export default CashFlowWidget;
