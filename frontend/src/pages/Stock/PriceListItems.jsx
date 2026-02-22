import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { inventoryAPI } from '../../utils/api';
import { getCurrency } from '../../utils/auth';
import { useTranslation } from 'react-i18next';
import { toastEmitter } from '../../utils/toastEmitter';
import BackButton from '../../components/common/BackButton';

const PriceListItems = () => {
    const { t } = useTranslation();
    const { id } = useParams();
    const navigate = useNavigate();
    const location = useLocation();
    const listCurrency = location.state?.currency || getCurrency();
    const listName = location.state?.name || `#${id}`;

    const [items, setItems] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        fetchItems();
    }, [id]);

    const fetchItems = async () => {
        try {
            setLoading(true);
            const response = await inventoryAPI.getPriceListItems(id);
            // Assuming the API returns a list of items based on previous checks
            // We use response.data if it's the axios response structure, or response if it's direct data
            // Based on utils/api.js, it returns `api.get(...)` which returns the full axios response.
            setItems(response.data || []);
        } catch (error) {
            console.error('Error fetching items:', error);
        } finally {
            setLoading(false);
        }
    };

    const handlePriceChange = (productId, newPrice) => {
        setItems(items.map(item =>
            item.product_id === productId ? { ...item, price: parseFloat(newPrice) || 0 } : item
        ));
    };

    const handleSave = async () => {
        try {
            setSaving(true);
            const updates = items.map(item => ({
                product_id: item.product_id,
                price: item.price
            }));

            await inventoryAPI.updatePriceListItems(id, updates);
            toastEmitter.emit(t('stock.price_lists.edit_prices.validation.success'), 'success');
            navigate('/stock/price-lists');
        } catch (error) {
            console.error('Error saving prices:', error);
            toastEmitter.emit(t('stock.price_lists.edit_prices.validation.error'), 'error');
        } finally {
            setSaving(false);
        }
    };

    const filteredItems = items.filter(item =>
        item.product_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.product_code?.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <div className="header-title">
                    <h1 className="workspace-title">{t('stock.price_lists.edit_prices.title')}</h1>
                    <p className="workspace-subtitle">{t('stock.price_lists.edit_prices.subtitle', { name: listName })}</p>
                </div>
                <div className="header-actions">
                    <button
                        onClick={handleSave}
                        disabled={saving}
                        className="btn btn-primary"
                    >
                        {saving ? t('stock.price_lists.edit_prices.saving') : t('stock.price_lists.edit_prices.save')}
                    </button>
                    <button
                        onClick={() => navigate('/stock/price-lists')}
                        className="btn btn-secondary"
                    >
                        {t('stock.price_lists.edit_prices.cancel')}
                    </button>
                </div>
            </div>

            <div className="card">
                <div className="p-4 border-b">
                    <input
                        type="text"
                        placeholder={t('stock.price_lists.edit_prices.search')}
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="form-input w-full max-w-md p-2 border rounded"
                    />
                </div>

                <table className="data-table">
                    <thead>
                        <tr>
                            <th>{t('stock.price_lists.edit_prices.table.code')}</th>
                            <th>{t('stock.price_lists.edit_prices.table.name')}</th>
                            <th>{t('stock.price_lists.edit_prices.table.price', { currency: listCurrency })}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {loading ? (
                            <tr>
                                <td colSpan="3" className="text-center py-8 text-muted">{t('stock.price_lists.edit_prices.loading')}</td>
                            </tr>
                        ) : filteredItems.length === 0 ? (
                            <tr>
                                <td colSpan="3" className="text-center py-8 text-muted">{t('stock.price_lists.edit_prices.no_results')}</td>
                            </tr>
                        ) : (
                            filteredItems.map((item) => (
                                <tr key={item.product_id}>
                                    <td className="font-mono text-sm">{item.product_code}</td>
                                    <td className="font-medium">{item.product_name}</td>
                                    <td>
                                        <input
                                            type="number"
                                            min="0"
                                            step="0.01"
                                            value={item.price}
                                            onChange={(e) => handlePriceChange(item.product_id, e.target.value)}
                                            className="form-input p-1 border rounded w-32 bg-gray-50 text-center"
                                        />
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default PriceListItems;
