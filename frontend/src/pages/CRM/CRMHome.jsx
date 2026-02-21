import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { crmAPI } from '../../utils/api'
import { getCurrency } from '../../utils/auth'
import { formatNumber } from '../../utils/format'
import '../../components/ModuleStyles.css'

function CRMHome() {
    const navigate = useNavigate()
    const currency = getCurrency()
    const [loading, setLoading] = useState(true)
    const [pipeline, setPipeline] = useState({ total_opportunities: 0, total_value: 0, stages: [] })
    const [ticketStats, setTicketStats] = useState({ open: 0, critical: 0 })

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true)
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
                setTicketStats({
                    open: ticketRes.data?.open_count ?? 0,
                    critical: ticketRes.data?.critical_open ?? 0
                })
            } catch (err) {
                console.error('Failed to fetch CRM data', err)
            } finally {
                setLoading(false)
            }
        }
        fetchData()
    }, [])

    const stageLabels = {
        lead: 'عميل محتمل',
        qualified: 'مؤهل',
        proposal: 'عرض سعر',
        negotiation: 'تفاوض'
    }

    const stageColors = {
        lead: '#3b82f6',
        qualified: '#eab308',
        proposal: '#f97316',
        negotiation: '#8b5cf6'
    }

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <h1 className="workspace-title">إدارة علاقات العملاء</h1>
                <p className="workspace-subtitle">متابعة الفرص البيعية وتذاكر الدعم الفني</p>
            </div>

            {/* Metrics */}
            <div className="metrics-grid">
                <div className="metric-card">
                    <div className="metric-label">إجمالي الفرص</div>
                    <div className="metric-value text-primary">
                        {loading ? '...' : pipeline.total_opportunities}
                    </div>
                </div>
                <div className="metric-card">
                    <div className="metric-label">قيمة خط الأنابيب</div>
                    <div className="metric-value text-success">
                        {loading ? '...' : formatNumber(pipeline.total_value)} <small>{currency}</small>
                    </div>
                </div>
                <div className="metric-card">
                    <div className="metric-label">تذاكر مفتوحة</div>
                    <div className="metric-value text-warning">
                        {loading ? '...' : ticketStats.open}
                    </div>
                </div>
                <div className="metric-card">
                    <div className="metric-label">تذاكر حرجة</div>
                    <div className="metric-value text-danger">
                        {loading ? '...' : ticketStats.critical}
                    </div>
                </div>
            </div>

            {/* Navigation Cards */}
            <div className="nav-grid" style={{ marginTop: 24 }}>
                <div className="nav-card" onClick={() => navigate('/crm/opportunities')}>
                    <div className="nav-icon">💼</div>
                    <div className="nav-title">الفرص البيعية</div>
                    <div className="nav-desc">إدارة ومتابعة الفرص البيعية وخط الأنابيب</div>
                </div>
                <div className="nav-card" onClick={() => navigate('/crm/tickets')}>
                    <div className="nav-icon">🎫</div>
                    <div className="nav-title">تذاكر الدعم</div>
                    <div className="nav-desc">متابعة تذاكر الدعم الفني وخدمة العملاء</div>
                </div>
            </div>

            {/* Pipeline Summary */}
            <div className="card section-card" style={{ marginTop: 24 }}>
                <h3 className="section-title">ملخص خط الأنابيب</h3>
                {loading ? (
                    <div className="empty-state">جاري التحميل...</div>
                ) : (
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>المرحلة</th>
                                <th>عدد الفرص</th>
                                <th>القيمة</th>
                            </tr>
                        </thead>
                        <tbody>
                            {(pipeline.stages || []).map(stage => (
                                <tr key={stage.stage}>
                                    <td>
                                        <span
                                            className="badge"
                                            style={{
                                                background: stageColors[stage.stage] || '#6b7280',
                                                color: '#fff'
                                            }}
                                        >
                                            {stageLabels[stage.stage] || stage.stage}
                                        </span>
                                    </td>
                                    <td>{stage.count}</td>
                                    <td>{formatNumber(stage.total_value)} {currency}</td>
                                </tr>
                            ))}
                            {(!pipeline.stages || pipeline.stages.length === 0) && (
                                <tr>
                                    <td colSpan={3} style={{ textAlign: 'center', padding: 20 }}>
                                        لا توجد بيانات
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                )}
            </div>
        </div>
    )
}

export default CRMHome
