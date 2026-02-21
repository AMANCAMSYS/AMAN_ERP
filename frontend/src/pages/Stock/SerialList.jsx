import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { inventoryAPI } from '../../utils/api'
import { useBranch } from '../../context/BranchContext'
import { formatShortDate } from '../../utils/dateUtils';


function SerialList() {
    const { t } = useTranslation()
    const { currentBranch } = useBranch()
    const [serials, setSerials] = useState([])
    const [loading, setLoading] = useState(true)
    const [search, setSearch] = useState('')
    const [statusFilter, setStatusFilter] = useState('')
    const [products, setProducts] = useState([])
    const [warehouses, setWarehouses] = useState([])
    const [productFilter, setProductFilter] = useState('')
    const [showCreateModal, setShowCreateModal] = useState(false)
    const [showBulkModal, setShowBulkModal] = useState(false)
    const [total, setTotal] = useState(0)

    const [form, setForm] = useState({
        product_id: '',
        warehouse_id: '',
        serial_number: '',
        batch_id: '',
        notes: ''
    })

    const [bulkForm, setBulkForm] = useState({
        product_id: '',
        warehouse_id: '',
        prefix: '',
        start_number: 1,
        count: 10,
        batch_id: ''
    })

    const [saving, setSaving] = useState(false)
    const [error, setError] = useState(null)
    const [lookupSerial, setLookupSerial] = useState('')
    const [lookupResult, setLookupResult] = useState(null)
    const [showLookup, setShowLookup] = useState(false)

    useEffect(() => {
        fetchSerials()
        fetchProducts()
        fetchWarehouses()
    }, [currentBranch, search, statusFilter, productFilter])

    const fetchSerials = async () => {
        try {
            setLoading(true)
            const params = { limit: 100 }
            if (search) params.search = search
            if (statusFilter) params.status = statusFilter
            if (productFilter) params.product_id = productFilter
            const res = await inventoryAPI.listSerials(params)
            setSerials(res.data.items || [])
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
            await inventoryAPI.createSerial({
                ...form,
                product_id: parseInt(form.product_id),
                warehouse_id: parseInt(form.warehouse_id),
                batch_id: form.batch_id ? parseInt(form.batch_id) : null
            })
            setShowCreateModal(false)
            setForm({ product_id: '', warehouse_id: '', serial_number: '', batch_id: '', notes: '' })
            fetchSerials()
        } catch (err) {
            setError(err.response?.data?.detail || 'حدث خطأ')
        } finally {
            setSaving(false)
        }
    }

    const handleBulkCreate = async (e) => {
        e.preventDefault()
        setSaving(true)
        setError(null)
        try {
            await inventoryAPI.createSerialsBulk({
                product_id: parseInt(bulkForm.product_id),
                warehouse_id: parseInt(bulkForm.warehouse_id),
                prefix: bulkForm.prefix,
                start_number: parseInt(bulkForm.start_number),
                count: parseInt(bulkForm.count),
                batch_id: bulkForm.batch_id ? parseInt(bulkForm.batch_id) : null
            })
            setShowBulkModal(false)
            setBulkForm({ product_id: '', warehouse_id: '', prefix: '', start_number: 1, count: 10, batch_id: '' })
            fetchSerials()
        } catch (err) {
            setError(err.response?.data?.detail || 'حدث خطأ')
        } finally {
            setSaving(false)
        }
    }

    const handleLookup = async () => {
        if (!lookupSerial.trim()) return
        try {
            const res = await inventoryAPI.lookupSerial(lookupSerial.trim())
            setLookupResult(res.data)
        } catch (err) {
            setLookupResult({ error: 'لم يتم العثور على الرقم التسلسلي' })
        }
    }

    const getStatusBadge = (status) => {
        const map = {
            available: { label: 'متاح', cls: 'badge-success' },
            sold: { label: 'مباع', cls: 'badge-primary' },
            reserved: { label: 'محجوز', cls: 'badge-warning' },
            defective: { label: 'معيب', cls: 'badge-danger' },
            returned: { label: 'مرتجع', cls: 'badge-secondary' },
            in_warranty: { label: 'تحت الضمان', cls: 'badge-info' }
        }
        const s = map[status] || { label: status, cls: 'badge-secondary' }
        return <span className={`badge ${s.cls}`}>{s.label}</span>
    }

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <div>
                    <h1 className="workspace-title">🏷️ {t('stock.serials.title', 'الأرقام التسلسلية')}</h1>
                    <p className="workspace-subtitle">{t('stock.serials.subtitle', 'تتبع المنتجات بالأرقام التسلسلية الفريدة')}</p>
                </div>
                <div style={{ display: 'flex', gap: '10px' }}>
                    <button className="btn btn-secondary" onClick={() => setShowLookup(!showLookup)}>
                        🔍 بحث سريع
                    </button>
                    <button className="btn btn-secondary" onClick={() => setShowBulkModal(true)}>
                        📋 إنشاء جماعي
                    </button>
                    <button className="btn btn-primary" onClick={() => setShowCreateModal(true)}>
                        + إضافة رقم تسلسلي
                    </button>
                </div>
            </div>

            {/* Quick Lookup */}
            {showLookup && (
                <div className="card mb-4" style={{ background: 'var(--bg-secondary)' }}>
                    <h3 style={{ marginBottom: '12px' }}>🔍 بحث سريع عن رقم تسلسلي</h3>
                    <div style={{ display: 'flex', gap: '12px' }}>
                        <input type="text" className="form-input" style={{ maxWidth: '350px' }}
                            placeholder="أدخل الرقم التسلسلي..."
                            value={lookupSerial} onChange={(e) => setLookupSerial(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && handleLookup()} />
                        <button className="btn btn-primary" onClick={handleLookup}>بحث</button>
                    </div>
                    {lookupResult && (
                        <div style={{ marginTop: '16px', padding: '12px', background: 'var(--bg-primary)', borderRadius: '8px' }}>
                            {lookupResult.error ? (
                                <p style={{ color: 'var(--danger)' }}>{lookupResult.error}</p>
                            ) : (
                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px' }}>
                                    <div><strong>الرقم:</strong> {lookupResult.serial_number}</div>
                                    <div><strong>المنتج:</strong> {lookupResult.product_name}</div>
                                    <div><strong>المستودع:</strong> {lookupResult.warehouse_name}</div>
                                    <div><strong>الحالة:</strong> {getStatusBadge(lookupResult.status)}</div>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            )}

            {/* Stats */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '24px' }}>
                <div className="card p-3 text-center">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mx-auto mb-2 text-primary">
                        <path d="M3 7V5a2 2 0 0 1 2-2h2"/>
                        <path d="M17 3h2a2 2 0 0 1 2 2v2"/>
                        <path d="M21 17v2a2 2 0 0 1-2 2h-2"/>
                        <path d="M7 21H5a2 2 0 0 1-2-2v-2"/>
                        <path d="M7 12h10"/>
                    </svg>
                    <div className="small text-muted">إجمالي الأرقام</div>
                    <div className="fw-bold fs-4">{total}</div>
                </div>
                <div className="card p-3 text-center">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mx-auto mb-2 text-success">
                        <path d="M21.801 10A10 10 0 1 1 17 3.335"/>
                        <path d="m9 11 3 3L22 4"/>
                    </svg>
                    <div className="small text-muted">متاح</div>
                    <div className="fw-bold fs-4 text-success">
                        {serials.filter(s => s.status === 'available').length}
                    </div>
                </div>
                <div className="card p-3 text-center">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mx-auto mb-2 text-primary">
                        <circle cx="12" cy="12" r="10"/>
                        <path d="m15 9-6 6"/>
                        <path d="m9 9 6 6"/>
                    </svg>
                    <div className="small text-muted">مباع</div>
                    <div className="fw-bold fs-4 text-primary">
                        {serials.filter(s => s.status === 'sold').length}
                    </div>
                </div>
                <div className="card p-3 text-center">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mx-auto mb-2 text-danger">
                        <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/>
                        <path d="M12 9v4"/>
                        <path d="M12 17h.01"/>
                    </svg>
                    <div className="small text-muted">معيب</div>
                    <div className="fw-bold fs-4 text-danger">
                        {serials.filter(s => s.status === 'defective').length}
                    </div>
                </div>
            </div>

            {/* Filters */}
            <div className="card mb-4">
                <div className="form-row" style={{ gap: '12px', flexWrap: 'wrap' }}>
                    <input type="text" className="form-input" style={{ maxWidth: '250px' }}
                        placeholder="🔍 بحث بالرقم التسلسلي..."
                        value={search} onChange={(e) => setSearch(e.target.value)} />
                    <select className="form-input" style={{ maxWidth: '180px' }}
                        value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
                        <option value="">كل الحالات</option>
                        <option value="available">متاح</option>
                        <option value="sold">مباع</option>
                        <option value="reserved">محجوز</option>
                        <option value="defective">معيب</option>
                        <option value="returned">مرتجع</option>
                    </select>
                    <select className="form-input" style={{ maxWidth: '200px' }}
                        value={productFilter} onChange={(e) => setProductFilter(e.target.value)}>
                        <option value="">كل المنتجات</option>
                        {products.filter(p => p.item_type === 'product').map(p => (
                            <option key={p.id} value={p.id}>{p.item_name}</option>
                        ))}
                    </select>
                </div>
            </div>

            {/* Table */}
            <div className="card">
                <div className="invoice-items-container">
                    <table className="data-table">
                        <thead>
                            <tr style={{ background: 'var(--bg-secondary)' }}>
                                <th style={{ width: '15%' }}>الرقم التسلسلي</th>
                                <th style={{ width: '20%' }}>المنتج</th>
                                <th style={{ width: '15%' }}>المستودع</th>
                                <th style={{ width: '12%' }}>رقم الدفعة</th>
                                <th style={{ width: '12%' }}>تاريخ الانتهاء</th>
                                <th style={{ width: '10%' }}>الحالة</th>
                                <th style={{ width: '16%' }}>تاريخ الإنشاء</th>
                            </tr>
                        </thead>
                        <tbody>
                            {loading ? (
                                <tr><td colSpan="7" style={{ textAlign: 'center', padding: '40px' }}>جاري التحميل...</td></tr>
                            ) : serials.length === 0 ? (
                                <tr><td colSpan="7" style={{ textAlign: 'center', padding: '40px', color: 'var(--text-secondary)' }}>
                                    لا توجد أرقام تسلسلية
                                </td></tr>
                            ) : serials.map(serial => (
                                <tr key={serial.id}>
                                    <td><strong>{serial.serial_number}</strong></td>
                                    <td>{serial.product_name}</td>
                                    <td>{serial.warehouse_name}</td>
                                    <td>{serial.batch_number || '-'}</td>
                                    <td>{serial.warranty_expiry || '-'}</td>
                                    <td>{getStatusBadge(serial.status)}</td>
                                    <td>{serial.created_at ? formatShortDate(serial.created_at) : '-'}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Create Single Modal */}
            {showCreateModal && (
                <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
                    <div className="modal-content" onClick={(e) => e.stopPropagation()}
                        style={{ maxWidth: '600px', width: '90%' }}>
                        <div className="modal-header">
                            <h2>إضافة رقم تسلسلي</h2>
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
                            <div className="form-group">
                                <label className="form-label">الرقم التسلسلي *</label>
                                <input type="text" className="form-input" required value={form.serial_number}
                                    onChange={(e) => setForm({ ...form, serial_number: e.target.value })}
                                    placeholder="مثال: SN-2026-000001" />
                            </div>
                            <div className="form-group">
                                <label className="form-label">ملاحظات</label>
                                <input type="text" className="form-input" value={form.notes}
                                    onChange={(e) => setForm({ ...form, notes: e.target.value })} />
                            </div>
                            <div style={{ display: 'flex', gap: '12px', marginTop: '20px' }}>
                                <button type="submit" className="btn btn-primary" disabled={saving}>
                                    {saving ? 'جاري الحفظ...' : 'إنشاء'}
                                </button>
                                <button type="button" className="btn btn-secondary" onClick={() => setShowCreateModal(false)}>
                                    إلغاء
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Bulk Create Modal */}
            {showBulkModal && (
                <div className="modal-overlay" onClick={() => setShowBulkModal(false)}>
                    <div className="modal-content" onClick={(e) => e.stopPropagation()}
                        style={{ maxWidth: '600px', width: '90%' }}>
                        <div className="modal-header">
                            <h2>إنشاء أرقام تسلسلية جماعية</h2>
                            <button className="modal-close" onClick={() => setShowBulkModal(false)}>✕</button>
                        </div>
                        <form onSubmit={handleBulkCreate}>
                            {error && <div className="alert alert-error mb-4">{error}</div>}
                            <div className="form-row">
                                <div className="form-group">
                                    <label className="form-label">المنتج *</label>
                                    <select className="form-input" required value={bulkForm.product_id}
                                        onChange={(e) => setBulkForm({ ...bulkForm, product_id: e.target.value })}>
                                        <option value="">-- اختر المنتج --</option>
                                        {products.filter(p => p.item_type === 'product').map(p => (
                                            <option key={p.id} value={p.id}>{p.item_name}</option>
                                        ))}
                                    </select>
                                </div>
                                <div className="form-group">
                                    <label className="form-label">المستودع *</label>
                                    <select className="form-input" required value={bulkForm.warehouse_id}
                                        onChange={(e) => setBulkForm({ ...bulkForm, warehouse_id: e.target.value })}>
                                        <option value="">-- اختر المستودع --</option>
                                        {warehouses.map(w => (
                                            <option key={w.id} value={w.id}>{w.warehouse_name}</option>
                                        ))}
                                    </select>
                                </div>
                            </div>
                            <div className="form-row">
                                <div className="form-group">
                                    <label className="form-label">البادئة *</label>
                                    <input type="text" className="form-input" required value={bulkForm.prefix}
                                        onChange={(e) => setBulkForm({ ...bulkForm, prefix: e.target.value })}
                                        placeholder="مثال: SN-LAPTOP-" />
                                </div>
                                <div className="form-group">
                                    <label className="form-label">رقم البداية</label>
                                    <input type="number" className="form-input" min="1"
                                        value={bulkForm.start_number}
                                        onChange={(e) => setBulkForm({ ...bulkForm, start_number: e.target.value })} />
                                </div>
                                <div className="form-group">
                                    <label className="form-label">العدد</label>
                                    <input type="number" className="form-input" min="1" max="1000"
                                        value={bulkForm.count}
                                        onChange={(e) => setBulkForm({ ...bulkForm, count: e.target.value })} />
                                </div>
                            </div>
                            <div style={{ padding: '12px', background: 'var(--bg-secondary)', borderRadius: '8px', marginTop: '8px' }}>
                                <strong>معاينة:</strong> {bulkForm.prefix}{String(bulkForm.start_number).padStart(6, '0')} → {bulkForm.prefix}{String(parseInt(bulkForm.start_number) + parseInt(bulkForm.count) - 1).padStart(6, '0')}
                                <br /><small>سيتم إنشاء {bulkForm.count} رقم تسلسلي</small>
                            </div>
                            <div style={{ display: 'flex', gap: '12px', marginTop: '20px' }}>
                                <button type="submit" className="btn btn-primary" disabled={saving}>
                                    {saving ? 'جاري الإنشاء...' : `إنشاء ${bulkForm.count} رقم`}
                                </button>
                                <button type="button" className="btn btn-secondary" onClick={() => setShowBulkModal(false)}>
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

export default SerialList
