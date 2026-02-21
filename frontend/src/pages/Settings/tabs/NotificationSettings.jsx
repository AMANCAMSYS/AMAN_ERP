import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Mail, Bell, Server, CheckCircle, XCircle } from 'lucide-react';
import api from '../../../utils/api';
import { useToast } from '../../../context/ToastContext';

const NotificationSettings = ({ settings, handleSettingChange }) => {
    const { t } = useTranslation();
    const { showToast } = useToast();
    const [testing, setTesting] = useState(false);

    // Test email connection via backend
    const testEmailConnection = async () => {
        setTesting(true);
        try {
            const response = await api.post('/settings/test-email', { settings });
            if (response.data.success) {
                showToast(response.data.message || t('settings.notifications.test_success'), 'success');
            } else {
                throw new Error(response.data.message || "Failed");
            }
        } catch (err) {
            console.error("Email test failed", err);
            showToast(err.response?.data?.detail || t('settings.notifications.test_failed'), 'error');
        } finally {
            setTesting(false);
        }
    };

    return (
        <div className="space-y-8">
            {/* SMTP Configuration */}
            <div className="bg-base-50 p-6 rounded-2xl border border-base-200">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <Server size={20} className="text-primary" />
                    {t('settings.notifications.smtp_title') || 'إعدادات خادم البريد (SMTP)'}
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="form-group">
                        <label className="form-label">{t('settings.notifications.smtp_host') || 'عنوان الخادم (Host)'}</label>
                        <input
                            type="text"
                            className="form-input ltr"
                            value={settings.smtp_host || ''}
                            onChange={(e) => handleSettingChange('smtp_host', e.target.value)}
                            placeholder="smtp.gmail.com"
                        />
                    </div>
                    <div className="form-group">
                        <label className="form-label">{t('settings.notifications.smtp_port') || 'المنفذ (Port)'}</label>
                        <input
                            type="number"
                            className="form-input ltr"
                            value={settings.smtp_port || '587'}
                            onChange={(e) => handleSettingChange('smtp_port', e.target.value)}
                            placeholder="587"
                        />
                    </div>
                    <div className="form-group">
                        <label className="form-label">{t('settings.notifications.smtp_user') || 'اسم المستخدم (Email)'}</label>
                        <input
                            type="email"
                            className="form-input ltr"
                            value={settings.smtp_user || ''}
                            onChange={(e) => handleSettingChange('smtp_user', e.target.value)}
                        />
                    </div>
                    <div className="form-group">
                        <label className="form-label">{t('settings.notifications.smtp_pass') || 'كلمة المرور (Password/App Key)'}</label>
                        <input
                            type="password"
                            className="form-input ltr"
                            value={settings.smtp_pass || ''}
                            onChange={(e) => handleSettingChange('smtp_pass', e.target.value)}
                        />
                    </div>
                </div>

                <div className="mt-6 flex justify-end">
                    <button
                        type="button"
                        className="btn btn-ghost gap-2 border-base-300"
                        onClick={testEmailConnection}
                        disabled={testing}
                    >
                        {testing ? <span className="loading loading-spinner loading-xs"></span> : <CheckCircle size={18} />}
                        {t('settings.notifications.test_conn') || 'اختبار الاتصال'}
                    </button>
                </div>
            </div>

            {/* SMS Gateway Configuration */}
            <div className="bg-base-50 p-6 rounded-2xl border border-base-200">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <Mail size={20} className="text-primary" />
                    {t('settings.notifications.sms_title') || 'إعدادات الرسائل النصية (SMS)'}
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="form-group">
                        <label className="form-label">Provider</label>
                        <select
                            className="form-input"
                            value={settings.sms_provider || ''}
                            onChange={(e) => handleSettingChange('sms_provider', e.target.value)}
                        >
                            <option value="">Select Provider</option>
                            <option value="twilio">Twilio</option>
                            <option value="infobip">Infobip</option>
                        </select>
                    </div>
                    <div className="form-group">
                        <label className="form-label">Account SID / API Key</label>
                        <input
                            type="text"
                            className="form-input ltr"
                            value={settings.sms_account_sid || ''}
                            onChange={(e) => handleSettingChange('sms_account_sid', e.target.value)}
                        />
                    </div>
                    <div className="form-group">
                        <label className="form-label">Auth Token / Secret</label>
                        <input
                            type="password"
                            className="form-input ltr"
                            value={settings.sms_auth_token || ''}
                            onChange={(e) => handleSettingChange('sms_auth_token', e.target.value)}
                        />
                    </div>
                    <div className="form-group">
                        <label className="form-label">Sender Name / Number</label>
                        <input
                            type="text"
                            className="form-input ltr"
                            value={settings.sms_from_number || ''}
                            onChange={(e) => handleSettingChange('sms_from_number', e.target.value)}
                            placeholder="AMAN_ERP"
                        />
                    </div>
                </div>
            </div>

            {/* Alerts */}
            <div className="bg-base-50 p-6 rounded-2xl border border-base-200">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <Bell size={20} className="text-primary" />
                    {t('settings.notifications.alerts_title') || 'التنبيهات التلقائية'}
                </h3>
                <div className="space-y-4">
                    <div className="flex items-center gap-3">
                        <input
                            type="checkbox"
                            className="checkbox checkbox-primary"
                            id="notify_low_stock"
                            checked={settings.notify_low_stock === 'true'}
                            onChange={(e) => handleSettingChange('notify_low_stock', e.target.checked.toString())}
                        />
                        <label className="cursor-pointer font-medium" htmlFor="notify_low_stock">
                            {t('settings.notifications.notify_low_stock') || 'إرسال تنبيه عند وصول المخزون للحد الأدنى'}
                        </label>
                    </div>

                    <div className="flex items-center gap-3">
                        <input
                            type="checkbox"
                            className="checkbox checkbox-primary"
                            id="notify_new_invoice"
                            checked={settings.notify_new_invoice === 'true'}
                            onChange={(e) => handleSettingChange('notify_new_invoice', e.target.checked.toString())}
                        />
                        <label className="cursor-pointer font-medium" htmlFor="notify_new_invoice">
                            {t('settings.notifications.notify_new_invoice') || 'إرسال نسخة من الفاتورة للعميل (إذا توفر الإيميل)'}
                        </label>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default NotificationSettings;
