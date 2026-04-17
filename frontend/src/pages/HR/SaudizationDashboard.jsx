import { useState, useEffect } from 'react'
import { wpsAPI } from '../../utils/api'
import { toastEmitter } from '../../utils/toastEmitter'
import { useTranslation } from 'react-i18next'
import BackButton from '../../components/common/BackButton'
import { formatNumber } from '../../utils/format'

function SaudizationDashboard() {
    const { t } = useTranslation()
    const [data, setData] = useState(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        wpsAPI.getSaudizationDashboard()
            .then(r => setData(r.data))
            .catch(err => toastEmitter.emit(err.response?.data?.detail || t('common.error'), 'error'))
            .finally(() => setLoading(false))
    }, [])

    if (loading) return <div className="p-4"><span className="loading"></span></div>
    if (!data) return <div className="p-4 text-muted">{t('common.no_data')}</div>

    const bandColors = {
        platinum: '#8b5cf6', high_green: '#22c55e', low_green: '#86efac',
        yellow: '#eab308', red: '#ef4444'
    }

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <div className="header-title">
                    <h1 className="workspace-title">🇸🇦 {t('saudization.title')}</h1>
                    <p className="workspace-subtitle">{t('saudization.subtitle')}</p>
                </div>
            </div>

            <div className="alert alert-info mb-4">
                ⚠️ {t('saudization.sa_only_note')}
            </div>

            {/* Metrics */}
            <div className="metrics-grid">
                <div className="metric-card">
                    <div className="metric-label">{t('saudization.total_employees')}</div>
                    <div className="metric-value text-primary">{data.total_employees}</div>
                </div>
                <div className="metric-card">
                    <div className="metric-label">{t('saudization.saudi_count')}</div>
                    <div className="metric-value text-success">{data.saudi_count}</div>
                </div>
                <div className="metric-card">
                    <div className="metric-label">{t('saudization.saudization_rate')}</div>
                    <div className="metric-value" style={{ color: bandColors[data.nitaqat_band] || '#333' }}>
                        {formatNumber(data.saudization_percentage)}%
                    </div>
                </div>
                <div className="metric-card">
                    <div className="metric-label">{t('saudization.nitaqat_band')}</div>
                    <div className="metric-value" style={{ color: bandColors[data.nitaqat_band] || '#333' }}>
                        {t(`saudization.band_${data.nitaqat_band}`, data.nitaqat_band)}
                    </div>
                </div>
            </div>

            {/* Band Info */}
            {data.needed_for_next_band > 0 && (
                <div className="card p-4 mt-4">
                    <div className="alert alert-warning">
                        📈 {t('saudization.need_more', { count: data.needed_for_next_band })}
                    </div>
                </div>
            )}

            {/* Department Breakdown */}
            {data.by_department && data.by_department.length > 0 && (
                <div className="card mt-4 p-4">
                    <h3 className="card-title">{t('saudization.by_department')}</h3>
                    <table className="data-table mt-2">
                        <thead>
                            <tr>
                                <th>{t('common.department')}</th>
                                <th>{t('saudization.total')}</th>
                                <th>{t('saudization.saudi')}</th>
                                <th>{t('saudization.rate')}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {data.by_department.map((d, i) => (
                                <tr key={i}>
                                    <td>{d.department || t('common.unassigned')}</td>
                                    <td>{d.total}</td>
                                    <td>{d.saudi}</td>
                                    <td className="font-bold">{formatNumber(d.percentage)}%</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {/* Nationality Breakdown */}
            {data.by_nationality && data.by_nationality.length > 0 && (
                <div className="card mt-4 p-4">
                    <h3 className="card-title">{t('saudization.by_nationality')}</h3>
                    <table className="data-table mt-2">
                        <thead>
                            <tr><th>{t('saudization.nationality')}</th><th>{t('saudization.count')}</th></tr>
                        </thead>
                        <tbody>
                            {data.by_nationality.map((n, i) => (
                                <tr key={i}>
                                    <td>{n.nationality || t('common.unknown')}</td>
                                    <td>{n.count}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    )
}

export default SaudizationDashboard
