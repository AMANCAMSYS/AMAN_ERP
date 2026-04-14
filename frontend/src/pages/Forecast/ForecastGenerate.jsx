import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { demandForecastAPI, inventoryAPI } from '../../utils/api';
import { TrendingUp, Loader } from 'lucide-react';
import '../../index.css';
import '../../components/ModuleStyles.css';
import BackButton from '../../components/common/BackButton';

const ForecastGenerate = () => {
    const { t, i18n } = useTranslation();
    const isRTL = i18n.language === 'ar';
    const navigate = useNavigate();
    const [products, setProducts] = useState([]);
    const [productId, setProductId] = useState('');
    const [warehouseId, setWarehouseId] = useState('');
    const [horizonMonths, setHorizonMonths] = useState(3);
    const [warehouses, setWarehouses] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    useEffect(() => {
        inventoryAPI.getProducts?.()
            .then(res => setProducts(res.data?.products || res.data || []))
            .catch(() => {});
        inventoryAPI.getWarehouses?.()
            .then(res => setWarehouses(res.data?.warehouses || res.data || []))
            .catch(() => {});
    }, []);

    const handleGenerate = async () => {
        if (!productId) {
            setError(t('forecast.select_product_required'));
            return;
        }
        setLoading(true);
        setError('');
        try {
            const res = await demandForecastAPI.generate({
                product_id: parseInt(productId),
                warehouse_id: warehouseId ? parseInt(warehouseId) : null,
                horizon_months: horizonMonths,
            });
            const data = res.data;
            navigate(`/inventory/forecast/${data.forecast_id}`);
        } catch (e) {
            setError(e.response?.data?.detail || t('forecast.generation_failed'));
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="module-container" dir={isRTL ? 'rtl' : 'ltr'}>
            <BackButton />
            <div className="module-header">
                <h1><TrendingUp size={24} /> {t('forecast.generate_forecast')}</h1>
            </div>

            <div className="form-card" style={{ maxWidth: 600, margin: '0 auto' }}>
                {error && <div className="alert alert-danger">{error}</div>}

                <div className="form-group">
                    <label>{t('forecast.product')} *</label>
                    <select className="form-control" value={productId} onChange={e => setProductId(e.target.value)}>
                        <option value="">{t('forecast.select_product')}</option>
                        {products.map(p => (
                            <option key={p.id} value={p.id}>{p.product_name || p.name}</option>
                        ))}
                    </select>
                </div>

                <div className="form-group">
                    <label>{t('forecast.warehouse')} ({t('common.optional')})</label>
                    <select className="form-control" value={warehouseId} onChange={e => setWarehouseId(e.target.value)}>
                        <option value="">{t('forecast.all_warehouses')}</option>
                        {warehouses.map(w => (
                            <option key={w.id} value={w.id}>{w.warehouse_name || w.name}</option>
                        ))}
                    </select>
                </div>

                <div className="form-group">
                    <label>{t('forecast.horizon_months')}</label>
                    <input
                        type="number"
                        className="form-control"
                        min={1}
                        max={24}
                        value={horizonMonths}
                        onChange={e => setHorizonMonths(parseInt(e.target.value) || 3)}
                    />
                </div>

                <button className="btn btn-primary" onClick={handleGenerate} disabled={loading} style={{ width: '100%', marginTop: 16 }}>
                    {loading ? <><Loader size={16} className="spin" /> {t('common.loading')}</> : t('forecast.generate_forecast')}
                </button>
            </div>
        </div>
    );
};

export default ForecastGenerate;
