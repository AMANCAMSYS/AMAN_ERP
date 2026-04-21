import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { crmAPI } from '../../utils/api'
import { getCurrency } from '../../utils/auth'
import { formatNumber } from '../../utils/format'
import BackButton from '../../components/common/BackButton'
import '../../components/ModuleStyles.css'
import { ModuleKPISection } from '../../components/kpi'
import { PageLoading } from '../../components/common/LoadingStates'

function PipelineAnalytics() {
    const { t } = useTranslation()
    const currency = getCurrency()
    const [tab, setTab] = useState('pipeline')
    const [pipelineData, setPipelineData] = useState(null)
    const [conversionData, setConversionData] = useState(null)
    const [campaignData, setCampaignData] = useState(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => { fetchData() }, [tab])

    const fetchData = async () => {
        try {
            setLoading(true)
            if (tab === 'pipeline' && !pipelineData) {
                const res = await crmAPI.getPipelineAnalytics()
                setPipelineData(res.data)
            } else if (tab === 'conversion' && !conversionData) {
                const res = await crmAPI.getConversionAnalytics()
                setConversionData(res.data)
            } else if (tab === 'campaigns' && !campaignData) {
                const res = await crmAPI.getCampaignROI()
                setCampaignData(res.data)
            }
        } catch (err) {
            console.error('Failed to fetch analytics', err)
        } finally {
            setLoading(false)
        }
    }

    const stageLabel = (stage) => t(`crm.stage_${stage}`, stage)

    const getStageColor = (stage) => {
        const colors = { lead: '#6b7280', qualified: '#3b82f6', proposal: '#8b5cf6', negotiation: '#f97316', won: '#22c55e', lost: '#ef4444' }
        return colors[stage] || '#6b7280'
    }

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <div>
                    <h1 className="workspace-title">{t('crm.pipeline_analytics', 'تحليلات خط الأنابيب')}</h1>
                    <p className="workspace-subtitle">{t('crm.analytics_desc', 'تحليل الأداء ومعدلات التحويل والعائد على الاستثمار')}</p>
                </div>
            </div>

            <ModuleKPISection roleKey="crm" color="#e11d48" defaultOpen={false} />

            <div className="tabs" style={{ marginBottom: 16 }}>
                <button className={`tab ${tab === 'pipeline' ? 'active' : ''}`} onClick={() => setTab('pipeline')}>
                    {t('crm.pipeline_tab', 'خط الأنابيب')}
                </button>
                <button className={`tab ${tab === 'conversion' ? 'active' : ''}`} onClick={() => setTab('conversion')}>
                    {t('crm.conversion_tab', 'معدلات التحويل')}
                </button>
                <button className={`tab ${tab === 'campaigns' ? 'active' : ''}`} onClick={() => setTab('campaigns')}>
                    {t('crm.campaign_roi_tab', 'عائد الحملات')}
                </button>
            </div>

            {loading ? (
                <PageLoading />
            ) : tab === 'pipeline' ? (
                renderPipeline()
            ) : tab === 'conversion' ? (
                renderConversion()
            ) : (
                renderCampaigns()
            )}
        </div>
    )

    function renderPipeline() {
        if (!pipelineData) return null
        const { funnel, win_rate, velocity, monthly_trend, top_performers, source_analysis } = pipelineData

        return (
            <>
                {/* Key Metrics */}
                <div className="metrics-grid">
                    <div className="metric-card">
                        <div className="metric-label">{t('crm.win_rate', 'معدل الفوز')}</div>
                        <div className="metric-value text-success">{win_rate?.win_rate_pct || 0}%</div>
                    </div>
                    <div className="metric-card">
                        <div className="metric-label">{t('crm.avg_days_close', 'متوسط أيام الإغلاق')}</div>
                        <div className="metric-value text-primary">{Math.round(velocity?.avg_days_to_close || 0)}</div>
                    </div>
                    <div className="metric-card">
                        <div className="metric-label">{t('crm.total_won', 'إجمالي الفائزة')}</div>
                        <div className="metric-value text-success">{velocity?.total_won || 0}</div>
                    </div>
                    <div className="metric-card">
                        <div className="metric-label">{t('crm.avg_deal', 'متوسط الصفقة')}</div>
                        <div className="metric-value text-primary">{formatNumber(velocity?.avg_deal_value || 0)} <small>{currency}</small></div>
                    </div>
                </div>

                {/* Sales Funnel */}
                <div className="section-card" style={{ marginTop: 20 }}>
                    <h3 className="section-title">{t('crm.sales_funnel', 'قمع المبيعات')}</h3>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                        {funnel?.map((s, i) => {
                            const maxVal = Math.max(...funnel.map(f => f.count), 1)
                            const pct = (s.count / maxVal) * 100
                            return (
                                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                                    <div style={{ width: 100, fontWeight: 600, fontSize: '0.875rem', color: getStageColor(s.stage) }}>
                                        {stageLabel(s.stage)}
                                    </div>
                                    <div style={{ flex: 1, background: '#f3f4f6', borderRadius: 8, height: 28, overflow: 'hidden' }}>
                                        <div style={{
                                            width: `${pct}%`, height: '100%', borderRadius: 8,
                                            backgroundColor: getStageColor(s.stage),
                                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                                            color: '#fff', fontSize: '0.75rem', fontWeight: 600, minWidth: 40
                                        }}>
                                            {s.count}
                                        </div>
                                    </div>
                                    <div style={{ width: 120, textAlign: 'end', fontSize: '0.85rem', color: '#6b7280' }}>
                                        {formatNumber(s.total_value)} {currency}
                                    </div>
                                </div>
                            )
                        })}
                    </div>
                </div>

                {/* Top Performers & Source Analysis side by side */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: 16, marginTop: 20 }}>
                    {/* Top Performers */}
                    <div className="section-card">
                        <h3 className="section-title">{t('crm.top_performers', 'أفضل الموظفين')}</h3>
                        {top_performers?.length > 0 ? (
                            <div className="data-table-container">
                                <table className="data-table">
                                    <thead>
                                        <tr>
                                            <th>{t('common.name', 'الاسم')}</th>
                                            <th>{t('crm.wins', 'فوز')}</th>
                                            <th>{t('common.value', 'القيمة')}</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {top_performers.map((p, i) => (
                                            <tr key={i}>
                                                <td style={{ fontWeight: 600 }}>{p.full_name || p.username}</td>
                                                <td><span className="badge badge-success">{p.wins}</span></td>
                                                <td>{formatNumber(p.total_value)} {currency}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        ) : <p style={{ color: '#9ca3af', textAlign: 'center', padding: 16 }}>{t('common.no_data', 'لا توجد بيانات')}</p>}
                    </div>

                    {/* Source Analysis */}
                    <div className="section-card">
                        <h3 className="section-title">{t('crm.source_analysis', 'تحليل المصادر')}</h3>
                        {source_analysis?.length > 0 ? (
                            <div className="data-table-container">
                                <table className="data-table">
                                    <thead>
                                        <tr>
                                            <th>{t('crm.source', 'المصدر')}</th>
                                            <th>{t('common.total', 'الإجمالي')}</th>
                                            <th>{t('crm.won', 'فاز')}</th>
                                            <th>{t('common.value', 'القيمة')}</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {source_analysis.map((s, i) => (
                                            <tr key={i}>
                                                <td style={{ fontWeight: 600 }}>{s.source}</td>
                                                <td>{s.total}</td>
                                                <td><span className="badge badge-success">{s.won}</span></td>
                                                <td>{formatNumber(s.won_value)} {currency}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        ) : <p style={{ color: '#9ca3af', textAlign: 'center', padding: 16 }}>{t('common.no_data', 'لا توجد بيانات')}</p>}
                    </div>
                </div>

                {/* Monthly Trend */}
                {monthly_trend?.length > 0 && (
                    <div className="section-card" style={{ marginTop: 20 }}>
                        <h3 className="section-title">{t('crm.monthly_trend', 'الاتجاه الشهري')}</h3>
                        <div className="data-table-container">
                            <table className="data-table">
                                <thead>
                                    <tr>
                                        <th>{t('common.month', 'الشهر')}</th>
                                        <th>{t('crm.created', 'أُنشئت')}</th>
                                        <th>{t('crm.won', 'فاز')}</th>
                                        <th>{t('crm.lost', 'خسر')}</th>
                                        <th>{t('crm.won_value', 'قيمة الفائزة')}</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {monthly_trend.map((m, i) => (
                                        <tr key={i}>
                                            <td style={{ fontWeight: 600 }}>{m.month}</td>
                                            <td>{m.created}</td>
                                            <td><span className="badge badge-success">{m.won}</span></td>
                                            <td><span className="badge badge-danger">{m.lost}</span></td>
                                            <td>{formatNumber(m.won_value)} {currency}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}
            </>
        )
    }

    function renderConversion() {
        if (!conversionData) return null

        return (
            <>
                <div className="metrics-grid">
                    <div className="metric-card">
                        <div className="metric-label">{t('crm.win_rate', 'معدل الفوز')}</div>
                        <div className="metric-value text-success">{conversionData.win_rate}%</div>
                    </div>
                    <div className="metric-card">
                        <div className="metric-label">{t('crm.loss_rate', 'معدل الخسارة')}</div>
                        <div className="metric-value text-danger">{conversionData.loss_rate}%</div>
                    </div>
                    <div className="metric-card">
                        <div className="metric-label">{t('crm.avg_days_close', 'متوسط أيام الإغلاق')}</div>
                        <div className="metric-value text-primary">{Math.round(conversionData.avg_days_to_close)}</div>
                    </div>
                    <div className="metric-card">
                        <div className="metric-label">{t('crm.total_closed', 'إجمالي المغلقة')}</div>
                        <div className="metric-value">{conversionData.total_closed}</div>
                    </div>
                </div>

                {/* Won vs Lost */}
                <div className="section-card" style={{ marginTop: 20 }}>
                    <h3 className="section-title">{t('crm.won_vs_lost', 'الفوز مقابل الخسارة')}</h3>
                    <div style={{ display: 'flex', gap: 16, alignItems: 'center', justifyContent: 'center', padding: 20 }}>
                        <div style={{ textAlign: 'center' }}>
                            <div style={{ fontSize: '2.5rem', fontWeight: 800, color: '#22c55e' }}>{conversionData.won}</div>
                            <div style={{ fontSize: '0.85rem', color: '#6b7280' }}>{t('crm.won_deals', 'صفقات فائزة')}</div>
                        </div>
                        <div style={{ fontSize: '1.5rem', color: '#d1d5db', fontWeight: 300 }}>|</div>
                        <div style={{ textAlign: 'center' }}>
                            <div style={{ fontSize: '2.5rem', fontWeight: 800, color: '#ef4444' }}>{conversionData.lost}</div>
                            <div style={{ fontSize: '0.85rem', color: '#6b7280' }}>{t('crm.lost_deals', 'صفقات خاسرة')}</div>
                        </div>
                    </div>
                </div>

                {/* By Source */}
                {conversionData.by_source?.length > 0 && (
                    <div className="section-card" style={{ marginTop: 20 }}>
                        <h3 className="section-title">{t('crm.conversion_by_source', 'التحويل حسب المصدر')}</h3>
                        <div className="data-table-container">
                            <table className="data-table">
                                <thead>
                                    <tr>
                                        <th>{t('crm.source', 'المصدر')}</th>
                                        <th>{t('common.total', 'الإجمالي')}</th>
                                        <th>{t('crm.won', 'فاز')}</th>
                                        <th>{t('crm.conversion_rate', 'معدل التحويل')}</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {conversionData.by_source.map((s, i) => (
                                        <tr key={i}>
                                            <td style={{ fontWeight: 600 }}>{s.source}</td>
                                            <td>{s.total}</td>
                                            <td><span className="badge badge-success">{s.won}</span></td>
                                            <td>
                                                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                                    <div style={{ flex: 1, background: '#f3f4f6', borderRadius: 4, height: 8, maxWidth: 120 }}>
                                                        <div style={{
                                                            width: `${s.conversion_rate}%`, height: '100%', borderRadius: 4,
                                                            backgroundColor: s.conversion_rate >= 50 ? '#22c55e' : s.conversion_rate >= 25 ? '#f97316' : '#ef4444'
                                                        }} />
                                                    </div>
                                                    <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>{s.conversion_rate}%</span>
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}

                {/* Stage Distribution */}
                {conversionData.stage_distribution?.length > 0 && (
                    <div className="section-card" style={{ marginTop: 20 }}>
                        <h3 className="section-title">{t('crm.stage_distribution', 'توزيع المراحل')}</h3>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                            {conversionData.stage_distribution.map((s, i) => {
                                const maxVal = Math.max(...conversionData.stage_distribution.map(x => x.count), 1)
                                const pct = (s.count / maxVal) * 100
                                return (
                                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                                        <div style={{ width: 100, fontWeight: 600, fontSize: '0.875rem', color: getStageColor(s.stage) }}>
                                            {stageLabel(s.stage)}
                                        </div>
                                        <div style={{ flex: 1, background: '#f3f4f6', borderRadius: 8, height: 24, overflow: 'hidden' }}>
                                            <div style={{
                                                width: `${pct}%`, height: '100%', borderRadius: 8,
                                                backgroundColor: getStageColor(s.stage),
                                                display: 'flex', alignItems: 'center', paddingInlineStart: 8,
                                                color: '#fff', fontSize: '0.75rem', fontWeight: 600, minWidth: 30
                                            }}>
                                                {s.count}
                                            </div>
                                        </div>
                                        <div style={{ width: 100, textAlign: 'end', fontSize: '0.85rem', color: '#6b7280' }}>
                                            {formatNumber(s.value)} {currency}
                                        </div>
                                    </div>
                                )
                            })}
                        </div>
                    </div>
                )}
            </>
        )
    }

    function renderCampaigns() {
        if (!campaignData) return null
        const { campaigns, summary } = campaignData

        return (
            <>
                <div className="metrics-grid">
                    <div className="metric-card">
                        <div className="metric-label">{t('crm.total_investment', 'إجمالي الاستثمار')}</div>
                        <div className="metric-value text-primary">{formatNumber(summary?.total_investment || 0)} <small>{currency}</small></div>
                    </div>
                    <div className="metric-card">
                        <div className="metric-label">{t('crm.total_conversions', 'إجمالي التحويلات')}</div>
                        <div className="metric-value text-success">{summary?.total_conversions || 0}</div>
                    </div>
                    <div className="metric-card">
                        <div className="metric-label">{t('crm.avg_cost_conversion', 'متوسط تكلفة التحويل')}</div>
                        <div className="metric-value text-warning">{formatNumber(summary?.avg_cpc || 0)} <small>{currency}</small></div>
                    </div>
                    <div className="metric-card">
                        <div className="metric-label">{t('crm.overall_rate', 'المعدل الإجمالي')}</div>
                        <div className="metric-value">{summary?.overall_conversion_rate || 0}%</div>
                    </div>
                </div>

                {campaigns?.length > 0 && (
                    <div className="section-card" style={{ marginTop: 20 }}>
                        <h3 className="section-title">{t('crm.campaign_performance', 'أداء الحملات')}</h3>
                        <div className="data-table-container">
                            <table className="data-table">
                                <thead>
                                    <tr>
                                        <th>{t('common.name', 'الاسم')}</th>
                                        <th>{t('common.type', 'النوع')}</th>
                                        <th>{t('common.status_title', 'الحالة')}</th>
                                        <th>{t('crm.budget', 'الميزانية')}</th>
                                        <th>{t('crm.sent', 'أُرسل')}</th>
                                        <th>{t('crm.open_rate', 'معدل الفتح')}</th>
                                        <th>{t('crm.click_rate', 'معدل النقر')}</th>
                                        <th>{t('crm.conversions', 'التحويلات')}</th>
                                        <th>{t('crm.cost_per_conv', 'التكلفة/تحويل')}</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {campaigns.map(c => (
                                        <tr key={c.id}>
                                            <td style={{ fontWeight: 600 }}>{c.name}</td>
                                            <td><span className="badge badge-info">{c.campaign_type}</span></td>
                                            <td>
                                                <span className={`badge ${c.status === 'active' ? 'badge-success' : c.status === 'completed' ? 'badge-primary' : 'badge-secondary'}`}>
                                                    {c.status}
                                                </span>
                                            </td>
                                            <td>{formatNumber(c.budget)} {currency}</td>
                                            <td>{c.sent}</td>
                                            <td>{c.open_rate}%</td>
                                            <td>{c.click_rate}%</td>
                                            <td><span className="badge badge-success">{c.conversions}</span></td>
                                            <td>{formatNumber(c.cost_per_conversion)} {currency}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}
            </>
        )
    }
}

export default PipelineAnalytics
