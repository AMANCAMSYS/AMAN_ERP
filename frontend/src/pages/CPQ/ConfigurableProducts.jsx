import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { cpqAPI } from '../../utils/api';
import { Settings, Package } from 'lucide-react';
import '../../index.css';
import '../../components/ModuleStyles.css';
import BackButton from '../../components/common/BackButton';
import { useToast } from '../../context/ToastContext';
import { formatNumber } from '../../utils/format';
import { PageLoading } from '../../components/common/LoadingStates'

const ConfigurableProducts = () => {
    const { t, i18n } = useTranslation();
    const isRTL = i18n.language === 'ar';
    const navigate = useNavigate();
    const { showToast } = useToast();
    const [products, setProducts] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        cpqAPI.listProducts()
            .then(res => setProducts(res.data || []))
            .catch(() => showToast(t('common.error'), 'error'))
            .finally(() => setLoading(false));
    }, []);

    return (
        <div className="module-container" dir={isRTL ? 'rtl' : 'ltr'}>
            <BackButton />
            <div className="module-header">
                <h1><Package size={24} /> {t('cpq.configurable_products')}</h1>
                <button className="btn btn-primary" onClick={() => navigate('/sales/cpq/quotes')}>
                    {t('cpq.view_quotes')}
                </button>
            </div>

            {/* KPI */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 16, marginBottom: 24 }}>
                <div className="stat-card">
                    <div className="stat-value">{products.length}</div>
                    <div className="stat-label">{t('cpq.total_products')}</div>
                </div>
            </div>

            {loading ? (
                <PageLoading />
            ) : products.length === 0 ? (
                <div className="empty-state">{t('cpq.no_products')}</div>
            ) : (
                <div className="table-responsive">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>{t('cpq.product_code')}</th>
                                <th>{t('cpq.product_name')}</th>
                                <th>{t('cpq.configuration_name')}</th>
                                <th>{t('cpq.base_price')}</th>
                                <th>{t('common.actions')}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {products.map(p => (
                                <tr key={p.id}>
                                    <td>{p.product_code}</td>
                                    <td>{p.product_name}</td>
                                    <td>{p.name}</td>
                                    <td>{formatNumber(p.selling_price || 0)}</td>
                                    <td>
                                        <button
                                            className="btn btn-sm btn-primary"
                                            onClick={() => navigate(`/sales/cpq/configure/${p.id}`)}
                                        >
                                            <Settings size={14} /> {t('cpq.configure')}
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

export default ConfigurableProducts;
