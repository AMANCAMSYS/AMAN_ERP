
import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Plus, FileText, BarChart2, X, Trash2, AlertTriangle, PlayCircle, Lock, TrendingUp, TrendingDown } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { budgetsAPI } from '../../utils/api';
import { formatNumber } from '../../utils/format';
import { getCurrency } from '../../utils/auth';
import CustomDatePicker from '../../components/common/CustomDatePicker';
import { formatDate, formatDateTime } from '../../utils/dateUtils';
import BackButton from '../../components/common/BackButton';

const Budgets = () => {
    const { t } = useTranslation();
    const navigate = useNavigate();
    const [budgets, setBudgets] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [actionLoading, setActionLoading] = useState(false);
    const [stats, setStats] = useState(null);
    const [alerts, setAlerts] = useState([]);
    const currency = getCurrency() || '';

    const [formData, setFormData] = useState({
        name: '',
        start_date: '',
        end_date: '',
        description: ''
    });

    useEffect(() => {
        fetchAll();
    }, []);

    const fetchAll = async () => {
        setLoading(true);
        try {
            const [budgetsRes, statsRes, alertsRes] = await Promise.all([
                budgetsAPI.list(),
                budgetsAPI.getStats().catch(() => ({ data: null })),
                budgetsAPI.getOverrunAlerts(80).catch(() => ({ data: [] }))
            ]);
            setBudgets(budgetsRes.data || []);
            setStats(statsRes.data);
            setAlerts(alertsRes.data || []);
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const handleCreate = async (e) => {
        e.preventDefault();
        setActionLoading(true);
        try {
            await budgetsAPI.create(formData);
            toast.success(t('common.success'));
            setIsModalOpen(false);
            setFormData({ name: '', start_date: '', end_date: '', description: '' });
            fetchAll();
        } catch (error) {
            console.error(error);
            toast.error(error.response?.data?.detail || t('common.error'));
        } finally {
            setActionLoading(false);
        }
    };

    const handleDelete = async (id) => {
        if (!window.confirm(t('common.confirm_delete'))) return;
        try {
            await budgetsAPI.delete(id);
            toast.success(t('common.success'));
            fetchAll();
        } catch (error) {
            console.error(error);
            toast.error(t('common.error'));
        }
    };

    const handleActivate = async (id) => {
        try {
            await budgetsAPI.activate(id);
            toast.success(t('accounting.budgets.activated'));
            fetchAll();
        } catch (error) {
            toast.error(error.response?.data?.detail || t('common.error'));
        }
    };

    const handleClose = async (id) => {
        if (!window.confirm(t('accounting.budgets.confirm_close'))) return;
        try {
            await budgetsAPI.close(id);
            toast.success(t('accounting.budgets.closed_success'));
            fetchAll();
        } catch (error) {
            toast.error(error.response?.data?.detail || t('common.error'));
        }
    };

    const getStatusBadge = (status) => {
        const styles = {
            draft: { bg: '#f3f4f6', color: '#6b7280', icon: '📝' },
            active: { bg: '#dcfce7', color: '#16a34a', icon: '✅' },
            closed: { bg: '#fef3c7', color: '#d97706', icon: '🔒' }
        };
        const s = styles[status] || styles.draft;
        return (
            <span style={{ background: s.bg, color: s.color, padding: '4px 12px', borderRadius: '20px', fontSize: '12px', fontWeight: '600' }}>
                {s.icon} {t(`accounting.budgets.status_${status}`, status)}
            </span>
        );
    };

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                        <BackButton />
                        <div>
                            <h1 className="workspace-title">{t('accounting.budgets.title')}</h1>
                            <p className="text-muted small mb-0">{t('accounting.budgets.subtitle')}</p>
                        </div>
                    </div>
                    <button onClick={() => setIsModalOpen(true)} className="btn btn-primary">
                        <span style={{ marginLeft: '8px' }}>+</span>
                        {t('accounting.budgets.new')}
                    </button>
                </div>
            </div>

            {/* Stats Cards */}
            {stats && (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '24px' }}>
                    <div className="card p-3 text-center">
                        <BarChart2 size={24} className="text-primary mb-2" />
                        <div className="small text-muted">{t('accounting.budgets.stats.total')}</div>
                        <div className="fw-bold fs-4">{stats.total_budgets}</div>
                        <div className="small text-muted">
                            {t('accounting.budgets.stats.active')}: {stats.active_count} | {t('accounting.budgets.stats.draft')}: {stats.draft_count}
                        </div>
                    </div>
                    <div className="card p-3 text-center">
                        <TrendingUp size={24} className="text-primary mb-2" />
                        <div className="small text-muted">{t('accounting.budgets.stats.total_planned')}</div>
                        <div className="fw-bold fs-4">{formatNumber(stats.total_planned)}</div>
                        <div className="small text-muted">{currency}</div>
                    </div>
                    <div className="card p-3 text-center">
                        <TrendingDown size={24} className="text-warning mb-2" />
                        <div className="small text-muted">{t('accounting.budgets.stats.total_actual')}</div>
                        <div className="fw-bold fs-4">{formatNumber(stats.total_actual)}</div>
                        <div className="small text-muted">{currency} • {stats.overall_usage_pct}%</div>
                    </div>
                    <div className="card p-3 text-center">
                        <AlertTriangle size={24} className={stats.overrun_items_count > 0 ? 'text-danger mb-2' : 'text-success mb-2'} />
                        <div className="small text-muted">{t('accounting.budgets.stats.overruns')}</div>
                        <div className={`fw-bold fs-4 ${stats.overrun_items_count > 0 ? 'text-danger' : 'text-success'}`}>
                            {stats.overrun_items_count}
                        </div>
                        <div className="small text-muted">{stats.overrun_items_count > 0 ? '⚠️ تحذير' : '✅ جيد'}</div>
                    </div>
                </div>
            )}

            {/* Overrun Alerts */}
            {alerts.length > 0 && (
                <div className="card card-compact mb-4" style={{ borderLeft: '4px solid #dc2626' }}>
                    <div >
                        <h6 className="fw-bold mb-3 d-flex align-items-center gap-2">
                            <AlertTriangle size={18} className="text-danger" />
                            {t('accounting.budgets.overrun_alerts')}
                            <span className="badge bg-danger rounded-pill">{alerts.length}</span>
                        </h6>
                        <div className="table-responsive" style={{ maxHeight: '200px', overflowY: 'auto' }}>
                            <table className="data-table" style={{ fontSize: '13px' }}>
                                <thead>
                                    <tr>
                                        <th>{t('accounting.budgets.budget_name')}</th>
                                        <th>{t('accounting.account_name')}</th>
                                        <th className="text-center">{t('reports.budget_vs_actual.planned')}</th>
                                        <th className="text-center">{t('reports.budget_vs_actual.actual')}</th>
                                        <th className="text-center">{t('accounting.budgets.usage')}</th>
                                        <th className="text-center">{t('common.status_title')}</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {alerts.slice(0, 10).map((alert, idx) => (
                                        <tr key={idx}>
                                            <td className="fw-medium">{alert.budget_name}</td>
                                            <td>
                                                <span className="text-primary me-1">{alert.account_number}</span>
                                                {alert.account_name}
                                            </td>
                                            <td className="text-center">{formatNumber(alert.planned)}</td>
                                            <td className="text-center">{formatNumber(alert.actual)}</td>
                                            <td className="text-center">
                                                <div className="d-flex align-items-center gap-1 justify-content-center">
                                                    <div style={{ width: '60px', height: '5px', background: '#f3f4f6', borderRadius: '3px', overflow: 'hidden' }}>
                                                        <div style={{
                                                            height: '100%',
                                                            width: `${Math.min(alert.usage_percentage, 100)}%`,
                                                            background: alert.severity === 'critical' ? '#dc2626' : alert.severity === 'danger' ? '#f97316' : '#f59e0b',
                                                            borderRadius: '3px'
                                                        }} />
                                                    </div>
                                                    <span style={{ fontSize: '11px', fontWeight: '600' }}>{alert.usage_percentage}%</span>
                                                </div>
                                            </td>
                                            <td className="text-center">
                                                <span className={`badge ${alert.severity === 'critical' ? 'bg-danger' : 'bg-warning text-dark'}`} style={{ fontSize: '11px' }}>
                                                    {alert.severity === 'critical' ? '🔴 ' + t('accounting.budgets.over_budget') :
                                                     alert.severity === 'danger' ? '🟠 ' + t('accounting.budgets.near_limit') :
                                                     '🟡 ' + t('accounting.budgets.warning_label')}
                                                </span>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            )}

            {/* Budget Cards */}
            <div className="row g-4">
                {loading ? (
                    <div className="col-12 text-center p-5">
                        <div className="spinner-border text-primary" role="status">
                            <span className="visually-hidden">{t('common.loading')}</span>
                        </div>
                    </div>
                ) : budgets.length === 0 ? (
                    <div className="col-12 text-center p-5">
                        <div style={{ fontSize: '48px', marginBottom: '16px' }}>📊</div>
                        <h3 className="h5 text-muted">{t('common.no_data')}</h3>
                    </div>
                ) : (
                    budgets.map((budget) => (
                        <div key={budget.id} className="col-md-6 col-lg-4">
                            <div className="card h-100" style={{ transition: 'transform 0.2s' }}>
                                <div >
                                    <div className="d-flex justify-content-between align-items-start mb-3">
                                        <h5 className="fw-bold mb-0" style={{ color: 'var(--text-primary)' }}>{budget.name}</h5>
                                        {getStatusBadge(budget.status)}
                                    </div>

                                    {budget.description && (
                                        <p className="text-muted small mb-3">{budget.description}</p>
                                    )}

                                    <div className="row g-2 mb-3">
                                        <div className="col-6">
                                            <div className="text-muted small mb-1">{t('common.start_date')}</div>
                                            <div className="fw-semibold small" style={{ color: 'var(--text-primary)' }}>{formatDate(budget.start_date)}</div>
                                        </div>
                                        <div className="col-6">
                                            <div className="text-muted small mb-1">{t('common.end_date')}</div>
                                            <div className="fw-semibold small" style={{ color: 'var(--text-primary)' }}>{formatDate(budget.end_date)}</div>
                                        </div>
                                    </div>

                                    <div className="d-flex gap-2 mb-2">
                                        <button
                                            className="btn btn-outline-primary btn-sm flex-grow-1"
                                            onClick={() => navigate(`/accounting/budgets/${budget.id}/items`)}
                                            style={{ borderRadius: '8px' }}
                                        >
                                            <FileText size={14} className="me-1" />
                                            {t('accounting.budgets.items')}
                                        </button>
                                        <button
                                            className="btn btn-primary btn-sm flex-grow-1"
                                            onClick={() => navigate(`/accounting/budgets/${budget.id}/report`)}
                                            style={{ borderRadius: '8px' }}
                                        >
                                            <BarChart2 size={14} className="me-1" />
                                            {t('accounting.budgets.report')}
                                        </button>
                                    </div>

                                    <div className="d-flex gap-2 align-items-center mt-2">
                                        {budget.status === 'draft' && (
                                            <button
                                                className="btn btn-outline-success btn-sm flex-grow-1"
                                                onClick={() => handleActivate(budget.id)}
                                                style={{ borderRadius: '8px', fontSize: '12px' }}
                                            >
                                                <PlayCircle size={14} className="me-1" />
                                                {t('accounting.budgets.activate')}
                                            </button>
                                        )}
                                        {budget.status === 'active' && (
                                            <button
                                                className="btn btn-outline-warning btn-sm flex-grow-1"
                                                onClick={() => handleClose(budget.id)}
                                                style={{ borderRadius: '8px', fontSize: '12px' }}
                                            >
                                                <Lock size={14} className="me-1" />
                                                {t('accounting.budgets.close_budget')}
                                            </button>
                                        )}
                                        {budget.status !== 'active' && (
                                            <button
                                                onClick={() => handleDelete(budget.id)}
                                                className="btn btn-outline-danger btn-sm"
                                                style={{ borderRadius: '8px', fontSize: '12px' }}
                                                title={t('common.delete')}
                                            >
                                                <Trash2 size={14} />
                                            </button>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))
                )}
            </div>

            {/* Create Modal */}
            {isModalOpen && (
                <div className="modal-overlay">
                    <div className="modal-content" style={{ maxWidth: '500px', borderRadius: '16px' }}>
                        <div className="modal-header d-flex justify-content-between align-items-center" style={{ padding: '20px 24px', borderBottom: '1px solid #eee' }}>
                            <h5 className="modal-title fw-bold" style={{ fontSize: '18px' }}>{t('accounting.budgets.new')}</h5>
                            <button type="button" className="btn-icon bg-transparent" onClick={() => setIsModalOpen(false)}>
                                <X size={20} className="text-muted" />
                            </button>
                        </div>
                        <form onSubmit={handleCreate}>
                            <div className="modal-body p-4">
                                <div className="form-group mb-4">
                                    <label className="form-label mb-2">{t('common.name')}</label>
                                    <input
                                        type="text" className="form-input" required
                                        value={formData.name}
                                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                        placeholder={t('accounting.budgets.name_placeholder')}
                                    />
                                </div>
                                <div className="row g-3">
                                    <div className="col-6 mb-4">
                                        <CustomDatePicker
                                            label={t('common.start_date')}
                                            selected={formatDate(formData.start_date)}
                                            onChange={(dateStr) => setFormData({ ...formData, start_date: dateStr })}
                                            required
                                        />
                                    </div>
                                    <div className="col-6 mb-4">
                                        <CustomDatePicker
                                            label={t('common.end_date')}
                                            selected={formatDate(formData.end_date)}
                                            onChange={(dateStr) => setFormData({ ...formData, end_date: dateStr })}
                                            required
                                        />
                                    </div>
                                </div>
                                <div className="form-group mb-0">
                                    <label className="form-label mb-2">{t('common.description')}</label>
                                    <textarea
                                        className="form-input" rows="3"
                                        value={formData.description}
                                        onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                                        placeholder={t('common.notes')}
                                    ></textarea>
                                </div>
                            </div>
                            <div className="modal-footer p-3 bg-light border-top-0 d-flex justify-content-end gap-2" style={{ borderRadius: '0 0 16px 16px' }}>
                                <button type="button" className="btn btn-secondary" onClick={() => setIsModalOpen(false)}>
                                    {t('common.cancel')}
                                </button>
                                <button type="submit" className="btn btn-primary px-4" disabled={actionLoading}>
                                    {actionLoading ? t('common.saving') : t('common.save')}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Budgets;
