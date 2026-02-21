import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { hasPermission } from '../../utils/auth';
import { hrAPI, attendanceAPI } from '../../utils/api';
import {
    Users,
    Briefcase,
    DollarSign,
    FileText,
    Settings,
    Activity,
    Plus,
    UserPlus,
    Calendar,
    Clock
} from 'lucide-react';
import '../../index.css';
import '../../components/ModuleStyles.css';

const HRHome = () => {
    const { t, i18n } = useTranslation();
    const navigate = useNavigate();
    const [stats, setStats] = useState({ employees: 0, present: 0, payroll: 0, leaves: 0 });

    useEffect(() => {
        const fetchStats = async () => {
            try {
                const [empRes, attRes] = await Promise.all([
                    hrAPI.listEmployees({ limit: 1 }),
                    attendanceAPI.getHistory({ limit: 1 })
                ]);
                setStats(prev => ({
                    ...prev,
                    employees: empRes.data?.total || empRes.data?.length || 0,
                    present: attRes.data?.today_count || attRes.data?.length || 0
                }));
            } catch (err) {
                console.error('Failed to fetch HR stats', err);
            }
        };
        if (hasPermission('hr.view')) fetchStats();
    }, []);

    // Dashboard metrics
    const metrics = [
        { title: t('hr.home.total_employees'), value: String(stats.employees), icon: Users, color: "#2563eb", bg: "#dbeafe" },
        { title: t('hr.home.present_today'), value: String(stats.present), icon: Activity, color: "#16a34a", bg: "#dcfce7" },
        { title: t('hr.home.salaries_due'), value: String(stats.payroll), icon: DollarSign, color: "#d97706", bg: "#fef3c7" },
        { title: t('hr.home.leaves'), value: String(stats.leaves), icon: FileText, color: "#7c3aed", bg: "#ede9fe" },
    ];

    return (
        <div className="workspace fade-in">
            {/* Header */}
            <div className="workspace-header">
                <div className="header-title">
                    <h1 className="workspace-title">{t('hr.home.title')}</h1>
                    <p className="workspace-subtitle">{t('hr.home.subtitle')}</p>
                </div>
            </div>

            {/* Metrics Grid */}
            <div className="metrics-grid">
                {metrics.map((metric, index) => (
                    <div key={index} className="metric-card">
                        <div className="metric-label">{metric.title}</div>
                        <div className="metric-value" style={{ color: metric.color }}>
                            {hasPermission('hr.reports') ? metric.value : '***'}
                        </div>
                    </div>
                ))}
            </div>

            {/* Modules Grid - Consistent with Sales/Stock */}
            <div className="modules-grid">

                {/* Employee Management Section */}
                <div className="card section-card">
                    <h3 className="section-title">{t('hr.home.employee_mgmt')}</h3>
                    <div className="links-list">
                        <div className="link-item" onClick={() => navigate('/hr/employees')}>
                            <span className="link-icon">👥</span>
                            {t('hr.home.employee_list')}
                            <span className="link-arrow">{i18n.language === 'ar' ? '←' : '→'}</span>
                        </div>
                        <div className="link-item" onClick={() => navigate('/hr/employees', { state: { openModal: true } })}>
                            <span className="link-icon">➕</span>
                            {t('hr.home.new_employee')}
                            <span className="link-arrow">{i18n.language === 'ar' ? '←' : '→'}</span>
                        </div>
                        <div className="link-item" onClick={() => navigate('/hr/positions')}>
                            <span className="link-icon">👔</span>
                            {t('hr.home.positions')}
                            <span className="link-arrow">{i18n.language === 'ar' ? '←' : '→'}</span>
                        </div>
                        <div className="link-item" onClick={() => navigate('/hr/departments')}>
                            <span className="link-icon">🏢</span>
                            {t('hr.home.departments')}
                            <span className="link-arrow">{i18n.language === 'ar' ? '←' : '→'}</span>
                        </div>
                    </div>
                </div>

                {/* Payroll & Attendance Section */}
                <div className="card section-card">
                    <h3 className="section-title">{t('hr.home.payroll_attendance')}</h3>
                    <div className="links-list">
                        <div className="link-item" onClick={() => navigate('/hr/payroll')}>
                            <span className="link-icon">💰</span>
                            {t('hr.home.payroll_sheet')}
                            <span className="link-arrow">{i18n.language === 'ar' ? '←' : '→'}</span>
                        </div>
                        <div className="link-item" onClick={() => navigate('/hr/loans')}>
                            <span className="link-icon">💸</span>
                            {t('hr.home.loans')}
                            <span className="link-arrow">{i18n.language === 'ar' ? '←' : '→'}</span>
                        </div>
                        <div className="link-item" onClick={() => navigate('/hr/attendance')}>
                            <span className="link-icon">⏰</span>
                            {t('hr.home.attendance_log')}
                            <span className="link-arrow">{i18n.language === 'ar' ? '←' : '→'}</span>
                        </div>
                        <div className="link-item" onClick={() => navigate('/hr/leaves')}>
                            <span className="link-icon">🏖️</span>
                            {t('hr.leaves.title')}
                            <span className="link-arrow">{i18n.language === 'ar' ? '←' : '→'}</span>
                        </div>
                    </div>
                </div>

                {/* Reports Section */}
                {/* Reports Section */}
                {hasPermission('hr.reports') && (
                    <div className="card section-card">
                        <h3 className="section-title">{t('hr.home.reports')}</h3>
                        <div className="links-list">
                            <div className="link-item" onClick={() => navigate('/hr/reports')}>
                                <span className="link-icon">📊</span>
                                {t('reports_center.hr_reports.payroll', 'Payroll Analytics')}
                                <span className="link-arrow">{i18n.language === 'ar' ? '←' : '→'}</span>
                            </div>
                            <div className="link-item" onClick={() => navigate('/hr/reports', { state: { tab: 'leaves' } })}>
                                <span className="link-icon">📉</span>
                                {t('reports_center.hr_reports.leaves', 'Leave Usage')}
                                <span className="link-arrow">{i18n.language === 'ar' ? '←' : '→'}</span>
                            </div>
                        </div>
                    </div>
                )}

                {/* Advanced Payroll Section */}
                <div className="card section-card">
                    <h3 className="section-title">{i18n.language === 'ar' ? 'الرواتب المتقدمة' : 'Advanced Payroll'}</h3>
                    <div className="links-list">
                        <div className="link-item" onClick={() => navigate('/hr/salary-structures')}>
                            <span className="link-icon">🏗️</span>
                            {i18n.language === 'ar' ? 'هياكل الرواتب والمكونات' : 'Salary Structures'}
                            <span className="link-arrow">{i18n.language === 'ar' ? '←' : '→'}</span>
                        </div>
                        <div className="link-item" onClick={() => navigate('/hr/overtime')}>
                            <span className="link-icon">⏱️</span>
                            {i18n.language === 'ar' ? 'العمل الإضافي' : 'Overtime Requests'}
                            <span className="link-arrow">{i18n.language === 'ar' ? '←' : '→'}</span>
                        </div>
                        <div className="link-item" onClick={() => navigate('/hr/gosi')}>
                            <span className="link-icon">🛡️</span>
                            {i18n.language === 'ar' ? 'التأمينات الاجتماعية' : 'GOSI / Social Insurance'}
                            <span className="link-arrow">{i18n.language === 'ar' ? '←' : '→'}</span>
                        </div>
                    </div>
                </div>

                {/* HR Management Section */}
                <div className="card section-card">
                    <h3 className="section-title">{i18n.language === 'ar' ? 'إدارة الموارد البشرية' : 'HR Management'}</h3>
                    <div className="links-list">
                        <div className="link-item" onClick={() => navigate('/hr/documents')}>
                            <span className="link-icon">📄</span>
                            {i18n.language === 'ar' ? 'مستندات الموظفين' : 'Employee Documents'}
                            <span className="link-arrow">{i18n.language === 'ar' ? '←' : '→'}</span>
                        </div>
                        <div className="link-item" onClick={() => navigate('/hr/performance')}>
                            <span className="link-icon">⭐</span>
                            {i18n.language === 'ar' ? 'تقييم الأداء' : 'Performance Reviews'}
                            <span className="link-arrow">{i18n.language === 'ar' ? '←' : '→'}</span>
                        </div>
                        <div className="link-item" onClick={() => navigate('/hr/training')}>
                            <span className="link-icon">🎓</span>
                            {i18n.language === 'ar' ? 'برامج التدريب' : 'Training Programs'}
                            <span className="link-arrow">{i18n.language === 'ar' ? '←' : '→'}</span>
                        </div>
                        <div className="link-item" onClick={() => navigate('/hr/violations')}>
                            <span className="link-icon">⚠️</span>
                            {i18n.language === 'ar' ? 'المخالفات والجزاءات' : 'Violations & Penalties'}
                            <span className="link-arrow">{i18n.language === 'ar' ? '←' : '→'}</span>
                        </div>
                        <div className="link-item" onClick={() => navigate('/hr/custody')}>
                            <span className="link-icon">📦</span>
                            {i18n.language === 'ar' ? 'إدارة العهد' : 'Custody Management'}
                            <span className="link-arrow">{i18n.language === 'ar' ? '←' : '→'}</span>
                        </div>
                        <div className="link-item" onClick={() => navigate('/hr/payslips')}>
                            <span className="link-icon">🧾</span>
                            {i18n.language === 'ar' ? 'كشوف الرواتب' : 'Payslips'}
                            <span className="link-arrow">{i18n.language === 'ar' ? '←' : '→'}</span>
                        </div>
                        <div className="link-item" onClick={() => navigate('/hr/leave-carryover')}>
                            <span className="link-icon">🔄</span>
                            {i18n.language === 'ar' ? 'ترحيل الإجازات' : 'Leave Carryover'}
                            <span className="link-arrow">{i18n.language === 'ar' ? '←' : '→'}</span>
                        </div>
                        <div className="link-item" onClick={() => navigate('/hr/recruitment')}>
                            <span className="link-icon">💼</span>
                            {i18n.language === 'ar' ? 'التوظيف' : 'Recruitment'}
                            <span className="link-arrow">{i18n.language === 'ar' ? '←' : '→'}</span>
                        </div>
                    </div>
                </div>

            </div>
        </div>
    );
};

export default HRHome;
