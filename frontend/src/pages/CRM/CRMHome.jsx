import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { crmAPI, salesAPI } from '../../utils/api'
import { getCurrency } from '../../utils/auth'
import { formatNumber } from '../../utils/format'
import { formatShortDate } from '../../utils/dateUtils'
import '../../components/ModuleStyles.css'
import DateInput from '../../components/common/DateInput';
import { useToast } from '../../context/ToastContext'
import { getIndustryFeature } from '../../hooks/useIndustryType'

// ─── Stage / Status / Priority maps ───────────────────────────────────────────
const stageBadgeColors = {
    lead:        { background: '#3b82f6', color: '#fff' },
    qualified:   { background: '#eab308', color: '#fff' },
    proposal:    { background: '#f97316', color: '#fff' },
    negotiation: { background: '#8b5cf6', color: '#fff' },
    won:         { background: '#22c55e', color: '#fff' },
    lost:        { background: '#ef4444', color: '#fff' }
}
const stageColors = {
    lead: '#3b82f6', qualified: '#eab308', proposal: '#f97316', negotiation: '#8b5cf6'
}
const statusBadgeStyles = {
    open:        { background: '#3b82f6', color: '#fff' },
    in_progress: { background: '#eab308', color: '#fff' },
    resolved:    { background: '#22c55e', color: '#fff' },
    closed:      { background: '#6b7280', color: '#fff' }
}
const priorityBadgeStyles = {
    critical: { background: '#ef4444', color: '#fff' },
    high:     { background: '#f97316', color: '#fff' },
    medium:   { background: '#eab308', color: '#fff' },
    low:      { background: '#22c55e', color: '#fff' }
}
const detailPanelStyle = {
    background: 'var(--bg-secondary,#f9fafb)',
    padding: 20,
    borderTop: '2px solid var(--border-color,#e5e7eb)'
}
const commentStyle = (isInternal) => ({
    background: isInternal ? 'rgba(234,179,8,0.08)' : 'var(--bg-primary,#fff)',
    border: `1px solid ${isInternal ? '#eab308' : 'var(--border-color,#e5e7eb)'}`,
    borderRadius: 8,
    padding: 12
})

// ══════════════════════════════════════════════════════════════════════════════
function CRMHome() {
    const { t } = useTranslation()
  const { showToast } = useToast()
    const currency = getCurrency()
    const [activeTab, setActiveTab] = useState('overview')

    // ── Overview state ──────────────────────────────────────────────────────
    const [overviewLoading, setOverviewLoading] = useState(true)
    const [pipeline, setPipeline] = useState({ total_opportunities: 0, total_value: 0, stages: [] })
    const [ticketStats, setTicketStats] = useState({ open: 0, critical: 0 })

    // ── Opportunities state ─────────────────────────────────────────────────
    const [opportunities, setOpportunities] = useState([])
    const [oppLoading, setOppLoading] = useState(false)
    const [showOppModal, setShowOppModal] = useState(false)
    const [isOppEdit, setIsOppEdit] = useState(false)
    const [selectedOppId, setSelectedOppId] = useState(null)
    const [filterStage, setFilterStage] = useState('')
    const [deleteOppConfirm, setDeleteOppConfirm] = useState(null)
    const emptyOppForm = { title: '', customer_id: '', stage: 'lead', probability: 50, expected_value: 0, expected_close_date: '', source: '', notes: '' }
    const [oppForm, setOppForm] = useState({ ...emptyOppForm })

    // ── Support Tickets state ───────────────────────────────────────────────
    const [tickets, setTickets] = useState([])
    const [ticketsLoading, setTicketsLoading] = useState(false)
    const [showTicketModal, setShowTicketModal] = useState(false)
    const [filterStatus, setFilterStatus] = useState('')
    const [filterPriority, setFilterPriority] = useState('')
    const [expandedId, setExpandedId] = useState(null)
    const [ticketDetail, setTicketDetail] = useState(null)
    const [detailLoading, setDetailLoading] = useState(false)
    const [commentText, setCommentText] = useState('')
    const [isInternal, setIsInternal] = useState(false)
    const emptyTicketForm = { subject: '', description: '', customer_id: '', priority: 'medium', category: '', sla_hours: 24 }
    const [ticketForm, setTicketForm] = useState({ ...emptyTicketForm })

    // ── Shared ──────────────────────────────────────────────────────────────
    const [customers, setCustomers] = useState([])

    const stageOptions = [
        { value: 'lead',        label: t('crm.stage_lead') },
        { value: 'qualified',   label: t('crm.stage_qualified') },
        { value: 'proposal',    label: t('crm.stage_proposal') },
        { value: 'negotiation', label: t('crm.stage_negotiation') },
        { value: 'won',         label: t('crm.stage_won') },
        { value: 'lost',        label: t('crm.stage_lost') }
    ]
    const statusOptions = [
        { value: 'open',        label: t('crm.status_open') },
        { value: 'in_progress', label: t('crm.status_in_progress') },
        { value: 'resolved',    label: t('crm.status_resolved') },
        { value: 'closed',      label: t('crm.status_closed') }
    ]
    const priorityOptions = [
        { value: 'critical', label: t('crm.priority_critical') },
        { value: 'high',     label: t('crm.priority_high') },
        { value: 'medium',   label: t('crm.priority_medium') },
        { value: 'low',      label: t('crm.priority_low') }
    ]
    const stageLabels = {
        lead: t('crm.stage_lead'), qualified: t('crm.stage_qualified'),
        proposal: t('crm.stage_proposal'), negotiation: t('crm.stage_negotiation')
    }

    // ── Effects ─────────────────────────────────────────────────────────────
    useEffect(() => { fetchOverview(); fetchCustomers() }, [])
    useEffect(() => { if (activeTab === 'opportunities') fetchOpportunities() }, [activeTab, filterStage])
    useEffect(() => { if (activeTab === 'tickets') fetchTickets() }, [activeTab, filterStatus, filterPriority])

    // ── Fetch helpers ───────────────────────────────────────────────────────
    const fetchOverview = async () => {
        try {
            setOverviewLoading(true)
            const [pipelineRes, ticketRes] = await Promise.all([
                crmAPI.getPipelineSummary(),
                crmAPI.getTicketStats()
            ])
            const stagesData = pipelineRes.data?.pipeline || []
            setPipeline({
                total_opportunities: stagesData.reduce((sum, s) => sum + (parseInt(s.count) || 0), 0),
                total_value: stagesData.reduce((sum, s) => sum + (parseFloat(s.total_value) || 0), 0),
                stages: stagesData
            })
            setTicketStats({ open: ticketRes.data?.open_count ?? 0, critical: ticketRes.data?.critical_open ?? 0 })
        } catch (err) { console.error('Failed to fetch CRM overview', err) }
        finally { setOverviewLoading(false) }
    }
    const fetchCustomers = async () => {
        try { const res = await salesAPI.listCustomers(); setCustomers(res.data || []) }
        catch (err) { console.error(err) }
    }
    const fetchOpportunities = async () => {
        try {
            setOppLoading(true)
            const params = {}; if (filterStage) params.stage = filterStage
            const res = await crmAPI.listOpportunities(params); setOpportunities(res.data)
        } catch (err) { console.error(err) } finally { setOppLoading(false) }
    }
    const fetchTickets = async () => {
        try {
            setTicketsLoading(true)
            const params = {}
            if (filterStatus) params.status = filterStatus
            if (filterPriority) params.priority = filterPriority
            const res = await crmAPI.listTickets(params); setTickets(res.data)
        } catch (err) { console.error(err) } finally { setTicketsLoading(false) }
    }

    // ── Opportunity handlers ────────────────────────────────────────────────
    const openCreateOpp = () => { setOppForm({ ...emptyOppForm }); setIsOppEdit(false); setSelectedOppId(null); setShowOppModal(true) }
    const openEditOpp = (opp) => {
        setOppForm({ title: opp.title || '', customer_id: opp.customer_id || '', stage: opp.stage || 'lead', probability: opp.probability ?? 50, expected_value: opp.expected_value || 0, expected_close_date: opp.expected_close_date || '', source: opp.source || '', notes: opp.notes || '' })
        setIsOppEdit(true); setSelectedOppId(opp.id); setShowOppModal(true)
    }
    const handleOppSubmit = async (e) => {
        e.preventDefault()
        try {
            const payload = { ...oppForm, probability: Number(oppForm.probability), expected_value: Number(oppForm.expected_value), customer_id: oppForm.customer_id ? Number(oppForm.customer_id) : null }
            if (isOppEdit) { await crmAPI.updateOpportunity(selectedOppId, payload) } else { await crmAPI.createOpportunity(payload) }
            setShowOppModal(false); fetchOpportunities()
        } catch (err) { showToast(err.response?.data?.detail || t('crm.save_error', 'error')) }
    }
    const handleDeleteOpp = async (id) => {
        try { await crmAPI.deleteOpportunity(id); setDeleteOppConfirm(null); fetchOpportunities() }
        catch (err) { showToast(err.response?.data?.detail || t('crm.delete_error', 'error')) }
    }
    const getStageLabel = (stage) => { const opt = stageOptions.find(s => s.value === stage); return opt ? opt.label : stage }

    // ── Ticket handlers ─────────────────────────────────────────────────────
    const openCreateTicket = () => { setTicketForm({ ...emptyTicketForm }); setShowTicketModal(true) }
    const handleTicketSubmit = async (e) => {
        e.preventDefault()
        try {
            const payload = { ...ticketForm, customer_id: ticketForm.customer_id ? Number(ticketForm.customer_id) : null, sla_hours: Number(ticketForm.sla_hours) }
            await crmAPI.createTicket(payload); setShowTicketModal(false); fetchTickets()
        } catch (err) { showToast(err.response?.data?.detail || t('crm.create_error', 'error')) }
    }
    const toggleExpand = async (ticketId) => {
        if (expandedId === ticketId) { setExpandedId(null); setTicketDetail(null); return }
        try { setExpandedId(ticketId); setDetailLoading(true); const res = await crmAPI.getTicket(ticketId); setTicketDetail(res.data); setCommentText(''); setIsInternal(false) }
        catch (err) { console.error(err) } finally { setDetailLoading(false) }
    }
    const handleStatusChange = async (ticketId, newStatus) => {
        try {
            await crmAPI.updateTicket(ticketId, { status: newStatus }); fetchTickets()
            if (expandedId === ticketId) { const res = await crmAPI.getTicket(ticketId); setTicketDetail(res.data) }
        } catch (err) { console.error(err) }
    }
    const handleAddComment = async (e) => {
        e.preventDefault()
        if (!commentText.trim()) return
        try { await crmAPI.addComment(expandedId, { content: commentText, is_internal: isInternal }); const res = await crmAPI.getTicket(expandedId); setTicketDetail(res.data); setCommentText(''); setIsInternal(false) }
        catch (err) { showToast(err.response?.data?.detail || t('crm.comment_error', 'error')) }
    }
    const getStatusLabel = (status) => { const opt = statusOptions.find(s => s.value === status); return opt ? opt.label : status }
    const getPriorityLabel = (priority) => { const opt = priorityOptions.find(p => p.value === priority); return opt ? opt.label : priority }
    const formatDate = (dateStr) => { if (!dateStr) return '-'; try { return formatShortDate(dateStr) } catch { return dateStr } }

    // ── Render ──────────────────────────────────────────────────────────────
    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <h1 className="workspace-title">{t('crm.title')}</h1>
                <p className="workspace-subtitle">{t('crm.subtitle')}</p>
            </div>

            {/* Metrics */}
            <div className="metrics-grid">
                <div className="metric-card">
                    <div className="metric-label">{t('crm.total_opportunities')}</div>
                    <div className="metric-value text-primary">{overviewLoading ? '...' : pipeline.total_opportunities}</div>
                </div>
                <div className="metric-card">
                    <div className="metric-label">{t('crm.pipeline_value')}</div>
                    <div className="metric-value text-success">{overviewLoading ? '...' : formatNumber(pipeline.total_value)} <small>{currency}</small></div>
                </div>
                <div className="metric-card">
                    <div className="metric-label">{t('crm.open_tickets')}</div>
                    <div className="metric-value text-warning">{overviewLoading ? '...' : ticketStats.open}</div>
                </div>
                <div className="metric-card">
                    <div className="metric-label">{t('crm.critical_tickets')}</div>
                    <div className="metric-value text-danger">{overviewLoading ? '...' : ticketStats.critical}</div>
                </div>
            </div>

            {/* Grouped Navigation Cards */}
            <div className="modules-grid" style={{ gap: '16px', marginTop: '16px' }}>

                {/* Sales Activities */}
                <div className="card">
                    <h3 className="section-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        🤝 {t('crm.sales_activities', 'النشاطات التجارية')}
                    </h3>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginTop: '12px' }}>
                        <button className="btn btn-outline" onClick={() => setActiveTab('opportunities')} style={{ textAlign: 'center', fontSize: '13px', padding: '10px 8px' }}>
                            💼 {t('crm.tab_opportunities')}
                        </button>
                        <button className="btn btn-primary btn-sm" onClick={openCreateOpp} style={{ textAlign: 'center', fontSize: '13px', padding: '10px 8px' }}>
                            + {t('crm.new_opportunity')}
                        </button>
                    </div>
                </div>

                {/* Customer Support */}
                <div className="card">
                    <h3 className="section-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        🎧 {t('crm.customer_support', 'دعم العملاء')}
                    </h3>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginTop: '12px' }}>
                        <button className="btn btn-outline" onClick={() => setActiveTab('tickets')} style={{ textAlign: 'center', fontSize: '13px', padding: '10px 8px' }}>
                            🎫 {t('crm.tab_tickets')}
                        </button>
                        <button className="btn btn-primary btn-sm" onClick={openCreateTicket} style={{ textAlign: 'center', fontSize: '13px', padding: '10px 8px' }}>
                            + {t('crm.new_ticket')}
                        </button>
                    </div>
                </div>

                {/* Advanced CRM Tools */}
                <div className="card">
                    <h3 className="section-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        🔧 {t('crm.advanced_tools', 'الأدوات المتقدمة')}
                    </h3>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '8px', marginTop: '12px' }}>
                        <Link to="/crm/dashboard" className="btn btn-info btn-sm" style={{ textAlign: 'center' }}>
                            📊 {t('crm.dashboard_title', 'لوحة التحكم')}
                        </Link>
                        <Link to="/crm/lead-scoring" className="btn btn-info btn-sm" style={{ textAlign: 'center' }}>
                            ⭐ {t('crm.lead_scoring', 'تقييم العملاء')}
                        </Link>
                        <Link to="/crm/segments" className="btn btn-info btn-sm" style={{ textAlign: 'center' }}>
                            👥 {t('crm.customer_segments', 'شرائح العملاء')}
                        </Link>
                        <Link to="/crm/analytics" className="btn btn-info btn-sm" style={{ textAlign: 'center' }}>
                            📈 {t('crm.analytics', 'التحليلات')}
                        </Link>
                        <Link to="/crm/contacts" className="btn btn-info btn-sm" style={{ textAlign: 'center' }}>
                            📇 {t('crm.contacts', 'جهات الاتصال')}
                        </Link>
                        <Link to="/crm/forecasts" className="btn btn-info btn-sm" style={{ textAlign: 'center' }}>
                            🔮 {t('crm.sales_forecasts', 'التنبؤات')}
                        </Link>
                    </div>
                </div>

                {/* Marketing */}
                <div className="card">
                    <h3 className="section-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        📣 {t('crm.marketing', 'التسويق')}
                    </h3>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '8px', marginTop: '12px' }}>
                        {getIndustryFeature('crm.campaigns') && (
                            <Link to="/crm/campaigns" className="btn btn-outline" style={{ textAlign: 'center', fontSize: '13px', padding: '10px 8px' }}>
                                📣 {t('crm.campaigns.title', 'الحملات التسويقية')}
                            </Link>
                        )}
                        {getIndustryFeature('crm.knowledge_base') && (
                            <Link to="/crm/knowledge-base" className="btn btn-outline" style={{ textAlign: 'center', fontSize: '13px', padding: '10px 8px' }}>
                                📚 {t('crm.knowledge_base.title', 'قاعدة المعرفة')}
                            </Link>
                        )}
                    </div>
                </div>
            </div>

            {/* Tabs */}
            <div className="tabs mt-4">
                {['overview', 'opportunities', 'tickets'].map(tab => (
                    <button
                        key={tab}
                        className={`tab ${activeTab === tab ? 'active' : ''}`}
                        onClick={() => setActiveTab(tab)}
                    >
                        {tab === 'overview'      && t('crm.tab_overview')}
                        {tab === 'opportunities' && t('crm.tab_opportunities')}
                        {tab === 'tickets'       && t('crm.tab_tickets')}
                    </button>
                ))}
            </div>

            {/* ── Overview Tab ───────────────────────────────────────────────── */}
            {activeTab === 'overview' && (
                <div className="card mt-4">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                        <h3 className="section-title" style={{ margin: 0 }}>{t('crm.pipeline_summary')}</h3>
                    </div>
                    {overviewLoading ? (
                        <div className="empty-state">{t('common.loading')}</div>
                    ) : (
                        <div className="data-table-container">
                            <table className="data-table">
                                <thead>
                                    <tr>
                                        <th>{t('crm.stage')}</th>
                                        <th>{t('crm.opportunity_count')}</th>
                                        <th>{t('crm.value')}</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {(pipeline.stages || []).map(stage => (
                                        <tr key={stage.stage}>
                                            <td>
                                                <span className="badge" style={{ background: stageColors[stage.stage] || '#6b7280', color: '#fff' }}>
                                                    {stageLabels[stage.stage] || stage.stage}
                                                </span>
                                            </td>
                                            <td>{stage.count}</td>
                                            <td>{formatNumber(stage.total_value)} {currency}</td>
                                        </tr>
                                    ))}
                                    {(!pipeline.stages || pipeline.stages.length === 0) && (
                                        <tr><td colSpan={3} style={{ textAlign: 'center', padding: 20 }}>{t('common.no_data')}</td></tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    )}

                </div>
            )}

            {/* ── Opportunities Tab ───────────────────────────────────────────── */}
            {activeTab === 'opportunities' && (
                <div className="card mt-4">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                            <h3 className="section-title" style={{ margin: 0 }}>{t('crm.tab_opportunities')}</h3>
                            <select className="form-input" style={{ width: '180px' }} value={filterStage} onChange={e => setFilterStage(e.target.value)}>
                                <option value="">{t('crm.all_stages')}</option>
                                {stageOptions.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
                            </select>
                        </div>
                        <button className="btn btn-primary btn-sm" onClick={openCreateOpp}>+ {t('crm.new_opportunity')}</button>
                    </div>

                    {oppLoading ? (
                        <div className="empty-state">{t('common.loading')}</div>
                    ) : opportunities.length === 0 ? (
                        <div className="empty-state">{t('crm.no_opportunities')}</div>
                    ) : (
                        <div className="data-table-container">
                            <table className="data-table">
                                <thead>
                                    <tr>
                                        <th>{t('crm.title_label')}</th>
                                        <th>{t('common.customer')}</th>
                                        <th>{t('crm.stage')}</th>
                                        <th>{t('crm.probability')}</th>
                                        <th>{t('crm.expected_value')}</th>
                                        <th>{t('crm.expected_close')}</th>
                                        <th>{t('crm.responsible')}</th>
                                        <th>{t('common.actions')}</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {opportunities.map(opp => (
                                        <tr key={opp.id}>
                                            <td>{opp.title}</td>
                                            <td>{opp.customer_name || '-'}</td>
                                            <td><span className="badge" style={stageBadgeColors[opp.stage] || {}}>{getStageLabel(opp.stage)}</span></td>
                                            <td>{opp.probability}%</td>
                                            <td>{formatNumber(opp.expected_value)} {currency}</td>
                                            <td>{opp.expected_close_date || '-'}</td>
                                            <td>{opp.assigned_name || '-'}</td>
                                            <td>
                                                <div style={{ display: 'flex', gap: 6 }}>
                                                    <button className="btn btn-secondary btn-sm" onClick={() => openEditOpp(opp)}>{t('crm.edit')}</button>
                                                    <button className="btn btn-danger btn-sm" onClick={() => setDeleteOppConfirm(opp.id)}>{t('common.delete')}</button>
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}

                    {deleteOppConfirm && (
                        <div className="modal-backdrop" onClick={() => setDeleteOppConfirm(null)}>
                            <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: 420 }}>
                                <div className="modal-header"><h3>{t('crm.confirm_delete')}</h3></div>
                                <div className="modal-body"><p>{t('crm.confirm_delete_opportunity')}</p></div>
                                <div className="modal-footer">
                                    <button className="btn btn-danger" onClick={() => handleDeleteOpp(deleteOppConfirm)}>{t('common.delete')}</button>
                                    <button className="btn btn-secondary" onClick={() => setDeleteOppConfirm(null)}>{t('common.cancel')}</button>
                                </div>
                            </div>
                        </div>
                    )}

                    {showOppModal && (
                        <div className="modal-backdrop" onClick={() => setShowOppModal(false)}>
                            <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: 600 }}>
                                <div className="modal-header">
                                    <h3>{isOppEdit ? t('crm.edit_opportunity') : t('crm.new_opportunity')}</h3>
                                </div>
                                <div className="modal-body">
                                    <form id="opp-form" onSubmit={handleOppSubmit}>
                                        <div className="form-section">
                                            <div className="form-grid">
                                                <div className="form-group">
                                                    <label className="form-label">{t('crm.title_label')}</label>
                                                    <input type="text" className="form-input" value={oppForm.title} onChange={e => setOppForm(p => ({ ...p, title: e.target.value }))} required />
                                                </div>
                                                <div className="form-group">
                                                    <label className="form-label">{t('common.customer')}</label>
                                                    <select className="form-input" value={oppForm.customer_id} onChange={e => setOppForm(p => ({ ...p, customer_id: e.target.value }))}>
                                                        <option value="">{t('crm.select_customer')}</option>
                                                        {customers.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                                                    </select>
                                                </div>
                                                <div className="form-group">
                                                    <label className="form-label">{t('crm.stage')}</label>
                                                    <select className="form-input" value={oppForm.stage} onChange={e => setOppForm(p => ({ ...p, stage: e.target.value }))} required>
                                                        {stageOptions.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
                                                    </select>
                                                </div>
                                                <div className="form-group">
                                                    <label className="form-label">{t('crm.probability')} (%)</label>
                                                    <input type="number" className="form-input" min="0" max="100" value={oppForm.probability} onChange={e => setOppForm(p => ({ ...p, probability: e.target.value }))} />
                                                </div>
                                                <div className="form-group">
                                                    <label className="form-label">{t('crm.expected_value')}</label>
                                                    <input type="number" className="form-input" min="0" step="0.01" value={oppForm.expected_value} onChange={e => setOppForm(p => ({ ...p, expected_value: e.target.value }))} />
                                                </div>
                                                <div className="form-group">
                                                    <label className="form-label">{t('crm.expected_close')}</label>
                                                    <DateInput className="form-input" value={oppForm.expected_close_date} onChange={e => setOppForm(p => ({ ...p, expected_close_date: e.target.value }))} />
                                                </div>
                                                <div className="form-group">
                                                    <label className="form-label">{t('crm.source')}</label>
                                                    <input type="text" className="form-input" value={oppForm.source} onChange={e => setOppForm(p => ({ ...p, source: e.target.value }))} />
                                                </div>
                                                <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                                                    <label className="form-label">{t('common.notes')}</label>
                                                    <textarea className="form-input" rows={3} value={oppForm.notes} onChange={e => setOppForm(p => ({ ...p, notes: e.target.value }))} />
                                                </div>
                                            </div>
                                        </div>
                                    </form>
                                </div>
                                <div className="modal-footer">
                                    <button type="submit" form="opp-form" className="btn btn-primary">{isOppEdit ? t('common.update') : t('common.create')}</button>
                                    <button type="button" className="btn btn-secondary" onClick={() => setShowOppModal(false)}>{t('common.cancel')}</button>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* ── Support Tickets Tab ─────────────────────────────────────────── */}
            {activeTab === 'tickets' && (
                <div className="card mt-4">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                            <h3 className="section-title" style={{ margin: 0 }}>{t('crm.tab_tickets')}</h3>
                            <select className="form-input" style={{ width: '160px' }} value={filterStatus} onChange={e => setFilterStatus(e.target.value)}>
                                <option value="">{t('common.all_statuses')}</option>
                                {statusOptions.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
                            </select>
                            <select className="form-input" style={{ width: '150px' }} value={filterPriority} onChange={e => setFilterPriority(e.target.value)}>
                                <option value="">{t('crm.all_priorities')}</option>
                                {priorityOptions.map(p => <option key={p.value} value={p.value}>{p.label}</option>)}
                            </select>
                        </div>
                        <button className="btn btn-primary btn-sm" onClick={openCreateTicket}>+ {t('crm.new_ticket')}</button>
                    </div>

                    {ticketsLoading ? (
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
                                        <th>{t('common.status_title')}</th>
                                        <th>{t('crm.priority')}</th>
                                        <th>{t('crm.responsible')}</th>
                                        <th>{t('crm.created_date')}</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {tickets.map(ticket => (
                                        <>
                                            <tr key={ticket.id} onClick={() => toggleExpand(ticket.id)} style={{ cursor: 'pointer' }}>
                                                <td>{ticket.ticket_number}</td>
                                                <td>{ticket.subject}</td>
                                                <td>{ticket.customer_name || '-'}</td>
                                                <td><span className="badge" style={statusBadgeStyles[ticket.status] || {}}>{getStatusLabel(ticket.status)}</span></td>
                                                <td><span className="badge" style={priorityBadgeStyles[ticket.priority] || {}}>{getPriorityLabel(ticket.priority)}</span></td>
                                                <td>{ticket.assigned_name || '-'}</td>
                                                <td>{formatDate(ticket.created_at)}</td>
                                            </tr>
                                            {expandedId === ticket.id && (
                                                <tr key={`detail-${ticket.id}`}>
                                                    <td colSpan={7} style={{ padding: 0 }}>
                                                        <div style={detailPanelStyle}>
                                                            {detailLoading ? (
                                                                <div style={{ padding: 20, textAlign: 'center' }}>{t('common.loading')}</div>
                                                            ) : ticketDetail ? (
                                                                <>
                                                                    <div style={{ marginBottom: 16 }}>
                                                                        <h4 style={{ marginBottom: 8 }}>{t('crm.ticket_details')}</h4>
                                                                        <p><strong>{t('common.description')}:</strong> {ticketDetail.description || t('crm.no_description')}</p>
                                                                        <p><strong>{t('crm.category')}:</strong> {ticketDetail.category || '-'}</p>
                                                                        <p><strong>{t('crm.sla_hours')}:</strong> {ticketDetail.sla_hours || '-'}</p>
                                                                        <div style={{ marginTop: 8, display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
                                                                            <span>{t('crm.change_status')}:</span>
                                                                            {statusOptions.map(s => (
                                                                                <button
                                                                                    key={s.value}
                                                                                    className={`btn ${ticketDetail.status === s.value ? 'btn-primary' : 'btn-secondary'}`}
                                                                                    style={{ fontSize: 12, padding: '4px 10px' }}
                                                                                    onClick={e => { e.stopPropagation(); handleStatusChange(ticket.id, s.value) }}
                                                                                >{s.label}</button>
                                                                            ))}
                                                                        </div>
                                                                    </div>
                                                                    <div style={{ borderTop: '1px solid var(--border-color,#e5e7eb)', paddingTop: 12 }}>
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
                                                                                                {comment.is_internal && <span className="badge badge-warning" style={{ marginRight: 6, fontSize: 10 }}>{t('crm.internal')}</span>}
                                                                                            </span>
                                                                                        </div>
                                                                                        <p style={{ margin: 0 }}>{comment.content}</p>
                                                                                    </div>
                                                                                ))}
                                                                            </div>
                                                                        )}
                                                                        <form onSubmit={handleAddComment} style={{ marginTop: 8 }}>
                                                                            <div className="form-group">
                                                                                <textarea className="form-input" rows={3} placeholder={t('crm.add_comment_placeholder')} value={commentText} onChange={e => setCommentText(e.target.value)} required style={{ width: '100%' }} />
                                                                            </div>
                                                                            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: 8 }}>
                                                                                <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}>
                                                                                    <input type="checkbox" checked={isInternal} onChange={e => setIsInternal(e.target.checked)} />
                                                                                    {t('crm.internal_comment')}
                                                                                </label>
                                                                                <button type="submit" className="btn btn-primary" style={{ fontSize: 13, padding: '6px 16px' }}>{t('common.submit')}</button>
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

                    {showTicketModal && (
                        <div className="modal-backdrop" onClick={() => setShowTicketModal(false)}>
                            <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: 600 }}>
                                <div className="modal-header"><h3>{t('crm.new_ticket')}</h3></div>
                                <div className="modal-body">
                                    <form id="ticket-form" onSubmit={handleTicketSubmit}>
                                        <div className="form-section">
                                            <div className="form-grid">
                                                <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                                                    <label className="form-label">{t('crm.subject')}</label>
                                                    <input type="text" className="form-input" value={ticketForm.subject} onChange={e => setTicketForm(p => ({ ...p, subject: e.target.value }))} required />
                                                </div>
                                                <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                                                    <label className="form-label">{t('common.description')}</label>
                                                    <textarea className="form-input" rows={4} value={ticketForm.description} onChange={e => setTicketForm(p => ({ ...p, description: e.target.value }))} />
                                                </div>
                                                <div className="form-group">
                                                    <label className="form-label">{t('common.customer')}</label>
                                                    <select className="form-input" value={ticketForm.customer_id} onChange={e => setTicketForm(p => ({ ...p, customer_id: e.target.value }))}>
                                                        <option value="">{t('crm.select_customer')}</option>
                                                        {customers.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                                                    </select>
                                                </div>
                                                <div className="form-group">
                                                    <label className="form-label">{t('crm.priority')}</label>
                                                    <select className="form-input" value={ticketForm.priority} onChange={e => setTicketForm(p => ({ ...p, priority: e.target.value }))} required>
                                                        {priorityOptions.map(p => <option key={p.value} value={p.value}>{p.label}</option>)}
                                                    </select>
                                                </div>
                                                <div className="form-group">
                                                    <label className="form-label">{t('crm.category')}</label>
                                                    <input type="text" className="form-input" value={ticketForm.category} onChange={e => setTicketForm(p => ({ ...p, category: e.target.value }))} />
                                                </div>
                                                <div className="form-group">
                                                    <label className="form-label">{t('crm.sla_hours')}</label>
                                                    <input type="number" className="form-input" min="1" value={ticketForm.sla_hours} onChange={e => setTicketForm(p => ({ ...p, sla_hours: e.target.value }))} />
                                                </div>
                                            </div>
                                        </div>
                                    </form>
                                </div>
                                <div className="modal-footer">
                                    <button type="submit" form="ticket-form" className="btn btn-primary">{t('common.create')}</button>
                                    <button type="button" className="btn btn-secondary" onClick={() => setShowTicketModal(false)}>{t('common.cancel')}</button>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}

export default CRMHome
