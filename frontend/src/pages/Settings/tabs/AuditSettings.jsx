import React from 'react';
import { useTranslation } from 'react-i18next';
import { FileText, Clock, Shield } from 'lucide-react';

const AuditSettings = ({ settings, handleSettingChange }) => {
    const { t } = useTranslation();

    return (
        <div className="space-y-8">
            {/* Log Retention */}
            <div className="bg-base-50 p-6 rounded-2xl border border-base-200">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <Clock size={20} className="text-primary" />
                    {t('settings.audit.retention_title')}
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="form-group">
                        <label className="form-label">{t('settings.audit.activity_logs')}</label>
                        <select
                            className="form-input"
                            value={settings.audit_retention_days || '365'}
                            onChange={(e) => handleSettingChange('audit_retention_days', e.target.value)}
                        >
                            <option value="90">90 {t('common.days')}</option>
                            <option value="180">180 {t('common.days')}</option>
                            <option value="365">1 {t('common.year')}</option>
                            <option value="1095">3 {t('common.years')}</option>
                            <option value="3650">10 {t('common.years')}</option>
                        </select>
                    </div>

                    <div className="form-group">
                        <label className="form-label">{t('settings.audit.login_history')}</label>
                        <select
                            className="form-input"
                            value={settings.audit_login_retention || '90'}
                            onChange={(e) => handleSettingChange('audit_login_retention', e.target.value)}
                        >
                            <option value="30">30 {t('common.days')}</option>
                            <option value="90">90 {t('common.days')}</option>
                            <option value="180">6 {t('common.months')}</option>
                        </select>
                    </div>
                </div>
            </div>

            {/* Detailed Logging */}
            <div className="bg-base-50 p-6 rounded-2xl border border-base-200">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <Shield size={20} className="text-primary" />
                    {t('settings.audit.level_title')}
                </h3>

                <div className="space-y-3">
                    <div className="flex items-center gap-3">
                        <input
                            type="checkbox"
                            className="checkbox checkbox-primary"
                            id="audit_log_sensitive"
                            checked={settings.audit_log_sensitive === 'true'}
                            onChange={(e) => handleSettingChange('audit_log_sensitive', e.target.checked.toString())}
                        />
                        <div>
                            <label className="cursor-pointer font-medium block" htmlFor="audit_log_sensitive">
                                {t('settings.audit.log_sensitive')}
                            </label>
                            <p className="text-xs text-base-content/40 mt-1">
                                {t('settings.audit.sensitive_hint')}
                            </p>
                        </div>
                    </div>

                    <div className="flex items-center gap-3">
                        <input
                            type="checkbox"
                            className="checkbox checkbox-primary"
                            id="audit_log_view"
                            checked={settings.audit_log_view === 'true'}
                            onChange={(e) => handleSettingChange('audit_log_view', e.target.checked.toString())}
                        />
                        <label className="cursor-pointer font-medium" htmlFor="audit_log_view">
                            {t('settings.audit.log_view')}
                        </label>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AuditSettings;
