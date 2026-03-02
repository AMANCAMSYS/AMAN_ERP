import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { hasPermission } from '../../utils/auth';
import BackButton from '../../components/common/BackButton';

const ReportCenter = () => {
    const { t, i18n } = useTranslation();
    const navigate = useNavigate();

    const reportGroups = [
        {
            title: t('reports_center.groups.sales'),
            icon: '📊',
            color: '#10B981',
            permission: 'sales.reports',
            reports: [
                { name: t('reports_center.reports.sales_analytics'), path: '/sales/reports/analytics', desc: t('reports_center.reports.sales_analytics_desc') },
                { name: t('reports_center.reports.customer_statement'), path: '/sales/reports/customer-statement', desc: t('reports_center.reports.customer_statement_desc') },
                { name: t('reports_center.reports.aging_report'), path: '/sales/reports/aging', desc: t('reports_center.reports.aging_report_desc') },
                { name: t('reports.commissions.title', 'Sales Commission Report'), path: '/sales/commissions', desc: t('reports_center.reports.commissions_desc', 'Track salesperson commissions and payouts') }
            ]
        },
        {
            title: t('reports_center.groups.buying'),
            icon: '🛒',
            color: '#3B82F6',
            permission: 'buying.reports',
            reports: [
                { name: t('reports_center.reports.buying_analytics'), path: '/buying/reports/analytics', desc: t('reports_center.reports.buying_analytics_desc') },
                { name: t('reports_center.reports.supplier_statement'), path: '/buying/reports/supplier-statement', desc: t('reports_center.reports.supplier_statement_desc') },
                { name: t('purchases_aging.title'), path: '/buying/reports/aging', desc: t('purchases_aging.subtitle') }
            ]
        },
        {
            title: t('reports_center.groups.stock'),
            icon: '📦',
            color: '#F59E0B',
            permission: 'stock.reports',
            reports: [
                { name: t('reports_center.reports.stock_balance'), path: '/stock/reports', desc: t('reports_center.reports.stock_balance_desc') },
                { name: t('reports_center.reports.stock_movements'), path: '/stock/reports/movements', desc: t('reports_center.reports.stock_movements_desc') }
            ]
        },
        {
            title: t('reports_center.groups.accounting'),
            icon: '📒',
            color: '#8B5CF6',
            permission: 'accounting.view',
            reports: [
                { name: t('reports_center.reports.trial_balance'), path: '/accounting/trial-balance', desc: t('reports_center.reports.trial_balance_desc') },
                { name: t('accounting.home.links.general_ledger'), path: '/accounting/general-ledger', desc: t('accounting.general_ledger.subtitle') },
                { name: t('accounting.home.links.income_statement'), path: '/accounting/income-statement', desc: t('accounting.income_statement.subtitle') },
                { name: t('accounting.home.links.balance_sheet'), path: '/accounting/balance-sheet', desc: t('accounting.balance_sheet.subtitle') },
                { name: t('reports_center.reports.cashflow'), path: '/accounting/cashflow', desc: t('reports_center.reports.cashflow_desc') },
                { name: t('cashflow_ias7.title'), path: '/reports/cashflow-ias7', desc: t('cashflow_ias7.subtitle') },
                { name: t('fx_report.title'), path: '/reports/fx-gain-loss', desc: t('fx_report.subtitle') },
                { name: t('consolidation.title'), path: '/reports/consolidation', desc: t('consolidation.subtitle') },
                { name: t('reports.detailed_pl.title', 'Detailed P&L'), path: '/reports/detailed-pl', desc: t('reports_center.reports.detailed_pl_desc', 'Profit & loss breakdown by customer, product, or category') }
            ]
        },
        {
            title: t('reports_center.groups.treasury'),
            icon: '🏦',
            color: '#06B6D4',
            permission: 'treasury.view',
            reports: [
                { name: t('reports_center.reports.treasury_balances'), path: '/treasury/reports/balances', desc: t('reports_center.reports.treasury_balances_desc') },
                { name: t('reports_center.reports.treasury_cashflow'), path: '/treasury/reports/cashflow', desc: t('reports_center.reports.treasury_cashflow_desc') },
                { name: t('checks_aging.title'), path: '/treasury/reports/checks-aging', desc: t('checks_aging.subtitle') }
            ]
        },
        {
            title: t('reports_center.groups.manufacturing', 'Manufacturing'),
            icon: '🏭',
            color: '#6366f1',
            permission: 'manufacturing.view',
            reports: [
                { name: t('reports_center.reports.production_analytics', 'Production Analytics'), path: '/manufacturing/reports/analytics', desc: t('reports_center.reports.production_analytics_desc', 'Monitor production output and efficiency') },
                { name: t('reports_center.reports.work_order_status', 'Work Order Status'), path: '/manufacturing/reports/work-orders', desc: t('reports_center.reports.work_order_status_desc', 'Track status and progress of work orders') }
            ]
        },
        {
            title: t('reports_center.groups.assets', 'Fixed Assets'),
            icon: '🏗️',
            color: '#D97706',
            permission: 'assets.view',
            reports: [
                { name: t('asset_reports.title'), path: '/assets/reports', desc: t('asset_reports.subtitle') }
            ]
        },
        {
            title: t('reports_center.groups.projects', 'Projects'),
            icon: '🏗️',
            color: '#8b5cf6',
            permission: 'projects.view',
            reports: [
                { name: t('reports_center.reports.project_financials', 'Project Financials'), path: '/projects/reports/financials', desc: t('reports_center.reports.project_financials_desc', 'Profitability and cost analysis per project') },
                { name: t('reports_center.reports.resource_utilization', 'Resource Utilization'), path: '/projects/reports/resources', desc: t('reports_center.reports.resource_utilization_desc', 'Track employee allocation and workload') }
            ]
        },
        {
            title: t('reports_center.groups.hr'),
            icon: '👥',
            color: '#EC4899',
            permission: 'hr.view',
            reports: [
                { name: t('reports_center.reports.payroll_trend'), path: '/hr/reports', desc: t('reports_center.reports.payroll_trend_desc') },
                { name: t('reports_center.reports.leave_usage'), path: '/hr/reports', desc: t('reports_center.reports.leave_usage_desc') }
            ]
        },
        {
            title: t('reports_center.groups.taxes'),
            icon: '🧾',
            color: '#F97316',
            permission: 'accounting.view',
            reports: [
                { name: t('reports_center.reports.vat_report'), path: '/taxes', desc: t('reports_center.reports.vat_report_desc') },
                { name: t('reports_center.reports.tax_audit'), path: '/taxes', desc: t('reports_center.reports.tax_audit_desc') }
            ]
        },
        {
            title: t('reports_center.groups.custom', 'Custom Reports'),
            icon: '✨',
            color: '#DB2777',
            permission: 'reports.create',
            reports: [
                { name: t('reports_center.reports.builder', 'Report Builder'), path: '/reports/builder', desc: t('reports_center.reports.builder_desc', 'Create and save custom reports') },
                { name: t('reports.scheduled.title', 'Scheduled Reports'), path: '/reports/scheduled', desc: t('reports_center.reports.scheduled_desc', 'Automate report delivery via email') },
                { name: t('reports.sharing.shared_with_me', 'Shared With Me'), path: '/reports/shared', desc: t('reports_center.reports.shared_desc', 'Reports that colleagues have shared with you') }
            ]
        }
    ].filter(g => hasPermission(g.permission || 'reports.view'));

    const totalReports = reportGroups.reduce((sum, g) => sum + g.reports.length, 0);

    return (
        <div className="workspace fade-in">
            {/* Header Section */}
            <div className="workspace-header">
                <BackButton />
                <div className="header-title">
                    <h1 className="workspace-title">📈 {t('reports_center.title')}</h1>
                    <p className="workspace-subtitle">{t('reports_center.subtitle')}</p>
                </div>
            </div>

            {/* Summary Stats */}
            <div className="metrics-grid" style={{ marginBottom: '24px' }}>
                <div className="metric-card">
                    <div className="metric-label">{t('reports_center.metrics.total_reports')}</div>
                    <div className="metric-value text-primary">{totalReports}</div>
                    <div className="metric-change">{t('reports_center.metrics.reports_available')}</div>
                </div>
                <div className="metric-card">
                    <div className="metric-label">{t('reports_center.metrics.main_sections')}</div>
                    <div className="metric-value text-secondary">{reportGroups.length}</div>
                    <div className="metric-change">{t('reports_center.metrics.sections_list')}</div>
                </div>
                <div className="metric-card">
                    <div className="metric-label">{t('reports_center.metrics.system_status')}</div>
                    <div className="metric-value text-success">{t('reports_center.metrics.active')}</div>
                    <div className="metric-change">{t('reports_center.metrics.availability')}</div>
                </div>
            </div>

            {/* Reports Grid */}
            <div className="modules-grid">
                {reportGroups.map((group, idx) => (
                    <div key={idx} className="section-card" style={{ borderTop: `4px solid ${group.color}` }}>
                        <h3 className="section-title" style={{ color: group.color, borderBottom: 'none', paddingBottom: '8px' }}>
                            {group.icon} {group.title}
                        </h3>
                        <div className="links-list">
                            {group.reports.map((report, rIdx) => (
                                <div
                                    key={rIdx}
                                    className="link-item"
                                    onClick={() => navigate(report.path)}
                                    style={{
                                        padding: '14px 12px',
                                        marginBottom: '8px',
                                        background: 'var(--bg-secondary)',
                                        borderRadius: 'var(--radius)',
                                        border: '1px solid var(--border-color)'
                                    }}
                                >
                                    <div style={{ flex: 1 }}>
                                        <div style={{ fontWeight: '600', marginBottom: '4px', color: 'var(--text-primary)' }}>
                                            {report.name}
                                        </div>
                                        <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                                            {report.desc}
                                        </div>
                                    </div>
                                    <span className="link-arrow" style={{ fontSize: '18px' }}>
                                        {i18n.language === 'ar' ? '←' : '→'}
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>
                ))}
            </div>

            {/* Quick Actions */}
            <div className="section-card" style={{ marginTop: '24px', textAlign: 'center' }}>
                <h3 className="section-title" style={{ textAlign: 'center', borderBottom: 'none' }}>
                    🚀 {t('reports_center.quick_access.title')}
                </h3>
                <div style={{ display: 'flex', gap: '12px', justifyContent: 'center', flexWrap: 'wrap' }}>
                    <button className="btn btn-primary" onClick={() => navigate('/sales/reports/analytics')}>
                        📊 {t('reports_center.reports.sales_analytics')}
                    </button>
                    <button className="btn btn-secondary" onClick={() => navigate('/buying/reports/analytics')}>
                        📈 {t('reports_center.reports.buying_analytics')}
                    </button>
                    <button className="btn btn-secondary" onClick={() => navigate('/sales/reports/aging')}>
                        ⏳ {t('reports_center.reports.aging_report')}
                    </button>
                    <button className="btn btn-secondary" onClick={() => navigate('/treasury/reports/balances')}>
                        🏦 {t('reports_center.reports.treasury_balances')}
                    </button>
                    <button className="btn btn-secondary" onClick={() => navigate('/accounting/cashflow')}>
                        💸 {t('reports_center.reports.cashflow')}
                    </button>
                    <button className="btn btn-secondary" onClick={() => navigate('/reports/scheduled')}>
                        ⏰ {t('reports.scheduled.title', 'Scheduled Reports')}
                    </button>
                    <button className="btn btn-secondary" onClick={() => navigate('/reports/detailed-pl')}>
                        📊 {t('reports.detailed_pl.title', 'Detailed P&L')}
                    </button>
                    <button className="btn btn-secondary" onClick={() => navigate('/sales/commissions')}>
                        💰 {t('reports.commissions.title', 'Commissions')}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default ReportCenter;