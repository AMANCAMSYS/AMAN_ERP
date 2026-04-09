import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
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

function EnrollmentDetail() {
    const { t } = useTranslation()
    const { id } = useParams()
    const navigate = useNavigate()
    const [enrollment, setEnrollment] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [actionLoading, setActionLoading] = useState(false)

    const fetchData = async () => {
        try {
            setLoading(true)
            const response = await subscriptionsAPI.getEnrollment(id)
            setEnrollment(response.data)
        } catch (err) {
            setError(t('common.error_loading'))
            console.error(err)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => { fetchData() }, [id])

    const handlePause = async () => {
        if (!window.confirm(t('subscription.confirm_pause'))) return
        setActionLoading(true)
        try {
            await subscriptionsAPI.pauseEnrollment(id)
            await fetchData()
        } catch (err) {
            setError(err.response?.data?.detail || t('common.error_saving'))
        } finally {
            setActionLoading(false)
        }
    }

    const handleResume = async () => {
        setActionLoading(true)
        try {
            await subscriptionsAPI.resumeEnrollment(id)
            await fetchData()
        } catch (err) {
            setError(err.response?.data?.detail || t('common.error_saving'))
        } finally {
            setActionLoading(false)
        }
    }

    const handleCancel = async () => {
        const reason = window.prompt(t('subscription.cancel_reason'))
        if (reason === null) return
        setActionLoading(true)
        try {
            await subscriptionsAPI.cancelEnrollment(id, { reason })
            await fetchData()
        } catch (err) {
            setError(err.response?.data?.detail || t('common.error_saving'))
        } finally {
            setActionLoading(false)
        }
    }

    const invoiceColumns = [
        { key: 'id', label: '#', style: { width: '60px' } },
        {
            key: 'billing_period_start',
            label: t('subscription.table.period_start'),
            render: (val) => formatShortDate(val),
        },
        {
            key: 'billing_period_end',
            label: t('subscription.table.period_end'),
            render: (val) => formatShortDate(val),
        },
        {
            key: 'is_prorated',
            label: t('subscription.table.prorated'),
            render: (val) => val ? t('common.yes') : t('common.no'),
        },
        { key: 'invoice_id', label: t('subscription.table.invoice_id') },
    ]

    if (loading) return <div className="workspace"><div className="loading-spinner" /></div>

    if (!enrollment) return (
        <div className="workspace fade-in">
            <BackButton />
            <div className="alert alert-error">{error || t('subscription.not_found')}</div>
        </div>
    )

    const canPause = ['active', 'at_risk'].includes(enrollment.status)
    const canResume = enrollment.status === 'paused'
    const canCancel = enrollment.status !== 'cancelled'

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        <h1 className="workspace-title">
                            {t('subscription.enrollment_detail')} #{enrollment.id}
                        </h1>
                        <p className="workspace-subtitle">
                            {enrollment.plan_name} — {enrollment.customer_name}
                        </p>
                    </div>
                    <div style={{ display: 'flex', gap: '8px' }}>
                        {canPause && (
                            <button className="btn btn-warning" onClick={handlePause} disabled={actionLoading}>
                                {t('subscription.action.pause')}
                            </button>
                        )}
                        {canResume && (
                            <button className="btn btn-success" onClick={handleResume} disabled={actionLoading}>
                                {t('subscription.action.resume')}
                            </button>
                        )}
                        {canCancel && (
                            <button className="btn btn-danger" onClick={handleCancel} disabled={actionLoading}>
                                {t('subscription.action.cancel')}
                            </button>
                        )}
                    </div>
                </div>
            </div>

            {error && <div className="alert alert-error">{error}</div>}

            <div className="stats-grid">
                <div className="stat-card">
                    <span>{t('subscription.detail.status')}</span>
                    <span className={`badge ${STATUS_COLORS[enrollment.status] || 'badge-secondary'}`}>
                        {t(`subscription.status.${enrollment.status}`)}
                    </span>
                </div>
                <div className="stat-card">
                    <span>{t('subscription.detail.enrolled')}</span>
                    <strong>{formatShortDate(enrollment.enrollment_date)}</strong>
                </div>
                <div className="stat-card">
                    <span>{t('subscription.detail.next_billing')}</span>
                    <strong>{formatShortDate(enrollment.next_billing_date)}</strong>
                </div>
                {enrollment.trial_end_date && (
                    <div className="stat-card">
                        <span>{t('subscription.detail.trial_end')}</span>
                        <strong>{formatShortDate(enrollment.trial_end_date)}</strong>
                    </div>
                )}
                {enrollment.failed_payment_count > 0 && (
                    <div className="stat-card">
                        <span>{t('subscription.detail.failed_payments')}</span>
                        <strong className="text-danger">{enrollment.failed_payment_count}</strong>
                    </div>
                )}
            </div>

            <h2 style={{ marginTop: '24px' }}>{t('subscription.billing_history')}</h2>
            <DataTable
                columns={invoiceColumns}
                data={enrollment.invoices || []}
                loading={false}
                emptyTitle={t('subscription.no_invoices')}
                emptyDesc={t('subscription.invoices_empty_desc')}
            />
        </div>
    )
}

export default EnrollmentDetail
