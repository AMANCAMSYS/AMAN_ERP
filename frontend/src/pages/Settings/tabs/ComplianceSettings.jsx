import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ShieldCheck, FileKey, Globe, Loader, Clock } from 'lucide-react';
import api from '../../../utils/api';
import { useToast } from '../../../context/ToastContext';
import { getCountry } from '../../../utils/auth';

// Countries with full ZATCA / Zakat compliance support
const ZATCA_SUPPORTED_COUNTRIES = ['SA'];

const COUNTRY_FLAGS = {
    SA: '🇸🇦', SY: '🇸🇾', AE: '🇦🇪', EG: '🇪🇬', JO: '🇯🇴',
    KW: '🇰🇼', BH: '🇧🇭', OM: '🇴🇲', QA: '🇶🇦', IQ: '🇮🇶',
    LB: '🇱🇧', TR: '🇹🇷'
};

const ComingSoonCard = ({ icon, title }) => {
    const { t } = useTranslation();
    const country = getCountry();
    const flag = COUNTRY_FLAGS[country] || '🌍';
    return (
        <div className="bg-base-50 p-6 rounded-2xl border border-base-200">
            <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                {icon}
                {title}
            </h3>
            <div className="flex flex-col items-center justify-center py-10 text-center gap-4">
                <div style={{ fontSize: '48px' }}>{flag}</div>
                <div className="flex items-center gap-2 text-muted">
                    <Clock size={20} />
                    <span className="text-xl font-semibold">{t('coming_soon.title', 'قريباً')}</span>
                </div>
                <p className="text-muted max-w-md">
                    {t('settings.compliance.coming_soon_country', 'خيار الزكاة والامتثال الضريبي غير مدعوم بعد لدولتك. سيتم تفعيله في التحديثات القادمة.')}
                </p>
            </div>
        </div>
    );
};

const ComplianceSettings = ({ settings, handleSettingChange }) => {
    const { t } = useTranslation();
    const { showToast } = useToast();
    const [generating, setGenerating] = useState(false);
    const country = getCountry();
    const isSupported = ZATCA_SUPPORTED_COUNTRIES.includes(country);

    const generateCSID = async () => {
        setGenerating(true);
        try {
            const response = await api.post('/settings/generate-csid', { settings });
            if (response.data.success) {
                showToast(response.data.message, 'success');
                // You might want to update the settings with the new CSID if backend returned it, 
                // but currently we just show toast. 
                // In a real app, we would update 'zatca_csid' setting.
            } else {
                throw new Error(response.data.message || t('common.error_occurred'));
            }
        } catch (err) {
            console.error("CSID generation failed", err);
            showToast(err.response?.data?.detail || t('common.error_occurred'), 'error');
        } finally {
            setGenerating(false);
        }
    };

    return (
        <div className="space-y-8">
            {/* ZATCA Phase 2 */}
            {!isSupported ? (
                <ComingSoonCard
                    icon={<ShieldCheck size={20} className="text-primary" />}
                    title={t('settings.compliance.zatca_title')}
                />
            ) : (
            <div className="bg-base-50 p-6 rounded-2xl border border-base-200">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <ShieldCheck size={20} className="text-primary" />
                    {t('settings.compliance.zatca_title')}
                </h3>

                <div className="alert alert-info mb-6">
                    <span>{t('settings.compliance.zatca_info')}</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="form-group">
                        <label className="form-label">{t('settings.compliance.csr_common_name')}</label>
                        <input
                            type="text"
                            className="form-input"
                            value={settings.zatca_csr_common_name || ''}
                            onChange={(e) => handleSettingChange('zatca_csr_common_name', e.target.value)}
                            placeholder={t('settings.compliance.company_name_placeholder')}
                        />
                    </div>
                    <div className="form-group">
                        <label className="form-label">{t('settings.compliance.csr_serial_number')}</label>
                        <input
                            type="text"
                            className="form-input"
                            value={settings.zatca_csr_serial_number || ''}
                            onChange={(e) => handleSettingChange('zatca_csr_serial_number', e.target.value)}
                            placeholder="1-700XXXXXXXX"
                        />
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4">
                    <div className="form-group">
                        <label className="form-label">{t('settings.compliance.otp')}</label>
                        <div className="flex gap-2">
                            <input
                                type="text"
                                className="form-input"
                                value={settings.zatca_otp || ''}
                                onChange={(e) => handleSettingChange('zatca_otp', e.target.value)}
                                placeholder="123456"
                            />
                            <button
                                type="button"
                                className="btn btn-primary min-w-[140px]"
                                onClick={generateCSID}
                                disabled={generating || !settings.zatca_otp}
                            >
                                {generating ? <Loader size={18} className="animate-spin" /> : (t('settings.compliance.generate_csid'))}
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            )}

            {/* Environment */}
            {!isSupported ? (
                <ComingSoonCard
                    icon={<Globe size={20} className="text-primary" />}
                    title={t('settings.compliance.env_title')}
                />
            ) : (
            <div className="bg-base-50 p-6 rounded-2xl border border-base-200">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <Globe size={20} className="text-primary" />
                    {t('settings.compliance.env_title')}
                </h3>
                <div className="flex gap-6">
                    <label className="flex items-center gap-2 cursor-pointer">
                        <input
                            type="radio"
                            name="zatca_env"
                            className="radio radio-primary"
                            checked={settings.zatca_env === 'sandbox'}
                            onChange={() => handleSettingChange('zatca_env', 'sandbox')}
                        />
                        <span>{t('settings.compliance.env_sandbox')}</span>
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer">
                        <input
                            type="radio"
                            name="zatca_env"
                            className="radio radio-primary"
                            checked={settings.zatca_env === 'production'}
                            onChange={() => handleSettingChange('zatca_env', 'production')}
                        />
                        <span>{t('settings.compliance.env_production')}</span>
                    </label>
                </div>
            </div>
            )}
        </div>
    );
};

export default ComplianceSettings;
