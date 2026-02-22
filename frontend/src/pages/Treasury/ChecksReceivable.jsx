import { useState, useEffect, useCallback } from 'react'
import { checksAPI, salesAPI, treasuryAPI } from '../../utils/api'
import { useTranslation } from 'react-i18next'
import { formatShortDate } from '../../utils/dateUtils'
import { useBranch } from '../../context/BranchContext'
import { formatNumber } from '../../utils/format'
import { getCurrency } from '../../utils/auth'
import { Clock, CheckCircle, XCircle, AlertTriangle } from 'lucide-react'
import '../../components/ModuleStyles.css'

import DateInput from '../../components/common/DateInput';
import BackButton from '../../components/common/BackButton';
function ChecksReceivable() {
    const { t } = useTranslation()
    const { currentBranch } = useBranch()
    const currency = getCurrency()

    const [items, setItems] = useState([])
    const [loading, setLoading] = useState(true)
    const [total, setTotal] = useState(0)
    const [page, setPage] = useState(1)
    const [search, setSearch] = useState('')
    const [statusFilter, setStatusFilter] = useState('')
    const [stats, setStats] = useState(null)

    // Create modal
    const [showCreate, setShowCreate] = useState(false)
    const [customers, setCustomers] = useState([])
    const [treasuryAccounts, setTreasuryAccounts] = useState([])
    const [form, setForm] = useState({
        check_number: '', drawer_name: '', bank_name: '', branch_name: '',
        amount: '', currency: getCurrency(), issue_date: new Date().toISOString().split('T')[0],
        due_date: '', party_id: '', treasury_account_id: '', notes: ''
    })
    const [saving, setSaving] = useState(false)

    // Detail modal
    const [detailItem, setDetailItem] = useState(null)
    const [showDetail, setShowDetail] = useState(false)

    // Action modals
    const [showCollect, setShowCollect] = useState(false)
    const [showBounce, setShowBounce] = useState(false)
    const [actionForm, setActionForm] = useState({})

    const fetchList = useCallback(async () => {
        try {
            setLoading(true)
            const params = { page, limit: 50, branch_id: currentBranch?.id }
            if (search) params.search = search
            if (statusFilter) params.status = statusFilter
            const res = await checksAPI.listReceivable(params)
            setItems(res.data.items || [])
            setTotal(res.data.total || 0)
        } catch (err) { console.error(err) }
        finally { setLoading(false) }
    }, [page, search, statusFilter, currentBranch])

    const fetchStats = useCallback(async () => {
        try {
            const res = await checksAPI.receivableStats({ branch_id: currentBranch?.id })
            setStats(res.data)
        } catch (err) { console.error(err) }
    }, [currentBranch])

    useEffect(() => { fetchList(); fetchStats() }, [fetchList, fetchStats])

    const loadCreateData = async () => {
        try {
            const [custRes, treasRes] = await Promise.all([
                salesAPI.listCustomers({ limit: 500 }),
                treasuryAPI.listAccounts()
            ])
            setCustomers(custRes.data?.data || custRes.data || [])
            setTreasuryAccounts(treasRes.data?.items || treasRes.data || [])
        } catch (err) { console.error(err) }
    }

    const openCreate = () => {
        setForm({
            check_number: '', drawer_name: '', bank_name: '', branch_name: '',
            amount: '', currency: getCurrency(), issue_date: new Date().toISOString().split('T')[0],
            due_date: '', party_id: '', treasury_account_id: '', notes: ''
        })
        loadCreateData()
        setShowCreate(true)
    }

    const handleCreate = async () => {
        if (!form.check_number || !form.amount || !form.due_date) return alert('يجب تعبئة رقم الشيك والمبلغ وتاريخ الاستحقاق')
        try {
            setSaving(true)
            await checksAPI.createReceivable({
                ...form,
                amount: parseFloat(form.amount),
                party_id: form.party_id ? parseInt(form.party_id) : null,
                treasury_account_id: form.treasury_account_id ? parseInt(form.treasury_account_id) : null,
                branch_id: currentBranch?.id,
            })
            setShowCreate(false)
            fetchList(); fetchStats()
        } catch (err) {
            alert(err.response?.data?.detail || 'حدث خطأ')
        } finally { setSaving(false) }
    }

    const viewDetail = async (id) => {
        try {
            const res = await checksAPI.getReceivable(id)
            setDetailItem(res.data)
            setShowDetail(true)
        } catch (err) { console.error(err) }
    }

    const handleCollect = async () => {
        try {
            setSaving(true)
            await checksAPI.collectReceivable(detailItem.id, {
                collection_date: actionForm.collection_date || new Date().toISOString().split('T')[0],
                treasury_account_id: actionForm.treasury_account_id ? parseInt(actionForm.treasury_account_id) : null,
            })
            setShowCollect(false); setShowDetail(false)
            fetchList(); fetchStats()
        } catch (err) {
            alert(err.response?.data?.detail || 'حدث خطأ')
        } finally { setSaving(false) }
    }

    const handleBounce = async () => {
        try {
            setSaving(true)
            await checksAPI.bounceReceivable(detailItem.id, {
                bounce_date: actionForm.bounce_date || new Date().toISOString().split('T')[0],
                bounce_reason: actionForm.bounce_reason || '',
            })
            setShowBounce(false); setShowDetail(false)
            fetchList(); fetchStats()
        } catch (err) {
            alert(err.response?.data?.detail || 'حدث خطأ')
        } finally { setSaving(false) }
    }

    const openCollect = () => {
        loadCreateData()
        setActionForm({ collection_date: new Date().toISOString().split('T')[0], treasury_account_id: detailItem.treasury_account_id || '' })
        setShowCollect(true)
    }

    const openBounce = () => {
        setActionForm({ bounce_date: new Date().toISOString().split('T')[0], bounce_reason: '' })
        setShowBounce(true)
    }

    const statusBadge = (s) => {
        const map = { pending: 'badge-warning', collected: 'badge-success', bounced: 'badge-danger' }
        const labels = { pending: 'معلق', collected: 'محصّل', bounced: 'مرتجع' }
        return <span className={`badge ${map[s] || 'badge-secondary'}`}>{labels[s] || s}</span>
    }

    const isOverdue = (dueDate, status) => {
        if (status !== 'pending') return false
        return new Date(dueDate) <= new Date()
    }

    if (loading && !items.length) return <div className="page-center"><span className="loading"></span></div>

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
                    <div>
                        <h1 className="workspace-title">📥 شيكات تحت التحصيل</h1>
                        <p className="workspace-subtitle">Checks Receivable - إدارة الشيكات الواردة</p>
                    </div>
                    <button className="btn btn-primary" onClick={openCreate}>+ تسجيل شيك وارد</button>
                </div>
            </div>

            {/* Stats Cards */}
            {stats && (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '24px' }}>
                    <div className="card p-3 text-center">
                        <Clock size={24} className="text-warning mb-2" />
                        <div className="small text-muted">معلق</div>
                        <div className="fw-bold fs-4">{stats.pending.count}</div>
                        <div className="small text-muted">{formatNumber(stats.pending.amount)} {currency}</div>
                    </div>
                    <div className="card p-3 text-center">
                        <CheckCircle size={24} className="text-success mb-2" />
                        <div className="small text-muted">محصّل</div>
                        <div className="fw-bold fs-4 text-success">{stats.collected.count}</div>
                        <div className="small text-muted">{formatNumber(stats.collected.amount)} {currency}</div>
                    </div>
                    <div className="card p-3 text-center">
                        <XCircle size={24} className="text-danger mb-2" />
                        <div className="small text-muted">مرتجع</div>
                        <div className="fw-bold fs-4 text-danger">{stats.bounced.count}</div>
                        <div className="small text-muted">{formatNumber(stats.bounced.amount)} {currency}</div>
                    </div>
                    <div className="card p-3 text-center">
                        <AlertTriangle size={24} className="text-danger mb-2" />
                        <div className="small text-muted">مستحق اليوم</div>
                        <div className="fw-bold fs-4 text-danger">{stats.overdue.count}</div>
                        <div className="small text-muted">{formatNumber(stats.overdue.amount)} {currency}</div>
                    </div>
                </div>
            )}

            {/* Filters */}
            <div className="card" style={{ padding: 16, display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 16 }}>
                <input className="form-input" placeholder="بحث برقم الشيك أو الساحب..." value={search}
                    onChange={e => setSearch(e.target.value)} style={{ maxWidth: 280 }} />
                <select className="form-input" value={statusFilter} onChange={e => setStatusFilter(e.target.value)} style={{ maxWidth: 160 }}>
                    <option value="">جميع الحالات</option>
                    <option value="pending">معلق</option>
                    <option value="collected">محصّل</option>
                    <option value="bounced">مرتجع</option>
                </select>
                <div style={{ marginRight: 'auto', fontWeight: 600, alignSelf: 'center' }}>الإجمالي: {total}</div>
            </div>

            {/* Table */}
            <div className="card card-flush" style={{ overflow: 'auto' }}>
                <table className="data-table">
                    <thead>
                        <tr>
                            <th>رقم الشيك</th>
                            <th>الساحب</th>
                            <th>البنك</th>
                            <th>المبلغ</th>
                            <th>تاريخ الاستحقاق</th>
                            <th>الحالة</th>
                        </tr>
                    </thead>
                    <tbody>
                        {items.length === 0 ? (
                            <tr><td colSpan="6" style={{ textAlign: 'center', padding: 40 }}>لا توجد شيكات</td></tr>
                        ) : items.map(item => (
                            <tr key={item.id} onClick={() => viewDetail(item.id)}
                                style={{ cursor: 'pointer', background: isOverdue(item.due_date, item.status) ? 'rgba(220,53,69,0.05)' : undefined }}>
                                <td style={{ fontWeight: 'bold' }}>{item.check_number}</td>
                                <td>{item.drawer_name || item.party_name || '—'}</td>
                                <td>{item.bank_name || '—'}</td>
                                <td style={{ fontWeight: 'bold' }}>{formatNumber(item.amount)} {currency}</td>
                                <td style={{ color: isOverdue(item.due_date, item.status) ? '#dc3545' : undefined, fontWeight: isOverdue(item.due_date, item.status) ? 'bold' : undefined }}>
                                    {formatShortDate(item.due_date)}
                                    {isOverdue(item.due_date, item.status) && ' ⚠️'}
                                </td>
                                <td>{statusBadge(item.status)}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Create Modal */}
            {showCreate && (
                <div className="modal-overlay" onClick={() => setShowCreate(false)}>
                    <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: 780, maxHeight: '90vh', overflow: 'auto' }}>
                        <div className="modal-header">
                            <h2>تسجيل شيك وارد</h2>
                            <button className="modal-close" onClick={() => setShowCreate(false)}>✕</button>
                        </div>
                        <div style={{ padding: 20 }}>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                                <div>
                                    <label className="form-label">رقم الشيك *</label>
                                    <input className="form-input" value={form.check_number} onChange={e => setForm(f => ({ ...f, check_number: e.target.value }))} />
                                </div>
                                <div>
                                    <label className="form-label">المبلغ *</label>
                                    <input className="form-input" type="number" min="0" step="0.01" value={form.amount} onChange={e => setForm(f => ({ ...f, amount: e.target.value }))} />
                                </div>
                                <div>
                                    <label className="form-label">اسم الساحب</label>
                                    <input className="form-input" value={form.drawer_name} onChange={e => setForm(f => ({ ...f, drawer_name: e.target.value }))} />
                                </div>
                                <div>
                                    <label className="form-label">البنك</label>
                                    <input className="form-input" value={form.bank_name} onChange={e => setForm(f => ({ ...f, bank_name: e.target.value }))} />
                                </div>
                                <div>
                                    <label className="form-label">تاريخ الإصدار</label>
                                    <DateInput className="form-input" value={form.issue_date} onChange={e => setForm(f => ({ ...f, issue_date: e.target.value }))} />
                                </div>
                                <div>
                                    <label className="form-label">تاريخ الاستحقاق *</label>
                                    <DateInput className="form-input" value={form.due_date} onChange={e => setForm(f => ({ ...f, due_date: e.target.value }))} />
                                </div>
                                <div>
                                    <label className="form-label">العميل</label>
                                    <select className="form-input" value={form.party_id} onChange={e => setForm(f => ({ ...f, party_id: e.target.value }))}>
                                        <option value="">اختر العميل</option>
                                        {customers.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                                    </select>
                                </div>
                                <div>
                                    <label className="form-label">حساب الخزينة</label>
                                    <select className="form-input" value={form.treasury_account_id} onChange={e => setForm(f => ({ ...f, treasury_account_id: e.target.value }))}>
                                        <option value="">اختر الخزينة</option>
                                        {treasuryAccounts.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
                                    </select>
                                </div>
                                <div style={{ gridColumn: '1 / -1' }}>
                                    <label className="form-label">ملاحظات</label>
                                    <input className="form-input" value={form.notes} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))} />
                                </div>
                            </div>
                            <div style={{ marginTop: 24, display: 'flex', gap: 12, justifyContent: 'flex-end' }}>
                                <button className="btn btn-secondary" onClick={() => setShowCreate(false)}>إلغاء</button>
                                <button className="btn btn-primary" onClick={handleCreate} disabled={saving}>
                                    {saving ? 'جاري الحفظ...' : 'تسجيل الشيك'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Detail Modal */}
            {showDetail && detailItem && (
                <div className="modal-overlay" onClick={() => setShowDetail(false)}>
                    <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: 700, maxHeight: '90vh', overflow: 'auto' }}>
                        <div className="modal-header">
                            <h2>شيك رقم: {detailItem.check_number}</h2>
                            <button className="modal-close" onClick={() => setShowDetail(false)}>✕</button>
                        </div>
                        <div style={{ padding: 20 }}>
                            <div className="metrics-grid" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', marginBottom: 20 }}>
                                <div className="metric-card"><div className="metric-label">المبلغ</div><div className="metric-value text-primary" style={{ fontSize: 20 }}>{formatNumber(detailItem.amount)} {currency}</div></div>
                                <div className="metric-card"><div className="metric-label">الحالة</div><div className="metric-value" style={{ fontSize: 16 }}>{statusBadge(detailItem.status)}</div></div>
                                <div className="metric-card"><div className="metric-label">الاستحقاق</div><div className="metric-value" style={{ fontSize: 14 }}>{formatShortDate(detailItem.due_date)}</div></div>
                            </div>

                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 20 }}>
                                <div><strong>الساحب:</strong> {detailItem.drawer_name || '—'}</div>
                                <div><strong>البنك:</strong> {detailItem.bank_name || '—'}</div>
                                <div><strong>العميل:</strong> {detailItem.party_name || '—'}</div>
                                <div><strong>الخزينة:</strong> {detailItem.treasury_name || '—'}</div>
                                <div><strong>تاريخ الإصدار:</strong> {detailItem.issue_date ? formatShortDate(detailItem.issue_date) : '—'}</div>
                                {detailItem.collection_date && <div><strong>تاريخ التحصيل:</strong> {formatShortDate(detailItem.collection_date)}</div>}
                                {detailItem.bounce_date && <div><strong>تاريخ الارتجاع:</strong> {formatShortDate(detailItem.bounce_date)}</div>}
                                {detailItem.bounce_reason && <div style={{ gridColumn: '1 / -1' }}><strong>سبب الارتجاع:</strong> {detailItem.bounce_reason}</div>}
                            </div>

                            {detailItem.notes && <p style={{ color: '#666', marginBottom: 16 }}>📝 {detailItem.notes}</p>}

                            {/* Actions */}
                            {detailItem.status === 'pending' && (
                                <div style={{ display: 'flex', gap: 12, marginTop: 20 }}>
                                    <button className="btn btn-primary" onClick={openCollect}>✅ تحصيل الشيك</button>
                                    <button className="btn" style={{ background: '#dc3545', color: '#fff' }} onClick={openBounce}>❌ شيك مرتجع</button>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* Collect Modal */}
            {showCollect && (
                <div className="modal-overlay" onClick={() => setShowCollect(false)}>
                    <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: 500 }}>
                        <div className="modal-header">
                            <h2>تحصيل الشيك</h2>
                            <button className="modal-close" onClick={() => setShowCollect(false)}>✕</button>
                        </div>
                        <div style={{ padding: 20 }}>
                            <div style={{ marginBottom: 16 }}>
                                <label className="form-label">تاريخ التحصيل</label>
                                <DateInput className="form-input" value={actionForm.collection_date}
                                    onChange={e => setActionForm(f => ({ ...f, collection_date: e.target.value }))} />
                            </div>
                            <div style={{ marginBottom: 16 }}>
                                <label className="form-label">حساب الخزينة (البنك)</label>
                                <select className="form-input" value={actionForm.treasury_account_id || ''}
                                    onChange={e => setActionForm(f => ({ ...f, treasury_account_id: e.target.value }))}>
                                    <option value="">اختر الخزينة</option>
                                    {treasuryAccounts.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
                                </select>
                            </div>
                            <div style={{ display: 'flex', gap: 12, justifyContent: 'flex-end' }}>
                                <button className="btn btn-secondary" onClick={() => setShowCollect(false)}>إلغاء</button>
                                <button className="btn btn-primary" onClick={handleCollect} disabled={saving}>
                                    {saving ? 'جاري...' : 'تأكيد التحصيل'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Bounce Modal */}
            {showBounce && (
                <div className="modal-overlay" onClick={() => setShowBounce(false)}>
                    <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: 500 }}>
                        <div className="modal-header">
                            <h2>تسجيل شيك مرتجع</h2>
                            <button className="modal-close" onClick={() => setShowBounce(false)}>✕</button>
                        </div>
                        <div style={{ padding: 20 }}>
                            <div style={{ marginBottom: 16 }}>
                                <label className="form-label">تاريخ الارتجاع</label>
                                <DateInput className="form-input" value={actionForm.bounce_date}
                                    onChange={e => setActionForm(f => ({ ...f, bounce_date: e.target.value }))} />
                            </div>
                            <div style={{ marginBottom: 16 }}>
                                <label className="form-label">سبب الارتجاع</label>
                                <textarea className="form-input" rows="3" value={actionForm.bounce_reason || ''}
                                    onChange={e => setActionForm(f => ({ ...f, bounce_reason: e.target.value }))}
                                    placeholder="رصيد غير كافٍ، توقيع غير مطابق..." />
                            </div>
                            <div style={{ display: 'flex', gap: 12, justifyContent: 'flex-end' }}>
                                <button className="btn btn-secondary" onClick={() => setShowBounce(false)}>إلغاء</button>
                                <button className="btn" style={{ background: '#dc3545', color: '#fff' }} onClick={handleBounce} disabled={saving}>
                                    {saving ? 'جاري...' : 'تأكيد الارتجاع'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}

export default ChecksReceivable
