import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { selfServiceAPI } from '../../utils/api';
import { toastEmitter } from '../../utils/toastEmitter';
import { formatNumber } from '../../utils/format';
import { Calendar, FileText, User, Clock, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import BackButton from '../../components/common/BackButton';
import '../../components/ModuleStyles.css';
import { PageLoading } from '../../components/common/LoadingStates'

const EmployeeDashboard = () => {
    const { t, i18n } = useTranslation();
    const navigate = useNavigate();
    const isRTL = i18n.language === 'ar';
    const [balance, setBalance] = useState(null);
    const [recentLeaves, setRecentLeaves] = useState([]);
    const [recentPayslips, setRecentPayslips] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchDashboardData();
    }, []);

    const fetchDashboardData = async () => {
        setLoading(true);
        try {
            const [balRes, leavesRes, payslipsRes] = await Promise.all([
                selfServiceAPI.getLeaveBalance(),
                selfServiceAPI.listLeaveRequests(),
                selfServiceAPI.listPayslips(),
            ]);
            setBalance(balRes.data?.data || balRes.data);
            setRecentLeaves((leavesRes.data?.data || []).slice(0, 5));
            setRecentPayslips((payslipsRes.data?.data || []).slice(0, 5));
        } catch (err) {
            toastEmitter.emit(t('common.error'), 'error');
        } finally {
            setLoading(false);
        }
    };

    const statusBadge = (status) => {
        const map = {
            approved: { icon: <CheckCircle size={14} />, cls: 'badge-success' },
            pending: { icon: <Clock size={14} />, cls: 'badge-warning' },
            rejected: { icon: <XCircle size={14} />, cls: 'badge-danger' },
        };
        const s = map[status] || { icon: <AlertCircle size={14} />, cls: 'badge-secondary' };
        return <span className={`status-badge ${s.cls}`}>{s.icon} {t(`self_service.status_${status}`) || status}</span>;
    };

    if (loading) return <PageLoading />;

    return (
        <div className="module-container">
            <div className="module-header">
                <BackButton />
                <h1>{t('self_service.dashboard_title')}</h1>
            </div>

            {/* Leave Balance Cards */}
            {balance && (
                <div className="stats-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 16, marginBottom: 24 }}>
                    <div className="stat-card" onClick={() => navigate('/hr/self-service/leave-requests')} style={{ cursor: 'pointer' }}>
                        <Calendar size={24} />
                        <div className="stat-value">{balance.remaining_days}</div>
                        <div className="stat-label">{t('self_service.remaining_days')}</div>
                    </div>
                    <div className="stat-card">
                        <Calendar size={24} />
                        <div className="stat-value">{balance.annual_entitlement}</div>
                        <div className="stat-label">{t('self_service.annual_entitlement')}</div>
                    </div>
                    <div className="stat-card">
                        <CheckCircle size={24} />
                        <div className="stat-value">{balance.used_days}</div>
                        <div className="stat-label">{t('self_service.used_days')}</div>
                    </div>
                    <div className="stat-card">
                        <Clock size={24} />
                        <div className="stat-value">{balance.pending_days}</div>
                        <div className="stat-label">{t('self_service.pending_days')}</div>
                    </div>
                </div>
            )}

            {/* Quick Actions */}
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 24 }}>
                <button className="btn btn-primary" onClick={() => navigate('/hr/self-service/leave-request')}>
                    <Calendar size={16} /> {t('self_service.new_leave_request')}
                </button>
                <button className="btn btn-secondary" onClick={() => navigate('/hr/self-service/payslips')}>
                    <FileText size={16} /> {t('self_service.view_payslips')}
                </button>
                <button className="btn btn-secondary" onClick={() => navigate('/hr/self-service/profile')}>
                    <User size={16} /> {t('self_service.edit_profile')}
                </button>
            </div>

            {/* Recent Leave Requests */}
            <div className="card" style={{ marginBottom: 24 }}>
                <h3>{t('self_service.recent_leave_requests')}</h3>
                {recentLeaves.length === 0 ? (
                    <p className="text-muted">{t('self_service.no_leave_requests')}</p>
                ) : (
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>{t('self_service.leave_type')}</th>
                                <th>{t('self_service.start_date')}</th>
                                <th>{t('self_service.end_date')}</th>
                                <th>{t('self_service.days')}</th>
                                <th>{t('self_service.status')}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {recentLeaves.map(lr => (
                                <tr key={lr.id}>
                                    <td>{lr.leave_type}</td>
                                    <td>{lr.start_date}</td>
                                    <td>{lr.end_date}</td>
                                    <td>{lr.days}</td>
                                    <td>{statusBadge(lr.status)}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>

            {/* Recent Payslips */}
            <div className="card">
                <h3>{t('self_service.recent_payslips')}</h3>
                {recentPayslips.length === 0 ? (
                    <p className="text-muted">{t('self_service.no_payslips')}</p>
                ) : (
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>{t('self_service.period')}</th>
                                <th>{t('self_service.net_salary')}</th>
                                <th>{t('self_service.status')}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {recentPayslips.map(ps => (
                                <tr key={ps.id} onClick={() => navigate(`/hr/self-service/payslips/${ps.id}`)} style={{ cursor: 'pointer' }}>
                                    <td>{ps.period_name || `${ps.month}/${ps.year}`}</td>
                                    <td>{formatNumber(ps.net_salary || 0)}</td>
                                    <td>{ps.status}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>
        </div>
    );
};

export default EmployeeDashboard;
