
import { useState, useEffect, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { Plus, Eye } from 'lucide-react';
import { hrAPI } from '../../utils/api';
import { useNavigate } from 'react-router-dom';
import { getCurrency, hasPermission } from '../../utils/auth';
import { formatShortDate } from '../../utils/dateUtils';
import { formatNumber } from '../../utils/format';
import { toastEmitter } from '../../utils/toastEmitter';
import BackButton from '../../components/common/BackButton';
import DataTable from '../../components/common/DataTable';
import SearchFilter from '../../components/common/SearchFilter';

const PayrollList = () => {
    const { t } = useTranslation();
    const navigate = useNavigate();
    const currency = getCurrency();
    const [periods, setPeriods] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [search, setSearch] = useState('');
    const [statusFilter, setStatusFilter] = useState('');

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
            toastEmitter.emit(t('hr.payroll.error_creating_period') + (err.response?.data?.detail || err.message), 'error');
        }
    };

    const filteredData = useMemo(() => {
        let result = periods;
        if (search) {
            const q = search.toLowerCase();
            result = result.filter(period =>
                (period.name || '').toLowerCase().includes(q)
            );
        }
        if (statusFilter) {
            result = result.filter(period => period.status === statusFilter);
        }
        return result;
    }, [periods, search, statusFilter]);

    const columns = [
        { key: 'name', label: t("hr.payroll.period_name"), style: { fontWeight: 'bold' } },
        { key: 'start_date', label: t("hr.payroll.start_date"), render: (val) => formatShortDate(val) },
        { key: 'end_date', label: t("hr.payroll.end_date"), render: (val) => formatShortDate(val) },
        {
            key: 'status', label: t("common.status_title"),
            render: (val) => (
                <span className={`status-badge status-${val === 'posted' ? 'active' : 'draft'}`}>
                    {val === 'posted' ? t('common.posted') : t('common.draft')}
                </span>
            ),
        },
        {
            key: 'total_net', label: t("hr.payroll.total_salaries"),
            style: { fontWeight: 'bold', color: 'var(--primary)' },
            render: (val) => `${formatNumber(val)} ${currency}`,
        },
        {
            key: '_actions', label: t("common.actions"),
            render: (_val, row) => (
                <button
                    className="btn btn-sm btn-outline-primary"
                    onClick={(e) => { e.stopPropagation(); navigate(`/hr/payroll/${row.id}`); }}
                >
                    <Eye size={14} className="ms-1" />
                    {t('common.view_details')}
                </button>
            ),
        },
    ];

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        <h1 className="workspace-title">{t("hr.payroll.title")}</h1>
                        <p className="workspace-subtitle">{t("hr.payroll.subtitle")}</p>
                    </div>
                    {hasPermission('hr.manage') && (
                        <button className="btn btn-primary" onClick={() => setShowModal(true)}>
                            <Plus size={18} className="ms-2" />
                            {t('hr.payroll.new_period')}
                        </button>
                    )}
                </div>
            </div>

            <SearchFilter
                value={search}
                onChange={setSearch}
                placeholder={t("hr.payroll.period_name")}
                filters={[
                    {
                        key: 'status', label: t("common.status_title"), options: [
                            { value: 'draft', label: t('common.draft') },
                            { value: 'posted', label: t('common.posted') },
                        ]
                    },
                ]}
                filterValues={{ status: statusFilter }}
                onFilterChange={(_key, val) => setStatusFilter(val)}
            />

            <DataTable
                columns={columns}
                data={filteredData}
                loading={loading}
                emptyIcon="📅"
                emptyTitle={t("hr.payroll.no_periods")}
                emptyAction={hasPermission('hr.manage') ? { label: t('hr.payroll.create_first'), onClick: () => setShowModal(true) } : undefined}
                onRowClick={(row) => navigate(`/hr/payroll/${row.id}`)}
            />

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
