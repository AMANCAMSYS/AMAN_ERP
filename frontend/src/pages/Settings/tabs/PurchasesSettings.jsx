import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Truck, Calendar, User } from 'lucide-react';
import api from '../../../utils/api';

const PurchasesSettings = ({ settings, handleSettingChange, currency }) => {
    const { t } = useTranslation();
    const [suppliers, setSuppliers] = useState([]);

    useEffect(() => {
        const fetchSuppliers = async () => {
            try {
                const response = await api.get('/parties/suppliers');
                setSuppliers(response.data.items || []);
            } catch (error) {
                console.error("Failed to fetch suppliers", error);
            }
        };
        fetchSuppliers();
    }, []);

    return (
        <div className="space-y-8">
            {/* Payment Terms */}
            <div className="bg-base-50 p-6 rounded-2xl border border-base-200">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <Calendar size={20} className="text-primary" />
                    {t('settings.purchases.terms_title')}
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="form-group">
                        <label className="form-label">{t('settings.purchases.default_payment_term')}</label>
                        <select
                            className="form-input"
                            value={settings.purchases_payment_term || '30'}
                            onChange={(e) => handleSettingChange('purchases_payment_term', e.target.value)}
                        >
                            <option value="0">{t('common.immediate')}</option>
                            <option value="15">15 {t('common.days')}</option>
                            <option value="30">30 {t('common.days')}</option>
                            <option value="45">45 {t('common.days')}</option>
                            <option value="60">60 {t('common.days')}</option>
                            <option value="90">90 {t('common.days')}</option>
                        </select>
                        <p className="text-xs text-base-content/40 mt-1">
                            {t('settings.purchases.term_hint')}
                        </p>
                    </div>
                </div>
            </div>

            {/* Defaults */}
            <div className="bg-base-50 p-6 rounded-2xl border border-base-200">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <Truck size={20} className="text-primary" />
                    {t('settings.purchases.defaults_title')}
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="form-group">
                        <label className="form-label">{t('settings.purchases.default_supplier')}</label>
                        <div className="relative">
                            <select
                                className="form-select"
                                value={settings.purchases_default_supplier || ''}
                                onChange={(e) => handleSettingChange('purchases_default_supplier', e.target.value)}
                            >
                                <option value="">{t('common.select')}</option>
                                {suppliers.map(supplier => (
                                    <option key={supplier.id} value={supplier.id}>
                                        {supplier.name}
                                    </option>
                                ))}
                            </select>
                            <User className="absolute right-3 top-3 text-base-content/30 pointer-events-none" size={16} />
                        </div>
                    </div>

                    <div className="flex items-center gap-3 pt-8">
                        <input
                            type="checkbox"
                            className="checkbox checkbox-primary"
                            id="purchases_auto_approve"
                            checked={settings.purchases_auto_approve === 'true'}
                            onChange={(e) => handleSettingChange('purchases_auto_approve', e.target.checked.toString())}
                        />
                        <label className="cursor-pointer font-medium" htmlFor="purchases_auto_approve">
                            {t('settings.purchases.auto_approve')}
                        </label>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default PurchasesSettings;
