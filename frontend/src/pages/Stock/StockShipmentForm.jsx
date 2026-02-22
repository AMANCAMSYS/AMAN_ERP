import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { inventoryAPI } from '../../utils/api';
import { toastEmitter } from '../../utils/toastEmitter';
import BackButton from '../../components/common/BackButton';

const StockShipmentForm = () => {
    const { t } = useTranslation();
    const navigate = useNavigate();
    const [loading, setLoading] = useState(false);
    const [warehouses, setWarehouses] = useState([]);
    const [products, setProducts] = useState([]);

    const [formData, setFormData] = useState({
        source_warehouse_id: '',
        destination_warehouse_id: '',
        notes: '',
        items: []
    });

    const [currentItem, setCurrentItem] = useState({
        product_id: '',
        quantity: 1
    });

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [whRes, prodRes] = await Promise.all([
                    inventoryAPI.listWarehouses(),
                    inventoryAPI.listProducts()
                ]);
                setWarehouses(whRes.data);
                setProducts(prodRes.data);
            } catch (err) {
                console.error("Failed to load data", err);
            }
        };
        fetchData();
    }, []);

    const addItem = () => {
        if (!currentItem.product_id || currentItem.quantity <= 0) return;

        const exists = formData.items.find(i => i.product_id === parseInt(currentItem.product_id));
        if (exists) {
            toastEmitter.emit(t('stock.shipments.form.validation.already_added'), 'error');
            return;
        }

        const product = products.find(p => p.id === parseInt(currentItem.product_id));

        setFormData(prev => ({
            ...prev,
            items: [...prev.items, {
                product_id: parseInt(currentItem.product_id),
                product_name: product.item_name,
                quantity: parseFloat(currentItem.quantity)
            }]
        }));

        setCurrentItem({ product_id: '', quantity: 1 });
    };

    const removeItem = (idx) => {
        setFormData(prev => ({
            ...prev,
            items: prev.items.filter((_, i) => i !== idx)
        }));
    };

    const handleSubmit = async () => {
        if (!formData.source_warehouse_id || !formData.destination_warehouse_id || formData.items.length === 0) {
            toastEmitter.emit(t('stock.shipments.form.validation.fill_required'), 'error');
            return;
        }

        if (formData.source_warehouse_id === formData.destination_warehouse_id) {
            toastEmitter.emit(t('stock.shipments.form.validation.source_dest_same'), 'error');
            return;
        }

        setLoading(true);
        try {
            await inventoryAPI.createShipment({
                source_warehouse_id: parseInt(formData.source_warehouse_id),
                destination_warehouse_id: parseInt(formData.destination_warehouse_id),
                notes: formData.notes,
                items: formData.items.map(i => ({ product_id: i.product_id, quantity: i.quantity }))
            });
            toastEmitter.emit(t('stock.shipments.form.validation.success'), 'success');
            navigate('/stock/shipments');
        } catch (err) {
            toastEmitter.emit(err.response?.data?.detail || t('stock.shipments.form.validation.error'), 'error');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <div className="header-title">
                    <h1 className="workspace-title">🚚 {t('stock.shipments.form.title')}</h1>
                    <p className="workspace-subtitle">{t('stock.shipments.form.subtitle')}</p>
                </div>
                <div className="header-actions">
                    <button className="btn btn-secondary" onClick={() => navigate('/stock')}>
                        {t('stock.shipments.form.cancel')}
                    </button>
                    <button
                        className="btn btn-primary"
                        onClick={handleSubmit}
                        disabled={loading || formData.items.length === 0}
                    >
                        {loading ? t('stock.shipments.form.sending') : t('stock.shipments.form.send')}
                    </button>
                </div>
            </div>

            <div className="form-container">
                <div className="section-card">
                    <h3 className="section-title">{t('stock.shipments.form.shipment_data')}</h3>
                    <div className="form-grid">
                        <div className="form-group">
                            <label className="form-label">{t('stock.shipments.form.from_warehouse')}</label>
                            <select
                                className="form-input"
                                value={formData.source_warehouse_id}
                                onChange={e => setFormData({ ...formData, source_warehouse_id: e.target.value })}
                            >
                                <option value="">{t('stock.shipments.form.select_warehouse')}</option>
                                {warehouses.map(w => (
                                    <option key={w.id} value={w.id}>{w.name}</option>
                                ))}
                            </select>
                        </div>
                        <div className="form-group">
                            <label className="form-label">{t('stock.shipments.form.to_warehouse')}</label>
                            <select
                                className="form-input"
                                value={formData.destination_warehouse_id}
                                onChange={e => setFormData({ ...formData, destination_warehouse_id: e.target.value })}
                            >
                                <option value="">{t('stock.shipments.form.select_warehouse')}</option>
                                {warehouses.filter(w => w.id !== parseInt(formData.source_warehouse_id)).map(w => (
                                    <option key={w.id} value={w.id}>{w.name}</option>
                                ))}
                            </select>
                        </div>
                        <div className="form-group full-width">
                            <label className="form-label">{t('stock.shipments.form.notes')}</label>
                            <textarea
                                className="form-input"
                                rows="2"
                                value={formData.notes}
                                onChange={e => setFormData({ ...formData, notes: e.target.value })}
                            />
                        </div>
                    </div>
                </div>

                <div className="section-card">
                    <h3 className="section-title">{t('stock.shipments.form.shipped_products')}</h3>

                    <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr auto', gap: '16px', alignItems: 'end', marginBottom: '24px', padding: '16px', background: 'var(--bg-secondary)', borderRadius: '8px' }}>
                        <div className="form-group" style={{ marginBottom: 0 }}>
                            <label className="form-label">{t('stock.shipments.form.product')}</label>
                            <select
                                className="form-input"
                                value={currentItem.product_id}
                                onChange={e => setCurrentItem({ ...currentItem, product_id: e.target.value })}
                            >
                                <option value="">{t('stock.shipments.form.select_product')}</option>
                                {products.map(p => (
                                    <option key={p.id} value={p.id}>{p.item_name} ({p.item_code})</option>
                                ))}
                            </select>
                        </div>
                        <div className="form-group" style={{ marginBottom: 0 }}>
                            <label className="form-label">{t('stock.shipments.form.quantity')}</label>
                            <input
                                type="number"
                                className="form-input"
                                min="0.01"
                                step="0.01"
                                value={currentItem.quantity}
                                onChange={e => setCurrentItem({ ...currentItem, quantity: e.target.value })}
                                onKeyDown={e => e.key === 'Enter' && addItem()}
                            />
                        </div>
                        <button
                            className="btn btn-primary"
                            onClick={addItem}
                            disabled={!currentItem.product_id || currentItem.quantity <= 0}
                        >
                            {t('stock.shipments.form.add')}
                        </button>
                    </div>

                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>{t('stock.shipments.form.table.product')}</th>
                                <th>{t('stock.shipments.form.table.quantity')}</th>
                                <th>{t('stock.shipments.form.table.actions')}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {formData.items.length === 0 && (
                                <tr>
                                    <td colSpan="4" className="text-center text-muted py-5">
                                        {t('stock.shipments.form.table.empty')}
                                    </td>
                                </tr>
                            )}
                            {formData.items.map((item, idx) => (
                                <tr key={idx}>
                                    <td>{idx + 1}</td>
                                    <td className="font-medium">{item.product_name}</td>
                                    <td className="font-bold">{item.quantity}</td>
                                    <td>
                                        <button
                                            className="btn-icon text-danger"
                                            onClick={() => removeItem(idx)}
                                        >
                                            🗑️
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default StockShipmentForm;
