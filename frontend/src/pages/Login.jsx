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
