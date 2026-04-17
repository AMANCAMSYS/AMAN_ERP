
import { useState, useEffect, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { Plus, Trash2 } from 'lucide-react';
import { hrAPI } from '../../utils/api';
import { toastEmitter } from '../../utils/toastEmitter';
import BackButton from '../../components/common/BackButton';
import DataTable from '../../components/common/DataTable';
import SearchFilter from '../../components/common/SearchFilter';

const DepartmentList = () => {
    const { t } = useTranslation();
    const [departments, setDepartments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [search, setSearch] = useState('');

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
            toastEmitter.emit(t('common.error'), 'error');
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
            toastEmitter.emit(t('hr.departments.error_creating') + (err.response?.data?.detail || err.message), 'error');
        }
    };

    const handleDelete = async (id) => {
        if (!window.confirm(t("hr.departments.confirm_delete"))) return;
        try {
            await hrAPI.deleteDepartment(id);
            fetchDepartments();
        } catch (err) {
            toastEmitter.emit(t('hr.departments.error_deleting') + (err.response?.data?.detail || err.message), 'error');
        }
    };

    const filteredData = useMemo(() => {
        let result = departments;
        if (search) {
            const q = search.toLowerCase();
            result = result.filter(dept =>
                (dept.department_name || '').toLowerCase().includes(q)
            );
        }
        return result;
    }, [departments, search]);

    const columns = [
        { key: 'department_name', label: t("hr.departments.name"), style: { fontWeight: 'bold' } },
        {
            key: '_actions', label: t("common.actions"), width: '100px',
            render: (_val, row) => (
                <button
                    className="btn btn-icon text-danger"
                    onClick={(e) => { e.stopPropagation(); handleDelete(row.id); }}
                    title={t("common.delete")}
                >
                    <Trash2 size={16} />
                </button>
            ),
        },
    ];

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        <h1 className="workspace-title">{t("hr.departments.title")}</h1>
                        <p className="workspace-subtitle">{t("hr.departments.subtitle")}</p>
                    </div>
                    <button className="btn btn-primary" onClick={() => setShowModal(true)}>
                        <Plus size={18} className="ms-2" />
                        {t('hr.departments.add')}
                    </button>
                </div>
            </div>

            <SearchFilter
                value={search}
                onChange={setSearch}
                placeholder={t("hr.departments.name")}
            />

            <DataTable
                columns={columns}
                data={filteredData}
                loading={loading}
                emptyIcon="🏢"
                emptyTitle={t("hr.departments.no_departments")}
                emptyAction={{ label: t('hr.departments.add'), onClick: () => setShowModal(true) }}
            />

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
