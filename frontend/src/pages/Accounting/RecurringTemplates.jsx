import React, { useState, useEffect, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { accountingAPI } from '../../utils/api'
import { useToast } from '../../context/ToastContext'

import DateInput from '../../components/common/DateInput';
const FREQ_LABELS = {
    daily: { ar: 'يومي', en: 'Daily' },
    weekly: { ar: 'أسبوعي', en: 'Weekly' },
    monthly: { ar: 'شهري', en: 'Monthly' },
    quarterly: { ar: 'ربع سنوي', en: 'Quarterly' },
    yearly: { ar: 'سنوي', en: 'Yearly' },
}

export default function RecurringTemplates() {
    const { t, i18n } = useTranslation()
    const { showToast } = useToast()
    const isAr = i18n.language === 'ar'

    const [templates, setTemplates] = useState([])
    const [loading, setLoading] = useState(true)
    const [accounts, setAccounts] = useState([])
    const [showModal, setShowModal] = useState(false)
    const [showDetailModal, setShowDetailModal] = useState(false)
    const [editId, setEditId] = useState(null)
    const [detailData, setDetailData] = useState(null)
    const [generating, setGenerating] = useState(null)
    const [filterActive, setFilterActive] = useState('')

    const [form, setForm] = useState({
        name: '', description: '', reference: '',
        frequency: 'monthly', start_date: '', end_date: '',
        next_run_date: '', is_active: true, auto_post: false,
        currency: 'SAR', exchange_rate: 1, max_runs: '',
        lines: [
            { account_id: '', debit: '', credit: '', description: '', cost_center_id: '' },
            { account_id: '', debit: '', credit: '', description: '', cost_center_id: '' },
        ],
    })

    const fetchTemplates = useCallback(async () => {
        setLoading(true)
        try {
            const params = {}
            if (filterActive !== '') params.is_active = filterActive === 'true'
            const res = await accountingAPI.listRecurringTemplates(params)
            setTemplates(res.data)
        } catch {
            showToast(isAr ? 'خطأ في جلب القوالب' : 'Error loading templates', 'error')
        } finally {
            setLoading(false)
        }
    }, [filterActive])

    const fetchAccounts = async () => {
        try {
            const res = await accountingAPI.list()
            setAccounts(Array.isArray(res.data) ? res.data : res.data?.data || [])
        } catch { /* ignore */ }
    }

    useEffect(() => { fetchTemplates() }, [fetchTemplates])
    useEffect(() => { fetchAccounts() }, [])

    const resetForm = () => {
        setForm({
            name: '', description: '', reference: '',
            frequency: 'monthly', start_date: '', end_date: '',
            next_run_date: '', is_active: true, auto_post: false,
            currency: 'SAR', exchange_rate: 1, max_runs: '',
            lines: [
                { account_id: '', debit: '', credit: '', description: '', cost_center_id: '' },
                { account_id: '', debit: '', credit: '', description: '', cost_center_id: '' },
            ],
        })
        setEditId(null)
    }

    const openCreate = () => { resetForm(); setShowModal(true) }

    const openEdit = async (id) => {
        try {
            const res = await accountingAPI.getRecurringTemplate(id)
            const d = res.data
            setForm({
                name: d.name || '', description: d.description || '', reference: d.reference || '',
                frequency: d.frequency || 'monthly',
                start_date: d.start_date ? d.start_date.slice(0, 10) : '',
                end_date: d.end_date ? d.end_date.slice(0, 10) : '',
                next_run_date: d.next_run_date ? d.next_run_date.slice(0, 10) : '',
                is_active: d.is_active, auto_post: d.auto_post,
                currency: d.currency || 'SAR', exchange_rate: d.exchange_rate || 1,
                max_runs: d.max_runs || '',
                lines: d.lines.length ? d.lines.map(l => ({
                    account_id: l.account_id, debit: l.debit || '', credit: l.credit || '',
                    description: l.description || '', cost_center_id: l.cost_center_id || ''
                })) : [
                    { account_id: '', debit: '', credit: '', description: '', cost_center_id: '' },
                    { account_id: '', debit: '', credit: '', description: '', cost_center_id: '' },
                ],
            })
            setEditId(id)
            setShowModal(true)
        } catch {
            showToast(isAr ? 'خطأ في جلب التفاصيل' : 'Error loading details', 'error')
        }
    }

    const openDetail = async (id) => {
        try {
            const res = await accountingAPI.getRecurringTemplate(id)
            setDetailData(res.data)
            setShowDetailModal(true)
        } catch {
            showToast(isAr ? 'خطأ' : 'Error', 'error')
        }
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        const payload = {
            ...form,
            max_runs: form.max_runs ? parseInt(form.max_runs) : null,
            end_date: form.end_date || null,
            next_run_date: form.next_run_date || form.start_date,
            lines: form.lines.filter(l => l.account_id).map(l => ({
                account_id: parseInt(l.account_id),
                debit: parseFloat(l.debit) || 0,
                credit: parseFloat(l.credit) || 0,
                description: l.description,
                cost_center_id: l.cost_center_id ? parseInt(l.cost_center_id) : null,
            })),
        }

        try {
            if (editId) {
                await accountingAPI.updateRecurringTemplate(editId, payload)
                showToast(isAr ? 'تم تعديل القالب' : 'Template updated', 'success')
            } else {
                await accountingAPI.createRecurringTemplate(payload)
                showToast(isAr ? 'تم إنشاء القالب' : 'Template created', 'success')
            }
            setShowModal(false)
            resetForm()
            fetchTemplates()
        } catch (err) {
            showToast(err.response?.data?.detail || 'Error', 'error')
        }
    }

    const handleDelete = async (id, name) => {
        if (!confirm(isAr ? `حذف القالب "${name}"؟` : `Delete template "${name}"?`)) return
        try {
            await accountingAPI.deleteRecurringTemplate(id)
            showToast(isAr ? 'تم الحذف' : 'Deleted', 'success')
            fetchTemplates()
        } catch (err) {
            showToast(err.response?.data?.detail || 'Error', 'error')
        }
    }

    const handleGenerate = async (id) => {
        setGenerating(id)
        try {
            const res = await accountingAPI.generateFromTemplate(id)
            showToast(
                isAr ? `تم توليد القيد #${res.data.entry_id}` : `Generated entry #${res.data.entry_id}`,
                'success'
            )
            fetchTemplates()
        } catch (err) {
            showToast(err.response?.data?.detail || 'Error', 'error')
        } finally {
            setGenerating(null)
        }
    }

    const handleGenerateAll = async () => {
        try {
            const res = await accountingAPI.generateDueTemplates()
            const d = res.data
            showToast(
                isAr
                    ? `تم توليد ${d.generated_count} قيد${d.error_count ? ` (${d.error_count} أخطاء)` : ''}`
                    : `Generated ${d.generated_count} entries${d.error_count ? ` (${d.error_count} errors)` : ''}`,
                d.error_count ? 'warning' : 'success'
            )
            fetchTemplates()
        } catch (err) {
            showToast(err.response?.data?.detail || 'Error', 'error')
        }
    }

    const addLine = () => {
        setForm(f => ({
            ...f,
            lines: [...f.lines, { account_id: '', debit: '', credit: '', description: '', cost_center_id: '' }]
        }))
    }

    const removeLine = (idx) => {
        if (form.lines.length <= 2) return
        setForm(f => ({ ...f, lines: f.lines.filter((_, i) => i !== idx) }))
    }

    const updateLine = (idx, field, value) => {
        setForm(f => {
            const lines = [...f.lines]
            lines[idx] = { ...lines[idx], [field]: value }
            return { ...f, lines }
        })
    }

    const totalDebit = form.lines.reduce((s, l) => s + (parseFloat(l.debit) || 0), 0)
    const totalCredit = form.lines.reduce((s, l) => s + (parseFloat(l.credit) || 0), 0)
    const isBalanced = Math.abs(totalDebit - totalCredit) < 0.01

    const freqLabel = (f) => FREQ_LABELS[f]?.[isAr ? 'ar' : 'en'] || f

    return (
        <div className="module-container" dir={isAr ? 'rtl' : 'ltr'}>
            <div className="module-header">
                <div className="d-flex justify-content-between align-items-center flex-wrap gap-2">
                    <h2>🔄 {isAr ? 'القيود المتكررة' : 'Recurring Journal Entries'}</h2>
                    <div className="d-flex gap-2">
                        <select className="form-input" style={{ width: 'auto' }}
                            value={filterActive} onChange={e => setFilterActive(e.target.value)}>
                            <option value="">{isAr ? 'الكل' : 'All'}</option>
                            <option value="true">{isAr ? 'نشط' : 'Active'}</option>
                            <option value="false">{isAr ? 'متوقف' : 'Inactive'}</option>
                        </select>
                        <button className="btn btn-outline-primary btn-sm" onClick={handleGenerateAll}>
                            ⚡ {isAr ? 'توليد المستحقة' : 'Generate Due'}
                        </button>
                        <button className="btn btn-primary btn-sm" onClick={openCreate}>
                            + {isAr ? 'قالب جديد' : 'New Template'}
                        </button>
                    </div>
                </div>
            </div>

            {loading ? (
                <div className="text-center p-5"><div className="spinner-border" /></div>
            ) : templates.length === 0 ? (
                <div className="text-center text-muted p-5">
                    {isAr ? 'لا توجد قوالب متكررة' : 'No recurring templates'}
                </div>
            ) : (
                <div className="data-table-container">
                    <table className="data-table table-hover">
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>{isAr ? 'الاسم' : 'Name'}</th>
                                <th>{isAr ? 'التكرار' : 'Frequency'}</th>
                                <th>{isAr ? 'التنفيذ التالي' : 'Next Run'}</th>
                                <th>{isAr ? 'آخر تنفيذ' : 'Last Run'}</th>
                                <th>{isAr ? 'التنفيذ' : 'Runs'}</th>
                                <th>{isAr ? 'ترحيل تلقائي' : 'Auto Post'}</th>
                                <th>{isAr ? 'الحالة' : 'Status'}</th>
                                <th>{isAr ? 'إجراءات' : 'Actions'}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {templates.map((t, idx) => (
                                <tr key={t.id}>
                                    <td>{idx + 1}</td>
                                    <td>
                                        <a href="#" onClick={(e) => { e.preventDefault(); openDetail(t.id) }}
                                            className="text-primary text-decoration-none fw-bold">
                                            {t.name}
                                        </a>
                                        {t.reference && <div className="text-muted small">{t.reference}</div>}
                                    </td>
                                    <td><span className="badge bg-info">{freqLabel(t.frequency)}</span></td>
                                    <td>{t.next_run_date || '-'}</td>
                                    <td>{t.last_run_date || '-'}</td>
                                    <td>
                                        {t.run_count || 0}
                                        {t.max_runs && <span className="text-muted">/{t.max_runs}</span>}
                                    </td>
                                    <td>{t.auto_post ? '✅' : '❌'}</td>
                                    <td>
                                        <span className={`badge ${t.is_active ? 'bg-success' : 'bg-secondary'}`}>
                                            {t.is_active ? (isAr ? 'نشط' : 'Active') : (isAr ? 'متوقف' : 'Inactive')}
                                        </span>
                                    </td>
                                    <td>
                                        <div className="btn-group btn-group-sm">
                                            <button className="btn btn-outline-success" title={isAr ? 'توليد الآن' : 'Generate Now'}
                                                disabled={generating === t.id} onClick={() => handleGenerate(t.id)}>
                                                {generating === t.id ? '⏳' : '⚡'}
                                            </button>
                                            <button className="btn btn-outline-primary" onClick={() => openEdit(t.id)}>✏️</button>
                                            <button className="btn btn-outline-danger" onClick={() => handleDelete(t.id, t.name)}>🗑</button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {/* Create / Edit Modal */}
            {showModal && (
                <div className="modal d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }} onClick={() => setShowModal(false)}>
                    <div className="modal-dialog modal-xl" onClick={e => e.stopPropagation()}>
                        <form className="modal-content" onSubmit={handleSubmit}>
                            <div className="modal-header">
                                <h5 className="modal-title">
                                    {editId
                                        ? (isAr ? 'تعديل قالب متكرر' : 'Edit Recurring Template')
                                        : (isAr ? 'قالب متكرر جديد' : 'New Recurring Template')}
                                </h5>
                                <button type="button" className="btn-close" onClick={() => setShowModal(false)} />
                            </div>
                            <div className="modal-body">
                                <div className="row g-3 mb-3">
                                    <div className="col-md-4">
                                        <label className="form-label">{isAr ? 'اسم القالب *' : 'Template Name *'}</label>
                                        <input className="form-control" required value={form.name}
                                            onChange={e => setForm(f => ({ ...f, name: e.target.value }))} />
                                    </div>
                                    <div className="col-md-4">
                                        <label className="form-label">{isAr ? 'المرجع' : 'Reference'}</label>
                                        <input className="form-control" value={form.reference}
                                            onChange={e => setForm(f => ({ ...f, reference: e.target.value }))} />
                                    </div>
                                    <div className="col-md-4">
                                        <label className="form-label">{isAr ? 'التكرار *' : 'Frequency *'}</label>
                                        <select className="form-input" required value={form.frequency}
                                            onChange={e => setForm(f => ({ ...f, frequency: e.target.value }))}>
                                            {Object.entries(FREQ_LABELS).map(([k, v]) => (
                                                <option key={k} value={k}>{v[isAr ? 'ar' : 'en']}</option>
                                            ))}
                                        </select>
                                    </div>
                                </div>
                                <div className="row g-3 mb-3">
                                    <div className="col-md-3">
                                        <label className="form-label">{isAr ? 'تاريخ البداية *' : 'Start Date *'}</label>
                                        <DateInput className="form-control" required value={form.start_date}
                                            onChange={e => setForm(f => ({
                                                ...f, start_date: e.target.value,
                                                next_run_date: f.next_run_date || e.target.value
                                            }))} />
                                    </div>
                                    <div className="col-md-3">
                                        <label className="form-label">{isAr ? 'تاريخ النهاية' : 'End Date'}</label>
                                        <DateInput className="form-control" value={form.end_date}
                                            onChange={e => setForm(f => ({ ...f, end_date: e.target.value }))} />
                                    </div>
                                    <div className="col-md-3">
                                        <label className="form-label">{isAr ? 'التنفيذ التالي' : 'Next Run Date'}</label>
                                        <DateInput className="form-control" value={form.next_run_date}
                                            onChange={e => setForm(f => ({ ...f, next_run_date: e.target.value }))} />
                                    </div>
                                    <div className="col-md-3">
                                        <label className="form-label">{isAr ? 'الحد الأقصى للتنفيذ' : 'Max Runs'}</label>
                                        <input type="number" className="form-control" min="1" value={form.max_runs}
                                            placeholder={isAr ? 'بلا حد' : 'Unlimited'}
                                            onChange={e => setForm(f => ({ ...f, max_runs: e.target.value }))} />
                                    </div>
                                </div>
                                <div className="row g-3 mb-3">
                                    <div className="col-md-8">
                                        <label className="form-label">{isAr ? 'الوصف' : 'Description'}</label>
                                        <input className="form-control" value={form.description}
                                            onChange={e => setForm(f => ({ ...f, description: e.target.value }))} />
                                    </div>
                                    <div className="col-md-2">
                                        <label className="form-label d-block">&nbsp;</label>
                                        <div className="form-check">
                                            <input type="checkbox" className="form-check-input" id="is_active"
                                                checked={form.is_active}
                                                onChange={e => setForm(f => ({ ...f, is_active: e.target.checked }))} />
                                            <label className="form-check-label" htmlFor="is_active">
                                                {isAr ? 'نشط' : 'Active'}
                                            </label>
                                        </div>
                                    </div>
                                    <div className="col-md-2">
                                        <label className="form-label d-block">&nbsp;</label>
                                        <div className="form-check">
                                            <input type="checkbox" className="form-check-input" id="auto_post"
                                                checked={form.auto_post}
                                                onChange={e => setForm(f => ({ ...f, auto_post: e.target.checked }))} />
                                            <label className="form-check-label" htmlFor="auto_post">
                                                {isAr ? 'ترحيل تلقائي' : 'Auto Post'}
                                            </label>
                                        </div>
                                    </div>
                                </div>

                                {/* Lines */}
                                <h6 className="mt-3 mb-2">{isAr ? 'بنود القيد' : 'Journal Lines'}</h6>
                                <div className="data-table-container">
                                    <table className="data-table table-bordered">
                                        <thead className="table-light">
                                            <tr>
                                                <th style={{ width: '35%' }}>{isAr ? 'الحساب' : 'Account'}</th>
                                                <th style={{ width: '15%' }}>{isAr ? 'مدين' : 'Debit'}</th>
                                                <th style={{ width: '15%' }}>{isAr ? 'دائن' : 'Credit'}</th>
                                                <th style={{ width: '25%' }}>{isAr ? 'البيان' : 'Description'}</th>
                                                <th style={{ width: '10%' }}></th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {form.lines.map((line, idx) => (
                                                <tr key={idx}>
                                                    <td>
                                                        <select className="form-input" required
                                                            value={line.account_id}
                                                            onChange={e => updateLine(idx, 'account_id', e.target.value)}>
                                                            <option value="">{isAr ? '-- اختر --' : '-- Select --'}</option>
                                                            {accounts.map(a => (
                                                                <option key={a.id} value={a.id}>{a.account_number} - {a.name}</option>
                                                            ))}
                                                        </select>
                                                    </td>
                                                    <td>
                                                        <input type="number" className="form-control form-control-sm"
                                                            step="0.01" min="0" value={line.debit}
                                                            onChange={e => updateLine(idx, 'debit', e.target.value)} />
                                                    </td>
                                                    <td>
                                                        <input type="number" className="form-control form-control-sm"
                                                            step="0.01" min="0" value={line.credit}
                                                            onChange={e => updateLine(idx, 'credit', e.target.value)} />
                                                    </td>
                                                    <td>
                                                        <input className="form-control form-control-sm" value={line.description}
                                                            onChange={e => updateLine(idx, 'description', e.target.value)} />
                                                    </td>
                                                    <td className="text-center">
                                                        <button type="button" className="btn btn-sm btn-outline-danger"
                                                            disabled={form.lines.length <= 2}
                                                            onClick={() => removeLine(idx)}>✕</button>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                        <tfoot>
                                            <tr className="fw-bold">
                                                <td className="text-end">{isAr ? 'الإجمالي' : 'Total'}</td>
                                                <td className={!isBalanced ? 'text-danger' : ''}>{totalDebit.toFixed(2)}</td>
                                                <td className={!isBalanced ? 'text-danger' : ''}>{totalCredit.toFixed(2)}</td>
                                                <td colSpan="2">
                                                    <button type="button" className="btn btn-sm btn-outline-primary" onClick={addLine}>
                                                        + {isAr ? 'سطر' : 'Line'}
                                                    </button>
                                                </td>
                                            </tr>
                                        </tfoot>
                                    </table>
                                </div>
                                {!isBalanced && (
                                    <div className="alert alert-warning py-1 small">
                                        ⚠️ {isAr ? 'القيد غير متوازن' : 'Entry is not balanced'} —
                                        {isAr ? ' الفرق: ' : ' Difference: '}{Math.abs(totalDebit - totalCredit).toFixed(2)}
                                    </div>
                                )}
                            </div>
                            <div className="modal-footer">
                                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>
                                    {isAr ? 'إلغاء' : 'Cancel'}
                                </button>
                                <button type="submit" className="btn btn-primary" disabled={!isBalanced || totalDebit === 0}>
                                    {editId ? (isAr ? 'تحديث' : 'Update') : (isAr ? 'إنشاء' : 'Create')}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Detail Modal */}
            {showDetailModal && detailData && (
                <div className="modal d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }} onClick={() => setShowDetailModal(false)}>
                    <div className="modal-dialog modal-lg" onClick={e => e.stopPropagation()}>
                        <div className="modal-content">
                            <div className="modal-header">
                                <h5 className="modal-title">🔄 {detailData.name}</h5>
                                <button type="button" className="btn-close" onClick={() => setShowDetailModal(false)} />
                            </div>
                            <div className="modal-body">
                                <div className="row mb-3">
                                    <div className="col-md-4">
                                        <strong>{isAr ? 'التكرار:' : 'Frequency:'}</strong>{' '}
                                        <span className="badge bg-info">{freqLabel(detailData.frequency)}</span>
                                    </div>
                                    <div className="col-md-4">
                                        <strong>{isAr ? 'الحالة:' : 'Status:'}</strong>{' '}
                                        <span className={`badge ${detailData.is_active ? 'bg-success' : 'bg-secondary'}`}>
                                            {detailData.is_active ? (isAr ? 'نشط' : 'Active') : (isAr ? 'متوقف' : 'Inactive')}
                                        </span>
                                    </div>
                                    <div className="col-md-4">
                                        <strong>{isAr ? 'ترحيل تلقائي:' : 'Auto Post:'}</strong>{' '}
                                        {detailData.auto_post ? '✅' : '❌'}
                                    </div>
                                </div>
                                <div className="row mb-3">
                                    <div className="col-md-3"><strong>{isAr ? 'البداية:' : 'Start:'}</strong> {detailData.start_date}</div>
                                    <div className="col-md-3"><strong>{isAr ? 'النهاية:' : 'End:'}</strong> {detailData.end_date || '-'}</div>
                                    <div className="col-md-3"><strong>{isAr ? 'التالي:' : 'Next:'}</strong> {detailData.next_run_date}</div>
                                    <div className="col-md-3"><strong>{isAr ? 'آخر تنفيذ:' : 'Last:'}</strong> {detailData.last_run_date || '-'}</div>
                                </div>
                                <div className="row mb-3">
                                    <div className="col-md-4">
                                        <strong>{isAr ? 'التنفيذ:' : 'Runs:'}</strong>{' '}
                                        {detailData.run_count || 0}{detailData.max_runs ? `/${detailData.max_runs}` : ''}
                                    </div>
                                    {detailData.reference && (
                                        <div className="col-md-4"><strong>{isAr ? 'المرجع:' : 'Ref:'}</strong> {detailData.reference}</div>
                                    )}
                                    {detailData.description && (
                                        <div className="col-md-4"><strong>{isAr ? 'الوصف:' : 'Desc:'}</strong> {detailData.description}</div>
                                    )}
                                </div>

                                <h6>{isAr ? 'البنود' : 'Lines'}</h6>
                                <table className="data-table table-bordered">
                                    <thead className="table-light">
                                        <tr>
                                            <th>{isAr ? 'الحساب' : 'Account'}</th>
                                            <th>{isAr ? 'مدين' : 'Debit'}</th>
                                            <th>{isAr ? 'دائن' : 'Credit'}</th>
                                            <th>{isAr ? 'البيان' : 'Description'}</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {detailData.lines.map((l, i) => (
                                            <tr key={i}>
                                                <td>{l.account_code || l.account_number} - {l.account_name}</td>
                                                <td>{parseFloat(l.debit || 0).toFixed(2)}</td>
                                                <td>{parseFloat(l.credit || 0).toFixed(2)}</td>
                                                <td>{l.description || '-'}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                    <tfoot>
                                        <tr className="fw-bold">
                                            <td>{isAr ? 'الإجمالي' : 'Total'}</td>
                                            <td>{detailData.lines.reduce((s, l) => s + parseFloat(l.debit || 0), 0).toFixed(2)}</td>
                                            <td>{detailData.lines.reduce((s, l) => s + parseFloat(l.credit || 0), 0).toFixed(2)}</td>
                                            <td></td>
                                        </tr>
                                    </tfoot>
                                </table>
                            </div>
                            <div className="modal-footer">
                                <button className="btn btn-outline-success btn-sm" onClick={() => { setShowDetailModal(false); handleGenerate(detailData.id) }}>
                                    ⚡ {isAr ? 'توليد الآن' : 'Generate Now'}
                                </button>
                                <button className="btn btn-outline-primary btn-sm" onClick={() => { setShowDetailModal(false); openEdit(detailData.id) }}>
                                    ✏️ {isAr ? 'تعديل' : 'Edit'}
                                </button>
                                <button className="btn btn-secondary btn-sm" onClick={() => setShowDetailModal(false)}>
                                    {isAr ? 'إغلاق' : 'Close'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
