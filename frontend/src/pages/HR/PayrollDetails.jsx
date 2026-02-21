import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useParams, useNavigate } from 'react-router-dom';
import {
    Calculator, CheckCircle, ArrowLeft, Printer, RefreshCw,
    AlertTriangle, DollarSign, Wallet, Users, FileText
} from 'lucide-react';
import { hrAPI } from '../../utils/api';
import { getCurrency, hasPermission } from '../../utils/auth';
import { formatNumber } from '../../utils/format';
import { useBranch } from '../../context/BranchContext';
import { toastEmitter } from '../../utils/toastEmitter';
import '../../components/ModuleStyles.css';

const PayrollDetails = () => {
    const { t, i18n } = useTranslation();
    const { id } = useParams();
    const navigate = useNavigate();
    const currency = getCurrency();
    const { currentBranch } = useBranch();
    const [period, setPeriod] = useState(null);
    const [entries, setEntries] = useState([]);
    const [loading, setLoading] = useState(true);
    const [processing, setProcessing] = useState(false);

    useEffect(() => {
        fetchData();
    }, [id, currentBranch]);

    const fetchData = async () => {
        setLoading(true);
        try {
            const params = {};
            if (currentBranch?.id) {
                params.branch_id = currentBranch.id;
            }

            // Always fetch period
            const pRes = await hrAPI.getPayrollPeriod(id);
            setPeriod(pRes.data);

            // Only fetch entries if user can manage or view reports
            if (hasPermission('hr.manage') || hasPermission('hr.reports')) {
                const eRes = await hrAPI.getPayrollEntries(id, params);
                setEntries(eRes.data);
            }
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleGenerate = async () => {
        if (!window.confirm(t('hr.payroll.confirm_generate', "This will recalculate salaries for all active employees. Are you sure?"))) return;

        setProcessing(true);
        try {
            await hrAPI.generatePayroll(id);
            await fetchData(); // Reload
        } catch (err) {
            toastEmitter.emit(t('common.error', 'Error') + ": " + (err.response?.data?.detail || err.message), 'error');
        } finally {
            setProcessing(false);
        }
    };

    const handlePost = async () => {
        if (!window.confirm(t('hr.payroll.confirm_post', "This will post the payroll and create journal entries. This cannot be undone. Are you sure?"))) return;

        setProcessing(true);
        try {
            await hrAPI.postPayroll(id);
            await fetchData(); // Reload status
        } catch (err) {
            toastEmitter.emit(t('common.error', 'Error') + ": " + (err.response?.data?.detail || err.message), 'error');
        } finally {
            setProcessing(false);
        }
    };

    if (loading) return <div className="page-center"><span className="loading"></span></div>;
    if (!period) return <div className="page-center text-error">{t('hr.payroll.period_not_found', 'Payroll period not found')}</div>;

    const isDraft = period.status === 'draft';
    const isRTL = i18n.language === 'ar';

    return (
        <div className="workspace fade-in">
            {/* Header */}
            <div className="workspace-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                    <button className="btn-icon" onClick={() => navigate('/hr/payroll')}>
                        {isRTL ? <ArrowLeft size={20} style={{ transform: 'rotate(180deg)' }} /> : <ArrowLeft size={20} />}
                    </button>
                    <div>
                        <h1 className="workspace-title">{period.name}</h1>
                        <div className="workspace-subtitle">
                            <span>{period.start_date}</span>
                            <span className="mx-2">{t('common.to')}</span>
                            <span>{period.end_date}</span>
                        </div>
                    </div>
                </div>

                <div className="action-buttons gap-2" style={{ display: 'flex', alignItems: 'center', marginTop: '16px' }}>
                    {/* Status Badge */}
                    <span className={`badge border ${isDraft ? 'bg-warning-subtle text-warning border-warning-subtle' : 'bg-success-subtle text-success border-success-subtle'} px-3 py-2 d-flex align-items-center gap-2`}>
                        <span className={`spinner-grow spinner-grow-sm ${isDraft ? 'text-warning' : 'd-none'}`} role="status" aria-hidden="true"></span>
                        {isDraft ? t('common.status.draft', 'Draft') : t('common.status.posted', 'Posted')}
                    </span>

                    {isDraft && (
                        <>
                            <button
                                className="btn btn-primary"
                                onClick={handleGenerate}
                                disabled={processing}
                            >
                                <RefreshCw size={18} className={`me-2 ${processing ? 'spin' : ''}`} />
                                {entries.length > 0 ? t('hr.payroll.recalculate', 'Recalculate') : t('hr.payroll.generate', 'Generate Payroll')}
                            </button>

                            {entries.length > 0 && (
                                <button
                                    className="btn btn-success text-white"
                                    onClick={handlePost}
                                    disabled={processing}
                                >
                                    <CheckCircle size={18} className="me-2" />
                                    {t('hr.payroll.post', 'Post & Finalize')}
                                </button>
                            )}
                        </>
                    )}

                    {!isDraft && (
                        <button className="btn btn-secondary" onClick={() => window.print()}>
                            <Printer size={18} className="me-2" />
                            {t('common.print', 'Print')}
                        </button>
                    )}
                </div>
            </div>

            {/* Metrics Section (Consistent with ModuleStyles) */}
            <div className="metrics-grid mb-4">
                <div className="metric-card">
                    <div className="metric-label">{t('hr.payroll.total_net', 'Total Net Salary')}</div>
                    <div className="metric-value text-primary">
                        {hasPermission('hr.reports') ? formatNumber(entries.reduce((sum, e) => sum + (e.net_salary || 0), 0)) : '***'}
                        {hasPermission('hr.reports') && <small>{currency}</small>}
                    </div>
                </div>
                <div className="metric-card">
                    <div className="metric-label">{t('hr.payroll.employees_count', 'Employees')}</div>
                    <div className="metric-value text-dark">
                        {hasPermission('hr.reports') ? entries.length : '***'}
                    </div>
                </div>
                <div className="metric-card">
                    <div className="metric-label">{t('common.status')}</div>
                    <div className={`metric-value ${isDraft ? 'text-warning' : 'text-success'} fs-4`}>{isDraft ? t('status.draft') : t('status.posted')}</div>
                </div>
            </div>

            {/* Entries Table */}
            <div className="card shadow-sm border-0 section-card">
                <h3 className="section-title">{t('hr.payroll.entries', 'Payroll Entries')}</h3>
                <div className="data-table-container">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>{t('hr.employees.name', 'Employee')}</th>
                                <th>{t('hr.employees.position', 'Position')}</th>
                                <th>{t('hr.payroll.basic', 'Basic')}</th>
                                <th>{t('hr.payroll.housing', 'Housing')}</th>
                                <th>{t('hr.payroll.transport', 'Transport')}</th>
                                <th>{t('hr.payroll.other', 'Other')}</th>
                                <th className="text-danger">{t('hr.payroll.deductions', 'Deductions')}</th>
                                <th className="fw-bold">{t('hr.payroll.net', 'Net Salary')}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {entries.length === 0 ? (
                                <tr>
                                    <td colSpan="8" className="start-guide">
                                        <div style={{ padding: '60px 20px', textAlign: 'center' }}>
                                            <div style={{ fontSize: '48px', marginBottom: '16px' }}>💸</div>
                                            <h3 style={{ fontSize: '18px', marginBottom: '8px' }}>{t('hr.payroll.no_entries', 'No payroll entries yet')}</h3>
                                            <p className="text-muted mb-3">{t('hr.payroll.generate_hint', 'Click "Generate Payroll" to calculate salaries.')}</p>
                                            <button className="btn btn-primary" onClick={handleGenerate} disabled={processing}>
                                                <RefreshCw size={18} className={`me-2 ${processing ? 'spin' : ''}`} />
                                                {t('hr.payroll.generate', 'Generate Payroll')}
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ) : (
                                <>
                                    {entries.map(entry => (
                                        <tr key={entry.id}>
                                            <td className="fw-medium text-dark">{entry.employee_name}</td>
                                            <td className="text-muted small">{entry.position || '-'}</td>
                                            <td className="text-muted">{!hasPermission('hr.reports') ? '***' : formatNumber(entry.basic_salary)}</td>
                                            <td className="text-muted">{!hasPermission('hr.reports') ? '***' : formatNumber(entry.housing_allowance)}</td>
                                            <td className="text-muted">{!hasPermission('hr.reports') ? '***' : formatNumber(entry.transport_allowance)}</td>
                                            <td className="text-muted">{!hasPermission('hr.reports') ? '***' : formatNumber(entry.other_allowances)}</td>
                                            <td className="text-danger">{!hasPermission('hr.reports') ? '***' : formatNumber(entry.deductions)}</td>
                                            <td className="fw-bold text-primary">{!hasPermission('hr.reports') ? '***' : formatNumber(entry.net_salary)}</td>
                                        </tr>
                                    ))}
                                    <tr style={{ fontWeight: 700, backgroundColor: 'var(--bg-hover)' }}>
                                        <td colSpan="2">{t('common.total', 'Total')}</td>
                                        <td>{!hasPermission('hr.reports') ? '***' : formatNumber(entries.reduce((sum, e) => sum + (e.basic_salary || 0), 0))}</td>
                                        <td>{!hasPermission('hr.reports') ? '***' : formatNumber(entries.reduce((sum, e) => sum + (e.housing_allowance || 0), 0))}</td>
                                        <td>{!hasPermission('hr.reports') ? '***' : formatNumber(entries.reduce((sum, e) => sum + (e.transport_allowance || 0), 0))}</td>
                                        <td>{!hasPermission('hr.reports') ? '***' : formatNumber(entries.reduce((sum, e) => sum + (e.other_allowances || 0), 0))}</td>
                                        <td className="text-danger">{!hasPermission('hr.reports') ? '***' : formatNumber(entries.reduce((sum, e) => sum + (e.deductions || 0), 0))}</td>
                                        <td className="text-primary">{!hasPermission('hr.reports') ? '***' : formatNumber(entries.reduce((sum, e) => sum + (e.net_salary || 0), 0))} {currency}</td>
                                    </tr>
                                </>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default PayrollDetails;
