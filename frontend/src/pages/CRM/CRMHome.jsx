import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { crmAPI } from '../../utils/api'
import { getCurrency } from '../../utils/auth'
import { formatNumber } from '../../utils/format'
import '../../components/ModuleStyles.css'

function CRMHome() {
    const { t, i18n } = useTranslation()
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
        lead: t('crm.stage_lead'),
        qualified: t('crm.stage_qualified'),
        proposal: t('crm.stage_proposal'),
        negotiation: t('crm.stage_negotiation')
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
                <h1 className="workspace-title">{t('crm.title')}</h1>
                <p className="workspace-subtitle">{t('crm.subtitle')}</p>
            </div>

            {/* Metrics */}
            <div className="metrics-grid">
                <div className="metric-card">
                    <div className="metric-label">{t('crm.total_opportunities')}</div>
                    <div className="metric-value text-primary">
                        {loading ? '...' : pipeline.total_opportunities}
                    </div>
                </div>
                <div className="metric-card">
                    <div className="metric-label">{t('crm.pipeline_value')}</div>
                    <div className="metric-value text-success">
                        {loading ? '...' : formatNumber(pipeline.total_value)} <small>{currency}</small>
                    </div>
                </div>
                <div className="metric-card">
                    <div className="metric-label">{t('crm.open_tickets')}</div>
                    <div className="metric-value text-warning">
                        {loading ? '...' : ticketStats.open}
                    </div>
                </div>
                <div className="metric-card">
                    <div className="metric-label">{t('crm.critical_tickets')}</div>
                    <div className="metric-value text-danger">
                        {loading ? '...' : ticketStats.critical}
                    </div>
                </div>
            </div>

            {/* Navigation */}
            <div className="modules-grid">
                <div className="card section-card">
                    <h3 className="section-title">{t('crm.opportunities')}</h3>
                    <div className="links-list">
                        <div className="link-item" onClick={() => navigate('/crm/opportunities')}>
                            <span className="link-icon">💼</span>
                            {t('crm.opportunities')}
                            <span className="link-arrow">{i18n.language === 'ar' ? '←' : '→'}</span>
                        </div>
                    </div>
                </div>
                <div className="card section-card">
                    <h3 className="section-title">{t('crm.support_tickets')}</h3>
                    <div className="links-list">
                        <div className="link-item" onClick={() => navigate('/crm/tickets')}>
                            <span className="link-icon">🎫</span>
                            {t('crm.support_tickets')}
                            <span className="link-arrow">{i18n.language === 'ar' ? '←' : '→'}</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Pipeline Summary */}
            <div className="card section-card" style={{ marginTop: 24 }}>
                <h3 className="section-title">{t('crm.pipeline_summary')}</h3>
                {loading ? (
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
                                        {t('common.no_data')}
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                    </div>
                )}
            </div>
        </div>
    )
}

export default CRMHome
