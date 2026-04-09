import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import BackButton from '../../components/common/BackButton'
import { hasPermission } from '../../utils/auth'

function SubscriptionHome() {
    const { t } = useTranslation()
    const navigate = useNavigate()

    const sections = [
        {
            icon: '📋',
            title: t('subscription.plans_title'),
            desc: t('subscription.plans_subtitle'),
            path: '/finance/subscriptions/plans',
            permission: 'finance.subscription_view',
        },
        {
            icon: '👥',
            title: t('subscription.enrollments_title'),
            desc: t('subscription.enrollments_subtitle'),
            path: '/finance/subscriptions/enrollments',
            permission: 'finance.subscription_view',
        },
    ]

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <h1 className="workspace-title">{t('subscription.title') || 'الاشتراكات'}</h1>
                <p className="workspace-subtitle">{t('subscription.home_subtitle') || 'إدارة خطط الاشتراك وتسجيل العملاء'}</p>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '16px' }}>
                {sections.filter(s => hasPermission(s.permission)).map(section => (
                    <div
                        key={section.path}
                        className="card"
                        style={{ padding: '24px', cursor: 'pointer', transition: 'transform 0.2s' }}
                        onClick={() => navigate(section.path)}
                        onMouseEnter={e => e.currentTarget.style.transform = 'translateY(-2px)'}
                        onMouseLeave={e => e.currentTarget.style.transform = 'none'}
                    >
                        <div style={{ fontSize: '2rem', marginBottom: '12px' }}>{section.icon}</div>
                        <h3 style={{ margin: '0 0 8px' }}>{section.title}</h3>
                        <p className="text-muted" style={{ margin: 0 }}>{section.desc}</p>
                    </div>
                ))}
            </div>
        </div>
    )
}

export default SubscriptionHome
