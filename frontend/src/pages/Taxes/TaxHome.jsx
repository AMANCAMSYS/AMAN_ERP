import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { taxesAPI, companiesAPI } from '../../utils/api'
import { useTranslation } from 'react-i18next'
import { formatNumber } from '../../utils/format'
import { useBranch } from '../../context/BranchContext'
import { getCurrency } from '../../utils/auth'
import './TaxHome.css'
import { formatShortDate } from '../../utils/dateUtils';


function TaxHome() {
    const { t } = useTranslation()
    const navigate = useNavigate()
    const { currentBranch } = useBranch()
    const currency = getCurrency()
    const [loading, setLoading] = useState(true)
    const [summary, setSummary] = useState(null)
    const [rates, setRates] = useState([])
    const [returns, setReturns] = useState([])
    const [activeTab, setActiveTab] = useState('overview')
    const [showRateModal, setShowRateModal] = useState(false)
    const [rateForm, setRateForm] = useState({ tax_code: '', tax_name: '', tax_name_en: '', rate_value: 15, description: '' })
    const [editingRate, setEditingRate] = useState(null)

    const fetchAll = async () => {
        try {
            setLoading(true)
            const params = {};
            if (currentBranch) params.branch_id = currentBranch.id;
            
            const [summaryRes, ratesRes, returnsRes] = await Promise.all([
                taxesAPI.getSummary(params),
                taxesAPI.listRates(),
                taxesAPI.listReturns(params)
            ])
            setSummary(summaryRes.data)
            setRates(ratesRes.data)
            setReturns(returnsRes.data)
        } catch (err) {
            console.error('Error fetching tax data:', err)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => { fetchAll() }, [currentBranch])

    const handleCreateRate = async () => {
        try {
            if (editingRate) {
                await taxesAPI.updateRate(editingRate.id, {
                    tax_name: rateForm.tax_name,
                    tax_name_en: rateForm.tax_name_en,
                    rate_value: parseFloat(rateForm.rate_value),
                    description: rateForm.description
                })
            } else {
                await taxesAPI.createRate(rateForm)
            }
            setShowRateModal(false)
            setEditingRate(null)
            setRateForm({ tax_code: '', tax_name: '', tax_name_en: '', rate_value: 15, description: '' })
            fetchAll()
        } catch (err) {
            alert(err.response?.data?.detail || 'خطأ')
        }
    }

    const handleDeleteRate = async (id) => {
        if (!confirm(t('taxes.confirm_delete_rate') || 'هل أنت متأكد من إيقاف هذا النوع؟')) return
        try {
            await taxesAPI.deleteRate(id)
            fetchAll()
        } catch (err) {
            alert(err.response?.data?.detail || 'خطأ')
        }
    }

    const handleEditRate = (rate) => {
        setEditingRate(rate)
        setRateForm({
            tax_code: rate.tax_code,
            tax_name: rate.tax_name,
            tax_name_en: rate.tax_name_en || '',
            rate_value: rate.rate_value,
            description: rate.description || ''
        })
        setShowRateModal(true)
    }

    const getStatusBadge = (status) => {
        const map = {
            draft: { label: t('taxes.status_draft') || 'مسودة', bg: 'rgb(254, 243, 199)', color: 'rgb(217, 119, 6)', emoji: '⏳' },
            filed: { label: t('taxes.status_filed') || 'مقدم', bg: 'rgba(59, 130, 246, 0.1)', color: 'rgb(59, 130, 246)', emoji: '📤' },
            paid: { label: t('taxes.status_paid') || 'مدفوع', bg: 'rgb(220, 252, 231)', color: 'rgb(22, 163, 74)', emoji: '✅' },
            cancelled: { label: t('taxes.status_cancelled') || 'ملغى', bg: 'rgb(254, 226, 226)', color: 'rgb(220, 38, 38)', emoji: '❌' },
            overdue: { label: t('taxes.status_overdue') || 'متأخر', bg: 'rgb(254, 226, 226)', color: 'rgb(220, 38, 38)', emoji: '⚠️' }
        }
        const s = map[status] || { label: status, bg: 'rgba(107, 114, 128, 0.082)', color: 'rgb(107, 114, 128)', emoji: '' }
        return <span style={{ background: s.bg, color: s.color, padding: '4px 12px', borderRadius: '20px', fontSize: '12px', fontWeight: '600', whiteSpace: 'nowrap' }}>
            {s.emoji} {s.label}
        </span>
    }

    if (loading && !summary) return <div className="page-center"><span className="loading"></span></div>

    return (
        <div className="workspace fade-in">
            {/* Header */}
            <div className="workspace-header">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
                    <div>
                        <h1 className="workspace-title">🧾 {t('taxes.title') || 'إدارة الضرائب'}</h1>
                        <p className="workspace-subtitle">{t('taxes.subtitle') || 'إدارة أنواع الضرائب، الإقرارات، المدفوعات والتسويات'}</p>
                    </div>
                    <div style={{ display: 'flex', gap: '8px' }}>
                        <button className="btn btn-primary" onClick={() => navigate('/taxes/returns/new')}>
                            + {t('taxes.new_return') || 'إقرار جديد'}
                        </button>
                    </div>
                </div>
            </div>

            {/* Summary Cards */}
            {summary && (
                <div className="metrics-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))' }}>
                    <div className="metric-card">
                        <div className="metric-label">{t('taxes.active_rates') || 'أنواع الضرائب النشطة'}</div>
                        <div className="metric-value">{summary.active_rates}</div>
                    </div>
                    <div className="metric-card">
                        <div className="metric-label">{t('taxes.output_vat_current') || 'ضريبة المخرجات (الشهر الحالي)'}</div>
                        <div className="metric-value text-secondary">{formatNumber(summary.current_period.output_vat)} <small>{currency}</small></div>
                    </div>
                    <div className="metric-card">
                        <div className="metric-label">{t('taxes.input_vat_current') || 'ضريبة المدخلات (الشهر الحالي)'}</div>
                        <div className="metric-value text-primary">{formatNumber(summary.current_period.input_vat)} <small>{currency}</small></div>
                    </div>
                    <div className="metric-card">
                        <div className="metric-label">{t('taxes.net_vat_current') || 'صافي الضريبة المستحقة'}</div>
                        <div className={`metric-value ${summary.current_period.net_vat >= 0 ? 'text-error' : 'text-success'}`}>
                            {formatNumber(Math.abs(summary.current_period.net_vat))} <small>{currency}</small>
                        </div>
                        <div className="metric-change">{summary.current_period.net_vat >= 0 ? (t('taxes.payable') || 'مستحق للدفع') : (t('taxes.refundable') || 'مستحق للاسترداد')}</div>
                    </div>
                    <div className="metric-card">
                        <div className="metric-label">{t('taxes.pending_returns') || 'إقرارات بانتظار الدفع'}</div>
                        <div className="metric-value text-warning">{summary.returns.filed}</div>
                        <div className="metric-change">{formatNumber(summary.returns.pending_amount)} {currency}</div>
                    </div>
                    {summary.overdue_returns > 0 && (
                        <div className="metric-card" style={{ borderColor: 'var(--error)' }}>
                            <div className="metric-label" style={{ color: 'var(--error)' }}>⚠️ {t('taxes.overdue_returns') || 'إقرارات متأخرة'}</div>
                            <div className="metric-value text-error">{summary.overdue_returns}</div>
                        </div>
                    )}
                </div>
            )}

            {/* Tabs */}
            <div className="tabs mt-4">
                {['overview', 'rates', 'returns'].map(tab => (
                    <button key={tab} className={`tab ${activeTab === tab ? 'active' : ''}`} onClick={() => setActiveTab(tab)}>
                        {tab === 'overview' && (t('taxes.tab_overview') || 'نظرة عامة')}
                        {tab === 'rates' && (t('taxes.tab_rates') || 'أنواع الضرائب')}
                        {tab === 'returns' && (t('taxes.tab_returns') || 'الإقرارات الضريبية')}
                    </button>
                ))}
            </div>

            {/* Overview Tab */}
            {activeTab === 'overview' && (
                <div className="mt-4">
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                        {/* Quick Actions */}
                        <div className="card">
                            <h3 className="section-title">{t('taxes.quick_actions') || 'إجراءات سريعة'}</h3>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '12px' }}>
                                <Link to="/taxes/returns/new" className="btn btn-outline" style={{ textAlign: 'center' }}>
                                    📝 {t('taxes.create_return') || 'إنشاء إقرار ضريبي'}
                                </Link>
                                <Link to="/accounting/vat-report" className="btn btn-outline" style={{ textAlign: 'center' }}>
                                    📊 {t('taxes.vat_report') || 'تقرير ضريبة القيمة المضافة'}
                                </Link>
                                <Link to="/accounting/tax-audit" className="btn btn-outline" style={{ textAlign: 'center' }}>
                                    🔍 {t('taxes.audit_report') || 'تقرير التدقيق الضريبي'}
                                </Link>
                                <button className="btn btn-outline" onClick={() => setActiveTab('rates')} style={{ textAlign: 'center' }}>
                                    ⚙️ {t('taxes.manage_rates') || 'إدارة أنواع الضرائب'}
                                </button>
                            </div>
                        </div>

                        {/* Recent Returns */}
                        <div className="card">
                            <h3 className="section-title">{t('taxes.recent_returns') || 'آخر الإقرارات'}</h3>
                            {returns.length === 0 ? (
                                <p className="text-muted mt-3">{t('taxes.no_returns') || 'لا توجد إقرارات بعد'}</p>
                            ) : (
                                <div className="data-table-container mt-3">
                                    <table className="data-table">
                                        <thead>
                                            <tr>
                                                <th>{t('taxes.return_number') || 'الرقم'}</th>
                                                <th>{t('taxes.period') || 'الفترة'}</th>
                                                <th style={{ textAlign: 'left' }}>{t('taxes.amount') || 'المبلغ'}</th>
                                                <th>{t('common.status') || 'الحالة'}</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {returns.slice(0, 5).map(r => (
                                                <tr key={r.id} style={{ cursor: 'pointer' }} onClick={() => navigate(`/taxes/returns/${r.id}`)}>
                                                    <td>
                                                        <span className="fw-bold" style={{ color: 'var(--primary)', fontFamily: 'monospace' }}>{r.return_number}</span>
                                                    </td>
                                                    <td style={{ whiteSpace: 'nowrap' }}>{r.tax_period}</td>
                                                    <td style={{ textAlign: 'left', fontWeight: '700', whiteSpace: 'nowrap' }}>
                                                        {formatNumber(r.total_amount)} <span className="text-muted fw-normal small">{currency}</span>
                                                    </td>
                                                    <td>{getStatusBadge(r.status)}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* Rates Tab */}
            {activeTab === 'rates' && (
                <div className="card mt-4">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                        <h3 className="section-title" style={{ margin: 0 }}>{t('taxes.tax_rates') || 'أنواع الضرائب'}</h3>
                        <button className="btn btn-primary btn-sm" onClick={() => { setEditingRate(null); setRateForm({ tax_code: '', tax_name: '', tax_name_en: '', rate_value: 15, description: '' }); setShowRateModal(true) }}>
                            + {t('taxes.add_rate') || 'إضافة نوع'}
                        </button>
                    </div>
                    <div className="data-table-container">
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th>{t('taxes.tax_code') || 'الكود'}</th>
                                    <th>{t('taxes.tax_name') || 'الاسم'}</th>
                                    <th>{t('taxes.tax_name_en') || 'الاسم (EN)'}</th>
                                    <th>{t('taxes.rate_value') || 'النسبة %'}</th>
                                    <th>{t('taxes.effective_from') || 'تاريخ البدء'}</th>
                                    <th>{t('taxes.effective_to') || 'تاريخ الانتهاء'}</th>
                                    <th>{t('common.status') || 'الحالة'}</th>
                                    <th>{t('common.actions') || 'إجراءات'}</th>
                                </tr>
                            </thead>
                            <tbody>
                                {rates.length === 0 ? (
                                    <tr><td colSpan="8" className="text-center text-muted">{t('taxes.no_rates') || 'لا توجد أنواع ضرائب'}</td></tr>
                                ) : rates.map(rate => (
                                    <tr key={rate.id}>
                                        <td>
                                            <span className="fw-bold" style={{ color: 'var(--primary)', fontFamily: 'monospace' }}>{rate.tax_code}</span>
                                        </td>
                                        <td>{rate.tax_name}</td>
                                        <td>{rate.tax_name_en || <span className="text-muted">—</span>}</td>
                                        <td style={{ fontWeight: 'bold', color: 'var(--primary)' }}>{rate.rate_value}%</td>
                                        <td style={{ whiteSpace: 'nowrap' }}>{rate.effective_from ? formatShortDate(rate.effective_from) : <span className="text-muted">—</span>}</td>
                                        <td style={{ whiteSpace: 'nowrap' }}>{rate.effective_to ? formatShortDate(rate.effective_to) : <span className="text-muted">—</span>}</td>
                                        <td>
                                            <span style={{ background: rate.is_active ? 'rgb(220, 252, 231)' : 'rgb(254, 226, 226)', color: rate.is_active ? 'rgb(22, 163, 74)' : 'rgb(220, 38, 38)', padding: '4px 12px', borderRadius: '20px', fontSize: '12px', fontWeight: '600', whiteSpace: 'nowrap' }}>
                                                {rate.is_active ? '✅ ' + (t('common.active') || 'نشط') : '❌ ' + (t('common.inactive') || 'معطل')}
                                            </span>
                                        </td>
                                        <td>
                                            <div style={{ display: 'flex', gap: '4px' }}>
                                                <button className="btn btn-sm btn-outline-primary" style={{ borderRadius: '8px', fontSize: '12px' }} onClick={() => handleEditRate(rate)}>✏️</button>
                                                {rate.is_active && <button className="btn btn-sm btn-outline-danger" style={{ borderRadius: '8px', fontSize: '12px' }} onClick={() => handleDeleteRate(rate.id)}>🗑️</button>}
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {/* Returns Tab */}
            {activeTab === 'returns' && (
                <div className="card mt-4">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                        <h3 className="section-title" style={{ margin: 0 }}>{t('taxes.tax_returns') || 'الإقرارات الضريبية'}</h3>
                        <button className="btn btn-primary btn-sm" onClick={() => navigate('/taxes/returns/new')}>
                            + {t('taxes.new_return') || 'إقرار جديد'}
                        </button>
                    </div>
                    <div className="data-table-container">
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th>{t('taxes.return_number') || 'رقم الإقرار'}</th>
                                    <th>{t('taxes.period') || 'الفترة'}</th>
                                    <th>{t('taxes.tax_type') || 'النوع'}</th>
                                    <th style={{ textAlign: 'left' }}>{t('taxes.taxable_amount') || 'المبلغ الخاضع'}</th>
                                    <th style={{ textAlign: 'left' }}>{t('taxes.tax_amount') || 'مبلغ الضريبة'}</th>
                                    <th style={{ textAlign: 'left' }}>{t('taxes.total_amount') || 'الإجمالي'}</th>
                                    <th style={{ textAlign: 'left' }}>{t('taxes.paid_amount') || 'المدفوع'}</th>
                                    <th>{t('taxes.due_date') || 'تاريخ الاستحقاق'}</th>
                                    <th>{t('common.status') || 'الحالة'}</th>
                                    <th>{t('common.actions') || 'إجراءات'}</th>
                                </tr>
                            </thead>
                            <tbody>
                                {returns.length === 0 ? (
                                    <tr><td colSpan="10" className="text-center text-muted">{t('taxes.no_returns') || 'لا توجد إقرارات'}</td></tr>
                                ) : returns.map(r => (
                                    <tr key={r.id} style={{ cursor: 'pointer' }} onClick={() => navigate(`/taxes/returns/${r.id}`)}>
                                        <td>
                                            <span className="fw-bold" style={{ color: 'var(--primary)', fontFamily: 'monospace' }}>{r.return_number}</span>
                                        </td>
                                        <td style={{ whiteSpace: 'nowrap' }}>{r.tax_period}</td>
                                        <td>
                                            <span style={{ background: 'rgba(59, 130, 246, 0.1)', color: 'rgb(59, 130, 246)', padding: '4px 10px', borderRadius: '6px', fontSize: '12px', fontWeight: '600' }}>
                                                {r.tax_type === 'vat' ? 'ض.ق.م' : r.tax_type}
                                            </span>
                                        </td>
                                        <td style={{ textAlign: 'left', whiteSpace: 'nowrap' }}>{formatNumber(r.taxable_amount)}</td>
                                        <td style={{ textAlign: 'left', whiteSpace: 'nowrap' }}>{formatNumber(r.tax_amount)}</td>
                                        <td style={{ textAlign: 'left', fontWeight: '700', whiteSpace: 'nowrap' }}>
                                            {formatNumber(r.total_amount)} <span className="text-muted fw-normal small">{currency}</span>
                                        </td>
                                        <td style={{ textAlign: 'left', whiteSpace: 'nowrap' }}>{formatNumber(r.paid_amount || 0)}</td>
                                        <td style={{ whiteSpace: 'nowrap' }}>{r.due_date ? formatShortDate(r.due_date) : <span className="text-muted">—</span>}</td>
                                        <td>{getStatusBadge(r.status)}</td>
                                        <td>
                                            <button className="btn btn-sm btn-outline-primary" style={{ borderRadius: '8px', fontSize: '12px' }} onClick={(e) => { e.stopPropagation(); navigate(`/taxes/returns/${r.id}`); }}>
                                                👁️ {t('common.view') || 'عرض'}
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {/* Tax Rate Modal */}
            {showRateModal && (
                <div className="modal-backdrop" onClick={() => setShowRateModal(false)}>
                    <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: '500px' }}>
                        <div className="modal-header">
                            <h3>{editingRate ? (t('taxes.edit_rate') || 'تعديل نوع الضريبة') : (t('taxes.add_rate') || 'إضافة نوع ضريبة')}</h3>
                            <button className="btn-close" onClick={() => setShowRateModal(false)}>✕</button>
                        </div>
                        <div className="modal-body">
                            {!editingRate && (
                                <div className="form-group">
                                    <label className="form-label">{t('taxes.tax_code') || 'كود الضريبة'} *</label>
                                    <input className="form-control" value={rateForm.tax_code}
                                        onChange={e => setRateForm({...rateForm, tax_code: e.target.value})}
                                        placeholder="مثال: VAT15, WHT5" />
                                </div>
                            )}
                            <div className="form-group">
                                <label className="form-label">{t('taxes.tax_name') || 'اسم الضريبة (عربي)'} *</label>
                                <input className="form-control" value={rateForm.tax_name}
                                    onChange={e => setRateForm({...rateForm, tax_name: e.target.value})}
                                    placeholder="مثال: ضريبة القيمة المضافة" />
                            </div>
                            <div className="form-group">
                                <label className="form-label">{t('taxes.tax_name_en') || 'اسم الضريبة (إنجليزي)'}</label>
                                <input className="form-control" value={rateForm.tax_name_en}
                                    onChange={e => setRateForm({...rateForm, tax_name_en: e.target.value})}
                                    placeholder="e.g. VAT" />
                            </div>
                            <div className="form-group">
                                <label className="form-label">{t('taxes.rate_value') || 'نسبة الضريبة (%)'} *</label>
                                <input className="form-control" type="number" min="0" max="100" step="0.01"
                                    value={rateForm.rate_value}
                                    onChange={e => setRateForm({...rateForm, rate_value: parseFloat(e.target.value) || 0})} />
                            </div>
                            <div className="form-group">
                                <label className="form-label">{t('taxes.description') || 'الوصف'}</label>
                                <textarea className="form-control" rows="2" value={rateForm.description}
                                    onChange={e => setRateForm({...rateForm, description: e.target.value})} />
                            </div>
                        </div>
                        <div className="modal-footer">
                            <button className="btn btn-secondary" onClick={() => setShowRateModal(false)}>
                                {t('common.cancel') || 'إلغاء'}
                            </button>
                            <button className="btn btn-primary" onClick={handleCreateRate}
                                disabled={!rateForm.tax_name || (!editingRate && !rateForm.tax_code)}>
                                {editingRate ? (t('common.save') || 'حفظ') : (t('common.create') || 'إنشاء')}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}

export default TaxHome
