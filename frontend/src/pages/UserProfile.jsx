import { useState, useEffect } from 'react'
import { authAPI, securityAPI } from '../utils/api'
import { getUser, getCompanyId, updateUser } from '../utils/auth'
import { useTranslation } from 'react-i18next'

function UserProfile() {
    const { t } = useTranslation()
    const [user, setUser] = useState(null)
    const [profileForm, setProfileForm] = useState({ full_name: '', email: '' })
    const [passwordForm, setPasswordForm] = useState({ current_password: '', new_password: '', confirm_password: '' })
    const [showPasswords, setShowPasswords] = useState({ current: false, next: false, confirm: false })
    const [savingProfile, setSavingProfile] = useState(false)
    const [savingPassword, setSavingPassword] = useState(false)
    const [profileMessage, setProfileMessage] = useState('')
    const [passwordMessage, setPasswordMessage] = useState('')
    const [profileError, setProfileError] = useState('')
    const [passwordError, setPasswordError] = useState('')
    const companyId = getCompanyId()

    useEffect(() => {
        const currentUser = getUser()
        setUser(currentUser)
        setProfileForm({
            full_name: currentUser?.full_name || '',
            email: currentUser?.email || ''
        })
    }, [])

    const handleProfileSave = async (e) => {
        e.preventDefault()
        setProfileError('')
        setProfileMessage('')

        const fullName = profileForm.full_name.trim()
        const email = profileForm.email.trim()

        if (!fullName) {
            setProfileError(t('common.profile_page.full_name_required', 'الاسم الكامل مطلوب'))
            return
        }

        setSavingProfile(true)
        try {
            const response = await authAPI.updateMe({ full_name: fullName, email: email || null })
            const updated = response.data
            setUser(updated)
            updateUser({
                full_name: updated.full_name,
                email: updated.email
            })
            setProfileMessage(t('common.profile_page.profile_saved', 'تم تحديث بيانات الحساب بنجاح'))
        } catch (err) {
            setProfileError(err.response?.data?.detail || t('common.profile_page.profile_save_failed', 'تعذر حفظ بيانات الحساب'))
        } finally {
            setSavingProfile(false)
        }
    }

    const handlePasswordSave = async (e) => {
        e.preventDefault()
        setPasswordError('')
        setPasswordMessage('')

        if (passwordForm.new_password !== passwordForm.confirm_password) {
            setPasswordError(t('common.profile_page.password_mismatch', 'كلمتا المرور غير متطابقتين'))
            return
        }
        if (passwordForm.new_password.length < 8) {
            setPasswordError(t('common.profile_page.password_too_short', 'كلمة المرور يجب أن تكون 8 أحرف على الأقل'))
            return
        }

        setSavingPassword(true)
        try {
            await securityAPI.changePassword({
                current_password: passwordForm.current_password,
                new_password: passwordForm.new_password
            })
            setPasswordForm({ current_password: '', new_password: '', confirm_password: '' })
            setPasswordMessage(t('common.profile_page.password_saved', 'تم تغيير كلمة المرور بنجاح'))
        } catch (err) {
            setPasswordError(err.response?.data?.detail || t('common.profile_page.password_save_failed', 'تعذر تغيير كلمة المرور'))
        } finally {
            setSavingPassword(false)
        }
    }

    const togglePasswordVisibility = (key) => {
        setShowPasswords((prev) => ({ ...prev, [key]: !prev[key] }))
    }

    if (!user) return <div className="page-center"><span className="loading"></span></div>

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <h1 className="workspace-title">{t('common.profile_page.title')}</h1>
                <p className="workspace-subtitle">{t('common.profile_page.subtitle')}</p>
            </div>

            <div className="card" style={{ maxWidth: '680px' }}>
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

                <form onSubmit={handleProfileSave}>
                    {profileError && <div className="alert alert-error">{profileError}</div>}
                    {profileMessage && <div className="alert" style={{ background: 'rgba(16, 185, 129, 0.12)', color: 'var(--success)', border: '1px solid rgba(16, 185, 129, 0.25)' }}>{profileMessage}</div>}

                    <div className="form-group mb-4">
                        <div className="form-label">{t('common.profile_page.username')}</div>
                        <div style={{ padding: '12px', background: 'var(--bg-hover)', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                            {user.username}
                        </div>
                    </div>

                    <div className="form-group mb-4">
                        <label className="form-label" htmlFor="full_name_input">{t('common.profile_page.full_name', 'الاسم الكامل')}</label>
                        <input
                            id="full_name_input"
                            className="form-input"
                            value={profileForm.full_name}
                            onChange={(e) => setProfileForm((prev) => ({ ...prev, full_name: e.target.value }))}
                            required
                        />
                    </div>

                    <div className="form-group mb-4">
                        <label className="form-label" htmlFor="email_input">{t('common.profile_page.email')}</label>
                        <input
                            id="email_input"
                            type="email"
                            className="form-input"
                            placeholder={t('common.profile_page.not_set')}
                            value={profileForm.email}
                            onChange={(e) => setProfileForm((prev) => ({ ...prev, email: e.target.value }))}
                        />
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '24px' }}>
                        <button type="submit" className="btn btn-primary" disabled={savingProfile}>
                            {savingProfile ? t('common.saving', 'جار الحفظ...') : t('common.save', 'حفظ التعديلات')}
                        </button>
                    </div>
                </form>

                <hr style={{ border: 0, borderTop: '1px solid var(--border-color)', margin: '8px 0 24px 0' }} />

                <form onSubmit={handlePasswordSave}>
                    <h3 style={{ marginBottom: '16px' }}>{t('common.profile_page.change_password', 'تغيير كلمة المرور')}</h3>
                    {passwordError && <div className="alert alert-error">{passwordError}</div>}
                    {passwordMessage && <div className="alert" style={{ background: 'rgba(16, 185, 129, 0.12)', color: 'var(--success)', border: '1px solid rgba(16, 185, 129, 0.25)' }}>{passwordMessage}</div>}

                    <div className="form-group mb-4">
                        <label className="form-label" htmlFor="current_password_input">{t('common.profile_page.current_password', 'كلمة المرور الحالية')}</label>
                        <div className="input-group">
                            <input
                                id="current_password_input"
                                type={showPasswords.current ? 'text' : 'password'}
                                className="form-input"
                                value={passwordForm.current_password}
                                onChange={(e) => setPasswordForm((prev) => ({ ...prev, current_password: e.target.value }))}
                                required
                            />
                            <button className="btn btn-light" type="button" onClick={() => togglePasswordVisibility('current')}>
                                {showPasswords.current ? t('common.hide', 'إخفاء') : t('common.show', 'إظهار')}
                            </button>
                        </div>
                    </div>

                    <div className="form-group mb-4">
                        <label className="form-label" htmlFor="new_password_input">{t('common.profile_page.new_password', 'كلمة المرور الجديدة')}</label>
                        <div className="input-group">
                            <input
                                id="new_password_input"
                                type={showPasswords.next ? 'text' : 'password'}
                                className="form-input"
                                value={passwordForm.new_password}
                                onChange={(e) => setPasswordForm((prev) => ({ ...prev, new_password: e.target.value }))}
                                required
                                minLength={8}
                            />
                            <button className="btn btn-light" type="button" onClick={() => togglePasswordVisibility('next')}>
                                {showPasswords.next ? t('common.hide', 'إخفاء') : t('common.show', 'إظهار')}
                            </button>
                        </div>
                    </div>

                    <div className="form-group mb-4">
                        <label className="form-label" htmlFor="confirm_password_input">{t('common.profile_page.confirm_password', 'تأكيد كلمة المرور')}</label>
                        <div className="input-group">
                            <input
                                id="confirm_password_input"
                                type={showPasswords.confirm ? 'text' : 'password'}
                                className="form-input"
                                value={passwordForm.confirm_password}
                                onChange={(e) => setPasswordForm((prev) => ({ ...prev, confirm_password: e.target.value }))}
                                required
                            />
                            <button className="btn btn-light" type="button" onClick={() => togglePasswordVisibility('confirm')}>
                                {showPasswords.confirm ? t('common.hide', 'إخفاء') : t('common.show', 'إظهار')}
                            </button>
                        </div>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                        <button type="submit" className="btn btn-primary" disabled={savingPassword}>
                            {savingPassword ? t('common.saving', 'جار الحفظ...') : t('common.profile_page.save_password', 'تحديث كلمة المرور')}
                        </button>
                    </div>
                </form>

                {companyId && (
                    <div className="form-group mb-4">
                        <div className="form-label">{t('common.profile_page.company_id')}</div>
                        <div style={{ padding: '12px', background: 'var(--bg-hover)', borderRadius: '8px', border: '1px solid var(--border-color)', fontFamily: 'monospace' }}>
                            {companyId}
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}

export default UserProfile
