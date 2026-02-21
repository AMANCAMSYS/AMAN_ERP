import { useState, useEffect } from 'react'
import { crmAPI, salesAPI } from '../../utils/api'
import { getCurrency } from '../../utils/auth'
import { formatNumber } from '../../utils/format'
import '../../components/ModuleStyles.css'

const stageOptions = [
    { value: 'lead', label: 'عميل محتمل' },
    { value: 'qualified', label: 'مؤهل' },
    { value: 'proposal', label: 'عرض سعر' },
    { value: 'negotiation', label: 'تفاوض' },
    { value: 'won', label: 'مكسوبة' },
    { value: 'lost', label: 'خاسرة' }
]

const stageBadgeStyles = {
    lead: 'badge-info',
    qualified: 'badge-warning',
    proposal: 'badge-warning',
    negotiation: 'badge-info',
    won: 'badge-success',
    lost: 'badge-danger'
}

const stageBadgeColors = {
    lead: { background: '#3b82f6', color: '#fff' },
    qualified: { background: '#eab308', color: '#fff' },
    proposal: { background: '#f97316', color: '#fff' },
    negotiation: { background: '#8b5cf6', color: '#fff' },
    won: { background: '#22c55e', color: '#fff' },
    lost: { background: '#ef4444', color: '#fff' }
}

function Opportunities() {
    const currency = getCurrency()
    const [opportunities, setOpportunities] = useState([])
    const [customers, setCustomers] = useState([])
    const [loading, setLoading] = useState(true)
    const [showModal, setShowModal] = useState(false)
    const [isEdit, setIsEdit] = useState(false)
    const [selectedId, setSelectedId] = useState(null)
    const [filterStage, setFilterStage] = useState('')
    const [deleteConfirm, setDeleteConfirm] = useState(null)

    const emptyForm = {
        title: '',
        customer_id: '',
        stage: 'lead',
        probability: 50,
        expected_value: 0,
        expected_close_date: '',
        source: '',
        notes: ''
    }
    const [formData, setFormData] = useState({ ...emptyForm })

    useEffect(() => {
        fetchOpportunities()
        fetchCustomers()
    }, [filterStage])

    const fetchOpportunities = async () => {
        try {
            setLoading(true)
            const params = {}
            if (filterStage) params.stage = filterStage
            const res = await crmAPI.listOpportunities(params)
            setOpportunities(res.data)
        } catch (err) {
            console.error('Failed to fetch opportunities', err)
        } finally {
            setLoading(false)
        }
    }

    const fetchCustomers = async () => {
        try {
            const res = await salesAPI.listCustomers()
            setCustomers(res.data || [])
        } catch (err) {
            console.error('Failed to fetch customers', err)
        }
    }

    const openCreate = () => {
        setFormData({ ...emptyForm })
        setIsEdit(false)
        setSelectedId(null)
        setShowModal(true)
    }

    const openEdit = (opp) => {
        setFormData({
            title: opp.title || '',
            customer_id: opp.customer_id || '',
            stage: opp.stage || 'lead',
            probability: opp.probability ?? 50,
            expected_value: opp.expected_value || 0,
            expected_close_date: opp.expected_close_date || '',
            source: opp.source || '',
            notes: opp.notes || ''
        })
        setIsEdit(true)
        setSelectedId(opp.id)
        setShowModal(true)
    }

    const handleChange = (e) => {
        const { name, value } = e.target
        setFormData(prev => ({ ...prev, [name]: value }))
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        try {
            const payload = {
                ...formData,
                probability: Number(formData.probability),
                expected_value: Number(formData.expected_value),
                customer_id: formData.customer_id ? Number(formData.customer_id) : null
            }
            if (isEdit) {
                await crmAPI.updateOpportunity(selectedId, payload)
            } else {
                await crmAPI.createOpportunity(payload)
            }
            setShowModal(false)
            fetchOpportunities()
        } catch (err) {
            console.error('Failed to save opportunity', err)
            alert(err.response?.data?.detail || 'حدث خطأ أثناء الحفظ')
        }
    }

    const handleDelete = async (id) => {
        try {
            await crmAPI.deleteOpportunity(id)
            setDeleteConfirm(null)
            fetchOpportunities()
        } catch (err) {
            console.error('Failed to delete opportunity', err)
            alert(err.response?.data?.detail || 'حدث خطأ أثناء الحذف')
        }
    }

    const getStageLabel = (stage) => {
        const opt = stageOptions.find(s => s.value === stage)
        return opt ? opt.label : stage
    }

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <h1 className="workspace-title">الفرص البيعية</h1>
                <p className="workspace-subtitle">إدارة ومتابعة فرص المبيعات</p>
            </div>

            {/* Toolbar */}
            <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: 16, flexWrap: 'wrap' }}>
                <button className="btn btn-primary" onClick={openCreate}>+ فرصة جديدة</button>
                <select
                    className="search-bar"
                    style={{ maxWidth: 200 }}
                    value={filterStage}
                    onChange={e => setFilterStage(e.target.value)}
                >
                    <option value="">جميع المراحل</option>
                    {stageOptions.map(s => (
                        <option key={s.value} value={s.value}>{s.label}</option>
                    ))}
                </select>
            </div>

            {/* Table */}
            {loading ? (
                <div className="empty-state">جاري التحميل...</div>
            ) : opportunities.length === 0 ? (
                <div className="empty-state">لا توجد فرص بيعية</div>
            ) : (
                <table className="data-table">
                    <thead>
                        <tr>
                            <th>العنوان</th>
                            <th>العميل</th>
                            <th>المرحلة</th>
                            <th>الاحتمالية</th>
                            <th>القيمة المتوقعة</th>
                            <th>تاريخ الإغلاق المتوقع</th>
                            <th>المسؤول</th>
                            <th>إجراءات</th>
                        </tr>
                    </thead>
                    <tbody>
                        {opportunities.map(opp => (
                            <tr key={opp.id}>
                                <td>{opp.title}</td>
                                <td>{opp.customer_name || '-'}</td>
                                <td>
                                    <span
                                        className="badge"
                                        style={stageBadgeColors[opp.stage] || {}}
                                    >
                                        {getStageLabel(opp.stage)}
                                    </span>
                                </td>
                                <td>{opp.probability}%</td>
                                <td>{formatNumber(opp.expected_value)} {currency}</td>
                                <td>{opp.expected_close_date || '-'}</td>
                                <td>{opp.assigned_name || '-'}</td>
                                <td>
                                    <div style={{ display: 'flex', gap: 6 }}>
                                        <button className="btn btn-secondary" onClick={() => openEdit(opp)}>تعديل</button>
                                        <button className="btn btn-danger" onClick={() => setDeleteConfirm(opp.id)}>حذف</button>
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            )}

            {/* Delete Confirmation */}
            {deleteConfirm && (
                <div className="modal-overlay" style={overlayStyle}>
                    <div className="card" style={modalBoxStyle}>
                        <h3 style={{ marginBottom: 16 }}>تأكيد الحذف</h3>
                        <p>هل أنت متأكد من حذف هذه الفرصة البيعية؟</p>
                        <div className="form-actions" style={{ marginTop: 16 }}>
                            <button className="btn btn-danger" onClick={() => handleDelete(deleteConfirm)}>حذف</button>
                            <button className="btn btn-secondary" onClick={() => setDeleteConfirm(null)}>إلغاء</button>
                        </div>
                    </div>
                </div>
            )}

            {/* Create/Edit Modal */}
            {showModal && (
                <div className="modal-overlay" style={overlayStyle}>
                    <div className="card" style={{ ...modalBoxStyle, maxWidth: 600 }}>
                        <h3 style={{ marginBottom: 16 }}>{isEdit ? 'تعديل الفرصة' : 'فرصة جديدة'}</h3>
                        <form onSubmit={handleSubmit}>
                            <div className="form-section">
                                <div className="form-grid">
                                    <div className="form-group">
                                        <label>العنوان</label>
                                        <input
                                            type="text"
                                            name="title"
                                            value={formData.title}
                                            onChange={handleChange}
                                            required
                                        />
                                    </div>
                                    <div className="form-group">
                                        <label>العميل</label>
                                        <select name="customer_id" value={formData.customer_id} onChange={handleChange}>
                                            <option value="">-- اختر العميل --</option>
                                            {customers.map(c => (
                                                <option key={c.id} value={c.id}>{c.name}</option>
                                            ))}
                                        </select>
                                    </div>
                                    <div className="form-group">
                                        <label>المرحلة</label>
                                        <select name="stage" value={formData.stage} onChange={handleChange} required>
                                            {stageOptions.map(s => (
                                                <option key={s.value} value={s.value}>{s.label}</option>
                                            ))}
                                        </select>
                                    </div>
                                    <div className="form-group">
                                        <label>الاحتمالية (%)</label>
                                        <input
                                            type="number"
                                            name="probability"
                                            min="0"
                                            max="100"
                                            value={formData.probability}
                                            onChange={handleChange}
                                        />
                                    </div>
                                    <div className="form-group">
                                        <label>القيمة المتوقعة</label>
                                        <input
                                            type="number"
                                            name="expected_value"
                                            min="0"
                                            step="0.01"
                                            value={formData.expected_value}
                                            onChange={handleChange}
                                        />
                                    </div>
                                    <div className="form-group">
                                        <label>تاريخ الإغلاق المتوقع</label>
                                        <input
                                            type="date"
                                            name="expected_close_date"
                                            value={formData.expected_close_date}
                                            onChange={handleChange}
                                        />
                                    </div>
                                    <div className="form-group">
                                        <label>المصدر</label>
                                        <input
                                            type="text"
                                            name="source"
                                            value={formData.source}
                                            onChange={handleChange}
                                        />
                                    </div>
                                    <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                                        <label>ملاحظات</label>
                                        <textarea
                                            name="notes"
                                            rows={3}
                                            value={formData.notes}
                                            onChange={handleChange}
                                        />
                                    </div>
                                </div>
                            </div>
                            <div className="form-actions" style={{ marginTop: 16 }}>
                                <button type="submit" className="btn btn-primary">
                                    {isEdit ? 'تحديث' : 'إنشاء'}
                                </button>
                                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>
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

const overlayStyle = {
    position: 'fixed',
    inset: 0,
    background: 'rgba(0,0,0,0.5)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000
}

const modalBoxStyle = {
    background: 'var(--bg-primary, #fff)',
    borderRadius: 12,
    padding: 24,
    width: '90%',
    maxWidth: 480,
    maxHeight: '90vh',
    overflowY: 'auto'
}

export default Opportunities
