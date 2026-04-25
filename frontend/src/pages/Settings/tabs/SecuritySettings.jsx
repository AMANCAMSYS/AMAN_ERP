import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { ShieldCheck, Key, Clock, Smartphone, Trash2, AlertTriangle, Monitor } from 'lucide-react';
import api from '../../../utils/api';
import { useToast } from '../../../context/ToastContext';
import SimpleModal from '../../../components/common/SimpleModal';

const SecuritySettings = ({ settings, handleSettingChange }) => {
    const { t } = useTranslation();
    const { showToast } = useToast();

    // Sessions State
    const [sessions, setSessions] = useState([]);
    const [loadingSessions, setLoadingSessions] = useState(false);

    // 2FA State
    const [is2FAEnabled, setIs2FAEnabled] = useState(false);
    const [show2FAModal, setShow2FAModal] = useState(false);
    const [twoFAStep, setTwoFAStep] = useState('setup'); // setup, verify, success, disable
    const [twoFASecret, setTwoFASecret] = useState('');
    const [otpCode, setOtpCode] = useState('');
    const [backupCodes, setBackupCodes] = useState([]);
    const [verifying, setVerifying] = useState(false);

    // Load initial data
    useEffect(() => {
        fetchSessions();
        check2FAStatus();
    }, []);

    const fetchSessions = async () => {
        setLoadingSessions(true);
        try {
            const response = await api.get('/security/sessions');
            setSessions(response.data.sessions || []);
        } catch (error) {
            console.error("Failed to fetch sessions", error);
        } finally {
            setLoadingSessions(false);
        }
    };

    const check2FAStatus = async () => {
        try {
            const response = await api.get('/security/2fa/status');
            setIs2FAEnabled(response.data.is_enabled);
        } catch (error) {
            console.error("Failed to check 2FA status", error);
        }
    };

    const handleTerminateSession = async (sessionId) => {
        if (!window.confirm(t('common.confirm_action'))) return;
        try {
            await api.delete(`/security/sessions/${sessionId}`);
            showToast(t('settings.security.session_terminated'), 'success');
            fetchSessions();
        } catch (error) {
            showToast(t('common.error'), 'error');
        }
    };

    const handleTerminateAllSessions = async () => {
        if (!window.confirm(t('settings.security.confirm_terminate_all'))) return;
        try {
            await api.delete('/security/sessions');
            showToast(t('settings.security.all_sessions_terminated'), 'success');
            fetchSessions();
        } catch (error) {
            showToast(t('common.error'), 'error');
        }
    };

    // 2FA Handlers
    const handleToggle2FA = async () => {
        if (is2FAEnabled) {
            // Start disable flow
            setTwoFAStep('disable');
            setOtpCode('');
            setShow2FAModal(true);
        } else {
            // Start setup flow
            try {
                const response = await api.post('/security/2fa/setup');
                setTwoFASecret(response.data.secret);
                setTwoFAStep('setup');
                setOtpCode('');
                setShow2FAModal(true);
            } catch (error) {
                showToast(error.response?.data?.detail || t('security_page.two_factor.setup_failed'), 'error');
            }
        }
    };

    const verify2FA = async () => {
        setVerifying(true);
        try {
            const endpoint = twoFAStep === 'disable' ? '/security/2fa/disable' : '/security/2fa/verify';
            const response = await api.post(endpoint, { code: otpCode });

            if (twoFAStep === 'disable') {
                setIs2FAEnabled(false);
                setShow2FAModal(false);
                showToast(t('settings.security.2fa_disabled'), 'success');
            } else {
                // Enabled successfully
                setIs2FAEnabled(true);
                setBackupCodes(response.data.backup_codes || []);
                setTwoFAStep('success');
                showToast(t('settings.security.2fa_enabled'), 'success');
            }
        } catch (error) {
            showToast(error.response?.data?.detail || t('security_page.two_factor.verification_failed'), 'error');
        } finally {
            setVerifying(false);
        }
    };

    return (
        <div className="space-y-8">
            {/* Password Policy */}
            <div className="bg-base-50 p-6 rounded-2xl border border-base-200">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <Key size={20} className="text-primary" />
                    {t('settings.security.password_title') || t('settings.security.password_policy')}
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="flex items-center gap-3">
                        <input
                            type="checkbox"
                            className="checkbox checkbox-primary"
                            id="security_complex_password"
                            checked={settings.security_complex_password === 'true'}
                            onChange={(e) => handleSettingChange('security_complex_password', e.target.checked.toString())}
                        />
                        <label className="cursor-pointer font-medium" htmlFor="security_complex_password">
                            {t('settings.security.complex_password') || t('settings.security.complex_passwords')}
                        </label>
                    </div>

                    <div className="form-group">
                        <label className="form-label">{t('settings.security.password_expiry') || t('settings.security.password_expiry')}</label>
                        <select
                            className="form-input"
                            value={settings.security_password_expiry || '0'}
                            onChange={(e) => handleSettingChange('security_password_expiry', e.target.value)}
                        >
                            <option value="0">{t('common.never') || t('settings.security.never_expire')}</option>
                            <option value="30">30 {t('common.days') || 'days'}</option>
                            <option value="60">60 {t('common.days') || 'days'}</option>
                            <option value="90">90 {t('common.days') || 'days'}</option>
                            <option value="180">180 {t('common.days') || 'days'}</option>
                        </select>
                    </div>
                </div>
            </div>

            {/* Session Management */}
            <div className="bg-base-50 p-6 rounded-2xl border border-base-200">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <Clock size={20} className="text-primary" />
                    {t('settings.security.session_title')}
                </h3>

                {/* Session Timeout Config */}
                <div className="mb-6 grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="form-group">
                        <label className="form-label">{t('settings.security.session_timeout')}</label>
                        <input
                            type="number"
                            className="form-input"
                            value={settings.security_session_timeout || '30'}
                            onChange={(e) => handleSettingChange('security_session_timeout', e.target.value)}
                            min="5"
                            max="1440"
                        />
                        <p className="text-xs text-base-content/40 mt-1">
                            {t('settings.security.timeout_hint')}
                        </p>
                    </div>
                </div>

                {/* Active Sessions List */}
                <div className="overflow-x-auto">
                    <div className="flex justify-between items-center mb-2">
                        <h4 className="font-semibold">{t('security_page.sessions.title')}</h4>
                        <button onClick={handleTerminateAllSessions} className="btn btn-xs btn-error btn-outline">
                            {t('security_page.sessions.terminate_all')}
                        </button>
                    </div>
                    <table className="table table-zebra w-full text-sm">
                        <thead>
                            <tr>
                                <th>{t('security_page.sessions.device')}</th>
                                <th>{t('security_page.sessions.ip_address')}</th>
                                <th>{t('security_page.sessions.last_active')}</th>
                                <th></th>
                            </tr>
                        </thead>
                        <tbody>
                            {loadingSessions ? (
                                <tr><td colSpan="4" className="text-center p-4">{t('common.loading')}</td></tr>
                            ) : sessions.length === 0 ? (
                                <tr><td colSpan="4" className="text-center p-4">{t('security_page.sessions.no_sessions')}</td></tr>
                            ) : (
                                sessions.map((session) => (
                                    <tr key={session.id}>
                                        <td className="flex items-center gap-2">
                                            {session.user_agent?.includes('Mobile') ? <Smartphone size={16} /> : <Monitor size={16} />}
                                            <span className="truncate max-w-[200px]" title={session.user_agent}>
                                                {session.user_agent || t('security_page.sessions.unknown_device')}
                                            </span>
                                        </td>
                                        <td>{session.ip_address}</td>
                                        <td>{session.last_activity}</td>
                                        <td className="text-end">
                                            <button
                                                onClick={() => handleTerminateSession(session.id)}
                                                className="btn btn-ghost btn-xs text-error"
                                                title={t('security_page.sessions.terminate')}
                                            >
                                                <Trash2 size={16} />
                                            </button>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* 2FA */}
            <div className="bg-base-50 p-6 rounded-2xl border border-base-200">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <ShieldCheck size={20} className="text-primary" />
                    {t('settings.security.2fa_title') || t('security_page.two_factor.title')}
                </h3>
                <div className="flex items-center justify-between">
                    <div>
                        <p className="font-medium">{t('security_page.two_factor.enable')}</p>
                        <p className="text-sm text-base-content/60">
                            {is2FAEnabled
                                ? t('security_page.two_factor.status_enabled')
                                : t('security_page.two_factor.protect_desc')}
                        </p>
                    </div>
                    <input
                        type="checkbox"
                        className="toggle toggle-primary"
                        checked={is2FAEnabled}
                        onChange={handleToggle2FA}
                    />
                </div>
            </div>

            {/* 2FA Modal */}
            <SimpleModal
                isOpen={show2FAModal}
                onClose={() => setShow2FAModal(false)}
                title={twoFAStep === 'setup' ? t('security_page.two_factor.setup_title') : twoFAStep === 'disable' ? t('security_page.two_factor.disable_title') : t('security_page.two_factor.enabled_title')}
            >
                <div className="p-4 space-y-4">
                    {twoFAStep === 'setup' && (
                        <>
                            <div className="bg-base-200 p-4 rounded text-center">
                                <p className="text-sm mb-2 font-bold">{t('security_page.two_factor.secret_key')}</p>
                                <code className="bg-base-300 p-2 rounded text-lg tracking-wider mb-2 block select-all">
                                    {twoFASecret}
                                </code>
                                <p className="text-xs opacity-70">{t('security_page.two_factor.enter_key_hint')}</p>
                            </div>

                            <div className="form-group">
                                <label className="label">{t('security_page.two_factor.verification_code')}</label>
                                <input
                                    type="text"
                                    className="input input-bordered w-full text-center text-lg tracking-widest"
                                    placeholder="000 000"
                                    value={otpCode}
                                    onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                                />
                            </div>
                            <button
                                className="btn btn-primary w-full"
                                onClick={verify2FA}
                                disabled={otpCode.length !== 6 || verifying}
                            >
                                {verifying ? t('security_page.two_factor.verifying') : t('security_page.two_factor.verify_enable')}
                            </button>
                        </>
                    )}

                    {twoFAStep === 'disable' && (
                        <>
                            <p>{t('security_page.two_factor.disable_hint')}</p>
                            <div className="form-group">
                                <input
                                    type="text"
                                    className="input input-bordered w-full text-center text-lg tracking-widest"
                                    placeholder="000 000"
                                    value={otpCode}
                                    onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                                />
                            </div>
                            <button
                                className="btn btn-error w-full"
                                onClick={verify2FA}
                                disabled={otpCode.length !== 6 || verifying}
                            >
                                {verifying ? t('security_page.two_factor.verifying') : t('security_page.two_factor.disable_btn')}
                            </button>
                        </>
                    )}

                    {twoFAStep === 'success' && (
                        <div className="text-center space-y-4">
                            <CheckCircle size={48} className="text-success mx-auto" />
                            <h3 className="text-lg font-bold text-success">{t('security_page.two_factor.enabled_success')}</h3>

                            <div className="bg-warning/10 p-4 rounded border border-warning/20 text-left">
                                <div className="flex items-center gap-2 text-warning mb-2">
                                    <AlertTriangle size={18} />
                                    <span className="font-bold">{t('security_page.two_factor.backup_codes_title')}</span>
                                </div>
                                <p className="text-xs mb-3">{t('security_page.two_factor.backup_codes_warning')}</p>
                                <div className="grid grid-cols-2 gap-2 font-mono text-sm">
                                    {backupCodes.map(code => (
                                        <span key={code} className="bg-base-100 p-1 rounded">{code}</span>
                                    ))}
                                </div>
                            </div>

                            <button className="btn btn-outline w-full" onClick={() => setShow2FAModal(false)}>{t('security_page.two_factor.done')}</button>
                        </div>
                    )}
                </div>
            </SimpleModal>
        </div>
    );
};

export default SecuritySettings;
