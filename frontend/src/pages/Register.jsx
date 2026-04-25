import { useState } from 'react'
import { Link } from 'react-router-dom'
import { companiesAPI } from '../utils/api'
import { useTranslation } from 'react-i18next'
import BackButton from '../components/common/BackButton'
import { Spinner } from '../components/common/LoadingStates'

function Register() {
    const { t, i18n } = useTranslation()

    const toggleLanguage = () => {
        const nextLang = i18n.language === 'ar' ? 'en' : 'ar'
        i18n.changeLanguage(nextLang)
    }

    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')
    const [success, setSuccess] = useState(null)
    const [formData, setFormData] = useState({
        company_name: '',
        company_name_en: '',
        email: '',
        phone: '',
        address: '',
        country: 'SA',
        currency: 'SAR',
        admin_username: '',
        admin_email: '',
        admin_full_name: '',
        admin_password: '',
        admin_password_confirm: '',
        timezone: 'Asia/Riyadh',
        plan_type: 'basic',
    })

    const COUNTRY_DEFAULTS = {
        SA: { currency: 'SAR', timezone: 'Asia/Riyadh' },
        SY: { currency: 'SYP', timezone: 'Asia/Damascus' },
        AE: { currency: 'AED', timezone: 'Asia/Dubai' },
        EG: { currency: 'EGP', timezone: 'Africa/Cairo' },
        KW: { currency: 'KWD', timezone: 'Asia/Kuwait' },
        TR: { currency: 'TRY', timezone: 'Europe/Istanbul' },
    }

    const handleChange = (e) => {
        const { name, value } = e.target;
        if (name === 'country') {
            const defaults = COUNTRY_DEFAULTS[value] || {};
            setFormData(prev => ({ ...prev, country: value, currency: defaults.currency || prev.currency, timezone: defaults.timezone || prev.timezone }));
        } else {
            setFormData(prev => ({ ...prev, [name]: value }));
        }
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        setLoading(true)
        setError('')

        if (formData.admin_password !== formData.admin_password_confirm) {
            setError(t('auth.password_mismatch'))
            setLoading(false)
            return
        }

        try {
            const { admin_password_confirm, ...submitData } = formData
            const response = await companiesAPI.register(submitData)
            setSuccess(response.data)
        } catch (err) {
            setError(err.response?.data?.detail || t('auth.register_failed'))
        } finally {
            setLoading(false)
        }
    }


    if (success) {
        return (
            <div className="auth-layout" style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', minHeight: '100vh' }}>
                <div style={{ position: 'fixed', top: '16px', insetInlineStart: '16px', zIndex: 30 }}>
                    <BackButton />
                </div>
                <div className="floating-language-toggle">
                    <button
                        type="button"
                        className="btn btn-light"
                        onClick={toggleLanguage}
                        title={t('common.language')}
                    >
                        {i18n.language === 'ar' ? 'EN' : 'AR'}
                    </button>
                </div>
                <div style={{
                    background: 'white',
                    borderRadius: '20px',
                    padding: '50px 40px',
                    maxWidth: '500px',
                    width: '90%',
                    textAlign: 'center',
                    boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
                    animation: 'fadeInUp 0.6s ease-out'
                }}>
                    {/* Celebration Icon */}
                    <div style={{
                        fontSize: '80px',
                        marginBottom: '20px',
                        animation: 'bounce 1s infinite'
                    }}>
                        🎉
                    </div>

                    <h1 style={{
                        fontSize: '28px',
                        fontWeight: '800',
                        color: '#1e293b',
                        marginBottom: '10px'
                    }}>
                        {t('auth.success_title')}
                    </h1>

                    <p style={{ color: '#64748b', marginBottom: '30px' }}>
                        {t('auth.success_subtitle')}
                    </p>

                    {/* Important Info Card */}
                    <div style={{
                        background: 'linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%)',
                        border: '2px solid #22c55e',
                        borderRadius: '12px',
                        padding: '24px',
                        marginBottom: '24px',
                        textAlign: 'right'
                    }}>
                        <div style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '10px',
                            marginBottom: '16px',
                            justifyContent: 'center'
                        }}>
                            <span style={{ fontSize: '24px' }}>⚠️</span>
                            <span style={{ fontWeight: 'bold', color: '#166534', fontSize: '16px' }}>
                                {t('auth.save_info')}
                            </span>
                        </div>

                        <div style={{
                            background: 'white',
                            borderRadius: '8px',
                            padding: '16px',
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '12px'
                        }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <span style={{ color: '#64748b', fontSize: '14px' }}>{t('auth.company_id')}</span>
                                <span style={{
                                    background: '#3b82f6',
                                    color: 'white',
                                    padding: '6px 16px',
                                    borderRadius: '20px',
                                    fontWeight: 'bold',
                                    fontFamily: 'monospace',
                                    letterSpacing: '1px'
                                }}>
                                    {success.company_id}
                                </span>
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <span style={{ color: '#64748b', fontSize: '14px' }}>{t('auth.username')}</span>
                                <span style={{ fontWeight: 'bold', color: '#1e293b' }}>{success.admin_username}</span>
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <span style={{ color: '#64748b', fontSize: '14px' }}>{t('auth.database')}</span>
                                <span style={{ fontFamily: 'monospace', color: '#64748b', fontSize: '13px' }}>{success.database_name}</span>
                            </div>
                        </div>
                    </div>

                    <Link to="/login" style={{
                        display: 'block',
                        background: 'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)',
                        color: 'white',
                        padding: '16px 32px',
                        borderRadius: '12px',
                        fontWeight: 'bold',
                        fontSize: '18px',
                        textDecoration: 'none',
                        boxShadow: '0 10px 25px -5px rgba(59, 130, 246, 0.5)',
                        transition: 'transform 0.2s ease'
                    }}>
                        {t('auth.start_login')}
                    </Link>
                </div>

                <style>{`
                    @keyframes fadeInUp {
                        from {
                            opacity: 0;
                            transform: translateY(30px);
                        }
                        to {
                            opacity: 1;
                            transform: translateY(0);
                        }
                    }
                    @keyframes bounce {
                        0%, 100% { transform: translateY(0); }
                        50% { transform: translateY(-10px); }
                    }
                `}</style>
            </div>
        )
    }

    return (
        <div className="auth-layout" style={{ padding: '40px 20px' }}>
            <div style={{ position: 'fixed', top: '16px', insetInlineStart: '16px', zIndex: 30 }}>
                <BackButton />
            </div>
            <div className="floating-language-toggle">
                <button
                    type="button"
                    className="btn btn-light"
                    onClick={toggleLanguage}
                    title={t('common.language')}
                >
                    {i18n.language === 'ar' ? 'EN' : 'AR'}
                </button>
            </div>
            <div className="card" style={{ maxWidth: '800px', width: '100%', padding: '40px' }}>
                <div className="auth-header">
                    <h1>{t('auth.register_title')}</h1>
                    <p>{t('auth.register_subtitle')}</p>
                </div>

                {error && <div className="alert alert-error">{error}</div>}

                <form onSubmit={handleSubmit}>
                    <div className="form-section">
                        <h3 className="section-title">{t('auth.company_info')}</h3>
                        <div className="form-row">
                            <div className="form-group">
                                <label className="form-label" htmlFor="company_name">{t('auth.company_name')} *</label>
                                <input type="text" name="company_name" id="company_name" className="form-input"
                                    placeholder={t("auth.register.company_placeholder")} required
                                    value={formData.company_name} onChange={handleChange} autoComplete="organization" />
                            </div>
                            <div className="form-group">
                                <label className="form-label" htmlFor="company_name_en">{t('auth.company_name_en')}</label>
                                <input type="text" name="company_name_en" id="company_name_en" className="form-input"
                                    placeholder={t('auth.register.company_name_placeholder')}
                                    value={formData.company_name_en} onChange={handleChange} autoComplete="off" />
                            </div>
                        </div>

                        <div className="form-row">
                            <div className="form-group">
                                <label className="form-label" htmlFor="email">{t('auth.email')} *</label>
                                <input type="email" name="email" id="email" className="form-input"
                                    placeholder="info@company.com" required
                                    value={formData.email} onChange={handleChange} autoComplete="email" />
                            </div>
                            <div className="form-group">
                                <label className="form-label" htmlFor="phone">{t('auth.phone')}</label>
                                <input type="tel" name="phone" id="phone" className="form-input"
                                    placeholder="+966 5x xxx xxxx"
                                    value={formData.phone} onChange={handleChange} autoComplete="tel" />
                            </div>
                        </div>
                    </div>

                    <div className="form-section">
                        <h3 className="section-title">{t('auth.settings')}</h3>
                        <div className="form-row">
                            <div className="form-group">
                                <label className="form-label" htmlFor="country">{t('auth.country')} *</label>
                                <select name="country" id="country" className="form-input" value={formData.country} onChange={handleChange} required>
                                    <option value="SY">🇸🇾 {t('countries.SY')}</option>
                                    <option value="SA">🇸🇦 {t('countries.SA')}</option>
                                    <option value="AE">🇦🇪 {t('countries.AE')}</option>
                                    <option value="EG">🇪🇬 {t('countries.EG')}</option>
                                    <option value="KW">🇰🇼 {t('countries.KW')}</option>
                                    <option value="TR">🇹🇷 {t('countries.TR')}</option>
                                </select>
                            </div>
                            <div className="form-group">
                                <label className="form-label" htmlFor="currency">{t('auth.currency')}</label>
                                <select name="currency" id="currency" className="form-input" value={formData.currency} onChange={handleChange}>
                                    <option value="SYP">{t('auth.register.syp')}</option>
                                    <option value="SAR">{t('auth.register.sar')}</option>
                                    <option value="USD">{t('auth.register.usd')}</option>
                                    <option value="AED">{t('auth.register.aed')}</option>
                                    <option value="EGP">{t('auth.register.egp')}</option>
                                    <option value="KWD">{t('auth.register.kwd')}</option>
                                    <option value="TRY">{t('auth.register.try_currency')}</option>
                                    <option value="EUR">{t('auth.register.eur')}</option>
                                </select>
                            </div>
                        </div>
                        <div className="form-row">
                            <div className="form-group">
                                <label className="form-label" htmlFor="timezone">{t('auth.timezone')}</label>
                                <select name="timezone" id="timezone" className="form-input" value={formData.timezone} onChange={handleChange}>
                                    <option value="Asia/Damascus">{t('timezones.damascus_gmt')}</option>
                                    <option value="Asia/Riyadh">{t('timezones.riyadh_gmt')}</option>
                                    <option value="Asia/Dubai">{t('timezones.dubai_gmt')}</option>
                                    <option value="Africa/Cairo">{t('timezones.cairo_gmt')}</option>
                                    <option value="Asia/Kuwait">{t('timezones.kuwait_gmt')}</option>
                                    <option value="Europe/Istanbul">{t('timezones.istanbul_gmt')}</option>
                                    <option value="UTC">UTC</option>
                                </select>
                            </div>
                        </div>
                    </div>

                    <div className="form-section">
                        <h3 className="section-title">{t('auth.admin_info')}</h3>

                        <div className="form-row">
                            <div className="form-group">
                                <label className="form-label" htmlFor="admin_username">{t('auth.username')} *</label>
                                <input type="text" name="admin_username" id="admin_username" className="form-input"
                                    placeholder="admin_1" required minLength={4}
                                    value={formData.admin_username} onChange={handleChange} autoComplete="username" />
                            </div>
                            <div className="form-group">
                                <label className="form-label" htmlFor="admin_email">{t('auth.email')} *</label>
                                <input type="email" name="admin_email" id="admin_email" className="form-input"
                                    placeholder="admin@company.com" required
                                    value={formData.admin_email} onChange={handleChange} autoComplete="email" />
                            </div>
                        </div>

                        <div className="form-row">
                            <div className="form-group">
                                <label className="form-label" htmlFor="admin_full_name">{t('auth.full_name')} *</label>
                                <input type="text" name="admin_full_name" id="admin_full_name" className="form-input"
                                    placeholder={t("auth.register.full_name_ph")} required
                                    value={formData.admin_full_name} onChange={handleChange} autoComplete="name" />
                            </div>
                            <div className="form-group">
                                <label className="form-label" htmlFor="admin_password">{t('auth.password')} *</label>
                                <input type="password" name="admin_password" id="admin_password" className="form-input"
                                    placeholder={t("auth.register.password_ph")} required minLength={8}
                                    value={formData.admin_password} onChange={handleChange} autoComplete="new-password" />
                            </div>
                        </div>

                        <div className="form-row">
                            <div className="form-group">
                                <label className="form-label" htmlFor="admin_password_confirm">{t('auth.password_confirm')} *</label>
                                <input type="password" name="admin_password_confirm" id="admin_password_confirm" className="form-input"
                                    placeholder={t("auth.register.confirm_password_ph")} required minLength={8}
                                    value={formData.admin_password_confirm} onChange={handleChange} autoComplete="new-password" />
                            </div>
                        </div>
                    </div>

                    <button type="submit" className="btn btn-primary btn-block" disabled={loading} style={{ padding: '16px' }}>
                        {loading ? <Spinner size="sm"/> : t('auth.register_btn')}
                    </button>
                </form>

                <div className="mt-4 text-center">
                    <Link to="/login" className="link" style={{ fontSize: '14px' }}>
                        {t('auth.has_account')}
                    </Link>
                </div>
            </div>
        </div>
    )
}

export default Register
