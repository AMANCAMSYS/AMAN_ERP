import React from 'react';
import { useTranslation } from 'react-i18next';
import { getCountry, getCurrency } from '../../../utils/auth';

const COUNTRIES = [
    { code: 'SA', name: 'المملكة العربية السعودية', flag: '🇸🇦' },
    { code: 'SY', name: 'سوريا', flag: '🇸🇾' },
    { code: 'AE', name: 'الإمارات', flag: '🇦🇪' },
    { code: 'EG', name: 'مصر', flag: '🇪🇬' },
    { code: 'KW', name: 'الكويت', flag: '🇰🇼' },
    { code: 'TR', name: 'تركيا', flag: '🇹🇷' },
];

const GeneralSettings = ({ formData, handleChange }) => {
    const { t } = useTranslation();
    const country = getCountry();
    const currency = getCurrency();
    const countryInfo = COUNTRIES.find(c => c.code === country);

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="form-group">
                <label className="form-label" htmlFor="company_name">{t('settings.company.name')}</label>
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
                <label className="form-label" htmlFor="company_name_en">{t('settings.company.name_en')}</label>
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
                <label className="form-label" htmlFor="email">{t('settings.company.email')}</label>
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
                <label className="form-label" htmlFor="phone">{t('settings.company.phone')}</label>
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
                <label className="form-label" htmlFor="address">{t('settings.company.address')}</label>
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
                <label className="form-label">{t('settings.company.country')}</label>
                <div className="form-input" style={{ background: 'var(--bg-main)', cursor: 'not-allowed', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '20px' }}>{countryInfo?.flag || '🌍'}</span>
                    <span>{countryInfo?.name || country || '-'}</span>
                </div>
                <small className="text-muted">{t('settings.company.country_note')}</small>
            </div>

            <div className="form-group">
                <label className="form-label">{t('settings.company.base_currency')}</label>
                <div className="form-input" style={{ background: 'var(--bg-main)', cursor: 'not-allowed' }}>
                    {currency || '-'}
                </div>
                <small className="text-muted">{t('settings.company.currency_note')}</small>
            </div>

            <div className="form-group">
                <label className="form-label">{t('settings.company.plan')}</label>
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
