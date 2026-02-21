import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { attendanceAPI } from '../../utils/api';
import { Clock, Calendar, AlertCircle, Play, Square, LogOut, CheckCircle } from 'lucide-react';
import { toast } from 'react-hot-toast';
import { formatShortDate, formatDateTime } from '../../utils/dateUtils';

const Attendance = () => {
    const { t } = useTranslation();
    const [status, setStatus] = useState('loading'); // loading, checked_in, checked_out, not_linked
    const [checkInTime, setCheckInTime] = useState(null);
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(true);
    const [actionLoading, setActionLoading] = useState(false);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            setLoading(true);
            const [statusRes, historyRes] = await Promise.all([
                attendanceAPI.getStatus(),
                attendanceAPI.getHistory()
            ]);

            // Check if statusRes.data is wrapped or direct
            const statusData = statusRes.data || statusRes;
            const historyData = historyRes.data || historyRes;

            setStatus(statusData.status);
            if (statusData.check_in_time) {
                setCheckInTime(statusData.check_in_time);
            }
            setHistory(Array.isArray(historyData) ? historyData : []);
        } catch (error) {
            console.error(error);
            // toast.error(t('common.error_loading_data'));
        } finally {
            setLoading(false);
        }
    };

    const handleAction = async () => {
        try {
            setActionLoading(true);
            if (status === 'checked_in') {
                await attendanceAPI.checkOut();
                toast.success(t('hr.attendance.check_out_success', 'Checked out successfully'));
            } else {
                await attendanceAPI.checkIn();
                toast.success(t('hr.attendance.check_in_success', 'Checked in successfully'));
            }
            // Refresh data
            fetchData();
        } catch (error) {
            console.error(error);
            toast.error(error.response?.data?.detail || t('common.error'));
        } finally {
            setActionLoading(false);
        }
    };

    const formatTime = (isoString) => {
        if (!isoString) return '-';
        // Using formatDateTime but only keeping the time part or custom format
        return formatDateTime(isoString).split(' ')[1];
    };

    const formatDate = (isoString) => {
        return formatShortDate(isoString);
    };

    if (loading) {
        return (
            <div className="workspace fade-in">
                <div className="card shadow-sm border-0 p-5 text-center">
                    <div className="spinner-border text-primary mb-3"></div>
                    <p className="text-muted">{t('common.loading')}</p>
                </div>
            </div>
        );
    }

    if (status === 'not_linked') {
        return (
            <div className="workspace fade-in">
                <div className="card shadow-sm border-0 p-5 text-center border-danger">
                    <AlertCircle className="mx-auto mb-4 text-danger" size={48} />
                    <h2 className="text-xl font-bold text-danger mb-2">{t('hr.attendance.not_linked')}</h2>
                    <p className="text-muted">{t('hr.attendance.contact_admin')}</p>
                </div>
            </div>
        );
    }

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <div className="header-title">
                    <h1 className="workspace-title">
                        <Clock size={24} className="me-2 text-primary" />
                        {t('hr.attendance.title')}
                    </h1>
                    <p className="workspace-subtitle">{t('hr.attendance.manage_subtitle')}</p>
                </div>
            </div>

            {/* Action Card */}
            <div className="card shadow-sm border-0 mb-4 overflow-hidden">
                <div className="card-body p-5 text-center">
                    <div className="mb-4">
                        <h2 className="display-4 fw-bold text-dark mb-0">
                            {formatDateTime(new Date()).split(' ')[1]}
                        </h2>
                        <p className="text-muted fs-5">
                            {formatShortDate(new Date())}
                        </p>
                    </div>

                    <div className="my-4 py-3 border-top border-bottom">
                        {status === 'checked_in' ? (
                            <div className="animate-pulse">
                                <span className="badge bg-success-light text-success px-3 py-2 rounded-pill mb-3">
                                    <span className="relative flex h-2 w-2 me-2 d-inline-block">
                                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-success opacity-75"></span>
                                        <span className="relative inline-flex rounded-full h-2 w-2 bg-success"></span>
                                    </span>
                                    {t('hr.attendance.active')}
                                </span>
                                <h3 className="h4 fw-bold">{t('hr.attendance.currently_working')}</h3>
                                <p className="text-muted">{t('hr.attendance.started_at')} {formatTime(checkInTime)}</p>
                            </div>
                        ) : (
                            <div>
                                <div className="mb-3 d-inline-block p-3 bg-light rounded-circle">
                                    <LogOut className="text-muted" size={32} />
                                </div>
                                <h3 className="h4 fw-bold text-muted">{t('hr.attendance.not_working')}</h3>
                                <p className="text-muted">{t('hr.attendance.please_check_in')}</p>
                            </div>
                        )}
                    </div>

                    <button
                        onClick={handleAction}
                        disabled={actionLoading}
                        className={`btn btn-lg px-5 py-3 fw-bold rounded-3 shadow-sm transition-all ${status === 'checked_in'
                            ? 'btn-danger bg-danger'
                            : 'btn-primary bg-primary'
                            }`}
                        style={{ minWidth: '220px' }}
                    >
                        {actionLoading ? (
                            <span>{t('common.processing')}</span>
                        ) : status === 'checked_in' ? (
                            <>
                                <Square size={20} className="me-2 fill-current" />
                                {t('hr.attendance.check_out')}
                            </>
                        ) : (
                            <>
                                <Play size={20} className="me-2 fill-current" />
                                {t('hr.attendance.check_in')}
                            </>
                        )}
                    </button>
                </div>
            </div>

            {/* History Table */}
            <div className="card shadow-sm border-0">
                <div className="card-header bg-white py-3 border-bottom d-flex align-items-center justify-content-between">
                    <h3 className="card-title h6 mb-0 fw-bold">
                        <Calendar size={18} className="me-2 text-primary" />
                        {t('hr.attendance.history')}
                    </h3>
                </div>
                <div className="card-body p-0">
                    <div className="data-table-container">
                        <table className="data-table mb-0 w-100">
                            <thead>
                                <tr>
                                    <th>{t('common.date')}</th>
                                    <th>{t('hr.attendance.check_in')}</th>
                                    <th>{t('hr.attendance.check_out')}</th>
                                    <th>{t('common.status')}</th>
                                    <th>{t('common.notes')}</th>
                                </tr>
                            </thead>
                            <tbody>
                                {history.length > 0 ? (
                                    history.map((record) => (
                                        <tr key={record.id} className="hover-row">
                                            <td className="fw-medium">{formatDate(record.date)}</td>
                                            <td className="text-success fw-bold">{formatTime(record.check_in)}</td>
                                            <td className="text-danger fw-bold">{formatTime(record.check_out)}</td>
                                            <td>
                                                <span className={`badge rounded-pill px-2 py-1 ${record.status === 'present'
                                                    ? 'bg-success-light text-success'
                                                    : 'bg-light text-muted'
                                                    }`}>
                                                    {record.status === 'present' && <CheckCircle size={10} className="me-1" />}
                                                    {record.status}
                                                </span>
                                            </td>
                                            <td className="text-muted small">{record.notes || '-'}</td>
                                        </tr>
                                    ))
                                ) : (
                                    <tr>
                                        <td colSpan="5" className="p-5 text-center text-muted">
                                            <Calendar size={48} className="text-light mb-3" />
                                            <p>{t('common.no_records_found')}</p>
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Attendance;
