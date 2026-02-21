import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { budgetsAPI } from '../../utils/api'
import { useBranch } from '../../context/BranchContext'
import { useTranslation } from 'react-i18next'
import { formatNumber } from '../../utils/format'
import { getCurrency } from '../../utils/auth'
import { toInputDate } from '../../utils/dateUtils'
import CustomDatePicker from '../../components/common/CustomDatePicker'

function BudgetReport() {
    const { t, i18n } = useTranslation()
    const { currentBranch } = useBranch()
    const [budgets, setBudgets] = useState([])
    const [selectedBudgetId, setSelectedBudgetId] = useState('')
    const [data, setData] = useState(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const [fromDate, setFromDate] = useState('')
    const [toDate, setToDate] = useState('')
    const currency = getCurrency()

    useEffect(() => {
        const fetchBudgets = async () => {
            try {
                const response = await budgetsAPI.list()
                setBudgets(response.data)
                if (response.data.length > 0) {
                    setSelectedBudgetId(response.data[0].id)
                }
            } catch (err) {
                console.error("Failed to fetch budgets", err)
            }
        }
        fetchBudgets()
    }, [])

    const fetchData = async () => {
        if (!selectedBudgetId) return
        try {
            setLoading(true)
            setError(null)

            const params = {}
            if (fromDate) params.from_date = fromDate
            if (toDate) params.to_date = toDate

            const response = await budgetsAPI.getReport(selectedBudgetId, params)
            setData(response.data)
        } catch (err) {
            console.error("Failed to fetch budget report", err)
            setError(t('errors.fetch_failed'))
        } finally {
            setLoading(false)
        }
    }

    const navigate = useNavigate()

    useEffect(() => {
        if (selectedBudgetId && budgets.length > 0) {
            const budget = budgets.find(b => b.id.toString() === selectedBudgetId.toString());
            if (budget) {
                setFromDate(budget.start_date);
                setToDate(budget.end_date);
            }
        }
    }, [selectedBudgetId, budgets]);

    useEffect(() => {
        fetchData()
    }, [selectedBudgetId, currentBranch, fromDate, toDate])

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                        <button onClick={() => navigate('/accounting/budgets')} className="table-action-btn" style={{ background: 'var(--bg-hover)', borderRadius: '50%', width: '36px', height: '36px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                            <ArrowLeft size={20} />
                        </button>
                        <div>
                            <h1 className="workspace-title">{t('reports.budget_vs_actual.title')}</h1>
                        </div>
                    </div>
                    <div style={{ display: 'flex', gap: '12px' }}>
                        <div style={{ minWidth: '180px' }}>
                            <label className="form-label">{t('reports.budget_vs_actual.select_budget')}</label>
                            <select
                                className="form-input w-full"
                                value={selectedBudgetId}
                                onChange={e => setSelectedBudgetId(e.target.value)}
                            >
                                <option value="">{t('common.select')}</option>
                                {budgets.map(b => (
                                    <option key={b.id} value={b.id}>{b.name}</option>
                                ))}
                            </select>
                        </div>
                        <CustomDatePicker
                            label={t('common.start_date')}
                            selected={fromDate}
                            onChange={setFromDate}
                        />
                        <CustomDatePicker
                            label={t('common.end_date')}
                            selected={toDate}
                            onChange={setToDate}
                        />
                        <button className="btn btn-secondary" onClick={() => window.print()} style={{ alignSelf: 'flex-end', height: '42px' }}>
                            🖨️ {t('common.print')}
                        </button>
                    </div>
                </div>
            </div>

            {loading ? (
                <div className="text-center p-5">
                    <div className="spinner"></div>
                    <p className="mt-2">{t('common.loading')}</p>
                </div>
            ) : error ? (
                <div className="alert alert-danger">{error}</div>
            ) : data && (
                <div className="card card-flush" style={{ overflow: 'hidden' }}>
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>{t('accounting.coa.account')}</th>
                                <th className="text-center">{t('reports.budget_vs_actual.planned')} ({currency})</th>
                                <th className="text-center">{t('reports.budget_vs_actual.actual')} ({currency})</th>
                                <th className="text-center">{t('reports.budget_vs_actual.variance')} (%)</th>
                                <th className="text-center">{t('common.status_title')}</th>
                                <th className="text-center">{t('reports.budget_vs_actual.performance')}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {data.map((item, idx) => {
                                const isOverBudget = item.actual > item.planned;
                                const variancePct = item.planned > 0 ? ((item.actual - item.planned) / item.planned) * 100 : 0;
                                const performancePct = item.actual > 0 && item.planned > 0 ? (item.actual / item.planned) * 100 : 0;

                                return (
                                    <tr key={idx}>
                                        <td>
                                            <div style={{ fontWeight: '500', marginBottom: '4px' }}>
                                                {item.account_name}
                                            </div>
                                            <div style={{ fontSize: '12px', opacity: 0.6 }}>
                                                {item.account_number}
                                            </div>
                                        </td>
                                        <td className="text-center">{formatNumber(item.planned)}</td>
                                        <td className="text-center">{formatNumber(item.actual)}</td>
                                        <td className="text-center" style={{ fontWeight: '600' }}>
                                            <span style={{ color: isOverBudget ? '#dc2626' : '#059669' }}>
                                                {variancePct > 0 ? '+' : ''}{Math.round(variancePct)}%
                                            </span>
                                        </td>
                                        <td className="text-center">
                                            {isOverBudget ? (
                                                <span className="badge badge-danger">
                                                    ⚠️ {t('accounting.budgets.over_budget')}
                                                </span>
                                            ) : (
                                                <span className="badge badge-success">
                                                    ✅ {t('accounting.budgets.within_budget')}
                                                </span>
                                            )}
                                        </td>
                                        <td>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                                                <div style={{ flex: 1, height: '6px', background: '#f3f4f6', borderRadius: '3px', overflow: 'hidden' }}>
                                                    <div style={{
                                                        height: '100%',
                                                        width: `${Math.min(performancePct, 100)}%`,
                                                        background: isOverBudget ? '#dc2626' : '#10b981',
                                                        borderRadius: '3px'
                                                    }} />
                                                </div>
                                                <span style={{ fontSize: '12px', opacity: 0.7, minWidth: '40px', textAlign: 'right' }}>
                                                    {Math.round(performancePct)}%
                                                </span>
                                            </div>
                                        </td>
                                    </tr>
                                );
                            })}
                            {data.length === 0 && (
                                <tr>
                                    <td colSpan="6" className="start-guide">
                                        <div style={{ padding: '40px', textAlign: 'center' }}>
                                            <div style={{ fontSize: '40px', marginBottom: '12px' }}>📊</div>
                                            <div style={{ opacity: 0.6 }}>{t('common.no_data')}</div>
                                        </div>
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    )
}

export default BudgetReport
