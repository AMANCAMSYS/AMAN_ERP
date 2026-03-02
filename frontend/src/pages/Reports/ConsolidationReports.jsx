import { useState } from 'react'
import { consolidationAPI } from '../../utils/api'
import { getCurrency } from '../../utils/auth'
import { useTranslation } from 'react-i18next'
import { useToast } from '../../context/ToastContext'
import BackButton from '../../components/common/BackButton'
import { formatNumber } from '../../utils/format'
import DateInput from '../../components/common/DateInput';

function ConsolidationReports() {
    const { t } = useTranslation()
    const { showToast } = useToast()
    const currency = getCurrency()
    const [reportType, setReportType] = useState('trial_balance')
    const [dateFrom, setDateFrom] = useState('')
    const [dateTo, setDateTo] = useState('')
    const [data, setData] = useState(null)
    const [loading, setLoading] = useState(false)

    const handleGenerate = async () => {
        setLoading(true)
        try {
            const params = {}
            if (dateFrom) params.date_from = dateFrom
            if (dateTo) params.date_to = dateTo

            let res
            if (reportType === 'trial_balance') {
                res = await consolidationAPI.getTrialBalance(params)
            } else if (reportType === 'income_statement') {
                res = await consolidationAPI.getIncomeStatement(params)
            } else {
                res = await consolidationAPI.getBalanceSheet(params)
            }
            setData(res.data)
        } catch (err) {
            showToast(err.response?.data?.detail || t('common.error'), 'error')
        } finally { setLoading(false) }
    }

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <div className="header-title">
                    <h1 className="workspace-title">🏢 {t('consolidation.title')}</h1>
                    <p className="workspace-subtitle">{t('consolidation.subtitle')}</p>
                </div>
            </div>

            <div className="card p-4">
                <div className="form-grid-4">
                    <div className="form-group">
                        <label>{t('consolidation.report_type')}</label>
                        <select className="form-select" value={reportType} onChange={e => setReportType(e.target.value)}>
                            <option value="trial_balance">{t('consolidation.trial_balance')}</option>
                            <option value="income_statement">{t('consolidation.income_statement')}</option>
                            <option value="balance_sheet">{t('consolidation.balance_sheet')}</option>
                        </select>
                    </div>
                    <div className="form-group">
                        <label>{t('common.from_date')}</label>
                        <DateInput className="form-input" value={dateFrom} onChange={e => setDateFrom(e.target.value)} />
                    </div>
                    <div className="form-group">
                        <label>{t('common.to_date')}</label>
                        <DateInput className="form-input" value={dateTo} onChange={e => setDateTo(e.target.value)} />
                    </div>
                    <div className="form-group" style={{ display: 'flex', alignItems: 'flex-end' }}>
                        <button className="btn btn-primary" onClick={handleGenerate} disabled={loading}>
                            {loading ? t('common.loading') : t('common.generate')}
                        </button>
                    </div>
                </div>
            </div>

            {data && reportType === 'trial_balance' && (
                <div className="card mt-4">
                    <div className="p-4"><h3 className="card-title">{t('consolidation.consolidated_trial_balance')}</h3></div>
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>{t('common.account_code')}</th>
                                <th>{t('common.account_name')}</th>
                                <th>{t('common.debit')}</th>
                                <th>{t('common.credit')}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {(data.accounts || data).map((a, i) => (
                                <tr key={i}>
                                    <td className="font-medium">{a.account_code}</td>
                                    <td>{a.account_name}</td>
                                    <td className="text-danger">{a.total_debit ? formatNumber(a.total_debit) : '-'}</td>
                                    <td className="text-success">{a.total_credit ? formatNumber(a.total_credit) : '-'}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {data && reportType === 'income_statement' && (
                <div className="card mt-4 p-4">
                    <h3 className="card-title mb-3">{t('consolidation.consolidated_income_statement')}</h3>
                    {data.companies && data.companies.map((c, i) => (
                        <div key={i} className="mb-3 p-3 border rounded">
                            <h4 className="font-bold">{c.company_name}</h4>
                            <div className="grid grid-3 mt-2" style={{ gap: 8 }}>
                                <div><span className="text-muted">{t('common.revenue')}:</span> <strong className="text-success">{formatNumber(c.revenue)}</strong></div>
                                <div><span className="text-muted">{t('common.expenses')}:</span> <strong className="text-danger">{formatNumber(c.expenses)}</strong></div>
                                <div><span className="text-muted">{t('common.net_income')}:</span> <strong>{formatNumber(c.net_income)}</strong></div>
                            </div>
                        </div>
                    ))}
                    {data.consolidated && (
                        <div className="p-3 bg-light rounded mt-3">
                            <h4 className="font-bold text-primary">{t('consolidation.consolidated_total')}</h4>
                            <div className="grid grid-3 mt-2" style={{ gap: 8 }}>
                                <div>{t('common.revenue')}: <strong>{formatNumber(data.consolidated.revenue)}</strong></div>
                                <div>{t('common.expenses')}: <strong>{formatNumber(data.consolidated.expenses)}</strong></div>
                                <div>{t('common.net_income')}: <strong className="text-xl">{formatNumber(data.consolidated.net_income)}</strong></div>
                            </div>
                        </div>
                    )}
                </div>
            )}

            {data && reportType === 'balance_sheet' && (
                <div className="card mt-4 p-4">
                    <h3 className="card-title mb-3">{t('consolidation.consolidated_balance_sheet')}</h3>
                    {data.companies && data.companies.map((c, i) => (
                        <div key={i} className="mb-3 p-3 border rounded">
                            <h4 className="font-bold">{c.company_name}</h4>
                            <div className="grid grid-3 mt-2" style={{ gap: 8 }}>
                                <div><span className="text-muted">{t('consolidation.total_assets')}:</span> <strong className="text-primary">{formatNumber(c.total_assets)}</strong></div>
                                <div><span className="text-muted">{t('consolidation.total_liabilities')}:</span> <strong className="text-danger">{formatNumber(c.total_liabilities)}</strong></div>
                                <div><span className="text-muted">{t('consolidation.total_equity')}:</span> <strong className="text-success">{formatNumber(c.total_equity)}</strong></div>
                            </div>
                        </div>
                    ))}
                    {data.consolidated && (
                        <div className="p-3 bg-light rounded mt-3">
                            <h4 className="font-bold text-primary">{t('consolidation.consolidated_total')}</h4>
                            <div className="grid grid-3 mt-2" style={{ gap: 8 }}>
                                <div>{t('consolidation.total_assets')}: <strong>{formatNumber(data.consolidated.total_assets)}</strong></div>
                                <div>{t('consolidation.total_liabilities')}: <strong>{formatNumber(data.consolidated.total_liabilities)}</strong></div>
                                <div>{t('consolidation.total_equity')}: <strong className="text-xl">{formatNumber(data.consolidated.total_equity)}</strong></div>
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}

export default ConsolidationReports
