import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { dashboardAPI } from '../../services/dashboard'
import BackButton from '../../components/common/BackButton'

const WIDGET_TYPES = [
    { value: 'kpi_card', label: 'KPI Card' },
    { value: 'bar_chart', label: 'Bar Chart' },
    { value: 'line_chart', label: 'Line Chart' },
    { value: 'pie_chart', label: 'Pie Chart' },
    { value: 'table', label: 'Table' },
    { value: 'gauge', label: 'Gauge' },
]

const DATA_SOURCES = [
    { value: 'revenue', label: 'Revenue' },
    { value: 'expenses', label: 'Expenses' },
    { value: 'cash_position', label: 'Cash Position' },
    { value: 'top_customers', label: 'Top Customers' },
    { value: 'inventory_turnover', label: 'Inventory Turnover' },
    { value: 'ar_aging', label: 'AR Aging' },
    { value: 'ap_aging', label: 'AP Aging' },
    { value: 'sales_pipeline', label: 'Sales Pipeline' },
]

function DashboardEditor() {
    const { t } = useTranslation()
    const navigate = useNavigate()
    const [saving, setSaving] = useState(false)
    const [error, setError] = useState(null)

    const [form, setForm] = useState({
        name: '',
        description: '',
        access_roles: [],
        branch_scope: 'all',
        refresh_interval_minutes: 15,
    })

    const [widgets, setWidgets] = useState([])

    const addWidget = () => {
        setWidgets(prev => [...prev, {
            widget_type: 'kpi_card',
            title: '',
            data_source: 'revenue',
            position: { row: prev.length, col: 0, width: 3, height: 1 },
            sort_order: prev.length + 1,
        }])
    }

    const updateWidget = (index, field, value) => {
        setWidgets(prev => prev.map((w, i) => i === index ? { ...w, [field]: value } : w))
    }

    const removeWidget = (index) => {
        setWidgets(prev => prev.filter((_, i) => i !== index))
    }

    const moveWidget = (index, direction) => {
        setWidgets(prev => {
            const arr = [...prev]
            const newIndex = index + direction
            if (newIndex < 0 || newIndex >= arr.length) return arr
            ;[arr[index], arr[newIndex]] = [arr[newIndex], arr[index]]
            return arr.map((w, i) => ({ ...w, sort_order: i + 1 }))
        })
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        if (!form.name.trim()) {
            setError(t('analytics.name_required'))
            return
        }
        try {
            setSaving(true)
            setError(null)
            await dashboardAPI.createAnalyticsDashboard({
                ...form,
                widgets: widgets.map(w => ({
                    widget_type: w.widget_type,
                    title: w.title || `${w.data_source} widget`,
                    data_source: w.data_source,
                    filters: {},
                    position: w.position,
                    sort_order: w.sort_order,
                }))
            })
            navigate('/analytics')
        } catch (err) {
            setError(err.response?.data?.detail || t('analytics.create_failed'))
            console.error(err)
        } finally {
            setSaving(false)
        }
    }

    return (
        <div className="p-4">
            <BackButton fallback="/analytics" />
            <h2>{t('analytics.create_dashboard')}</h2>

            {error && <div className="alert alert-danger">{error}</div>}

            <form onSubmit={handleSubmit}>
                <div className="card mb-4">
                    <div className="card-body">
                        <h5 className="card-title">{t('analytics.dashboard_details')}</h5>
                        <div className="row g-3">
                            <div className="col-md-6">
                                <label className="form-label">{t('analytics.dashboard_name')}</label>
                                <input
                                    type="text"
                                    className="form-control"
                                    value={form.name}
                                    onChange={(e) => setForm(prev => ({ ...prev, name: e.target.value }))}
                                    required
                                />
                            </div>
                            <div className="col-md-6">
                                <label className="form-label">{t('analytics.branch_scope')}</label>
                                <select
                                    className="form-select"
                                    value={form.branch_scope}
                                    onChange={(e) => setForm(prev => ({ ...prev, branch_scope: e.target.value }))}
                                >
                                    <option value="all">{t('analytics.all_branches')}</option>
                                    <option value="assigned">{t('analytics.assigned_branches')}</option>
                                </select>
                            </div>
                            <div className="col-md-12">
                                <label className="form-label">{t('analytics.description')}</label>
                                <textarea
                                    className="form-control"
                                    rows={2}
                                    value={form.description}
                                    onChange={(e) => setForm(prev => ({ ...prev, description: e.target.value }))}
                                />
                            </div>
                            <div className="col-md-4">
                                <label className="form-label">{t('analytics.refresh_interval')}</label>
                                <input
                                    type="number"
                                    className="form-control"
                                    min={5}
                                    max={60}
                                    value={form.refresh_interval_minutes}
                                    onChange={(e) => setForm(prev => ({ ...prev, refresh_interval_minutes: Number(e.target.value) }))}
                                />
                            </div>
                        </div>
                    </div>
                </div>

                <div className="card mb-4">
                    <div className="card-body">
                        <div className="d-flex justify-content-between align-items-center mb-3">
                            <h5 className="card-title mb-0">{t('analytics.widgets')}</h5>
                            <button type="button" className="btn btn-sm btn-outline-primary" onClick={addWidget}>
                                + {t('analytics.add_widget')}
                            </button>
                        </div>

                        {widgets.length === 0 && (
                            <p className="text-muted">{t('analytics.no_widgets_yet')}</p>
                        )}

                        {widgets.map((widget, index) => (
                            <div key={index} className="border rounded p-3 mb-3 bg-light">
                                <div className="d-flex justify-content-between align-items-center mb-2">
                                    <span className="badge bg-secondary">#{index + 1}</span>
                                    <div className="d-flex gap-1">
                                        <button type="button" className="btn btn-sm btn-outline-secondary" onClick={() => moveWidget(index, -1)} disabled={index === 0}>↑</button>
                                        <button type="button" className="btn btn-sm btn-outline-secondary" onClick={() => moveWidget(index, 1)} disabled={index === widgets.length - 1}>↓</button>
                                        <button type="button" className="btn btn-sm btn-outline-danger" onClick={() => removeWidget(index)}>✕</button>
                                    </div>
                                </div>
                                <div className="row g-2">
                                    <div className="col-md-4">
                                        <label className="form-label form-label-sm">{t('analytics.widget_title')}</label>
                                        <input
                                            type="text"
                                            className="form-control form-control-sm"
                                            value={widget.title}
                                            onChange={(e) => updateWidget(index, 'title', e.target.value)}
                                            placeholder={t('analytics.widget_title')}
                                        />
                                    </div>
                                    <div className="col-md-4">
                                        <label className="form-label form-label-sm">{t('analytics.widget_type')}</label>
                                        <select
                                            className="form-select form-select-sm"
                                            value={widget.widget_type}
                                            onChange={(e) => updateWidget(index, 'widget_type', e.target.value)}
                                        >
                                            {WIDGET_TYPES.map(wt => (
                                                <option key={wt.value} value={wt.value}>{wt.label}</option>
                                            ))}
                                        </select>
                                    </div>
                                    <div className="col-md-4">
                                        <label className="form-label form-label-sm">{t('analytics.data_source')}</label>
                                        <select
                                            className="form-select form-select-sm"
                                            value={widget.data_source}
                                            onChange={(e) => updateWidget(index, 'data_source', e.target.value)}
                                        >
                                            {DATA_SOURCES.map(ds => (
                                                <option key={ds.value} value={ds.value}>{ds.label}</option>
                                            ))}
                                        </select>
                                    </div>
                                    <div className="col-md-3">
                                        <label className="form-label form-label-sm">{t('analytics.col_width')}</label>
                                        <select
                                            className="form-select form-select-sm"
                                            value={widget.position?.width || 3}
                                            onChange={(e) => updateWidget(index, 'position', { ...widget.position, width: Number(e.target.value) })}
                                        >
                                            <option value={3}>3 (quarter)</option>
                                            <option value={4}>4 (third)</option>
                                            <option value={6}>6 (half)</option>
                                            <option value={12}>12 (full)</option>
                                        </select>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="d-flex gap-2">
                    <button type="submit" className="btn btn-primary" disabled={saving}>
                        {saving ? t('common.saving') : t('analytics.create_dashboard')}
                    </button>
                    <button type="button" className="btn btn-secondary" onClick={() => navigate('/analytics')}>
                        {t('common.cancel')}
                    </button>
                </div>
            </form>
        </div>
    )
}

export default DashboardEditor
