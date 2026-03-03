import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, useLocation } from 'react-router-dom';
import { BarChart2, Calendar, FileText } from 'lucide-react';
import PayrollReport from './PayrollReport';
import LeaveReport from './LeaveReport';
import '../../../components/ModuleStyles.css';
import BackButton from '../../../components/common/BackButton';
import { ModuleKPISection } from '../../../components/kpi';

const HRReports = () => {
    const { t, i18n } = useTranslation();
    const navigate = useNavigate();
    const isRTL = i18n.language === 'ar';
    const location = useLocation();
    const [activeTab, setActiveTab] = useState(location.state?.tab || 'payroll');

    useEffect(() => {
        if (location.state?.tab) {
            setActiveTab(location.state.tab);
        }
    }, [location.state]);

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                        <BackButton />
                    <div>
                        <h1 className="workspace-title">{t('hr.reports.title', 'HR Reports')}</h1>
                        <p className="workspace-subtitle">{t('hr.reports.subtitle', 'Analytics and Insights')}</p>
                    </div>
                </div>
            </div>

            <ModuleKPISection roleKey="hr" color="#7c3aed" defaultOpen={false} />

            {/* Reports Navigation (Tabs) */}
            <div className="reports-nav mb-4">
                <div className="d-flex gap-2 border-bottom pb-0" style={{ overflowX: 'auto' }}>
                    <button
                        className={`btn btn-link nav-link ${activeTab === 'payroll' ? 'active border-primary text-primary' : 'text-muted'}`}
                        style={{ borderBottom: activeTab === 'payroll' ? '2px solid var(--primary)' : 'none', borderRadius: 0, paddingBottom: '12px' }}
                        onClick={() => setActiveTab('payroll')}
                    >
                        <BarChart2 size={18} className="me-2" />
                        {t('hr.reports.payroll', 'Payroll Analysis')}
                    </button>
                    <button
                        className={`btn btn-link nav-link ${activeTab === 'leaves' ? 'active border-primary text-primary' : 'text-muted'}`}
                        style={{ borderBottom: activeTab === 'leaves' ? '2px solid var(--primary)' : 'none', borderRadius: 0, paddingBottom: '12px' }}
                        onClick={() => setActiveTab('leaves')}
                    >
                        <Calendar size={18} className="me-2" />
                        {t('hr.reports.leaves', 'Leave Usage')}
                    </button>
                </div>
            </div>

            {/* Report Content */}
            <div className="report-content">
                {activeTab === 'payroll' && <PayrollReport />}
                {activeTab === 'leaves' && <LeaveReport />}
            </div>
        </div>
    );
};

export default HRReports;
