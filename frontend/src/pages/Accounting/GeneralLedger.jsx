import { useState, useEffect } from 'react'
import { reportsAPI, accountingAPI } from '../../utils/api'
import { useBranch } from '../../context/BranchContext'
import { useTranslation } from 'react-i18next'
import { formatNumber } from '../../utils/format'
import { getCurrency } from '../../utils/auth'
import CustomDatePicker from '../../components/common/CustomDatePicker'

function GeneralLedger() {
    const { t, i18n } = useTranslation()
    const { currentBranch } = useBranch()
    const [startDate, setStartDate] = useState(new Date(new Date().getFullYear(), 0, 1))
    const [endDate, setEndDate] = useState(new Date())
    const [accounts, setAccounts] = useState([])
    const [selectedAccount, setSelectedAccount] = useState('')
    const [entries, setEntries] = useState([])
    const [loading, setLoading] = useState(false)
    const [loadingAccounts, setLoadingAccounts] = useState(true)
    const [error, setError] = useState(null)
    const currency = getCurrency()

    // Load accounts list
    useEffect(() => {
        const fetchAccounts = async () => {
            try {
                setLoadingAccounts(true)
                const res = await accountingAPI.list({ branch_id: currentBranch?.id })
                const data = Array.isArray(res.data) ? res.data : (res.data?.data || [])
                setAccounts(data)
            } catch (err) {
                console.error("Failed to load accounts", err)
            } finally {
                setLoadingAccounts(false)
            }
        }
        fetchAccounts()
    }, [currentBranch])

    const fetchLedger = async () => {
        if (!selectedAccount) return
        try {
            setLoading(true)
            setError(null)
            const params = {
                account_id: selectedAccount,
                start_date: startDate.toISOString().split('T')[0],
                end_date: endDate.toISOString().split('T')[0],
                branch_id: currentBranch?.id
            }
            const response = await reportsAPI.getGeneralLedger(params)
            setEntries(response.data.entries || [])
        } catch (err) {
            console.error("Failed to fetch ledger", err)
            setError(t('accounting.general_ledger.error_loading'))
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        if (selectedAccount) {
            fetchLedger()
        }
    }, [selectedAccount, startDate, endDate, currentBranch])

    const selectedAccountData = accounts.find(a => String(a.id) === String(selectedAccount))

    // Calculate running balance
    let runningBalance = 0
    const entriesWithBalance = entries.map(entry => {
        const debit = parseFloat(entry.debit || 0)
        const credit = parseFloat(entry.credit || 0)
        if (selectedAccountData && ['asset', 'expense'].includes(selectedAccountData.account_type)) {
            runningBalance += debit - credit
        } else {
            runningBalance += credit - debit
        }
        return { ...entry, running_balance: runningBalance }
    })

    const totalDebit = entries.reduce((sum, e) => sum + parseFloat(e.debit || 0), 0)
    const totalCredit = entries.reduce((sum, e) => sum + parseFloat(e.credit || 0), 0)

    return (
        <div className="workspace fade-in">
            <div className="workspace-header display-flex justify-between align-center">
                <div>
                    <h1 className="workspace-title">📚 {t('accounting.general_ledger.title')}</h1>
                    <p className="workspace-subtitle">{t('accounting.general_ledger.subtitle')}</p>
                </div>
                <div className="display-flex gap-2">
                    <button className="btn btn-secondary" onClick={() => window.print()}>
                        {t('common.print')}
                    </button>
                </div>
            </div>

            {/* Filters */}
            <div className="card mb-4 mt-4">
                <div className="card-body">
                    <div className="display-flex gap-4 align-center flex-wrap">
                        <div style={{ minWidth: '250px', flex: 1 }}>
                            <label className="form-label">{t('accounting.general_ledger.select_account')}</label>
                            <select
                                className="form-control"
                                value={selectedAccount}
                                onChange={(e) => setSelectedAccount(e.target.value)}
                            >
                                <option value="">{t('accounting.general_ledger.choose_account')}</option>
                                {accounts.map(acc => (
                                    <option key={acc.id} value={acc.id}>
                                        {acc.account_number} - {i18n.language === 'en' && acc.name_en ? acc.name_en : acc.name}
                                    </option>
                                ))}
                            </select>
                        </div>
                        <div style={{ width: '200px' }}>
                            <label className="form-label">{t('common.start_date')}</label>
                            <CustomDatePicker
                                selected={startDate}
                                onChange={date => setStartDate(date)}
                                className="form-control"
                            />
                        </div>
                        <div style={{ width: '200px' }}>
                            <label className="form-label">{t('common.end_date')}</label>
                            <CustomDatePicker
                                selected={endDate}
                                onChange={date => setEndDate(date)}
                                className="form-control"
                            />
                        </div>
                    </div>
                </div>
            </div>

            {!selectedAccount ? (
                <div className="card">
                    <div className="text-center p-5 text-muted">
                        <div style={{ fontSize: '3rem', marginBottom: '16px' }}>📚</div>
                        <p>{t('accounting.general_ledger.select_account_prompt')}</p>
                    </div>
                </div>
            ) : loading ? (
                <div className="text-center p-5">
                    <div className="spinner"></div>
                    <p className="mt-2">{t('common.loading')}</p>
                </div>
            ) : error ? (
                <div className="alert alert-danger">{error}</div>
            ) : (
                <>
                    {/* Account Info & Summary */}
                    {selectedAccountData && (
                        <div className="metrics-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))' }}>
                            <div className="metric-card">
                                <div className="metric-label">{t('accounting.general_ledger.account')}</div>
                                <div className="metric-value" style={{ fontSize: '1rem' }}>
                                    {selectedAccountData.account_number} - {i18n.language === 'en' && selectedAccountData.name_en ? selectedAccountData.name_en : selectedAccountData.name}
                                </div>
                            </div>
                            <div className="metric-card">
                                <div className="metric-label">{t('accounting.general_ledger.total_debit')}</div>
                                <div className="metric-value text-primary">{formatNumber(totalDebit)} <small>{currency}</small></div>
                            </div>
                            <div className="metric-card">
                                <div className="metric-label">{t('accounting.general_ledger.total_credit')}</div>
                                <div className="metric-value text-secondary">{formatNumber(totalCredit)} <small>{currency}</small></div>
                            </div>
                            <div className="metric-card">
                                <div className="metric-label">{t('accounting.general_ledger.net_balance')}</div>
                                <div className={`metric-value ${runningBalance >= 0 ? 'text-success' : 'text-error'}`}>
                                    {formatNumber(Math.abs(runningBalance))} <small>{currency}</small>
                                    <small style={{ fontSize: '0.7em', marginRight: '4px' }}>
                                        {runningBalance >= 0 ? t('accounting.table.debit') : t('accounting.table.credit')}
                                    </small>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Entries Table */}
                    <div className="card">
                        <div className="data-table-container">
                            <table className="data-table">
                                <thead>
                                    <tr>
                                        <th>{t('accounting.general_ledger.date')}</th>
                                        <th>{t('accounting.general_ledger.entry_number')}</th>
                                        <th>{t('accounting.general_ledger.description')}</th>
                                        <th>{t('accounting.general_ledger.reference')}</th>
                                        <th style={{ textAlign: 'left' }}>{t('accounting.table.debit')}</th>
                                        <th style={{ textAlign: 'left' }}>{t('accounting.table.credit')}</th>
                                        <th style={{ textAlign: 'left' }}>{t('accounting.general_ledger.balance')}</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {entriesWithBalance.length === 0 ? (
                                        <tr>
                                            <td colSpan="7" className="text-center p-4 text-muted">
                                                {t('accounting.general_ledger.no_entries')}
                                            </td>
                                        </tr>
                                    ) : (
                                        entriesWithBalance.map((entry, idx) => (
                                            <tr key={idx} className="hover-row">
                                                <td className="font-mono">{entry.entry_date}</td>
                                                <td className="font-mono">{entry.entry_number}</td>
                                                <td>{entry.description}</td>
                                                <td>{entry.reference || '-'}</td>
                                                <td style={{ textAlign: 'left', color: parseFloat(entry.debit) > 0 ? 'var(--text-primary)' : 'var(--text-light)' }}>
                                                    {parseFloat(entry.debit) > 0 ? formatNumber(entry.debit) : '-'}
                                                </td>
                                                <td style={{ textAlign: 'left', color: parseFloat(entry.credit) > 0 ? 'var(--text-primary)' : 'var(--text-light)' }}>
                                                    {parseFloat(entry.credit) > 0 ? formatNumber(entry.credit) : '-'}
                                                </td>
                                                <td style={{ textAlign: 'left', fontWeight: 'bold' }}>
                                                    {formatNumber(Math.abs(entry.running_balance))}
                                                </td>
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                                {entriesWithBalance.length > 0 && (
                                    <tfoot>
                                        <tr style={{ background: 'var(--primary)', color: 'white', fontWeight: 'bold' }}>
                                            <td colSpan="4" style={{ textAlign: 'center' }}>{t('accounting.general_ledger.totals')}</td>
                                            <td style={{ textAlign: 'left' }}>{formatNumber(totalDebit)}</td>
                                            <td style={{ textAlign: 'left' }}>{formatNumber(totalCredit)}</td>
                                            <td style={{ textAlign: 'left' }}>{formatNumber(Math.abs(runningBalance))}</td>
                                        </tr>
                                    </tfoot>
                                )}
                            </table>
                        </div>
                    </div>
                </>
            )}
        </div>
    )
}

export default GeneralLedger
