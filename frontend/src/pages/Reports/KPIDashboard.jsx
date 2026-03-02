import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { reportsAPI } from '../../utils/api';
import { useToast } from '../../context/ToastContext';
import { BarChart3, TrendingUp, TrendingDown, DollarSign, Package, Users, Wallet, ArrowUpRight, ArrowDownRight, RefreshCw } from 'lucide-react';
import BackButton from '../../components/common/BackButton';
import '../../components/ModuleStyles.css';

const KPIDashboard = () => {
    const { t, i18n } = useTranslation();
    const isRTL = i18n.language === 'ar';
    const { showToast } = useToast();
    const [kpiData, setKpiData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [lastRefresh, setLastRefresh] = useState(null);

    useEffect(() => { fetchKPIs(); }, []);

    const fetchKPIs = async () => {
        try {
            setLoading(true);
            const res = await reportsAPI.getKPIDashboard();
            setKpiData(res.data);
            setLastRefresh(new Date());
        } catch (err) {
            showToast(err.response?.data?.detail || (isRTL ? 'خطأ في تحميل المؤشرات' : 'Error loading KPIs'), 'error');
            console.error(err);
        } finally { setLoading(false); }
    };

    const formatCurrency = (val) => {
        if (!val && val !== 0) return '—';
        return new Intl.NumberFormat(isRTL ? 'ar-SA' : 'en-SA', {
            style: 'currency', currency: 'SAR', maximumFractionDigits: 0
        }).format(val);
    };

    const formatNumber = (val) => {
        if (!val && val !== 0) return '—';
        return new Intl.NumberFormat(isRTL ? 'ar-SA' : 'en-SA').format(val);
    };

    const changeIndicator = (val) => {
        if (!val || val === 0) return null;
        const isPositive = val > 0;
        return (
            <span className="d-flex align-items-center gap-1" style={{ fontSize: '0.8rem', color: isPositive ? '#2e7d32' : '#c62828' }}>
                {isPositive ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
                {Math.abs(val).toFixed(1)}%
            </span>
        );
    };

    const kpiCards = kpiData ? [
        {
            label: isRTL ? 'الإيرادات' : 'Revenue',
            value: formatCurrency(kpiData.revenue),
            change: kpiData.revenue_change,
            icon: <DollarSign size={24} />,
            iconBg: '#e8f5e9', iconColor: '#2e7d32',
            accounting: isRTL ? 'إجمالي الإيرادات المسجلة (دائن 4xxx)' : 'Total recognized revenue (Cr. 4xxx)'
        },
        {
            label: isRTL ? 'المصروفات' : 'Expenses',
            value: formatCurrency(kpiData.expenses),
            change: kpiData.expenses_change,
            icon: <TrendingDown size={24} />,
            iconBg: '#fce4ec', iconColor: '#c62828',
            accounting: isRTL ? 'إجمالي المصروفات (مدين 5xxx-6xxx)' : 'Total expenses (Dr. 5xxx-6xxx)',
            invertColor: true
        },
        {
            label: isRTL ? 'ذمم مدينة' : 'Accounts Receivable',
            value: formatCurrency(kpiData.accounts_receivable),
            change: kpiData.ar_change,
            icon: <TrendingUp size={24} />,
            iconBg: '#e3f2fd', iconColor: '#1565c0',
            accounting: isRTL ? 'رصيد الذمم المدينة (مدين 1200)' : 'AR balance (Dr. 1200)'
        },
        {
            label: isRTL ? 'ذمم دائنة' : 'Accounts Payable',
            value: formatCurrency(kpiData.accounts_payable),
            change: kpiData.ap_change,
            icon: <Wallet size={24} />,
            iconBg: '#fff3e0', iconColor: '#e65100',
            accounting: isRTL ? 'رصيد الذمم الدائنة (دائن 2100)' : 'AP balance (Cr. 2100)'
        },
        {
            label: isRTL ? 'الرصيد النقدي' : 'Cash Balance',
            value: formatCurrency(kpiData.cash_balance),
            change: kpiData.cash_change,
            icon: <DollarSign size={24} />,
            iconBg: '#f3e5f5', iconColor: '#7b1fa2',
            accounting: isRTL ? 'النقد والأرصدة البنكية (1000-1100)' : 'Cash & bank balances (1000-1100)'
        },
        {
            label: isRTL ? 'قيمة المخزون' : 'Inventory Value',
            value: formatCurrency(kpiData.inventory_value),
            change: kpiData.inventory_change,
            icon: <Package size={24} />,
            iconBg: '#e0f2f1', iconColor: '#00695c',
            accounting: isRTL ? 'مخزون آخر المدة (مدين 1400)' : 'Ending inventory (Dr. 1400)'
        },
        {
            label: isRTL ? 'عدد الموظفين' : 'Employee Count',
            value: formatNumber(kpiData.employee_count),
            change: kpiData.employee_change,
            icon: <Users size={24} />,
            iconBg: '#fce4ec', iconColor: '#ad1457',
            accounting: isRTL ? 'عدد الموظفين النشطين' : 'Active headcount'
        }
    ] : [];

    // Calculate key financial ratios
    const ratios = kpiData ? {
        netIncome: (kpiData.revenue || 0) - (kpiData.expenses || 0),
        profitMargin: kpiData.revenue ? (((kpiData.revenue - kpiData.expenses) / kpiData.revenue) * 100) : 0,
        currentRatio: kpiData.accounts_payable ? (((kpiData.cash_balance || 0) + (kpiData.accounts_receivable || 0) + (kpiData.inventory_value || 0)) / kpiData.accounts_payable) : 0,
        cashRatio: kpiData.accounts_payable ? ((kpiData.cash_balance || 0) / kpiData.accounts_payable) : 0,
        arTurnover: kpiData.accounts_receivable ? ((kpiData.revenue || 0) / kpiData.accounts_receivable) : 0,
    } : null;

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <div className="d-flex align-items-center justify-content-between w-100">
                    <div>
                        <h1 className="workspace-title">
                            <BarChart3 size={24} className="me-2" />
                            {isRTL ? 'لوحة مؤشرات الأداء الرئيسية' : 'Key Performance Indicators'}
                        </h1>
                        <p className="workspace-subtitle">
                            {isRTL ? 'مؤشرات مالية وتشغيلية حية مع النسب المحاسبية' : 'Live financial & operational KPIs with accounting ratios'}
                            {lastRefresh && <span className="ms-2 text-muted" style={{ fontSize: '0.8rem' }}>
                                ({isRTL ? 'آخر تحديث: ' : 'Last: '}{lastRefresh.toLocaleTimeString()})
                            </span>}
                        </p>
                    </div>
                    <button className="btn btn-outline-primary" onClick={fetchKPIs} disabled={loading}>
                        <RefreshCw size={16} className={loading ? 'spin' : ''} /> <span className="ms-1">{isRTL ? 'تحديث' : 'Refresh'}</span>
                    </button>
                </div>
            </div>

            {loading && !kpiData ? (
                <div className="text-center p-5"><div className="spinner-border" /></div>
            ) : (
                <>
                    {/* KPI Cards */}
                    <div className="metrics-grid mb-4" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))' }}>
                        {kpiCards.map((kpi, idx) => (
                            <div key={idx} className="metric-card" style={{ position: 'relative' }}>
                                <div className="metric-icon" style={{ background: kpi.iconBg, color: kpi.iconColor }}>
                                    {kpi.icon}
                                </div>
                                <div className="metric-info">
                                    <div className="d-flex align-items-center gap-2">
                                        <span className="metric-value">{kpi.value}</span>
                                        {changeIndicator(kpi.change)}
                                    </div>
                                    <span className="metric-label">{kpi.label}</span>
                                    <small className="text-muted" style={{ fontSize: '0.7rem' }}>{kpi.accounting}</small>
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* Financial Ratios */}
                    {ratios && (
                        <div className="section-card mb-4">
                            <h4 className="mb-3">{isRTL ? 'النسب المالية الرئيسية' : 'Key Financial Ratios'}</h4>
                            <div className="row g-3">
                                <div className="col-md-3">
                                    <div className="p-3 rounded" style={{ background: ratios.netIncome >= 0 ? '#e8f5e9' : '#fce4ec', textAlign: 'center' }}>
                                        <div style={{ fontSize: '1.4rem', fontWeight: 700, color: ratios.netIncome >= 0 ? '#2e7d32' : '#c62828' }}>
                                            {formatCurrency(ratios.netIncome)}
                                        </div>
                                        <div style={{ fontWeight: 600 }}>{isRTL ? 'صافي الدخل' : 'Net Income'}</div>
                                        <small className="text-muted">{isRTL ? 'الإيرادات - المصروفات' : 'Revenue - Expenses'}</small>
                                    </div>
                                </div>
                                <div className="col-md-3">
                                    <div className="p-3 rounded" style={{ background: '#f3f4f6', textAlign: 'center' }}>
                                        <div style={{ fontSize: '1.4rem', fontWeight: 700, color: ratios.profitMargin >= 0 ? '#2e7d32' : '#c62828' }}>
                                            {ratios.profitMargin.toFixed(1)}%
                                        </div>
                                        <div style={{ fontWeight: 600 }}>{isRTL ? 'هامش الربح' : 'Profit Margin'}</div>
                                        <small className="text-muted">{isRTL ? 'صافي الدخل / الإيرادات' : 'Net Income / Revenue'}</small>
                                    </div>
                                </div>
                                <div className="col-md-3">
                                    <div className="p-3 rounded" style={{ background: ratios.currentRatio >= 1 ? '#e8f5e9' : '#fff3e0', textAlign: 'center' }}>
                                        <div style={{ fontSize: '1.4rem', fontWeight: 700 }}>
                                            {ratios.currentRatio.toFixed(2)}x
                                        </div>
                                        <div style={{ fontWeight: 600 }}>{isRTL ? 'نسبة التداول' : 'Current Ratio'}</div>
                                        <small className="text-muted">{isRTL ? 'الأصول المتداولة / الخصوم المتداولة' : 'Current Assets / Current Liabilities'}</small>
                                    </div>
                                </div>
                                <div className="col-md-3">
                                    <div className="p-3 rounded" style={{ background: '#f3f4f6', textAlign: 'center' }}>
                                        <div style={{ fontSize: '1.4rem', fontWeight: 700 }}>
                                            {ratios.arTurnover.toFixed(1)}x
                                        </div>
                                        <div style={{ fontWeight: 600 }}>{isRTL ? 'دوران الذمم' : 'AR Turnover'}</div>
                                        <small className="text-muted">{isRTL ? 'المبيعات / متوسط الذمم' : 'Sales / Avg. AR'}</small>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Accounting Reference */}
                    <div className="section-card" style={{ background: '#f0f7ff', border: '1px dashed #90caf9' }}>
                        <h5 style={{ color: '#1565c0' }}>{isRTL ? 'المرجعية المحاسبية' : 'Accounting Reference'}</h5>
                        <div className="row g-3">
                            <div className="col-md-6">
                                <table className="data-table" style={{ fontSize: '0.85rem' }}>
                                    <thead>
                                        <tr>
                                            <th>{isRTL ? 'المؤشر' : 'KPI'}</th>
                                            <th>{isRTL ? 'المعيار' : 'Standard'}</th>
                                            <th>{isRTL ? 'الحسابات' : 'GL Accounts'}</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr><td>{isRTL ? 'الإيرادات' : 'Revenue'}</td><td>IFRS 15</td><td>4000-4999</td></tr>
                                        <tr><td>{isRTL ? 'المصروفات' : 'Expenses'}</td><td>IAS 1</td><td>5000-6999</td></tr>
                                        <tr><td>{isRTL ? 'ذمم مدينة' : 'AR'}</td><td>IFRS 9</td><td>1200-1299</td></tr>
                                        <tr><td>{isRTL ? 'ذمم دائنة' : 'AP'}</td><td>IAS 37</td><td>2100-2199</td></tr>
                                    </tbody>
                                </table>
                            </div>
                            <div className="col-md-6">
                                <table className="data-table" style={{ fontSize: '0.85rem' }}>
                                    <thead>
                                        <tr>
                                            <th>{isRTL ? 'المؤشر' : 'KPI'}</th>
                                            <th>{isRTL ? 'المعيار' : 'Standard'}</th>
                                            <th>{isRTL ? 'الحسابات' : 'GL Accounts'}</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr><td>{isRTL ? 'النقد' : 'Cash'}</td><td>IAS 7</td><td>1000-1100</td></tr>
                                        <tr><td>{isRTL ? 'المخزون' : 'Inventory'}</td><td>IAS 2</td><td>1400-1499</td></tr>
                                        <tr><td>{isRTL ? 'الأجور' : 'Payroll'}</td><td>IAS 19</td><td>5100-5199</td></tr>
                                        <tr><td>{isRTL ? 'الإيجارات' : 'Leases'}</td><td>IFRS 16</td><td>1600, 2300</td></tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </>
            )}
        </div>
    );
};

export default KPIDashboard;
