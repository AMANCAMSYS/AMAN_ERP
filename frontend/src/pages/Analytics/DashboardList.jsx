import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { dashboardAPI } from '../../services/dashboard'
import DataTable from '../../components/common/DataTable'
import BackButton from '../../components/common/BackButton'
import { hasPermission } from '../../utils/auth'

function DashboardList() {
    const { t } = useTranslation()
    const navigate = useNavigate()
    const [dashboards, setDashboards] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true)
                const response = await dashboardAPI.listAnalyticsDashboards()
                setDashboards(response.data?.dashboards || [])
            } catch (err) {
                setError(t('analytics.error_loading'))
                console.error(err)
            } finally {
                setLoading(false)
            }
        }
        fetchData()
    }, [t])

    const columns = [
        {
            key: 'name',
            label: t('analytics.dashboard_name'),
            style: { fontWeight: 'bold', cursor: 'pointer' },
            render: (val, row) => (
                <span onClick={() => navigate(`/analytics/${row.id}`)} style={{ color: 'var(--primary)', cursor: 'pointer' }}>
                    {val}
                </span>
            )
        },
        { key: 'description', label: t('analytics.description') },
        {
            key: 'is_system',
            label: t('analytics.type'),
            render: (val) => (
                <span className={`badge ${val ? 'badge-info' : 'badge-secondary'}`}>
                    {val ? t('analytics.system') : t('analytics.custom')}
                </span>
            )
        },
        { key: 'branch_scope', label: t('analytics.branch_scope') },
        {
            key: 'refresh_interval_minutes',
            label: t('analytics.refresh_interval'),
            render: (val) => `${val} ${t('analytics.minutes')}`
        },
    ]

    if (loading) return <div className="p-4">{t('common.loading')}</div>
    if (error) return <div className="p-4 text-danger">{error}</div>

    return (
        <div className="p-4">
            <div className="d-flex justify-content-between align-items-center mb-4">
                <div>
                    <BackButton />
                    <h2>{t('analytics.title')}</h2>
                    <p className="text-muted">{t('analytics.subtitle')}</p>
                </div>
                {hasPermission('dashboard.analytics_manage') && (
                    <button
                        className="btn btn-primary"
                        onClick={() => navigate('/analytics/new')}
                    >
                        {t('analytics.create_dashboard')}
                    </button>
                )}
            </div>

            <DataTable
                data={dashboards}
                columns={columns}
                onRowClick={(row) => navigate(`/analytics/${row.id}`)}
                emptyMessage={t('analytics.no_dashboards')}
            />
        </div>
    )
}

export default DashboardList
