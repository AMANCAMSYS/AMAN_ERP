import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { scheduledReportsAPI, branchesAPI } from '../../utils/api';
import { useToast } from '../../context/ToastContext';

const ScheduledReports = () => {
    const { t } = useTranslation();
    const { showToast } = useToast();
    const [reports, setReports] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [branches, setBranches] = useState([]);

    // Form State
    const [formData, setFormData] = useState({
        report_type: 'profit_loss',
        frequency: 'monthly',
        recipients: '',
        format: 'pdf',
        branch_id: ''
    });

    useEffect(() => {
        fetchReports();
        fetchBranches();
    }, []);

    const fetchReports = async () => {
        try {
            setLoading(true);
            const response = await scheduledReportsAPI.list();
            setReports(response.data);
        } catch (error) {
            console.error("Failed to fetch scheduled reports", error);
            showToast(t('common.error_loading'), 'error');
        } finally {
            setLoading(false);
        }
    };

    const fetchBranches = async () => {
        try {
            const response = await branchesAPI.list();
            setBranches(response.data);
        } catch (error) {
            console.error("Failed to fetch branches", error);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            await scheduledReportsAPI.create({
                ...formData,
                branch_id: formData.branch_id || null
            });
            showToast(t('common.success_create'), 'success');
            setShowModal(false);
            setFormData({
                report_type: 'profit_loss',
                frequency: 'monthly',
                recipients: '',
                format: 'pdf',
                branch_id: ''
            });
            fetchReports();
        } catch (error) {
            console.error("Failed to create schedule", error);
            showToast(t('common.error_create'), 'error');
        }
    };

    const handleDelete = async (id) => {
        if (!window.confirm(t('common.confirm_delete'))) return;
        try {
            await scheduledReportsAPI.delete(id);
            showToast(t('common.success_delete'), 'success');
            fetchReports();
        } catch (error) {
            showToast(t('common.error_delete'), 'error');
        }
    };

    const handleToggle = async (id, currentStatus) => {
        try {
            await scheduledReportsAPI.toggle(id, !currentStatus);
            fetchReports();
        } catch (error) {
            showToast(t('common.error_update'), 'error');
        }
    };

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <div className="header-title">
                    <h1 className="workspace-title">⏰ {t('reports.scheduled.title', 'Scheduled Reports')}</h1>
                    <p className="workspace-subtitle">{t('reports.scheduled.subtitle', 'Manage automated report generation and emailing')}</p>
                </div>
                <div className="header-actions">
                    <button className="btn btn-primary" onClick={() => setShowModal(true)}>
                        + {t('reports.scheduled.new', 'New Schedule')}
                    </button>
                </div>
            </div>

            <div className="table-container">
                <table className="data-table">
                    <thead>
                        <tr>
                            <th>{t('reports.scheduled.report_type', 'Report Type')}</th>
                            <th>{t('reports.scheduled.frequency', 'Frequency')}</th>
                            <th>{t('reports.scheduled.recipients', 'Recipients')}</th>
                            <th>{t('reports.scheduled.branch', 'Branch')}</th>
                            <th>{t('reports.scheduled.next_run', 'Next Run')}</th>
                            <th>{t('reports.scheduled.status', 'Status')}</th>
                            <th>{t('common.actions', 'Actions')}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {loading ? (
                            <tr><td colSpan="7" className="text-center">{t('common.loading')}</td></tr>
                        ) : reports.length === 0 ? (
                            <tr><td colSpan="7" className="text-center">{t('common.no_data')}</td></tr>
                        ) : (
                            reports.map(report => (
                                <tr key={report.id}>
                                    <td>
                                        {report.report_type === 'profit_loss' ? t('reports.profit_loss', 'Profit & Loss') : t('reports.balance_sheet', 'Balance Sheet')}
                                        <span className="badge badge-secondary ms-2">{report.format.toUpperCase()}</span>
                                    </td>
                                    <td>{t(`reports.frequency.${report.frequency}`, report.frequency)}</td>
                                    <td><div className="text-truncate" style={{ maxWidth: '200px' }} title={report.recipients}>{report.recipients}</div></td>
                                    <td>{report.branch_name || t('common.all_branches', 'All Branches')}</td>
                                    <td>{report.next_run_at ? new Date(report.next_run_at).toLocaleString() : '-'}</td>
                                    <td>
                                        <div className="form-check form-switch">
                                            <input
                                                className="form-check-input"
                                                type="checkbox"
                                                checked={report.is_active}
                                                onChange={() => handleToggle(report.id, report.is_active)}
                                            />
                                        </div>
                                    </td>
                                    <td>
                                        <button className="btn-icon text-danger" onClick={() => handleDelete(report.id)}>
                                            🗑️
                                        </button>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            {/* Modal */}
            {showModal && (
                <div className="modal-overlay">
                    <div className="modal-content">
                        <div className="modal-header">
                            <h3>{t('reports.scheduled.new', 'New Schedule')}</h3>
                            <button className="btn-close" onClick={() => setShowModal(false)}>×</button>
                        </div>
                        <form onSubmit={handleSubmit}>
                            <div className="modal-body">
                                <div className="form-group">
                                    <label>{t('reports.scheduled.report_type', 'Report Type')}</label>
                                    <select
                                        className="form-input"
                                        value={formData.report_type}
                                        onChange={e => setFormData({ ...formData, report_type: e.target.value })}
                                    >
                                        <option value="profit_loss">{t('reports.profit_loss', 'Profit & Loss')}</option>
                                        <option value="balance_sheet">{t('reports.balance_sheet', 'Balance Sheet')}</option>
                                    </select>
                                </div>

                                <div className="form-group">
                                    <label>{t('reports.scheduled.frequency', 'Frequency')}</label>
                                    <select
                                        className="form-input"
                                        value={formData.frequency}
                                        onChange={e => setFormData({ ...formData, frequency: e.target.value })}
                                    >
                                        <option value="daily">{t('reports.frequency.daily', 'Daily')}</option>
                                        <option value="weekly">{t('reports.frequency.weekly', 'Weekly')}</option>
                                        <option value="monthly">{t('reports.frequency.monthly', 'Monthly')}</option>
                                    </select>
                                </div>

                                <div className="form-group">
                                    <label>{t('reports.scheduled.format', 'Format')}</label>
                                    <select
                                        className="form-input"
                                        value={formData.format}
                                        onChange={e => setFormData({ ...formData, format: e.target.value })}
                                    >
                                        <option value="pdf">PDF</option>
                                        <option value="excel">Excel</option>
                                    </select>
                                </div>

                                <div className="form-group">
                                    <label>{t('reports.scheduled.branch', 'Branch')}</label>
                                    <select
                                        className="form-input"
                                        value={formData.branch_id}
                                        onChange={e => setFormData({ ...formData, branch_id: e.target.value })}
                                    >
                                        <option value="">{t('common.all_branches', 'All Branches')}</option>
                                        {branches.map(b => (
                                            <option key={b.id} value={b.id}>{b.branch_name}</option>
                                        ))}
                                    </select>
                                </div>

                                <div className="form-group">
                                    <label>{t('reports.scheduled.recipients', 'Recipients (comma separated emails)')}</label>
                                    <textarea
                                        className="form-input"
                                        rows="3"
                                        required
                                        value={formData.recipients}
                                        onChange={e => setFormData({ ...formData, recipients: e.target.value })}
                                        placeholder="email1@example.com, email2@example.com"
                                    />
                                </div>
                            </div>
                            <div className="modal-footer">
                                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>
                                    {t('common.cancel')}
                                </button>
                                <button type="submit" className="btn btn-primary">
                                    {t('common.save')}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ScheduledReports;
