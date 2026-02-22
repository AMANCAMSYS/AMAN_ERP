import React from 'react';
import { useTranslation } from 'react-i18next';
import { Printer, Monitor, Scissors, Keyboard, Disc } from 'lucide-react';

const POSSettings = ({ settings, handleSettingChange }) => {
    const { t } = useTranslation();

    return (
        <div className="space-y-8">
            {/* Printing Configuration */}
            <div className="bg-base-50 p-6 rounded-2xl border border-base-200">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <Printer size={20} className="text-primary" />
                    {t('settings.pos.printing_title')}
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="form-group">
                        <label className="form-label">{t('settings.pos.default_printer')}</label>
                        <select
                            className="form-input"
                            value={settings.pos_default_printer || 'system_default'}
                            onChange={(e) => handleSettingChange('pos_default_printer', e.target.value)}
                        >
                            <option value="system_default">{t('settings.pos.system_default')}</option>
                            <option value="thermal_80">{t('settings.pos.thermal_80')}</option>
                            <option value="thermal_58">{t('settings.pos.thermal_58')}</option>
                            <option value="a4">{t('settings.pos.printer_a4')}</option>
                        </select>
                    </div>

                    <div className="space-y-4 pt-6">
                        <div className="flex items-center gap-3">
                            <input
                                type="checkbox"
                                className="checkbox checkbox-primary"
                                id="pos_silent_print"
                                checked={settings.pos_silent_print === 'true'}
                                onChange={(e) => handleSettingChange('pos_silent_print', e.target.checked.toString())}
                            />
                            <label className="cursor-pointer font-medium" htmlFor="pos_silent_print">
                                {t('settings.pos.silent_print')}
                            </label>
                        </div>

                        <div className="flex items-center gap-3">
                            <input
                                type="checkbox"
                                className="checkbox checkbox-primary"
                                id="pos_auto_cut"
                                checked={settings.pos_auto_cut === 'true'}
                                onChange={(e) => handleSettingChange('pos_auto_cut', e.target.checked.toString())}
                            />
                            <div className="flex items-center gap-2">
                                <Scissors size={16} className="text-base-content/50" />
                                <label className="cursor-pointer font-medium" htmlFor="pos_auto_cut">
                                    {t('settings.pos.auto_cut')}
                                </label>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Behavior & UI */}
            <div className="bg-base-50 p-6 rounded-2xl border border-base-200">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <Monitor size={20} className="text-primary" />
                    {t('settings.pos.behavior_title')}
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-4">
                        <div className="flex items-center gap-3">
                            <input
                                type="checkbox"
                                className="checkbox checkbox-primary"
                                id="pos_open_drawer"
                                checked={settings.pos_open_drawer === 'true'}
                                onChange={(e) => handleSettingChange('pos_open_drawer', e.target.checked.toString())}
                            />
                            <div className="flex items-center gap-2">
                                <Disc size={16} className="text-base-content/50" />
                                <label className="cursor-pointer font-medium" htmlFor="pos_open_drawer">
                                    {t('settings.pos.open_drawer')}
                                </label>
                            </div>
                        </div>

                        <div className="flex items-center gap-3">
                            <input
                                type="checkbox"
                                className="checkbox checkbox-primary"
                                id="pos_onscreen_keyboard"
                                checked={settings.pos_onscreen_keyboard === 'true'}
                                onChange={(e) => handleSettingChange('pos_onscreen_keyboard', e.target.checked.toString())}
                            />
                            <div className="flex items-center gap-2">
                                <Keyboard size={16} className="text-base-content/50" />
                                <label className="cursor-pointer font-medium" htmlFor="pos_onscreen_keyboard">
                                    {t('settings.pos.onscreen_keyboard')}
                                </label>
                            </div>
                        </div>
                    </div>

                    <div className="form-group">
                        <label className="form-label">{t('settings.pos.default_payment')}</label>
                        <select
                            className="form-select"
                            value={settings.pos_default_payment || 'cash'}
                            onChange={(e) => handleSettingChange('pos_default_payment', e.target.value)}
                        >
                            <option value="cash">{t('common.cash')}</option>
                            <option value="card">{t('common.card')}</option>
                        </select>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default POSSettings;
