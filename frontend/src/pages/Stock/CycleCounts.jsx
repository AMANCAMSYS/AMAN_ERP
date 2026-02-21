import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { inventoryAPI } from '../../utils/api'
import { useBranch } from '../../context/BranchContext'

function CycleCounts() {
    const { t } = useTranslation()
    const { currentBranch } = useBranch()
    const [cycleCounts, setCycleCounts] = useState([])
    const [loading, setLoading] = useState(true)
    const [statusFilter, setStatusFilter] = useState('')
    const [warehouses, setWarehouses] = useState([])
    const [products, setProducts] = useState([])
    const [showCreateModal, setShowCreateModal] = useState(false)
    const [showDetailModal, setShowDetailModal] = useState(false)
    const [selectedCount, setSelectedCount] = useState(null)
    const [countDetail, setCountDetail] = useState(null)
    const [total, setTotal] = useState(0)

    const [form, setForm] = useState({
        warehouse_id: '',
        count_type: 'full',
        product_ids: [],
        notes: ''
    })

    const [itemUpdates, setItemUpdates] = useState([])
    const [saving, setSaving] = useState(false)
    const [error, setError] = useState(null)

    useEffect(() => {
        fetchCycleCounts()
        fetchWarehouses()
        fetchProducts()
    }, [currentBranch, statusFilter])

    const fetchCycleCounts = async () => {
        try {
            setLoading(true)
            const params = { limit: 100 }
            if (statusFilter) params.status = statusFilter
            const res = await inventoryAPI.listCycleCounts(params)
            setCycleCounts(res.data.items || [])
            setTotal(res.data.total || 0)
        } catch (err) {
            console.error(err)
        } finally {
            setLoading(false)
        }
    }

    const fetchWarehouses = async () => {
        try {
            const res = await inventoryAPI.listWarehouses({ branch_id: currentBranch?.id })
            setWarehouses(res.data || [])
        } catch (err) { console.error(err) }
    }

    const fetchProducts = async () => {
        try {
            const res = await inventoryAPI.listProducts({ limit: 500, branch_id: currentBranch?.id })
            setProducts(res.data || [])
        } catch (err) { console.error(err) }
    }

    const handleCreate = async (e) => {
        e.preventDefault()
        setSaving(true)
        setError(null)
        try {
            await inventoryAPI.createCycleCount({
                warehouse_id: parseInt(form.warehouse_id),
                count_type: form.count_type,
                product_ids: form.product_ids.map(id => parseInt(id)),
                notes: form.notes || null
            })
            setShowCreateModal(false)
            setForm({ warehouse_id: '', count_type: 'full', product_ids: [], notes: '' })
            fetchCycleCounts()
        } catch (err) {
            setError(err.response?.data?.detail || 'حدث خطأ')
        } finally {
            setSaving(false)
        }
    }

    const handleStart = async (id) => {
        try {
            await inventoryAPI.startCycleCount(id)
            fetchCycleCounts()
        } catch (err) {
            alert(err.response?.data?.detail || 'حدث خطأ')
        }
    }

    const openDetail = async (cc) => {
        setSelectedCount(cc)
        try {
            const res = await inventoryAPI.getCycleCount(cc.id)
            setCountDetail(res.data)
            const items = (res.data.items || []).map(item => ({
                item_id: item.id,
                counted_quantity: item.counted_quantity ?? item.system_quantity ?? 0,
                notes: item.notes || ''
            }))
            setItemUpdates(items)
            setShowDetailModal(true)
        } catch (err) {
            alert('حدث خطأ في تحميل التفاصيل')
        }
    }

    const updateItemCount = (itemId, field, value) => {
        setItemUpdates(prev => prev.map(item =>
            item.item_id === itemId ? { ...item, [field]: value } : item
        ))
    }

    const handleComplete = async () => {
        setSaving(true)
        setError(null)
        try {
            await inventoryAPI.completeCycleCount(selectedCount.id, {
                items: itemUpdates.map(item => ({
                    ...item,
                    counted_quantity: parseFloat(item.counted_quantity || 0)
                }))
            })
            setShowDetailModal(false)
            setSelectedCount(null)
            setCountDetail(null)
            fetchCycleCounts()
        } catch (err) {
            setError(err.response?.data?.detail || 'حدث خطأ')
        } finally {
            setSaving(false)
        }
    }

    const getStatusBadge = (status) => {
        const map = {
            draft: { label: 'مسودة', cls: 'badge-secondary' },
            in_progress: { label: 'جاري العد', cls: 'badge-warning' },
            completed: { label: 'مكتمل', cls: 'badge-success' },
            cancelled: { label: 'ملغي', cls: 'badge-danger' }
        }
        const s = map[status] || { label: status, cls: 'badge-secondary' }
        return <span className={`badge ${s.cls}`}>{s.label}</span>
    }

    const getCountTypeName = (type) => {
        const map = { full: 'جرد شامل', partial: 'جرد جزئي', random: 'جرد عشوائي' }
        return map[type] || type
    }

    const toggleProductSelect = (productId) => {
        const id = String(productId)
        setForm(prev => ({
            ...prev,
            product_ids: prev.product_ids.includes(id)
                ? prev.product_ids.filter(p => p !== id)
                : [...prev.product_ids, id]
        }))
    }

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <div>
                    <h1 className="workspace-title">📋 {t('stock.cycleCounts.title', 'الجرد الدوري')}</h1>
                    <p className="workspace-subtitle">{t('stock.cycleCounts.subtitle', 'جرد المخزون ومطابقة الكميات الفعلية مع النظام')}</p>
                </div>
                <button className="btn btn-primary" onClick={() => setShowCreateModal(true)}>
                    + إنشاء عملية جرد
                </button>
            </div>

            {/* Stats */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '24px' }}>
                <div className="card p-3 text-center">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mx-auto mb-2 text-primary">
                        <path d="M3 3v18h18"/>
                        <path d="m19 9-5 5-4-4-3 3"/>
                    </svg>
                    <div className="small text-muted">إجمالي عمليات الجرد</div>
                    <div className="fw-bold fs-4">{total}</div>
                </div>
                <div className="card p-3 text-center">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mx-auto mb-2 text-warning">
                        <path d="M12 2v20"/>
                        <path d="m15 19-3 3-3-3"/>
                        <path d="m19 15 3-3-3-3"/>
                        <circle cx="12" cy="12" r="3"/>
                    </svg>
                    <div className="small text-muted">جاري العد</div>
                    <div className="fw-bold fs-4 text-warning">
                        {cycleCounts.filter(c => c.status === 'in_progress').length}
                    </div>
                </div>
                <div className="card p-3 text-center">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mx-auto mb-2 text-success">
                        <path d="M21.801 10A10 10 0 1 1 17 3.335"/>
                        <path d="m9 11 3 3L22 4"/>
                    </svg>
                    <div className="small text-muted">مكتمل</div>
                    <div className="fw-bold fs-4 text-success">
                        {cycleCounts.filter(c => c.status === 'completed').length}
                    </div>
                </div>
                <div className="card p-3 text-center">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mx-auto mb-2 text-primary">
                        <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/>
                        <polyline points="14 2 14 8 20 8"/>
                    </svg>
                    <div className="small text-muted">مسودات</div>
                    <div className="fw-bold fs-4 text-primary">
                        {cycleCounts.filter(c => c.status === 'draft').length}
                    </div>
                </div>
            </div>

            {/* Filters */}
            <div className="card mb-4">
                <div className="form-row" style={{ gap: '12px', flexWrap: 'wrap' }}>
                    <select className="form-input" style={{ maxWidth: '180px' }}
                        value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
                        <option value="">كل الحالات</option>
                        <option value="draft">مسودة</option>
                        <option value="in_progress">جاري العد</option>
                        <option value="completed">مكتمل</option>
                    </select>
                </div>
            </div>

            {/* Table */}
            <div className="card">
                <div className="invoice-items-container">
                    <table className="data-table">
                        <thead>
                            <tr style={{ background: 'var(--bg-secondary)' }}>
                                <th style={{ width: '12%' }}>رقم الجرد</th>
                                <th style={{ width: '15%' }}>المستودع</th>
                                <th style={{ width: '12%' }}>النوع</th>
                                <th style={{ width: '10%' }}>عدد الأصناف</th>
                                <th style={{ width: '10%' }}>الفروقات</th>
                                <th style={{ width: '10%' }}>الحالة</th>
                                <th style={{ width: '15%' }}>التاريخ</th>
                                <th style={{ width: '16%' }}>إجراءات</th>
                            </tr>
                        </thead>
                        <tbody>
                            {loading ? (
                                <tr><td colSpan="8" style={{ textAlign: 'center', padding: '40px' }}>جاري التحميل...</td></tr>
                            ) : cycleCounts.length === 0 ? (
                                <tr><td colSpan="8" style={{ textAlign: 'center', padding: '40px', color: 'var(--text-secondary)' }}>
                                    لا توجد عمليات جرد
                                </td></tr>
                            ) : cycleCounts.map(cc => (
                                <tr key={cc.id}>
                                    <td><strong>{cc.count_number}</strong></td>
                                    <td>{cc.warehouse_name}</td>
                                    <td>{getCountTypeName(cc.count_type)}</td>
                                    <td>{cc.total_items || '-'}</td>
                                    <td>
                                        {cc.total_variance != null ? (
                                            <span style={{ color: cc.total_variance !== 0 ? 'var(--danger)' : 'var(--success)' }}>
                                                {cc.total_variance}
                                            </span>
                                        ) : '-'}
                                    </td>
                                    <td>{getStatusBadge(cc.status)}</td>
                                    <td>{cc.created_at ? new Date(cc.created_at).toLocaleDateString('ar-SA') : '-'}</td>
                                    <td>
                                        <div style={{ display: 'flex', gap: '6px' }}>
                                            {cc.status === 'draft' && (
                                                <button className="btn btn-sm btn-primary" onClick={() => handleStart(cc.id)}>
                                                    ▶ بدء العد
                                                </button>
                                            )}
                                            {cc.status === 'in_progress' && (
                                                <button className="btn btn-sm btn-success" onClick={() => openDetail(cc)}>
                                                    📝 تسجيل العد
                                                </button>
                                            )}
                                            {cc.status === 'completed' && (
                                                <button className="btn btn-sm btn-secondary" onClick={() => openDetail(cc)}>
                                                    👁 عرض
                                                </button>
                                            )}
                                        </div>
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
                        style={{ maxWidth: '700px', width: '90%', maxHeight: '90vh', overflowY: 'auto' }}>
                        <div className="modal-header">
                            <h2>إنشاء عملية جرد جديدة</h2>
                            <button className="modal-close" onClick={() => setShowCreateModal(false)}>✕</button>
                        </div>
                        <form onSubmit={handleCreate}>
                            {error && <div className="alert alert-error mb-4">{error}</div>}
                            <div className="form-row">
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
                                <div className="form-group">
                                    <label className="form-label">نوع الجرد</label>
                                    <select className="form-input" value={form.count_type}
                                        onChange={(e) => setForm({ ...form, count_type: e.target.value })}>
                                        <option value="full">جرد شامل</option>
                                        <option value="partial">جرد جزئي</option>
                                        <option value="random">جرد عشوائي</option>
                                    </select>
                                </div>
                            </div>

                            {form.count_type === 'partial' && (
                                <div className="form-group">
                                    <label className="form-label">اختر المنتجات للجرد</label>
                                    <div style={{ maxHeight: '200px', overflowY: 'auto', border: '1px solid var(--border)', borderRadius: '8px', padding: '8px' }}>
                                        {products.filter(p => p.item_type === 'product').map(p => (
                                            <label key={p.id} style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '6px', cursor: 'pointer' }}>
                                                <input type="checkbox" checked={form.product_ids.includes(String(p.id))}
                                                    onChange={() => toggleProductSelect(p.id)} />
                                                {p.item_name} ({p.item_code})
                                            </label>
                                        ))}
                                    </div>
                                    <small style={{ color: 'var(--text-secondary)' }}>تم اختيار {form.product_ids.length} منتج</small>
                                </div>
                            )}

                            <div className="form-group">
                                <label className="form-label">ملاحظات</label>
                                <textarea className="form-input" rows="2" value={form.notes}
                                    onChange={(e) => setForm({ ...form, notes: e.target.value })} />
                            </div>

                            <div style={{ display: 'flex', gap: '12px', marginTop: '20px' }}>
                                <button type="submit" className="btn btn-primary" disabled={saving}>
                                    {saving ? 'جاري الإنشاء...' : 'إنشاء الجرد'}
                                </button>
                                <button type="button" className="btn btn-secondary" onClick={() => setShowCreateModal(false)}>
                                    إلغاء
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Detail/Count Modal */}
            {showDetailModal && countDetail && (
                <div className="modal-overlay" onClick={() => setShowDetailModal(false)}>
                    <div className="modal-content" onClick={(e) => e.stopPropagation()}
                        style={{ maxWidth: '900px', width: '95%', maxHeight: '90vh', overflowY: 'auto' }}>
                        <div className="modal-header">
                            <h2>
                                {selectedCount?.status === 'in_progress' ? '📝 تسجيل العد' : '👁 تفاصيل الجرد'} - {countDetail.count_number}
                            </h2>
                            <button className="modal-close" onClick={() => setShowDetailModal(false)}>✕</button>
                        </div>

                        <div style={{ marginBottom: '16px', display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' }}>
                            <div><strong>المستودع:</strong> {countDetail.warehouse_name}</div>
                            <div><strong>النوع:</strong> {getCountTypeName(countDetail.count_type)}</div>
                            <div><strong>الحالة:</strong> {getStatusBadge(countDetail.status)}</div>
                        </div>

                        {error && <div className="alert alert-error mb-4">{error}</div>}

                        <div className="invoice-items-container">
                            <table className="data-table">
                                <thead>
                                    <tr style={{ background: 'var(--bg-secondary)' }}>
                                        <th>المنتج</th>
                                        <th>كمية النظام</th>
                                        <th>الكمية الفعلية</th>
                                        <th>الفرق</th>
                                        <th>ملاحظات</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {(countDetail.items || []).map(item => {
                                        const update = itemUpdates.find(u => u.item_id === item.id)
                                        const variance = (parseFloat(update?.counted_quantity || 0) - parseFloat(item.system_quantity || 0))
                                        return (
                                            <tr key={item.id}>
                                                <td>{item.product_name}</td>
                                                <td>{parseFloat(item.system_quantity || 0).toLocaleString()}</td>
                                                <td>
                                                    {selectedCount?.status === 'in_progress' ? (
                                                        <input type="number" className="form-input" min="0" step="0.01"
                                                            style={{ width: '120px' }}
                                                            value={update?.counted_quantity ?? ''}
                                                            onChange={(e) => updateItemCount(item.id, 'counted_quantity', e.target.value)} />
                                                    ) : (
                                                        parseFloat(item.counted_quantity || 0).toLocaleString()
                                                    )}
                                                </td>
                                                <td>
                                                    <span style={{ color: variance !== 0 ? 'var(--danger)' : 'var(--success)', fontWeight: 'bold' }}>
                                                        {variance > 0 ? '+' : ''}{variance}
                                                    </span>
                                                </td>
                                                <td>
                                                    {selectedCount?.status === 'in_progress' ? (
                                                        <input type="text" className="form-input"
                                                            style={{ width: '150px' }}
                                                            value={update?.notes ?? ''}
                                                            onChange={(e) => updateItemCount(item.id, 'notes', e.target.value)}
                                                            placeholder="سبب الفرق..." />
                                                    ) : (
                                                        item.notes || '-'
                                                    )}
                                                </td>
                                            </tr>
                                        )
                                    })}
                                </tbody>
                            </table>
                        </div>

                        {selectedCount?.status === 'in_progress' && (
                            <div style={{ display: 'flex', gap: '12px', marginTop: '20px' }}>
                                <button className="btn btn-success" onClick={handleComplete} disabled={saving}>
                                    {saving ? 'جاري الحفظ...' : '✓ إتمام الجرد وتعديل المخزون'}
                                </button>
                                <button className="btn btn-secondary" onClick={() => setShowDetailModal(false)}>
                                    إلغاء
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    )
}

export default CycleCounts
