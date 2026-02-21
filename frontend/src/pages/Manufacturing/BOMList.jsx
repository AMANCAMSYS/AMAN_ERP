import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import api from '../../utils/api';
import { Plus, Edit, Trash2, Layers } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { toastEmitter } from '../../utils/toastEmitter';
import '../../components/ModuleStyles.css';

const BOMList = () => {
    const { t } = useTranslation();
    const [boms, setBoms] = useState([]);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        fetchBOMs();
    }, []);

    const fetchBOMs = async () => {
        try {
            const res = await api.get('/manufacturing/boms');
            setBoms(res.data);
        } catch (err) {
            console.error("Failed to fetch BOMs", err);
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (bomId) => {
        if (!window.confirm(t('common.confirm_delete') || 'هل أنت متأكد من الحذف؟')) return;
        try {
            await api.delete(`/manufacturing/boms/${bomId}`);
            toastEmitter.emit(t('common.deleted_successfully') || 'تم الحذف بنجاح', 'success');
            fetchBOMs();
        } catch (err) {
            toastEmitter.emit(t('common.error_occurred') || 'حدث خطأ', 'error');
        }
    };

    if (loading) return <div className="page-center"><span className="loading"></span></div>;

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <div className="header-title">
                    <h1 className="workspace-title" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <Layers size={22} />
                        {t('manufacturing.bom_list') || 'قوائم المواد (BOM)'}
                    </h1>
                    <p className="workspace-subtitle">{t('manufacturing.bom_desc') || 'إدارة قوائم مكونات الإنتاج'}</p>
                </div>
                <div className="header-actions">
                    <button className="btn btn-primary" onClick={() => navigate('/manufacturing/boms/new')}>
                        <Plus size={16} />
                        {t('common.add_new') || 'إضافة جديدة'}
                    </button>
                </div>
            </div>

            <div className="card section-card">
                <div style={{ overflowX: 'auto' }}>
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>{t('manufacturing.bom_name') || 'اسم القائمة'}</th>
                                <th>{t('manufacturing.product') || 'المنتج النهائي'}</th>
                                <th>{t('manufacturing.quantity') || 'الكمية الناتجة'}</th>
                                <th>{t('common.status') || 'الحالة'}</th>
                                <th>{t('common.actions') || 'إجراءات'}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {boms.length === 0 ? (
                                <tr><td colSpan="6" className="text-center text-muted" style={{ padding: '32px' }}>{t('common.no_data') || 'لا توجد بيانات'}</td></tr>
                            ) : boms.map((bom) => (
                                <tr key={bom.id}>
                                    <td>{bom.id}</td>
                                    <td style={{ fontWeight: 500 }}>{bom.name}</td>
                                    <td>{bom.product_name}</td>
                                    <td>{bom.quantity}</td>
                                    <td>
                                        <span className={`badge ${bom.is_active ? 'badge-success' : 'badge-danger'}`}>
                                            {bom.is_active ? (t('common.active') || 'نشط') : (t('common.inactive') || 'غير نشط')}
                                        </span>
                                    </td>
                                    <td>
                                        <div style={{ display: 'flex', gap: '8px' }}>
                                            <button className="table-action-btn" title={t('common.edit')} onClick={() => navigate(`/manufacturing/boms/${bom.id}`)}>
                                                <Edit size={15} />
                                            </button>
                                            <button className="table-action-btn" title={t('common.delete')} onClick={() => handleDelete(bom.id)} style={{ color: 'var(--danger)' }}>
                                                <Trash2 size={15} />
                                            </button>
                                        </div>
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

export default BOMList;

