import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ShieldCheck, FileKey, Globe, Loader } from 'lucide-react';
import api from '../../../utils/api';
import { useToast } from '../../../context/ToastContext';

const ComplianceSettings = ({ settings, handleSettingChange }) => {
    const { t } = useTranslation();
    const { showToast } = useToast();
    const [generating, setGenerating] = useState(false);

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
                throw new Error(response.data.message || "Failed");
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
                            placeholder="e.g. Aman Trading Est."
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

            {/* Environment */}
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
        </div>
    );
};

export default ComplianceSettings;
