
import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Plus, Search, Edit2, Trash2, X } from 'lucide-react';
import { costCentersAPI } from '../../../utils/api';
import { toastEmitter } from '../../../utils/toastEmitter';
import { useNavigate } from 'react-router-dom';
import BackButton from '../../../components/common/BackButton';

const CostCenterList = () => {
    const { t } = useTranslation();
    const navigate = useNavigate();
    const [costCenters, setCostCenters] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');
    const [editingId, setEditingId] = useState(null);

    const [formData, setFormData] = useState({
        center_code: '',
        center_name: '',
        center_name_en: '',
        is_active: true
    });

    useEffect(() => {
        fetchCostCenters();
    }, []);

    const fetchCostCenters = async () => {
        try {
            setLoading(true);
            const response = await costCentersAPI.list();
            setCostCenters(response.data);
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            if (editingId) {
                await costCentersAPI.update(editingId, formData);
                toastEmitter.emit(t('cost_centers.updated'), 'success');
            } else {
                await costCentersAPI.create(formData);
                toastEmitter.emit(t('cost_centers.created'), 'success');
            }
            setShowModal(false);
            fetchCostCenters();
            resetForm();
        } catch (error) {
            console.error(error);
        }
    };

    const handleDelete = async (id) => {
        if (!window.confirm(t('common.confirm_delete'))) return;
        try {
            await costCentersAPI.delete(id);
            toastEmitter.emit(t('cost_centers.deleted'), 'success');
            fetchCostCenters();
        } catch (error) {
            console.error(error);
        }
    };

    const handleEdit = (center) => {
        setEditingId(center.id);
        setFormData({
            center_code: center.center_code || '',
            center_name: center.center_name,
            center_name_en: center.center_name_en || '',
            is_active: center.is_active
        });
        setShowModal(true);
    };

    const resetForm = () => {
        setEditingId(null);
        setFormData({
            center_code: '',
            center_name: '',
            center_name_en: '',
            is_active: true
        });
    };

    const filteredCenters = costCenters.filter(c =>
        c.center_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (c.center_code && c.center_code.toLowerCase().includes(searchTerm.toLowerCase()))
    );

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                        <BackButton />
                        <div>
                            <h1 className="workspace-title">{t('cost_centers.title')}</h1>
                            <p className="workspace-subtitle">{t('cost_centers.subtitle')}</p>
                        </div>
                    </div>
                    <button
                        onClick={() => { resetForm(); setShowModal(true); }}
                        className="btn btn-primary"
                    >
                        <span style={{ marginLeft: '8px' }}>+</span>
                        {t('cost_centers.add')}
                    </button>
                </div>
            </div>

            <div className="mb-4" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div className="search-box">
                    <Search size={16} />
                    <input
                        type="text"
                        name="search"
                        id="search"
                        placeholder={t('common.search')}
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        autoComplete="off"
                    />
                </div>
            </div>

            <div className="data-table-container">
                <table className="data-table">
                    <thead>
                        <tr>
                            <th style={{ width: '20%' }}>{t('cost_centers.code')}</th>
                            <th style={{ width: '40%' }}>{t('cost_centers.name')}</th>
                            <th style={{ width: '20%' }}>{t('cost_centers.status')}</th>
                            <th style={{ width: '20%' }}>{t('common.actions')}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {loading ? (
                            <tr><td colSpan="4" className="text-center py-4">{t('common.loading')}</td></tr>
                        ) : filteredCenters.length === 0 ? (
                            <tr><td colSpan="4" className="text-center py-4 text-muted">{t('common.no_data')}</td></tr>
                        ) : (
                            filteredCenters.map((center) => (
                                <tr key={center.id}>
                                    <td className="fw-medium">{center.center_code || '-'}</td>
                                    <td>
                                        <div style={{ fontWeight: '600', color: 'var(--text-primary)' }}>{center.center_name}</div>
                                        <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>{center.center_name_en}</div>
                                    </td>
                                    <td>
                                        <span className={`badge ${center.is_active ? 'badge-success' : 'badge-danger'}`}>
                                            {center.is_active ? t('common.active') : t('common.inactive')}
                                        </span>
                                    </td>
                                    <td>
                                        <div className="d-flex gap-2">
                                            <button
                                                onClick={(e) => { e.stopPropagation(); handleEdit(center); }}
                                                className="table-action-btn"
                                                title={t('common.edit')}
                                            >
                                                <Edit2 size={16} />
                                            </button>
                                            <button
                                                onClick={(e) => { e.stopPropagation(); handleDelete(center.id); }}
                                                className="table-action-btn"
                                                style={{ color: 'var(--danger)' }}
                                                title={t('common.delete')}
                                            >
                                                <Trash2 size={16} />
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            {showModal && (
                <div className="modal-overlay">
                    <div className="modal-content" style={{ maxWidth: '500px' }}>
                        <div className="modal-header">
                            <h2 className="modal-title">
                                {editingId ? t('cost_centers.edit') : t('cost_centers.new')}
                            </h2>
                            <button onClick={() => setShowModal(false)} className="btn-icon" style={{ background: 'transparent' }}>
                                <X size={20} />
                            </button>
                        </div>
                        <form onSubmit={handleSubmit}>
                            <div className="modal-body">
                                <div className="form-group">
                                    <label className="form-label" htmlFor="center_code">{t('cost_centers.code')}</label>
                                    <input
                                        type="text"
                                        id="center_code"
                                        name="center_code"
                                        value={formData.center_code}
                                        onChange={(e) => setFormData({ ...formData, center_code: e.target.value })}
                                        className="form-input"
                                        autoComplete="off"
                                    />
                                </div>
                                <div className="form-group">
                                    <label className="form-label" htmlFor="center_name">{t('cost_centers.name_ar')} <span className="text-danger">*</span></label>
                                    <input
                                        type="text"
                                        id="center_name"
                                        name="center_name"
                                        required
                                        value={formData.center_name}
                                        onChange={(e) => setFormData({ ...formData, center_name: e.target.value })}
                                        className="form-input"
                                        autoComplete="off"
                                    />
                                </div>
                                <div className="form-group">
                                    <label className="form-label" htmlFor="center_name_en">{t('cost_centers.name_en')}</label>
                                    <input
                                        type="text"
                                        id="center_name_en"
                                        name="center_name_en"
                                        value={formData.center_name_en}
                                        onChange={(e) => setFormData({ ...formData, center_name_en: e.target.value })}
                                        className="form-input"
                                        autoComplete="off"
                                    />
                                </div>
                                <div className="d-flex align-items-center gap-2 mt-4">
                                    <input
                                        type="checkbox"
                                        id="is_active"
                                        checked={formData.is_active}
                                        onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                                        style={{ width: '18px', height: '18px' }}
                                    />
                                    <label htmlFor="is_active" className="mb-0" style={{ cursor: 'pointer' }}>{t('common.active')}</label>
                                </div>
                            </div>
                            <div className="modal-footer">
                                <button type="button" onClick={() => setShowModal(false)} className="btn" style={{ background: 'var(--bg-hover)' }}>
                                    {t('common.cancel')}
                                </button>
                                <button type="submit" className="btn btn-primary">
                                    {t('common.save')}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default CostCenterList;
