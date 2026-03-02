import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import api from '../../utils/api';
import { formatDateTime } from '../../utils/dateUtils';
import CustomDatePicker from '../../components/common/CustomDatePicker';
import BackButton from '../../components/common/BackButton';
import { useBranch } from '../../context/BranchContext';
import { getUser } from '../../utils/auth';
import './AuditLogs.css';
import Pagination, { usePagination } from '../../components/common/Pagination';

const AuditLogs = () => {
    const { t } = useTranslation();
    const { currentBranch, loading: branchLoading } = useBranch();
    const [logs, setLogs] = useState([]);
    const [stats, setStats] = useState(null);
    const [actions, setActions] = useState([]);
    const [companies, setCompanies] = useState([]);
    const [loading, setLoading] = useState(true);
    const { currentPage, pageSize, totalItems, paginatedItems, onPageChange, onPageSizeChange } = usePagination(logs);
    const [user] = useState(getUser());
    const [filters, setFilters] = useState({
        action: '',
        username: '',
        resource_type: '',
        start_date: '',
        end_date: '',
        company_id: ''
    });

    useEffect(() => {
        if (!branchLoading) {
            fetchData();
        }
    }, [currentBranch, branchLoading]);

    useEffect(() => {
        if (user?.role === 'system_admin') {
            fetchCompanies();
        }
    }, [user]);

    const fetchCompanies = async () => {
        try {
            const res = await api.get('/companies/list');
            setCompanies(res.data.companies || []);
        } catch (error) {
            console.error('Error fetching companies:', error);
        }
    };

    const fetchData = async () => {
        setLoading(true);
        try {
            // Filter out empty values to avoid 422 error
            const cleanFilters = Object.fromEntries(
                Object.entries(filters).filter(([_, v]) => v !== '' && v !== null && v !== undefined)
            );

            // Add branch_id if a specific branch is selected AND no company_id filter (branch is company-specific)
            if (currentBranch && !filters.company_id) {
                cleanFilters.branch_id = currentBranch.id;
            }

            // company_id is already in cleanFilters if provided in filters state

            const [logsRes, statsRes, actionsRes] = await Promise.all([
                api.get('/audit/logs', { params: cleanFilters }),
                api.get('/audit/logs/stats', { params: cleanFilters }),
                api.get('/audit/logs/actions', { params: { company_id: filters.company_id } })
            ]);
            setLogs(logsRes.data);
            setStats(statsRes.data);
            setActions(actionsRes.data);
        } catch (error) {
            console.error('Error fetching audit logs:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleFilterChange = (e) => {
        setFilters({ ...filters, [e.target.name]: e.target.value });
    };

    const handleDateChange = (name, dateStr) => {
        setFilters({ ...filters, [name]: dateStr });
    };

    const applyFilters = () => {
        fetchData();
    };

    const resetFilters = () => {
        setFilters({
            action: '',
            username: '',
            resource_type: '',
            start_date: '',
            end_date: '',
            company_id: ''
        });
        fetchData();
    };

    const getActionIcon = (action) => {
        if (action.includes('login')) return '🔐';
        if (action.includes('create')) return '➕';
        if (action.includes('update')) return '✏️';
        if (action.includes('delete')) return '🗑️';
        if (action.includes('transfer')) return '🔄';
        if (action.includes('adjustment')) return '📊';
        return '📝';
    };

    const getActionColor = (action) => {
        if (action.includes('login')) return '#3498db';
        if (action.includes('create')) return '#2ecc71';
        if (action.includes('update')) return '#f39c12';
        if (action.includes('delete')) return '#e74c3c';
        return '#9b59b6';
    };

    return (
        <div className="audit-logs-container">
            <div className="audit-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <BackButton />
                    <div>
                        <h1>📋 {t('audit.title')}</h1>
                        <p className="subtitle">{t('audit.subtitle')}</p>
                    </div>
                </div>
            </div>

            {/* Stats Cards */}
            {stats && (
                <div className="metrics-grid">
                    <div className="metric-card">
                        <div className="metric-label">{t('audit.totalLogs')}</div>
                        <div className="metric-value text-primary">{stats.total_logs}</div>
                    </div>
                    <div className="metric-card">
                        <div className="metric-label">{t('audit.todayLogs')}</div>
                        <div className="metric-value text-success">{stats.today_logs}</div>
                    </div>
                    <div className="metric-card">
                        <div className="metric-label">{t('audit.activeUsers')}</div>
                        <div className="metric-value text-secondary">{stats.top_users?.length || 0}</div>
                    </div>
                </div>
            )}

            {/* Filters */}
            <div className="filters-panel">
                <div className="filter-group">
                    <label htmlFor="actionFilter">{t('audit.filterAction')}</label>
                    <select
                        name="action"
                        id="actionFilter"
                        value={filters.action}
                        onChange={handleFilterChange}
                    >
                        <option value="">{t('common.all')}</option>
                        {actions.map(action => (
                            <option key={action} value={action}>{t(`audit.actions.${action}`) || action}</option>
                        ))}
                    </select>
                </div>
                {user?.role === 'system_admin' && (
                    <div className="filter-group">
                        <label htmlFor="companyFilter">{t('companies.title')}</label>
                        <select
                            name="company_id"
                            id="companyFilter"
                            value={filters.company_id}
                            onChange={handleFilterChange}
                        >
                            <option value="">{t('audit.system_logs')}</option>
                            {Array.isArray(companies) && companies.map(c => (
                                <option key={c.id} value={c.id}>{c.company_name} ({c.id})</option>
                            ))}
                        </select>
                    </div>
                )}
                <div className="filter-group">
                    <label htmlFor="userFilter">{t('audit.filterUser')}</label>
                    <input
                        type="text"
                        name="username"
                        id="userFilter"
                        value={filters.username}
                        onChange={handleFilterChange}
                        placeholder={t('audit.searchUser')}
                        autoComplete="off"
                    />
                </div>
                <div className="filter-group">
                    <CustomDatePicker
                        label={t('audit.filterStartDate')}
                        selected={filters.start_date}
                        onChange={(dateStr) => handleDateChange('start_date', dateStr)}
                    />
                </div>
                <div className="filter-group">
                    <CustomDatePicker
                        label={t('audit.filterEndDate')}
                        selected={filters.end_date}
                        onChange={(dateStr) => handleDateChange('end_date', dateStr)}
                    />
                </div>
                <div className="filter-actions">
                    <button className="btn-apply" onClick={applyFilters}>
                        🔍 {t('common.filter')}
                    </button>
                    <button className="btn-reset" onClick={resetFilters}>
                        ↺ {t('common.reset')}
                    </button>
                </div>
            </div>

            {/* Logs Table */}
            <div className="logs-table-container">
                {loading ? (
                    <div className="loading-spinner">⏳ {t('common.loading')}</div>
                ) : logs.length === 0 ? (
                    <div className="no-data">📭 {t('audit.noLogs')}</div>
                ) : (
                    <table className="logs-table">
                        <thead>
                            <tr>
                                <th>{t('audit.action')}</th>
                                <th>{t('audit.user')}</th>
                                <th>{t('audit.resource')}</th>
                                <th>{t('audit.details')}</th>
                                <th>{t('audit.ip') || 'IP'}</th>
                                <th>{filters.company_id || !user?.company_id ? t('common.branch_or_company') : t('common.branch')}</th>
                                <th>{t('audit.time')}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {paginatedItems.map(log => (
                                <tr key={log.id}>
                                    <td>
                                        <span
                                            className="action-badge"
                                            style={{ backgroundColor: getActionColor(log.action) }}
                                        >
                                            {getActionIcon(log.action)} {t(`audit.actions.${log.action}`) || log.action}
                                        </span>
                                    </td>
                                    <td>{log.username}</td>
                                    <td>
                                        {/* Display Name from details if available, otherwise Type #ID */}
                                        {log.details && (log.details.name || log.details.customer_name || log.details.supplier_name || log.details.group_name || log.details.product_name || log.details.username || log.details.full_name) ? (
                                            <span className="resource-name-tag">
                                                {log.details.name || log.details.customer_name || log.details.supplier_name || log.details.group_name || log.details.product_name || log.details.username || log.details.full_name}
                                                <small className="resource-id-sub"> ({log.resource_type} #{log.resource_id})</small>
                                            </span>
                                        ) : (
                                            log.resource_type && (
                                                <span className="resource-tag">
                                                    {log.resource_type} #{log.resource_id}
                                                </span>
                                            )
                                        )}
                                    </td>
                                    <td className="details-cell">
                                        {log.details && Object.keys(log.details).length > 0 ? (
                                            <DetailsViewer details={log.details} t={t} />
                                        ) : '-'}
                                    </td>
                                    <td className="ip-cell">{log.ip_address || '-'}</td>
                                    <td className="branch-cell">
                                        {log.branch_name || (log.details?.company_id ? `🏢 ${log.details.company_id}` : '-')}
                                    </td>
                                    <td className="time-cell">{formatDateTime(log.created_at)}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
                <Pagination currentPage={currentPage} totalItems={totalItems} pageSize={pageSize} onPageChange={onPageChange} onPageSizeChange={onPageSizeChange} />
            </div>
        </div>
    );
};

const DetailsViewer = ({ details, t }) => {
    const [expanded, setExpanded] = useState(false);

    // Prepare entries to display
    const entries = Object.entries(details).filter(([key, value]) => {
        return !['name', 'customer_name', 'supplier_name', '_sa_instance_state'].includes(key);
    });

    if (entries.length === 0) return null;

    // Changes logic
    const changesIndex = entries.findIndex(([k]) => k === 'changes');
    const hasChanges = changesIndex > -1;
    let changesCount = 0;
    if (hasChanges && typeof entries[changesIndex][1] === 'object') {
        changesCount = Object.keys(entries[changesIndex][1]).length;
    }

    // Sort so 'changes' come completely last if they exist
    if (hasChanges) {
        const changes = entries.splice(changesIndex, 1)[0];
        entries.push(changes);
    }

    // Logic to determine if toggle is needed
    // 1. More than 1 top level entry?
    const hasManyEntries = entries.length > 1;
    // 2. Or the "changes" list is deep (more than 1 item)?
    const hasDeepChanges = hasChanges && changesCount > 1;

    const showToggle = hasManyEntries || hasDeepChanges;

    const visibleEntries = expanded ? entries : entries.slice(0, 1);

    // Use chevron icon
    const toggleIcon = expanded ? '▲' : '▼';

    return (
        <div className="details-viewer">
            <div className="details-list">
                {visibleEntries.map(([key, value]) => {
                    // Handling 'changes' object separately
                    if (key === 'changes' && typeof value === 'object') {
                        const allChanges = Object.entries(value);
                        // Show only 1 sub-item if collapsed to save space
                        const visibleChanges = expanded ? allChanges : allChanges.slice(0, 1);

                        return (
                            <div key={key} className="details-item changes-group">
                                <span className="details-key full-width">{t('audit.changes')}:</span>
                                <div className="changes-list">
                                    {visibleChanges.map(([cKey, cVal]) => (
                                        <div key={cKey} className="change-item">
                                            <span className="change-key">{t(`common.${cKey}`) || cKey}:</span>
                                            <span className="change-val">{String(cVal)}</span>
                                        </div>
                                    ))}
                                    {(!expanded && allChanges.length > 1) && (
                                        <div className="change-item more-dots">...</div>
                                    )}
                                </div>
                            </div>
                        );
                    }

                    return (
                        <div key={key} className="details-item">
                            <span className="details-key">{t(`common.${key}`) || t(`audit.${key}`) || key}:</span>
                            <span className="details-value">{String(value)}</span>
                        </div>
                    );
                })}
            </div>
            {showToggle && (
                <button
                    className="btn-show-more-icon"
                    onClick={() => setExpanded(!expanded)}
                    title={expanded ? (t('common.show_less')) : (t('common.show_more'))}
                >
                    {toggleIcon}
                </button>
            )}
        </div>
    );
};



export default AuditLogs;
