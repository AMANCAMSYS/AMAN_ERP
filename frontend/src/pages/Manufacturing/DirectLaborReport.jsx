import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { manufacturingAPI } from '../../utils/api';
import { formatNumber } from '../../utils/format';
import '../../components/ModuleStyles.css';
import BackButton from '../../components/common/BackButton';
import DateInput from '../../components/common/DateInput';

const DirectLaborReport = () => {
    const { t } = useTranslation();
    const [loading, setLoading] = useState(false);
    const [report, setReport] = useState(null);
    const [workCenters, setWorkCenters] = useState([]);
    const [filters, setFilters] = useState({
        start_date: new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split('T')[0],
        end_date: new Date().toISOString().split('T')[0],
        work_center_id: ''
    });

    useEffect(() => {
        manufacturingAPI.listWorkCenters().then(r => setWorkCenters(r.data?.work_centers || r.data || [])).catch(() => {});
    }, []);

    const fetchReport = async () => {
        setLoading(true);
        try {
            const params = { ...filters };
            if (!params.work_center_id) delete params.work_center_id;
            const res = await manufacturingAPI.getDirectLaborReport(params);
            setReport(res.data);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { fetchReport(); }, []);

    const exportReport = async (format) => {
        try {
            const params = { ...filters, format };
            if (!params.work_center_id) delete params.work_center_id;
            const res = await manufacturingAPI.getDirectLaborReport(params);
            if (res.data?.file_url) window.open(res.data.file_url, '_blank');
        } catch (e) { console.error(e); }
    };

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <div className="header-title">
                    <h1 className="workspace-title">👷 {t('manufacturing.direct_labor.title', 'تقرير العمالة المباشرة')}</h1>
                    <p className="workspace-subtitle">{t('manufacturing.direct_labor.subtitle', 'تفاصيل ساعات العمل والتكاليف حسب مركز العمل')}</p>
                </div>
                <div className="header-actions">
                    <button className="btn btn-outline" onClick={() => exportReport('excel')}>📥 Excel</button>
                    <button className="btn btn-outline" onClick={() => exportReport('pdf')}>📄 PDF</button>
                </div>
            </div>

            {/* Filters */}
            <div className="card" style={{ marginBottom: 16 }}>
                <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'flex-end' }}>
                    <div className="form-group" style={{ flex: 1, minWidth: 150 }}>
                        <label className="form-label">{t('common.from_date', 'من تاريخ')}</label>
                        <DateInput className="form-input" value={filters.start_date}
                            onChange={e => setFilters(p => ({ ...p, start_date: e.target.value }))} />
                    </div>
                    <div className="form-group" style={{ flex: 1, minWidth: 150 }}>
                        <label className="form-label">{t('common.to_date', 'إلى تاريخ')}</label>
                        <DateInput className="form-input" value={filters.end_date}
                            onChange={e => setFilters(p => ({ ...p, end_date: e.target.value }))} />
                    </div>
                    <div className="form-group" style={{ flex: 1, minWidth: 180 }}>
                        <label className="form-label">{t('manufacturing.work_center', 'مركز العمل')}</label>
                        <select className="form-input" value={filters.work_center_id}
                            onChange={e => setFilters(p => ({ ...p, work_center_id: e.target.value }))}>
                            <option value="">{t('common.all', 'الكل')}</option>
                            {workCenters.map(wc => (
                                <option key={wc.id} value={wc.id}>{wc.name}</option>
                            ))}
                        </select>
                    </div>
                    <button className="btn btn-primary" onClick={fetchReport} disabled={loading}>
                        {loading ? '...' : t('common.search', 'بحث')}
                    </button>
                </div>
            </div>

            {/* Summary Cards */}
            {report?.totals && (
                <div className="metrics-grid" style={{ marginBottom: 16 }}>
                    <div className="metric-card">
                        <div className="metric-label">{t('manufacturing.direct_labor.total_hours', 'إجمالي الساعات الفعلية')}</div>
                        <div className="metric-value text-primary">{formatNumber(report.totals.total_actual_hours, 1)}</div>
                    </div>
                    <div className="metric-card">
                        <div className="metric-label">{t('manufacturing.direct_labor.planned_hours', 'الساعات المخططة')}</div>
                        <div className="metric-value text-secondary">{formatNumber(report.totals.total_planned_hours, 1)}</div>
                    </div>
                    <div className="metric-card">
                        <div className="metric-label">{t('manufacturing.direct_labor.efficiency', 'الكفاءة الإجمالية')}</div>
                        <div className="metric-value" style={{ color: report.totals.overall_efficiency_pct >= 90 ? 'var(--success)' : 'var(--warning)' }}>
                            {formatNumber(report.totals.overall_efficiency_pct, 1)}%
                        </div>
                    </div>
                    <div className="metric-card">
                        <div className="metric-label">{t('manufacturing.direct_labor.total_cost', 'إجمالي تكلفة العمالة')}</div>
                        <div className="metric-value text-danger">{formatNumber(report.totals.total_labor_cost)}</div>
                    </div>
                </div>
            )}

            {/* Work Center Summary */}
            {report?.work_center_summary?.length > 0 && (
                <div className="section-card" style={{ marginBottom: 16 }}>
                    <h3 className="section-title">{t('manufacturing.direct_labor.wc_summary', 'ملخص مراكز العمل')}</h3>
                    <div className="table-responsive">
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th>{t('manufacturing.work_center', 'مركز العمل')}</th>
                                    <th>{t('manufacturing.direct_labor.total_hours', 'إجمالي الساعات')}</th>
                                    <th>{t('manufacturing.direct_labor.total_cost', 'إجمالي التكلفة')}</th>
                                    <th>{t('manufacturing.direct_labor.operations_count', 'عدد العمليات')}</th>
                                </tr>
                            </thead>
                            <tbody>
                                {report.work_center_summary.map((wc, i) => (
                                    <tr key={i}>
                                        <td style={{ fontWeight: 600 }}>{wc.work_center}</td>
                                        <td>{formatNumber(wc.total_hours, 1)}</td>
                                        <td>{formatNumber(wc.total_cost)}</td>
                                        <td>{wc.operations_count}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {/* Details Table */}
            <div className="section-card">
                <h3 className="section-title">{t('manufacturing.direct_labor.details', 'التفاصيل')}</h3>
                {loading ? (
                    <div className="loading-container"><div className="spinner" /></div>
                ) : !report?.details?.length ? (
                    <div className="empty-state">
                        <p>{t('manufacturing.direct_labor.no_data', 'لا توجد بيانات عمالة في الفترة المحددة')}</p>
                    </div>
                ) : (
                    <div className="table-responsive">
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th>{t('manufacturing.work_center', 'مركز العمل')}</th>
                                    <th>{t('manufacturing.order_number', 'رقم الأمر')}</th>
                                    <th>{t('manufacturing.product', 'المنتج')}</th>
                                    <th>{t('manufacturing.operation', 'العملية')}</th>
                                    <th>{t('manufacturing.direct_labor.planned_hours', 'مخطط')}</th>
                                    <th>{t('manufacturing.direct_labor.actual_hours', 'فعلي')}</th>
                                    <th>{t('manufacturing.direct_labor.efficiency', 'الكفاءة')}</th>
                                    <th>{t('manufacturing.direct_labor.cost_per_hour', 'تكلفة/ساعة')}</th>
                                    <th>{t('manufacturing.direct_labor.labor_cost', 'تكلفة العمالة')}</th>
                                    <th>{t('manufacturing.direct_labor.qty', 'الكمية')}</th>
                                    <th>{t('manufacturing.direct_labor.cost_per_unit', 'تكلفة/وحدة')}</th>
                                </tr>
                            </thead>
                            <tbody>
                                {report.details.map((row, i) => (
                                    <tr key={i}>
                                        <td>{row.work_center}</td>
                                        <td><strong>{row.order_number}</strong></td>
                                        <td>{row.product_name}</td>
                                        <td>{row.operation}</td>
                                        <td>{formatNumber(row.planned_hours, 1)}</td>
                                        <td>{formatNumber(row.actual_hours, 1)}</td>
                                        <td>
                                            <span className={`status-badge ${row.efficiency_pct >= 90 ? 'status-active' : row.efficiency_pct >= 70 ? 'status-pending' : 'status-rejected'}`}>
                                                {formatNumber(row.efficiency_pct, 1)}%
                                            </span>
                                        </td>
                                        <td>{formatNumber(row.cost_per_hour)}</td>
                                        <td>{formatNumber(row.labor_cost)}</td>
                                        <td>{formatNumber(row.completed_qty)}</td>
                                        <td>{formatNumber(row.cost_per_unit)}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
};

export default DirectLaborReport;
