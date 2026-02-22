
import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Plus, Trash2, Briefcase } from 'lucide-react';
import { hrAPI } from '../../utils/api';
import { toastEmitter } from '../../utils/toastEmitter';
import BackButton from '../../components/common/BackButton';

const PositionList = () => {
    const { t } = useTranslation();
    const [positions, setPositions] = useState([]);
    const [departments, setDepartments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);

    const [formData, setFormData] = useState({
        position_name: '',
        department_id: ''
    });

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            const [posRes, deptRes] = await Promise.all([
                hrAPI.listPositions(),
                hrAPI.listDepartments()
            ]);
            setPositions(posRes.data);
            setDepartments(deptRes.data);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            await hrAPI.createPosition(formData);
            setShowModal(false);
            fetchData();
            setFormData({ position_name: '', department_id: '' });
        } catch (err) {
            toastEmitter.emit("Error creating position: " + (err.response?.data?.detail || err.message), 'error');
        }
    };

    const handleDelete = async (id) => {
        if (!window.confirm(t("hr.positions.confirm_delete"))) return;
        try {
            await hrAPI.deletePosition(id);
            fetchData();
        } catch (err) {
            toastEmitter.emit("Error deleting position: " + (err.response?.data?.detail || err.message), 'error');
        }
    };

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <div className="header-title">
                    <h1 className="workspace-title">{t("hr.positions.title")}</h1>
                    <p className="workspace-subtitle">{t("hr.positions.subtitle")}</p>
                </div>
                <div className="header-actions">
                    <button className="btn btn-primary" onClick={() => setShowModal(true)}>
                        <Plus size={18} className="ms-2" />
                        {t('hr.positions.add')}
                    </button>
                </div>
            </div>

            <div className="card shadow-sm border-0">
                <div className="card-body p-0">
                    <table className="data-table mb-0">
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>{t("hr.positions.job_title")}</th>
                                <th>{t("hr.positions.department")}</th>
                                <th style={{ width: '100px' }}>{t("common.actions")}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {loading ? (
                                <tr><td colSpan="4" className="text-center p-4">{t("common.loading")}</td></tr>
                            ) : positions.length === 0 ? (
                                <tr>
                                    <td colSpan="4" className="text-center p-5">
                                        <div className="text-muted mb-3" style={{ fontSize: '30px' }}>💼</div>
                                        <p>{t("hr.positions.no_positions")}</p>
                                    </td>
                                </tr>
                            ) : (
                                positions.map((pos, index) => (
                                    <tr key={pos.id} className="hover-row">
                                        <td>{index + 1}</td>
                                        <td className="fw-bold">{pos.position_name}</td>
                                        <td>
                                            {pos.department_name ? (
                                                <span className="badge bg-light text-dark border">
                                                    {pos.department_name}
                                                </span>
                                            ) : '-'}
                                        </td>
                                        <td>
                                            <button
                                                className="btn btn-icon text-danger"
                                                onClick={() => handleDelete(pos.id)}
                                                title={t("common.delete")}
                                            >
                                                <Trash2 size={16} />
                                            </button>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Create Modal */}
            {showModal && (
                <div className="modal-overlay">
                    <div className="modal-content" style={{ maxWidth: '400px' }}>
                        <div className="modal-header">
                            <h3 className="modal-title">{t("hr.positions.add_new")}</h3>
                            <button className="btn-icon" onClick={() => setShowModal(false)}>×</button>
                        </div>
                        <form onSubmit={handleSubmit}>
                            <div className="modal-body">
                                <div className="mb-3">
                                    <label className="form-label" htmlFor="position_name">{t("hr.positions.job_title")}</label>
                                    <input
                                        type="text"
                                        id="position_name"
                                        name="position_name"
                                        className="form-input"
                                        placeholder={t("hr.positions.title_placeholder")}
                                        required
                                        value={formData.position_name}
                                        onChange={e => setFormData({ ...formData, position_name: e.target.value })}
                                        autoComplete="off"
                                    />
                                </div>
                                <div className="mb-3">
                                    <label className="form-label" htmlFor="department_id">{t("hr.positions.department")}</label>
                                    <select
                                        id="department_id"
                                        name="department_id"
                                        className="form-select"
                                        value={formData.department_id}
                                        onChange={e => setFormData({ ...formData, department_id: e.target.value })}
                                    >
                                        <option value="">{t("hr.positions.select_dept")}</option>
                                        {departments.map(dept => (
                                            <option key={dept.id} value={dept.id}>{dept.department_name}</option>
                                        ))}
                                    </select>
                                </div>
                            </div>
                            <div className="modal-footer">
                                <button type="button" className="btn btn-outline-secondary" onClick={() => setShowModal(false)}>{t("common.cancel")}</button>
                                <button type="submit" className="btn btn-primary">{t("common.save")}</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default PositionList;
