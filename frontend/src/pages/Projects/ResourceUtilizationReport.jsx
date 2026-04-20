import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { projectsAPI } from '../../utils/api';
import { formatNumber } from '../../utils/format';
import '../../components/ModuleStyles.css';
import BackButton from '../../components/common/BackButton';
import DateInput from '../../components/common/DateInput';

const ResourceUtilizationReport = () => {
    const { t } = useTranslation();
    const [loading, setLoading] = useState(false);
    const [report, setReport] = useState(null);
    const [filters, setFilters] = useState({
        start_date: new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split('T')[0],
        end_date: new Date().toISOString().split('T')[0],
    });

    const fetchReport = async () => {
        setLoading(true);
        try {
            const res = await projectsAPI.getResourceUtilization(filters);
            setReport(res.data);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { fetchReport(); }, []);

    const resources = report?.resources || [];
    const totalHours = resources.reduce((s, r) => s + (r.total_hours || 0), 0);
    const avgUtilization = resources.length > 0
        ? resources.reduce((s, r) => s + (r.utilization_pct || 0), 0) / resources.length
        : 0;

    const getUtilizationColor = (pct) => {
        if (pct >= 100) return '#ef4444';
        if (pct >= 80) return '#22c55e';
        if (pct >= 50) return '#f59e0b';
        return '#94a3b8';
    };

    const getUtilizationLabel = (pct) => {
        if (pct >= 100) return t('projects.load_overload', 'حمل زائد');
        if (pct >= 80) return t('projects.load_optimal', 'حمل مثالي');
        if (pct >= 50) return t('projects.load_moderate', 'حمل متوسط');
        return t('projects.load_light', 'حمل خفيف');
    };

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <div className="header-title">
                    <h1 className="workspace-title">👥 {t('projects.reports.resources_title', 'استغلال الموارد')}</h1>
                    <p className="workspace-subtitle">{t('projects.reports.resources_subtitle', 'تتبع توزيع الموظفين وأعباء العمل عبر المشاريع')}</p>
                </div>
            </div>

            {/* Filters */}
            <div className="card" style={{ marginBottom: 16 }}>
                <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'flex-end' }}>
                    <div className="form-group" style={{ flex: 1, minWidth: 150 }}>
                        <label className="form-label">{t('common.from_date', 'من تاريخ')}</label>
                        <DateInput className="form-input" value={filters.start_date}
                            onChange={e => setFilters(p => ({ ...p, start_date: e.target.value }))} />
                    </div>
                    <div className="form-group" style={{ flex: 1, minWidth: 150 }}>
                        <label className="form-label">{t('common.to_date', 'إلى تاريخ')}</label>
                        <DateInput className="form-input" value={filters.end_date}
                            onChange={e => setFilters(p => ({ ...p, end_date: e.target.value }))} />
                    </div>
                    <button className="btn btn-primary" onClick={fetchReport} disabled={loading}>
                        {loading ? '...' : t('common.search', 'بحث')}
                    </button>
                </div>
            </div>

            {loading ? (
                <div className="loading-container"><div className="spinner" /></div>
            ) : (
                <>
                    {/* KPI Metrics */}
                    <div className="metrics-grid" style={{ marginBottom: 16 }}>
                        <div className="metric-card">
                            <div className="metric-label">{t('projects.reports.total_employees', 'عدد الموظفين')}</div>
                            <div className="metric-value text-primary">{resources.length}</div>
                        </div>
                        <div className="metric-card">
                            <div className="metric-label">{t('projects.reports.total_hours', 'إجمالي الساعات')}</div>
                            <div className="metric-value text-success">{formatNumber(totalHours, 1)}</div>
                        </div>
                        <div className="metric-card">
                            <div className="metric-label">{t('projects.reports.avg_utilization', 'متوسط الاستغلال')}</div>
                            <div className="metric-value" style={{ color: getUtilizationColor(avgUtilization) }}>
                                {formatNumber(avgUtilization, 1)}%
                            </div>
                        </div>
                        <div className="metric-card">
                            <div className="metric-label">{t('projects.reports.overloaded', 'حمل زائد')}</div>
                            <div className="metric-value text-danger">
                                {resources.filter(r => r.utilization_pct >= 100).length}
                            </div>
                        </div>
                    </div>

                    {/* Resource Cards */}
                    {resources.length === 0 ? (
                        <div className="card">
                            <div className="empty-state">
                                <p>{t('projects.reports.no_resources', 'لا توجد بيانات موارد في الفترة المحددة')}</p>
                            </div>
                        </div>
                    ) : (
                        <>
                            {/* Visual Summary */}
                            <div className="card" style={{ marginBottom: 16 }}>
                                <h3 className="section-title">{t('projects.reports.utilization_overview', 'نظرة عامة على الاستغلال')}</h3>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginTop: 12 }}>
                                    {resources.map(r => (
                                        <div key={r.user_id}>
                                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4, alignItems: 'center' }}>
                                                <span style={{ fontWeight: 600 }}>{r.name}</span>
                                                <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                                                    <span style={{ fontSize: 12, color: '#6b7280' }}>{r.projects_count} {t('projects.title', 'مشاريع')}</span>
                                                    <span style={{ fontWeight: 700, color: getUtilizationColor(r.utilization_pct), minWidth: 45, textAlign: 'left' }}>
                                                        {formatNumber(r.utilization_pct, 1)}%
                                                    </span>
                                                </div>
                                            </div>
                                            <div style={{ background: '#e5e7eb', borderRadius: 999, height: 10, overflow: 'hidden' }}>
                                                <div style={{
                                                    width: `${Math.min(r.utilization_pct, 100)}%`,
                                                    background: getUtilizationColor(r.utilization_pct),
                                                    height: '100%', borderRadius: 999, transition: 'width 0.5s'
                                                }} />
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Details Table */}
                            <div className="card">
                                <h3 className="section-title">{t('projects.reports.details', 'التفاصيل')}</h3>
                                <div className="table-responsive" style={{ marginTop: 8 }}>
                                    <table className="data-table">
                                        <thead>
                                            <tr>
                                                <th>{t('projects.reports.employee', 'الموظف')}</th>
                                                <th>{t('projects.reports.projects_count', 'عدد المشاريع')}</th>
                                                <th>{t('projects.reports.total_hours', 'إجمالي الساعات')}</th>
                                                <th>{t('projects.reports.avg_daily', 'متوسط يومي')}</th>
                                                <th>{t('projects.reports.working_days', 'أيام العمل')}</th>
                                                <th>{t('projects.reports.utilization', 'الاستغلال')}</th>
                                                <th>{t('projects.reports.load_status', 'الحالة')}</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {resources.map(r => (
                                                <tr key={r.user_id}>
                                                    <td style={{ fontWeight: 600 }}>{r.name}</td>
                                                    <td>{r.projects_count}</td>
                                                    <td>{formatNumber(r.total_hours, 1)}</td>
                                                    <td>{formatNumber(r.avg_daily_hours, 1)}</td>
                                                    <td>{r.working_days}</td>
                                                    <td>
                                                        <span className={`status-badge ${r.utilization_pct >= 80 ? (r.utilization_pct >= 100 ? 'status-rejected' : 'status-active') : 'status-pending'}`}>
                                                            {formatNumber(r.utilization_pct, 1)}%
                                                        </span>
                                                    </td>
                                                    <td>
                                                        <span style={{ fontSize: 12, fontWeight: 600, color: getUtilizationColor(r.utilization_pct) }}>
                                                            {getUtilizationLabel(r.utilization_pct)}
                                                        </span>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </>
                    )}
                </>
            )}
        </div>
    );
};

export default ResourceUtilizationReport;
