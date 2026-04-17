import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { reportsAPI } from '../../../utils/api';
import { toastEmitter } from '../../../utils/toastEmitter';
import { getCurrency } from '../../../utils/auth';
import { formatNumber } from '../../../utils/format';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const PayrollReport = () => {
    const { t } = useTranslation();
    const currency = getCurrency();
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await reportsAPI.getPayrollTrend(12); // Last 12 months
                setData(response.data);
            } catch (error) {
                toastEmitter.emit(t('common.error'), 'error');
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    if (loading) return <div className="text-center py-5"><span className="loading"></span></div>;

    return (
        <div className="fade-in">
            {/* Chart Section */}
            <div className="card mb-4 section-card">
                <h3 className="section-title mb-4">{t('hr.reports.payroll_trend', 'Payroll Cost Trend (Last 12 Months)')}</h3>
                <div className="recharts-container" style={{ position: 'relative', width: '100%', height: '300px', minWidth: '0' }}>
                    <ResponsiveContainer width="100%" height="100%" debounce={50}>
                        <BarChart data={data}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                            <XAxis dataKey="month" axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 12 }} dy={10} />
                            <YAxis axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 12 }} tickFormatter={(value) => `${value / 1000}k`} />
                            <Tooltip
                                contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)' }}
                                formatter={(value) => [`${formatNumber(value)} ${currency}`, '']}
                            />
                            <Legend wrapperStyle={{ paddingTop: '20px' }} />
                            <Bar dataKey="total_gross" name={t('hr.payroll.gross', 'Gross Salary')} fill="#94a3b8" radius={[4, 4, 0, 0]} barSize={20} />
                            <Bar dataKey="total_net" name={t('hr.payroll.net', 'Net Salary')} fill="#3b82f6" radius={[4, 4, 0, 0]} barSize={20} />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Detailed Table */}
            <div className="card section-card">
                <h3 className="section-title">{t('common.details', 'Detailed Breakdown')}</h3>
                <div className="data-table-container">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>{t('common.period', 'Month')}</th>
                                <th className="text-end">{t('hr.payroll.gross', 'Gross Salary')}</th>
                                <th className="text-end">{t('hr.payroll.net', 'Net Salary')}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {data.map((row, index) => (
                                <tr key={index}>
                                    <td className="fw-medium">{row.month}</td>
                                    <td className="text-end text-muted">{formatNumber(row.total_gross)} {currency}</td>
                                    <td className="text-end text-primary fw-bold">{formatNumber(row.total_net)} {currency}</td>
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
    );
};

export default PayrollReport;
