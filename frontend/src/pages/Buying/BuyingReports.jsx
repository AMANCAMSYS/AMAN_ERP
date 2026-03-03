import { useState, useEffect } from 'react';
import { reportsAPI } from '../../utils/api';
import { getCurrency } from '../../utils/auth';
import ReactECharts from 'echarts-for-react';
import { useTranslation } from 'react-i18next';
import { useBranch } from '../../context/BranchContext';
import { formatNumber } from '../../utils/format';
import BackButton from '../../components/common/BackButton';
import CustomDatePicker from '../../components/common/CustomDatePicker';
import { ModuleKPISection } from '../../components/kpi';

const BuyingReports = () => {
    const { t } = useTranslation();
    const [loading, setLoading] = useState(true);
    const [summary, setSummary] = useState(null);
    const [trend, setTrend] = useState([]);
    const [topSuppliers, setTopSuppliers] = useState([]);
    const currency = getCurrency();
    const { currentBranch } = useBranch();
    const [dates, setDates] = useState({
        start: new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split('T')[0],
        end: new Date().toISOString().split('T')[0]
    });

    useEffect(() => {
        fetchReports();
    }, [currentBranch, dates]);

    const fetchReports = async () => {
        try {
            setLoading(true);
            const branchId = currentBranch ? currentBranch.id : null;
            const daysDiff = Math.ceil((new Date(dates.end) - new Date(dates.start)) / (1000 * 60 * 60 * 24)) || 30;
            const [sumRes, trendRes, suppRes] = await Promise.all([
                reportsAPI.getPurchasesSummary({ branch_id: branchId, start_date: dates.start, end_date: dates.end }),
                reportsAPI.getPurchasesTrend(daysDiff, branchId),
                reportsAPI.getPurchasesBySupplier(5, branchId)
            ]);

            setSummary(sumRes.data.stats);
            setTrend(trendRes.data);
            setTopSuppliers(suppRes.data);
        } catch (error) {
            console.error("Failed to load reports", error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <div className="p-8 text-center">{t('common.loading')}</div>;

    const trendChartOption = {
        tooltip: {
            trigger: 'axis',
            axisPointer: { type: 'cross' },
            formatter: (params) => {
                const data = params[0];
                return `${data.axisValue}<br/>${t('buying.reports.analytics.charts.purchases_series')}: <b>${formatNumber(data.value)} ${currency}</b>`;
            }
        },
        legend: { data: [t('buying.reports.analytics.charts.purchases_series')], bottom: 0 },
        grid: { left: '3%', right: '4%', bottom: '15%', top: '10%', containLabel: true },
        xAxis: {
            type: 'category',
            data: trend.map(d => d.date),
            axisLabel: { rotate: 45, fontSize: 10 }
        },
        yAxis: {
            type: 'value',
            axisLabel: { formatter: (val) => val >= 1000 ? `${val / 1000}K` : val }
        },
        series: [{
            name: t('buying.reports.analytics.charts.purchases_series'),
            type: 'line',
            smooth: true,
            data: trend.map(d => d.total),
            areaStyle: {
                color: {
                    type: 'linear',
                    x: 0, y: 0, x2: 0, y2: 1,
                    colorStops: [
                        { offset: 0, color: 'rgba(59, 130, 246, 0.4)' },
                        { offset: 1, color: 'rgba(59, 130, 246, 0.05)' }
                    ]
                }
            },
            lineStyle: { color: '#3B82F6', width: 3 },
            itemStyle: { color: '#3B82F6' },
            symbol: 'circle',
            symbolSize: 8
        }],
        toolbox: {
            show: true,
            feature: {
                saveAsImage: { title: t('common.save') },
                dataZoom: { title: { zoom: t('buying.reports.analytics.charts.zoom'), back: t('buying.reports.analytics.charts.back') } }
            }
        }
    };

    const suppliersChartOption = {
        tooltip: {
            trigger: 'axis',
            axisPointer: { type: 'shadow' },
            formatter: (params) => `${params[0].name}: <b>${formatNumber(params[0].value)} ${currency}</b>`
        },
        grid: { left: '3%', right: '4%', bottom: '3%', top: '10%', containLabel: true },
        xAxis: { type: 'value' },
        yAxis: {
            type: 'category',
            data: topSuppliers.map(s => s.name),
            axisLabel: { fontSize: 11 }
        },
        series: [{
            type: 'bar',
            data: topSuppliers.map(s => s.value),
            itemStyle: {
                color: {
                    type: 'linear',
                    x: 0, y: 0, x2: 1, y2: 0,
                    colorStops: [
                        { offset: 0, color: '#3B82F6' },
                        { offset: 1, color: '#6366F1' }
                    ]
                },
                borderRadius: [0, 4, 4, 0]
            },
            label: {
                show: true,
                position: 'right',
                formatter: (params) => formatNumber(params.value)
            }
        }],
        toolbox: {
            show: true,
            feature: { saveAsImage: { title: t('common.save') } }
        }
    };

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <div className="header-title">
                    <h1 className="workspace-title">📉 {t('buying.reports.analytics.title')}</h1>
                    <p className="workspace-subtitle">{t('buying.reports.analytics.subtitle')}</p>
                </div>
                <div className="header-actions">
                    <CustomDatePicker
                        label={t('common.start_date')}
                        selected={dates.start}
                        onChange={(d) => setDates(prev => ({ ...prev, start: d }))}
                    />
                    <CustomDatePicker
                        label={t('common.end_date')}
                        selected={dates.end}
                        onChange={(d) => setDates(prev => ({ ...prev, end: d }))}
                    />
                    <button onClick={fetchReports} className="btn btn-secondary">🔄 {t('buying.reports.analytics.update')}</button>
                </div>
            </div>

            {/* KPI Performance Indicators */}
            <ModuleKPISection roleKey="procurement" color="#d97706" defaultOpen={false} />

            {/* Summary Cards */}
            <div className="metrics-grid">
                <div className="metric-card">
                    <div className="metric-label">{t('buying.reports.analytics.metrics.total_purchases')}</div>
                    <div className="metric-value text-primary">
                        {formatNumber(summary?.total_purchases)} <small>{currency}</small>
                    </div>
                </div>
                <div className="metric-card">
                    <div className="metric-label">{t('buying.reports.analytics.metrics.invoice_count')}</div>
                    <div className="metric-value text-secondary">
                        {summary?.invoice_count}
                    </div>
                </div>
                <div className="metric-card">
                    <div className="metric-label">{t('buying.reports.analytics.metrics.total_paid')}</div>
                    <div className="metric-value text-success">
                        {formatNumber(summary?.total_paid)} <small>{currency}</small>
                    </div>
                </div>
            </div>

            {/* Charts */}
            <div className="modules-grid">
                {/* Purchase Trend */}
                <div className="section-card">
                    <h3 className="section-title">📉 {t('buying.reports.analytics.charts.trend')}</h3>
                    <ReactECharts
                        option={trendChartOption}
                        style={{ height: '350px', width: '100%' }}
                        opts={{ renderer: 'canvas' }}
                        notMerge={true}
                        lazyUpdate={true}
                    />
                </div>

                {/* Top Suppliers */}
                <div className="section-card">
                    <h3 className="section-title">🏭 {t('buying.reports.analytics.charts.top_suppliers')}</h3>
                    <ReactECharts
                        option={suppliersChartOption}
                        style={{ height: '350px', width: '100%' }}
                        opts={{ renderer: 'canvas' }}
                        notMerge={true}
                        lazyUpdate={true}
                    />
                </div>
            </div>
        </div>
    );
};

export default BuyingReports;
