import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
    Plus, Check, X, Calendar, FileText, User, Clock,
    CheckCircle, XCircle
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { hrAPI } from '../../utils/api';
import { hasPermission } from '../../utils/auth';
import { useBranch } from '../../context/BranchContext';
import '../../components/ModuleStyles.css';
import SimpleModal from '../../components/common/SimpleModal';
import Pagination, { usePagination } from '../../components/common/Pagination';
import { formatShortDate } from '../../utils/dateUtils';

import DateInput from '../../components/common/DateInput';
import BackButton from '../../components/common/BackButton';
const LeaveList = () => {
    const { t, i18n } = useTranslation();
    const navigate = useNavigate();
    const isRTL = i18n.language === 'ar';
    const [leaves, setLeaves] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [actionLoading, setActionLoading] = useState(false);
    const [filter, setFilter] = useState('all');
    const { currentBranch } = useBranch();

    // Permissions
    const canManageLeaves = hasPermission('hr.leaves.manage');

    // Form State
    const [formData, setFormData] = useState({
        leave_type: 'annual',
        start_date: '',
        end_date: '',
        reason: ''
    });

    useEffect(() => {
        fetchData();
    }, [currentBranch]);

    const fetchData = async () => {
        setLoading(true);
        try {
            const params = {};
            if (currentBranch?.id) {
                params.branch_id = currentBranch.id;
            }
            const response = await hrAPI.listLeaveRequests(params);
            setLeaves(Array.isArray(response.data) ? response.data : []);
        } catch (error) {
            console.error('Error fetching leaves:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleCreate = async () => {
        setActionLoading(true);
        try {
            await hrAPI.createLeaveRequest(formData);
            toast.success(t('common.success'));
            setIsModalOpen(false);
            setFormData({ leave_type: 'annual', start_date: '', end_date: '', reason: '' });
            fetchData();
        } catch (error) {
            console.error(error);
            toast.error(error.message || t('common.error_occurred'));
        } finally {
            setActionLoading(false);
        }
    };

    const handleStatusUpdate = async (id, status) => {
        if (!window.confirm(t('common.confirm_action'))) return;

        try {
            await hrAPI.updateLeaveStatus(id, status);
            toast.success(t('common.success'));
            fetchData();
        } catch (error) {
            console.error(error);
            toast.error(t('common.error_occurred'));
        }
    };

    const getStatusBadge = (status) => {
        const styles = {
            pending: 'badge-warning',
            approved: 'badge-success',
            rejected: 'badge-danger'
        };
        const icons = {
            pending: Clock,
            approved: CheckCircle,
            rejected: XCircle
        };
        const Icon = icons[status] || Clock;
        const label = t(`status.${status}`) || status;

        return (
            <span className={`badge ${styles[status] || 'badge-secondary'}`}>
                <span className="d-flex align-items-center gap-1">
                    <Icon size={12} />
                    {label}
                </span>
            </span>
        );
    };

    const getLeaveTypeLabel = (type) => {
        const types = {
            annual: t('hr.leaves.type_annual'),
            sick: t('hr.leaves.type_sick'),
            unpaid: t('hr.leaves.type_unpaid'),
            emergency: t('hr.leaves.type_emergency')
        };
        return types[type] || type;
    };

    // Calculate Stats
    const totalRequests = leaves.length;
    const pendingRequests = leaves.filter(l => l.status === 'pending').length;
    const approvedRequests = leaves.filter(l => l.status === 'approved').length;

    const filteredLeaves = leaves.filter(l => filter === 'all' || l.status === filter);
    const { currentPage, pageSize, totalItems, paginatedItems, onPageChange, onPageSizeChange } = usePagination(filteredLeaves);

    return (
        <div className="workspace fade-in">
            {/* Header */}
            <div className="workspace-header">
                <BackButton />
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
                    <div className="d-flex align-items-center gap-4">
                        <div>
                            <h1 className="workspace-title">{t('hr.leaves.title')}</h1>
                            <p className="workspace-subtitle">{t('hr.leaves.subtitle')}</p>
                        </div>
                        {/* Filters moved next to title (Right in RTL) */}
                        <div className="btn-group">
                            <button className={`btn btn-sm ${filter === 'all' ? 'btn-secondary' : 'btn-outline-secondary'}`} onClick={() => setFilter('all')}>{t('common.all')}</button>
                            <button className={`btn btn-sm ${filter === 'pending' ? 'btn-warning' : 'btn-outline-secondary'}`} onClick={() => setFilter('pending')}>{t('status.pending')}</button>
                        </div>
                    </div>

                    <button
                        onClick={() => setIsModalOpen(true)}
                        className="btn btn-primary"
                    >
                        <Plus size={18} className="me-2" />
                        {t('hr.leaves.request')}
                    </button>
                </div>
            </div>

            {/* Metrics Section */}
            <div className="metrics-grid mb-4">
                <div className="metric-card">
                    <div className="metric-label">{t('common.count', 'Total Requests')}</div>
                    <div className="metric-value text-primary">
                        {hasPermission('hr.reports') ? totalRequests : '***'}
                    </div>
                </div>
                <div className="metric-card">
                    <div className="metric-label">{t('status.pending', 'Pending')}</div>
                    <div className="metric-value text-warning">
                        {hasPermission('hr.reports') ? pendingRequests : '***'}
                    </div>
                </div>
                <div className="metric-card">
                    <div className="metric-label">{t('status.approved', 'Approved')}</div>
                    <div className="metric-value text-success">
                        {hasPermission('hr.reports') ? approvedRequests : '***'}
                    </div>
                </div>
            </div>

            {/* Content Table */}
            <div className="data-table-container">
                <table className="data-table">
                    <thead>
                        <tr>
                            <th style={{ width: '25%' }}>{t('hr.leaves.employee')}</th>
                            <th style={{ width: '15%' }}>{t('hr.leaves.type')}</th>
                            <th style={{ width: '20%' }}>{t('hr.leaves.period')}</th>
                            <th className="text-center" style={{ width: '10%' }}>{t('hr.leaves.duration')}</th>
                            <th style={{ width: '20%' }}>{t('hr.leaves.reason')}</th>
                            <th>{t('common.status')}</th>
                            <th style={{ width: '10%' }}>{t('common.created_at')}</th>
                            {canManageLeaves && <th className="text-end">{t('common.actions')}</th>}
                        </tr>
                    </thead>
                    <tbody>
                        {loading ? (
                            <tr><td colSpan="8" className="text-center py-5"><div className="spinner-border text-primary"></div></td></tr>
                        ) : filteredLeaves.length === 0 ? (
                            <tr>
                                <td colSpan="8" className="start-guide">
                                    <div style={{ padding: '60px 20px', textAlign: 'center' }}>
                                        <div style={{ fontSize: '48px', marginBottom: '16px' }}>📝</div>
                                        <h3 style={{ fontSize: '18px', marginBottom: '8px' }}>{t('common.no_data')}</h3>
                                        <button className="btn btn-primary" onClick={() => setIsModalOpen(true)}>
                                            {t('hr.leaves.request')}
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        ) : (
                            paginatedItems.map((leave) => {
                                const start = new Date(leave.start_date);
                                const end = new Date(leave.end_date);
                                const duration = Math.ceil((end - start) / (1000 * 60 * 60 * 24)) + 1;

                                return (
                                    <tr key={leave.id}>
                                        <td>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                                                <div className="avatar-xs" style={{ background: '#eff6ff', color: 'var(--primary)', fontWeight: 'bold' }}>
                                                    {leave.employee_name?.charAt(0).toUpperCase() || 'U'}
                                                </div>
                                                <span style={{ fontWeight: '600', color: 'var(--text-primary)' }}>{leave.employee_name || t('common.me')}</span>
                                            </div>
                                        </td>
                                        <td><span style={{ color: 'var(--text-primary)' }}>{getLeaveTypeLabel(leave.leave_type)}</span></td>
                                        <td>
                                            <div style={{ display: 'flex', flexDirection: 'column' }}>
                                                <span style={{ fontWeight: '500', color: 'var(--text-primary)' }}>{formatShortDate(leave.start_date)}</span>
                                                <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{t('common.to')} {formatShortDate(leave.end_date)}</span>
                                            </div>
                                        </td>
                                        <td className="text-center"><span className="badge" style={{ background: '#f1f5f9', color: 'var(--text-secondary)' }}>{duration} {t('common.days')}</span></td>
                                        <td className="text-truncate" style={{ maxWidth: '150px', color: 'var(--text-secondary)' }} title={leave.reason}>{leave.reason || '-'}</td>
                                        <td>{getStatusBadge(leave.status)}</td>
                                        <td><span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>{formatShortDate(leave.created_at)}</span></td>
                                        {canManageLeaves && (
                                            <td className="text-end">
                                                {leave.status === 'pending' && (
                                                    <div className="btn-group">
                                                        <button
                                                            onClick={() => handleStatusUpdate(leave.id, 'approved')}
                                                            className="table-action-btn text-success"
                                                            title={t('common.approve')}
                                                        >
                                                            <Check size={16} />
                                                        </button>
                                                        <button
                                                            onClick={() => handleStatusUpdate(leave.id, 'rejected')}
                                                            className="table-action-btn text-danger"
                                                            title={t('common.reject')}
                                                        >
                                                            <X size={16} />
                                                        </button>
                                                    </div>
                                                )}
                                            </td>
                                        )}
                                    </tr>
                                );
                            })
                        )}
                    </tbody>
                </table>
                <Pagination currentPage={currentPage} totalItems={totalItems} pageSize={pageSize} onPageChange={onPageChange} onPageSizeChange={onPageSizeChange} />
            </div>

            {/* Create Modal */}
            <SimpleModal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                title={t('hr.leaves.request')}
                footer={
                    <>
                        <button className="btn btn-secondary" onClick={() => setIsModalOpen(false)}>
                            {t('common.cancel')}
                        </button>
                        <button className="btn btn-primary" onClick={handleCreate} disabled={actionLoading}>
                            {actionLoading ? t('common.saving') : t('common.submit')}
                        </button>
                    </>
                }
            >
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    <div className="form-group">
                        <label className="form-label">{t('hr.leaves.type')}</label>
                        <select
                            className="form-input"
                            value={formData.leave_type}
                            onChange={(e) => setFormData({ ...formData, leave_type: e.target.value })}
                            required
                        >
                            <option value="annual">{t('hr.leaves.type_annual')}</option>
                            <option value="sick">{t('hr.leaves.type_sick')}</option>
                            <option value="emergency">{t('hr.leaves.type_emergency')}</option>
                            <option value="unpaid">{t('hr.leaves.type_unpaid')}</option>
                        </select>
                    </div>
                    <div style={{ display: 'flex', gap: '16px' }}>
                        <div className="form-group" style={{ flex: 1 }}>
                            <label className="form-label">{t('hr.leaves.start_date')}</label>
                            <input
                               
                                className="form-input"
                                value={formData.start_date}
                                onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                                required
                                style={{ direction: 'ltr' }}
                            />
                        </div>
                        <div className="form-group" style={{ flex: 1 }}>
                            <label className="form-label">{t('hr.leaves.end_date')}</label>
                            <input
                               
                                className="form-input"
                                value={formData.end_date}
                                onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                                required
                                style={{ direction: 'ltr' }}
                            />
                        </div>
                    </div>
                    <div className="form-group">
                        <label className="form-label">{t('hr.leaves.reason')}</label>
                        <textarea
                            className="form-input"
                            rows="3"
                            value={formData.reason}
                            onChange={(e) => setFormData({ ...formData, reason: e.target.value })}
                            placeholder={t('common.notes', 'Notes')}
                        ></textarea>
                    </div>
                </div>
            </SimpleModal>
        </div>
    );
};

export default LeaveList;
