import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { accountingAPI } from '../../utils/api'
import { getCurrency } from '../../utils/auth'
import { formatNumber } from '../../utils/format'
import BackButton from '../../components/common/BackButton'
import '../../components/ModuleStyles.css'
import { useToast } from '../../context/ToastContext'

function IntercompanyTransactions() {
    const { t } = useTranslation()
  const { showToast } = useToast()
    const currency = getCurrency()
    const [transactions, setTransactions] = useState([])
    const [eliminationReport, setEliminationReport] = useState(null)
    const [loading, setLoading] = useState(true)
    const [tab, setTab] = useState('list')
    const [showForm, setShowForm] = useState(false)
    const [form, setForm] = useState({
        target_company_id: '', transaction_type: 'sale',
        description: '', amount: '', currency: 'SAR', reference: ''
    })

    useEffect(() => { fetchData() }, [])

    const fetchData = async () => {
        try {
            setLoading(true)
            const res = await accountingAPI.listIntercompanyTransactions()
            setTransactions(res.data)
        } catch (err) {
            console.error('Failed to fetch intercompany transactions', err)
        } finally {
            setLoading(false)
        }
    }

    const fetchElimination = async () => {
        try {
            const res = await accountingAPI.getIntercompanyEliminationReport()
            setEliminationReport(res.data)
            setTab('elimination')
        } catch (err) {
            showToast(err.response?.data?.detail || 'Error', 'error')
        }
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        try {
            await accountingAPI.createIntercompanyTransaction({
                target_company_id: form.target_company_id,
                transaction_type: form.transaction_type,
                description: form.description,
                amount: parseFloat(form.amount),
                currency: form.currency,
                reference: form.reference || undefined
            })
            setShowForm(false)
            setForm({ target_company_id: '', transaction_type: 'sale', description: '', amount: '', currency: 'SAR', reference: '' })
            fetchData()
        } catch (err) {
            showToast(err.response?.data?.detail || 'Error', 'error')
        }
    }

    const handleProcess = async (id) => {
        if (!confirm(t('accounting.confirm_process', 'هل تريد معالجة هذه المعاملة وإنشاء القيود المحاسبية؟'))) return
        try {
            await accountingAPI.processIntercompanyTransaction(id)
            fetchData()
        } catch (err) {
            showToast(err.response?.data?.detail || 'Error', 'error')
        }
    }

    const getStatusBadge = (status) => {
        const map = { pending: 'badge-warning', processed: 'badge-success', eliminated: 'badge-info' }
        return map[status] || 'badge-secondary'
    }

    if (loading) return <div className="loading-spinner"><div className="spinner"></div></div>

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <div>
                    <h1 className="workspace-title">{t('accounting.intercompany', 'المعاملات بين الشركات')}</h1>
                    <p className="workspace-subtitle">{t('accounting.intercompany_desc', 'إدارة المعاملات المالية بين الشركات التابعة والاستبعادات')}</p>
                </div>
            </div>

            {/* Tabs + Actions */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <div className="tabs">
                    <button className={`tab ${tab === 'list' ? 'active' : ''}`} onClick={() => setTab('list')}>
                        {t('accounting.ic_transactions', 'المعاملات')}
                    </button>
                    <button className={`tab ${tab === 'elimination' ? 'active' : ''}`} onClick={fetchElimination}>
                        {t('accounting.elimination_report', 'تقرير الاستبعاد')}
                    </button>
                </div>
                <button className="btn btn-primary btn-sm" onClick={() => setShowForm(!showForm)}>
                    {showForm ? t('common.cancel', 'إلغاء') : t('accounting.add_ic_transaction', '+ معاملة جديدة')}
                </button>
            </div>

            {/* Create Form */}
            {showForm && (
                <div className="section-card" style={{ marginBottom: 16 }}>
                    <h3 className="section-title">{t('accounting.new_ic_transaction', 'معاملة جديدة بين الشركات')}</h3>
                    <form onSubmit={handleSubmit}>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 12 }}>
                            <div className="form-group">
                                <label className="form-label">{t('accounting.target_company', 'الشركة المستهدفة (ID)')} *</label>
                                <input className="form-input" required value={form.target_company_id}
                                    onChange={e => setForm({ ...form, target_company_id: e.target.value })}
                                    placeholder="e.g. fcfa5fae" />
                            </div>
                            <div className="form-group">
                                <label className="form-label">{t('accounting.transaction_type', 'النوع')}</label>
                                <select className="form-input" value={form.transaction_type}
                                    onChange={e => setForm({ ...form, transaction_type: e.target.value })}>
                                    <option value="sale">{t('accounting.ic_sale', 'بيع')}</option>
                                    <option value="purchase">{t('accounting.ic_purchase', 'شراء')}</option>
                                    <option value="service">{t('accounting.ic_service', 'خدمة')}</option>
                                    <option value="transfer">{t('accounting.ic_transfer', 'تحويل')}</option>
                                </select>
                            </div>
                            <div className="form-group">
                                <label className="form-label">{t('common.amount', 'المبلغ')} *</label>
                                <input className="form-input" type="number" step="0.01" required value={form.amount}
                                    onChange={e => setForm({ ...form, amount: e.target.value })} />
                            </div>
                            <div className="form-group">
                                <label className="form-label">{t('common.currency', 'العملة')}</label>
                                <input className="form-input" value={form.currency}
                                    onChange={e => setForm({ ...form, currency: e.target.value })} />
                            </div>
                            <div className="form-group" style={{ gridColumn: 'span 2' }}>
                                <label className="form-label">{t('common.description', 'الوصف')} *</label>
                                <input className="form-input" required value={form.description}
                                    onChange={e => setForm({ ...form, description: e.target.value })} />
                            </div>
                            <div className="form-group">
                                <label className="form-label">{t('accounting.reference', 'المرجع')}</label>
                                <input className="form-input" value={form.reference}
                                    onChange={e => setForm({ ...form, reference: e.target.value })}
                                    placeholder={t('accounting.auto_generated', 'تلقائي')} />
                            </div>
                        </div>
                        <div style={{ marginTop: 12 }}>
                            <button type="submit" className="btn btn-primary btn-sm">{t('common.save', 'حفظ')}</button>
                        </div>
                    </form>
                </div>
            )}

            {/* Transactions List */}
            {tab === 'list' && (
                <div className="section-card">
                    <h3 className="section-title">{t('accounting.ic_transactions', 'المعاملات')} ({transactions.length})</h3>
                    {transactions.length === 0 ? (
                        <p style={{ color: '#9ca3af', textAlign: 'center', padding: 24 }}>
                            {t('common.no_data', 'لا توجد بيانات')}
                        </p>
                    ) : (
                        <div className="data-table-container">
                            <table className="data-table">
                                <thead>
                                    <tr>
                                        <th>#</th>
                                        <th>{t('accounting.reference', 'المرجع')}</th>
                                        <th>{t('accounting.target_company', 'الشركة المستهدفة')}</th>
                                        <th>{t('accounting.transaction_type', 'النوع')}</th>
                                        <th>{t('common.amount', 'المبلغ')}</th>
                                        <th>{t('common.status', 'الحالة')}</th>
                                        <th>{t('common.date', 'التاريخ')}</th>
                                        <th>{t('common.actions', 'إجراءات')}</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {transactions.map(tx => (
                                        <tr key={tx.id}>
                                            <td>{tx.id}</td>
                                            <td style={{ fontWeight: 600 }}>{tx.reference}</td>
                                            <td>{tx.target_company_id}</td>
                                            <td>
                                                <span className="badge badge-info">
                                                    {t(`accounting.ic_${tx.transaction_type}`, tx.transaction_type)}
                                                </span>
                                            </td>
                                            <td>{formatNumber(tx.amount)} {tx.currency || currency}</td>
                                            <td>
                                                <span className={`badge ${getStatusBadge(tx.status)}`}>
                                                    {t(`common.status_${tx.status}`, tx.status)}
                                                </span>
                                            </td>
                                            <td style={{ color: '#9ca3af', fontSize: '0.85rem' }}>
                                                {tx.created_at ? new Date(tx.created_at).toLocaleDateString('ar-SA') : '—'}
                                            </td>
                                            <td>
                                                {tx.status === 'pending' && (
                                                    <button className="btn btn-success btn-sm" onClick={() => handleProcess(tx.id)}>
                                                        {t('accounting.process', 'معالجة')}
                                                    </button>
                                                )}
                                                {tx.status === 'processed' && (
                                                    <span style={{ color: '#22c55e', fontSize: '0.85rem' }}>✓ {t('accounting.processed', 'تمت المعالجة')}</span>
                                                )}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            )}

            {/* Elimination Report */}
            {tab === 'elimination' && eliminationReport && (
                <>
                    {/* Totals */}
                    <div className="metrics-grid" style={{ marginBottom: 16 }}>
                        <div className="metric-card">
                            <div className="metric-label">{t('accounting.total_intercompany', 'إجمالي المعاملات')}</div>
                            <div className="metric-value text-primary">{formatNumber(eliminationReport.totals?.total_intercompany || 0)} <small>{currency}</small></div>
                        </div>
                        <div className="metric-card">
                            <div className="metric-label">{t('accounting.total_eliminated', 'تم الاستبعاد')}</div>
                            <div className="metric-value text-success">{formatNumber(eliminationReport.totals?.total_eliminated || 0)} <small>{currency}</small></div>
                        </div>
                        <div className="metric-card">
                            <div className="metric-label">{t('accounting.pending_elimination', 'بانتظار الاستبعاد')}</div>
                            <div className="metric-value text-warning">{formatNumber(eliminationReport.totals?.pending_elimination || 0)} <small>{currency}</small></div>
                        </div>
                    </div>

                    {/* By Company */}
                    <div className="section-card">
                        <h3 className="section-title">{t('accounting.elimination_by_company', 'التفاصيل حسب الشركة')}</h3>
                        {eliminationReport.by_company?.length === 0 ? (
                            <p style={{ color: '#9ca3af', textAlign: 'center', padding: 24 }}>{t('common.no_data', 'لا توجد بيانات')}</p>
                        ) : (
                            <div className="data-table-container">
                                <table className="data-table">
                                    <thead>
                                        <tr>
                                            <th>{t('accounting.target_company', 'الشركة المستهدفة')}</th>
                                            <th>{t('accounting.transaction_type', 'النوع')}</th>
                                            <th>{t('common.count', 'العدد')}</th>
                                            <th>{t('accounting.total_amount', 'إجمالي المبلغ')}</th>
                                            <th>{t('accounting.processed_amount', 'تمت المعالجة')}</th>
                                            <th>{t('accounting.pending_amount', 'معلق')}</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {eliminationReport.by_company.map((row, i) => (
                                            <tr key={i}>
                                                <td style={{ fontWeight: 600 }}>{row.target_company_id}</td>
                                                <td><span className="badge badge-info">{row.transaction_type}</span></td>
                                                <td>{row.txn_count}</td>
                                                <td>{formatNumber(row.total_amount)} {currency}</td>
                                                <td style={{ color: '#22c55e' }}>{formatNumber(row.processed_amount || 0)} {currency}</td>
                                                <td style={{ color: '#f97316' }}>{formatNumber(row.pending_amount || 0)} {currency}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                </>
            )}
        </div>
    )
}

export default IntercompanyTransactions
