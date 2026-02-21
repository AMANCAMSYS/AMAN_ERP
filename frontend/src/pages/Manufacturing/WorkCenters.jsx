import React, { useState, useEffect } from 'react';
import { manufacturingAPI, costCentersAPI, accountingAPI } from '../../utils/api';
import { useTranslation } from 'react-i18next';
import { toastEmitter } from '../../utils/toastEmitter';
import {
    FaIndustry, FaPlus, FaEdit, FaTrash, FaSearch, FaDollarSign, FaClock
} from 'react-icons/fa';
import '../../components/ModuleStyles.css';

const WorkCenters = () => {
    const { t } = useTranslation();
    const [workCenters, setWorkCenters] = useState([]);
    const [costCenters, setCostCenters] = useState([]);
    const [accounts, setAccounts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [formData, setFormData] = useState({
        name: '',
        code: '',
        capacity_per_day: 8,
        cost_per_hour: 0,
        location: '',
        cost_center_id: '',
        default_expense_account_id: '',
        status: 'active'
    });
    const [isEditing, setIsEditing] = useState(false);
    const [editId, setEditId] = useState(null);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            setLoading(true);
            const [wcRes, ccRes, accRes] = await Promise.all([
                manufacturingAPI.listWorkCenters(),
                costCentersAPI.list(),
                accountingAPI.list() // Fetch all accounts, might need filtering
            ]);
            setWorkCenters(wcRes.data);
            setCostCenters(ccRes.data);
            // Filter for Expense accounts if possible, or just all for simplicity now
            setAccounts(accRes.data.filter(a => a.type === 'expense' || a.type === 'cogs' || true));
            setLoading(false);
        } catch (error) {
            console.error("Error fetching data:", error);
            setLoading(false);
        }
    };

    const handleOpenModal = (wc = null) => {
        if (wc) {
            setFormData({
                name: wc.name,
                code: wc.code || '',
                capacity_per_day: wc.capacity_per_day || 8,
                cost_per_hour: wc.cost_per_hour || 0,
                location: wc.location || '',
                cost_center_id: wc.cost_center_id || '',
                default_expense_account_id: wc.default_expense_account_id || '',
                status: wc.status || 'active'
            });
            setIsEditing(true);
            setEditId(wc.id);
        } else {
            setFormData({
                name: '',
                code: '',
                capacity_per_day: 8,
                cost_per_hour: 0,
                location: '',
                cost_center_id: '',
                default_expense_account_id: '',
                status: 'active'
            });
            setIsEditing(false);
            setEditId(null);
        }
        setShowModal(true);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const payload = {
                ...formData,
                cost_center_id: formData.cost_center_id ? parseInt(formData.cost_center_id) : null,
                default_expense_account_id: formData.default_expense_account_id ? parseInt(formData.default_expense_account_id) : null,
            };

            if (isEditing) {
                await manufacturingAPI.updateWorkCenter(editId, payload);
                toastEmitter.emit(t('common.updated_successfully'), 'success');
            } else {
                await manufacturingAPI.createWorkCenter(payload);
                toastEmitter.emit(t('common.created_successfully'), 'success');
            }
            setShowModal(false);
            fetchData();
        } catch (error) {
            console.error("Error saving work center:", error);
        }
    };

    if (loading) return <div className="page-center"><span className="loading"></span></div>;

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <div className="header-title">
                    <h1 className="workspace-title flex items-center gap-2">
                        <FaIndustry /> {t('manufacturing.work_centers')}
                    </h1>
                    <p className="workspace-subtitle">{t('manufacturing.work_centers_desc')}</p>
                </div>
                <div className="header-actions">
                    <button
                        onClick={() => handleOpenModal()}
                        className="btn btn-primary"
                    >
                        <FaPlus /> {t('manufacturing.add_work_center')}
                    </button>
                </div>
            </div>

            <div className="data-table-container">
                <table className="data-table">
                    <thead>
                        <tr>
                            <th>{t('common.name')}</th>
                            <th>{t('branches.code')}</th>
                            <th>{t('manufacturing.cost_per_hour')}</th>
                            <th>{t('manufacturing.daily_capacity')}</th>
                            <th>{t('manufacturing.accounting_integration')}</th>
                            <th>{t('common.status')}</th>
                            <th>{t('common.actions')}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {workCenters.map((wc) => (
                            <tr key={wc.id}>
                                <td style={{ fontWeight: 500 }}>{wc.name}</td>
                                <td>
                                    <span style={{ fontFamily: 'monospace', fontWeight: 600, fontSize: '12px', background: 'var(--bg-hover)', padding: '2px 8px', borderRadius: '4px', color: 'var(--text-secondary)' }}>{wc.code}</span>
                                </td>
                                <td style={{ color: 'var(--success)', fontWeight: 600 }}>{wc.cost_per_hour}</td>
                                <td>{wc.capacity_per_day} {t('common.hours')}</td>
                                <td>
                                    {costCenters.find(c => c.id === wc.cost_center_id)?.center_name || '-'}
                                </td>
                                <td>
                                    <span className={`badge ${wc.status === 'active' ? 'badge-success' : wc.status === 'maintenance' ? 'badge-warning' : 'badge-danger'}`}>
                                        {t(`common.${wc.status}`) || t(wc.status)}
                                    </span>
                                </td>
                                <td>
                                    <button onClick={() => handleOpenModal(wc)} className="table-action-btn" title={t('common.edit')}>
                                        <FaEdit />
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {showModal && (
                <div className="modal-overlay">
                    <div className="modal-content">
                        <div className="modal-header">
                            <h2 className="modal-title">
                                {isEditing ? t('manufacturing.edit_work_center') : t('manufacturing.add_work_center')}
                            </h2>
                            <button onClick={() => setShowModal(false)} className="btn-icon">
                                <FaTrash className="text-gray-500" />
                            </button>
                        </div>
                        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', flex: 1, overflow: 'hidden' }}>
                            <div className="modal-body">
                                <div className="row">
                                    <div className="col-md-6 form-group">
                                        <label className="form-label">{t('common.name')}</label>
                                        <input
                                            type="text"
                                            required
                                            className="form-input"
                                            value={formData.name}
                                            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                        />
                                    </div>
                                    <div className="col-md-6 form-group">
                                        <label className="form-label">{t('branches.code')}</label>
                                        <input
                                            type="text"
                                            className="form-input"
                                            value={formData.code}
                                            onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                                        />
                                    </div>
                                </div>

                                <div className="border-t pt-3 mt-3">
                                    <h3 className="text-sm font-bold text-gray-500 mb-2">{t('manufacturing.capacity_costs')}</h3>
                                </div>

                                <div className="row">
                                    <div className="col-md-6 form-group">
                                        <label className="form-label">{t('manufacturing.cost_per_hour')}</label>
                                        <div className="input-group">
                                            <span className="input-group-text"><FaDollarSign /></span>
                                            <input
                                                type="number"
                                                step="0.01"
                                                className="form-input"
                                                value={formData.cost_per_hour}
                                                onChange={(e) => setFormData({ ...formData, cost_per_hour: e.target.value })}
                                            />
                                        </div>
                                    </div>

                                    <div className="col-md-6 form-group">
                                        <label className="form-label">{t('manufacturing.daily_capacity')}</label>
                                        <div className="input-group">
                                            <span className="input-group-text"><FaClock /></span>
                                            <input
                                                type="number"
                                                step="0.5"
                                                className="form-input"
                                                value={formData.capacity_per_day}
                                                onChange={(e) => setFormData({ ...formData, capacity_per_day: e.target.value })}
                                            />
                                        </div>
                                    </div>
                                </div>

                                <div className="border-t pt-3 mt-3">
                                    <h3 className="text-sm font-bold text-gray-500 mb-2">{t('manufacturing.accounting_integration')}</h3>
                                </div>

                                <div className="row">
                                    <div className="col-md-6 form-group">
                                        <label className="form-label">{t('reports.cost_id') || t('Cost Center')}</label>
                                        <select
                                            className="form-input"
                                            value={formData.cost_center_id}
                                            onChange={(e) => setFormData({ ...formData, cost_center_id: e.target.value })}
                                        >
                                            <option value="">{t('common.select')}</option>
                                            {costCenters.map(cc => (
                                                <option key={cc.id} value={cc.id}>{cc.center_name}</option>
                                            ))}
                                        </select>
                                    </div>

                                    <div className="col-md-6 form-group">
                                        <label className="form-label">{t('manufacturing.overhead_account')}</label>
                                        <select
                                            className="form-input"
                                            value={formData.default_expense_account_id}
                                            onChange={(e) => setFormData({ ...formData, default_expense_account_id: e.target.value })}
                                        >
                                            <option value="">{t('common.select')}</option>
                                            {accounts.map(acc => (
                                                <option key={acc.id} value={acc.id}>{acc.code} - {acc.name}</option>
                                            ))}
                                        </select>
                                    </div>
                                </div>

                                <div className="border-t pt-3 mt-3">
                                    <h3 className="text-sm font-bold text-gray-500 mb-2">{t('common.details')}</h3>
                                </div>

                                <div className="row">
                                    <div className="col-md-6 form-group">
                                        <label className="form-label">{t('manufacturing.location')}</label>
                                        <input
                                            type="text"
                                            className="form-input"
                                            value={formData.location}
                                            onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                                        />
                                    </div>

                                    <div className="col-md-6 form-group">
                                        <label className="form-label">{t('common.status')}</label>
                                        <select
                                            className="form-input"
                                            value={formData.status}
                                            onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                                        >
                                            <option value="active">{t('common.active')}</option>
                                            <option value="inactive">{t('common.inactive')}</option>
                                            <option value="maintenance">{t('maintenance') || 'Maintenance'}</option>
                                        </select>
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
                                    {isEditing ? t('common.save') : t('manufacturing.add_work_center')}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default WorkCenters;
