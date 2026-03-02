import { useState } from 'react'
import { Link } from 'react-router-dom'
import { passwordResetAPI } from '../utils/api'
import { useTranslation } from 'react-i18next'

function ForgotPassword() {
    const { t } = useTranslation()
    const [email, setEmail] = useState('')
    const [loading, setLoading] = useState(false)
    const [sent, setSent] = useState(false)
    const [error, setError] = useState('')
    const [devResetUrl, setDevResetUrl] = useState('')

    const handleSubmit = async (e) => {
        e.preventDefault()
        setLoading(true)
        setError('')
        try {
            const res = await passwordResetAPI.forgotPassword({ email })
            if (res.data?.dev_reset_url) {
                setDevResetUrl(res.data.dev_reset_url)
            }
            setSent(true)
        } catch (err) {
            const detail = err.response?.data?.detail
            if (Array.isArray(detail)) {
                setError(detail.map(d => d.msg).join(', '))
            } else {
                setError(typeof detail === 'string' ? detail : t('forgot_password.error'))
            }
        } finally { setLoading(false) }
    }

    return (
        <div className="login-container">
            <div className="login-card">
                <div className="text-center mb-4">
                    <h1 className="text-2xl font-bold">🔑 {t('forgot_password.title')}</h1>
                    <p className="text-muted mt-2">{t('forgot_password.description')}</p>
                </div>

                {sent ? (
                    <div className="text-center">
                        <div className="alert alert-success">
                            ✅ {t('forgot_password.email_sent')}
                        </div>
                        {devResetUrl ? (
                            <div className="alert alert-warning mt-3" style={{ textAlign: 'left', wordBreak: 'break-all' }}>
                                <strong>⚙️ وضع التطوير — SMTP غير مُهيأ</strong>
                                <p className="mt-2" style={{ fontSize: '0.85rem' }}>انقر على الرابط أدناه لإعادة تعيين كلمة المرور:</p>
                                <a href={devResetUrl} className="text-primary" style={{ fontSize: '0.8rem' }}>{devResetUrl}</a>
                            </div>
                        ) : (
                            <p className="text-muted mt-3">{t('forgot_password.check_inbox')}</p>
                        )}
                        <Link to="/login" className="btn btn-primary mt-4">{t('forgot_password.back_to_login')}</Link>
                    </div>
                ) : (
                    <form onSubmit={handleSubmit}>
                        {error && <div className="alert alert-danger mb-3">{error}</div>}
                        <div className="form-group">
                            <label>{t('forgot_password.username_or_email')}</label>
                            <input
                                type="email"
                                className="form-input"
                                value={email}
                                onChange={e => setEmail(e.target.value)}
                                placeholder="your@email.com"
                                required
                                autoFocus
                            />
                        </div>
                        <button type="submit" className="btn btn-primary w-full mt-3" disabled={loading || !email}>
                            {loading ? t('common.sending') : t('forgot_password.send_reset')}
                        </button>
                        <div className="text-center mt-3">
                            <Link to="/login" className="text-primary">{t('forgot_password.back_to_login')}</Link>
                        </div>
                    </form>
                )}
            </div>
        </div>
    )
}

export default ForgotPassword
