import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { purchasesAPI, accountingAPI } from '../../utils/api'
import { getCurrency, hasPermission } from '../../utils/auth'
import { useTranslation } from 'react-i18next'
import { useBranch } from '../../context/BranchContext'
import { formatNumber } from '../../utils/format'

function AccountingHome() {
    const { t, i18n } = useTranslation()
    const navigate = useNavigate()
    const { currentBranch } = useBranch()
    const [stats, setStats] = useState({ total_income: 0, total_expenses: 0, net_profit: 0, cash_balance: 0 })
    const [loading, setLoading] = useState(true)
    const currency = getCurrency()

    useEffect(() => {
        const fetchStats = async () => {
            if (!hasPermission('reports.view')) {
                setLoading(false);
                return;
            }
            try {
                setLoading(true)
                const response = await accountingAPI.getSummary({ branch_id: currentBranch?.id })
                setStats(response.data)
            } catch (err) {
                console.error("Failed to fetch accounting stats", err)
            } finally {
                setLoading(false)
            }
        }
        fetchStats()
    }, [currentBranch])

    const metrics = [
        { label: t('accounting.home.metrics.total_income'), value: stats.total_income, color: 'success' },
        { label: t('accounting.home.metrics.total_expenses'), value: stats.total_expenses, color: 'danger' },
        { label: t('accounting.home.metrics.net_profit'), value: stats.net_profit, color: 'primary' },
        { label: t('accounting.home.metrics.cash_balance'), value: stats.cash_balance, color: 'warning' }
    ]

    // ... rest of sections ...

    const sections = [
        {
            title: t('accounting.home.sections.masters'),
            items: [
                { label: t('accounting.home.links.coa'), path: '/accounting/coa', icon: '🌳', permission: 'accounting.view' },
                { label: t('accounting.home.links.cost_centers'), path: '/accounting/cost-centers', icon: '🎯', permission: 'accounting.view' },
                { label: t('accounting.home.links.currencies'), path: '/accounting/currencies', icon: '💱', permission: 'accounting.view' }, // Placeholder
                { label: t('accounting.budgets.title'), path: '/accounting/budgets', icon: '📊', permission: 'accounting.budgets.view' },
                { label: i18n.language === 'ar' ? 'الموازنات المتقدمة' : 'Advanced Budgets', path: '/accounting/budgets/advanced', icon: '📈', permission: 'accounting.budgets.view' },
                { label: i18n.language === 'ar' ? 'السنوات المالية' : 'Fiscal Years', path: '/accounting/fiscal-years', icon: '📅', permission: 'accounting.view' },
                { label: i18n.language === 'ar' ? 'القيود المتكررة' : 'Recurring Entries', path: '/accounting/recurring-templates', icon: '🔄', permission: 'accounting.view' },
                { label: i18n.language === 'ar' ? 'الأرصدة الافتتاحية' : 'Opening Balances', path: '/accounting/opening-balances', icon: '📋', permission: 'accounting.manage' },
                { label: i18n.language === 'ar' ? 'قيود الإقفال' : 'Closing Entries', path: '/accounting/closing-entries', icon: '🔒', permission: 'accounting.manage' }
            ]
        },
        {
            title: t('accounting.home.sections.transactions'),
            items: [
                { label: t('accounting.home.links.journal_entry'), path: '/accounting/journal-entries', icon: '📝', permission: 'accounting.edit' },
                { label: t('accounting.home.links.sales_invoices'), path: '/sales/invoices', icon: '💰', permission: 'sales.view' },
                { label: t('accounting.home.links.purchase_invoices'), path: '/buying/invoices', icon: '🛒', permission: 'buying.view' },
                { label: t('accounting.home.links.vouchers'), path: '/accounting/general-ledger', icon: '🎫', permission: 'accounting.view' }
            ]
        },
        {
            title: i18n.language === 'ar' ? 'المحاسبة المتقدمة' : 'Advanced Accounting',
            items: [
                { label: t('accounting.intercompany', 'المعاملات بين الشركات'), path: '/accounting/intercompany', icon: '🏢', permission: 'accounting.view' },
                { label: t('accounting.revenue_recognition', 'الاعتراف بالإيراد'), path: '/accounting/revenue-recognition', icon: '📊', permission: 'accounting.view' },
                { label: t('zakat.title', 'حاسبة الزكاة'), path: '/accounting/zakat', icon: '🕌', permission: 'accounting.view' }
            ]
        },
        {
            title: t('accounting.home.sections.reports'),
            items: [
                { label: i18n.language === 'ar' ? 'مؤشرات الأداء المالي' : 'Financial KPI Dashboard', path: '/accounting/kpi', icon: '📈', permission: 'accounting.view', highlight: true, color: '#2563eb' },
                { label: t('accounting.home.links.general_ledger'), path: '/accounting/general-ledger', icon: '📚', permission: 'accounting.view' },
                { label: t('accounting.home.links.trial_balance'), path: '/accounting/trial-balance', icon: '⚖️', permission: 'accounting.view' },
                { label: t('accounting.home.links.vat_report'), path: '/accounting/vat-report', icon: '🧾', permission: 'accounting.view' },
                { label: t('accounting.home.links.income_statement'), path: '/accounting/income-statement', icon: '📈', permission: 'accounting.view' },
                { label: t('accounting.home.links.balance_sheet'), path: '/accounting/balance-sheet', icon: '🏦', permission: 'accounting.view' },
                { label: t('accounting.home.links.tax_audit'), path: '/accounting/tax-audit', icon: '🔍', permission: 'accounting.view' },
                { label: t('accounting.home.links.cashflow_report'), path: '/accounting/cashflow', icon: '🌊', permission: 'accounting.view' },
                { label: t('accounting.home.links.inventory_valuation'), path: '/stock/valuation-report', icon: '📦', permission: 'reports.view' },
                { label: i18n.language === 'ar' ? 'مقارنة الفترات' : 'Period Comparison', path: '/accounting/period-comparison', icon: '📊', permission: 'accounting.view' },
                { label: t('cashflow_ias7.title', 'التدفق النقدي IAS 7'), path: '/reports/cashflow-ias7', icon: '💧', permission: 'accounting.view' },
                { label: t('fx_report.title', 'أرباح/خسائر العملات'), path: '/reports/fx-gain-loss', icon: '💱', permission: 'accounting.view' },
                { label: t('consolidation.title', 'التقارير الموحدة'), path: '/reports/consolidation', icon: '🏢', permission: 'accounting.view' },
                { label: t('reports.detailed_pl.title', 'الربح والخسارة التفصيلي'), path: '/reports/detailed-pl', icon: '📋', permission: 'accounting.view' }
            ]
        }
    ]

    const filteredSections = sections.map(section => ({
        ...section,
        items: section.items.filter(item => !item.permission || hasPermission(item.permission))
    })).filter(section => section.items.length > 0)

    return (
        <div className="workspace fade-in">
            <div className="workspace-header display-flex justify-between align-center">
                <div>
                    <h1 className="workspace-title">{t('accounting.home.title')}</h1>
                    <p className="workspace-subtitle">{t('accounting.home.subtitle')}</p>
                </div>
            </div>

            {/* Metrics Section */}
            <div className="metrics-grid mb-6">
                {metrics.map((metric, index) => (
                    <div key={index} className="metric-card">
                        <div className="metric-label">{metric.label}</div>
                        <div className="metric-value">
                            {!hasPermission('reports.view') ? '***' : (loading ? '...' : formatNumber(metric.value))} {hasPermission('reports.view') && <small>{currency}</small>}
                        </div>
                    </div>
                ))}
            </div>

            {/* Shortcuts Sections */}
            <div className="modules-grid">
                {filteredSections.map((section, idx) => (
                    <div key={idx} className="card section-card">
                        <h3 className="section-title mb-4">{section.title}</h3>
                        <div className="links-list">
                            {section.items.map((item, itemIdx) => (
                                <div
                                    key={itemIdx}
                                    className="link-item"
                                    onClick={() => item.path !== '#' && navigate(item.path)}
                                    style={item.highlight ? { background: `linear-gradient(135deg, ${item.color}0F, ${item.color}1F)`, borderRight: i18n.language === 'ar' ? `3px solid ${item.color}` : 'none', borderLeft: i18n.language !== 'ar' ? `3px solid ${item.color}` : 'none' } : undefined}
                                >
                                    <span className="link-icon">{item.icon}</span>
                                    <span className="link-label" style={item.highlight ? { fontWeight: 600, color: item.color } : undefined}>{item.label}</span>
                                    <span className="link-arrow">{i18n.language === 'ar' ? '←' : '→'}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    )
}

export default AccountingHome
