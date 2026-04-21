import React, { useState, useEffect } from 'react';
import { manufacturingAPI, inventoryAPI } from '../../utils/api';
import { useTranslation } from 'react-i18next';
import { toastEmitter } from '../../utils/toastEmitter';
import {
    FaRoute, FaPlus, FaEdit, FaTrash, FaTimesCircle, FaCogs, FaClock, FaListOl
} from 'react-icons/fa';
import '../../components/ModuleStyles.css';
import BackButton from '../../components/common/BackButton';
import { PageLoading } from '../../components/common/LoadingStates'

const Routings = () => {
    const { t } = useTranslation();
    const [routes, setRoutes] = useState([]);
    const [products, setProducts] = useState([]);
    const [workCenters, setWorkCenters] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);

    const [formData, setFormData] = useState({
        name: '',
        product_id: '',
        description: '',
        is_active: true,
        operations: []
    });

    // Operation form state for adding new ops inside modal
    const [newOp, setNewOp] = useState({
        sequence: 10,
        work_center_id: '',
        description: '',
        setup_time: 0,
        cycle_time: 0
    });

    const [isEditing, setIsEditing] = useState(false);
    const [editId, setEditId] = useState(null);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            setLoading(true);
            const [routesRes, productsRes, wcRes] = await Promise.all([
                manufacturingAPI.listRoutes(),
                inventoryAPI.listProducts({ limit: 1000 }), // Get all products for selection
                manufacturingAPI.listWorkCenters()
            ]);
            setRoutes(routesRes.data);
            setProducts(productsRes.data.products || []); // Adjust based on actual API response structure
            setWorkCenters(wcRes.data);
            setLoading(false);
        } catch (error) {
            toastEmitter.emit(t('common.error'), 'error');
            setLoading(false);
        }
    };

    const handleOpenModal = (route = null) => {
        if (route) {
            setFormData({
                name: route.name,
                product_id: route.product_id || '',
                description: route.description || '',
                is_active: route.is_active,
                operations: route.operations || []
            });
            setIsEditing(true);
            setEditId(route.id);
        } else {
            setFormData({
                name: '',
                product_id: '',
                description: '',
                is_active: true,
                operations: []
            });
            setNewOp({ sequence: 10, work_center_id: '', description: '', setup_time: 0, cycle_time: 0 });
            setIsEditing(false);
            setEditId(null);
        }
        setShowModal(true);
    };

    const handleAddOperation = () => {
        if (!newOp.work_center_id) {
            toastEmitter.emit(t('manufacturing.validation.select_work_center'), 'warning');
            return;
        }
        const wc = workCenters.find(w => w.id === parseInt(newOp.work_center_id));
        const op = { ...newOp, work_center_name: wc ? wc.name : '' };

        setFormData({
            ...formData,
            operations: [...formData.operations, op].sort((a, b) => a.sequence - b.sequence)
        });

        // Reset new op form for next entry, increment sequence
        setNewOp({
            ...newOp,
            sequence: parseInt(newOp.sequence) + 10,
            work_center_id: '',
            description: '',
            setup_time: 0,
            cycle_time: 0
        });
    };

    const handleRemoveOperation = (index) => {
        const updatedOps = [...formData.operations];
        updatedOps.splice(index, 1);
        setFormData({ ...formData, operations: updatedOps });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const payload = {
                ...formData,
                product_id: formData.product_id ? parseInt(formData.product_id) : null,
            };

            if (isEditing) {
                // Update not fully implemented in backend for ops yet, but assuming full replace or smart update
                // For now, let's just create logic. Assuming updateRoute exists and handles this.
                await manufacturingAPI.updateRoute(editId, payload);
                toastEmitter.emit(t('common.updated_successfully'), 'success');
            } else {
                await manufacturingAPI.createRoute(payload);
                toastEmitter.emit(t('common.created_successfully'), 'success');
            }
            setShowModal(false);
            fetchData();
        } catch (error) {
            toastEmitter.emit(t('common.error'), 'error');
        }
    };

    if (loading) return <PageLoading />;

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <div className="header-title">
                    <h1 className="workspace-title flex items-center gap-2">
                        <FaRoute /> {t('manufacturing.routings')}
                    </h1>
                    <p className="workspace-subtitle">{t('manufacturing.routings_desc')}</p>
                </div>
                <div className="header-actions">
                    <button
                        onClick={() => handleOpenModal()}
                        className="btn btn-primary"
                    >
                        <FaPlus /> {t('manufacturing.add_routing')}
                    </button>
                </div>
            </div>

            <div className="modules-grid">
                {routes.map((route) => (
                    <div key={route.id} className="section-card" style={{ cursor: 'default' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                            <div>
                                <h3 style={{ fontWeight: 700, fontSize: '15px', color: 'var(--text-main)', marginBottom: '2px' }}>{route.name}</h3>
                                <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>{route.product_name || t('manufacturing.no_product_linked')}</p>
                            </div>
                            <button onClick={() => handleOpenModal(route)} className="table-action-btn" title={t('common.edit')}>
                                <FaEdit />
                            </button>
                        </div>

                        <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '12px', minHeight: '18px' }}>
                            {route.description}
                        </p>

                        <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '10px' }}>
                            <p style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                                <FaCogs /> {t('manufacturing.operations')} ({route.operations?.length || 0})
                            </p>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                                {route.operations?.slice(0, 3).map((op, idx) => (
                                    <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', background: 'var(--bg-hover)', padding: '4px 8px', borderRadius: '4px' }}>
                                        <span><span style={{ fontFamily: 'monospace', fontWeight: 700 }}>{op.sequence}</span> {op.work_center_name}</span>
                                        <span style={{ color: 'var(--text-muted)' }}>{op.cycle_time}m</span>
                                    </div>
                                ))}
                                {(route.operations?.length > 3) && (
                                    <div style={{ textAlign: 'center', fontSize: '12px', color: 'var(--primary)' }}>+{route.operations.length - 3} {t('common.more')}</div>
                                )}
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {showModal && (
                <div className="modal-overlay">
                    <div className="modal-content large">
                        <div className="modal-header">
                            <h2 className="modal-title">
                                {isEditing ? t('manufacturing.edit_routing') : t('manufacturing.add_routing')}
                            </h2>
                            <button onClick={() => setShowModal(false)} className="btn-icon">
                                <FaTimesCircle />
                            </button>
                        </div>
                        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', flex: 1, overflow: 'hidden' }}>
                            <div className="modal-body">
                                <div className="row">
                                    <div className="col-md-6 form-group">
                                        <label className="form-label">{t('manufacturing.routing_name')}</label>
                                        <input
                                            type="text"
                                            required
                                            className="form-input"
                                            value={formData.name}
                                            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                            placeholder={t('manufacturing.routing_name_placeholder')}
                                        />
                                    </div>
                                    <div className="col-md-6 form-group">
                                        <label className="form-label">{t('manufacturing.finished_product')}</label>
                                        <select
                                            className="form-input"
                                            value={formData.product_id}
                                            onChange={(e) => setFormData({ ...formData, product_id: e.target.value })}
                                        >
                                            <option value="">{t('common.select')}</option>
                                            {products.map(p => (
                                                <option key={p.id} value={p.id}>{p.name_ar} ({p.sku})</option>
                                            ))}
                                        </select>
                                    </div>
                                </div>
                                <div className="form-group">
                                    <label className="form-label">{t('common.description')}</label>
                                    <textarea
                                        className="form-input"
                                        rows="2"
                                        value={formData.description}
                                        onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                                    />
                                </div>

                                {/* Operations Section */}
                                <div style={{ border: '1px solid var(--border-color)', borderRadius: '8px', padding: '12px', background: 'var(--bg-hover)', marginTop: '12px' }}>
                                    <h3 style={{ fontWeight: 700, fontSize: '13px', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '10px' }}>
                                        <FaListOl /> {t('manufacturing.operations_sequence')}
                                    </h3>

                                    {/* List of current operations */}
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginBottom: '12px' }}>
                                        {formData.operations.length === 0 && (
                                            <p style={{ fontSize: '13px', color: 'var(--text-muted)', textAlign: 'center', padding: '12px', fontStyle: 'italic' }}>{t('common.no_data')}</p>
                                        )}
                                        {formData.operations.map((op, idx) => (
                                            <div key={idx} style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '8px', background: 'var(--bg-primary)', padding: '8px 12px', borderRadius: '6px', border: '1px solid var(--border-color)' }}>
                                                <div style={{ fontFamily: 'monospace', fontWeight: 700, minWidth: '32px', textAlign: 'center', background: 'var(--bg-hover)', borderRadius: '4px', padding: '2px 6px', color: 'var(--primary)' }}>{op.sequence}</div>
                                                <div style={{ flex: 1, fontWeight: 600, fontSize: '14px' }}>{op.work_center_name || workCenters.find(w => w.id === parseInt(op.work_center_id))?.name}</div>
                                                <div style={{ width: '130px', fontSize: '13px', color: 'var(--text-secondary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={op.description}>{op.description}</div>
                                                <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}><span style={{ fontWeight: 600 }}>{t('manufacturing.setup_time')}:</span> {op.setup_time}m</div>
                                                <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}><span style={{ fontWeight: 600 }}>{t('manufacturing.run_time')}:</span> {op.cycle_time}m</div>
                                                <button type="button" onClick={() => handleRemoveOperation(idx)} className="table-action-btn" style={{ color: 'var(--danger)' }}>
                                                    <FaTrash />
                                                </button>
                                            </div>
                                        ))}
                                    </div>

                                    {/* Add New Operation Form */}
                                    <div className="border-t pt-3">
                                        <div className="row">
                                            <div className="col-md-2 form-group">
                                                <label className="text-xs font-bold text-gray-500">{t('manufacturing.operations_sequence')}</label>
                                                <input type="number" className="form-input text-sm" value={newOp.sequence} onChange={e => setNewOp({ ...newOp, sequence: e.target.value })} />
                                            </div>
                                            <div className="col-md-4 form-group">
                                                <label className="text-xs font-bold text-gray-500">{t('manufacturing.work_center')}</label>
                                                <select className="form-input text-sm" value={newOp.work_center_id} onChange={e => setNewOp({ ...newOp, work_center_id: e.target.value })}>
                                                    <option value="">{t('common.select')}</option>
                                                    {workCenters.map(wc => (
                                                        <option key={wc.id} value={wc.id}>{wc.name}</option>
                                                    ))}
                                                </select>
                                            </div>
                                            <div className="col-md-6 form-group">
                                                <label className="text-xs font-bold text-gray-500">{t('common.description')}</label>
                                                <input type="text" className="form-input text-sm" value={newOp.description} onChange={e => setNewOp({ ...newOp, description: e.target.value })} />
                                            </div>
                                        </div>
                                        <div className="row">
                                            <div className="col-md-3 form-group">
                                                <label className="text-xs font-bold text-gray-500">{t('manufacturing.setup_time')}</label>
                                                <input type="number" className="form-input text-sm" value={newOp.setup_time} onChange={e => setNewOp({ ...newOp, setup_time: e.target.value })} />
                                            </div>
                                            <div className="col-md-3 form-group">
                                                <label className="text-xs font-bold text-gray-500">{t('manufacturing.cycle_time')}</label>
                                                <input type="number" className="form-input text-sm" value={newOp.cycle_time} onChange={e => setNewOp({ ...newOp, cycle_time: e.target.value })} />
                                            </div>
                                            <div className="col-md-6 flex items-end justify-end pb-1">
                                                <button type="button" onClick={handleAddOperation} className="btn btn-sm btn-success flex items-center gap-1">
                                                    <FaPlus /> {t('common.add')}
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div className="modal-footer">
                                <button
                                    type="button"
                                    onClick={() => setShowModal(false)}
                                    className="btn btn-secondary"
                                >
                                    {t('common.cancel')}
                                </button>
                                <button
                                    type="submit"
                                    className="btn btn-primary"
                                >
                                    {isEditing ? t('common.save') : t('manufacturing.add_routing')}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Routings;
