import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import api from '../utils/api';
import StatsCards from '../components/dashboard/StatsCards';
import FinancialChart from '../components/dashboard/FinancialChart';
import TopProductsChart from '../components/dashboard/TopProductsChart';
import SalesSummaryWidget from '../components/dashboard/SalesSummaryWidget';
import LowStockWidget from '../components/dashboard/LowStockWidget';
import PendingTasksWidget from '../components/dashboard/PendingTasksWidget';
import CashFlowWidget from '../components/dashboard/CashFlowWidget';
import {
    RefreshCw, Calendar, Wallet, TrendingUp, Package, Users,
    Building2, FileText, ShieldCheck,
} from 'lucide-react';
import { useBranch } from '../context/BranchContext';
import { getUser } from '../utils/auth';
import { formatShortDate } from '../utils/dateUtils';


/* ── Card wrapper ────────────────────────────────────── */
const Card = ({ title, children, style = {} }) => (
    <div style={{
        background: '#fff', borderRadius: '1rem', border: '1px solid #e2e8f0',
        boxShadow: '0 1px 3px rgba(0,0,0,.06)', overflow: 'hidden',
        display: 'flex', flexDirection: 'column', ...style
    }}>
        {title && (
            <div style={{ padding: '0.85rem 1.1rem 0.6rem', borderBottom: '1px solid #f1f5f9' }}>
                <span style={{ fontSize: '0.82rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    {title}
                </span>
            </div>
        )}
        <div style={{ flex: 1, padding: '1rem', overflow: 'auto' }}>{children}</div>
    </div>
);

/* ── Dashboard ───────────────────────────────────────── */
const Dashboard = () => {
    const { t, i18n } = useTranslation();
    const { currentBranch } = useBranch();
    const user = getUser();
    const isRTL = i18n.dir() === 'rtl';
    const currency = user?.currency || '';

    const [stats, setStats]      = useState(null);
    const [finData, setFin]      = useState([]);
    const [prodData, setProds]   = useState([]);
    const [loading, setLoading]  = useState(true);

    const fetchAll = useCallback(async () => {
        if (user?.role === 'system_admin') {
            try { const r = await api.get('/dashboard/system-stats'); setStats(r.data); }
            catch (_) {}
            finally { setLoading(false); }
            return;
        }
        setLoading(true);
        try {
            const p = currentBranch ? { branch_id: currentBranch.id } : {};
            const [sR, fR, pR] = await Promise.all([
                api.get('/dashboard/stats', { params: p }),
                api.get('/dashboard/charts/financial', { params: p }),
                api.get('/dashboard/charts/products', { params: p }),
            ]);
            setStats(sR.data);
            setFin(fR.data);
            setProds(pR.data);
        } catch (_) {}
        finally { setLoading(false); }
    }, [currentBranch, user?.role]);

    useEffect(() => { fetchAll(); }, [fetchAll]);

    const greeting = () => {
        const h = new Date().getHours();
        if (h < 12) return t('common.good_morning') || (isRTL ? 'صباح الخير' : 'Good morning');
        if (h < 18) return t('common.good_afternoon') || (isRTL ? 'مساء الخير' : 'Good afternoon');
        return t('common.good_evening') || (isRTL ? 'مساء النور' : 'Good evening');
    };

    /* ── System-Admin ───────────────────────────────── */
    if (user?.role === 'system_admin') {
        return (
            <div className="workspace fade-in">
                <div className="workspace-header">
                    <h1 className="workspace-title">{t('dashboard.system_admin_title')}</h1>
                    <p className="workspace-subtitle">{t('dashboard.system_admin_welcome')}</p>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px,1fr))', gap: '1rem', marginBottom: '2rem' }}>
                    {[
                        { label: t('dashboard.apps.companies'), val: stats?.total_companies },
                        { label: t('dashboard.total_users'),     val: stats?.total_users },
                        { label: t('dashboard.active_users'),    val: stats?.active_users },
                        { label: t('dashboard.system_status'),   val: stats?.system_status, green: stats?.system_status === 'Healthy' },
                    ].map(m => (
                        <Card key={m.label}>
                            <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginBottom: '0.3rem' }}>{m.label}</div>
                            <div style={{ fontSize: '1.6rem', fontWeight: 700, color: m.green ? '#16a34a' : '#1e293b' }}>
                                {loading ? <span style={{ display: 'inline-block', width: 60, height: 28, borderRadius: 6, background: '#f1f5f9' }} /> : (m.val ?? '—')}
                            </div>
                        </Card>
                    ))}
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px,1fr))', gap: '1.5rem' }}>
                    <AdminCard icon={<Building2 size={36} strokeWidth={1.5}/>} title={t('dashboard.apps.companies')} desc={t('dashboard.apps.companies_desc')} link="/admin/companies" />
                    <AdminCard icon={<FileText   size={36} strokeWidth={1.5}/>} title={t('audit.title')}             desc={t('audit.subtitle')}             link="/admin/audit-logs" />
                    <AdminCard icon={<ShieldCheck size={36} strokeWidth={1.5}/>}title={t('nav.roles')}              desc={t('dashboard.apps.security_desc')}link="/admin/roles" />
                </div>
            </div>
        );
    }

    /* ── Company user ───────────────────────────────── */
    const gap = '1rem';

    return (
        <div className="workspace fade-in">

            {/* Header */}
            <div className="workspace-header" style={{ marginBottom: '1.5rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem' }}>
                    <div>
                        <h1 className="workspace-title" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            {t('nav.dashboard') || (isRTL ? 'لوحة التحكم' : 'Dashboard')}
                            {currentBranch && (
                                <span style={{ fontSize: '0.78rem', fontWeight: 400, color: '#64748b', background: '#f1f5f9', border: '1px solid #e2e8f0', borderRadius: '0.4rem', padding: '2px 8px' }}>
                                    {currentBranch.branch_name}
                                </span>
                            )}
                        </h1>
                        <p className="workspace-subtitle">{greeting()}, {user?.full_name || user?.username}.</p>
                    </div>
                    <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', alignItems: 'center' }}>
                        <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', padding: '6px 12px', background: '#fff', border: '1px solid #e2e8f0', borderRadius: '0.6rem', fontSize: '0.8rem', color: '#64748b' }}>
                            <Calendar size={14} />
                            {formatShortDate(new Date())}
                        </span>
                        <button onClick={fetchAll} disabled={loading}
                            style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', padding: '6px 14px', background: '#fff', border: '1px solid #e2e8f0', borderRadius: '0.6rem', fontSize: '0.8rem', cursor: 'pointer', color: '#475569' }}>
                            <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
                            {t('common.refresh') || (isRTL ? 'تحديث' : 'Refresh')}
                        </button>
                    </div>
                </div>
            </div>

            {/* Row 1 — Key metrics */}
            <div style={{ marginBottom: gap }}>
                <StatsCards stats={stats} loading={loading} currency={currency} />
            </div>

            {/* Row 2 — Sales summary × 3 */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap, marginBottom: gap }}>
                <Card title={t('dashboard.today') || (isRTL ? 'اليوم' : 'Today')} style={{ minHeight: 120 }}>
                    <SalesSummaryWidget config={{ period: 'today' }} currency={currency} />
                </Card>
                <Card title={t('dashboard.this_week') || (isRTL ? 'هذا الأسبوع' : 'This Week')} style={{ minHeight: 120 }}>
                    <SalesSummaryWidget config={{ period: 'week' }} currency={currency} />
                </Card>
                <Card title={t('dashboard.this_month') || (isRTL ? 'هذا الشهر' : 'This Month')} style={{ minHeight: 120 }}>
                    <SalesSummaryWidget config={{ period: 'month' }} currency={currency} />
                </Card>
            </div>

            {/* Row 3 — Financial chart + Quick actions */}
            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap, marginBottom: gap }}>
                <Card title={t('dashboard.financial_overview') || (isRTL ? 'المبيعات والمصروفات' : 'Revenue & Expenses')} style={{ minHeight: 320 }}>
                    <FinancialChart data={finData} loading={loading} currency={currency} />
                </Card>
                <Card title={isRTL ? 'الإجراءات السريعة' : 'Quick Actions'} style={{ minHeight: 320 }}>
                    <QuickActions t={t} isRTL={isRTL} />
                </Card>
            </div>

            {/* Row 4 — Top products + Low stock */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap, marginBottom: gap }}>
                <Card title={t('dashboard.top_products') || (isRTL ? 'أفضل المنتجات' : 'Top Products')} style={{ minHeight: 280 }}>
                    <TopProductsChart data={prodData} loading={loading} currency={currency} />
                </Card>
                <Card title={t('dashboard.low_stock') || (isRTL ? 'المخزون المنخفض' : 'Low Stock')} style={{ minHeight: 280 }}>
                    <LowStockWidget config={{ limit: 8 }} currency={currency} />
                </Card>
            </div>

            {/* Row 5 — Cash flow */}
            <div style={{ marginBottom: gap }}>
                <Card title={isRTL ? 'التدفق النقدي (آخر 30 يوم)' : 'Cash Flow (Last 30 days)'} style={{ minHeight: 280 }}>
                    <CashFlowWidget config={{ days: 30 }} currency={currency} />
                </Card>
            </div>

            {/* Row 6 — Pending tasks */}
            <div style={{ marginBottom: gap }}>
                <Card title={isRTL ? 'المهام المعلقة' : 'Pending Tasks'}>
                    <PendingTasksWidget config={{ limit: 10 }} currency={currency} />
                </Card>
            </div>

        </div>
    );
};

/* ── AdminCard ───────────────────────────────────────── */
const AdminCard = ({ icon, title, desc, link }) => (
    <button onClick={() => window.location.href = link}
        style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: 230, width: '100%', background: '#fff', border: '1px solid #e2e8f0', borderRadius: '1.5rem', padding: '1.5rem', cursor: 'pointer', boxShadow: '0 1px 3px rgba(0,0,0,.06)', transition: 'all .2s' }}
        onMouseEnter={e => { e.currentTarget.style.boxShadow='0 6px 20px rgba(59,130,246,.15)'; e.currentTarget.style.borderColor='#93c5fd'; }}
        onMouseLeave={e => { e.currentTarget.style.boxShadow='0 1px 3px rgba(0,0,0,.06)';     e.currentTarget.style.borderColor='#e2e8f0'; }}>
        <div style={{ marginBottom: '0.9rem', color: '#3b82f6' }}>{icon}</div>
        <div style={{ fontWeight: 700, fontSize: '1rem', color: '#1e293b', marginBottom: '0.35rem' }}>{title}</div>
        <div style={{ fontSize: '0.78rem', color: '#94a3b8', textAlign: 'center', lineHeight: 1.5 }}>{desc}</div>
    </button>
);

/* ── QuickActions ────────────────────────────────────── */
const ACTIONS = [
    { icon: <TrendingUp size={20}/>, key: 'nav.sales',       fallbackAR: 'مبيعات',       link: '/sales/invoices/new',            bg: '#dbeafe', fg: '#2563eb' },
    { icon: <Package    size={20}/>, key: 'nav.inventory',   fallbackAR: 'مخزون',        link: '/stock/products/new',            bg: '#dcfce7', fg: '#16a34a' },
    { icon: <Wallet     size={20}/>, key: 'nav.accounting',  fallbackAR: 'محاسبة',       link: '/accounting/journal-entries/new',bg: '#fef9c3', fg: '#ca8a04' },
    { icon: <Users      size={20}/>, key: 'nav.hr',          fallbackAR: 'موارد بشرية',  link: '/hr/employees',                  bg: '#fae8ff', fg: '#9333ea' },
];

const QuickActions = ({ t, isRTL }) => (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.7rem', height: '100%' }}>
        {ACTIONS.map(a => (
            <button key={a.key} onClick={() => window.location.href = a.link}
                style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '0.4rem', padding: '0.9rem', background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '0.75rem', cursor: 'pointer', fontSize: '0.8rem', fontWeight: 600, color: '#475569', transition: 'all .15s' }}
                onMouseEnter={e => { e.currentTarget.style.background=a.bg; e.currentTarget.style.borderColor=a.fg+'66'; e.currentTarget.style.color=a.fg; }}
                onMouseLeave={e => { e.currentTarget.style.background='#f8fafc'; e.currentTarget.style.borderColor='#e2e8f0'; e.currentTarget.style.color='#475569'; }}>
                <span style={{ padding: '0.45rem', background: a.bg, borderRadius: '0.5rem', color: a.fg, display: 'flex' }}>
                    {a.icon}
                </span>
                {t(a.key) || (isRTL ? a.fallbackAR : a.key.split('.')[1])}
            </button>
        ))}
    </div>
);

export default Dashboard;
