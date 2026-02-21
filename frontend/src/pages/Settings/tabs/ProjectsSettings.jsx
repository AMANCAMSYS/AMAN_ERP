import React from 'react';
import { useTranslation } from 'react-i18next';
import { Briefcase, Clock, Hash } from 'lucide-react';

const ProjectsSettings = ({ settings, handleSettingChange }) => {
    const { t } = useTranslation();

    return (
        <div className="space-y-8">
            {/* Project Module Control */}
            <div className="bg-base-50 p-6 rounded-2xl border border-base-200">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <Briefcase size={20} className="text-primary" />
                    {t('settings.projects.main_title') || 'إعدادات إدارة المشاريع'}
                </h3>

                <div className="flex items-center gap-3 mb-6">
                    <input
                        type="checkbox"
                        className="checkbox checkbox-primary"
                        id="projects_enabled"
                        checked={settings.projects_enabled === 'true'}
                        onChange={(e) => handleSettingChange('projects_enabled', e.target.checked.toString())}
                    />
                    <div>
                        <label className="cursor-pointer font-medium block" htmlFor="projects_enabled">
                            {t('settings.projects.enable_module') || 'تفعيل وحدة إدارة المشاريع'}
                        </label>
                        <p className="text-xs text-base-content/40 mt-1">
                            {t('settings.projects.enable_hint') || 'عند التفعيل، ستظهر قائمة المشاريع في القائمة الجانبية.'}
                        </p>
                    </div>
                </div>

                <div className={`grid grid-cols-1 md:grid-cols-2 gap-6 transition-all ${settings.projects_enabled === 'true' ? 'opacity-100' : 'opacity-50 pointer-events-none'}`}>
                    <div className="form-group">
                        <label className="form-label mb-2 flex items-center gap-2">
                            <Hash size={16} />
                            {t('settings.projects.prefix') || 'بادئة ترميز المشاريع'}
                        </label>
                        <input
                            type="text"
                            className="form-input font-mono uppercase"
                            value={settings.project_prefix || 'PRJ-'}
                            onChange={(e) => handleSettingChange('project_prefix', e.target.value)}
                            placeholder="PRJ-"
                        />
                    </div>
                </div>
            </div>

            {/* Time Tracking */}
            <div className="bg-base-50 p-6 rounded-2xl border border-base-200">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                    <Clock size={20} className="text-primary" />
                    {t('settings.projects.time_title') || 'تتبع الوقت والمهام'}
                </h3>
                <div className="flex items-center gap-3">
                    <input
                        type="checkbox"
                        className="checkbox checkbox-primary"
                        id="project_timesheet_required"
                        checked={settings.project_timesheet_required === 'true'}
                        onChange={(e) => handleSettingChange('project_timesheet_required', e.target.checked.toString())}
                    />
                    <label className="cursor-pointer font-medium" htmlFor="project_timesheet_required">
                        {t('settings.projects.require_timesheets') || 'إلزام الموظفين بتسجيل الجداول الزمنية (Timesheets)'}
                    </label>
                </div>
            </div>
        </div>
    );
};

export default ProjectsSettings;
