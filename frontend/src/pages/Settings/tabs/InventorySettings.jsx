import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Box, MapPin, AlertTriangle } from 'lucide-react';
import api from '../../../utils/api';

const InventorySettings = ({ settings, handleSettingChange }) => {
    const { t } = useTranslation();
    const [warehouses, setWarehouses] = useState([]);

    useEffect(() => {
        const fetchWarehouses = async () => {
            try {
                const response = await api.get('/inventory/warehouses');
                setWarehouses(response.data || []);
            } catch (err) {
                console.error("Failed to fetch warehouses", err);
            }
        };
        fetchWarehouses();
    }, []);

    return (
        <div className="space-y-8">
            {/* Stock Policy */}
            <div className="bg-base-50 p-6 rounded-2xl border border-base-200">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <AlertTriangle size={20} className="text-warning" />
                    {t('settings.inventory.policy_title') || '{t("settings.inventory.policies")}'}
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="flex items-start gap-3">
                        <div className="pt-1">
                            <input
                                type="checkbox"
                                className="checkbox checkbox-primary"
                                id="allow_negative_stock"
                                checked={settings.allow_negative_stock === 'true'}
                                onChange={(e) => handleSettingChange('allow_negative_stock', e.target.checked.toString())}
                            />
                        </div>
                        <div>
                            <label className="cursor-pointer font-medium block" htmlFor="allow_negative_stock">
                                {t('settings.inventory.allow_negative') || '{t("settings.inventory.allow_negative")}'}
                            </label>
                            <p className="text-xs text-base-content/40 mt-1">
                                {t('settings.inventory.negative_hint') || '{t("settings.inventory.negative_note")}'}
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Defaults Section */}
            <div className="bg-base-50 p-6 rounded-2xl border border-base-200">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <MapPin size={20} className="text-primary" />
                    {t('settings.inventory.defaults_title') || '{t("settings.inventory.warehouses_links")}'}
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="form-group">
                        <label className="form-label" htmlFor="default_warehouse">
                            {t('settings.inventory.default_warehouse') || '{t("settings.inventory.default_warehouse")}'}
                        </label>
                        <select
                            id="default_warehouse"
                            className="form-input"
                            value={settings.default_warehouse || ''}
                            onChange={(e) => handleSettingChange('default_warehouse', e.target.value)}
                        >
                            <option value="">{t('common.select') || 'اختر...'}</option>
                            {warehouses.map(w => (
                                <option key={w.id} value={w.id.toString()}>{w.name}</option>
                            ))}
                        </select>
                        <p className="text-xs text-base-content/40 mt-1">
                            {t('settings.inventory.warehouse_hint') || '{t("settings.inventory.warehouse_note")}'}
                        </p>
                    </div>
                </div>
            </div>

            {/* Valuation Section */}
            <div className="bg-base-50 p-6 rounded-2xl border border-base-200">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <Box size={20} className="text-primary" />
                    {t('settings.inventory.valuation_title') || '{t("settings.inventory.valuation")}'}
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="form-group">
                        <label className="form-label">{t('settings.inventory.valuation_method') || '{t("settings.inventory.valuation_method")}'}</label>
                        <select
                            className="form-select"
                            value={settings.valuation_method || 'moving_average'}
                            onChange={(e) => handleSettingChange('valuation_method', e.target.value)}
                            disabled
                        >
                            <option value="moving_average">Moving Average ({t("settings.inventory.weighted_avg")})</option>
                            <option value="fifo">FIFO ({t("settings.inventory.fifo")})</option>
                        </select>
                        <p className="text-xs text-base-content/40 mt-1">
                            {t('settings.inventory.valuation_hint') || 'طريقة حساب تكلفة البضاعة المباعة (مثبتة حالياً على {t("settings.inventory.weighted_avg")}).'}
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default InventorySettings;
