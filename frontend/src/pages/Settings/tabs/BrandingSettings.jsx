import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Upload, X, Check, Image as ImageIcon } from 'lucide-react';
import api from '../../../utils/api';
import { useToast } from '../../../context/ToastContext';

const BrandingSettings = ({ settings, handleSettingChange, companyId }) => {
    const { t } = useTranslation();
    const { showToast } = useToast();
    const [uploading, setUploading] = useState(false);
    const [preview, setPreview] = useState(settings.company_logo || null);

    const handleLogoUpload = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        // Preview
        const reader = new FileReader();
        reader.onloadend = () => setPreview(reader.result);
        reader.readAsDataURL(file);

        // Upload
        const formData = new FormData();
        formData.append('file', file);

        setUploading(true);
        try {
            const response = await api.post(`/companies/upload-logo/${companyId}`, formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            handleSettingChange('company_logo', response.data.logo_url);
            showToast(t('settings.branding.logo_success'), 'success');
        } catch (err) {
            console.error("Logo upload failed", err);
            showToast(t('settings.branding.logo_error'), 'error');
        } finally {
            setUploading(false);
        }
    };

    const removeLogo = () => {
        setPreview(null);
        handleSettingChange('company_logo', '');
    };

    return (
        <div className="space-y-8">
            {/* Logo Upload Section */}
            <div className="bg-base-50 p-6 rounded-2xl border border-base-200">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <ImageIcon size={20} className="text-primary" />
                    {t('settings.branding.logo_title')}
                </h3>
                <div className="flex flex-col md:flex-row items-center gap-8">
                    <div className="relative group">
                        <div className="w-40 h-40 rounded-2xl bg-base-100 border-2 border-dashed border-base-300 flex items-center justify-center overflow-hidden relative">
                            {preview ? (
                                <img
                                    src={preview.startsWith('data:') ? preview : `${import.meta.env.VITE_API_URL}${preview}`}
                                    alt="Logo Preview"
                                    className="w-full h-full object-contain"
                                />
                            ) : (
                                <div className="text-base-content/30 flex flex-col items-center">
                                    <Upload size={32} />
                                    <span className="text-xs mt-2">{t('settings.branding.no_logo')}</span>
                                </div>
                            )}

                            {uploading && (
                                <div className="absolute inset-0 bg-base-100/80 flex items-center justify-center">
                                    <span className="loading loading-spinner text-primary"></span>
                                </div>
                            )}
                        </div>

                        {preview && (
                            <button
                                onClick={removeLogo}
                                className="absolute -top-2 -right-2 p-1 bg-error text-error-content rounded-full shadow-lg opacity-0 group-hover:opacity-100 transition-opacity"
                            >
                                <X size={16} />
                            </button>
                        )}
                    </div>

                    <div className="flex-1 space-y-4">
                        <p className="text-sm text-base-content/60 leading-relaxed">
                            {t('settings.branding.logo_hint')}
                        </p>
                        <label className="btn btn-primary btn-outline gap-2">
                            <Upload size={18} />
                            {t('settings.branding.upload_btn')}
                            <input
                                type="file"
                                className="hidden"
                                accept="image/*"
                                onChange={handleLogoUpload}
                                disabled={uploading}
                            />
                        </label>
                    </div>
                </div>
            </div>

            {/* Color Selection Section */}
            <div className="bg-base-50 p-6 rounded-2xl border border-base-200">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <div className="w-5 h-5 rounded-full bg-primary"></div>
                    {t('settings.branding.theme_title')}
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="form-group">
                        <label className="form-label">{t('settings.branding.primary_color')}</label>
                        <div className="flex items-center gap-3">
                            <input
                                type="color"
                                className="w-12 h-12 rounded-lg cursor-pointer bg-transparent border-none"
                                value={settings.primary_color || '#2563eb'}
                                onChange={(e) => handleSettingChange('primary_color', e.target.value)}
                            />
                            <input
                                type="text"
                                className="form-input font-mono flex-1"
                                value={settings.primary_color || '#2563eb'}
                                onChange={(e) => handleSettingChange('primary_color', e.target.value)}
                            />
                        </div>
                    </div>
                </div>
                <p className="text-xs text-base-content/40 mt-4">
                    {t('settings.branding.theme_hint')}
                </p>
            </div>
        </div>
    );
};

export default BrandingSettings;
