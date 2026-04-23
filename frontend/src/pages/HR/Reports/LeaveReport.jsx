import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { reportsAPI } from '../../../utils/api';
import { toastEmitter } from '../../../utils/toastEmitter';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts';
import CustomDatePicker from '../../../components/common/CustomDatePicker';
import BackButton from '../../../components/common/BackButton';
import { PageLoading } from '../../../components/common/LoadingStates'

const LeaveReport = () => {
    const { t } = useTranslation();
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [dates, setDates] = useState({
        start: new Date(new Date().getFullYear(), 0, 1).toISOString().split('T')[0],
        end: new Date().toISOString().split('T')[0]
    });

    const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                const response = await reportsAPI.getLeaveUsage({ start_date: dates.start, end_date: dates.end });
                // Map leave types to translated labels
                const formattedData = response.data.map(item => ({
                    ...item,
                    name: t(`hr.leaves.type_${item.type}`, item.type)
                }));
                setData(formattedData);
            } catch (error) {
                toastEmitter.emit(t('common.error'), 'error');
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [t, dates]);

    if (loading) return <PageLoading />;

    return (
        <div className="workspace fade-in">
            <div className="workspace-header" style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
                <BackButton />
                <h1 className="workspace-title" style={{ margin: 0 }}>{t('hr.reports.leaves_distribution', 'Leave Report')}</h1>
            </div>
            {/* Date Filters */}
            <div className="display-flex gap-3 mb-4 align-center flex-wrap">
                <CustomDatePicker
                    label={t('common.start_date')}
                    selected={dates.start}
                    onChange={(d) => setDates(prev => ({ ...prev, start: d }))}
                />
                <CustomDatePicker
                    label={t('common.end_date')}
                    selected={dates.end}
                    onChange={(d) => setDates(prev => ({ ...prev, end: d }))}
                />
            </div>
            <div className="row">
                {/* Stats Cards */}
                <div className="col-md-12 mb-4">
                    <div className="metrics-grid">
                        <div className="metric-card">
                            <div className="metric-label">{t('hr.leaves.total_requests', 'Total Requests')}</div>
                            <div className="metric-value text-primary">{data.reduce((sum, item) => sum + item.count, 0)}</div>
                        </div>
                        <div className="metric-card">
                            <div className="metric-label">{t('hr.leaves.total_days', 'Total Days Off')}</div>
                            <div className="metric-value text-dark">{data.reduce((sum, item) => sum + item.days, 0)}</div>
                        </div>
                    </div>
                </div>

                {/* Chart */}
                <div className="col-md-6 mb-4">
                    <div className="card section-card h-100">
                        <h3 className="section-title">{t('hr.reports.leaves_distribution', 'Leave Distribution by Type')}</h3>
                        <div className="recharts-container" style={{ position: 'relative', width: '100%', height: '300px', minWidth: '0' }}>
                            <ResponsiveContainer width="100%" height="100%" debounce={50}>
                                <PieChart>
                                    <Pie
                                        data={data}
                                        cx="50%"
                                        cy="50%"
                                        innerRadius={60}
                                        outerRadius={80}
                                        paddingAngle={5}
                                        dataKey="days"
                                    >
                                        {data.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                        ))}
                                    </Pie>
                                    <Tooltip formatter={(value) => [`${value} ${t('common.days')}`, t('hr.leaves.days')]} />
                                </PieChart>
                            </ResponsiveContainer>
                        </div>
                    </div>
                </div>

                {/* Table */}
                <div className="col-md-6 mb-4">
                    <div className="card section-card h-100">
                        <h3 className="section-title">{t('common.details', 'Details')}</h3>
                        <div className="data-table-container">
                            <table className="data-table">
                                <thead>
                                    <tr>
                                        <th>{t('hr.leaves.type', 'Type')}</th>
                                        <th className="text-center">{t('common.count', 'Requests')}</th>
                                        <th className="text-center">{t('common.days', 'Days')}</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {data.map((row, index) => (
                                        <tr key={index}>
                                            <td>
                                                <span className="d-flex align-items-center gap-2">
                                                    <span style={{ width: 10, height: 10, borderRadius: '50%', backgroundColor: COLORS[index % COLORS.length] }}></span>
                                                    {row.name}
                                                </span>
                                            </td>
                                            <td className="text-center">{row.count}</td>
                                            <td className="text-center fw-bold">{row.days}</td>
                                        </tr>
                                    ))}
                                    {data.length === 0 && (
                                        <tr>
                                            <td colSpan="3" className="text-center py-4 text-muted">{t('common.no_data')}</td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default LeaveReport;
