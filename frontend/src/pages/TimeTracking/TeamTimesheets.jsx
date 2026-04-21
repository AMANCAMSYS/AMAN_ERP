import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { timesheetAPI } from '../../utils/api';
import { toastEmitter } from '../../utils/toastEmitter';
import { CheckCircle, XCircle, Filter } from 'lucide-react';
import '../../index.css';
import '../../components/ModuleStyles.css';
import BackButton from '../../components/common/BackButton';
import DateInput from '../../components/common/DateInput';

const TeamTimesheets = () => {
    const { t, i18n } = useTranslation();
    const isRTL = i18n.language === 'ar';

    const [entries, setEntries] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filters, setFilters] = useState({ entry_status: 'submitted' });
    const [rejecting, setRejecting] = useState(null); // entry id being rejected
    const [rejectReason, setRejectReason] = useState('');
    const [actionMsg, setActionMsg] = useState('');

    const load = () => {
        setLoading(true);
        timesheetAPI.listTeam(filters)
            .then(res => setEntries(res.data || []))
            .catch(e => toastEmitter.emit(t('common.error'), 'error'))
            .finally(() => setLoading(false));
    };

    useEffect(() => { load(); }, [filters]);

    const handleApprove = async (id) => {
        try {
            await timesheetAPI.approve(id);
            setActionMsg(t('timetracking.approved_success'));
            load();
        } catch (e) {
            toastEmitter.emit(t('common.error'), 'error');
        }
    };

    const handleReject = async (id) => {
        if (!rejectReason.trim()) return;
        try {
            await timesheetAPI.reject(id, { rejection_reason: rejectReason });
            setRejecting(null);
            setRejectReason('');
            setActionMsg(t('timetracking.rejected_success'));
            load();
        } catch (e) {
            toastEmitter.emit(t('common.error'), 'error');
        }
    };

    const updateFilter = (key, value) => {
        setFilters(prev => ({ ...prev, [key]: value || undefined }));
    };

    return (
        <div className="module-container" dir={isRTL ? 'rtl' : 'ltr'}>
            <BackButton />
            <div className="module-header">
                <h1>{t('timetracking.team_timesheets')}</h1>
            </div>

            {actionMsg && (
                <div className="alert alert-success" style={{ marginBottom: 12 }}>
                    <CheckCircle size={16} /> {actionMsg}
                </div>
            )}

            <div className="module-filters" style={{ display: 'flex', gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
                <Filter size={16} style={{ alignSelf: 'center' }} />
                <select
                    className="form-control"
                    style={{ maxWidth: 160 }}
                    value={filters.entry_status || ''}
                    onChange={e => updateFilter('entry_status', e.target.value)}
                >
                    <option value="">{t('timetracking.all_statuses')}</option>
                    <option value="submitted">{t('timetracking.status_submitted')}</option>
                    <option value="approved">{t('timetracking.status_approved')}</option>
                    <option value="rejected">{t('timetracking.status_rejected')}</option>
                    <option value="draft">{t('timetracking.status_draft')}</option>
                </select>
                <DateInput
                    className="form-control"
                    style={{ maxWidth: 160 }}
                    placeholder={t('timetracking.date_from')}
                    onChange={e => updateFilter('date_from', e.target.value)}
                />
                <DateInput
                    className="form-control"
                    style={{ maxWidth: 160 }}
                    placeholder={t('timetracking.date_to')}
                    onChange={e => updateFilter('date_to', e.target.value)}
                />
            </div>

            {loading ? (
                <div className="loading-spinner">{t('common.loading')}</div>
            ) : entries.length === 0 ? (
                <div className="empty-state">{t('timetracking.no_entries')}</div>
            ) : (
                <div className="data-table-wrapper">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>{t('timetracking.employee')}</th>
                                <th>{t('timetracking.project')}</th>
                                <th>{t('timetracking.task')}</th>
                                <th>{t('timetracking.date')}</th>
                                <th>{t('timetracking.hours')}</th>
                                <th>{t('timetracking.billable')}</th>
                                <th>{t('timetracking.description')}</th>
                                <th>{t('timetracking.status')}</th>
                                <th>{t('common.actions')}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {entries.map(e => (
                                <React.Fragment key={e.id}>
                                    <tr>
                                        <td>{e.employee_name}</td>
                                        <td>{e.project_name}</td>
                                        <td>{e.task_name || '—'}</td>
                                        <td>{e.date}</td>
                                        <td style={{ fontWeight: 600 }}>{e.hours}</td>
                                        <td>
                                            <span className={`badge ${e.is_billable ? 'badge-success' : 'badge-secondary'}`}>
                                                {e.is_billable ? t('timetracking.billable') : t('timetracking.non_billable')}
                                            </span>
                                        </td>
                                        <td style={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                            {e.description || '—'}
                                        </td>
                                        <td>
                                            <span className={`badge badge-${
                                                e.status === 'approved' ? 'success' :
                                                e.status === 'submitted' ? 'warning' :
                                                e.status === 'rejected' ? 'danger' : 'secondary'
                                            }`}>
                                                {t(`timetracking.status_${e.status}`)}
                                            </span>
                                        </td>
                                        <td>
                                            {e.status === 'submitted' && (
                                                <div style={{ display: 'flex', gap: 4 }}>
                                                    <button
                                                        className="btn btn-sm btn-success"
                                                        title={t('timetracking.approve')}
                                                        onClick={() => handleApprove(e.id)}
                                                    >
                                                        <CheckCircle size={14} />
                                                    </button>
                                                    <button
                                                        className="btn btn-sm btn-danger"
                                                        title={t('timetracking.reject')}
                                                        onClick={() => { setRejecting(e.id); setRejectReason(''); }}
                                                    >
                                                        <XCircle size={14} />
                                                    </button>
                                                </div>
                                            )}
                                            {e.status === 'rejected' && e.rejection_reason && (
                                                <small style={{ color: '#dc3545' }}>{e.rejection_reason}</small>
                                            )}
                                        </td>
                                    </tr>
                                    {rejecting === e.id && (
                                        <tr>
                                            <td colSpan={9} style={{ background: '#fff8f8', padding: 12 }}>
                                                <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                                                    <input
                                                        type="text"
                                                        className="form-control"
                                                        placeholder={t('timetracking.rejection_reason')}
                                                        value={rejectReason}
                                                        onChange={e2 => setRejectReason(e2.target.value)}
                                                        style={{ flex: 1 }}
                                                    />
                                                    <button
                                                        className="btn btn-sm btn-danger"
                                                        onClick={() => handleReject(e.id)}
                                                        disabled={!rejectReason.trim()}
                                                    >
                                                        {t('timetracking.confirm_reject')}
                                                    </button>
                                                    <button
                                                        className="btn btn-sm btn-secondary"
                                                        onClick={() => setRejecting(null)}
                                                    >
                                                        {t('common.cancel')}
                                                    </button>
                                                </div>
                                            </td>
                                        </tr>
                                    )}
                                </React.Fragment>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
};

export default TeamTimesheets;
