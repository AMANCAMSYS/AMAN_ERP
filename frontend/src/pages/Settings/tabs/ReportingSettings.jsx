import React from 'react';
import { useTranslation } from 'react-i18next';
import { FileText, Printer } from 'lucide-react';

const ReportingSettings = ({ settings, handleSettingChange }) => {
    const { t } = useTranslation();

    return (
        <div className="space-y-8">
            {/* Header & Footer */}
            <div className="bg-base-50 p-6 rounded-2xl border border-base-200">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <FileText size={20} className="text-primary" />
                    {t('settings.reporting.header_title') || 'ترويسة وتذييل التقارير'}
                </h3>

                <div className="form-group mb-6">
                    <label className="form-label">{t('settings.reporting.report_header') || 'نص الترويسة (Header)'}</label>
                    <textarea
                        className="form-input min-h-[80px]"
                        value={settings.report_header_text || ''}
                        onChange={(e) => handleSettingChange('report_header_text', e.target.value)}
                        placeholder={t("settings.reporting.company_placeholder")}
                    ></textarea>
                </div>

                <div className="form-group">
                    <label className="form-label">{t('settings.reporting.report_footer') || 'نص التذييل (Footer)'}</label>
                    <textarea
                        className="form-input min-h-[80px]"
                        value={settings.report_footer_text || ''}
                        onChange={(e) => handleSettingChange('report_footer_text', e.target.value)}
                        placeholder={t("settings.reporting.address_placeholder")}
                    ></textarea>
                </div>
            </div>

            {/* Print Options */}
            <div className="bg-base-50 p-6 rounded-2xl border border-base-200">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <Printer size={20} className="text-primary" />
                    {t('settings.reporting.print_options') || 'خيارات الطباعة'}
                </h3>
                <div className="flex items-center gap-3">
                    <input
                        type="checkbox"
                        className="checkbox checkbox-primary"
                        id="report_show_logo"
                        checked={settings.report_show_logo === 'true'}
                        onChange={(e) => handleSettingChange('report_show_logo', e.target.checked.toString())}
                    />
                    <label className="cursor-pointer font-medium" htmlFor="report_show_logo">
                        {t('settings.reporting.show_logo') || 'إظهار الشعار في التقارير'}
                    </label>
                </div>
            </div>
        </div>
    );
};

export default ReportingSettings;
