import React, { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { accountingAPI, companiesAPI } from '../../utils/api'
import { useBranch } from '../../context/BranchContext'
import { formatNumber } from '../../utils/format'
import BackButton from '../../components/common/BackButton';

function TrialBalance() {
    const { t } = useTranslation()
    const { currentBranch } = useBranch()
    const [accounts, setAccounts] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState('')
    const [currency, setCurrency] = useState('')
    const [totals, setTotals] = useState({ debit: 0, credit: 0, balance: 0 })

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true)
                const userStr = localStorage.getItem('user')
                const user = userStr ? JSON.parse(userStr) : null
                const companyId = user?.company_id || localStorage.getItem('company_id')

                const [accountsRes, companyRes] = await Promise.all([
                    accountingAPI.list({ branch_id: currentBranch?.id }),
                    companyId ? companiesAPI.getCurrentCompany(companyId) : Promise.resolve({ data: { currency: '' } })
                ])

                const accData = accountsRes.data
                setAccounts(accData)

                // Calculate Totals
                let totalDebit = 0
                let totalCredit = 0

                // For Trial Balance, we usually just list balances. 
                // Positive Balance = Debit (Asset/Expense)
                // Negative Balance (if stored that way) or Credit Nature accounts = Credit.
                // However, our system stores 'balance' as a single number.
                // We need to interpret it based on Account Type.

                // Asset/Expense: Positive means Debit Balance.
                // Liability/Equity/Revenue: Positive means Credit Balance.

                let debSum = 0
                let credSum = 0

                accData.forEach(acc => {
                    const bal = parseFloat(acc.balance || 0)
                    if (['asset', 'expense'].includes(acc.account_type)) {
                        // Normal Debit balance
                        if (bal >= 0) debSum += bal
                        else credSum += Math.abs(bal) // Negative asset is credit
                    } else {
                        // Normal Credit balance
                        if (bal >= 0) credSum += bal
                        else debSum += Math.abs(bal) // Negative liab is debit
                    }
                })

                setTotals({
                    debit: debSum,
                    credit: credSum,
                    balance: debSum - credSum
                })

                if (companyRes.data && companyRes.data.currency) {
                    setCurrency(companyRes.data.currency)
                }
            } catch (err) {
                console.error(err)
                setError(t('accounting.trial_balance.error_loading'))
            } finally {
                setLoading(false)
            }
        }
        fetchData()
    }, [currentBranch, t])

    if (loading) return <div className="page-center"><span className="loading"></span></div>

    // Group by high-level type for summary
    const summaryData = [
        { name: t('accounting.coa.types.asset'), value: accounts.filter(a => a.account_type === 'asset').reduce((s, a) => s + parseFloat(a.balance || 0), 0) },
        { name: t('accounting.coa.types.liability'), value: accounts.filter(a => a.account_type === 'liability').reduce((s, a) => s + parseFloat(a.balance || 0), 0) },
        { name: t('accounting.coa.types.equity'), value: accounts.filter(a => a.account_type === 'equity').reduce((s, a) => s + parseFloat(a.balance || 0), 0) },
        { name: t('accounting.coa.types.revenue'), value: accounts.filter(a => a.account_type === 'revenue').reduce((s, a) => s + parseFloat(a.balance || 0), 0) },
        { name: t('accounting.coa.types.expense'), value: accounts.filter(a => a.account_type === 'expense').reduce((s, a) => s + parseFloat(a.balance || 0), 0) },
    ]

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <div>
                    <h1 className="workspace-title">⚖️ {t('accounting.trial_balance.title')}</h1>
                    <p className="workspace-subtitle">{t('accounting.trial_balance.subtitle')}</p>
                </div>
                <div className="action-buttons">
                    <button className="btn btn-secondary" onClick={() => window.print()}>
                        {t('accounting.trial_balance.print')}
                    </button>
                </div>
            </div>

            <div className="metrics-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))' }}>
                <div className="metric-card">
                    <div className="metric-label">{t('accounting.trial_balance.metrics.total_debit')}</div>
                    <div className="metric-value text-primary">{formatNumber(totals.debit)} <small>{currency}</small></div>
                </div>
                <div className="metric-card">
                    <div className="metric-label">{t('accounting.trial_balance.metrics.total_credit')}</div>
                    <div className="metric-value text-secondary">{formatNumber(totals.credit)} <small>{currency}</small></div>
                </div>
                <div className="metric-card">
                    <div className="metric-label">{t('accounting.trial_balance.metrics.difference')}</div>
                    <div className={`metric-value ${Math.abs(totals.balance) < 0.01 ? 'text-success' : 'text-error'}`}>
                        {formatNumber(totals.balance)} <small>{currency}</small>
                    </div>
                    {Math.abs(totals.balance) < 0.01 && <div className="metric-change">{t('accounting.trial_balance.matched')} ✅</div>}
                </div>
            </div>

            <div className="card">
                <table className="data-table">
                    <thead>
                        <tr>
                            <th>{t('accounting.trial_balance.table.account_number')}</th>
                            <th>{t('accounting.trial_balance.table.account_name')}</th>
                            <th style={{ textAlign: 'left' }}>{t('accounting.trial_balance.table.debit')}</th>
                            <th style={{ textAlign: 'left' }}>{t('accounting.trial_balance.table.credit')}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {['asset', 'liability', 'equity', 'revenue', 'expense'].map(type => {
                            const typeAccounts = accounts.filter(a => a.account_type === type)
                            if (typeAccounts.length === 0) return null

                            // Calculate Group Totals
                            let groupDebit = 0
                            let groupCredit = 0
                            typeAccounts.forEach(acc => {
                                const bal = parseFloat(acc.balance || 0)
                                if (['asset', 'expense'].includes(acc.account_type)) {
                                    if (bal >= 0) groupDebit += bal
                                    else groupCredit += Math.abs(bal)
                                } else {
                                    if (bal >= 0) groupCredit += bal
                                    else groupDebit += Math.abs(bal)
                                }
                            })

                            const typeLabels = {
                                asset: t('accounting.coa.types.asset'),
                                liability: t('accounting.coa.types.liability'),
                                equity: t('accounting.coa.types.equity'),
                                revenue: t('accounting.coa.types.revenue'),
                                expense: t('accounting.coa.types.expense')
                            }

                            return (
                                <React.Fragment key={type}>
                                    <tr style={{ background: 'var(--bg-secondary)' }}>
                                        <td colSpan="4" style={{ fontWeight: 'bold', padding: '12px 16px' }}>
                                            {typeLabels[type]}
                                        </td>
                                    </tr>
                                    {typeAccounts.map(acc => {
                                        const bal = parseFloat(acc.balance || 0)
                                        let debit = 0
                                        let credit = 0

                                        if (['asset', 'expense'].includes(acc.account_type)) {
                                            if (bal >= 0) debit = bal
                                            else credit = Math.abs(bal)
                                        } else {
                                            if (bal >= 0) credit = bal
                                            else debit = Math.abs(bal)
                                        }

                                        return (
                                            <tr key={acc.id} className="hover-row">
                                                <td className="font-mono" style={{ paddingLeft: '24px' }}>{acc.account_number}</td>
                                                <td className="font-medium">
                                                    {acc.parent_id ? <span style={{ marginRight: '8px', color: 'var(--text-secondary)' }}>↳</span> : ''}
                                                    {acc.name}
                                                </td>
                                                <td style={{ textAlign: 'left', color: debit > 0 ? 'var(--text-primary)' : 'var(--text-light)' }}>
                                                    {debit > 0 ? formatNumber(debit) : '-'}
                                                </td>
                                                <td style={{ textAlign: 'left', color: credit > 0 ? 'var(--text-primary)' : 'var(--text-light)' }}>
                                                    {credit > 0 ? formatNumber(credit) : '-'}
                                                </td>
                                            </tr>
                                        )
                                    })}
                                    <tr style={{ borderTop: '2px solid var(--border-color)', background: '#F8FAFC' }}>
                                        <td colSpan="2" style={{ textAlign: 'left', fontWeight: 'bold', paddingLeft: '24px' }}>
                                            {t('accounting.trial_balance.total_for')} {typeLabels[type]}
                                        </td>
                                        <td style={{ textAlign: 'left', fontWeight: 'bold' }}>{formatNumber(groupDebit)}</td>
                                        <td style={{ textAlign: 'left', fontWeight: 'bold' }}>{formatNumber(groupCredit)}</td>
                                    </tr>
                                </React.Fragment>
                            )
                        })}
                        <tr style={{ background: 'var(--primary)', color: 'white', fontWeight: 'bold', fontSize: '1.1em' }}>
                            <td colSpan="2" style={{ textAlign: 'center' }}>{t('accounting.trial_balance.total_grand')}</td>
                            <td style={{ textAlign: 'left' }}>{formatNumber(totals.debit)} {currency}</td>
                            <td style={{ textAlign: 'left' }}>{formatNumber(totals.credit)} {currency}</td>
                        </tr>
                    </tbody>
                </table>
            </div>

        </div>
    )
}

export default TrialBalance
