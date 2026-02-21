import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { inventoryAPI } from '../../utils/api'
import { useBranch } from '../../context/BranchContext'

function QualityInspections() {
    const { t } = useTranslation()
    const { currentBranch } = useBranch()
    const [inspections, setInspections] = useState([])
    const [loading, setLoading] = useState(true)
    const [statusFilter, setStatusFilter] = useState('')
    const [typeFilter, setTypeFilter] = useState('')
    const [products, setProducts] = useState([])
    const [warehouses, setWarehouses] = useState([])
    const [batches, setBatches] = useState([])
    const [showCreateModal, setShowCreateModal] = useState(false)
    const [showCompleteModal, setShowCompleteModal] = useState(false)
    const [selectedInspection, setSelectedInspection] = useState(null)
    const [total, setTotal] = useState(0)

    const [form, setForm] = useState({
        product_id: '',
        warehouse_id: '',
        batch_id: '',
        inspection_type: 'incoming',
        sample_size: '',
        notes: '',
        criteria: [{ criteria_name: '', expected_value: '', min_value: '', max_value: '' }]
    })

    const [completeForm, setCompleteForm] = useState({
        result: 'passed',
        defect_quantity: 0,
        inspector_notes: ''
    })

    const [saving, setSaving] = useState(false)
    const [error, setError] = useState(null)

    useEffect(() => {
        fetchInspections()
        fetchProducts()
        fetchWarehouses()
    }, [currentBranch, statusFilter, typeFilter])

    const fetchInspections = async () => {
        try {
            setLoading(true)
            const params = { limit: 100 }
            if (statusFilter) params.status = statusFilter
            if (typeFilter) params.inspection_type = typeFilter
            const res = await inventoryAPI.listQualityInspections(params)
            setInspections(res.data.items || [])
            setTotal(res.data.total || 0)
        } catch (err) {
            console.error(err)
        } finally {
            setLoading(false)
        }
    }

    const fetchProducts = async () => {
        try {
            const res = await inventoryAPI.listProducts({ limit: 500, branch_id: currentBranch?.id })
            setProducts(res.data || [])
        } catch (err) { console.error(err) }
    }

    const fetchWarehouses = async () => {
        try {
            const res = await inventoryAPI.listWarehouses({ branch_id: currentBranch?.id })
            setWarehouses(res.data || [])
        } catch (err) { console.error(err) }
    }

    const addCriteria = () => {
        setForm({ ...form, criteria: [...form.criteria, { criteria_name: '', expected_value: '', min_value: '', max_value: '' }] })
    }

    const removeCriteria = (index) => {
        const updated = form.criteria.filter((_, i) => i !== index)
        setForm({ ...form, criteria: updated })
    }

    const updateCriteria = (index, field, value) => {
        const updated = [...form.criteria]
        updated[index][field] = value
        setForm({ ...form, criteria: updated })
    }

    const handleCreate = async (e) => {
        e.preventDefault()
        setSaving(true)
        setError(null)
        try {
            await inventoryAPI.createQualityInspection({
                product_id: parseInt(form.product_id),
                warehouse_id: parseInt(form.warehouse_id),
                batch_id: form.batch_id ? parseInt(form.batch_id) : null,
                inspection_type: form.inspection_type,
                sample_size: form.sample_size ? parseInt(form.sample_size) : null,
                notes: form.notes || null,
                criteria: form.criteria.filter(c => c.criteria_name).map(c => ({
                    ...c,
                    min_value: c.min_value ? parseFloat(c.min_value) : null,
                    max_value: c.max_value ? parseFloat(c.max_value) : null
                }))
            })
            setShowCreateModal(false)
            setForm({
                product_id: '', warehouse_id: '', batch_id: '', inspection_type: 'incoming',
                sample_size: '', notes: '',
                criteria: [{ criteria_name: '', expected_value: '', min_value: '', max_value: '' }]
            })
            fetchInspections()
        } catch (err) {
            setError(err.response?.data?.detail || 'حدث خطأ')
        } finally {
            setSaving(false)
        }
    }

    const openCompleteModal = (inspection) => {
        setSelectedInspection(inspection)
        setCompleteForm({ result: 'passed', defect_quantity: 0, inspector_notes: '' })
        setShowCompleteModal(true)
    }

    const handleComplete = async (e) => {
        e.preventDefault()
        setSaving(true)
        setError(null)
        try {
            await inventoryAPI.completeQualityInspection(selectedInspection.id, {
                result: completeForm.result,
                defect_quantity: parseInt(completeForm.defect_quantity || 0),
                inspector_notes: completeForm.inspector_notes || null
            })
            setShowCompleteModal(false)
            setSelectedInspection(null)
            fetchInspections()
        } catch (err) {
            setError(err.response?.data?.detail || 'حدث خطأ')
        } finally {
            setSaving(false)
        }
    }

    const getStatusBadge = (status) => {
        const map = {
            pending: { label: 'قيد الانتظار', cls: 'badge-warning' },
            in_progress: { label: 'جاري الفحص', cls: 'badge-primary' },
            completed: { label: 'مكتمل', cls: 'badge-success' },
            failed: { label: 'فشل', cls: 'badge-danger' }
        }
        const s = map[status] || { label: status, cls: 'badge-secondary' }
        return <span className={`badge ${s.cls}`}>{s.label}</span>
    }

    const getResultBadge = (result) => {
        if (!result) return '-'
        const map = {
            passed: { label: '✅ ناجح', cls: 'badge-success' },
            failed: { label: '❌ فاشل', cls: 'badge-danger' },
            conditional: { label: '⚠️ مشروط', cls: 'badge-warning' }
        }
        const s = map[result] || { label: result, cls: 'badge-secondary' }
        return <span className={`badge ${s.cls}`}>{s.label}</span>
    }

    const getTypeName = (type) => {
        const map = { incoming: 'وارد', outgoing: 'صادر', in_process: 'أثناء التصنيع', random: 'عشوائي' }
        return map[type] || type
    }

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <div>
                    <h1 className="workspace-title">🔬 {t('stock.quality.title', 'فحوصات الجودة')}</h1>
                    <p className="workspace-subtitle">{t('stock.quality.subtitle', 'إدارة فحوصات جودة المنتجات والدفعات')}</p>
                </div>
                <button className="btn btn-primary" onClick={() => setShowCreateModal(true)}>
                    + إنشاء فحص جديد
                </button>
            </div>

            {/* Stats */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '24px' }}>
                <div className="card p-3 text-center">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mx-auto mb-2 text-primary">
                        <path d="M9 11a3 3 0 1 0 6 0a3 3 0 0 0 -6 0"/>
                        <path d="M17.8 20a9 9 0 1 0 -11.6 0"/>
                    </svg>
                    <div className="small text-muted">إجمالي الفحوصات</div>
                    <div className="fw-bold fs-4">{total}</div>
                </div>
                <div className="card p-3 text-center">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mx-auto mb-2 text-warning">
                        <circle cx="12" cy="12" r="10"/>
                        <path d="M12 6v6l4 2"/>
                    </svg>
                    <div className="small text-muted">قيد الانتظار</div>
                    <div className="fw-bold fs-4 text-warning">
                        {inspections.filter(i => i.status === 'pending').length}
                    </div>
                </div>
                <div className="card p-3 text-center">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mx-auto mb-2 text-success">
                        <path d="M21.801 10A10 10 0 1 1 17 3.335"/>
                        <path d="m9 11 3 3L22 4"/>
                    </svg>
                    <div className="small text-muted">ناجحة</div>
                    <div className="fw-bold fs-4 text-success">
                        {inspections.filter(i => i.result === 'passed').length}
                    </div>
                </div>
                <div className="card p-3 text-center">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mx-auto mb-2 text-danger">
                        <circle cx="12" cy="12" r="10"/>
                        <path d="m15 9-6 6"/>
                        <path d="m9 9 6 6"/>
                    </svg>
                    <div className="small text-muted">فاشلة</div>
                    <div className="fw-bold fs-4 text-danger">
                        {inspections.filter(i => i.result === 'failed').length}
                    </div>
                </div>
            </div>

            {/* Filters */}
            <div className="card mb-4">
                <div className="form-row" style={{ gap: '12px', flexWrap: 'wrap' }}>
                    <select className="form-input" style={{ maxWidth: '180px' }}
                        value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
                        <option value="">كل الحالات</option>
                        <option value="pending">قيد الانتظار</option>
                        <option value="in_progress">جاري الفحص</option>
                        <option value="completed">مكتمل</option>
                    </select>
                    <select className="form-input" style={{ maxWidth: '180px' }}
                        value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}>
                        <option value="">كل الأنواع</option>
                        <option value="incoming">وارد</option>
                        <option value="outgoing">صادر</option>
                        <option value="in_process">أثناء التصنيع</option>
                        <option value="random">عشوائي</option>
                    </select>
                </div>
            </div>

            {/* Table */}
            <div className="card">
                <div className="invoice-items-container">
                    <table className="data-table">
                        <thead>
                            <tr style={{ background: 'var(--bg-secondary)' }}>
                                <th style={{ width: '10%' }}>رقم الفحص</th>
                                <th style={{ width: '18%' }}>المنتج</th>
                                <th style={{ width: '12%' }}>المستودع</th>
                                <th style={{ width: '10%' }}>النوع</th>
                                <th style={{ width: '10%' }}>حجم العينة</th>
                                <th style={{ width: '10%' }}>الحالة</th>
                                <th style={{ width: '10%' }}>النتيجة</th>
                                <th style={{ width: '12%' }}>التاريخ</th>
                                <th style={{ width: '8%' }}>إجراءات</th>
                            </tr>
                        </thead>
                        <tbody>
                            {loading ? (
                                <tr><td colSpan="9" style={{ textAlign: 'center', padding: '40px' }}>جاري التحميل...</td></tr>
                            ) : inspections.length === 0 ? (
                                <tr><td colSpan="9" style={{ textAlign: 'center', padding: '40px', color: 'var(--text-secondary)' }}>
                                    لا توجد فحوصات مسجلة
                                </td></tr>
                            ) : inspections.map(insp => (
                                <tr key={insp.id}>
                                    <td><strong>{insp.inspection_number}</strong></td>
                                    <td>{insp.product_name}</td>
                                    <td>{insp.warehouse_name}</td>
                                    <td>{getTypeName(insp.inspection_type)}</td>
                                    <td>{insp.sample_size || '-'}</td>
                                    <td>{getStatusBadge(insp.status)}</td>
                                    <td>{getResultBadge(insp.result)}</td>
                                    <td>{insp.created_at ? new Date(insp.created_at).toLocaleDateString('ar-SA') : '-'}</td>
                                    <td>
                                        {insp.status !== 'completed' && (
                                            <button className="btn btn-sm btn-primary"
                                                onClick={() => openCompleteModal(insp)}
                                                title="إكمال الفحص">
                                                ✓
                                            </button>
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Create Modal */}
            {showCreateModal && (
                <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
                    <div className="modal-content" onClick={(e) => e.stopPropagation()}
                        style={{ maxWidth: '800px', width: '95%', maxHeight: '90vh', overflowY: 'auto' }}>
                        <div className="modal-header">
                            <h2>إنشاء فحص جودة جديد</h2>
                            <button className="modal-close" onClick={() => setShowCreateModal(false)}>✕</button>
                        </div>
                        <form onSubmit={handleCreate}>
                            {error && <div className="alert alert-error mb-4">{error}</div>}
                            <div className="form-row">
                                <div className="form-group">
                                    <label className="form-label">المنتج *</label>
                                    <select className="form-input" required value={form.product_id}
                                        onChange={(e) => setForm({ ...form, product_id: e.target.value })}>
                                        <option value="">-- اختر المنتج --</option>
                                        {products.filter(p => p.item_type === 'product').map(p => (
                                            <option key={p.id} value={p.id}>{p.item_name} ({p.item_code})</option>
                                        ))}
                                    </select>
                                </div>
                                <div className="form-group">
                                    <label className="form-label">المستودع *</label>
                                    <select className="form-input" required value={form.warehouse_id}
                                        onChange={(e) => setForm({ ...form, warehouse_id: e.target.value })}>
                                        <option value="">-- اختر المستودع --</option>
                                        {warehouses.map(w => (
                                            <option key={w.id} value={w.id}>{w.warehouse_name}</option>
                                        ))}
                                    </select>
                                </div>
                            </div>
                            <div className="form-row">
                                <div className="form-group">
                                    <label className="form-label">نوع الفحص</label>
                                    <select className="form-input" value={form.inspection_type}
                                        onChange={(e) => setForm({ ...form, inspection_type: e.target.value })}>
                                        <option value="incoming">وارد</option>
                                        <option value="outgoing">صادر</option>
                                        <option value="in_process">أثناء التصنيع</option>
                                        <option value="random">عشوائي</option>
                                    </select>
                                </div>
                                <div className="form-group">
                                    <label className="form-label">حجم العينة</label>
                                    <input type="number" className="form-input" min="1"
                                        value={form.sample_size}
                                        onChange={(e) => setForm({ ...form, sample_size: e.target.value })} />
                                </div>
                            </div>
                            <div className="form-group">
                                <label className="form-label">ملاحظات</label>
                                <textarea className="form-input" rows="2" value={form.notes}
                                    onChange={(e) => setForm({ ...form, notes: e.target.value })} />
                            </div>

                            {/* Criteria */}
                            <div style={{ marginTop: '20px' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                                    <h3>معايير الفحص</h3>
                                    <button type="button" className="btn btn-sm btn-secondary" onClick={addCriteria}>
                                        + إضافة معيار
                                    </button>
                                </div>
                                {form.criteria.map((c, i) => (
                                    <div key={i} className="form-row" style={{ alignItems: 'flex-end', gap: '8px', marginBottom: '8px' }}>
                                        <div className="form-group" style={{ flex: 2 }}>
                                            {i === 0 && <label className="form-label">اسم المعيار</label>}
                                            <input type="text" className="form-input" value={c.criteria_name}
                                                onChange={(e) => updateCriteria(i, 'criteria_name', e.target.value)}
                                                placeholder="مثال: الوزن، اللون..." />
                                        </div>
                                        <div className="form-group" style={{ flex: 1.5 }}>
                                            {i === 0 && <label className="form-label">القيمة المتوقعة</label>}
                                            <input type="text" className="form-input" value={c.expected_value}
                                                onChange={(e) => updateCriteria(i, 'expected_value', e.target.value)} />
                                        </div>
                                        <div className="form-group" style={{ flex: 1 }}>
                                            {i === 0 && <label className="form-label">الحد الأدنى</label>}
                                            <input type="number" step="0.01" className="form-input" value={c.min_value}
                                                onChange={(e) => updateCriteria(i, 'min_value', e.target.value)} />
                                        </div>
                                        <div className="form-group" style={{ flex: 1 }}>
                                            {i === 0 && <label className="form-label">الحد الأقصى</label>}
                                            <input type="number" step="0.01" className="form-input" value={c.max_value}
                                                onChange={(e) => updateCriteria(i, 'max_value', e.target.value)} />
                                        </div>
                                        {form.criteria.length > 1 && (
                                            <button type="button" className="btn btn-sm btn-danger"
                                                onClick={() => removeCriteria(i)} style={{ marginBottom: '4px' }}>✕</button>
                                        )}
                                    </div>
                                ))}
                            </div>

                            <div style={{ display: 'flex', gap: '12px', marginTop: '20px' }}>
                                <button type="submit" className="btn btn-primary" disabled={saving}>
                                    {saving ? 'جاري الحفظ...' : 'إنشاء الفحص'}
                                </button>
                                <button type="button" className="btn btn-secondary" onClick={() => setShowCreateModal(false)}>
                                    إلغاء
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Complete Modal */}
            {showCompleteModal && selectedInspection && (
                <div className="modal-overlay" onClick={() => setShowCompleteModal(false)}>
                    <div className="modal-content" onClick={(e) => e.stopPropagation()}
                        style={{ maxWidth: '500px', width: '90%' }}>
                        <div className="modal-header">
                            <h2>إكمال الفحص - {selectedInspection.inspection_number}</h2>
                            <button className="modal-close" onClick={() => setShowCompleteModal(false)}>✕</button>
                        </div>
                        <form onSubmit={handleComplete}>
                            {error && <div className="alert alert-error mb-4">{error}</div>}
                            <div className="form-group">
                                <label className="form-label">النتيجة *</label>
                                <select className="form-input" required value={completeForm.result}
                                    onChange={(e) => setCompleteForm({ ...completeForm, result: e.target.value })}>
                                    <option value="passed">✅ ناجح</option>
                                    <option value="failed">❌ فاشل</option>
                                    <option value="conditional">⚠️ مقبول بشروط</option>
                                </select>
                            </div>
                            <div className="form-group">
                                <label className="form-label">كمية العيوب</label>
                                <input type="number" className="form-input" min="0"
                                    value={completeForm.defect_quantity}
                                    onChange={(e) => setCompleteForm({ ...completeForm, defect_quantity: e.target.value })} />
                            </div>
                            <div className="form-group">
                                <label className="form-label">ملاحظات الفاحص</label>
                                <textarea className="form-input" rows="3" value={completeForm.inspector_notes}
                                    onChange={(e) => setCompleteForm({ ...completeForm, inspector_notes: e.target.value })} />
                            </div>
                            <div style={{ display: 'flex', gap: '12px', marginTop: '20px' }}>
                                <button type="submit" className="btn btn-primary" disabled={saving}>
                                    {saving ? 'جاري الحفظ...' : 'إكمال الفحص'}
                                </button>
                                <button type="button" className="btn btn-secondary" onClick={() => setShowCompleteModal(false)}>
                                    إلغاء
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    )
}

export default QualityInspections
