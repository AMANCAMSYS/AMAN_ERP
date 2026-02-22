
import React, { useState, useEffect } from 'react';
import { hrAPI } from '../../utils/api';
import { useTranslation } from 'react-i18next';
import { Plus, Check, X, DollarSign } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useBranch } from '../../context/BranchContext';
import { toast } from 'react-hot-toast';
import { hasPermission } from '../../utils/auth';
import { formatShortDate } from '../../utils/dateUtils';
import { formatNumber } from '../../utils/format';
import Pagination, { usePagination } from '../../components/common/Pagination';

import DateInput from '../../components/common/DateInput';
import BackButton from '../../components/common/BackButton';
const LoanList = () => {
    const { t, i18n } = useTranslation();
    const navigate = useNavigate();
    const isRTL = i18n.language === 'ar';
    const { currentBranch } = useBranch();
    const [loans, setLoans] = useState([]);
    const [employees, setEmployees] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [actionLoading, setActionLoading] = useState(false);
    const { currentPage, pageSize, totalItems, paginatedItems, onPageChange, onPageSizeChange } = usePagination(loans);

    // Permissions
    const canManageLoans = hasPermission('hr.loans.manage');
    const canViewLoans = hasPermission('hr.loans.view');

    // ... (state)

    useEffect(() => {
        if (!canViewLoans) {
            toast.error(t('common.unauthorized'));
            navigate('/hr');
            return;
        }
        fetchData();
    }, []);
    const [formData, setFormData] = useState({
        employee_id: '',
        amount: '',
        total_installments: '6',
        start_date: new Date().toISOString().split('T')[0],
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
            const [loansRes, employeesRes] = await Promise.all([
                hrAPI.listLoans(params),
                hrAPI.listEmployees(params)
            ]);
            setLoans(Array.isArray(loansRes.data) ? loansRes.data : loansRes || []);
            setEmployees(Array.isArray(employeesRes.data) ? employeesRes.data : employeesRes || []);
        } catch (error) {
            console.error('Error fetching data:', error);
            const detail = error.response?.data?.detail;
            if (detail) toast.error(detail);
        } finally {
            setLoading(false);
        }
    };

    const handleCreate = async (e) => {
        e.preventDefault();
        setActionLoading(true);
        try {
            await hrAPI.createLoan(formData);
            toast.success(t('hr.loans.save_success'));
            setIsModalOpen(false);
            fetchData();
            setFormData({ ...formData, amount: '', reason: '' });
        } catch (error) {
            toast.error(error.response?.data?.detail || error.message);
        } finally {
            setActionLoading(false);
        }
    };

    const handleApprove = async (id) => {
        if (!window.confirm(t('common.confirm_delete') || 'Are you sure?')) return;
        try {
            await hrAPI.approveLoan(id);
            toast.success(t('hr.loans.approve_success'));
            fetchData();
        } catch (error) {
            toast.error(error.response?.data?.detail || error.message);
        }
    };

    const getStatusBadge = (status) => {
        switch (status) {
            case 'active': return <span className="badge bg-success-light text-success">{t('hr.loans.active')}</span>;
            case 'completed': return <span className="badge bg-primary-light text-primary">{t('hr.loans.completed')}</span>;
            case 'pending': return <span className="badge bg-warning-light text-warning">{t('hr.loans.pending')}</span>;
            case 'rejected': return <span className="badge bg-danger-light text-danger">{t('hr.loans.rejected')}</span>;
            default: return <span className="badge bg-light text-muted">{status}</span>;
        }
    };

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <div className="header-title">
                    <h1 className="workspace-title">
                        <DollarSign size={24} className="me-2 text-primary" />
                        {t('hr.loans.title')}
                    </h1>
                    <p className="workspace-subtitle">{t('hr.loans.subtitle')}</p>
                </div>
                <div className="header-actions">
                    {canManageLoans && (
                        <button
                            onClick={() => setIsModalOpen(true)}
                            className="btn btn-primary shadow-sm"
                        >
                            <Plus size={18} className="me-2" />
                            {t('hr.loans.add')}
                        </button>
                    )}
                </div>
            </div>

            <div className="card shadow-sm border-0 overflow-hidden">
                <div className="card-body p-0">
                    <div className="data-table-container">
                        <table className="data-table mb-0 w-100">
                            <thead>
                                <tr>
                                    <th>{t('hr.loans.employee')}</th>
                                    <th>{t('hr.loans.amount')}</th>
                                    <th>{t('hr.loans.paid')}</th>
                                    <th>{t('hr.loans.remaining')}</th>
                                    <th>{t('hr.loans.installment')}</th>
                                    <th>{t('hr.loans.status')}</th>
                                    <th>{t('hr.loans.start_date')}</th>
                                    <th style={{ width: '120px' }}>{t('common.actions')}</th>
                                </tr>
                            </thead>
                            <tbody>
                                {loading ? (
                                    <tr><td colSpan="8" className="text-center p-5"><div className="spinner-border text-primary"></div></td></tr>
                                ) : loans.length > 0 ? (
                                    paginatedItems.map((loan) => (
                                        <tr key={loan.id} className="hover-row">
                                            <td className="fw-bold">{loan.employee_name}</td>
                                            <td>{formatNumber(loan.amount)}</td>
                                            <td className="text-success">{formatNumber(loan.paid_amount)}</td>
                                            <td className="text-danger">{formatNumber(loan.amount - loan.paid_amount)}</td>
                                            <td>{formatNumber(loan.monthly_installment)}</td>
                                            <td>{getStatusBadge(loan.status)}</td>
                                            <td className="text-muted small">{formatShortDate(loan.start_date)}</td>
                                            <td>
                                                {loan.status === 'pending' && canManageLoans && (
                                                    <button
                                                        onClick={() => handleApprove(loan.id)}
                                                        className="btn btn-icon text-success hover-bg-success-light"
                                                        title={t('hr.loans.approve')}
                                                    >
                                                        <Check size={18} />
                                                    </button>
                                                )}
                                            </td>
                                        </tr>
                                    ))
                                ) : (
                                    <tr>
                                        <td colSpan="8" className="p-5 text-center text-muted">
                                            <div className="mb-3"><DollarSign size={48} className="text-light" /></div>
                                            <p>{t('common.no_records_found')}</p>
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                        <Pagination currentPage={currentPage} totalItems={totalItems} pageSize={pageSize} onPageChange={onPageChange} onPageSizeChange={onPageSizeChange} />
                    </div>
                </div>
            </div>

            {/* Create Modal */}}
            {isModalOpen && (
                <div className="modal-overlay">
                    <div className="modal-content" style={{ maxWidth: '500px' }}>
                        <div className="modal-header">
                            <h3 className="modal-title">{t('hr.loans.form_title')}</h3>
                            <button className="btn-icon" onClick={() => setIsModalOpen(false)}><X size={20} /></button>
                        </div>
                        <form onSubmit={handleCreate}>
                            <div className="modal-body">
                                <div className="mb-3">
                                    <label className="form-label">{t('hr.loans.employee')}</label>
                                    <select
                                        className="form-input"
                                        value={formData.employee_id}
                                        onChange={(e) => setFormData({ ...formData, employee_id: e.target.value })}
                                        required
                                    >
                                        <option value="">-- {t('common.select')} --</option>
                                        {employees.map(emp => (
                                            <option key={emp.id} value={emp.id}>{emp.first_name} {emp.last_name}</option>
                                        ))}
                                    </select>
                                </div>

                                <div className="row g-3 mb-3">
                                    <div className="col-md-6">
                                        <label className="form-label">{t('hr.loans.amount_required')}</label>
                                        <input
                                            type="number"
                                            className="form-input"
                                            value={formData.amount}
                                            onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                                            required
                                        />
                                    </div>
                                    <div className="col-md-6">
                                        <label className="form-label">{t('hr.loans.installments')}</label>
                                        <input
                                            type="number"
                                            className="form-input"
                                            value={formData.total_installments}
                                            onChange={(e) => setFormData({ ...formData, total_installments: e.target.value })}
                                            required
                                            min="1"
                                        />
                                    </div>
                                </div>

                                <div className="mb-3">
                                    <label className="form-label">{t('hr.loans.start_date')}</label>
                                    <input
                                       
                                        className="form-input"
                                        value={formData.start_date}
                                        onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                                        required
                                        style={{ direction: 'ltr' }}
                                    />
                                    <div className="form-text small text-muted mt-1">{t('hr.loans.start_date_help')}</div>
                                </div>

                                <div>
                                    <label className="form-label">{t('hr.loans.reason')}</label>
                                    <textarea
                                        className="form-input"
                                        rows="3"
                                        value={formData.reason}
                                        onChange={(e) => setFormData({ ...formData, reason: e.target.value })}
                                        placeholder={t('hr.loans.reason')}
                                    />
                                </div>
                            </div>

                            <div className="modal-footer">
                                <button type="button" className="btn btn-outline-secondary" onClick={() => setIsModalOpen(false)}>
                                    {t('common.cancel')}
                                </button>
                                <button type="submit" className="btn btn-primary px-4" disabled={actionLoading}>
                                    {actionLoading ? t('common.processing') : t('common.save')}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default LoanList;
