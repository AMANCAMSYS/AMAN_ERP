
import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { FaCalendarAlt, FaFilter, FaList, FaStream, FaSearch, FaBox, FaCogs, FaClock } from 'react-icons/fa';
import { manufacturingAPI } from '../../utils/api';
import { toastEmitter } from '../../utils/toastEmitter';
import '../../components/ModuleStyles.css';

import DateInput from '../../components/common/DateInput';
const ProductionSchedule = () => {
    const { t } = useTranslation();
    const [viewMode, setViewMode] = useState('list'); // Default to list for better clarity initially
    const [operations, setOperations] = useState([]);
    const [workCenters, setWorkCenters] = useState([]);
    const [loading, setLoading] = useState(true);

    // Filters
    const [startDate, setStartDate] = useState(new Date().toISOString().split('T')[0]);
    const [endDate, setEndDate] = useState(new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]);
    const [selectedWC, setSelectedWC] = useState('');
    const [statusFilter, setStatusFilter] = useState('');

    useEffect(() => {
        fetchWorkCenters();
    }, []);

    useEffect(() => {
        fetchOperations();
    }, [startDate, endDate, selectedWC, statusFilter]);

    const fetchWorkCenters = async () => {
        try {
            const res = await manufacturingAPI.listWorkCenters();
            setWorkCenters(res.data);
        } catch (error) {
            console.error(error);
        }
    };

    const fetchOperations = async () => {
        setLoading(true);
        try {
            const params = {
                start_date: startDate,
                end_date: endDate,
                work_center_id: selectedWC || undefined,
                status: statusFilter || undefined
            };
            const res = await manufacturingAPI.listOperations(params);
            setOperations(res.data);
        } catch (error) {
            console.error("Error fetching operations:", error);
            toastEmitter.emit(t('error_fetching_data'), 'error');
        } finally {
            setLoading(false);
        }
    };

    const getStatusClass = (status) => {
        switch (status) {
            case 'pending': return 'op-status-pending';
            case 'in_progress': return 'op-status-in_progress';
            case 'completed': return 'op-status-completed';
            case 'blocked': return 'op-status-blocked';
            default: return '';
        }
    };

    const renderTimeline = () => {
        const filteredWCs = workCenters.filter(wc => !selectedWC || wc.id == selectedWC);

        return (
            <div className="timeline-canvas">
                {filteredWCs.map(wc => {
                    const wcOps = operations.filter(op => op.work_center_id === wc.id);
                    if (wcOps.length === 0 && selectedWC) return null;

                    return (
                        <div key={wc.id} className="wc-row">
                            <div className="wc-label">
                                {wc.name}
                            </div>
                            <div className="operations-track">
                                {wcOps.length === 0 ? (
                                    <span className="text-gray-300 text-xs italic ml-4">{t('common.no_data')}</span>
                                ) : (
                                    wcOps.map(op => (
                                        <div key={op.id} className={`op-bar ${getStatusClass(op.status)}`}>
                                            <div className="op-info">
                                                <span className="op-order">{op.order_number}</span>
                                                <span className="truncate max-w-[120px]">{op.product_name}</span>
                                            </div>
                                            <FaClock className="opacity-40" title={op.operation_description} />
                                        </div>
                                    ))
                                )}
                            </div>
                        </div>
                    );
                })}
                {operations.length === 0 && <div className="schedule-empty-state">{t('common.no_data')}</div>}
            </div>
        );
    };

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <div className="header-title">
                    <h1 className="workspace-title flex items-center gap-2">
                        <FaCalendarAlt className="text-primary" /> {t('manufacturing.production_schedule')}
                    </h1>
                    <p className="workspace-subtitle">{t('manufacturing.schedule_desc')}</p>
                </div>
                <div className="header-actions">
                    <div className="btn-group">
                        <button
                            className={`btn btn-sm ${viewMode === 'timeline' ? 'btn-primary' : 'btn-outline'}`}
                            onClick={() => setViewMode('timeline')}
                        >
                            <FaStream className="inline mr-1" /> {t('common.timeline')}
                        </button>
                        <button
                            className={`btn btn-sm ${viewMode === 'list' ? 'btn-primary' : 'btn-outline'}`}
                            onClick={() => setViewMode('list')}
                        >
                            <FaList className="inline mr-1" /> {t('common.list')}
                        </button>
                    </div>
                </div>
            </div>

            {/* Filters Expansion */}
            <div className="filter-panel">
                <div className="flex items-center gap-2 mb-4 text-gray-500 font-medium text-sm">
                    <FaFilter /> {t('common.filter')}
                </div>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <div className="form-group mb-0">
                        <label className="form-label text-xs uppercase tracking-wider text-gray-400">{t('common.from_date')}</label>
                        <DateInput className="form-control-sm w-full" value={startDate} onChange={e => setStartDate(e.target.value)} />
                    </div>
                    <div className="form-group mb-0">
                        <label className="form-label text-xs uppercase tracking-wider text-gray-400">{t('common.to_date')}</label>
                        <DateInput className="form-control-sm w-full" value={endDate} onChange={e => setEndDate(e.target.value)} />
                    </div>
                    <div className="form-group mb-0">
                        <label className="form-label text-xs uppercase tracking-wider text-gray-400">{t('manufacturing.work_center')}</label>
                        <select className="form-select-sm w-full" value={selectedWC} onChange={e => setSelectedWC(e.target.value)}>
                            <option value="">{t('common.all')}</option>
                            {workCenters.map(wc => (
                                <option key={wc.id} value={wc.id}>{wc.name}</option>
                            ))}
                        </select>
                    </div>
                    <div className="form-group mb-0">
                        <label className="form-label text-xs uppercase tracking-wider text-gray-400">{t('common.status')}</label>
                        <select className="form-select-sm w-full" value={statusFilter} onChange={e => setStatusFilter(e.target.value)}>
                            <option value="">{t('common.all')}</option>
                            <option value="pending">{t('status.pending', 'Pending')}</option>
                            <option value="in_progress">{t('status.in_progress', 'In Progress')}</option>
                            <option value="completed">{t('status.completed', 'Completed')}</option>
                        </select>
                    </div>
                </div>
            </div>

            <div className="schedule-container shadow-sm border">
                {loading ? (
                    <div className="flex flex-col items-center justify-center py-20 gap-4">
                        <div className="loading-spinner"></div>
                        <span className="text-gray-400 animate-pulse">{t('common.loading')}</span>
                    </div>
                ) : (
                    viewMode === 'list' ? (
                        <div className="overflow-x-auto rounded-lg">
                            <table className="data-table">
                                <thead>
                                    <tr>
                                        <th>{t('manufacturing.order')}</th>
                                        <th>{t('products.product')}</th>
                                        <th>{t('manufacturing.operation')}</th>
                                        <th>{t('manufacturing.work_center')}</th>
                                        <th>{t('common.start_date')}</th>
                                        <th>{t('common.status')}</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {operations.length === 0 ? (
                                        <tr><td colSpan="6" className="text-center py-10 text-gray-400">{t('common.no_data')}</td></tr>
                                    ) : (
                                        operations.map(op => (
                                            <tr key={op.id} className="hover:bg-slate-50 transition-colors">
                                                <td className="font-bold text-primary">{op.order_number}</td>
                                                <td>
                                                    <div className="flex items-center gap-2">
                                                        <FaBox className="text-gray-300 text-xs" />
                                                        {op.product_name}
                                                    </div>
                                                </td>
                                                <td>
                                                    <div className="flex items-center gap-2">
                                                        <FaCogs className="text-gray-300 text-xs" />
                                                        {op.operation_description}
                                                    </div>
                                                </td>
                                                <td>{op.work_center_name}</td>
                                                <td>
                                                    <span className="text-gray-500 flex items-center gap-1">
                                                        <FaClock className="text-[10px]" />
                                                        {op.planned_start_time ? new Date(op.planned_start_time).toLocaleDateString() : '-'}
                                                    </span>
                                                </td>
                                                <td>
                                                    <span className={`badge ${op.status === 'in_progress' ? 'badge-warning' : op.status === 'completed' ? 'badge-success' : 'badge-secondary'}`}>
                                                        {t(`status.${op.status}`, op.status)}
                                                    </span>
                                                </td>
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                            </table>
                        </div>
                    ) : (
                        renderTimeline()
                    )
                )}
            </div>
        </div>
    );
};

export default ProductionSchedule;
