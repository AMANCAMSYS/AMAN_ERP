import React from 'react';
import { useTranslation } from 'react-i18next';

const GeneralSettings = ({ formData, handleChange }) => {
    const { t } = useTranslation();

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="form-group">
                <label className="form-label" htmlFor="company_name">{t('settings.company.name') || '{t("settings.general.company_name")}'}</label>
                <input
                    type="text"
                    id="company_name"
                    name="company_name"
                    className="form-input"
                    value={formData.company_name}
                    onChange={handleChange}
                    required
                    autoComplete="organization"
                />
            </div>

            <div className="form-group">
                <label className="form-label" htmlFor="company_name_en">{t('settings.company.name_en') || '{t("settings.general.name_en")}'}</label>
                <input
                    type="text"
                    id="company_name_en"
                    name="company_name_en"
                    className="form-input"
                    value={formData.company_name_en}
                    onChange={handleChange}
                    autoComplete="organization"
                />
            </div>

            <div className="form-group">
                <label className="form-label" htmlFor="email">{t('settings.company.email') || '{t("settings.general.email")}'}</label>
                <input
                    type="email"
                    id="email"
                    name="email"
                    className="form-input"
                    value={formData.email}
                    onChange={handleChange}
                    required
                    autoComplete="email"
                />
            </div>

            <div className="form-group">
                <label className="form-label" htmlFor="phone">{t('settings.company.phone') || '{t("settings.general.phone")}'}</label>
                <input
                    type="text"
                    id="phone"
                    name="phone"
                    className="form-input"
                    value={formData.phone}
                    onChange={handleChange}
                    dir="ltr"
                    autoComplete="tel"
                />
            </div>

            <div className="form-group md:col-span-2">
                <label className="form-label" htmlFor="address">{t('settings.company.address') || '{t("settings.general.address")}'}</label>
                <textarea
                    id="address"
                    name="address"
                    className="form-input"
                    rows="2"
                    value={formData.address}
                    onChange={handleChange}
                    autoComplete="street-address"
                ></textarea>
            </div>

            <div className="form-group">
                <label className="form-label">{t('settings.company.plan') || '{t("settings.general.subscription_plan")}'}</label>
                <input
                    type="text"
                    name="plan_type"
                    id="plan_type"
                    className="form-input"
                    value={t(`plans.${formData.plan_type || 'basic'}`) || formData.plan_type || 'Basic'}
                    disabled
                    style={{ background: 'var(--bg-main)', cursor: 'not-allowed' }}
                />
            </div>
        </div>
    );
};

export default GeneralSettings;
