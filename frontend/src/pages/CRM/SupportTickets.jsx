import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { crmAPI, salesAPI } from '../../utils/api'
import '../../components/ModuleStyles.css'
import { formatShortDate } from '../../utils/dateUtils';


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
    const { t } = useTranslation()

    const statusOptions = [
        { value: 'open', label: t('crm.status_open') },
        { value: 'in_progress', label: t('crm.status_in_progress') },
        { value: 'resolved', label: t('crm.status_resolved') },
        { value: 'closed', label: t('crm.status_closed') }
    ]

    const priorityOptions = [
        { value: 'critical', label: t('crm.priority_critical') },
        { value: 'high', label: t('crm.priority_high') },
        { value: 'medium', label: t('crm.priority_medium') },
        { value: 'low', label: t('crm.priority_low') }
    ]

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
            alert(err.response?.data?.detail || t('crm.create_error'))
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
            alert(err.response?.data?.detail || t('crm.comment_error'))
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
                <h1 className="workspace-title">{t('crm.tickets_title')}</h1>
                <p className="workspace-subtitle">{t('crm.tickets_desc')}</p>
            </div>

            {/* Toolbar */}
            <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: 16, flexWrap: 'wrap' }}>
                <button className="btn btn-primary" onClick={openCreate}>+ {t('crm.new_ticket')}</button>
                <select
                    className="search-bar"
                    style={{ maxWidth: 180 }}
                    value={filterStatus}
                    onChange={e => setFilterStatus(e.target.value)}
                >
                    <option value="">{t('common.all_statuses')}</option>
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
                    <option value="">{t('crm.all_priorities')}</option>
                    {priorityOptions.map(p => (
                        <option key={p.value} value={p.value}>{p.label}</option>
                    ))}
                </select>
            </div>

            {/* Table */}
            {loading ? (
                <div className="empty-state">{t('common.loading')}</div>
            ) : tickets.length === 0 ? (
                <div className="empty-state">{t('crm.no_tickets')}</div>
            ) : (
                <div className="data-table-container">
                <table className="data-table">
                    <thead>
                        <tr>
                            <th>{t('crm.ticket_number')}</th>
                            <th>{t('crm.subject')}</th>
                            <th>{t('common.customer')}</th>
                            <th>{t('common.status')}</th>
                            <th>{t('crm.priority')}</th>
                            <th>{t('crm.responsible')}</th>
                            <th>{t('crm.created_date')}</th>
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
                                                    <div style={{ padding: 20, textAlign: 'center' }}>{t('common.loading')}</div>
                                                ) : ticketDetail ? (
                                                    <>
                                                        {/* Ticket Info */}
                                                        <div style={{ marginBottom: 16 }}>
                                                            <h4 style={{ marginBottom: 8 }}>{t('crm.ticket_details')}</h4>
                                                            <p><strong>{t('common.description')}:</strong> {ticketDetail.description || t('crm.no_description')}</p>
                                                            <p><strong>{t('crm.category')}:</strong> {ticketDetail.category || '-'}</p>
                                                            <p><strong>{t('crm.sla_hours')}:</strong> {ticketDetail.sla_hours || '-'}</p>
                                                            <div style={{ marginTop: 8, display: 'flex', gap: 8, alignItems: 'center' }}>
                                                                <span>{t('crm.change_status')}:</span>
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
                                                            <h4 style={{ marginBottom: 8 }}>{t('crm.comments')} ({(ticketDetail.comments || []).length})</h4>
                                                            {(ticketDetail.comments || []).length === 0 ? (
                                                                <p style={{ color: '#9ca3af' }}>{t('crm.no_comments')}</p>
                                                            ) : (
                                                                <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 12 }}>
                                                                    {ticketDetail.comments.map((comment, idx) => (
                                                                        <div key={idx} style={commentStyle(comment.is_internal)}>
                                                                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                                                                                <strong>{comment.user_name || t('crm.user')}</strong>
                                                                                <span style={{ fontSize: 12, color: '#9ca3af' }}>
                                                                                    {formatDate(comment.created_at)}
                                                                                    {comment.is_internal && (
                                                                                        <span className="badge badge-warning" style={{ marginRight: 6, fontSize: 10 }}>{t('crm.internal')}</span>
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
                                                                        placeholder={t('crm.add_comment_placeholder')}
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
                                                                        {t('crm.internal_comment')}
                                                                    </label>
                                                                    <button type="submit" className="btn btn-primary" style={{ fontSize: 13, padding: '6px 16px' }}>
                                                                        {t('common.submit')}
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
                </div>
            )}

            {/* Create Modal */}
            {showModal && (
                <div className="modal-backdrop" onClick={() => setShowModal(false)}>
                    <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: 600 }}>
                        <div className="modal-header">
                            <h3>{t('crm.new_ticket')}</h3>
                        </div>
                        <div className="modal-body">
                            <form id="ticket-form" onSubmit={handleSubmit}>
                                <div className="form-section">
                                    <div className="form-grid">
                                        <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                                            <label className="form-label">{t('crm.subject')}</label>
                                            <input
                                                type="text"
                                                name="subject"
                                                className="form-control"
                                                value={formData.subject}
                                                onChange={handleChange}
                                                required
                                            />
                                        </div>
                                        <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                                            <label className="form-label">{t('common.description')}</label>
                                            <textarea
                                                name="description"
                                                className="form-control"
                                                rows={4}
                                                value={formData.description}
                                                onChange={handleChange}
                                            />
                                        </div>
                                        <div className="form-group">
                                            <label className="form-label">{t('common.customer')}</label>
                                            <select className="form-control" name="customer_id" value={formData.customer_id} onChange={handleChange}>
                                                <option value="">{t('crm.select_customer')}</option>
                                                {customers.map(c => (
                                                    <option key={c.id} value={c.id}>{c.name}</option>
                                                ))}
                                            </select>
                                        </div>
                                        <div className="form-group">
                                            <label className="form-label">{t('crm.priority')}</label>
                                            <select className="form-control" name="priority" value={formData.priority} onChange={handleChange} required>
                                                {priorityOptions.map(p => (
                                                    <option key={p.value} value={p.value}>{p.label}</option>
                                                ))}
                                            </select>
                                        </div>
                                        <div className="form-group">
                                            <label className="form-label">{t('crm.category')}</label>
                                            <input
                                                type="text"
                                                name="category"
                                                className="form-control"
                                                value={formData.category}
                                                onChange={handleChange}
                                            />
                                        </div>
                                        <div className="form-group">
                                            <label className="form-label">{t('crm.sla_hours')}</label>
                                            <input
                                                type="number"
                                                name="sla_hours"
                                                className="form-control"
                                                min="1"
                                                value={formData.sla_hours}
                                                onChange={handleChange}
                                            />
                                        </div>
                                    </div>
                                </div>
                            </form>
                        </div>
                        <div className="modal-footer">
                            <button type="submit" form="ticket-form" className="btn btn-primary">{t('common.create')}</button>
                            <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>{t('common.cancel')}</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
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
