import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { crmAPI } from '../../utils/api'
import { getCurrency } from '../../utils/auth'
import { formatNumber } from '../../utils/format'
import BackButton from '../../components/common/BackButton'
import '../../components/ModuleStyles.css'

function SalesForecasts() {
    const { t } = useTranslation()
    const currency = getCurrency()
    const [data, setData] = useState(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => { fetchForecast() }, [])

    const fetchForecast = async () => {
        try {
            setLoading(true)
            const res = await crmAPI.getSalesForecast()
            setData(res.data)
        } catch (err) {
            console.error('Failed to fetch forecast', err)
        } finally {
            setLoading(false)
        }
    }

    if (loading) return <div className="loading-spinner"><div className="spinner"></div></div>
    if (!data) return null

    const wp = data.weighted_pipeline || {}
    const scenarios = data.scenarios || {}

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <div>
                    <h1 className="workspace-title">{t('crm.sales_forecasts', 'التنبؤات البيعية')}</h1>
                    <p className="workspace-subtitle">{t('crm.forecasts_desc', 'توقعات المبيعات بناءً على خط الأنابيب الحالي')}</p>
                </div>
            </div>

            {/* Weighted Pipeline */}
            <div className="metrics-grid">
                <div className="metric-card">
                    <div className="metric-label">{t('crm.weighted_value', 'القيمة المرجحة')}</div>
                    <div className="metric-value text-primary">{formatNumber(wp.weighted_value || 0)} <small>{currency}</small></div>
                </div>
                <div className="metric-card">
                    <div className="metric-label">{t('crm.total_pipeline', 'إجمالي خط الأنابيب')}</div>
                    <div className="metric-value text-success">{formatNumber(wp.total_pipeline || 0)} <small>{currency}</small></div>
                </div>
                <div className="metric-card">
                    <div className="metric-label">{t('crm.active_deals', 'الصفقات النشطة')}</div>
                    <div className="metric-value" style={{ color: '#8b5cf6' }}>{wp.active_deals || 0}</div>
                </div>
            </div>

            {/* Scenarios */}
            <div className="section-card" style={{ marginTop: 20 }}>
                <h3 className="section-title">{t('crm.forecast_scenarios', 'سيناريوهات التوقع')}</h3>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16 }}>
                    <div style={{
                        padding: 20, borderRadius: 12, textAlign: 'center',
                        background: 'linear-gradient(135deg, #dcfce7, #f0fdf4)',
                        border: '1px solid #bbf7d0'
                    }}>
                        <div style={{ fontSize: '0.85rem', color: '#16a34a', fontWeight: 600, marginBottom: 4 }}>
                            {t('crm.commit_value', 'القيمة المؤكدة')}
                        </div>
                        <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#15803d' }}>
                            {formatNumber(scenarios.commit_value || 0)}
                        </div>
                        <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>{t('crm.probability_75', 'احتمالية ≥ 75%')}</div>
                    </div>
                    <div style={{
                        padding: 20, borderRadius: 12, textAlign: 'center',
                        background: 'linear-gradient(135deg, #dbeafe, #eff6ff)',
                        border: '1px solid #bfdbfe'
                    }}>
                        <div style={{ fontSize: '0.85rem', color: '#2563eb', fontWeight: 600, marginBottom: 4 }}>
                            {t('crm.most_likely', 'الأكثر احتمالاً')}
                        </div>
                        <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#1d4ed8' }}>
                            {formatNumber(scenarios.most_likely || 0)}
                        </div>
                        <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>{t('crm.weighted_avg', 'المتوسط المرجح')}</div>
                    </div>
                    <div style={{
                        padding: 20, borderRadius: 12, textAlign: 'center',
                        background: 'linear-gradient(135deg, #fef3c7, #fffbeb)',
                        border: '1px solid #fde68a'
                    }}>
                        <div style={{ fontSize: '0.85rem', color: '#d97706', fontWeight: 600, marginBottom: 4 }}>
                            {t('crm.best_case', 'أفضل حالة')}
                        </div>
                        <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#b45309' }}>
                            {formatNumber(scenarios.best_case || 0)}
                        </div>
                        <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>{t('crm.probability_50', 'احتمالية ≥ 50%')}</div>
                    </div>
                </div>
            </div>

            {/* By Month */}
            {data.by_month?.length > 0 && (
                <div className="section-card" style={{ marginTop: 20 }}>
                    <h3 className="section-title">{t('crm.forecast_by_month', 'التوقعات حسب الشهر')}</h3>
                    <div className="data-table-container">
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th>{t('common.month', 'الشهر')}</th>
                                    <th>{t('crm.deals_count', 'عدد الصفقات')}</th>
                                    <th>{t('crm.total_value', 'القيمة الإجمالية')}</th>
                                    <th>{t('crm.weighted_value', 'القيمة المرجحة')}</th>
                                </tr>
                            </thead>
                            <tbody>
                                {data.by_month.map((m, i) => (
                                    <tr key={i}>
                                        <td style={{ fontWeight: 600 }}>{m.month}</td>
                                        <td>{m.deals}</td>
                                        <td>{formatNumber(m.total_value)} {currency}</td>
                                        <td>
                                            <span style={{ color: '#3b82f6', fontWeight: 600 }}>
                                                {formatNumber(m.weighted_value)} {currency}
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {/* Historical Actuals */}
            {data.historical_actuals?.length > 0 && (
                <div className="section-card" style={{ marginTop: 20 }}>
                    <h3 className="section-title">{t('crm.historical_actuals', 'الإنجازات السابقة')}</h3>
                    <div className="data-table-container">
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th>{t('common.month', 'الشهر')}</th>
                                    <th>{t('crm.actual_value', 'القيمة الفعلية')}</th>
                                    <th>{t('crm.deals_won', 'الصفقات المكسوبة')}</th>
                                </tr>
                            </thead>
                            <tbody>
                                {data.historical_actuals.map((h, i) => (
                                    <tr key={i}>
                                        <td style={{ fontWeight: 600 }}>{h.month}</td>
                                        <td>
                                            <span style={{ color: '#22c55e', fontWeight: 600 }}>
                                                {formatNumber(h.actual_value)} {currency}
                                            </span>
                                        </td>
                                        <td><span className="badge badge-success">{h.deals_won}</span></td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    )
}

export default SalesForecasts
