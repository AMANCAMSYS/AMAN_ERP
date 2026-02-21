import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
    ArrowRight, Save, Play, Plus, Trash2, Filter,
    Columns, Database, FileText, Download
} from 'lucide-react';
import { customReportsAPI } from '../../utils/api';
import { toastEmitter } from '../../utils/toastEmitter';
import '../../components/ModuleStyles.css';

export default function ReportBuilder() {
    const { t, i18n } = useTranslation();
    const navigate = useNavigate();
    const isRTL = i18n.language === 'ar';

    const [loading, setLoading] = useState(false);
    const [previewData, setPreviewData] = useState(null);
    const [savedReports, setSavedReports] = useState([]);
    const [showSavedList, setShowSavedList] = useState(false);

    // Available Tables (Mock for now, or could be fetched)
    const availableTables = [
        { id: 'projects', label: t('reports.tables.projects', 'المشاريع'), columns: ['id', 'project_name', 'status', 'start_date', 'end_date', 'budget', 'manager_id'] },
        { id: 'tasks', label: t('reports.tables.tasks', 'المهام'), columns: ['id', 'project_id', 'task_name', 'status', 'start_date', 'end_date', 'planned_hours', 'actual_hours'] },
        { id: 'sales_invoices', label: t('reports.tables.sales', 'فواتير المبيعات'), columns: ['id', 'invoice_number', 'customer_id', 'invoice_date', 'total_amount', 'status'] },
        { id: 'expenses', label: t('reports.tables.expenses', 'المصاريف'), columns: ['id', 'project_id', 'expense_date', 'amount', 'category', 'description'] },
        { id: 'customers', label: t('reports.tables.customers', 'العملاء'), columns: ['id', 'name', 'email', 'phone', 'city'] },
    ];

    const [config, setConfig] = useState({
        name: '',
        description: '',
        table_name: 'projects',
        columns: [],
        filters: {},
        sort_by: 'id',
        sort_order: 'desc'
    });

    useEffect(() => {
        fetchSavedReports();
    }, []);

    const fetchSavedReports = async () => {
        try {
            const res = await customReportsAPI.list();
            setSavedReports(res.data || []);
        } catch { }
    };

    const handleColumnToggle = (col) => {
        setConfig(prev => {
            const exists = prev.columns.includes(col);
            if (exists) {
                return { ...prev, columns: prev.columns.filter(c => c !== col) };
            } else {
                return { ...prev, columns: [...prev.columns, col] };
            }
        });
    };

    const handleAddFilter = () => {
        // Simplified filter UI: just adding a placeholder for now
        // In real app, we need field, operator, value
        const field = availableTables.find(t => t.id === config.table_name)?.columns[0];
        setConfig(prev => ({
            ...prev,
            filters: { ...prev.filters, [field]: '' }
        }));
    };

    const handleFilterChange = (oldField, newField, value) => {
        const newFilters = { ...config.filters };
        if (oldField !== newField) {
            delete newFilters[oldField];
        }
        newFilters[newField] = value;
        setConfig(prev => ({ ...prev, filters: newFilters }));
    };

    const handleRemoveFilter = (field) => {
        const newFilters = { ...config.filters };
        delete newFilters[field];
        setConfig(prev => ({ ...prev, filters: newFilters }));
    };

    const handlePreview = async () => {
        if (config.columns.length === 0) {
            toastEmitter.emit(t('reports.errors.no_columns', 'اختر عموداً واحداً على الأقل'), 'error');
            return;
        }
        setLoading(true);
        try {
            const res = await customReportsAPI.preview(config);
            setPreviewData(res.data);
        } catch (err) {
            toastEmitter.emit(t('common.error', 'خطأ في المعاينة'), 'error');
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async () => {
        if (!config.name) {
            toastEmitter.emit(t('reports.errors.name_required', 'اسم التقرير مطلوب'), 'error');
            return;
        }
        try {
            await customReportsAPI.create(config);
            toastEmitter.emit(t('common.saved', 'تم الحفظ'), 'success');
            fetchSavedReports();
        } catch (err) {
            toastEmitter.emit(t('common.save_error', 'خطأ في الحفظ'), 'error');
        }
    };

    const loadReport = async (id) => {
        try {
            const res = await customReportsAPI.get(id);
            const report = res.data;
            setConfig({
                ...report.query_config,
                name: report.report_name,
                description: report.description
            });
            setShowSavedList(false);
            handlePreview();
        } catch { }
    };

    const deleteReport = async (id) => {
        if (!window.confirm(t('common.confirm_delete'))) return;
        try {
            await customReportsAPI.delete(id);
            fetchSavedReports();
        } catch { }
    };

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <div className="d-flex align-items-center justify-content-between w-100">
                    <div className="d-flex align-items-center gap-3">
                        <button className="btn btn-icon btn-light" onClick={() => navigate('/reports')}>
                            <ArrowRight size={20} style={{ transform: isRTL ? 'none' : 'scaleX(-1)' }} />
                        </button>
                        <div>
                            <h1 className="workspace-title mb-0">{t('reports.builder_title', 'منشئ التقارير المخصص')}</h1>
                            <p className="workspace-subtitle mb-0">{t('reports.builder_subtitle', 'صمم تقاريرك الخاصة بسهولة')}</p>
                        </div>
                    </div>
                    <div className="d-flex gap-2">
                        <button className="btn btn-light" onClick={() => setShowSavedList(!showSavedList)}>
                            <FileText size={16} /> {t('reports.saved_reports', 'التقارير المحفوظة')}
                        </button>
                        <button className="btn btn-primary" onClick={handleSave}>
                            <Save size={16} /> {t('common.save', 'حفظ')}
                        </button>
                    </div>
                </div>
            </div>

            <div className="row g-4">
                {/* Configuration Panel */}
                <div className="col-lg-4">
                    <div className="card section-card border-0 shadow-sm mb-4">
                        <div className="card-body">
                            <h5 className="section-title mb-3"><Database size={16} /> {t('reports.data_source', 'مصدر البيانات')}</h5>

                            <div className="mb-3">
                                <label className="form-label">{t('reports.report_name', 'اسم التقرير')}</label>
                                <input type="text" className="form-input" value={config.name}
                                    onChange={e => setConfig({ ...config, name: e.target.value })}
                                    placeholder={t('reports.report_name_placeholder', 'مثال: تقرير مبيعات الشهر')} />
                            </div>

                            <div className="mb-3">
                                <label className="form-label">{t('reports.select_table', 'اختر الجدول')}</label>
                                <select className="form-input" value={config.table_name}
                                    onChange={e => setConfig({ ...config, table_name: e.target.value, columns: [] })}>
                                    {availableTables.map(t => (
                                        <option key={t.id} value={t.id}>{t.label}</option>
                                    ))}
                                </select>
                            </div>
                        </div>
                    </div>

                    <div className="card section-card border-0 shadow-sm mb-4">
                        <div className="card-body">
                            <h5 className="section-title mb-3"><Columns size={16} /> {t('reports.columns', 'الأعمدة')}</h5>
                            <div className="d-flex flex-wrap gap-2">
                                {availableTables.find(t => t.id === config.table_name)?.columns.map(col => (
                                    <button
                                        key={col}
                                        className={`btn btn-sm ${config.columns.includes(col) ? 'btn-primary' : 'btn-light'}`}
                                        onClick={() => handleColumnToggle(col)}
                                    >
                                        {col}
                                    </button>
                                ))}
                            </div>
                        </div>
                    </div>

                    <div className="card section-card border-0 shadow-sm">
                        <div className="card-body">
                            <h5 className="section-title mb-3">
                                <div className="d-flex justify-content-between align-items-center w-100">
                                    <span><Filter size={16} /> {t('reports.filters', 'الفلاتر')}</span>
                                    <button className="btn btn-sm btn-light btn-icon" onClick={handleAddFilter}><Plus size={14} /></button>
                                </div>
                            </h5>

                            {Object.entries(config.filters).map(([field, value], idx) => (
                                <div key={idx} className="d-flex gap-2 mb-2 align-items-center">
                                    <select className="form-input form-select-sm" value={field}
                                        onChange={(e) => handleFilterChange(field, e.target.value, value)}>
                                        {availableTables.find(t => t.id === config.table_name)?.columns.map(col => (
                                            <option key={col} value={col}>{col}</option>
                                        ))}
                                    </select>
                                    <span>=</span>
                                    <input type="text" className="form-input form-input-sm" value={value}
                                        onChange={(e) => handleFilterChange(field, field, e.target.value)} />
                                    <button className="btn btn-icon btn-sm text-danger" onClick={() => handleRemoveFilter(field)}>
                                        <Trash2 size={14} />
                                    </button>
                                </div>
                            ))}
                            {Object.keys(config.filters).length === 0 && (
                                <p className="text-muted small text-center">{t('reports.no_filters', 'لا توجد فلاتر')}</p>
                            )}

                            <button className="btn btn-success w-100 mt-3" onClick={handlePreview} disabled={loading}>
                                <Play size={16} /> {loading ? t('common.loading', 'جاري التحميل...') : t('reports.preview', 'معاينة التقرير')}
                            </button>
                        </div>
                    </div>
                </div>

                {/* Preview Panel */}
                <div className="col-lg-8">
                    {showSavedList ? (
                        <div className="card section-card border-0 shadow-sm">
                            <div className="card-body">
                                <h5 className="section-title mb-4">{t('reports.saved_reports', 'التقارير المحفوظة')}</h5>
                                {savedReports.length === 0 ? (
                                    <p className="text-muted text-center">{t('common.no_data', 'لا يوجد بيانات')}</p>
                                ) : (
                                    <div className="table-responsive">
                                        <table className="table">
                                            <thead>
                                                <tr>
                                                    <th>{t('common.name', 'الاسم')}</th>
                                                    <th>{t('common.description', 'الوصف')}</th>
                                                    <th>{t('common.created_at', 'تاريخ الإنشاء')}</th>
                                                    <th></th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {savedReports.map(r => (
                                                    <tr key={r.id}>
                                                        <td className="fw-bold text-primary" style={{ cursor: 'pointer' }} onClick={() => loadReport(r.id)}>
                                                            {r.report_name}
                                                        </td>
                                                        <td>{r.description || '-'}</td>
                                                        <td>{new Date(r.created_at).toLocaleDateString()}</td>
                                                        <td>
                                                            <button className="btn btn-icon btn-sm text-danger" onClick={() => deleteReport(r.id)}>
                                                                <Trash2 size={14} />
                                                            </button>
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                )}
                            </div>
                        </div>
                    ) : (
                        <div className="card section-card border-0 shadow-sm h-100">
                            <div className="card-body">
                                <div className="d-flex justify-content-between align-items-center mb-4">
                                    <h5 className="section-title mb-0">{t('reports.results', 'النتائج')}</h5>
                                    {previewData && (
                                        <button className="btn btn-sm btn-outline-secondary">
                                            <Download size={14} /> {t('common.export', 'تصدير')}
                                        </button>
                                    )}
                                </div>

                                {loading ? (
                                    <div className="text-center py-5"><span className="loading"></span></div>
                                ) : !previewData ? (
                                    <div className="text-center py-5 text-muted">
                                        <Database size={48} className="mb-3 opacity-25" />
                                        <p>{t('reports.click_preview', 'اضبط الإعدادات واضغط على معاينة')}</p>
                                    </div>
                                ) : (
                                    <div className="data-table-container">
                                        <table className="data-table">
                                            <thead>
                                                <tr>
                                                    {config.columns.map(col => (
                                                        <th key={col}>{col}</th>
                                                    ))}
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {previewData.slice(0, 50).map((row, idx) => (
                                                    <tr key={idx}>
                                                        {config.columns.map(col => (
                                                            <td key={col}>{typeof row[col] === 'object' ? JSON.stringify(row[col]) : row[col]}</td>
                                                        ))}
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                        <div className="mt-3 text-muted small">
                                            {t('reports.showing_rows', 'عرض أول 50 صف')}
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
