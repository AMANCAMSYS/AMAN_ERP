import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Plus, Search, FolderKanban, TrendingUp, Clock, CheckCircle2, PauseCircle, XCircle, BarChart3, Users, DollarSign, Calendar } from 'lucide-react';
import { projectsAPI } from '../../utils/api';
import { formatNumber } from '../../utils/format';
import BackButton from '../../components/common/BackButton';
import { useBranch } from '../../context/BranchContext';
import Pagination, { usePagination } from '../../components/common/Pagination';
import '../../components/ModuleStyles.css';

export default function ProjectList() {
    const { t } = useTranslation();
    const navigate = useNavigate();
    const { currentBranch, loading: branchLoading } = useBranch();
    const [projects, setProjects] = useState([]);
    const [summary, setSummary] = useState({});
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [statusFilter, setStatusFilter] = useState('');

    useEffect(() => {
        if (!branchLoading) {
            fetchData();
        }
    }, [statusFilter, currentBranch, branchLoading]);

    const fetchData = async () => {
        try {
            setLoading(true);
            const params = {};
            if (statusFilter) params.status_filter = statusFilter;
            if (currentBranch) params.branch_id = currentBranch.id;

            const [projectsRes, summaryRes] = await Promise.all([
                projectsAPI.list(params),
                projectsAPI.summary(params)
            ]);
            setProjects(projectsRes.data);
            setSummary(summaryRes.data);
        } catch (error) {
            console.error('Failed to fetch projects:', error);
        } finally {
            setLoading(false);
        }
    };

    const filteredProjects = projects.filter(p =>
        p.project_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        p.project_code?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        p.customer_name?.toLowerCase().includes(searchTerm.toLowerCase())
    );

    const { currentPage, pageSize, totalItems, paginatedItems, onPageChange, onPageSizeChange } = usePagination(filteredProjects);

    const getStatusBadge = (status) => {
        const map = {
            planning: { label: t('projects.status.planning'), class: 'badge-info' },
            in_progress: { label: t('projects.status.in_progress'), class: 'badge-warning' },
            completed: { label: t('projects.status.completed'), class: 'badge-success' },
            on_hold: { label: t('projects.status.on_hold'), class: 'badge-secondary' },
            cancelled: { label: t('projects.status.cancelled'), class: 'badge-danger' },
        };
        const s = map[status] || { label: status, class: 'badge-secondary' };
        return <span className={`badge ${s.class}`}>{s.label}</span>;
    };

    const getProgressColor = (pct) => {
        if (pct >= 80) return '#28a745';
        if (pct >= 50) return '#ffc107';
        if (pct >= 20) return '#17a2b8';
        return '#6c757d';
    };

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <div className="d-flex align-items-center justify-content-between w-100">
                    <div>
                        <h1 className="workspace-title">{t('projects.title')}</h1>
                        <p className="workspace-subtitle">{t('projects.subtitle')}</p>
                    </div>
                    <div className="header-actions d-flex gap-2">
                        <button className="btn btn-outline-primary" onClick={() => navigate('/projects/resources')}>
                            <FolderKanban size={18} /> {t('projects.resource_allocation')}
                        </button>
                        <button className="btn btn-primary" onClick={() => navigate('/projects/new')}>
                            <Plus size={18} /> {t('projects.new')}
                        </button>
                    </div>
                </div>
            </div>

            {/* Metrics */}
            <div className="metrics-grid mb-4">
                <div className="metric-card metric-card-iconic">
                    <div className="metric-icon" style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
                        <FolderKanban size={24} color="white" />
                    </div>
                    <div className="metric-info">
                        <span className="metric-label">{t('projects.metrics.total')}</span>
                        <span className="metric-value text-dark">{summary.total_projects || 0}</span>
                    </div>
                </div>
                <div className="metric-card metric-card-iconic">
                    <div className="metric-icon" style={{ background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)' }}>
                        <Clock size={24} color="white" />
                    </div>
                    <div className="metric-info">
                        <span className="metric-label">{t('projects.metrics.in_progress')}</span>
                        <span className="metric-value text-dark">{summary.in_progress || 0}</span>
                    </div>
                </div>
                <div className="metric-card metric-card-iconic">
                    <div className="metric-icon" style={{ background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)' }}>
                        <CheckCircle2 size={24} color="white" />
                    </div>
                    <div className="metric-info">
                        <span className="metric-label">{t('projects.metrics.completed')}</span>
                        <span className="metric-value text-dark">{summary.completed || 0}</span>
                    </div>
                </div>
                <div className="metric-card metric-card-iconic">
                    <div className="metric-icon" style={{ background: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)' }}>
                        <TrendingUp size={24} color="white" />
                    </div>
                    <div className="metric-info">
                        <span className="metric-label">{t('projects.metrics.total_budget')}</span>
                        <span className="metric-value text-dark" style={{ fontSize: '20px' }}>{formatNumber(summary.total_budget || 0)}</span>
                    </div>
                </div>
            </div>

            {/* Quick Navigation Cards */}
            <div className="modules-grid" style={{ gap: '16px', marginBottom: '16px' }}>

                {/* Project Management */}
                <div className="card">
                    <h3 className="section-title" style={{ display: 'flex', alignItems: 'center', gap: '8px', margin: 0 }}>
                        <FolderKanban size={18} style={{ color: 'var(--primary)' }} /> {t('projects.management', 'إدارة المشاريع')}
                    </h3>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginTop: '12px' }}>
                        <Link to="/projects/new" className="btn btn-outline" style={{ textAlign: 'center', fontSize: '13px', padding: '10px 8px' }}>
                            <Plus size={14} /> {t('projects.new')}
                        </Link>
                        <Link to="/projects/resources" className="btn btn-outline" style={{ textAlign: 'center', fontSize: '13px', padding: '10px 8px' }}>
                            <Users size={14} /> {t('projects.resource_allocation')}
                        </Link>
                        <Link to="/projects/gantt" className="btn btn-outline" style={{ textAlign: 'center', fontSize: '13px', padding: '10px 8px' }}>
                            📅 {t('projects.gantt_chart', 'مخطط جانت')}
                        </Link>
                        <Link to="/projects/risks" className="btn btn-outline" style={{ textAlign: 'center', fontSize: '13px', padding: '10px 8px' }}>
                            ⚠️ {t('projects.risks', 'سجل المخاطر')}
                        </Link>
                    </div>
                </div>

                {/* Reports */}
                <div className="card">
                    <h3 className="section-title" style={{ display: 'flex', alignItems: 'center', gap: '8px', margin: 0 }}>
                        <BarChart3 size={18} style={{ color: 'var(--success)' }} /> {t('common.reports', 'التقارير')}
                    </h3>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '8px', marginTop: '12px' }}>
                        <Link to="/projects/kpi" className="btn btn-outline" style={{ textAlign: 'center', fontSize: '13px', padding: '10px 8px', background: 'linear-gradient(135deg, rgba(79,70,229,0.06), rgba(79,70,229,0.12))', borderColor: '#4f46e5', color: '#4f46e5', fontWeight: 600 }}>
                            📈 {t('kpi.projects_dashboard', 'مؤشرات أداء المشاريع')}
                        </Link>
                        <Link to="/projects/reports/financials" className="btn btn-outline" style={{ textAlign: 'center', fontSize: '13px', padding: '10px 8px' }}>
                            <DollarSign size={14} /> {t('projects.reports.financials', 'التقرير المالي للمشاريع')}
                        </Link>
                        <Link to="/projects/reports/resources" className="btn btn-outline" style={{ textAlign: 'center', fontSize: '13px', padding: '10px 8px' }}>
                            <Users size={14} /> {t('projects.reports.resources', 'استخدام الموارد')}
                        </Link>
                    </div>
                </div>

                {/* Summary Stats Card */}
                <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                    <h3 className="section-title" style={{ display: 'flex', alignItems: 'center', gap: '8px', margin: 0 }}>
                        <TrendingUp size={18} style={{ color: 'var(--secondary)' }} /> {t('projects.overview', 'نظرة عامة')}
                    </h3>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginTop: '12px' }}>
                        <div style={{ textAlign: 'center' }}>
                            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{t('projects.status.planning')}</div>
                            <div style={{ fontSize: '20px', fontWeight: '700', color: 'var(--primary)' }}>{summary.planning || 0}</div>
                        </div>
                        <div style={{ textAlign: 'center' }}>
                            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{t('projects.status.on_hold')}</div>
                            <div style={{ fontSize: '20px', fontWeight: '700', color: 'var(--warning, #f59e0b)' }}>{summary.on_hold || 0}</div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Search & Filter */}
            <div className="card section-card">
                <div className="card-body">
                    <div className="d-flex gap-3 mb-3 flex-wrap">
                        <div className="search-box flex-grow-1">
                            <Search size={18} />
                            <input
                                type="text"
                                className="form-input"
                                placeholder={t('common.search')}
                                value={searchTerm}
                                onChange={e => setSearchTerm(e.target.value)}
                            />
                        </div>
                        <select
                            className="form-input"
                            style={{ width: 180 }}
                            value={statusFilter}
                            onChange={e => setStatusFilter(e.target.value)}
                        >
                            <option value="">{t('common.all')}</option>
                            <option value="planning">{t('projects.status.planning')}</option>
                            <option value="in_progress">{t('projects.status.in_progress')}</option>
                            <option value="completed">{t('projects.status.completed')}</option>
                            <option value="on_hold">{t('projects.status.on_hold')}</option>
                            <option value="cancelled">{t('projects.status.cancelled')}</option>
                        </select>
                    </div>

                    <div className="data-table-container">
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th>{t('projects.fields.code')}</th>
                                    <th>{t('projects.fields.name')}</th>
                                    <th>{t('projects.fields.customer')}</th>
                                    <th>{t('projects.fields.manager')}</th>
                                    <th>{t('projects.fields.status')}</th>
                                    <th>{t('projects.fields.progress')}</th>
                                    <th>{t('projects.fields.budget')}</th>
                                    <th>{t('projects.fields.expenses')}</th>
                                    <th>{t('projects.fields.tasks')}</th>
                                </tr>
                            </thead>
                            <tbody>
                                {loading ? (
                                    <tr>
                                        <td colSpan="9" className="text-center py-5">
                                            <span className="loading"></span>
                                        </td>
                                    </tr>
                                ) : filteredProjects.length === 0 ? (
                                    <tr>
                                        <td colSpan="9" className="text-center py-5 text-muted">
                                            {t('common.no_data')}
                                        </td>
                                    </tr>
                                ) : paginatedItems.map(project => {
                                    const progress = parseFloat(project.progress_percentage || 0);
                                    return (
                                        <tr key={project.id}
                                            onClick={() => navigate(`/projects/${project.id}`)}
                                            style={{ cursor: 'pointer' }}>
                                            <td className="fw-medium">{project.project_code}</td>
                                            <td className="fw-bold">{project.project_name}</td>
                                            <td>{project.customer_name || '-'}</td>
                                            <td>{project.manager_name || '-'}</td>
                                            <td>{getStatusBadge(project.status)}</td>
                                            <td style={{ minWidth: 120 }}>
                                                <div className="d-flex align-items-center gap-2">
                                                    <div style={{
                                                        flex: 1, height: 8, borderRadius: 4,
                                                        background: '#e9ecef', overflow: 'hidden'
                                                    }}>
                                                        <div style={{
                                                            width: `${progress}%`, height: '100%',
                                                            background: getProgressColor(progress),
                                                            borderRadius: 4, transition: 'width 0.3s'
                                                        }} />
                                                    </div>
                                                    <small className="text-muted">{progress.toFixed(0)}%</small>
                                                </div>
                                            </td>
                                            <td>{formatNumber(project.planned_budget || 0)}</td>
                                            <td className={parseFloat(project.total_expenses || 0) > parseFloat(project.planned_budget || 0) ? 'text-danger fw-bold' : ''}>
                                                {formatNumber(project.total_expenses || 0)}
                                            </td>
                                            <td>
                                                <span className="text-muted">
                                                    {project.completed_tasks || 0}/{project.total_tasks || 0}
                                                </span>
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                        <Pagination currentPage={currentPage} totalItems={totalItems} pageSize={pageSize} onPageChange={onPageChange} onPageSizeChange={onPageSizeChange} />
                    </div>
                </div>
            </div>
        </div>
    );
}
