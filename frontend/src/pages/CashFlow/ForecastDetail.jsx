import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { cashflowAPI } from '../../utils/api'
import { useTranslation } from 'react-i18next'
import { formatShortDate } from '../../utils/dateUtils'
import { formatNumber } from '../../utils/format'
import DataTable from '../../components/common/DataTable'
import BackButton from '../../components/common/BackButton'
import { PageLoading } from '../../components/common/LoadingStates'

function ForecastDetail() {
    const { id } = useParams()
    const { t } = useTranslation()
    const navigate = useNavigate()
    const [forecast, setForecast] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true)
                const response = await cashflowAPI.get(id)
                setForecast(response.data)
            } catch (err) {
                setError(t('common.error_loading'))
                console.error(err)
            } finally {
                setLoading(false)
            }
        }
        fetchData()
    }, [id, t])

    if (loading) return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <h1 className="workspace-title">{t('common.loading')}</h1>
            </div>
            <PageLoading />
        </div>
    )
    if (error) return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
            </div>
            <div className="alert alert-error">{error}</div>
        </div>
    )
    if (!forecast) return null

    const lineColumns = [
        { key: 'date', label: t('cashflow.detail.date'), render: (val) => formatShortDate(val) },
        {
            key: 'source_type',
            label: t('cashflow.detail.source'),
            render: (val) => t(`cashflow.source.${val}`),
        },
        {
            key: 'projected_inflow',
            label: t('cashflow.detail.inflow'),
            render: (val) => <span style={{ color: 'var(--color-success)' }}>{formatNumber(val)}</span>,
        },
        {
            key: 'projected_outflow',
            label: t('cashflow.detail.outflow'),
            render: (val) => <span style={{ color: 'var(--color-danger)' }}>{formatNumber(val)}</span>,
        },
        {
            key: 'projected_balance',
            label: t('cashflow.detail.balance'),
            style: { fontWeight: 'bold' },
            render: (val) => formatNumber(val),
        },
    ]

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <div>
                    <h1 className="workspace-title">{forecast.name}</h1>
                    <p className="workspace-subtitle">
                        {formatShortDate(forecast.forecast_date)} &middot; {forecast.horizon_days} {t('cashflow.form.days')} &middot; {t(`cashflow.mode.${forecast.mode}`)}
                    </p>
                </div>
            </div>

            {/* Summary cards */}
            <div className="stats-grid" style={{ marginBottom: '1.5rem' }}>
                <div className="stat-card">
                    <div className="stat-label">{t('cashflow.detail.total_inflow')}</div>
                    <div className="stat-value" style={{ color: 'var(--color-success)' }}>
                        {formatNumber(forecast.lines?.reduce((s, l) => s + Number(l.projected_inflow || 0), 0))}
                    </div>
                </div>
                <div className="stat-card">
                    <div className="stat-label">{t('cashflow.detail.total_outflow')}</div>
                    <div className="stat-value" style={{ color: 'var(--color-danger)' }}>
                        {formatNumber(forecast.lines?.reduce((s, l) => s + Number(l.projected_outflow || 0), 0))}
                    </div>
                </div>
                <div className="stat-card">
                    <div className="stat-label">{t('cashflow.detail.net')}</div>
                    <div className="stat-value">
                        {formatNumber(
                            forecast.lines?.reduce((s, l) => s + Number(l.projected_inflow || 0) - Number(l.projected_outflow || 0), 0)
                        )}
                    </div>
                </div>
            </div>

            <DataTable
                columns={lineColumns}
                data={forecast.lines || []}
                loading={false}
                emptyTitle={t('cashflow.detail.no_lines')}
                emptyDesc={t('cashflow.detail.no_lines_desc')}
            />

            <div style={{ marginTop: '1rem' }}>
                <button className="btn btn-secondary" onClick={() => navigate('/finance/cashflow')}>
                    {t('cashflow.back_to_list')}
                </button>
            </div>
        </div>
    )
}

export default ForecastDetail
