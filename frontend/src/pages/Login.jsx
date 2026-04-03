import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { authAPI } from '../utils/api'
import { setAuth, isAuthenticated } from '../utils/auth'
import { hasIndustryTypeSet } from '../hooks/useIndustryType'
import { useTranslation } from 'react-i18next'

function Login() {
    const { t, i18n } = useTranslation()
    const navigate = useNavigate()

    const toggleLanguage = () => {
        const nextLang = i18n.language === 'ar' ? 'en' : 'ar'
        i18n.changeLanguage(nextLang)
    }

    useEffect(() => {
        if (isAuthenticated()) {
            navigate('/dashboard');
        }
    }, [navigate]);

    const [formData, setFormData] = useState({ company_code: '', username: '', password: '' })
    const [showPassword, setShowPassword] = useState(false)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')

    // SSO state
    const [ssoProviders, setSsoProviders] = useState([])
    const [ssoLoading, setSsoLoading] = useState(false)

    // Fetch SSO providers when company_code changes
    useEffect(() => {
        const code = formData.company_code.trim()
        if (!code || code.length < 2) {
            setSsoProviders([])
            return
        }
        const timeout = setTimeout(async () => {
            try {
                const res = await authAPI.getSsoProviders(code)
                setSsoProviders(res.data || [])
            } catch {
                setSsoProviders([])
            }
        }, 500)
        return () => clearTimeout(timeout)
    }, [formData.company_code])

    const handleSsoLogin = async (provider) => {
        setSsoLoading(true)
        setError('')
        try {
            const res = await authAPI.ssoLogin(provider.id, formData.company_code.trim())
            if (res.data?.redirect_url) {
                window.location.href = res.data.redirect_url
            } else if (res.data?.access_token) {
                const { access_token, refresh_token, user, company_id } = res.data
                setAuth(access_token, user, company_id, refresh_token)
                window.location.href = '/dashboard'
            }
        } catch (err) {
            setError(err.response?.data?.detail || t('auth.sso_login_failed', 'SSO login failed'))
        } finally {
            setSsoLoading(false)
        }
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        setLoading(true)
        setError('')

        // مستخدم النظام (admin) لا يحتاج رمز شركة
        const isSystemAdmin = formData.username.trim() === 'admin'

        if (!isSystemAdmin && !formData.company_code.trim()) {
            setError(t('auth.company_code_required', 'رمز الشركة مطلوب'))
            setLoading(false)
            return
        }

        try {
            const response = await authAPI.login(
                formData.username,
                formData.password,
                isSystemAdmin ? null : formData.company_code
            )
            const { access_token, refresh_token, user, company_id } = response.data

            setAuth(access_token, user, company_id, refresh_token)

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
            <div className="floating-language-toggle">
                <button
                    type="button"
                    className="btn btn-light"
                    onClick={toggleLanguage}
                    aria-label={t('common.language', 'Language')}
                    title={t('common.language', 'Language')}
                >
                    {i18n.language === 'ar' ? 'EN' : 'AR'}
                </button>
            </div>
            <div className="auth-card">
                <div className="auth-header">
                    <h1>{t('auth.login_title')}</h1>
                    <p>{t('auth.login_subtitle')}</p>
                </div>

                {error && <div className="alert alert-error">{error}</div>}

                <form onSubmit={handleSubmit}>
                    {/* رمز الشركة — يُخفى تلقائياً إذا كان المستخدم "admin" */}
                    {formData.username.trim() !== 'admin' && (
                        <div className="form-group">
                            <label className="form-label" htmlFor="company_code">
                                {t('auth.company_code', 'رمز الشركة')}
                            </label>
                            <input
                                type="text"
                                id="company_code"
                                name="company_code"
                                className="form-input"
                                placeholder={t('auth.company_code_placeholder', 'أدخل رمز الشركة')}
                                value={formData.company_code}
                                onChange={(e) => setFormData({ ...formData, company_code: e.target.value })}
                                autoComplete="organization"
                                autoCapitalize="none"
                                spellCheck={false}
                            />
                            <small className="text-muted" style={{ fontSize: '12px', color: '#888' }}>
                                {t('auth.company_code_hint', 'يمكن الحصول عليه من مسؤول الشركة')}
                            </small>
                        </div>
                    )}

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
                        <div className="input-group">
                            <input
                                type={showPassword ? 'text' : 'password'}
                                id="password"
                                name="password"
                                className="form-input"
                                placeholder="••••••••"
                                value={formData.password}
                                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                                required
                                autoComplete="current-password"
                            />
                            <button
                                type="button"
                                className="btn btn-light"
                                onClick={() => setShowPassword((prev) => !prev)}
                                aria-label={showPassword ? t('common.hide', 'إخفاء كلمة المرور') : t('common.show', 'إظهار كلمة المرور')}
                            >
                                {showPassword ? t('common.hide', 'إخفاء') : t('common.show', 'إظهار')}
                            </button>
                        </div>
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

                {/* SSO Providers */}
                {ssoProviders.length > 0 && (
                    <div style={{ marginTop: '16px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', margin: '12px 0' }}>
                            <hr style={{ flex: 1, border: 'none', borderTop: '1px solid #e5e7eb' }} />
                            <span style={{ fontSize: '13px', color: '#888' }}>{t('auth.or_sso', 'أو عبر تسجيل الدخول الموحد')}</span>
                            <hr style={{ flex: 1, border: 'none', borderTop: '1px solid #e5e7eb' }} />
                        </div>
                        {ssoProviders.map((provider) => (
                            <button
                                key={provider.id}
                                type="button"
                                className="btn btn-outline btn-block"
                                style={{ marginBottom: '8px' }}
                                onClick={() => handleSsoLogin(provider)}
                                disabled={ssoLoading}
                            >
                                {ssoLoading ? <span className="loading"></span> : (
                                    <>🔐 {t('auth.login_with_sso', 'تسجيل الدخول عبر')} {provider.display_name}</>
                                )}
                            </button>
                        ))}
                    </div>
                )}

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
