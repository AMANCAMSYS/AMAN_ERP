import { useState, useEffect } from 'react'
import { getUser, getCompanyId } from '../utils/auth'
import { useTranslation } from 'react-i18next'

function UserProfile() {
    const { t } = useTranslation()
    const [user, setUser] = useState(null)
    const companyId = getCompanyId()

    useEffect(() => {
        setUser(getUser())
    }, [])

    if (!user) return <div className="page-center"><span className="loading"></span></div>

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <h1 className="workspace-title">{t('common.profile_page.title')}</h1>
                <p className="workspace-subtitle">{t('common.profile_page.subtitle')}</p>
            </div>

            <div className="card" style={{ maxWidth: '600px' }}>
                <div style={{ display: 'flex', alignItems: 'center', marginBottom: '32px' }}>
                    <div style={{
                        width: '80px',
                        height: '80px',
                        borderRadius: '50%',
                        backgroundColor: 'var(--primary)',
                        color: 'white',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '32px',
                        fontWeight: 'bold',
                        marginLeft: '24px'
                    }}>
                        {user.username.charAt(0).toUpperCase()}
                    </div>
                    <div>
                        <h2 style={{ fontSize: '24px', margin: '0 0 8px 0' }}>{user.full_name}</h2>
                        <span className="badge badge-primary">{user.role}</span>
                    </div>
                </div>

                <div className="form-group mb-4">
                    <div className="form-label">{t('common.profile_page.username')}</div>
                    <div style={{ padding: '12px', background: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                        {user.username}
                    </div>
                </div>

                <div className="form-group mb-4">
                    <div className="form-label">{t('common.profile_page.email')}</div>
                    <div style={{ padding: '12px', background: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                        {user.email || t('common.profile_page.not_set')}
                    </div>
                </div>

                {companyId && (
                    <div className="form-group mb-4">
                        <div className="form-label">{t('common.profile_page.company_id')}</div>
                        <div style={{ padding: '12px', background: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0', fontFamily: 'monospace' }}>
                            {companyId}
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}

export default UserProfile
