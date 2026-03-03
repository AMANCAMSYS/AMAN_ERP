import React from 'react';
import { useTranslation } from 'react-i18next';
import ReactECharts from 'echarts-for-react';
import { formatNumber } from '../../utils/format';

/**
 * KPIGauge — radial gauge for single percentage KPIs (e.g. OEE, Saudization, Gross Margin).
 * عداد دائري لمؤشر أداء بنسبة مئوية
 *
 * Props:
 *   value     — 0–100
 *   label     — gauge title
 *   status    — good | warning | danger | neutral
 *   target    — optional target line
 *   suffix    — "%" by default
 *   size      — px height (default 200)
 */

const STATUS_GAUGE_COLORS = {
    good:    [[0.7, '#22c55e'], [0.85, '#86efac'], [1, '#bbf7d0']],
    warning: [[0.5, '#f59e0b'], [0.75, '#fbbf24'], [1, '#fde68a']],
    danger:  [[0.4, '#ef4444'], [0.65, '#f87171'], [1, '#fca5a5']],
    neutral: [[0.5, '#3b82f6'], [0.75, '#60a5fa'], [1, '#93c5fd']],
};

const KPIGauge = ({
    value = 0,
    label = '',
    status = 'neutral',
    target,
    suffix = '%',
    size = 200,
}) => {
    const { i18n } = useTranslation();

    const axisLineColors = STATUS_GAUGE_COLORS[status] || STATUS_GAUGE_COLORS.neutral;

    const option = {
        animation: true,
        series: [
            {
                type: 'gauge',
                startAngle: 200,
                endAngle: -20,
                min: 0,
                max: 100,
                radius: '90%',
                itemStyle: { color: axisLineColors[0][1] },
                progress: {
                    show: true,
                    width: 12,
                    roundCap: true,
                },
                pointer: { show: false },
                axisLine: {
                    lineStyle: { width: 12, color: [[1, '#e2e8f0']] },
                    roundCap: true,
                },
                axisTick: { show: false },
                splitLine: { show: false },
                axisLabel: { show: false },
                title: {
                    show: true,
                    offsetCenter: [0, '65%'],
                    fontSize: 12,
                    fontWeight: 600,
                    color: '#64748b',
                },
                detail: {
                    valueAnimation: true,
                    offsetCenter: [0, '20%'],
                    fontSize: size > 180 ? 28 : 22,
                    fontWeight: 700,
                    formatter: `{value}${suffix}`,
                    color: '#1e293b',
                },
                data: [{ value: Math.round(value * 10) / 10, name: label }],
            },
        ],
    };

    // Add target marker if present
    if (target != null) {
        option.series.push({
            type: 'gauge',
            startAngle: 200,
            endAngle: -20,
            min: 0,
            max: 100,
            radius: '90%',
            pointer: {
                show: true,
                length: '60%',
                width: 2,
                itemStyle: { color: '#94a3b8' },
            },
            progress: { show: false },
            axisLine: { show: false },
            axisTick: { show: false },
            splitLine: { show: false },
            axisLabel: { show: false },
            title: { show: false },
            detail: { show: false },
            data: [{ value: target }],
        });
    }

    return (
        <div style={{ width: '100%', display: 'flex', justifyContent: 'center' }}>
            <ReactECharts
                option={option}
                style={{ height: size, width: size }}
                opts={{ renderer: 'svg' }}
            />
        </div>
    );
};

export default KPIGauge;
