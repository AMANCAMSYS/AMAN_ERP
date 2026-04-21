import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { selfServiceAPI } from '../../utils/api';
import { toastEmitter } from '../../utils/toastEmitter';
import { Users, CheckCircle, XCircle, Clock } from 'lucide-react';
import BackButton from '../../components/common/BackButton';
import SimpleModal from '../../components/common/SimpleModal';
import '../../components/ModuleStyles.css';
import { PageLoading } from '../../components/common/LoadingStates'

const TeamRequests = () => {
    const { t } = useTranslation();
    const [requests, setRequests] = useState([]);
    const [loading, setLoading] = useState(true);
    const [actionLoading, setActionLoading] = useState(null);
    const [rejectModal, setRejectModal] = useState({ open: false, id: null });
    const [rejectReason, setRejectReason] = useState('');
    const [filterStatus, setFilterStatus] = useState('pending');

    useEffect(() => {
        fetchRequests();
    }, [filterStatus]);

    const fetchRequests = async () => {
        setLoading(true);
        try {
            const res = await selfServiceAPI.listTeamRequests({ status: filterStatus || undefined });
            setRequests(res.data?.data || []);
        } catch (err) {
            toastEmitter.emit(t('common.error'), 'error');
        } finally {
            setLoading(false);
        }
    };

    const handleApprove = async (id) => {
        setActionLoading(id);
        try {
            await selfServiceAPI.approveLeave(id);
            toastEmitter.emit(t('self_service.leave_approved'), 'success');
            fetchRequests();
        } catch (err) {
            toastEmitter.emit(err.response?.data?.detail || t('common.error'), 'error');
        } finally {
            setActionLoading(null);
        }
    };

    const handleReject = async () => {
        if (!rejectModal.id) return;
        setActionLoading(rejectModal.id);
        try {
            await selfServiceAPI.rejectLeave(rejectModal.id, rejectReason);
            toastEmitter.emit(t('self_service.leave_rejected_msg'), 'success');
            setRejectModal({ open: false, id: null });
            setRejectReason('');
            fetchRequests();
        } catch (err) {
            toastEmitter.emit(err.response?.data?.detail || t('common.error'), 'error');
        } finally {
            setActionLoading(null);
        }
    };

    const statusBadge = (status) => {
        const map = {
            approved: { icon: <CheckCircle size={14} />, cls: 'badge-success' },
            pending: { icon: <Clock size={14} />, cls: 'badge-warning' },
            rejected: { icon: <XCircle size={14} />, cls: 'badge-danger' },
        };
        const s = map[status] || { icon: null, cls: 'badge-secondary' };
        return <span className={`status-badge ${s.cls}`}>{s.icon} {t(`self_service.status_${status}`) || status}</span>;
    };

    return (
        <div className="module-container">
            <div className="module-header">
                <BackButton />
                <h1><Users size={22} /> {t('self_service.team_requests_title')}</h1>
            </div>

            <div style={{ marginBottom: 16, display: 'flex', gap: 8 }}>
                {['pending', 'approved', 'rejected', ''].map(s => (
                    <button
                        key={s}
                        className={`btn btn-sm ${filterStatus === s ? 'btn-primary' : 'btn-secondary'}`}
                        onClick={() => setFilterStatus(s)}
                    >
                        {s ? t(`self_service.status_${s}`) : t('common.all')}
                    </button>
                ))}
            </div>

            {loading ? (
                <PageLoading />
            ) : requests.length === 0 ? (
                <div className="card"><p className="text-muted">{t('self_service.no_team_requests')}</p></div>
            ) : (
                <div className="card">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>{t('self_service.employee')}</th>
                                <th>{t('self_service.leave_type')}</th>
                                <th>{t('self_service.start_date')}</th>
                                <th>{t('self_service.end_date')}</th>
                                <th>{t('self_service.days')}</th>
                                <th>{t('self_service.reason')}</th>
                                <th>{t('self_service.status')}</th>
                                {filterStatus === 'pending' && <th>{t('self_service.actions')}</th>}
                            </tr>
                        </thead>
                        <tbody>
                            {requests.map(req => (
                                <tr key={req.id}>
                                    <td>{req.employee_name}</td>
                                    <td>{req.leave_type}</td>
                                    <td>{req.start_date}</td>
                                    <td>{req.end_date}</td>
                                    <td>{req.days}</td>
                                    <td>{req.reason || '-'}</td>
                                    <td>{statusBadge(req.status)}</td>
                                    {filterStatus === 'pending' && (
                                        <td>
                                            <div style={{ display: 'flex', gap: 6 }}>
                                                <button
                                                    className="btn btn-sm btn-success"
                                                    onClick={() => handleApprove(req.id)}
                                                    disabled={actionLoading === req.id}
                                                >
                                                    <CheckCircle size={14} />
                                                </button>
                                                <button
                                                    className="btn btn-sm btn-danger"
                                                    onClick={() => setRejectModal({ open: true, id: req.id })}
                                                    disabled={actionLoading === req.id}
                                                >
                                                    <XCircle size={14} />
                                                </button>
                                            </div>
                                        </td>
                                    )}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {/* Reject Modal */}
            {rejectModal.open && (
                <SimpleModal title={t('self_service.reject_leave')} onClose={() => setRejectModal({ open: false, id: null })}>
                    <div className="form-group">
                        <label>{t('self_service.rejection_reason')}</label>
                        <textarea
                            value={rejectReason}
                            onChange={(e) => setRejectReason(e.target.value)}
                            className="form-control"
                            rows={3}
                        />
                    </div>
                    <div style={{ display: 'flex', gap: 12, marginTop: 16 }}>
                        <button className="btn btn-danger" onClick={handleReject} disabled={actionLoading}>
                            {t('self_service.confirm_reject')}
                        </button>
                        <button className="btn btn-secondary" onClick={() => setRejectModal({ open: false, id: null })}>
                            {t('common.cancel')}
                        </button>
                    </div>
                </SimpleModal>
            )}
        </div>
    );
};

export default TeamRequests;
