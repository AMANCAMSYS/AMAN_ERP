import React from 'react';
import { useTranslation } from 'react-i18next';
import { DollarSign, CreditCard } from 'lucide-react';

const ExpensesSettings = ({ settings, handleSettingChange, currency }) => {
    const { t } = useTranslation();

    return (
        <div className="space-y-8">
            {/* General Expense Settings */}
            <div className="bg-base-50 p-6 rounded-2xl border border-base-200">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <DollarSign size={20} className="text-primary" />
                    {t('settings.expenses.general_title')}
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="form-group">
                        <label className="form-label">{t('settings.expenses.approval_limit')}</label>
                        <div className="flex items-center gap-2">
                            <input
                                type="number"
                                className="form-input"
                                value={settings.expense_approval_limit || '500'}
                                onChange={(e) => handleSettingChange('expense_approval_limit', e.target.value)}
                            />
                            <span className="text-sm opacity-70">{currency || ''}</span>
                        </div>
                        <p className="text-xs text-base-content/40 mt-1">
                            {t('settings.expenses.limit_hint')}
                        </p>
                    </div>

                    <div className="form-group">
                        <label className="form-label">{t('settings.expenses.default_category')}</label>
                        <select
                            className="form-input"
                            value={settings.default_expense_category || ''}
                            onChange={(e) => handleSettingChange('default_expense_category', e.target.value)}
                        >
                            <option value="">{t('common.select')}</option>
                            <option value="general">{t('settings.expenses.cat_general')}</option>
                            <option value="travel">{t('settings.expenses.cat_travel')}</option>
                            <option value="office">{t('settings.expenses.cat_office')}</option>
                        </select>
                    </div>
                </div>

                <div className="mt-4 flex items-center gap-3">
                    <input
                        type="checkbox"
                        className="checkbox checkbox-primary"
                        id="allow_expense_claims"
                        checked={settings.allow_expense_claims === 'true'}
                        onChange={(e) => handleSettingChange('allow_expense_claims', e.target.checked.toString())}
                    />
                    <label className="cursor-pointer font-medium" htmlFor="allow_expense_claims">
                        {t('settings.expenses.allow_claims')}
                    </label>
                </div>
            </div>

            {/* Payment Methods */}
            <div className="bg-base-50 p-6 rounded-2xl border border-base-200">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <CreditCard size={20} className="text-primary" />
                    {t('settings.expenses.method_title')}
                </h3>
                <div className="form-group">
                    <label className="form-label">{t('settings.expenses.default_method')}</label>
                    <select
                        className="form-input"
                        value={settings.expense_payment_method || 'cash'}
                        onChange={(e) => handleSettingChange('expense_payment_method', e.target.value)}
                    >
                        <option value="cash">{t('settings.expenses.method_cash')}</option>
                        <option value="bank">{t('settings.expenses.method_bank')}</option>
                        <option value="card">{t('settings.expenses.method_card')}</option>
                    </select>
                </div>
            </div>
        </div>
    );
};

export default ExpensesSettings;
