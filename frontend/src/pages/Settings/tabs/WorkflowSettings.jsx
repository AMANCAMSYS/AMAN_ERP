import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { GitPullRequest, CheckCircle, AlertTriangle } from 'lucide-react';

const WorkflowSettings = ({ settings, handleSettingChange, currency }) => {
    const { t } = useTranslation();

    return (
        <div className="space-y-8">
            {/* Approval Workflows */}
            <div className="bg-base-50 p-6 rounded-2xl border border-base-200">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <GitPullRequest size={20} className="text-primary" />
                    {t('settings.workflow.approvals_title') || '{t("settings.workflow.title")}'}
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="form-group">
                        <label className="form-label">{t('settings.workflow.po_limit') || '{t("settings.workflow.direct_purchase_limit")}'}</label>
                        <div className="flex items-center gap-2">
                            <input
                                type="number"
                                className="form-input"
                                value={settings.workflow_po_limit || '1000'}
                                onChange={(e) => handleSettingChange('workflow_po_limit', e.target.value)}
                            />
                            <span className="text-sm opacity-70">{currency || ''}</span>
                        </div>
                    </div>

                    <div className="form-group">
                        <label className="form-label">{t('settings.workflow.credit_limit_approval') || '{t("settings.workflow.credit_limit_exceed")}'}</label>
                        <select
                            className="form-input"
                            value={settings.workflow_credit_override || 'manager'}
                            onChange={(e) => handleSettingChange('workflow_credit_override', e.target.value)}
                        >
                            <option value="block">{t('settings.workflow.action_block') || '{t("settings.workflow.block_operation")}'}</option>
                            <option value="manager">{t('settings.workflow.action_manager') || '{t("settings.workflow.require_approval")}'}</option>
                            <option value="warn">{t('settings.workflow.action_warn') || '{t("settings.workflow.warning_only")}'}</option>
                        </select>
                    </div>
                </div>

                <div className="mt-6 space-y-3">
                    <div className="flex items-center gap-3">
                        <input
                            type="checkbox"
                            className="checkbox checkbox-primary"
                            id="workflow_sales_return"
                            checked={settings.workflow_sales_return === 'true'}
                            onChange={(e) => handleSettingChange('workflow_sales_return', e.target.checked.toString())}
                        />
                        <label className="cursor-pointer font-medium" htmlFor="workflow_sales_return">
                            {t('settings.workflow.return_approval') || '{t("settings.workflow.return_approval")}'}
                        </label>
                    </div>

                    <div className="flex items-center gap-3">
                        <input
                            type="checkbox"
                            className="checkbox checkbox-primary"
                            id="workflow_discount_limit"
                            checked={settings.workflow_discount_limit === 'true'}
                            onChange={(e) => handleSettingChange('workflow_discount_limit', e.target.checked.toString())}
                        />
                        <label className="cursor-pointer font-medium" htmlFor="workflow_discount_limit">
                            {t('settings.workflow.discount_approval') || '{t("settings.workflow.discount_approval")}'}
                        </label>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default WorkflowSettings;
