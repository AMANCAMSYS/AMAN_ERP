import React from 'react';
import { useTranslation } from 'react-i18next';
import { Zap, Database } from 'lucide-react';
import { useToast } from '../../../context/ToastContext';

const PerformanceSettings = ({ settings, handleSettingChange }) => {
    const { t } = useTranslation();
    const { showToast } = useToast();

    const clearCache = () => {
        // Simulate clearing cache
        localStorage.removeItem('aman_cache');
        showToast(t('settings.performance.cache_cleared'), 'success');
    };

    return (
        <div className="space-y-8">
            {/* Caching */}
            <div className="bg-base-50 p-6 rounded-2xl border border-base-200">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <Zap size={20} className="text-primary" />
                    {t('settings.performance.cache_title')}
                </h3>

                <div className="flex items-center gap-3 mb-6">
                    <input
                        type="checkbox"
                        className="checkbox checkbox-primary"
                        id="perf_enable_caching"
                        checked={settings.perf_enable_caching === 'true'}
                        onChange={(e) => handleSettingChange('perf_enable_caching', e.target.checked.toString())}
                    />
                    <div>
                        <label className="cursor-pointer font-medium block" htmlFor="perf_enable_caching">
                            {t('settings.performance.enable_cache')}
                        </label>
                        <p className="text-xs text-base-content/40 mt-1">
                            {t('settings.performance.cache_hint')}
                        </p>
                    </div>
                </div>

                <button className="btn btn-outline btn-warning gap-2" onClick={clearCache}>
                    <Database size={18} />
                    {t('settings.performance.clear_cache_btn')}
                </button>
            </div>
        </div>
    );
};

export default PerformanceSettings;
