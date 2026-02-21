import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import api from '../../utils/api';
import { Save, ArrowRight, Play, Factory, Package, AlertCircle } from 'lucide-react';
import { useToast } from '../../context/ToastContext';
import '../../components/ModuleStyles.css';

const ProductionOrderForm = () => {
    const { t, i18n } = useTranslation();
    const navigate = useNavigate();
    const { showToast } = useToast();
    const isRTL = i18n.dir() === 'rtl';

    const [boms, setBoms] = useState([]);
    const [selectedBom, setSelectedBom] = useState(null);
    const [quantity, setQuantity] = useState(1);
    const [loading, setLoading] = useState(false);
    const [loadingBoms, setLoadingBoms] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchBOMs();
    }, []);

    const fetchBOMs = async () => {
        try {
            const res = await api.get('/manufacturing/boms');
            setBoms(res.data.filter(b => b.is_active));
            setError(null);
        } catch (err) {
            console.error(err);
            setError(t('common.error_loading_data'));
        } finally {
            setLoadingBoms(false);
        }
    };

    const handleBomChange = (bomId) => {
        const bom = boms.find(b => b.id.toString() === bomId);
        setSelectedBom(bom);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!selectedBom) {
            showToast(t('manufacturing.select_bom_required'), 'error');
            return;
        }

        setLoading(true);
        try {
            await api.post('/manufacturing/orders', {
                bom_id: selectedBom.id,
                quantity: parseFloat(quantity),
                status: 'in_progress',
                start_date: new Date().toISOString()
            });
            showToast(t('manufacturing.order_created'), 'success');
            navigate('/manufacturing/orders');
        } catch (err) {
            showToast(t('common.error_occurred'), 'error');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    if (loadingBoms) {
        return (
            <div className="workspace flex items-center justify-center fade-in">
                <div className="text-center">
                    <span className="loading"></span>
                    <p className="text-slate-500">{t('common.loading')}</p>
                </div>
            </div>
        );
    }

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        <h1 className="workspace-title flex items-center gap-2">
                            <span className="p-2 rounded-lg bg-amber-50 text-amber-600">
                                <Factory size={24} />
                            </span>
                            {t('manufacturing.new_order')}
                        </h1>
                        <p className="workspace-subtitle">
                            {t('manufacturing.new_order_desc') || 'إنشاء أمر تصنيع جديد'}
                        </p>
                    </div>
                    <button
                        className="btn btn-secondary"
                        onClick={() => navigate('/manufacturing/orders')}
                    >
                        <ArrowRight size={18} className={isRTL ? '' : 'rotate-180'} />
                        {t('common.back')}
                    </button>
                </div>
            </div>

            {error && (
                <div className="alert alert-error mb-4">
                    <AlertCircle size={18} />
                    <span>{error}</span>
                </div>
            )}

            <div className="flex justify-center">
                <div className="card bg-base-100 shadow-lg max-w-2xl w-full">
                    <div className="card-body p-8">
                        <div className="flex items-center gap-4 mb-6">
                            <div className="w-14 h-14 bg-amber-50 text-amber-600 rounded-2xl flex items-center justify-center">
                                <Package size={28} />
                            </div>
                            <div>
                                <h2 className="text-xl font-bold text-slate-800">
                                    {t('manufacturing.production_details')}
                                </h2>
                                <p className="text-slate-500 text-sm">
                                    {t('manufacturing.production_details_desc') || 'حدد قائمة المواد والكمية المطلوبة'}
                                </p>
                            </div>
                        </div>

                        <form onSubmit={handleSubmit} className="space-y-6">
                            <div className="form-group">
                                <label className="form-label">
                                    {t('manufacturing.select_bom')}
                                    <span className="text-error">*</span>
                                </label>
                                <select
                                    className="form-input"
                                    onChange={(e) => handleBomChange(e.target.value)}
                                    required
                                    value={selectedBom?.id || ''}
                                >
                                    <option value="">{t('common.select')}</option>
                                    {boms.map(b => (
                                        <option key={b.id} value={b.id}>
                                            {b.name} ({b.product_name})
                                        </option>
                                    ))}
                                </select>
                                {boms.length === 0 && (
                                    <p className="text-sm text-warning mt-2">
                                        {t('manufacturing.no_boms_available') || 'لا توجد قوائم مواد متاحة. قم بإنشاء قائمة مواد أولاً.'}
                                    </p>
                                )}
                            </div>

                            {selectedBom && (
                                <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
                                    <div className="flex items-center gap-3">
                                        <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                                            <Package size={20} className="text-blue-600" />
                                        </div>
                                        <div>
                                            <h3 className="font-bold text-blue-800">
                                                {t('manufacturing.output')}: {selectedBom.product_name}
                                            </h3>
                                            <p className="text-sm text-blue-600">
                                                {t('manufacturing.produces_per_cycle', { count: selectedBom.quantity }) ||
                                                    `${t('manufacturing.produces')} ${selectedBom.quantity} ${t('manufacturing.units_per_cycle')}`}
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            )}

                            <div className="form-group">
                                <label className="form-label">
                                    {t('manufacturing.cycles')}
                                    <span className="text-error">*</span>
                                </label>
                                <input
                                    type="number"
                                    className="form-input text-lg font-bold"
                                    value={quantity}
                                    onChange={(e) => setQuantity(e.target.value)}
                                    min="1"
                                    required
                                />
                                {selectedBom && (
                                    <p className="text-sm text-success mt-2 font-medium">
                                        {t('manufacturing.total_output')}: {quantity * selectedBom.quantity} {t('common.unit')}
                                    </p>
                                )}
                            </div>

                            <div className="flex flex-col sm:flex-row gap-4 pt-4">
                                <button
                                    type="submit"
                                    className="btn btn-primary flex-1 py-3 gap-2"
                                    disabled={loading || !selectedBom}
                                >
                                    <Play size={18} />
                                    {loading ? t('common.processing') : t('manufacturing.start_production')}
                                </button>
                                <button
                                    type="button"
                                    onClick={() => navigate('/manufacturing/orders')}
                                    className="btn btn-secondary"
                                >
                                    {t('common.cancel')}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ProductionOrderForm;
