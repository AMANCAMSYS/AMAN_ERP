import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { demandForecastAPI } from '../../utils/api';
import { TrendingUp, Eye, Plus } from 'lucide-react';
import { useToast } from '../../context/ToastContext';
import '../../index.css';
import '../../components/ModuleStyles.css';
import BackButton from '../../components/common/BackButton';
import { PageLoading } from '../../components/common/LoadingStates'

const ForecastList = () => {
    const { t, i18n } = useTranslation();
    const isRTL = i18n.language === 'ar';
    const navigate = useNavigate();
    const { showToast } = useToast();
    const [forecasts, setForecasts] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        demandForecastAPI.list()
            .then(res => setForecasts(res.data || []))
            .catch(e => showToast(t('errors.fetch_failed'), 'error'))
            .finally(() => setLoading(false));
    }, []);

    const methodLabel = (m) => {
        const map = {
            moving_average: t('forecast.moving_average'),
            exponential_smoothing: t('forecast.exponential_smoothing'),
            seasonal_decomposition: t('forecast.seasonal_decomposition'),
        };
        return map[m] || m;
    };

    return (
        <div className="module-container" dir={isRTL ? 'rtl' : 'ltr'}>
            <BackButton />
            <div className="module-header">
                <h1><TrendingUp size={24} /> {t('forecast.demand_forecasts')}</h1>
                <button className="btn btn-primary" onClick={() => navigate('/inventory/forecast/generate')}>
                    <Plus size={16} /> {t('forecast.generate_forecast')}
                </button>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 16, marginBottom: 24 }}>
                <div className="stat-card">
                    <div className="stat-value">{forecasts.length}</div>
                    <div className="stat-label">{t('forecast.total_forecasts')}</div>
                </div>
            </div>

            {loading ? (
                <PageLoading />
            ) : forecasts.length === 0 ? (
                <div className="empty-state">{t('forecast.no_forecasts')}</div>
            ) : (
                <div className="data-table-wrapper">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>{t('forecast.product')}</th>
                                <th>{t('forecast.method')}</th>
                                <th>{t('forecast.generated_date')}</th>
                                <th>{t('forecast.history_months')}</th>
                                <th>{t('common.actions')}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {forecasts.map((f, idx) => (
                                <tr key={f.id}>
                                    <td>{idx + 1}</td>
                                    <td>{f.product_name || `#${f.product_id}`}</td>
                                    <td>{methodLabel(f.forecast_method)}</td>
                                    <td>{f.generated_date}</td>
                                    <td>{f.history_months_used}</td>
                                    <td>
                                        <button className="btn btn-sm btn-outline" onClick={() => navigate(`/inventory/forecast/${f.id}`)}>
                                            <Eye size={14} /> {t('common.view')}
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
};

export default ForecastList;
