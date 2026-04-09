import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { subscriptionsAPI } from '../../services/subscriptions'
import { useTranslation } from 'react-i18next'
import { formatShortDate } from '../../utils/dateUtils'
import DataTable from '../../components/common/DataTable'
import BackButton from '../../components/common/BackButton'

function PlanList() {
    const { t } = useTranslation()
    const navigate = useNavigate()
    const [plans, setPlans] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true)
                const response = await subscriptionsAPI.listPlans()
                const payload = response.data
                setPlans(Array.isArray(payload?.items) ? payload.items : Array.isArray(payload) ? payload : [])
            } catch (err) {
                setError(t('common.error_loading'))
                console.error(err)
            } finally {
                setLoading(false)
            }
        }
        fetchData()
    }, [t])

    const columns = [
        { key: 'name', label: t('subscription.table.name'), style: { fontWeight: 'bold' } },
        {
            key: 'billing_frequency',
            label: t('subscription.table.frequency'),
            render: (val) => t(`subscription.frequency.${val}`),
        },
        {
            key: 'base_amount',
            label: t('subscription.table.amount'),
            render: (val, row) => `${Number(val).toLocaleString()} ${row.currency}`,
        },
        { key: 'trial_period_days', label: t('subscription.table.trial_days') },
        {
            key: 'is_active',
            label: t('subscription.table.status'),
            render: (val) => (
                <span className={`badge ${val ? 'badge-success' : 'badge-secondary'}`}>
                    {val ? t('common.active') : t('common.inactive')}
                </span>
            ),
        },
    ]

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        <h1 className="workspace-title">{t('subscription.plans_title')}</h1>
                        <p className="workspace-subtitle">{t('subscription.plans_subtitle')}</p>
                    </div>
                    <button className="btn btn-primary" onClick={() => navigate('/finance/subscriptions/plans/new')}>
                        + {t('subscription.new_plan')}
                    </button>
                </div>
            </div>

            {error && <div className="alert alert-error">{error}</div>}

            <DataTable
                columns={columns}
                data={plans}
                loading={loading}
                onRowClick={(row) => navigate(`/finance/subscriptions/plans/${row.id}/edit`)}
                emptyTitle={t('subscription.no_plans')}
                emptyDesc={t('subscription.plans_empty_desc')}
                emptyAction={{ label: t('subscription.new_plan'), onClick: () => navigate('/finance/subscriptions/plans/new') }}
            />
        </div>
    )
}

export default PlanList
