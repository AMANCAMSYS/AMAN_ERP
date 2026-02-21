import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { taxesAPI } from '../../utils/api'
import { useTranslation } from 'react-i18next'
import { formatNumber } from '../../utils/format'
import { getCurrency } from '../../utils/auth'

import DateInput from '../../components/common/DateInput';
function TaxReturnDetails() {
    const { t } = useTranslation()
    const { id } = useParams()
    const navigate = useNavigate()
    const currency = getCurrency()
    const [loading, setLoading] = useState(true)
    const [data, setData] = useState(null)
    const [error, setError] = useState(null)
    const [showPayModal, setShowPayModal] = useState(false)
    const [payForm, setPayForm] = useState({ amount: 0, payment_date: new Date().toISOString().split('T')[0], payment_method: 'bank_transfer', reference: '', notes: '' })
    const [showFileModal, setShowFileModal] = useState(false)
    const [fileForm, setFileForm] = useState({ penalty_amount: 0, interest_amount: 0 })
    const [actionLoading, setActionLoading] = useState(false)
    const [treasuryAccounts, setTreasuryAccounts] = useState([])

    const fetchData = async () => {
        try {
            setLoading(true)
            const res = await taxesAPI.getReturn(id)
            setData(res.data)
            setPayForm(prev => ({ ...prev, amount: res.data.remaining_amount || 0 }))
        } catch (err) {
            setError(err.response?.data?.detail || 'خطأ في تحميل البيانات')
        } finally {
            setLoading(false)
        }
    }

    const fetchTreasury = async () => {
        try {
            const { default: api } = await import('../../utils/api')
            const res = await api.get('/treasury/accounts')
            setTreasuryAccounts(res.data || [])
        } catch (e) { /* ignore */ }
    }

    useEffect(() => {
        fetchData()
        fetchTreasury()
    }, [id])

    const handleFile = async () => {
        setActionLoading(true)
        try {
            await taxesAPI.fileReturn(id, fileForm)
            setShowFileModal(false)
            fetchData()
        } catch (err) {
            alert(err.response?.data?.detail || 'خطأ')
        } finally {
            setActionLoading(false)
        }
    }

    const handleCancel = async () => {
        if (!confirm(t('taxes.confirm_cancel') || 'هل أنت متأكد من إلغاء هذا الإقرار؟')) return
        setActionLoading(true)
        try {
            await taxesAPI.cancelReturn(id)
            fetchData()
        } catch (err) {
            alert(err.response?.data?.detail || 'خطأ')
        } finally {
            setActionLoading(false)
        }
    }

    const handlePay = async () => {
        setActionLoading(true)
        try {
            await taxesAPI.createPayment({
                tax_return_id: parseInt(id),
                payment_date: payForm.payment_date,
                amount: parseFloat(payForm.amount),
                payment_method: payForm.payment_method,
                reference: payForm.reference || null,
                notes: payForm.notes || null,
                treasury_account_id: payForm.treasury_account_id ? parseInt(payForm.treasury_account_id) : null
            })
            setShowPayModal(false)
            fetchData()
        } catch (err) {
            alert(err.response?.data?.detail || 'خطأ')
        } finally {
            setActionLoading(false)
        }
    }

    const getStatusBadge = (status) => {
        const map = {
            draft: { label: t('taxes.status_draft') || 'مسودة', bg: 'rgb(254, 243, 199)', color: 'rgb(217, 119, 6)', emoji: '⏳' },
            filed: { label: t('taxes.status_filed') || 'مقدم', bg: 'rgba(59, 130, 246, 0.1)', color: 'rgb(59, 130, 246)', emoji: '📤' },
            paid: { label: t('taxes.status_paid') || 'مدفوع', bg: 'rgb(220, 252, 231)', color: 'rgb(22, 163, 74)', emoji: '✅' },
            cancelled: { label: t('taxes.status_cancelled') || 'ملغى', bg: 'rgb(254, 226, 226)', color: 'rgb(220, 38, 38)', emoji: '❌' }
        }
        const s = map[status] || { label: status, bg: 'rgba(107, 114, 128, 0.082)', color: 'rgb(107, 114, 128)', emoji: '' }
        return <span style={{ background: s.bg, color: s.color, padding: '6px 16px', borderRadius: '20px', fontSize: '14px', fontWeight: '600', whiteSpace: 'nowrap' }}>
            {s.emoji} {s.label}
        </span>
    }

    const paymentMethodLabel = (method) => {
        const map = { bank_transfer: t('taxes.bank_transfer') || 'تحويل بنكي', cash: t('taxes.cash') || 'نقدي', cheque: t('taxes.cheque') || 'شيك' }
        return map[method] || method
    }

    if (loading) return <div className="page-center"><span className="loading"></span></div>
    if (error) return <div className="alert alert-danger m-4">{error}</div>
    if (!data) return null

    return (
        <div className="workspace fade-in">
            {/* Header */}
            <div className="workspace-header">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
                    <div>
                        <h1 className="workspace-title">📋 {t('taxes.return_details') || 'تفاصيل الإقرار الضريبي'}</h1>
                        <p className="workspace-subtitle" style={{ fontFamily: 'monospace', fontSize: '16px' }}>
                            {data.return_number} — {t('taxes.period') || 'الفترة'}: {data.tax_period}
                        </p>
                    </div>
                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                        {getStatusBadge(data.status)}
                        {data.status === 'draft' && (
                            <>
                                <button className="btn btn-primary" onClick={() => setShowFileModal(true)} disabled={actionLoading}>
                                    📤 {t('taxes.file_return') || 'تقديم الإقرار'}
                                </button>
                                <button className="btn btn-danger" onClick={handleCancel} disabled={actionLoading}>
                                    ❌ {t('common.cancel') || 'إلغاء'}
                                </button>
                            </>
                        )}
                        {data.status === 'filed' && data.remaining_amount > 0 && (
                            <>
                                <button className="btn btn-success" onClick={() => setShowPayModal(true)} disabled={actionLoading}>
                                    💰 {t('taxes.record_payment') || 'تسجيل دفعة'}
                                </button>
                                <button className="btn btn-danger" onClick={handleCancel} disabled={actionLoading}>
                                    ❌ {t('common.cancel') || 'إلغاء'}
                                </button>
                            </>
                        )}
                        <button className="btn btn-secondary" onClick={() => navigate('/taxes')}>
                            ← {t('common.back') || 'رجوع'}
                        </button>
                    </div>
                </div>
            </div>

            {/* Summary Cards */}
            <div className="metrics-grid mt-4" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))' }}>
                <div className="metric-card">
                    <div className="metric-label">{t('taxes.taxable_amount') || 'المبلغ الخاضع'}</div>
                    <div className="metric-value">{formatNumber(data.taxable_amount)} <small>{currency}</small></div>
                </div>
                <div className="metric-card">
                    <div className="metric-label">{t('taxes.tax_amount') || 'مبلغ الضريبة'}</div>
                    <div className="metric-value text-secondary">{formatNumber(data.tax_amount)} <small>{currency}</small></div>
                </div>
                {(data.penalty_amount > 0 || data.interest_amount > 0) && (
                    <div className="metric-card">
                        <div className="metric-label">{t('taxes.penalties') || 'غرامات + فوائد'}</div>
                        <div className="metric-value text-error">{formatNumber(parseFloat(data.penalty_amount || 0) + parseFloat(data.interest_amount || 0))} <small>{currency}</small></div>
                    </div>
                )}
                <div className="metric-card" style={{ borderColor: 'var(--primary)' }}>
                    <div className="metric-label" style={{ fontWeight: 'bold' }}>{t('taxes.total_amount') || 'الإجمالي المستحق'}</div>
                    <div className="metric-value text-primary" style={{ fontSize: '28px' }}>{formatNumber(data.total_amount)} <small>{currency}</small></div>
                </div>
                <div className="metric-card">
                    <div className="metric-label">{t('taxes.paid_amount') || 'المدفوع'}</div>
                    <div className="metric-value text-success">{formatNumber(data.paid_amount)} <small>{currency}</small></div>
                </div>
                <div className="metric-card">
                    <div className="metric-label">{t('taxes.remaining') || 'المتبقي'}</div>
                    <div className={`metric-value ${data.remaining_amount > 0 ? 'text-error' : 'text-success'}`}>
                        {formatNumber(data.remaining_amount)} <small>{currency}</small>
                    </div>
                </div>
            </div>

            {/* Info Card */}
            <div className="card mt-4">
                <h3 className="section-title">{t('taxes.return_info') || 'معلومات الإقرار'}</h3>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginTop: '12px' }}>
                    <div><strong>{t('taxes.return_number') || 'رقم الإقرار'}:</strong> <span style={{ fontFamily: 'monospace' }}>{data.return_number}</span></div>
                    <div><strong>{t('taxes.period') || 'الفترة'}:</strong> {data.tax_period}</div>
                    <div><strong>{t('taxes.tax_type') || 'نوع الضريبة'}:</strong> {data.tax_type === 'vat' ? 'ضريبة القيمة المضافة' : data.tax_type}</div>
                    <div><strong>{t('taxes.due_date') || 'تاريخ الاستحقاق'}:</strong> {data.due_date || '-'}</div>
                    <div><strong>{t('taxes.filed_date') || 'تاريخ التقديم'}:</strong> {data.filed_date || '-'}</div>
                    <div><strong>{t('taxes.created_by') || 'أنشئ بواسطة'}:</strong> {data.created_by_name || '-'}</div>
                    {data.notes && <div style={{ gridColumn: 'span 2' }}><strong>{t('taxes.notes') || 'ملاحظات'}:</strong> {data.notes}</div>}
                </div>
            </div>

            {/* Payments Table */}
            <div className="card mt-4">
                <h3 className="section-title">{t('taxes.payments') || 'المدفوعات'}</h3>
                {data.payments && data.payments.length > 0 ? (
                    <div className="data-table-container mt-3">
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th>{t('taxes.payment_number') || 'رقم الدفعة'}</th>
                                    <th>{t('common.date') || 'التاريخ'}</th>
                                    <th style={{ textAlign: 'left' }}>{t('taxes.amount') || 'المبلغ'}</th>
                                    <th>{t('taxes.payment_method') || 'طريقة الدفع'}</th>
                                    <th>{t('taxes.reference') || 'المرجع'}</th>
                                    <th>{t('common.status') || 'الحالة'}</th>
                                </tr>
                            </thead>
                            <tbody>
                                {data.payments.map(p => (
                                    <tr key={p.id}>
                                        <td>
                                            <span className="fw-bold" style={{ color: 'var(--primary)', fontFamily: 'monospace' }}>{p.payment_number}</span>
                                        </td>
                                        <td style={{ whiteSpace: 'nowrap' }}>{new Date(p.payment_date).toLocaleDateString('ar-EG')}</td>
                                        <td style={{ textAlign: 'left', fontWeight: '700', whiteSpace: 'nowrap' }}>
                                            {formatNumber(p.amount)} <span className="text-muted fw-normal small">{currency}</span>
                                        </td>
                                        <td>
                                            <span style={{ background: 'rgba(107, 114, 128, 0.082)', color: 'rgb(107, 114, 128)', padding: '4px 10px', borderRadius: '6px', fontSize: '12px', fontWeight: '600' }}>
                                                {paymentMethodLabel(p.payment_method)}
                                            </span>
                                        </td>
                                        <td>{p.reference || <span className="text-muted">—</span>}</td>
                                        <td>
                                            <span style={{ background: 'rgb(220, 252, 231)', color: 'rgb(22, 163, 74)', padding: '4px 12px', borderRadius: '20px', fontSize: '12px', fontWeight: '600', whiteSpace: 'nowrap' }}>
                                                ✅ {p.status === 'confirmed' ? (t('taxes.confirmed') || 'مؤكد') : p.status}
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <p className="text-muted mt-3">{t('taxes.no_payments') || 'لا توجد مدفوعات مسجلة'}</p>
                )}
            </div>

            {/* File Modal */}
            {showFileModal && (
                <div className="modal-backdrop" onClick={() => setShowFileModal(false)}>
                    <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: '450px' }}>
                        <div className="modal-header">
                            <h3>📤 {t('taxes.file_return') || 'تقديم الإقرار الضريبي'}</h3>
                            <button className="btn-close" onClick={() => setShowFileModal(false)}>✕</button>
                        </div>
                        <div className="modal-body">
                            <p>{t('taxes.file_confirm_msg') || 'سيتم تغيير حالة الإقرار من "مسودة" إلى "مقدم". يمكنك إضافة غرامات أو فوائد إن وجدت.'}</p>
                            <div className="form-group mt-3">
                                <label className="form-label">{t('taxes.penalty_amount') || 'مبلغ الغرامة'}</label>
                                <input type="number" className="form-control" min="0" step="0.01"
                                    value={fileForm.penalty_amount}
                                    onChange={e => setFileForm({...fileForm, penalty_amount: parseFloat(e.target.value) || 0})} />
                            </div>
                            <div className="form-group">
                                <label className="form-label">{t('taxes.interest_amount') || 'مبلغ الفوائد'}</label>
                                <input type="number" className="form-control" min="0" step="0.01"
                                    value={fileForm.interest_amount}
                                    onChange={e => setFileForm({...fileForm, interest_amount: parseFloat(e.target.value) || 0})} />
                            </div>
                            <div className="alert alert-info mt-2">
                                {t('taxes.new_total') || 'الإجمالي الجديد'}: <strong>{formatNumber(parseFloat(data.tax_amount || 0) + (fileForm.penalty_amount || 0) + (fileForm.interest_amount || 0))} {currency}</strong>
                            </div>
                        </div>
                        <div className="modal-footer">
                            <button className="btn btn-secondary" onClick={() => setShowFileModal(false)}>{t('common.cancel') || 'إلغاء'}</button>
                            <button className="btn btn-primary" onClick={handleFile} disabled={actionLoading}>
                                {actionLoading ? '...' : (t('taxes.submit') || 'تقديم')}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Payment Modal */}
            {showPayModal && (
                <div className="modal-backdrop" onClick={() => setShowPayModal(false)}>
                    <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: '500px' }}>
                        <div className="modal-header">
                            <h3>💰 {t('taxes.record_payment') || 'تسجيل دفعة ضريبية'}</h3>
                            <button className="btn-close" onClick={() => setShowPayModal(false)}>✕</button>
                        </div>
                        <div className="modal-body">
                            <div className="alert alert-info">
                                {t('taxes.remaining') || 'المتبقي'}: <strong>{formatNumber(data.remaining_amount)} {currency}</strong>
                            </div>
                            <div className="form-group mt-3">
                                <label className="form-label">{t('taxes.amount') || 'المبلغ'} *</label>
                                <input type="number" className="form-control" min="0.01" step="0.01"
                                    max={data.remaining_amount}
                                    value={payForm.amount}
                                    onChange={e => setPayForm({...payForm, amount: parseFloat(e.target.value) || 0})} />
                            </div>
                            <div className="form-group">
                                <label className="form-label">{t('taxes.payment_date') || 'تاريخ الدفع'} *</label>
                                <DateInput className="form-control" value={payForm.payment_date}
                                    onChange={e => setPayForm({...payForm, payment_date: e.target.value})} />
                            </div>
                            <div className="form-group">
                                <label className="form-label">{t('taxes.payment_method') || 'طريقة الدفع'}</label>
                                <select className="form-control" value={payForm.payment_method}
                                    onChange={e => setPayForm({...payForm, payment_method: e.target.value})}>
                                    <option value="bank_transfer">{t('taxes.bank_transfer') || 'تحويل بنكي'}</option>
                                    <option value="cash">{t('taxes.cash') || 'نقدي'}</option>
                                    <option value="cheque">{t('taxes.cheque') || 'شيك'}</option>
                                </select>
                            </div>
                            {treasuryAccounts.length > 0 && (
                                <div className="form-group">
                                    <label className="form-label">{t('taxes.treasury_account') || 'حساب الخزينة'}</label>
                                    <select className="form-control" value={payForm.treasury_account_id || ''}
                                        onChange={e => setPayForm({...payForm, treasury_account_id: e.target.value})}>
                                        <option value="">{t('taxes.auto_select') || '— تلقائي —'}</option>
                                        {treasuryAccounts.map(ta => (
                                            <option key={ta.id} value={ta.id}>{ta.name} ({ta.currency})</option>
                                        ))}
                                    </select>
                                </div>
                            )}
                            <div className="form-group">
                                <label className="form-label">{t('taxes.reference') || 'رقم المرجع'}</label>
                                <input className="form-control" value={payForm.reference}
                                    onChange={e => setPayForm({...payForm, reference: e.target.value})}
                                    placeholder={t('taxes.ref_placeholder') || 'رقم الإيصال أو التحويل'} />
                            </div>
                            <div className="form-group">
                                <label className="form-label">{t('taxes.notes') || 'ملاحظات'}</label>
                                <textarea className="form-control" rows="2" value={payForm.notes}
                                    onChange={e => setPayForm({...payForm, notes: e.target.value})} />
                            </div>
                        </div>
                        <div className="modal-footer">
                            <button className="btn btn-secondary" onClick={() => setShowPayModal(false)}>{t('common.cancel') || 'إلغاء'}</button>
                            <button className="btn btn-success" onClick={handlePay} disabled={actionLoading || payForm.amount <= 0}>
                                {actionLoading ? '...' : (t('taxes.confirm_payment') || 'تأكيد الدفع')}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}

export default TaxReturnDetails
