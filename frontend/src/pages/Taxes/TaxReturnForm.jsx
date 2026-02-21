import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { taxesAPI } from '../../utils/api'
import { useTranslation } from 'react-i18next'
import { getCurrency } from '../../utils/auth'
import { useBranch } from '../../context/BranchContext'
import CustomDatePicker from '../../components/common/CustomDatePicker'

function TaxReturnForm() {
    const { t } = useTranslation()
    const navigate = useNavigate()
    const { currentBranch } = useBranch()
    const currency = getCurrency()
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const [success, setSuccess] = useState(null)

    const now = new Date()
    const currentYear = now.getFullYear()
    const currentMonth = now.getMonth() + 1

    const [form, setForm] = useState({
        period_type: 'monthly', // monthly or quarterly
        year: currentYear,
        month: currentMonth,
        quarter: Math.ceil(currentMonth / 3),
        tax_type: 'vat',
        due_date: '',
        notes: ''
    })

    const getPeriodString = () => {
        if (form.period_type === 'quarterly') {
            return `${form.year}-Q${form.quarter}`
        }
        return `${form.year}-${String(form.month).padStart(2, '0')}`
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        setError(null)
        setSuccess(null)
        setLoading(true)

        try {
            const res = await taxesAPI.createReturn({
                tax_period: getPeriodString(),
                tax_type: form.tax_type,
                due_date: form.due_date || null,
                notes: form.notes || null,
                branch_id: currentBranch?.id || null
            })
            setSuccess(res.data)
        } catch (err) {
            setError(err.response?.data?.detail || t('errors.generic'))
        } finally {
            setLoading(false)
        }
    }

    const months = [
        { value: 1, label: t('months.jan') },
        { value: 2, label: t('months.feb') },
        { value: 3, label: t('months.mar') },
        { value: 4, label: t('months.apr') },
        { value: 5, label: t('months.may') },
        { value: 6, label: t('months.jun') },
        { value: 7, label: t('months.jul') },
        { value: 8, label: t('months.aug') },
        { value: 9, label: t('months.sep') },
        { value: 10, label: t('months.oct') },
        { value: 11, label: t('months.nov') },
        { value: 12, label: t('months.dec') }
    ]

    const quarters = [
        { value: 1, label: t('taxes.q1') },
        { value: 2, label: t('taxes.q2') },
        { value: 3, label: t('taxes.q3') },
        { value: 4, label: t('taxes.q4') }
    ]

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <div>
                    <h1 className="workspace-title">📝 {t('taxes.new_return_title')}</h1>
                    <p className="workspace-subtitle">{t('taxes.new_return_subtitle')}</p>
                </div>
            </div>

            {error && <div className="alert alert-danger mt-4">{error}</div>}

            {success ? (
                <div className="card mt-4">
                    <div style={{ textAlign: 'center', padding: '40px 20px' }}>
                        <div style={{ fontSize: '48px', marginBottom: '16px' }}>✅</div>
                        <h2 style={{ color: 'var(--success)' }}>{t('taxes.return_created')}</h2>
                        <p style={{ fontFamily: 'monospace', fontSize: '18px', margin: '8px 0' }}>{success.return_number}</p>

                        {success.summary && (
                            <div className="metrics-grid mt-4" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', maxWidth: '800px', margin: '24px auto' }}>
                                <div className="metric-card">
                                    <div className="metric-label">{t('taxes.output_vat')}</div>
                                    <div className="metric-value text-secondary">{(success.summary.output_vat || 0).toLocaleString('en', { minimumFractionDigits: 2 })}</div>
                                </div>
                                <div className="metric-card">
                                    <div className="metric-label">{t('taxes.input_vat')}</div>
                                    <div className="metric-value text-primary">{(success.summary.input_vat || 0).toLocaleString('en', { minimumFractionDigits: 2 })}</div>
                                </div>
                                <div className="metric-card">
                                    <div className="metric-label">{t('taxes.net_payable')}</div>
                                    <div className={`metric-value ${success.summary.net_payable >= 0 ? 'text-error' : 'text-success'}`}>
                                        {Math.abs(success.summary.net_payable || 0).toLocaleString('en', { minimumFractionDigits: 2 })} {currency}
                                    </div>
                                    <div className="metric-change">
                                        {success.summary.net_payable >= 0 ? (t('taxes.payable')) : (t('taxes.refundable'))}
                                    </div>
                                </div>
                            </div>
                        )}

                        <div style={{ display: 'flex', gap: '12px', justifyContent: 'center', marginTop: '24px' }}>
                            <button className="btn btn-primary" onClick={() => navigate(`/taxes/returns/${success.id}`)}>
                                👁️ {t('taxes.view_return')}
                            </button>
                            <button className="btn btn-secondary" onClick={() => navigate('/taxes')}>
                                🏠 {t('taxes.back_to_taxes')}
                            </button>
                        </div>
                    </div>
                </div>
            ) : (
                <form onSubmit={handleSubmit}>
                    {/* Period Settings Card */}
                    <div className="card border-0 shadow-sm mt-4" style={{ borderRadius: '12px' }}>
                        <div className="card-body p-4">
                            <div className="d-flex align-items-center gap-2 mb-3">
                                <div style={{ background: '#eff6ff', width: '32px', height: '32px', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                    <span style={{ fontSize: '18px' }}>📅</span>
                                </div>
                                <h5 className="mb-0 fw-semibold">{t('taxes.period_settings')}</h5>
                            </div>

                            <div className="form-row">
                                <div className="form-group" style={{ flex: 1 }}>
                                    <label className="form-label">{t('taxes.period_type')} *</label>
                                    <select className="form-input" value={form.period_type}
                                        onChange={e => setForm({...form, period_type: e.target.value})}>
                                        <option value="monthly">{t('taxes.monthly')}</option>
                                        <option value="quarterly">{t('taxes.quarterly')}</option>
                                    </select>
                                </div>

                                <div className="form-group" style={{ flex: 1 }}>
                                    <label className="form-label">{t('taxes.year')} *</label>
                                    <select className="form-input" value={form.year}
                                        onChange={e => setForm({...form, year: parseInt(e.target.value)})}>
                                        {[currentYear - 2, currentYear - 1, currentYear, currentYear + 1].map(y => (
                                            <option key={y} value={y}>{y}</option>
                                        ))}
                                    </select>
                                </div>
                            </div>

                            <div className="form-row">
                                {form.period_type === 'monthly' ? (
                                    <div className="form-group" style={{ flex: 1 }}>
                                        <label className="form-label">{t('taxes.month')} *</label>
                                        <select className="form-input" value={form.month}
                                            onChange={e => setForm({...form, month: parseInt(e.target.value)})}>
                                            {months.map(m => <option key={m.value} value={m.value}>{m.label}</option>)}
                                        </select>
                                    </div>
                                ) : (
                                    <div className="form-group" style={{ flex: 1 }}>
                                        <label className="form-label">{t('taxes.quarter')} *</label>
                                        <select className="form-input" value={form.quarter}
                                            onChange={e => setForm({...form, quarter: parseInt(e.target.value)})}>
                                            {quarters.map(q => <option key={q.value} value={q.value}>{q.label}</option>)}
                                        </select>
                                    </div>
                                )}

                                <div className="form-group" style={{ flex: 1 }}>
                                    <label className="form-label">{t('taxes.tax_type')}</label>
                                    <select className="form-input" value={form.tax_type}
                                        onChange={e => setForm({...form, tax_type: e.target.value})}>
                                        <option value="vat">{t('taxes.vat')}</option>
                                        <option value="income">{t('taxes.income_tax')}</option>
                                        <option value="withholding">{t('taxes.withholding')}</option>
                                    </select>
                                </div>
                            </div>

                            <div className="form-row">
                                <div className="form-group" style={{ flex: 1 }}>
                                    <CustomDatePicker
                                        label={t('taxes.due_date')}
                                        selected={form.due_date}
                                        onChange={(val) => setForm({...form, due_date: val})}
                                        placeholder="YYYY/MM/DD"
                                    />
                                </div>
                                <div className="form-group" style={{ flex: 1 }}>
                                    <label className="form-label">{t('taxes.selected_period')}</label>
                                    <input className="form-input" value={getPeriodString()} readOnly
                                        style={{ fontFamily: 'monospace', fontWeight: 'bold', background: 'var(--bg-secondary)' }} />
                                </div>
                            </div>

                            <div className="form-group">
                                <label className="form-label">{t('taxes.notes')}</label>
                                <textarea className="form-input" rows="3" value={form.notes}
                                    onChange={e => setForm({...form, notes: e.target.value})}
                                    placeholder={t('taxes.notes_placeholder')} />
                            </div>

                            <div className="alert alert-info mt-3">
                                ℹ️ {t('taxes.auto_calc_note')}
                            </div>

                            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end', marginTop: '16px' }}>
                                <button type="button" className="btn btn-outline-secondary" onClick={() => navigate('/taxes')}>
                                    {t('common.cancel')}
                                </button>
                                <button type="submit" className="btn btn-primary" disabled={loading}>
                                    {loading ? (t('common.creating')) : (t('taxes.create_return'))}
                                </button>
                            </div>
                        </div>
                    </div>
                </form>
            )}
        </div>
    )
}

export default TaxReturnForm
