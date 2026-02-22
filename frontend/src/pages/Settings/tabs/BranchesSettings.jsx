import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { GitBranch, Plus, Trash2 } from 'lucide-react';
import api from '../../../utils/api';

const BranchesSettings = ({ settings, handleSettingChange }) => {
    const { t } = useTranslation();
    const [branches, setBranches] = useState([]);

    useEffect(() => {
        const fetchBranches = async () => {
            try {
                const response = await api.get('/branches');
                // Response can be array or object depending on implementation, ensuring array
                setBranches(Array.isArray(response.data) ? response.data : []);
            } catch (error) {
                console.error("Failed to fetch branches", error);
            }
        };
        fetchBranches();
    }, []);

    return (
        <div className="space-y-8">
            {/* Multi-Branch */}
            <div className="bg-base-50 p-6 rounded-2xl border border-base-200">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <GitBranch size={20} className="text-primary" />
                    {t('settings.branches.main_title')}
                </h3>

                <div className="flex items-center gap-3 mb-6">
                    <input
                        type="checkbox"
                        className="checkbox checkbox-primary"
                        id="multi_branch_enabled"
                        checked={settings.multi_branch_enabled === 'true'}
                        onChange={(e) => handleSettingChange('multi_branch_enabled', e.target.checked.toString())}
                    />
                    <div>
                        <label className="cursor-pointer font-medium block" htmlFor="multi_branch_enabled">
                            {t('settings.branches.enable_multi')}
                        </label>
                        <p className="text-xs text-base-content/40 mt-1">
                            {t('settings.branches.enable_hint')}
                        </p>
                    </div>
                </div>

                <div className={`space-y-4 transition-all ${settings.multi_branch_enabled === 'true' ? 'opacity-100' : 'opacity-50 pointer-events-none'}`}>
                    <div className="form-group">
                        <label className="form-label">{t('settings.branches.main_branch')}</label>
                        <select
                            className="form-select"
                            value={settings.main_branch_id || ''}
                            onChange={(e) => handleSettingChange('main_branch_id', e.target.value)}
                        >
                            <option value="">{t('common.select')}</option>
                            {branches.map(branch => (
                                <option key={branch.id} value={branch.id}>
                                    {branch.branch_name} {branch.branch_code ? `(${branch.branch_code})` : ''}
                                </option>
                            ))}
                        </select>
                        <p className="text-xs text-base-content/40 mt-1">
                            {t('settings.branches.main_branch_hint')}
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default BranchesSettings;
