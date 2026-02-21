import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { ArrowRight, Edit2, RefreshCw, FileText, XCircle, Calendar, DollarSign, User, Clock } from 'lucide-react'
import { contractsAPI } from '../../utils/api'
import { formatNumber } from '../../utils/format'
import { formatShortDate } from '../../utils/dateUtils'
import { useToast } from '../../context/ToastContext'
import SimpleModal from '../../components/common/SimpleModal'
import '../../components/ModuleStyles.css'

export default function ContractDetails() {
    const { t, i18n } = useTranslation()
    const navigate = useNavigate()
    const { id } = useParams()
    const isRTL = i18n.language === 'ar'
    const { showToast } = useToast()

    const [contract, setContract] = useState(null)
    const [loading, setLoading] = useState(true)
    const [showCancelModal, setShowCancelModal] = useState(false)
    const [showRenewModal, setShowRenewModal] = useState(false)
    const [actionLoading, setActionLoading] = useState(false)

    useEffect(() => {
        fetchContract()
    }, [id])

    const fetchContract = async () => {
        try {
            setLoading(true)
            const res = await contractsAPI.getContract(id)
            setContract(res.data)
        } catch (err) {
            console.error('Failed to fetch contract', err)
            showToast(t('contracts.details.load_error') || 'فشل في تحميل العقد', 'error')
        } finally {
            setLoading(false)
        }
    }

    const handleRenew = async () => {
        setActionLoading(true)
        try {
            await contractsAPI.renewContract(id)
            showToast(t('contracts.details.renewed_success') || 'تم تجديد العقد بنجاح', 'success')
            setShowRenewModal(false)
            fetchContract()
        } catch (err) {
            showToast(err.response?.data?.detail || t('contracts.details.renew_error') || 'فشل في تجديد العقد', 'error')
        } finally {
            setActionLoading(false)
        }
    }

    const handleCancel = async () => {
        setActionLoading(true)
        try {
            await contractsAPI.cancelContract(id)
            showToast(t('contracts.details.cancelled_success') || 'تم إلغاء العقد', 'success')
            setShowCancelModal(false)
            fetchContract()
        } catch (err) {
            showToast(err.response?.data?.detail || t('contracts.details.cancel_error') || 'فشل في إلغاء العقد', 'error')
        } finally {
            setActionLoading(false)
        }
    }

    const handleGenerateInvoice = async () => {
        setActionLoading(true)
        try {
            const res = await contractsAPI.generateInvoice(id)
            showToast(
                `${t('contracts.details.invoice_generated') || 'تم إنشاء الفاتورة'}: ${res.data.invoice_number}`, 'success'
            )
        } catch (err) {
            showToast(err.response?.data?.detail || t('contracts.details.invoice_error') || 'فشل في إنشاء الفاتورة', 'error')
        } finally {
            setActionLoading(false)
        }
    }

    if (loading) return <div className="page-center"><span className="loading"></span></div>
    if (!contract) return <div className="page-center"><p>{t('contracts.details.not_found') || 'العقد غير موجود'}</p></div>

    const getStatusBadge = (status) => {
        switch (status) {
            case 'active': return 'badge-success'
            case 'expired': return 'badge-danger'
            case 'cancelled': return 'badge-ghost'
            default: return 'badge-info'
        }
    }

    const getStatusLabel = (status) => {
        switch (status) {
            case 'active': return t('contracts.details.status_active') || 'نشط'
            case 'expired': return t('contracts.details.status_expired') || 'منتهي'
            case 'cancelled': return t('contracts.details.status_cancelled') || 'ملغي'
            default: return status
        }
    }

    const getTypeLabel = (type) => {
        switch (type) {
            case 'subscription': return t('contracts.details.type_subscription') || 'اشتراك'
            case 'fixed': return t('contracts.details.type_fixed') || 'ثابت'
            case 'recurring': return t('contracts.details.type_recurring') || 'متكرر'
            case 'sales': return t('contracts.details.type_sales') || 'مبيعات'
            case 'purchase': return t('contracts.details.type_purchase') || 'مشتريات'
            default: return type
        }
    }

    const getIntervalLabel = (interval) => {
        switch (interval) {
            case 'monthly': return t('contracts.details.interval_monthly') || 'شهري'
            case 'quarterly': return t('contracts.details.interval_quarterly') || 'ربع سنوي'
            case 'semi_annual': return t('contracts.details.interval_semi_annual') || 'نصف سنوي'
            case 'annual': return t('contracts.details.interval_annual') || 'سنوي'
            default: return interval
        }
    }

    // Calculate days remaining
    const daysRemaining = contract.end_date
        ? Math.ceil((new Date(contract.end_date) - new Date()) / (1000 * 60 * 60 * 24))
        : null

    // Calculate item totals
    const subtotal = (contract.items || []).reduce((sum, item) => sum + (item.quantity * item.unit_price), 0)
    const taxTotal = (contract.items || []).reduce((sum, item) => sum + (item.quantity * item.unit_price * item.tax_rate / 100), 0)

    return (
        <div className="workspace fade-in">
            {/* Header */}
            <div className="workspace-header">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <button className="btn btn-ghost" onClick={() => navigate('/sales/contracts')}>
                            <ArrowRight size={18} />
                        </button>
                        <div>
                            <h1 className="workspace-title" style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                {contract.contract_number}
                                <span className={`badge ${getStatusBadge(contract.status)}`}>
                                    {getStatusLabel(contract.status)}
                                </span>
                            </h1>
                            <p className="workspace-subtitle">
                                {contract.party_name} — {getTypeLabel(contract.contract_type)}
                            </p>
                        </div>
                    </div>
                    {contract.status === 'active' && (
                        <div style={{ display: 'flex', gap: '8px' }}>
                            <button className="btn btn-secondary" onClick={() => navigate(`/sales/contracts/${id}/edit`)}>
                                <Edit2 size={16} /> {t('contracts.details.edit') || 'تعديل'}
                            </button>
                            <button className="btn btn-primary" onClick={handleGenerateInvoice} disabled={actionLoading}>
                                <FileText size={16} /> {t('contracts.details.generate_invoice') || 'إنشاء فاتورة'}
                            </button>
                            <button className="btn btn-secondary" onClick={() => setShowRenewModal(true)}>
                                <RefreshCw size={16} /> {t('contracts.details.renew') || 'تجديد'}
                            </button>
                            <button className="btn btn-danger" onClick={() => setShowCancelModal(true)}>
                                <XCircle size={16} /> {t('contracts.details.cancel') || 'إلغاء'}
                            </button>
                        </div>
                    )}
                </div>
            </div>

            {/* Expiry Alert */}
            {contract.status === 'active' && daysRemaining !== null && daysRemaining <= 30 && daysRemaining > 0 && (
                <div className="alert alert-warning mb-4" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Clock size={18} />
                    {t('contracts.details.expiring_alert', { days: daysRemaining }) || `⚠️ هذا العقد سينتهي خلال ${daysRemaining} يوم`}
                </div>
            )}
            {contract.status === 'active' && daysRemaining !== null && daysRemaining <= 0 && (
                <div className="alert alert-error mb-4" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Clock size={18} />
                    {t('contracts.details.expired_alert') || '⚠️ هذا العقد منتهي الصلاحية ويحتاج تجديد أو إلغاء'}
                </div>
            )}

            {/* Summary Cards */}
            <div className="grid grid-4 mb-4">
                <div className="metric-card">
                    <div className="metric-icon" style={{ background: 'var(--primary-light)' }}>
                        <DollarSign size={20} style={{ color: 'var(--primary)' }} />
                    </div>
                    <div className="metric-content">
                        <span className="metric-label">{t('contracts.details.total_value') || 'قيمة العقد'}</span>
                        <span className="metric-value">{formatNumber(contract.total_amount)} {contract.currency}</span>
                    </div>
                </div>
                <div className="metric-card">
                    <div className="metric-icon" style={{ background: '#e8f5e9' }}>
                        <User size={20} style={{ color: '#2e7d32' }} />
                    </div>
                    <div className="metric-content">
                        <span className="metric-label">{t('contracts.details.client') || 'العميل'}</span>
                        <span className="metric-value" style={{ fontSize: '1rem' }}>{contract.party_name}</span>
                    </div>
                </div>
                <div className="metric-card">
                    <div className="metric-icon" style={{ background: '#fff3e0' }}>
                        <Calendar size={20} style={{ color: '#e65100' }} />
                    </div>
                    <div className="metric-content">
                        <span className="metric-label">{t('contracts.details.period') || 'الفترة'}</span>
                        <span className="metric-value" style={{ fontSize: '0.9rem' }}>
                            {formatShortDate(contract.start_date)} — {contract.end_date ? formatShortDate(contract.end_date) : '∞'}
                        </span>
                    </div>
                </div>
                <div className="metric-card">
                    <div className="metric-icon" style={{ background: '#e3f2fd' }}>
                        <RefreshCw size={20} style={{ color: '#1565c0' }} />
                    </div>
                    <div className="metric-content">
                        <span className="metric-label">{t('contracts.details.billing_cycle') || 'دورة الفوترة'}</span>
                        <span className="metric-value" style={{ fontSize: '1rem' }}>{getIntervalLabel(contract.billing_interval)}</span>
                    </div>
                </div>
            </div>

            {/* Contract Info */}
            <div className="grid grid-2 mb-4">
                <div className="card">
                    <h3 className="section-title">{t('contracts.details.info') || 'معلومات العقد'}</h3>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                        <div>
                            <label className="form-label" style={{ fontWeight: 'normal', color: '#888' }}>{t('contracts.details.contract_number') || 'رقم العقد'}</label>
                            <p style={{ fontWeight: 'bold' }}>{contract.contract_number}</p>
                        </div>
                        <div>
                            <label className="form-label" style={{ fontWeight: 'normal', color: '#888' }}>{t('contracts.details.type') || 'النوع'}</label>
                            <p>{getTypeLabel(contract.contract_type)}</p>
                        </div>
                        <div>
                            <label className="form-label" style={{ fontWeight: 'normal', color: '#888' }}>{t('contracts.details.start_date') || 'تاريخ البدء'}</label>
                            <p>{formatShortDate(contract.start_date)}</p>
                        </div>
                        <div>
                            <label className="form-label" style={{ fontWeight: 'normal', color: '#888' }}>{t('contracts.details.end_date') || 'تاريخ الانتهاء'}</label>
                            <p>{contract.end_date ? formatShortDate(contract.end_date) : t('contracts.details.no_end_date') || 'غير محدد'}</p>
                        </div>
                        <div>
                            <label className="form-label" style={{ fontWeight: 'normal', color: '#888' }}>{t('contracts.details.days_remaining') || 'الأيام المتبقية'}</label>
                            <p style={{ color: daysRemaining <= 30 ? '#e65100' : 'inherit', fontWeight: daysRemaining <= 30 ? 'bold' : 'normal' }}>
                                {daysRemaining !== null ? (daysRemaining > 0 ? `${daysRemaining} ${t('contracts.details.days') || 'يوم'}` : t('contracts.details.expired_label') || 'منتهي') : '—'}
                            </p>
                        </div>
                        <div>
                            <label className="form-label" style={{ fontWeight: 'normal', color: '#888' }}>{t('contracts.details.currency') || 'العملة'}</label>
                            <p>{contract.currency}</p>
                        </div>
                    </div>
                    {contract.notes && (
                        <div style={{ marginTop: '16px', padding: '12px', background: '#f9f9f9', borderRadius: '8px' }}>
                            <label className="form-label" style={{ fontWeight: 'normal', color: '#888' }}>{t('contracts.details.notes') || 'ملاحظات'}</label>
                            <p>{contract.notes}</p>
                        </div>
                    )}
                </div>

                {/* Totals */}
                <div className="card">
                    <h3 className="section-title">{t('contracts.details.financial_summary') || 'الملخص المالي'}</h3>
                    <div style={{ marginTop: '12px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 0', borderBottom: '1px solid #eee' }}>
                            <span>{t('contracts.details.subtotal') || 'المجموع الفرعي'}</span>
                            <span>{formatNumber(subtotal)} {contract.currency}</span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 0', borderBottom: '1px solid #eee' }}>
                            <span>{t('contracts.details.tax') || 'الضريبة'}</span>
                            <span>{formatNumber(taxTotal)} {contract.currency}</span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', padding: '14px 0', fontWeight: 'bold', fontSize: '1.2rem' }}>
                            <span>{t('contracts.details.grand_total') || 'الإجمالي'}</span>
                            <span style={{ color: 'var(--primary)' }}>{formatNumber(contract.total_amount)} {contract.currency}</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Items Table */}
            <div className="card">
                <h3 className="section-title">{t('contracts.details.items') || 'بنود العقد'} ({(contract.items || []).length})</h3>
                <table className="data-table">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>{t('contracts.details.item_desc') || 'الوصف'}</th>
                            <th>{t('contracts.details.quantity') || 'الكمية'}</th>
                            <th>{t('contracts.details.unit_price') || 'سعر الوحدة'}</th>
                            <th>{t('contracts.details.tax_rate') || 'الضريبة %'}</th>
                            <th>{t('contracts.details.item_total') || 'الإجمالي'}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {(contract.items || []).map((item, idx) => (
                            <tr key={item.id || idx}>
                                <td>{idx + 1}</td>
                                <td>{item.description || '—'}</td>
                                <td>{formatNumber(item.quantity)}</td>
                                <td>{formatNumber(item.unit_price)} {contract.currency}</td>
                                <td>{item.tax_rate}%</td>
                                <td style={{ fontWeight: 'bold' }}>{formatNumber(item.total)} {contract.currency}</td>
                            </tr>
                        ))}
                        {(contract.items || []).length === 0 && (
                            <tr>
                                <td colSpan="6" style={{ textAlign: 'center', padding: '24px', color: '#888' }}>
                                    {t('contracts.details.no_items') || 'لا توجد بنود'}
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>

            {/* Cancel Modal */}
            {showCancelModal && (
                <SimpleModal
                    title={t('contracts.details.cancel_title') || 'إلغاء العقد'}
                    onClose={() => setShowCancelModal(false)}
                >
                    <p style={{ marginBottom: '16px' }}>
                        {t('contracts.details.cancel_confirm') || 'هل أنت متأكد من إلغاء هذا العقد؟ لا يمكن التراجع عن هذا الإجراء.'}
                    </p>
                    <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                        <button className="btn btn-secondary" onClick={() => setShowCancelModal(false)} disabled={actionLoading}>
                            {t('common.close') || 'إغلاق'}
                        </button>
                        <button className="btn btn-danger" onClick={handleCancel} disabled={actionLoading}>
                            {actionLoading ? t('common.loading') || '...' : t('contracts.details.confirm_cancel') || 'تأكيد الإلغاء'}
                        </button>
                    </div>
                </SimpleModal>
            )}

            {/* Renew Modal */}
            {showRenewModal && (
                <SimpleModal
                    title={t('contracts.details.renew_title') || 'تجديد العقد'}
                    onClose={() => setShowRenewModal(false)}
                >
                    <p style={{ marginBottom: '16px' }}>
                        {t('contracts.details.renew_confirm') || 'سيتم تجديد العقد لفترة جديدة بناءً على دورة الفوترة الحالية.'}
                    </p>
                    <div style={{ background: '#f5f5f5', padding: '12px', borderRadius: '8px', marginBottom: '16px' }}>
                        <p><strong>{t('contracts.details.billing_cycle') || 'دورة الفوترة'}:</strong> {getIntervalLabel(contract.billing_interval)}</p>
                        <p><strong>{t('contracts.details.current_end') || 'تاريخ الانتهاء الحالي'}:</strong> {contract.end_date ? formatShortDate(contract.end_date) : '—'}</p>
                    </div>
                    <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                        <button className="btn btn-secondary" onClick={() => setShowRenewModal(false)} disabled={actionLoading}>
                            {t('common.close') || 'إغلاق'}
                        </button>
                        <button className="btn btn-primary" onClick={handleRenew} disabled={actionLoading}>
                            {actionLoading ? t('common.loading') || '...' : t('contracts.details.confirm_renew') || 'تأكيد التجديد'}
                        </button>
                    </div>
                </SimpleModal>
            )}
        </div>
    )
}
