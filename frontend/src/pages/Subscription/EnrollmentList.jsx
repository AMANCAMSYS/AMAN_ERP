import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { subscriptionsAPI } from '../../services/subscriptions'
import { useTranslation } from 'react-i18next'
import { formatShortDate } from '../../utils/dateUtils'
import DataTable from '../../components/common/DataTable'
import BackButton from '../../components/common/BackButton'

const STATUS_COLORS = {
    trial: 'badge-info',
    active: 'badge-success',
    paused: 'badge-warning',
    cancelled: 'badge-secondary',
    at_risk: 'badge-danger',
}

function EnrollmentList() {
    const { t } = useTranslation()
    const navigate = useNavigate()
    const [enrollments, setEnrollments] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [statusFilter, setStatusFilter] = useState('')

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true)
                const params = {}
                if (statusFilter) params.status = statusFilter
                const response = await subscriptionsAPI.listEnrollments(params)
                const payload = response.data
                setEnrollments(Array.isArray(payload?.items) ? payload.items : Array.isArray(payload) ? payload : [])
            } catch (err) {
                setError(t('common.error_loading'))
                console.error(err)
            } finally {
                setLoading(false)
            }
        }
        fetchData()
    }, [t, statusFilter])

    const columns = [
        { key: 'id', label: '#', style: { width: '60px' } },
        { key: 'customer_id', label: t('subscription.table.customer') },
        { key: 'plan_id', label: t('subscription.table.plan') },
        {
            key: 'enrollment_date',
            label: t('subscription.table.enrolled'),
            render: (val) => formatShortDate(val),
        },
        {
            key: 'next_billing_date',
            label: t('subscription.table.next_billing'),
            render: (val) => formatShortDate(val),
        },
        {
            key: 'status',
            label: t('subscription.table.status'),
            render: (val) => (
                <span className={`badge ${STATUS_COLORS[val] || 'badge-secondary'}`}>
                    {t(`subscription.status.${val}`)}
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
                        <h1 className="workspace-title">{t('subscription.enrollments_title')}</h1>
                        <p className="workspace-subtitle">{t('subscription.enrollments_subtitle')}</p>
                    </div>
                    <div style={{ display: 'flex', gap: '8px' }}>
                        <select
                            className="form-input"
                            value={statusFilter}
                            onChange={(e) => setStatusFilter(e.target.value)}
                            style={{ width: '150px' }}
                        >
                            <option value="">{t('common.all')}</option>
                            <option value="trial">{t('subscription.status.trial')}</option>
                            <option value="active">{t('subscription.status.active')}</option>
                            <option value="paused">{t('subscription.status.paused')}</option>
                            <option value="at_risk">{t('subscription.status.at_risk')}</option>
                            <option value="cancelled">{t('subscription.status.cancelled')}</option>
                        </select>
                        <button className="btn btn-primary" onClick={() => navigate('/finance/subscriptions/enroll')}>
                            + {t('subscription.new_enrollment')}
                        </button>
                    </div>
                </div>
            </div>

            {error && <div className="alert alert-error">{error}</div>}

            <DataTable
                columns={columns}
                data={enrollments}
                loading={loading}
                onRowClick={(row) => navigate(`/finance/subscriptions/enrollments/${row.id}`)}
                emptyTitle={t('subscription.no_enrollments')}
                emptyDesc={t('subscription.enrollments_empty_desc')}
                emptyAction={{ label: t('subscription.new_enrollment'), onClick: () => navigate('/finance/subscriptions/enroll') }}
            />
        </div>
    )
}

export default EnrollmentList
