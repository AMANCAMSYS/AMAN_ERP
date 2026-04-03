import { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { cashflowAPI } from '../../utils/api'
import { useTranslation } from 'react-i18next'
import { formatShortDate } from '../../utils/dateUtils'
import DataTable from '../../components/common/DataTable'
import BackButton from '../../components/common/BackButton'

function ForecastList() {
    const { t } = useTranslation()
    const navigate = useNavigate()
    const [forecasts, setForecasts] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true)
                const response = await cashflowAPI.list()
                const payload = response.data
                setForecasts(Array.isArray(payload?.items) ? payload.items : Array.isArray(payload) ? payload : [])
            } catch (err) {
                setError(t('common.error_loading'))
                console.error(err)
            } finally {
                setLoading(false)
            }
        }
        fetchData()
    }, [t])

    const handleDelete = async (id) => {
        if (!window.confirm(t('cashflow.confirm_delete'))) return
        try {
            await cashflowAPI.delete(id)
            setForecasts(prev => prev.filter(f => f.id !== id))
        } catch (err) {
            console.error(err)
        }
    }

    const columns = [
        { key: 'name', label: t('cashflow.table.name'), style: { fontWeight: 'bold' } },
        { key: 'forecast_date', label: t('cashflow.table.date'), render: (val) => formatShortDate(val) },
        { key: 'horizon_days', label: t('cashflow.table.horizon') },
        {
            key: 'mode',
            label: t('cashflow.table.mode'),
            render: (val) => t(`cashflow.mode.${val}`),
        },
        {
            key: 'actions',
            label: '',
            render: (_, row) => (
                <button className="btn btn-sm btn-danger" onClick={(e) => { e.stopPropagation(); handleDelete(row.id) }}>
                    {t('common.delete')}
                </button>
            ),
        },
    ]

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        <h1 className="workspace-title">{t('cashflow.title')}</h1>
                        <p className="workspace-subtitle">{t('cashflow.subtitle')}</p>
                    </div>
                    <button className="btn btn-primary" onClick={() => navigate('/finance/cashflow/generate')}>
                        + {t('cashflow.generate_new')}
                    </button>
                </div>
            </div>

            {error && <div className="alert alert-error">{error}</div>}

            <DataTable
                columns={columns}
                data={forecasts}
                loading={loading}
                onRowClick={(row) => navigate(`/finance/cashflow/${row.id}`)}
                emptyTitle={t('cashflow.no_forecasts')}
                emptyDesc={t('cashflow.empty_desc')}
                emptyAction={{ label: t('cashflow.generate_new'), onClick: () => navigate('/finance/cashflow/generate') }}
            />
        </div>
    )
}

export default ForecastList
