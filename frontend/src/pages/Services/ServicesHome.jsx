import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import '../../components/ModuleStyles.css'
import BackButton from '../../components/common/BackButton'

function ServicesHome() {
    const { t } = useTranslation()
    const navigate = useNavigate()

    const modules = [
        {
            icon: '🔧',
            title: t('services.requests_title'),
            desc: t('services.requests_desc'),
            path: '/services/requests'
        },
        {
            icon: '📄',
            title: t('documents.title'),
            desc: t('documents.desc'),
            path: '/services/documents'
        }
    ]

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <div className="header-title">
                    <h1 className="workspace-title">{t('services.home_title')}</h1>
                    <p className="workspace-subtitle">{t('services.home_desc')}</p>
                </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '20px', marginTop: '24px' }}>
                {modules.map((m, i) => (
                    <div
                        key={i}
                        onClick={() => navigate(m.path)}
                        className="card"
                        style={{
                            cursor: 'pointer',
                            transition: 'transform 0.2s, box-shadow 0.2s',
                        }}
                        onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)' }}
                        onMouseLeave={e => { e.currentTarget.style.transform = 'none'; e.currentTarget.style.boxShadow = 'none' }}
                    >
                        <div style={{ fontSize: '36px', marginBottom: '12px' }}>{m.icon}</div>
                        <h3 style={{ margin: '0 0 8px', fontSize: '16px', fontWeight: 600 }}>{m.title}</h3>
                        <p style={{ margin: 0, fontSize: '13px', color: 'var(--text-secondary)' }}>{m.desc}</p>
                    </div>
                ))}
            </div>
        </div>
    )
}

export default ServicesHome
