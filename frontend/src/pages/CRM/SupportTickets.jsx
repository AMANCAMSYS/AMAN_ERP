import { useState, useEffect } from 'react'
import { crmAPI, salesAPI } from '../../utils/api'
import '../../components/ModuleStyles.css'
import { formatShortDate } from '../../utils/dateUtils';


const statusOptions = [
    { value: 'open', label: 'مفتوحة' },
    { value: 'in_progress', label: 'قيد المعالجة' },
    { value: 'resolved', label: 'تم الحل' },
    { value: 'closed', label: 'مغلقة' }
]

const priorityOptions = [
    { value: 'critical', label: 'حرجة' },
    { value: 'high', label: 'عالية' },
    { value: 'medium', label: 'متوسطة' },
    { value: 'low', label: 'منخفضة' }
]

const statusBadgeStyles = {
    open: { background: '#3b82f6', color: '#fff' },
    in_progress: { background: '#eab308', color: '#fff' },
    resolved: { background: '#22c55e', color: '#fff' },
    closed: { background: '#6b7280', color: '#fff' }
}

const priorityBadgeStyles = {
    critical: { background: '#ef4444', color: '#fff' },
    high: { background: '#f97316', color: '#fff' },
    medium: { background: '#eab308', color: '#fff' },
    low: { background: '#22c55e', color: '#fff' }
}

function SupportTickets() {
    const [tickets, setTickets] = useState([])
    const [customers, setCustomers] = useState([])
    const [loading, setLoading] = useState(true)
    const [showModal, setShowModal] = useState(false)
    const [filterStatus, setFilterStatus] = useState('')
    const [filterPriority, setFilterPriority] = useState('')

    // Expanded ticket detail
    const [expandedId, setExpandedId] = useState(null)
    const [ticketDetail, setTicketDetail] = useState(null)
    const [detailLoading, setDetailLoading] = useState(false)

    // Comment form
    const [commentText, setCommentText] = useState('')
    const [isInternal, setIsInternal] = useState(false)

    const emptyForm = {
        subject: '',
        description: '',
        customer_id: '',
        priority: 'medium',
        category: '',
        sla_hours: 24
    }
    const [formData, setFormData] = useState({ ...emptyForm })

    useEffect(() => {
        fetchTickets()
        fetchCustomers()
    }, [filterStatus, filterPriority])

    const fetchTickets = async () => {
        try {
            setLoading(true)
            const params = {}
            if (filterStatus) params.status = filterStatus
            if (filterPriority) params.priority = filterPriority
            const res = await crmAPI.listTickets(params)
            setTickets(res.data)
        } catch (err) {
            console.error('Failed to fetch tickets', err)
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
                customer_id: formData.customer_id ? Number(formData.customer_id) : null,
                sla_hours: Number(formData.sla_hours)
            }
            await crmAPI.createTicket(payload)
            setShowModal(false)
            fetchTickets()
        } catch (err) {
            console.error('Failed to create ticket', err)
            alert(err.response?.data?.detail || 'حدث خطأ أثناء الإنشاء')
        }
    }

    const toggleExpand = async (ticketId) => {
        if (expandedId === ticketId) {
            setExpandedId(null)
            setTicketDetail(null)
            return
        }
        try {
            setExpandedId(ticketId)
            setDetailLoading(true)
            const res = await crmAPI.getTicket(ticketId)
            setTicketDetail(res.data)
            setCommentText('')
            setIsInternal(false)
        } catch (err) {
            console.error('Failed to fetch ticket details', err)
        } finally {
            setDetailLoading(false)
        }
    }

    const handleStatusChange = async (ticketId, newStatus) => {
        try {
            await crmAPI.updateTicket(ticketId, { status: newStatus })
            fetchTickets()
            if (expandedId === ticketId) {
                const res = await crmAPI.getTicket(ticketId)
                setTicketDetail(res.data)
            }
        } catch (err) {
            console.error('Failed to update ticket', err)
        }
    }

    const handleAddComment = async (e) => {
        e.preventDefault()
        if (!commentText.trim()) return
        try {
            await crmAPI.addComment(expandedId, {
                content: commentText,
                is_internal: isInternal
            })
            const res = await crmAPI.getTicket(expandedId)
            setTicketDetail(res.data)
            setCommentText('')
            setIsInternal(false)
        } catch (err) {
            console.error('Failed to add comment', err)
            alert(err.response?.data?.detail || 'حدث خطأ أثناء إضافة التعليق')
        }
    }

    const getStatusLabel = (status) => {
        const opt = statusOptions.find(s => s.value === status)
        return opt ? opt.label : status
    }

    const getPriorityLabel = (priority) => {
        const opt = priorityOptions.find(p => p.value === priority)
        return opt ? opt.label : priority
    }

    const formatDate = (dateStr) => {
        if (!dateStr) return '-'
        try {
            return formatShortDate(dateStr)
        } catch {
            return dateStr
        }
    }

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <h1 className="workspace-title">تذاكر الدعم</h1>
                <p className="workspace-subtitle">إدارة ومتابعة تذاكر الدعم الفني وخدمة العملاء</p>
            </div>

            {/* Toolbar */}
            <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: 16, flexWrap: 'wrap' }}>
                <button className="btn btn-primary" onClick={openCreate}>+ تذكرة جديدة</button>
                <select
                    className="search-bar"
                    style={{ maxWidth: 180 }}
                    value={filterStatus}
                    onChange={e => setFilterStatus(e.target.value)}
                >
                    <option value="">جميع الحالات</option>
                    {statusOptions.map(s => (
                        <option key={s.value} value={s.value}>{s.label}</option>
                    ))}
                </select>
                <select
                    className="search-bar"
                    style={{ maxWidth: 180 }}
                    value={filterPriority}
                    onChange={e => setFilterPriority(e.target.value)}
                >
                    <option value="">جميع الأولويات</option>
                    {priorityOptions.map(p => (
                        <option key={p.value} value={p.value}>{p.label}</option>
                    ))}
                </select>
            </div>

            {/* Table */}
            {loading ? (
                <div className="empty-state">جاري التحميل...</div>
            ) : tickets.length === 0 ? (
                <div className="empty-state">لا توجد تذاكر</div>
            ) : (
                <table className="data-table">
                    <thead>
                        <tr>
                            <th>رقم التذكرة</th>
                            <th>الموضوع</th>
                            <th>العميل</th>
                            <th>الحالة</th>
                            <th>الأولوية</th>
                            <th>المسؤول</th>
                            <th>تاريخ الإنشاء</th>
                        </tr>
                    </thead>
                    <tbody>
                        {tickets.map(ticket => (
                            <>
                                <tr
                                    key={ticket.id}
                                    onClick={() => toggleExpand(ticket.id)}
                                    style={{ cursor: 'pointer' }}
                                >
                                    <td>{ticket.ticket_number}</td>
                                    <td>{ticket.subject}</td>
                                    <td>{ticket.customer_name || '-'}</td>
                                    <td>
                                        <span className="badge" style={statusBadgeStyles[ticket.status] || {}}>
                                            {getStatusLabel(ticket.status)}
                                        </span>
                                    </td>
                                    <td>
                                        <span className="badge" style={priorityBadgeStyles[ticket.priority] || {}}>
                                            {getPriorityLabel(ticket.priority)}
                                        </span>
                                    </td>
                                    <td>{ticket.assigned_name || '-'}</td>
                                    <td>{formatDate(ticket.created_at)}</td>
                                </tr>

                                {/* Expanded Detail Row */}
                                {expandedId === ticket.id && (
                                    <tr key={`detail-${ticket.id}`}>
                                        <td colSpan={7} style={{ padding: 0 }}>
                                            <div style={detailPanelStyle}>
                                                {detailLoading ? (
                                                    <div style={{ padding: 20, textAlign: 'center' }}>جاري التحميل...</div>
                                                ) : ticketDetail ? (
                                                    <>
                                                        {/* Ticket Info */}
                                                        <div style={{ marginBottom: 16 }}>
                                                            <h4 style={{ marginBottom: 8 }}>تفاصيل التذكرة</h4>
                                                            <p><strong>الوصف:</strong> {ticketDetail.description || 'لا يوجد وصف'}</p>
                                                            <p><strong>الفئة:</strong> {ticketDetail.category || '-'}</p>
                                                            <p><strong>SLA (ساعات):</strong> {ticketDetail.sla_hours || '-'}</p>
                                                            <div style={{ marginTop: 8, display: 'flex', gap: 8, alignItems: 'center' }}>
                                                                <span>تغيير الحالة:</span>
                                                                {statusOptions.map(s => (
                                                                    <button
                                                                        key={s.value}
                                                                        className={`btn ${ticketDetail.status === s.value ? 'btn-primary' : 'btn-secondary'}`}
                                                                        style={{ fontSize: 12, padding: '4px 10px' }}
                                                                        onClick={(e) => {
                                                                            e.stopPropagation()
                                                                            handleStatusChange(ticket.id, s.value)
                                                                        }}
                                                                    >
                                                                        {s.label}
                                                                    </button>
                                                                ))}
                                                            </div>
                                                        </div>

                                                        {/* Comments */}
                                                        <div style={{ borderTop: '1px solid var(--border-color, #e5e7eb)', paddingTop: 12 }}>
                                                            <h4 style={{ marginBottom: 8 }}>التعليقات ({(ticketDetail.comments || []).length})</h4>
                                                            {(ticketDetail.comments || []).length === 0 ? (
                                                                <p style={{ color: '#9ca3af' }}>لا توجد تعليقات بعد</p>
                                                            ) : (
                                                                <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 12 }}>
                                                                    {ticketDetail.comments.map((comment, idx) => (
                                                                        <div key={idx} style={commentStyle(comment.is_internal)}>
                                                                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                                                                                <strong>{comment.user_name || 'مستخدم'}</strong>
                                                                                <span style={{ fontSize: 12, color: '#9ca3af' }}>
                                                                                    {formatDate(comment.created_at)}
                                                                                    {comment.is_internal && (
                                                                                        <span className="badge badge-warning" style={{ marginRight: 6, fontSize: 10 }}>داخلي</span>
                                                                                    )}
                                                                                </span>
                                                                            </div>
                                                                            <p style={{ margin: 0 }}>{comment.content}</p>
                                                                        </div>
                                                                    ))}
                                                                </div>
                                                            )}

                                                            {/* Add Comment Form */}
                                                            <form onSubmit={handleAddComment} style={{ marginTop: 8 }}>
                                                                <div className="form-group">
                                                                    <textarea
                                                                        rows={3}
                                                                        placeholder="أضف تعليقاً..."
                                                                        value={commentText}
                                                                        onChange={e => setCommentText(e.target.value)}
                                                                        required
                                                                        style={{ width: '100%' }}
                                                                    />
                                                                </div>
                                                                <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: 8 }}>
                                                                    <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}>
                                                                        <input
                                                                            type="checkbox"
                                                                            checked={isInternal}
                                                                            onChange={e => setIsInternal(e.target.checked)}
                                                                        />
                                                                        تعليق داخلي
                                                                    </label>
                                                                    <button type="submit" className="btn btn-primary" style={{ fontSize: 13, padding: '6px 16px' }}>
                                                                        إرسال
                                                                    </button>
                                                                </div>
                                                            </form>
                                                        </div>
                                                    </>
                                                ) : null}
                                            </div>
                                        </td>
                                    </tr>
                                )}
                            </>
                        ))}
                    </tbody>
                </table>
            )}

            {/* Create Modal */}
            {showModal && (
                <div style={overlayStyle}>
                    <div className="card" style={modalBoxStyle}>
                        <h3 style={{ marginBottom: 16 }}>تذكرة جديدة</h3>
                        <form onSubmit={handleSubmit}>
                            <div className="form-section">
                                <div className="form-grid">
                                    <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                                        <label>الموضوع</label>
                                        <input
                                            type="text"
                                            name="subject"
                                            value={formData.subject}
                                            onChange={handleChange}
                                            required
                                        />
                                    </div>
                                    <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                                        <label>الوصف</label>
                                        <textarea
                                            name="description"
                                            rows={4}
                                            value={formData.description}
                                            onChange={handleChange}
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
                                        <label>الأولوية</label>
                                        <select name="priority" value={formData.priority} onChange={handleChange} required>
                                            {priorityOptions.map(p => (
                                                <option key={p.value} value={p.value}>{p.label}</option>
                                            ))}
                                        </select>
                                    </div>
                                    <div className="form-group">
                                        <label>الفئة</label>
                                        <input
                                            type="text"
                                            name="category"
                                            value={formData.category}
                                            onChange={handleChange}
                                        />
                                    </div>
                                    <div className="form-group">
                                        <label>SLA (ساعات)</label>
                                        <input
                                            type="number"
                                            name="sla_hours"
                                            min="1"
                                            value={formData.sla_hours}
                                            onChange={handleChange}
                                        />
                                    </div>
                                </div>
                            </div>
                            <div className="form-actions" style={{ marginTop: 16 }}>
                                <button type="submit" className="btn btn-primary">إنشاء</button>
                                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>إلغاء</button>
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
    maxWidth: 600,
    maxHeight: '90vh',
    overflowY: 'auto'
}

const detailPanelStyle = {
    background: 'var(--bg-secondary, #f9fafb)',
    padding: 20,
    borderTop: '2px solid var(--border-color, #e5e7eb)'
}

const commentStyle = (isInternal) => ({
    background: isInternal ? 'rgba(234, 179, 8, 0.08)' : 'var(--bg-primary, #fff)',
    border: `1px solid ${isInternal ? '#eab308' : 'var(--border-color, #e5e7eb)'}`,
    borderRadius: 8,
    padding: 12
})

export default SupportTickets
