
import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Plus, Calendar, DollarSign, Eye, CheckCircle } from 'lucide-react';
import { hrAPI } from '../../utils/api';
import { Link, useNavigate } from 'react-router-dom';
import { getCurrency, hasPermission } from '../../utils/auth';
import { formatShortDate } from '../../utils/dateUtils';
import { formatNumber } from '../../utils/format';
import { toastEmitter } from '../../utils/toastEmitter';
import Pagination, { usePagination } from '../../components/common/Pagination';

import DateInput from '../../components/common/DateInput';
import BackButton from '../../components/common/BackButton';
const PayrollList = () => {
    const { t } = useTranslation();
    const navigate = useNavigate();
    const currency = getCurrency();
    const [periods, setPeriods] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const { currentPage, pageSize, totalItems, paginatedItems, onPageChange, onPageSizeChange } = usePagination(periods);

    // New Period Form
    const [formData, setFormData] = useState({
        name: '',
        start_date: '',
        end_date: '',
        payment_date: ''
    });

    useEffect(() => {
        fetchPeriods();
    }, []);

    const fetchPeriods = async () => {
        try {
            const res = await hrAPI.listPayrollPeriods();
            setPeriods(res.data);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            await hrAPI.createPayrollPeriod(formData);
            setShowModal(false);
            fetchPeriods();
            setFormData({ name: '', start_date: '', end_date: '', payment_date: '' });
        } catch (err) {
            toastEmitter.emit("Error creating period: " + (err.response?.data?.detail || err.message), 'error');
        }
    };

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <div className="header-title">
                    <h1 className="workspace-title">{t("hr.payroll.title")}</h1>
                    <p className="workspace-subtitle">{t("hr.payroll.subtitle")}</p>
                </div>
                <div className="header-actions">
                    {hasPermission('hr.manage') && (
                        <button className="btn btn-primary" onClick={() => setShowModal(true)}>
                            <Plus size={18} className="ms-2" />
                            {t('hr.payroll.new_period')}
                        </button>
                    )}
                </div>
            </div>

            <div className="data-table-container">
                <table className="data-table">
                    <thead>
                        <tr>
                            <th>{t("hr.payroll.period_name")}</th>
                            <th>{t("hr.payroll.start_date")}</th>
                            <th>{t("hr.payroll.end_date")}</th>
                            <th>{t("common.status")}</th>
                            <th>{t("hr.payroll.total_salaries")}</th>
                            <th>{t("common.actions")}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {loading ? (
                            <tr><td colSpan="6" className="text-center p-4">{t("common.loading")}</td></tr>
                        ) : periods.length === 0 ? (
                            <tr>
                                <td colSpan="6" className="text-center p-5">
                                    <div className="text-muted mb-3" style={{ fontSize: '40px' }}>📅</div>
                                    <p>{t("hr.payroll.no_periods")}</p>
                                    {hasPermission('hr.manage') && (
                                        <button className="btn btn-outline-primary btn-sm" onClick={() => setShowModal(true)}>
                                            {t('hr.payroll.create_first')}
                                        </button>
                                    )}
                                </td>
                            </tr>
                        ) : (
                            paginatedItems.map(period => (
                                <tr key={period.id} className="hover-row">
                                    <td className="fw-bold">{period.name}</td>
                                    <td>{formatShortDate(period.start_date)}</td>
                                    <td>{formatShortDate(period.end_date)}</td>
                                    <td>
                                        <span className={`status-badge status-${period.status === 'posted' ? 'active' : 'draft'}`}>
                                            {period.status === 'posted' ? t('common.posted') : t('common.draft')}
                                        </span>
                                    </td>
                                    <td className="fw-bold text-primary">
                                        {formatNumber(period.total_net)} {currency}
                                    </td>
                                    <td>
                                        <button
                                            className="btn btn-sm btn-outline-primary"
                                            onClick={() => navigate(`/hr/payroll/${period.id}`)}
                                        >
                                            <Eye size={14} className="ms-1" />
                                            {t('common.view_details')}
                                        </button>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
                <Pagination currentPage={currentPage} totalItems={totalItems} pageSize={pageSize} onPageChange={onPageChange} onPageSizeChange={onPageSizeChange} />
            </div>

            {/* Create Modal */}
            {showModal && (
                <div className="modal-overlay">
                    <div className="modal-content" style={{ maxWidth: '500px' }}>
                        <div className="modal-header">
                            <h3 className="modal-title">{t("hr.payroll.create_new")}</h3>
                            <button className="btn-icon" onClick={() => setShowModal(false)}>×</button>
                        </div>
                        <form onSubmit={handleSubmit}>
                            <div className="modal-body">
                                <div className="mb-3">
                                    <label className="form-label">{t("hr.payroll.period_name")}</label>
                                    <input
                                        type="text"
                                        className="form-input"
                                        placeholder={t("hr.payroll.name_placeholder")}
                                        required
                                        value={formData.name}
                                        onChange={e => setFormData({ ...formData, name: e.target.value })}
                                    />
                                </div>
                                <div className="row g-2">
                                    <div className="col-6 mb-3">
                                        <label className="form-label">{t("hr.payroll.start_date")}</label>
                                        <input
                                           
                                            className="form-input"
                                            required
                                            value={formData.start_date}
                                            onChange={e => setFormData({ ...formData, start_date: e.target.value })}
                                            style={{ direction: 'ltr' }}
                                        />
                                    </div>
                                    <div className="col-6 mb-3">
                                        <label className="form-label">{t("hr.payroll.end_date")}</label>
                                        <input
                                           
                                            className="form-input"
                                            required
                                            value={formData.end_date}
                                            onChange={e => setFormData({ ...formData, end_date: e.target.value })}
                                            style={{ direction: 'ltr' }}
                                        />
                                    </div>
                                </div>
                                <div className="mb-3">
                                    <label className="form-label">{t("hr.payroll.payment_date")}</label>
                                    <input
                                       
                                        className="form-input"
                                        value={formData.payment_date}
                                        onChange={e => setFormData({ ...formData, payment_date: e.target.value })}
                                        style={{ direction: 'ltr' }}
                                    />
                                </div>
                            </div>
                            <div className="modal-footer">
                                <button type="button" className="btn btn-outline-secondary" onClick={() => setShowModal(false)}>{t("common.cancel")}</button>
                                <button type="submit" className="btn btn-primary">{t("common.save")}</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default PayrollList;
