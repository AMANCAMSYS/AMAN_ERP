import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { Plus, Search, Filter } from 'lucide-react';
import { assetsAPI } from '../../utils/api';
import { getCurrency } from '../../utils/auth';
import { formatShortDate } from '../../utils/dateUtils';
import Pagination, { usePagination } from '../../components/common/Pagination';

const AssetList = () => {
    const { t, i18n } = useTranslation();
    const navigate = useNavigate();
    const currency = getCurrency();
    const [assets, setAssets] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState('all');
    const { currentPage, pageSize, totalItems, paginatedItems, onPageChange, onPageSizeChange } = usePagination(assets);

    useEffect(() => {
        fetchAssets();
    }, [filter]);

    const fetchAssets = async () => {
        try {
            setLoading(true);
            const response = await assetsAPI.list(filter !== 'all' ? { status: filter } : {});
            setAssets(response.data);
        } catch (error) {
            console.error("Failed to fetch assets", error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <div className="d-flex align-items-center justify-content-between w-100">
                    <div>
                        <h1 className="workspace-title">{t('assets.title', 'Fixed Assets')}</h1>
                        <p className="workspace-subtitle">{t('assets.subtitle', 'Manage company assets and depreciation')}</p>
                    </div>
                    <div className="header-actions" style={{ display: 'flex', gap: '8px' }}>
                        <button className="btn btn-secondary shadow-sm" onClick={() => navigate('/assets/management')}>
                            {i18n.language === 'ar' ? 'النقل والتقييم' : 'Transfers & Reval'}
                        </button>
                        <button className="btn btn-primary shadow-sm" onClick={() => navigate('/assets/new')}>
                            <Plus size={18} className={t('common.is_rtl') === 'true' ? 'ms-2' : 'me-2'} />
                            {t('assets.new', 'New Asset')}
                        </button>
                    </div>
                </div>
            </div>

            <div className="metrics-grid mb-4">
                <div className="metric-card">
                    <div className="metric-label">{t('assets.total_value', 'Total Asset Value')}</div>
                    <div className="metric-value text-primary">
                        {assets.reduce((sum, a) => sum + (parseFloat(a.cost) || 0), 0).toLocaleString()} <small>{currency}</small>
                    </div>
                </div>
                <div className="metric-card">
                    <div className="metric-label">{t('assets.active_count', 'Active Assets')}</div>
                    <div className="metric-value text-success">
                        {assets.filter(a => a.status === 'active').length}
                    </div>
                </div>
            </div>

            <div className="card section-card border-0 shadow-sm">
                <div className="d-flex justify-content-between align-items-center mb-4">
                    <div className="d-flex gap-3">
                        <div className="search-box">
                            <Search size={16} />
                            <input
                                type="text"
                                name="asset_search"
                                id="asset_search"
                                placeholder={t('common.search')}
                                className="form-input form-input-sm"
                                autoComplete="off"
                            />
                        </div>
                        <div className="d-flex align-items-center gap-2 bg-light p-1 rounded-3 border">
                            <Filter size={14} className="text-muted ms-2" />
                            <select
                                name="asset_status_filter"
                                id="asset_status_filter"
                                className="form-select border-0 bg-transparent form-select-sm w-auto cursor-pointer"
                                value={filter}
                                onChange={(e) => setFilter(e.target.value)}
                                aria-label={t('common.filter_status')}
                            >
                                <option value="all">{t('common.all_status')}</option>
                                <option value="active">{t('status.active')}</option>
                                <option value="disposed">{t('status.disposed')}</option>
                            </select>
                        </div>
                    </div>
                </div>
                <div className="data-table-container border-0 bg-transparent">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th className="bg-transparent">{t('assets.code', 'Code')}</th>
                                <th className="bg-transparent">{t('assets.name', 'Name')}</th>
                                <th className="bg-transparent">{t('assets.type', 'Type')}</th>
                                <th className="bg-transparent text-center">{t('assets.purchase_date', 'Purchase Date')}</th>
                                <th className="bg-transparent text-end">{t('assets.cost', 'Cost')}</th>
                                <th className="bg-transparent text-center">{t('common.status.title', 'Status')}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {loading ? (
                                <tr><td colSpan="6" className="text-center py-5"><span className="loading"></span></td></tr>
                            ) : assets.length === 0 ? (
                                <tr><td colSpan="6" className="text-center py-5 text-muted">{t('common.no_data')}</td></tr>
                            ) : (
                                paginatedItems.map(asset => (
                                    <tr key={asset.id} onClick={() => navigate(`/assets/${asset.id}`)} style={{ cursor: 'pointer' }} className="align-middle">
                                        <td><span className="badge rounded-pill bg-light text-dark border px-3">{asset.code}</span></td>
                                        <td className="fw-semibold text-dark">{asset.name}</td>
                                        <td>
                                            <span className="text-muted d-flex align-items-center gap-2">
                                                <div style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: asset.type === 'tangible' ? 'var(--primary)' : 'var(--warning)' }}></div>
                                                {t(`assets.types.${asset.type}`, asset.type)}
                                            </span>
                                        </td>
                                        <td className="text-center text-muted small">{formatShortDate(asset.purchase_date)}</td>
                                        <td className="text-end fw-bold text-dark">{parseFloat(asset.cost).toLocaleString()} {currency}</td>
                                        <td className="text-center">
                                            <span className={`badge ${asset.status === 'active' ? 'bg-success-subtle text-success' : 'bg-secondary-subtle text-secondary'} border px-3`}>
                                                {t(`status.${asset.status}`, asset.status)}
                                            </span>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                    <Pagination currentPage={currentPage} totalItems={totalItems} pageSize={pageSize} onPageChange={onPageChange} onPageSizeChange={onPageSizeChange} />
                </div>
            </div>
        </div>
    );
};

export default AssetList;
