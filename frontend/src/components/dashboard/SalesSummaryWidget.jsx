import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import api from '../../utils/api';
import { formatNumber } from '../../utils/format';
import { TrendingUp, TrendingDown, DollarSign, ShoppingCart, CreditCard, Wallet } from 'lucide-react';

const SalesSummaryWidget = ({ config = {}, currency = '' }) => {
    const { t } = useTranslation();
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const period = config.period || 'month';

    useEffect(() => {
        api.get('/dashboard/widgets/sales-summary', { params: { period } })
            .then(res => setData(res.data))
            .catch(() => {})
            .finally(() => setLoading(false));
    }, [period]);

    const periodLabels = {
        today: t('dashboard.today') || 'اليوم',
        week: t('dashboard.this_week') || 'هذا الأسبوع',
        month: t('dashboard.this_month') || 'هذا الشهر',
        quarter: t('dashboard.this_quarter') || 'هذا الربع',
        year: t('dashboard.this_year') || 'هذه السنة',
    };

    if (loading) return <div className="animate-pulse h-20 bg-slate-100 rounded-lg" />;

    const isPositive = (data?.change_percent || 0) >= 0;

    return (
        <div className="h-full flex flex-col justify-between">
            <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-medium uppercase tracking-wider" style={{ color: 'var(--text-secondary)' }}>
                    {periodLabels[period] || period}
                </span>
                <ShoppingCart size={16} style={{ color: 'var(--primary)' }} />
            </div>
            <div className="text-2xl font-bold" style={{ color: 'var(--text-main)' }}>
                {formatNumber(data?.total || 0)} <small className="text-sm" style={{ color: 'var(--text-secondary)' }}>{currency}</small>
            </div>
            <div className="flex items-center gap-1 mt-2">
                <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>{data?.count || 0} {t('dashboard.invoices') || 'فاتورة'}</span>
                <span className="mx-1" style={{ color: 'var(--text-muted)' }}>•</span>
                <span className={`text-xs font-semibold flex items-center gap-0.5 ${isPositive ? 'text-emerald-600' : 'text-red-500'}`}>
                    {isPositive ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
                    {data?.change_percent > 0 ? '+' : ''}{data?.change_percent || 0}%
                </span>
            </div>
        </div>
    );
};

export default SalesSummaryWidget;
