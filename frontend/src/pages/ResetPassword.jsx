import { useState } from 'react'
import { useSearchParams, Link, useNavigate } from 'react-router-dom'
import { passwordResetAPI } from '../utils/api'
import { useTranslation } from 'react-i18next'
import BackButton from '../components/common/BackButton'

function ResetPassword() {
    const { t } = useTranslation()
    const navigate = useNavigate()
    const [searchParams] = useSearchParams()
    const token = searchParams.get('token') || ''
    const [password, setPassword] = useState('')
    const [confirmPassword, setConfirmPassword] = useState('')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')
    const [success, setSuccess] = useState(false)

    const handleSubmit = async (e) => {
        e.preventDefault()
        if (password !== confirmPassword) {
            setError(t('reset_password.mismatch'))
            return
        }
        if (password.length < 8) {
            setError(t('reset_password.too_short'))
            return
        }
        setLoading(true)
        setError('')
        try {
            await passwordResetAPI.resetPassword({ token, new_password: password })
            setSuccess(true)
            setTimeout(() => navigate('/login'), 3000)
        } catch (err) {
            const detail = err.response?.data?.detail
            if (Array.isArray(detail)) {
                setError(detail.map(d => d.msg).join(', '))
            } else {
                setError(typeof detail === 'string' ? detail : t('reset_password.error'))
            }
        } finally { setLoading(false) }
    }

    return (
        <div className="login-container">
            <div className="login-card">
                <div style={{ marginBottom: '12px' }}>
                    <BackButton />
                </div>
                <div className="text-center mb-4">
                    <h1 className="text-2xl font-bold">🔐 {t('reset_password.title')}</h1>
                </div>

                {success ? (
                    <div className="text-center">
                        <div className="alert alert-success">
                            ✅ {t('reset_password.success')}
                        </div>
                        <p className="text-muted mt-3">{t('reset_password.redirecting')}</p>
                    </div>
                ) : !token ? (
                    <div className="text-center">
                        <div className="alert alert-danger">{t('reset_password.invalid_token')}</div>
                        <Link to="/forgot-password" className="btn btn-primary mt-3">{t('reset_password.request_new')}</Link>
                    </div>
                ) : (
                    <form onSubmit={handleSubmit}>
                        {error && <div className="alert alert-danger mb-3">{error}</div>}
                        <div className="form-group">
                            <label>{t('reset_password.new_password')}</label>
                            <input type="password" className="form-input" value={password} onChange={e => setPassword(e.target.value)} required minLength={8} />
                        </div>
                        <div className="form-group mt-3">
                            <label>{t('reset_password.confirm_password')}</label>
                            <input type="password" className="form-input" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} required />
                        </div>
                        <button type="submit" className="btn btn-primary w-full mt-3" disabled={loading}>
                            {loading ? t('common.saving') : t('reset_password.reset_button')}
                        </button>
                    </form>
                )}
            </div>
        </div>
    )
}

export default ResetPassword
