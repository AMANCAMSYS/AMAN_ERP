import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useParams, useNavigate } from 'react-router-dom';
import { demandForecastAPI } from '../../utils/api';
import { TrendingUp, Save, ArrowLeft } from 'lucide-react';
import '../../index.css';
import '../../components/ModuleStyles.css';
import BackButton from '../../components/common/BackButton';

const ForecastDetail = () => {
    const { t, i18n } = useTranslation();
    const isRTL = i18n.language === 'ar';
    const { id } = useParams();
    const navigate = useNavigate();
    const [forecast, setForecast] = useState(null);
    const [loading, setLoading] = useState(true);
    const [adjustments, setAdjustments] = useState({});
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState('');

    useEffect(() => {
        demandForecastAPI.get(id)
            .then(res => {
                setForecast(res.data);
                const adj = {};
                (res.data.periods || []).forEach(p => {
                    adj[p.id] = parseFloat(p.manual_adjustment) || 0;
                });
                setAdjustments(adj);
            })
            .catch(e => console.error(e))
            .finally(() => setLoading(false));
    }, [id]);

    const methodLabel = (m) => {
        const map = {
            moving_average: t('forecast.moving_average'),
            exponential_smoothing: t('forecast.exponential_smoothing'),
            seasonal_decomposition: t('forecast.seasonal_decomposition'),
        };
        return map[m] || m;
    };

    const handleAdjustmentChange = (periodId, value) => {
        setAdjustments(prev => ({ ...prev, [periodId]: parseFloat(value) || 0 }));
    };

    const handleSaveAdjustments = async () => {
        setSaving(true);
        setMessage('');
        try {
            const adjList = Object.entries(adjustments).map(([pid, val]) => ({
                period_id: parseInt(pid),
                manual_adjustment: val,
            }));
            await demandForecastAPI.adjust(id, { adjustments: adjList });
            setMessage(t('forecast.adjustments_saved'));
            // Reload
            const res = await demandForecastAPI.get(id);
            setForecast(res.data);
        } catch (e) {
            setMessage(t('forecast.save_failed'));
        } finally {
            setSaving(false);
        }
    };

    if (loading) return <div className="module-container"><div className="loading-spinner">{t('common.loading')}</div></div>;
    if (!forecast) return <div className="module-container"><div className="empty-state">{t('forecast.not_found')}</div></div>;

    const periods = forecast.periods || [];

    // Simple bar chart using divs
    const maxQty = Math.max(...periods.map(p => parseFloat(p.confidence_upper) || 0), 1);

    return (
        <div className="module-container" dir={isRTL ? 'rtl' : 'ltr'}>
            <BackButton />
            <div className="module-header">
                <h1><TrendingUp size={24} /> {t('forecast.forecast_detail')}</h1>
                <button className="btn btn-outline" onClick={() => navigate('/inventory/forecast')}>
                    <ArrowLeft size={16} /> {t('forecast.back_to_list')}
                </button>
            </div>

            {/* Summary cards */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 16, marginBottom: 24 }}>
                <div className="stat-card">
                    <div className="stat-label">{t('forecast.product')}</div>
                    <div className="stat-value" style={{ fontSize: 16 }}>{forecast.product_name || `#${forecast.product_id}`}</div>
                </div>
                <div className="stat-card">
                    <div className="stat-label">{t('forecast.method')}</div>
                    <div className="stat-value" style={{ fontSize: 16 }}>{methodLabel(forecast.forecast_method)}</div>
                </div>
                <div className="stat-card">
                    <div className="stat-label">{t('forecast.history_months')}</div>
                    <div className="stat-value">{forecast.history_months_used}</div>
                </div>
                <div className="stat-card">
                    <div className="stat-label">{t('forecast.generated_date')}</div>
                    <div className="stat-value" style={{ fontSize: 16 }}>{forecast.generated_date}</div>
                </div>
            </div>

            {/* Confidence band chart (simple bar visualization) */}
            <div className="form-card" style={{ marginBottom: 24 }}>
                <h3>{t('forecast.projection_chart')}</h3>
                <div style={{ display: 'flex', alignItems: 'flex-end', gap: 8, height: 200, padding: '16px 0' }}>
                    {periods.map(p => {
                        const proj = parseFloat(p.adjusted_quantity) || 0;
                        const lower = parseFloat(p.confidence_lower) || 0;
                        const upper = parseFloat(p.confidence_upper) || 0;
                        const barH = (proj / maxQty) * 160;
                        const lowerH = (lower / maxQty) * 160;
                        const upperH = (upper / maxQty) * 160;
                        return (
                            <div key={p.id} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', position: 'relative' }}>
                                {/* Confidence range */}
                                <div style={{ position: 'absolute', bottom: 24, width: '60%', height: upperH - lowerH, marginBottom: lowerH, background: 'rgba(59,130,246,0.1)', border: '1px dashed #93c5fd', borderRadius: 4 }} />
                                {/* Projected bar */}
                                <div style={{ width: '50%', height: barH, background: 'linear-gradient(180deg, #3b82f6, #1d4ed8)', borderRadius: '4px 4px 0 0', position: 'relative', zIndex: 1 }} />
                                <div style={{ fontSize: 10, marginTop: 4, textAlign: 'center' }}>{p.period_start?.slice(0, 7)}</div>
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* Period detail table with editable adjustments */}
            {message && <div className="alert alert-info" style={{ marginBottom: 16 }}>{message}</div>}

            <div className="data-table-wrapper">
                <table className="data-table">
                    <thead>
                        <tr>
                            <th>{t('forecast.period')}</th>
                            <th>{t('forecast.projected_qty')}</th>
                            <th>{t('forecast.confidence_lower')}</th>
                            <th>{t('forecast.confidence_upper')}</th>
                            <th>{t('forecast.manual_adjustment')}</th>
                            <th>{t('forecast.adjusted_qty')}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {periods.map(p => (
                            <tr key={p.id}>
                                <td>{p.period_start} → {p.period_end}</td>
                                <td>{parseFloat(p.projected_quantity).toFixed(2)}</td>
                                <td>{parseFloat(p.confidence_lower).toFixed(2)}</td>
                                <td>{parseFloat(p.confidence_upper).toFixed(2)}</td>
                                <td>
                                    <input
                                        type="number"
                                        className="form-control"
                                        style={{ width: 100 }}
                                        value={adjustments[p.id] ?? 0}
                                        onChange={e => handleAdjustmentChange(p.id, e.target.value)}
                                        step="0.01"
                                    />
                                </td>
                                <td style={{ fontWeight: 'bold' }}>
                                    {(parseFloat(p.projected_quantity) + (adjustments[p.id] || 0)).toFixed(2)}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            <div style={{ marginTop: 16, textAlign: 'right' }}>
                <button className="btn btn-primary" onClick={handleSaveAdjustments} disabled={saving}>
                    <Save size={16} /> {saving ? t('common.loading') : t('forecast.save_adjustments')}
                </button>
            </div>
        </div>
    );
};

export default ForecastDetail;
