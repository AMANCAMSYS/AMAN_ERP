import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { subscriptionsAPI } from '../../services/subscriptions'
import { useTranslation } from 'react-i18next'
import BackButton from '../../components/common/BackButton'
import FormField from '../../components/common/FormField'

function EnrollmentForm() {
    const { t } = useTranslation()
    const navigate = useNavigate()
    const [plans, setPlans] = useState([])
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')
    const [formData, setFormData] = useState({
        customer_id: '',
        plan_id: '',
        enrollment_date: new Date().toISOString().split('T')[0],
    })

    useEffect(() => {
        const fetchPlans = async () => {
            try {
                const response = await subscriptionsAPI.listPlans()
                const payload = response.data
                const items = Array.isArray(payload?.items) ? payload.items : Array.isArray(payload) ? payload : []
                setPlans(items.filter(p => p.is_active))
            } catch (err) {
                console.error(err)
            }
        }
        fetchPlans()
    }, [])

    const handleChange = (e) => {
        const { name, value } = e.target
        setFormData(prev => ({ ...prev, [name]: value }))
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        if (!formData.customer_id || !formData.plan_id) {
            setError(t('common.required_field'))
            return
        }

        setLoading(true)
        setError('')
        try {
            await subscriptionsAPI.enroll({
                customer_id: parseInt(formData.customer_id),
                plan_id: parseInt(formData.plan_id),
                enrollment_date: formData.enrollment_date || null,
            })
            navigate('/finance/subscriptions/enrollments')
        } catch (err) {
            setError(err.response?.data?.detail || t('common.error_saving'))
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <div>
                    <h1 className="workspace-title">{t('subscription.new_enrollment')}</h1>
                    <p className="workspace-subtitle">{t('subscription.enrollments_subtitle')}</p>
                </div>
            </div>

            <div className="card" style={{ maxWidth: '900px', margin: '0 auto', padding: '32px', boxShadow: 'var(--shadow-lg)' }}>
                {error && <div className="alert alert-error mb-4">{error}</div>}

                <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                    <div className="form-section card">
                        <h3 className="section-title" style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: '12px', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--primary)' }}>
                            <span style={{ fontSize: '24px' }}>👥</span> {t('subscription.enrollment_info') || 'معلومات الاشتراك'}
                        </h3>
                        <div className="form-row" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
                            <FormField label={t('subscription.table.customer')} required style={{ marginBottom: 0 }}>
                                <input
                                    name="customer_id" type="number" min="1"
                                    value={formData.customer_id} onChange={handleChange}
                                    className="form-input"
                                    placeholder={t('subscription.customer_id_placeholder') || 'رقم العميل'}
                                    required
                                />
                            </FormField>
                            <FormField label={t('subscription.table.plan')} required style={{ marginBottom: 0 }}>
                                <select
                                    name="plan_id" value={formData.plan_id}
                                    onChange={handleChange} className="form-input" required
                                >
                                    <option value="">{t('common.select')}</option>
                                    {plans.map(plan => (
                                        <option key={plan.id} value={plan.id}>
                                            {plan.name} — {Number(plan.base_amount).toLocaleString()} {plan.currency}
                                        </option>
                                    ))}
                                </select>
                            </FormField>
                        </div>
                        <div style={{ marginTop: '24px' }}>
                            <FormField label={t('subscription.table.enrolled')} style={{ marginBottom: 0 }}>
                                <input
                                    name="enrollment_date" type="date"
                                    value={formData.enrollment_date} onChange={handleChange}
                                    className="form-input"
                                />
                            </FormField>
                        </div>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', paddingTop: '8px' }}>
                        <button type="button" className="btn btn-secondary" onClick={() => navigate('/finance/subscriptions/enrollments')}>
                            {t('common.cancel')}
                        </button>
                        <button type="submit" className="btn btn-primary" disabled={loading}>
                            {loading ? t('common.saving') : t('subscription.enroll_btn') || 'تسجيل الاشتراك'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    )
}

export default EnrollmentForm
