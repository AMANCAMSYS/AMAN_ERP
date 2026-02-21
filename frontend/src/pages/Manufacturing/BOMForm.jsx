import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import api from '../../utils/api';
import { Save, ArrowRight, Plus, Trash2 } from 'lucide-react';
import { useToast } from '../../context/ToastContext';
import '../../components/ModuleStyles.css';

const BOMForm = () => {
    const { t } = useTranslation();
    const navigate = useNavigate();
    const { id } = useParams();
    const { showToast } = useToast();

    const [formData, setFormData] = useState({
        name: '',
        product_id: '',
        quantity: 1,
        is_active: true,
        items: []
    });

    const [products, setProducts] = useState([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        fetchProducts();
        if (id) {
            fetchBOM();
        }
    }, [id]);

    const fetchProducts = async () => {
        try {
            const res = await api.get('/inventory/products');
            setProducts(res.data);
        } catch (err) {
            console.error(err);
        }
    };

    const fetchBOM = async () => {
        try {
            const res = await api.get(`/manufacturing/boms/${id}`);
            const bom = res.data;
            setFormData({
                name: bom.name || '',
                product_id: bom.product_id || '',
                quantity: bom.quantity || 1,
                is_active: bom.is_active !== undefined ? bom.is_active : true,
                items: bom.items || []
            });
        } catch (err) {
            console.error('Failed to fetch BOM', err);
            showToast(t('common.error_occurred'), 'error');
            navigate('/manufacturing/boms');
        }
    };

    const handleAddItem = () => {
        setFormData({
            ...formData,
            items: [...formData.items, { item_id: '', quantity: 1, waste_percentage: 0 }]
        });
    };

    const handleItemChange = (index, field, value) => {
        const newItems = [...formData.items];
        newItems[index][field] = value;
        setFormData({ ...formData, items: newItems });
    };

    const handleRemoveItem = (index) => {
        const newItems = formData.items.filter((_, i) => i !== index);
        setFormData({ ...formData, items: newItems });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            if (id) {
                await api.put(`/manufacturing/boms/${id}`, formData);
            } else {
                await api.post('/manufacturing/boms', formData);
            }
            showToast(t('common.saved_successfully'), 'success');
            navigate('/manufacturing/boms');
        } catch (err) {
            showToast(t('common.error_saving'), 'error');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <div className="header-title">
                    <h1 className="workspace-title">{id ? t('manufacturing.edit_bom') : t('manufacturing.new_bom') || 'قائمة مواد جديدة'}</h1>
                </div>
                <div className="header-actions">
                    <button className="btn btn-secondary" onClick={() => navigate('/manufacturing/boms')}>
                        <ArrowRight size={16} /> {t('common.back')}
                    </button>
                </div>
            </div>

            <div className="card section-card">
                <form onSubmit={handleSubmit}>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
                        <div className="form-group">
                            <label className="form-label">{t('manufacturing.bom_name') || 'اسم القائمة'}</label>
                            <input
                                type="text"
                                className="form-input"
                                value={formData.name}
                                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                required
                            />
                        </div>
                        <div className="form-group">
                            <label className="form-label">{t('manufacturing.product') || 'المنتج النهائي'}</label>
                            <select
                                className="form-select"
                                value={formData.product_id}
                                onChange={(e) => setFormData({ ...formData, product_id: e.target.value })}
                                required
                            >
                                <option value="">{t('common.select')}</option>
                                {products.map(p => (
                                    <option key={p.id} value={p.id}>{p.name}</option>
                                ))}
                            </select>
                        </div>
                        <div className="form-group">
                            <label className="form-label">{t('manufacturing.quantity') || 'الكمية الناتجة'}</label>
                            <input
                                type="number"
                                className="form-input"
                                value={formData.quantity}
                                onChange={(e) => setFormData({ ...formData, quantity: parseFloat(e.target.value) })}
                                min="1"
                                required
                            />
                        </div>
                    </div>

                    <div style={{ borderTop: '1px solid var(--border-color)', margin: '16px 0', paddingTop: '16px' }}>
                        <h3 style={{ fontWeight: 600, marginBottom: '12px' }}>{t('manufacturing.raw_materials') || 'المواد الخام'}</h3>
                    </div>

                    <div style={{ overflowX: 'auto', marginBottom: '12px' }}>
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th>{t('manufacturing.item') || 'المادة'}</th>
                                    <th style={{ width: '150px' }}>{t('manufacturing.quantity') || 'الكمية'}</th>
                                    <th style={{ width: '150px' }}>{t('manufacturing.waste') || 'نسبة الهالك %'}</th>
                                    <th style={{ width: '50px' }}></th>
                                </tr>
                            </thead>
                            <tbody>
                                {formData.items.map((item, index) => (
                                    <tr key={index}>
                                        <td>
                                            <select
                                                className="form-select"
                                                value={item.item_id}
                                                onChange={(e) => handleItemChange(index, 'item_id', e.target.value)}
                                                required
                                            >
                                                <option value="">{t('common.select')}</option>
                                                {products.map(p => (
                                                    <option key={p.id} value={p.id}>{p.name}</option>
                                                ))}
                                            </select>
                                        </td>
                                        <td>
                                            <input
                                                type="number"
                                                className="form-input"
                                                value={item.quantity}
                                                onChange={(e) => handleItemChange(index, 'quantity', parseFloat(e.target.value))}
                                                min="0.001"
                                                step="0.001"
                                                required
                                            />
                                        </td>
                                        <td>
                                            <input
                                                type="number"
                                                className="form-input"
                                                value={item.waste_percentage}
                                                onChange={(e) => handleItemChange(index, 'waste_percentage', parseFloat(e.target.value))}
                                                min="0"
                                                max="100"
                                            />
                                        </td>
                                        <td>
                                            <button type="button" className="table-action-btn" style={{ color: 'var(--danger)' }} onClick={() => handleRemoveItem(index)}>
                                                <Trash2 size={16} />
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    <button type="button" className="btn btn-secondary btn-sm" style={{ marginBottom: '16px' }} onClick={handleAddItem}>
                        <Plus size={14} /> {t('manufacturing.add_item') || 'إضافة مادة'}
                    </button>

                    <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', borderTop: '1px solid var(--border-color)', paddingTop: '16px' }}>
                        <button type="button" className="btn btn-secondary" onClick={() => navigate('/manufacturing/boms')}>
                            {t('common.cancel')}
                        </button>
                        <button type="submit" className="btn btn-primary" disabled={loading}>
                            <Save size={16} />
                            {loading ? t('common.saving') : t('common.save')}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default BOMForm;
