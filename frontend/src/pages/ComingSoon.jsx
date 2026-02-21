import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next';

// Generic Coming Soon Component
function ComingSoonPage({ title, description, icon, backPath }) {
    const navigate = useNavigate()
    const { t } = useTranslation()

    return (
        <div className="workspace fade-in">
            <div style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                minHeight: '60vh',
                textAlign: 'center'
            }}>
                <div style={{ fontSize: '80px', marginBottom: '20px' }}>{icon}</div>
                <h1 style={{ fontSize: '32px', fontWeight: '700', color: 'var(--text-primary)', marginBottom: '10px' }}>
                    {title}
                </h1>
                <p style={{ color: 'var(--text-secondary)', fontSize: '18px', marginBottom: '30px', maxWidth: '500px' }}>
                    {description}
                </p>
                <button className="btn btn-secondary" onClick={() => navigate(backPath || '/dashboard')}>
                    {t("common.back")}
                </button>
            </div>
        </div>
    )
}

export function ComingSoon() {
    const { t } = useTranslation()
    return <ComingSoonPage title={t("coming_soon.title")} description={t("coming_soon.desc")} icon="⏳" />
}

export default ComingSoonPage
