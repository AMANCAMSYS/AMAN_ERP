import React from 'react';
import { useTranslation } from 'react-i18next';
import { Hash, FileText, AlignLeft } from 'lucide-react';

const InvoicingSettings = ({ settings, handleSettingChange }) => {
    const { t } = useTranslation();

    return (
        <div className="space-y-8">
            {/* Sequencing Section */}
            <div className="bg-base-50 p-6 rounded-2xl border border-base-200">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <Hash size={20} className="text-primary" />
                    {t('settings.invoicing.sequence_title')}
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="form-group">
                        <label className="form-label" htmlFor="invoice_prefix">
                            {t('settings.invoicing.invoice_prefix')}
                        </label>
                        <input
                            type="text"
                            id="invoice_prefix"
                            className="form-input font-mono"
                            value={settings.invoice_prefix || 'INV-'}
                            onChange={(e) => handleSettingChange('invoice_prefix', e.target.value)}
                            placeholder={t('settings.invoicing.invoice_prefix_placeholder')}
                        />
                        <p className="text-xs text-base-content/40 mt-1">
                            {t('settings.invoicing.prefix_hint')}
                        </p>
                    </div>

                    <div className="form-group">
                        <label className="form-label" htmlFor="quotation_prefix">
                            {t('settings.invoicing.quotation_prefix')}
                        </label>
                        <input
                            type="text"
                            id="quotation_prefix"
                            className="form-input font-mono"
                            value={settings.quotation_prefix || 'QTN-'}
                            onChange={(e) => handleSettingChange('quotation_prefix', e.target.value)}
                            placeholder={t('settings.invoicing.quotation_prefix_placeholder')}
                        />
                    </div>
                </div>
            </div>

            {/* Terms & Footer Section */}
            <div className="bg-base-50 p-6 rounded-2xl border border-base-200">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <AlignLeft size={20} className="text-primary" />
                    {t('settings.invoicing.content_title')}
                </h3>
                <div className="space-y-6">
                    <div className="form-group">
                        <label className="form-label" htmlFor="invoice_terms">
                            {t('settings.invoicing.default_terms')}
                        </label>
                        <textarea
                            id="invoice_terms"
                            className="form-input min-h-[100px]"
                            value={settings.invoice_terms || ''}
                            onChange={(e) => handleSettingChange('invoice_terms', e.target.value)}
                            placeholder={t('settings.invoicing.terms_placeholder')}
                        ></textarea>
                    </div>

                    <div className="form-group">
                        <label className="form-label" htmlFor="invoice_footer">
                            {t('settings.invoicing.footer_text')}
                        </label>
                        <input
                            type="text"
                            id="invoice_footer"
                            className="form-input"
                            value={settings.invoice_footer || ''}
                            onChange={(e) => handleSettingChange('invoice_footer', e.target.value)}
                            placeholder={t('settings.invoicing.footer_placeholder')}
                        />
                    </div>
                </div>
            </div>

            {/* Display Options */}
            <div className="bg-base-50 p-6 rounded-2xl border border-base-200">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <FileText size={20} className="text-primary" />
                    {t('settings.invoicing.display_title')}
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="flex items-center gap-3">
                        <input
                            type="checkbox"
                            className="checkbox checkbox-primary"
                            id="show_logo_on_invoice"
                            checked={settings.show_logo_on_invoice === 'true'}
                            onChange={(e) => handleSettingChange('show_logo_on_invoice', e.target.checked.toString())}
                        />
                        <label className="cursor-pointer font-medium" htmlFor="show_logo_on_invoice">
                            {t('settings.invoicing.show_logo')}
                        </label>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default InvoicingSettings;
