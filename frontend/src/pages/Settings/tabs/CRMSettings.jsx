import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Heart, Gift, Users } from 'lucide-react';

const CRMSettings = ({ settings, handleSettingChange, currency }) => {
    const { t } = useTranslation();

    return (
        <div className="space-y-8">
            {/* Loyalty Program */}
            <div className="bg-base-50 p-6 rounded-2xl border border-base-200">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <Gift size={20} className="text-primary" />
                    {t('settings.crm.loyalty_title')}
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="flex items-start gap-3">
                        <div className="pt-1">
                            <input
                                type="checkbox"
                                className="checkbox checkbox-primary"
                                id="crm_loyalty_enabled"
                                checked={settings.crm_loyalty_enabled === 'true'}
                                onChange={(e) => handleSettingChange('crm_loyalty_enabled', e.target.checked.toString())}
                            />
                        </div>
                        <div>
                            <label className="cursor-pointer font-medium block" htmlFor="crm_loyalty_enabled">
                                {t('settings.crm.enable_loyalty')}
                            </label>
                            <p className="text-xs text-base-content/40 mt-1">
                                {t('settings.crm.loyalty_hint')}
                            </p>
                        </div>
                    </div>
                </div>

                <div className={`grid grid-cols-1 md:grid-cols-2 gap-6 mt-6 transition-all ${settings.crm_loyalty_enabled === 'true' ? 'opacity-100' : 'opacity-50 pointer-events-none'}`}>
                    <div className="form-group">
                        <label className="form-label">{t('settings.crm.earn_rate')}</label>
                        <div className="flex items-center gap-2">
                            <span className="text-sm">{t('settings.crm.per')}</span>
                            <input
                                type="number"
                                className="form-input w-24 text-center"
                                value={settings.crm_earn_amount || '10'}
                                onChange={(e) => handleSettingChange('crm_earn_amount', e.target.value)}
                            />
                            <span className="text-sm">{currency || ''} = 1 {t('settings.crm.point')}</span>
                        </div>
                    </div>

                    <div className="form-group">
                        <label className="form-label">{t('settings.crm.redeem_rate')}</label>
                        <div className="flex items-center gap-2">
                            <span className="text-sm">{t('settings.crm.per')}</span>
                            <input
                                type="number"
                                className="form-input w-24 text-center"
                                value={settings.crm_redeem_points || '100'}
                                onChange={(e) => handleSettingChange('crm_redeem_points', e.target.value)}
                            />
                            <span className="text-sm">{t('settings.crm.point')} = 1 {currency || ''}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default CRMSettings;
