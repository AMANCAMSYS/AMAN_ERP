import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { inventoryAPI } from '../../utils/api'
import { useBranch } from '../../context/BranchContext'
import { useNavigate } from 'react-router-dom'

import DateInput from '../../components/common/DateInput';
function BatchList() {
    const { t } = useTranslation()
    const navigate = useNavigate()
    const { currentBranch } = useBranch()
    const [batches, setBatches] = useState([])
    const [loading, setLoading] = useState(true)
    const [search, setSearch] = useState('')
    const [statusFilter, setStatusFilter] = useState('')
    const [products, setProducts] = useState([])
    const [warehouses, setWarehouses] = useState([])
    const [productFilter, setProductFilter] = useState('')
    const [warehouseFilter, setWarehouseFilter] = useState('')
    const [showCreateModal, setShowCreateModal] = useState(false)
    const [total, setTotal] = useState(0)

    const [form, setForm] = useState({
        product_id: '',
        warehouse_id: '',
        batch_number: '',
        manufacturing_date: '',
        expiry_date: '',
        quantity: '',
        unit_cost: '',
        notes: ''
    })
    const [saving, setSaving] = useState(false)
    const [error, setError] = useState(null)

    useEffect(() => {
        fetchBatches()
        fetchProducts()
        fetchWarehouses()
    }, [currentBranch, search, statusFilter, productFilter, warehouseFilter])

    const fetchBatches = async () => {
        try {
            setLoading(true)
            const params = { limit: 100 }
            if (search) params.search = search
            if (statusFilter) params.status = statusFilter
            if (productFilter) params.product_id = productFilter
            if (warehouseFilter) params.warehouse_id = warehouseFilter
            const res = await inventoryAPI.listBatches(params)
            setBatches(res.data.items || [])
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

    const handleCreate = async (e) => {
        e.preventDefault()
        setSaving(true)
        setError(null)
        try {
            await inventoryAPI.createBatch({
                ...form,
                product_id: parseInt(form.product_id),
                warehouse_id: parseInt(form.warehouse_id),
                quantity: parseFloat(form.quantity || 0),
                unit_cost: parseFloat(form.unit_cost || 0)
            })
            setShowCreateModal(false)
            setForm({ product_id: '', warehouse_id: '', batch_number: '', manufacturing_date: '', expiry_date: '', quantity: '', unit_cost: '', notes: '' })
            fetchBatches()
        } catch (err) {
            setError(err.response?.data?.detail || 'حدث خطأ')
        } finally {
            setSaving(false)
        }
    }

    const getStatusBadge = (status) => {
        const map = {
            active: { label: 'نشط', cls: 'badge-success' },
            expired: { label: 'منتهي', cls: 'badge-danger' },
            consumed: { label: 'مستهلك', cls: 'badge-secondary' },
            recalled: { label: 'مسترجع', cls: 'badge-warning' }
        }
        const s = map[status] || { label: status, cls: 'badge-secondary' }
        return <span className={`badge ${s.cls}`}>{s.label}</span>
    }

    const getDaysRemaining = (expiryDate) => {
        if (!expiryDate) return null
        const days = Math.ceil((new Date(expiryDate) - new Date()) / (1000 * 60 * 60 * 24))
        if (days < 0) return <span style={{ color: 'var(--danger)' }}>منتهي منذ {Math.abs(days)} يوم</span>
        if (days <= 30) return <span style={{ color: 'var(--warning)' }}>متبقي {days} يوم</span>
        return <span style={{ color: 'var(--success)' }}>متبقي {days} يوم</span>
    }

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <div>
                    <h1 className="workspace-title">📦 {t('stock.batches.title', 'إدارة الدفعات')}</h1>
                    <p className="workspace-subtitle">{t('stock.batches.subtitle', 'تتبع الدفعات وأرقام اللوت وتواريخ الصلاحية')}</p>
                </div>
                <button className="btn btn-primary" onClick={() => setShowCreateModal(true)}>
                    + {t('stock.batches.add', 'إضافة دفعة')}
                </button>
            </div>

            {/* Stats */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '24px' }}>
                <div className="card p-3 text-center">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mx-auto mb-2 text-primary">
                        <path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4Z"/>
                        <path d="M3 6h18"/>
                        <path d="M16 10a4 4 0 0 1-8 0"/>
                    </svg>
                    <div className="small text-muted">إجمالي الدفعات</div>
                    <div className="fw-bold fs-4">{total}</div>
                </div>
                <div className="card p-3 text-center">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mx-auto mb-2 text-success">
                        <path d="M21.801 10A10 10 0 1 1 17 3.335"/>
                        <path d="m9 11 3 3L22 4"/>
                    </svg>
                    <div className="small text-muted">دفعات نشطة</div>
                    <div className="fw-bold fs-4 text-success">{batches.filter(b => b.status === 'active').length}</div>
                </div>
                <div className="card p-3 text-center">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mx-auto mb-2 text-warning">
                        <circle cx="12" cy="12" r="10"/>
                        <path d="M12 6v6l4 2"/>
                    </svg>
                    <div className="small text-muted">قريبة الانتهاء</div>
                    <div className="fw-bold fs-4 text-warning">
                        {batches.filter(b => b.expiry_date && new Date(b.expiry_date) <= new Date(Date.now() + 30*24*60*60*1000) && new Date(b.expiry_date) > new Date()).length}
                    </div>
                </div>
                <div className="card p-3 text-center">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mx-auto mb-2 text-danger">
                        <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/>
                        <path d="M12 9v4"/>
                        <path d="M12 17h.01"/>
                    </svg>
                    <div className="small text-muted">منتهية الصلاحية</div>
                    <div className="fw-bold fs-4 text-danger">
                        {batches.filter(b => b.expiry_date && new Date(b.expiry_date) < new Date()).length}
                    </div>
                </div>
            </div>

            {/* Filters */}
            <div className="card mb-4">
                <div className="form-row" style={{ gap: '12px', flexWrap: 'wrap' }}>
                    <input type="text" className="form-input" style={{ maxWidth: '250px' }}
                        placeholder="🔍 بحث بالرقم أو المنتج..."
                        value={search} onChange={(e) => setSearch(e.target.value)} />
                    <select className="form-input" style={{ maxWidth: '180px' }}
                        value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
                        <option value="">كل الحالات</option>
                        <option value="active">نشط</option>
                        <option value="expired">منتهي</option>
                        <option value="consumed">مستهلك</option>
                    </select>
                    <select className="form-input" style={{ maxWidth: '200px' }}
                        value={warehouseFilter} onChange={(e) => setWarehouseFilter(e.target.value)}>
                        <option value="">كل المستودعات</option>
                        {warehouses.map(w => <option key={w.id} value={w.id}>{w.warehouse_name}</option>)}
                    </select>
                </div>
            </div>

            {/* Table */}
            <div className="card">
                <div className="invoice-items-container">
                    <table className="data-table">
                        <thead>
                            <tr style={{ background: 'var(--bg-secondary)' }}>
                                <th style={{ width: '12%' }}>رقم الدفعة</th>
                                <th style={{ width: '20%' }}>المنتج</th>
                                <th style={{ width: '12%' }}>المستودع</th>
                                <th style={{ width: '10%' }}>الكمية</th>
                                <th style={{ width: '12%' }}>تاريخ التصنيع</th>
                                <th style={{ width: '12%' }}>تاريخ الانتهاء</th>
                                <th style={{ width: '12%' }}>المتبقي</th>
                                <th style={{ width: '10%' }}>الحالة</th>
                            </tr>
                        </thead>
                        <tbody>
                            {loading ? (
                                <tr><td colSpan="8" style={{ textAlign: 'center', padding: '40px' }}>جاري التحميل...</td></tr>
                            ) : batches.length === 0 ? (
                                <tr><td colSpan="8" style={{ textAlign: 'center', padding: '40px', color: 'var(--text-secondary)' }}>
                                    لا توجد دفعات مسجلة
                                </td></tr>
                            ) : batches.map(batch => (
                                <tr key={batch.id} style={{ cursor: 'pointer' }}
                                    onClick={() => navigate(`/stock/batches/${batch.id}`)}>
                                    <td><strong>{batch.batch_number}</strong></td>
                                    <td>{batch.product_name}</td>
                                    <td>{batch.warehouse_name}</td>
                                    <td>{parseFloat(batch.quantity || 0).toLocaleString()}</td>
                                    <td>{batch.manufacturing_date || '-'}</td>
                                    <td>{batch.expiry_date || '-'}</td>
                                    <td>{getDaysRemaining(batch.expiry_date) || '-'}</td>
                                    <td>{getStatusBadge(batch.status)}</td>
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
                        style={{ maxWidth: '700px', width: '90%' }}>
                        <div className="modal-header">
                            <h2>إضافة دفعة جديدة</h2>
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
                                    <label className="form-label">رقم الدفعة *</label>
                                    <input type="text" className="form-input" required value={form.batch_number}
                                        onChange={(e) => setForm({ ...form, batch_number: e.target.value })}
                                        placeholder="مثال: BATCH-2026-001" />
                                </div>
                                <div className="form-group">
                                    <label className="form-label">الكمية</label>
                                    <input type="number" className="form-input" min="0" step="0.01"
                                        value={form.quantity}
                                        onChange={(e) => setForm({ ...form, quantity: e.target.value })} />
                                </div>
                            </div>
                            <div className="form-row">
                                <div className="form-group">
                                    <label className="form-label">تاريخ التصنيع</label>
                                    <DateInput className="form-input" value={form.manufacturing_date}
                                        onChange={(e) => setForm({ ...form, manufacturing_date: e.target.value })} />
                                </div>
                                <div className="form-group">
                                    <label className="form-label">تاريخ الانتهاء</label>
                                    <DateInput className="form-input" value={form.expiry_date}
                                        onChange={(e) => setForm({ ...form, expiry_date: e.target.value })} />
                                </div>
                            </div>
                            <div className="form-row">
                                <div className="form-group">
                                    <label className="form-label">تكلفة الوحدة</label>
                                    <input type="number" className="form-input" min="0" step="0.01"
                                        value={form.unit_cost}
                                        onChange={(e) => setForm({ ...form, unit_cost: e.target.value })} />
                                </div>
                                <div className="form-group">
                                    <label className="form-label">ملاحظات</label>
                                    <input type="text" className="form-input" value={form.notes}
                                        onChange={(e) => setForm({ ...form, notes: e.target.value })} />
                                </div>
                            </div>
                            <div style={{ display: 'flex', gap: '12px', marginTop: '20px' }}>
                                <button type="submit" className="btn btn-primary" disabled={saving}>
                                    {saving ? 'جاري الحفظ...' : 'إنشاء الدفعة'}
                                </button>
                                <button type="button" className="btn btn-secondary" onClick={() => setShowCreateModal(false)}>
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

export default BatchList
