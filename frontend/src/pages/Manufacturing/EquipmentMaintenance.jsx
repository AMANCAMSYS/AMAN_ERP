import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { FaTools, FaPlus, FaSearch, FaHistory, FaCalendarCheck, FaExclamationTriangle } from 'react-icons/fa';
import { manufacturingAPI } from '../../utils/api';
import { toastEmitter } from '../../utils/toastEmitter';
import '../../components/ModuleStyles.css';
import DateInput from '../../components/common/DateInput';
const EquipmentMaintenance = () => {
    const { t } = useTranslation();
    const [activeTab, setActiveTab] = useState('equipment');
    const [equipment, setEquipment] = useState([]);
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');

    // Modal States
    const [showEquipModal, setShowEquipModal] = useState(false);
    const [showLogModal, setShowLogModal] = useState(false);
    const [selectedEquipment, setSelectedEquipment] = useState(null);

    // Form Data
    const [equipForm, setEquipForm] = useState({
        name: '', code: '', work_center_id: '', status: 'active',
        purchase_date: '', last_maintenance_date: '', next_maintenance_date: '', notes: ''
    });

    const [logForm, setLogForm] = useState({
        equipment_id: '', maintenance_type: 'preventive', description: '',
        cost: 0, performed_by: '', maintenance_date: new Date().toISOString().split('T')[0],
        next_due_date: '', status: 'completed', notes: ''
    });

    // Fetch Data
    useEffect(() => {
        fetchData();
    }, [activeTab]);

    const fetchData = async () => {
        setLoading(true);
        try {
            if (activeTab === 'equipment') {
                const res = await manufacturingAPI.listEquipment();
                setEquipment(res.data);
            } else {
                const res = await manufacturingAPI.listMaintenanceLogs();
                setLogs(res.data);
                if (equipment.length === 0) {
                    const equipRes = await manufacturingAPI.listEquipment();
                    setEquipment(equipRes.data);
                }
            }
        } catch (error) {
            console.error("Error fetching data:", error);
            toastEmitter.emit(t('error_fetching_data'), 'error');
        } finally {
            setLoading(false);
        }
    };

    const handleCreateEquipment = async (e) => {
        e.preventDefault();
        try {
            await manufacturingAPI.createEquipment(equipForm);
            toastEmitter.emit(t('success_created'), 'success');
            setShowEquipModal(false);
            setEquipForm({
                name: '', code: '', work_center_id: '', status: 'active',
                purchase_date: '', last_maintenance_date: '', next_maintenance_date: '', notes: ''
            });
            fetchData();
        } catch (error) {
            console.error(error);
        }
    };

    const handleCreateLog = async (e) => {
        e.preventDefault();
        try {
            await manufacturingAPI.createMaintenanceLog(logForm);
            toastEmitter.emit(t('success_created'), 'success');
            setShowLogModal(false);
            setLogForm({
                equipment_id: '', maintenance_type: 'preventive', description: '',
                cost: 0, performed_by: '', maintenance_date: new Date().toISOString().split('T')[0],
                next_due_date: '', status: 'completed', notes: ''
            });
            fetchData();
        } catch (error) {
            console.error(error);
        }
    };

    const getStatusColor = (status) => {
        switch (status) {
            case 'active': return 'bg-green-100 text-green-800';
            case 'maintenance': return 'bg-yellow-100 text-yellow-800';
            case 'broken': return 'bg-red-100 text-red-800';
            case 'retired': return 'bg-gray-100 text-gray-800';
            default: return 'bg-gray-100';
        }
    };

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <div className="header-title">
                    <h1 className="workspace-title flex items-center gap-2">
                        <FaTools /> {t('manufacturing.equipment_maintenance', 'Equipment & Maintenance')}
                    </h1>
                    <p className="workspace-subtitle">{t('manufacturing.equip_desc', 'Manage machinery and track maintenance logs.')}</p>
                </div>
                <div className="header-actions">
                    {activeTab === 'equipment' ? (
                        <button onClick={() => setShowEquipModal(true)} className="btn btn-primary">
                            <FaPlus /> {t('manufacturing.add_equipment')}
                        </button>
                    ) : (
                        <button onClick={() => setShowLogModal(true)} className="btn btn-primary">
                            <FaPlus /> {t('manufacturing.log_maintenance')}
                        </button>
                    )}
                </div>
            </div>

            {/* Tabs */}
            <div className="tabs" style={{ marginBottom: '24px', width: 'fit-content' }}>
                <button
                    className={`tab ${activeTab === 'equipment' ? 'active' : ''}`}
                    onClick={() => setActiveTab('equipment')}
                >
                    {t('manufacturing.equipment_list')}
                </button>
                <button
                    className={`tab ${activeTab === 'logs' ? 'active' : ''}`}
                    onClick={() => setActiveTab('logs')}
                >
                    {t('manufacturing.maintenance_logs')}
                </button>
            </div>

            {loading ? (
                <div className="page-center"><span className="loading"></span></div>
            ) : (
                <>
                    {activeTab === 'equipment' && (
                        <div className="data-table-container">
                            <table className="data-table">
                                <thead>
                                    <tr>
                                        <th>{t('common.name')}</th>
                                        <th>{t('common.code')}</th>
                                        <th>{t('common.status')}</th>
                                        <th>{t('manufacturing.last_maintenance')}</th>
                                        <th>{t('manufacturing.next_due')}</th>
                                        <th>{t('common.actions')}</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {equipment.length === 0 ? (
                                        <tr><td colSpan="6" className="text-center py-8 text-gray-500 italic">{t('common.no_data')}</td></tr>
                                    ) : (
                                        equipment.map(eq => (
                                            <tr key={eq.id}>
                                                <td className="font-bold">{eq.name}</td>
                                                <td>
                                                    <span style={{ fontFamily: 'monospace', fontWeight: 600, fontSize: '12px', background: 'var(--bg-hover)', padding: '2px 8px', borderRadius: '4px', color: 'var(--text-secondary)' }}>{eq.code}</span>
                                                </td>
                                                <td>
                                                    <span className={`badge ${eq.status === 'active' ? 'badge-success' :
                                                            eq.status === 'maintenance' ? 'badge-warning' :
                                                                eq.status === 'broken' ? 'badge-danger' :
                                                                    'badge-secondary'
                                                        }`}>
                                                        {t(`status.${eq.status}`, eq.status)}
                                                    </span>
                                                </td>
                                                <td>{eq.last_maintenance_date || '-'}</td>
                                                <td style={{ color: (eq.next_maintenance_date && new Date(eq.next_maintenance_date) < new Date()) ? 'var(--danger)' : undefined, fontWeight: (eq.next_maintenance_date && new Date(eq.next_maintenance_date) < new Date()) ? 700 : undefined }}>
                                                    {eq.next_maintenance_date || '-'}
                                                </td>
                                                <td>
                                                    <button onClick={() => {
                                                        setActiveTab('logs');
                                                    }} className="table-action-btn" title={t('history')}>
                                                        <FaHistory />
                                                    </button>
                                                </td>
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                            </table>
                        </div>
                    )}

                    {activeTab === 'logs' && (
                        <div className="data-table-container">
                            <table className="data-table">
                                <thead>
                                    <tr>
                                        <th>{t('common.date')}</th>
                                        <th>{t('manufacturing.equipment')}</th>
                                        <th>{t('common.type')}</th>
                                        <th>{t('common.description')}</th>
                                        <th>{t('common.cost')}</th>
                                        <th>{t('common.status')}</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {logs.length === 0 ? (
                                        <tr><td colSpan="6" className="text-center py-8 text-gray-500 italic">{t('common.no_data')}</td></tr>
                                    ) : (
                                        logs.map(log => (
                                            <tr key={log.id}>
                                                <td>{log.maintenance_date}</td>
                                                <td className="font-bold">{log.equipment_name}</td>
                                                <td>{log.maintenance_type}</td>
                                                <td>{log.description}</td>
                                                <td>{log.cost}</td>
                                                <td>
                                                    <span className="badge badge-ghost">
                                                        {t(`status.${log.status}`, log.status)}
                                                    </span>
                                                </td>
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                            </table>
                        </div>
                    )}
                </>
            )}

            {/* Equipment Modal */}
            {showEquipModal && (
                <div className="modal-overlay">
                    <div className="modal-content">
                        <div className="modal-header">
                            <h2 className="modal-title">{t('manufacturing.add_equipment')}</h2>
                            <button onClick={() => setShowEquipModal(false)} className="btn-icon">✕</button>
                        </div>
                        <form onSubmit={handleCreateEquipment}>
                            <div className="modal-body">
                                <div className="form-group">
                                    <label className="form-label">{t('common.name')}</label>
                                    <input type="text" className="form-control-sm w-full" required
                                        value={equipForm.name} onChange={e => setEquipForm({ ...equipForm, name: e.target.value })} />
                                </div>
                                <div className="form-group">
                                    <label className="form-label">{t('common.code')}</label>
                                    <input type="text" className="form-control-sm w-full" required
                                        value={equipForm.code} onChange={e => setEquipForm({ ...equipForm, code: e.target.value })} />
                                </div>
                                <div className="form-group">
                                    <label className="form-label">{t('common.status')}</label>
                                    <select className="form-select-sm w-full" value={equipForm.status} onChange={e => setEquipForm({ ...equipForm, status: e.target.value })}>
                                        <option value="active">Active</option>
                                        <option value="maintenance">Maintenance</option>
                                        <option value="broken">Broken</option>
                                        <option value="retired">Retired</option>
                                    </select>
                                </div>
                                <div className="form-group">
                                    <label className="form-label">{t('manufacturing.next_maintenance_date')}</label>
                                    <DateInput className="form-control-sm w-full"
                                        value={equipForm.next_maintenance_date} onChange={e => setEquipForm({ ...equipForm, next_maintenance_date: e.target.value })} />
                                </div>
                            </div>
                            <div className="modal-footer">
                                <button type="button" onClick={() => setShowEquipModal(false)} className="btn btn-secondary">{t('common.cancel')}</button>
                                <button type="submit" className="btn btn-primary">{t('common.save')}</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Log Modal */}
            {showLogModal && (
                <div className="modal-overlay">
                    <div className="modal-content">
                        <div className="modal-header">
                            <h2 className="modal-title">{t('manufacturing.log_maintenance')}</h2>
                            <button onClick={() => setShowLogModal(false)} className="btn-icon">✕</button>
                        </div>
                        <form onSubmit={handleCreateLog}>
                            <div className="modal-body">
                                <div className="form-group">
                                    <label className="form-label">{t('manufacturing.equipment')}</label>
                                    <select className="form-input" required value={logForm.equipment_id} onChange={e => setLogForm({ ...logForm, equipment_id: e.target.value })}>
                                        <option value="">{t('common.select')}</option>
                                        {equipment.map(eq => (
                                            <option key={eq.id} value={eq.id}>{eq.name} ({eq.code})</option>
                                        ))}
                                    </select>
                                </div>
                                <div className="row">
                                    <div className="col-md-6 form-group">
                                        <label className="form-label">{t('common.type')}</label>
                                        <select className="form-input" value={logForm.maintenance_type} onChange={e => setLogForm({ ...logForm, maintenance_type: e.target.value })}>
                                            <option value="preventive">Preventive</option>
                                            <option value="corrective">Corrective</option>
                                            <option value="breakdown">Breakdown</option>
                                        </select>
                                    </div>
                                    <div className="col-md-6 form-group">
                                        <label className="form-label">{t('common.date')}</label>
                                        <DateInput className="form-input" required
                                            value={logForm.maintenance_date} onChange={e => setLogForm({ ...logForm, maintenance_date: e.target.value })} />
                                    </div>
                                </div>
                                <div className="form-group">
                                    <label className="form-label">{t('common.description')}</label>
                                    <textarea className="form-input" required
                                        value={logForm.description} onChange={e => setLogForm({ ...logForm, description: e.target.value })} />
                                </div>
                                <div className="row">
                                    <div className="col-md-6 form-group">
                                        <label className="form-label">{t('common.cost')}</label>
                                        <input type="number" className="form-input" min="0" step="0.01"
                                            value={logForm.cost} onChange={e => setLogForm({ ...logForm, cost: e.target.value })} />
                                    </div>
                                    <div className="col-md-6 form-group">
                                        <label className="form-label">{t('manufacturing.next_due_date')}</label>
                                        <DateInput className="form-input"
                                            value={logForm.next_due_date} onChange={e => setLogForm({ ...logForm, next_due_date: e.target.value })} />
                                    </div>
                                </div>
                            </div>
                            <div className="modal-footer">
                                <button type="button" onClick={() => setShowLogModal(false)} className="btn btn-secondary">{t('common.cancel')}</button>
                                <button type="submit" className="btn btn-primary">{t('common.save')}</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default EquipmentMaintenance;
