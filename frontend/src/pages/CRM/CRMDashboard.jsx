import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { crmAPI } from '../../utils/api'
import { getCurrency } from '../../utils/auth'
import { formatNumber } from '../../utils/format'
import '../../components/ModuleStyles.css'
import BackButton from '../../components/common/BackButton'
import { PageLoading } from '../../components/common/LoadingStates'

function CRMDashboard() {
    const { t } = useTranslation()
    const navigate = useNavigate()
    const currency = getCurrency()
    const [data, setData] = useState(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => { fetchDashboard() }, [])

    const fetchDashboard = async () => {
        try {
            setLoading(true)
            const res = await crmAPI.getDashboard()
            setData(res.data)
        } catch (err) {
            console.error('Failed to fetch CRM dashboard', err)
        } finally {
            setLoading(false)
        }
    }

    if (loading) return <PageLoading />

    const kpis = data?.kpis || {}
    const tickets = data?.tickets || {}
    const campaigns = data?.campaigns || {}

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <div>
                    <h1 className="workspace-title">{t('crm.dashboard_title', 'لوحة تحكم CRM')}</h1>
                    <p className="workspace-subtitle">{t('crm.dashboard_subtitle', 'نظرة شاملة على أداء إدارة العلاقات')}</p>
                </div>
            </div>

            {/* KPI Cards */}
            <div className="metrics-grid">
                <div className="metric-card">
                    <div className="metric-label">{t('crm.total_opportunities', 'إجمالي الفرص')}</div>
                    <div className="metric-value text-primary">{kpis.total_opportunities || 0}</div>
                </div>
                <div className="metric-card">
                    <div className="metric-label">{t('crm.pipeline_value', 'قيمة خط الأنابيب')}</div>
                    <div className="metric-value text-success">{formatNumber(kpis.pipeline_value || 0)} <small>{currency}</small></div>
                </div>
                <div className="metric-card">
                    <div className="metric-label">{t('crm.open_tickets', 'التذاكر المفتوحة')}</div>
                    <div className="metric-value text-warning">{tickets.open_tickets || 0}</div>
                </div>
                <div className="metric-card">
                    <div className="metric-label">{t('crm.active_campaigns', 'الحملات النشطة')}</div>
                    <div className="metric-value" style={{ color: '#8b5cf6' }}>{campaigns.active || 0}</div>
                </div>
                <div className="metric-card">
                    <div className="metric-label">{t('crm.win_rate', 'معدل الفوز')}</div>
                    <div className="metric-value text-success">{kpis.win_rate || 0}%</div>
                </div>
                <div className="metric-card">
                    <div className="metric-label">{t('crm.avg_deal_size', 'متوسط حجم الصفقة')}</div>
                    <div className="metric-value text-primary">{formatNumber(kpis.avg_deal_size || 0)} <small>{currency}</small></div>
                </div>
            </div>

            {/* Pipeline by Stage */}
            {data?.pipeline_by_stage && data.pipeline_by_stage.length > 0 && (
                <div className="section-card" style={{ marginTop: 20 }}>
                    <h3 className="section-title">{t('crm.pipeline_by_stage', 'خط الأنابيب حسب المرحلة')}</h3>
                    <div className="data-table-container">
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th>{t('common.stage', 'المرحلة')}</th>
                                    <th>{t('common.count', 'العدد')}</th>
                                    <th>{t('common.value', 'القيمة')}</th>
                                </tr>
                            </thead>
                            <tbody>
                                {data.pipeline_by_stage.map((s, i) => (
                                    <tr key={i}>
                                        <td>
                                            <span className={`badge ${s.stage === 'won' ? 'badge-success' : s.stage === 'lost' ? 'badge-danger' : 'badge-info'}`}>
                                                {t(`crm.stage_${s.stage}`, s.stage)}
                                            </span>
                                        </td>
                                        <td>{s.count}</td>
                                        <td>{formatNumber(s.total_value)} {currency}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {/* Lead Score Distribution */}
            {data?.lead_score_distribution && data.lead_score_distribution.length > 0 && (
                <div className="section-card" style={{ marginTop: 20 }}>
                    <h3 className="section-title">{t('crm.lead_score_distribution', 'توزيع تقييم العملاء')}</h3>
                    <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
                        {data.lead_score_distribution.map((d, i) => (
                            <div key={i} className="metric-card" style={{ flex: '1 1 120px', textAlign: 'center' }}>
                                <div className="metric-label">{t(`crm.grade_${d.grade}`, `التصنيف ${d.grade}`)}</div>
                                <div className="metric-value" style={{ color: d.grade === 'A' ? '#22c55e' : d.grade === 'B' ? '#3b82f6' : d.grade === 'C' ? '#f97316' : '#ef4444' }}>
                                    {d.count}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Quick Actions */}
            <div className="section-card" style={{ marginTop: 20 }}>
                <h3 className="section-title">{t('crm.quick_actions', 'إجراءات سريعة')}</h3>
                <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                    <button className="btn btn-primary btn-sm" onClick={() => navigate('/crm')}>{t('crm.title', 'إدارة العلاقات')}</button>
                    <button className="btn btn-info btn-sm" onClick={() => navigate('/crm/lead-scoring')}>{t('crm.lead_scoring', 'تقييم العملاء المحتملين')}</button>
                    <button className="btn btn-warning btn-sm" onClick={() => navigate('/crm/segments')}>{t('crm.customer_segments', 'شرائح العملاء')}</button>
                    <button className="btn btn-success btn-sm" onClick={() => navigate('/crm/contacts')}>{t('crm.contacts', 'جهات الاتصال')}</button>
                    <button className="btn btn-secondary btn-sm" onClick={() => navigate('/crm/analytics')}>{t('crm.analytics', 'التحليلات')}</button>
                    <button className="btn btn-dark btn-sm" onClick={() => navigate('/crm/forecasts')}>{t('crm.sales_forecasts', 'التنبؤات البيعية')}</button>
                </div>
            </div>
        </div>
    )
}

export default CRMDashboard
