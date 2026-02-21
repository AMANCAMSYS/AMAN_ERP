import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Users, CreditCard, Clock, Receipt } from 'lucide-react';
import api from '../../../utils/api';

const SalesSettings = ({ settings, handleSettingChange, currency }) => {
    const { t } = useTranslation();
    const [customers, setCustomers] = useState([]);

    useEffect(() => {
        const fetchCustomers = async () => {
            try {
                // Fetch only first 50 or search for "Walker"
                const response = await api.get('/parties/customers?limit=50');
                setCustomers(response.data.items || []);
            } catch (err) {
                console.error("Failed to fetch customers", err);
            }
        };
        fetchCustomers();
    }, []);

    return (
        <div className="space-y-8">
            {/* Customer Defaults */}
            <div className="bg-base-50 p-6 rounded-2xl border border-base-200">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <Users size={20} className="text-primary" />
                    {t('settings.sales.customers_title') || '{t("settings.sales.default_customers")}'}
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="form-group">
                        <label className="form-label">{t('settings.sales.default_customer') || '{t("settings.sales.default_cash_customer")}'}</label>
                        <select
                            className="form-input"
                            value={settings.sales_default_customer || ''}
                            onChange={(e) => handleSettingChange('sales_default_customer', e.target.value)}
                        >
                            <option value="">{t('common.select') || 'اختر...'}</option>
                            {customers.map(c => (
                                <option key={c.id} value={c.id.toString()}>{c.name}</option>
                            ))}
                        </select>
                        <p className="text-xs text-base-content/40 mt-1">
                            {t('settings.sales.customer_hint') || '{t("settings.sales.cash_customer_note")}'}
                        </p>
                    </div>

                    <div className="form-group">
                        <label className="form-label">{t('settings.sales.default_credit_limit') || '{t("settings.sales.default_credit_limit")}'}</label>
                        <div className="relative">
                            <input
                                type="number"
                                className="form-input pl-16"
                                value={settings.sales_default_credit_limit || '0'}
                                onChange={(e) => handleSettingChange('sales_default_credit_limit', e.target.value)}
                            />
                            <div className="absolute left-0 top-0 bottom-0 px-4 bg-base-200 flex items-center border-r border-base-300 rounded-l-lg text-sm text-base-content/60">
                                {currency || ''}
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Invoicing Rules */}
            <div className="bg-base-50 p-6 rounded-2xl border border-base-200">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <Receipt size={20} className="text-primary" />
                    {t('settings.sales.invoicing_rules') || '{t("settings.sales.billing_rules")}'}
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="form-group">
                        <label className="form-label">{t('settings.sales.quotation_expiry') || '{t("settings.sales.quote_validity")}'}</label>
                        <div className="relative">
                            <input
                                type="number"
                                className="form-input pl-16"
                                value={settings.sales_quotation_expiry || '15'}
                                onChange={(e) => handleSettingChange('sales_quotation_expiry', e.target.value)}
                            />
                            <div className="absolute left-0 top-0 bottom-0 px-4 bg-base-200 flex items-center border-r border-base-300 rounded-l-lg text-sm text-base-content/60">
                                {t('common.days') || 'أيام'}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default SalesSettings;
