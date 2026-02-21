import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Clock, Calendar, Users } from 'lucide-react';

const HRSettings = ({ settings, handleSettingChange }) => {
    const { t } = useTranslation();

    return (
        <div className="space-y-8">
            {/* Work Hours */}
            <div className="bg-base-50 p-6 rounded-2xl border border-base-200">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <Clock size={20} className="text-primary" />
                    {t('settings.hr.hours_title')}
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="form-group">
                        <label className="form-label">{t('settings.hr.work_start')}</label>
                        <input
                            type="time"
                            className="form-input"
                            value={settings.hr_work_start || '08:00'}
                            onChange={(e) => handleSettingChange('hr_work_start', e.target.value)}
                        />
                    </div>
                    <div className="form-group">
                        <label className="form-label">{t('settings.hr.work_end')}</label>
                        <input
                            type="time"
                            className="form-input"
                            value={settings.hr_work_end || '17:00'}
                            onChange={(e) => handleSettingChange('hr_work_end', e.target.value)}
                        />
                    </div>
                </div>
            </div>

            {/* Work Days */}
            <div className="bg-base-50 p-6 rounded-2xl border border-base-200">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <Calendar size={20} className="text-primary" />
                    {t('settings.hr.days_title')}
                </h3>
                <div className="form-group">
                    <label className="form-label mb-3">{t('settings.hr.weekends')}</label>
                    <div className="flex flex-wrap gap-4">
                        {['friday', 'saturday', 'sunday', 'monday', 'tuesday', 'wednesday', 'thursday'].map((day) => {
                            const isWeekend = (settings.hr_weekends || '').includes(day);
                            return (
                                <button
                                    key={day}
                                    type="button"
                                    onClick={() => {
                                        let current = (settings.hr_weekends || '').split(',').filter(d => d);
                                        if (current.includes(day)) {
                                            current = current.filter(d => d !== day);
                                        } else {
                                            current.push(day);
                                        }
                                        handleSettingChange('hr_weekends', current.join(','));
                                    }}
                                    className={`btn btn-sm ${isWeekend ? 'btn-primary' : 'btn-outline border-base-300'}`}
                                >
                                    {t(`common.days_full.${day}`) || day}
                                </button>
                            );
                        })}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default HRSettings;
