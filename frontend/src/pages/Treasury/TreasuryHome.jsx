import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { treasuryAPI } from '../../utils/api'
import { getCurrency, hasPermission } from '../../utils/auth'
import { useBranch } from '../../context/BranchContext'
import { useTranslation } from 'react-i18next'
import '../../components/ModuleStyles.css'
import { formatNumber } from '../../utils/format'

function TreasuryHome() {
    const { t, i18n } = useTranslation()
    const navigate = useNavigate()
    const [stats, setStats] = useState({ account_count: 0, cash_count: 0, bank_count: 0, total_balance: 0 })
    const [loading, setLoading] = useState(true)
    const currency = getCurrency() || ''
    const { currentBranch } = useBranch()

    useEffect(() => {
        const fetchStats = async () => {
            if (!hasPermission('reports.view')) {
                setLoading(false);
                return;
            }
            try {
                setLoading(true)
                const branchId = currentBranch?.id || null
                const response = await treasuryAPI.listAccounts(branchId)

                const accounts = response.data
                const total = accounts.reduce((sum, acc) => sum + Number(acc.current_balance), 0)
                const cash = accounts.filter(a => a.account_type === 'cash').length
                const bank = accounts.filter(a => a.account_type === 'bank').length

                setStats({
                    account_count: accounts.length,
                    cash_count: cash,
                    bank_count: bank,
                    total_balance: total
                })
            } catch (err) {
                console.error("Failed to fetch treasury stats", err)
            } finally {
                setLoading(false)
            }
        }
        fetchStats()
    }, [currentBranch])

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <h1 className="workspace-title">{t('treasury.title')}</h1>
                <p className="workspace-subtitle">{t('treasury.subtitle')}</p>
            </div>

            {/* Metrics Section */}
            <div className="metrics-grid">
                <div className="metric-card">
                    <div className="metric-label">{t('common.total_balance')}</div>
                    <div className="metric-value text-primary">
                        {!hasPermission('reports.view') ? '***' : (loading ? '...' : formatNumber(stats.total_balance))} {hasPermission('reports.view') && <small>{currency}</small>}
                    </div>
                </div>
                <div className="metric-card">
                    <div className="metric-label">{t('treasury.cash_accounts')}</div>
                    <div className="metric-value text-warning">
                        {!hasPermission('reports.view') ? '***' : (loading ? '...' : stats.cash_count)}
                    </div>
                    {hasPermission('reports.view') && (
                        <div className="metric-change">
                            {loading ? '' : t('common.active')}
                        </div>
                    )}
                </div>
                <div className="metric-card">
                    <div className="metric-label">{t('treasury.bank_accounts')}</div>
                    <div className="metric-value text-secondary">
                        {!hasPermission('reports.view') ? '***' : (loading ? '...' : stats.bank_count)}
                    </div>
                    {hasPermission('reports.view') && (
                        <div className="metric-change">
                            {loading ? '' : t('common.active')}
                        </div>
                    )}
                </div>
            </div>

            {/* Module Sections */}
            <div className="modules-grid">
                {/* Masters Section */}
                <div className="card section-card">
                    <h3 className="section-title">{t('treasury.sections.masters')}</h3>
                    <div className="links-list">
                        <div className="link-item" onClick={() => navigate('/treasury/accounts')}>
                            <span className="link-icon">🏦</span>
                            {t('treasury.menu.accounts')}
                            <span className="link-arrow">{i18n.language === 'ar' ? '←' : '→'}</span>
                        </div>
                    </div>
                </div>

                {/* Transactions Section */}
                <div className="card section-card">
                    <h3 className="section-title">{t('treasury.sections.transactions')}</h3>
                    <div className="links-list">
                        <div className="link-item" onClick={() => navigate('/treasury/expense')}>
                            <span className="link-icon">💸</span>
                            {t('treasury.menu.expense')}
                            <span className="link-arrow">{i18n.language === 'ar' ? '←' : '→'}</span>
                        </div>
                        <div className="link-item" onClick={() => navigate('/treasury/transfer')}>
                            <span className="link-icon">🔄</span>
                            {t('treasury.menu.transfer')}
                            <span className="link-arrow">{i18n.language === 'ar' ? '←' : '→'}</span>
                        </div>
                        <div className="link-item" onClick={() => navigate('/treasury/reconciliation')}>
                            <span className="link-icon">📑</span>
                            {t('treasury.menu.reconciliation')}
                            <span className="link-arrow">{i18n.language === 'ar' ? '←' : '→'}</span>
                        </div>
                        <div className="link-item" onClick={() => navigate('/treasury/checks-receivable')}>
                            <span className="link-icon">📥</span>
                            شيكات تحت التحصيل
                            <span className="link-arrow">{i18n.language === 'ar' ? '←' : '→'}</span>
                        </div>
                        <div className="link-item" onClick={() => navigate('/treasury/checks-payable')}>
                            <span className="link-icon">📤</span>
                            شيكات تحت الدفع
                            <span className="link-arrow">{i18n.language === 'ar' ? '←' : '→'}</span>
                        </div>
                        <div className="link-item" onClick={() => navigate('/treasury/notes-receivable')}>
                            <span className="link-icon">📜</span>
                            أوراق القبض
                            <span className="link-arrow">{i18n.language === 'ar' ? '←' : '→'}</span>
                        </div>
                        <div className="link-item" onClick={() => navigate('/treasury/notes-payable')}>
                            <span className="link-icon">📝</span>
                            أوراق الدفع
                            <span className="link-arrow">{i18n.language === 'ar' ? '←' : '→'}</span>
                        </div>
                    </div>
                </div>

                {/* Reports Section */}
                {/* Reports Section */}
                {hasPermission('reports.view') && (
                    <div className="card section-card">
                        <h3 className="section-title">{t('treasury.sections.reports')}</h3>
                        <div className="links-list">
                            <div className="link-item" onClick={() => navigate('/treasury/reports/cashflow')}>
                                <span className="link-icon">📈</span>
                                {t('treasury.menu.cashflow')}
                                <span className="link-arrow">{i18n.language === 'ar' ? '←' : '→'}</span>
                            </div>
                            <div className="link-item" onClick={() => navigate('/treasury/reports/balances')}>
                                <span className="link-icon">⚖️</span>
                                {t('treasury.menu.balances')}
                                <span className="link-arrow">{i18n.language === 'ar' ? '←' : '→'}</span>
                            </div>
                            <div className="link-item" onClick={() => navigate('/treasury/reports/checks-aging')}>
                                <span className="link-icon">⏳</span>
                                {i18n.t('treasury.checks_aging')}
                                <span className="link-arrow">{i18n.language === 'ar' ? '←' : '→'}</span>
                            </div>
                            <div className="link-item" onClick={() => navigate('/finance/cashflow')}>
                                <span className="link-icon">📉</span>
                                {i18n.t('treasury.cash_flow_forecast')}
                                <span className="link-arrow">{i18n.language === 'ar' ? '←' : '→'}</span>
                            </div>
                            <div className="link-item" onClick={() => navigate('/treasury/bank-import')}>
                                <span className="link-icon">🏦</span>
                                {i18n.t('bank_import.title')}
                                <span className="link-arrow">{i18n.language === 'ar' ? '←' : '→'}</span>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}

export default TreasuryHome
