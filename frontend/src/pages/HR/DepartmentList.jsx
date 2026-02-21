
import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Plus, Trash2, Building } from 'lucide-react';
import { hrAPI } from '../../utils/api';
import { toastEmitter } from '../../utils/toastEmitter';

const DepartmentList = () => {
    const { t } = useTranslation();
    const [departments, setDepartments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);

    const [formData, setFormData] = useState({
        department_name: ''
    });

    useEffect(() => {
        fetchDepartments();
    }, []);

    const fetchDepartments = async () => {
        try {
            const res = await hrAPI.listDepartments();
            setDepartments(res.data);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            await hrAPI.createDepartment(formData);
            setShowModal(false);
            fetchDepartments();
            setFormData({ department_name: '' });
        } catch (err) {
            toastEmitter.emit("Error creating department: " + (err.response?.data?.detail || err.message), 'error');
        }
    };

    const handleDelete = async (id) => {
        if (!window.confirm(t("hr.departments.confirm_delete"))) return;
        try {
            await hrAPI.deleteDepartment(id);
            fetchDepartments();
        } catch (err) {
            toastEmitter.emit("Error deleting department: " + (err.response?.data?.detail || err.message), 'error');
        }
    };

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <div className="header-title">
                    <h1 className="workspace-title">{t("hr.departments.title")}</h1>
                    <p className="workspace-subtitle">{t("hr.departments.subtitle")}</p>
                </div>
                <div className="header-actions">
                    <button className="btn btn-primary" onClick={() => setShowModal(true)}>
                        <Plus size={18} className="ms-2" />
                        {t('hr.departments.add')}
                    </button>
                </div>
            </div>

            <div className="card shadow-sm border-0">
                <div className="card-body p-0">
                    <table className="data-table mb-0">
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>{t("hr.departments.name")}</th>
                                <th style={{ width: '100px' }}>{t("common.actions")}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {loading ? (
                                <tr><td colSpan="3" className="text-center p-4">{t("common.loading")}</td></tr>
                            ) : departments.length === 0 ? (
                                <tr>
                                    <td colSpan="3" className="text-center p-5">
                                        <div className="text-muted mb-3" style={{ fontSize: '30px' }}>🏢</div>
                                        <p>{t("hr.departments.no_departments")}</p>
                                    </td>
                                </tr>
                            ) : (
                                departments.map((dept, index) => (
                                    <tr key={dept.id} className="hover-row">
                                        <td>{index + 1}</td>
                                        <td className="fw-bold">{dept.department_name}</td>
                                        <td>
                                            <button
                                                className="btn btn-icon text-danger"
                                                onClick={() => handleDelete(dept.id)}
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
                            <h3 className="modal-title">{t("hr.departments.add_new")}</h3>
                            <button className="btn-icon" onClick={() => setShowModal(false)}>×</button>
                        </div>
                        <form onSubmit={handleSubmit}>
                            <div className="modal-body">
                                <div className="mb-3">
                                    <label className="form-label">{t("hr.departments.name")}</label>
                                    <input
                                        type="text"
                                        className="form-input"
                                        placeholder={t("hr.departments.name_placeholder")}
                                        required
                                        value={formData.department_name}
                                        onChange={e => setFormData({ ...formData, department_name: e.target.value })}
                                    />
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

export default DepartmentList;
