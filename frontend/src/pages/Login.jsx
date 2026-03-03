import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { authAPI } from '../utils/api'
import { setAuth, isAuthenticated } from '../utils/auth'
import { hasIndustryTypeSet } from '../hooks/useIndustryType'
import { useTranslation } from 'react-i18next'

function Login() {
    const { t } = useTranslation()
    const navigate = useNavigate()

    useEffect(() => {
        if (isAuthenticated()) {
            navigate('/dashboard');
        }
    }, [navigate]);
    const [formData, setFormData] = useState({ username: '', password: '' })
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')

    const handleSubmit = async (e) => {
        e.preventDefault()
        setLoading(true)
        setError('')

        try {
            const response = await authAPI.login(formData.username, formData.password)
            const { access_token, user, company_id } = response.data

            setAuth(access_token, user, company_id)
            
            // توجيه: إذا لم يُحدد نوع النشاط بعد → صفحة الإعداد
            if (user?.role !== 'system_admin' && !hasIndustryTypeSet()) {
                window.location.href = '/setup/industry'
            } else {
                window.location.href = '/dashboard'
            }
        } catch (err) {
            setError(err.response?.data?.detail || t('auth.login_failed'))
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="auth-layout">
            <div className="auth-card">
                <div className="auth-header">
                    <h1>{t('auth.login_title')}</h1>
                    <p>{t('auth.login_subtitle')}</p>
                </div>

                {error && <div className="alert alert-error">{error}</div>}

                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label className="form-label" htmlFor="username">{t('auth.username')}</label>
                        <input
                            type="text"
                            id="username"
                            name="username"
                            className="form-input"
                            placeholder="username"
                            value={formData.username}
                            onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                            required
                            autoComplete="username"
                        />
                    </div>

                    <div className="form-group">
                        <label className="form-label" htmlFor="password">{t('auth.password')}</label>
                        <input
                            type="password"
                            id="password"
                            name="password"
                            className="form-input"
                            placeholder="••••••••"
                            value={formData.password}
                            onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                            required
                            autoComplete="current-password"
                        />
                    </div>

                    <div className="text-end" style={{ marginBottom: '12px' }}>
                        <Link to="/forgot-password" className="link" style={{ fontSize: '13px' }}>
                            {t('forgot_password.title')}
                        </Link>
                    </div>

                    <button type="submit" className="btn btn-primary btn-block" disabled={loading}>
                        {loading ? <span className="loading"></span> : t('auth.login_btn')}
                    </button>
                </form>

                <div className="mt-4 text-center">
                    <Link to="/register" className="link" style={{ fontSize: '14px' }}>
                        {t('auth.no_account')}
                    </Link>
                </div>
            </div>
        </div>
    )
}

export default Login
