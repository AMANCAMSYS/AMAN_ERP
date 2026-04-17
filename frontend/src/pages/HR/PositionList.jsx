
import { useState, useEffect, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { Plus, Trash2 } from 'lucide-react';
import { hrAPI } from '../../utils/api';
import { toastEmitter } from '../../utils/toastEmitter';
import BackButton from '../../components/common/BackButton';
import DataTable from '../../components/common/DataTable';
import SearchFilter from '../../components/common/SearchFilter';

const PositionList = () => {
    const { t } = useTranslation();
    const [positions, setPositions] = useState([]);
    const [departments, setDepartments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [search, setSearch] = useState('');
    const [departmentFilter, setDepartmentFilter] = useState('');

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
            toastEmitter.emit(t('common.error'), 'error');
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
            toastEmitter.emit(t('hr.positions.error_creating') + (err.response?.data?.detail || err.message), 'error');
        }
    };

    const handleDelete = async (id) => {
        if (!window.confirm(t("hr.positions.confirm_delete"))) return;
        try {
            await hrAPI.deletePosition(id);
            fetchData();
        } catch (err) {
            toastEmitter.emit(t('hr.positions.error_deleting') + (err.response?.data?.detail || err.message), 'error');
        }
    };

    const filteredData = useMemo(() => {
        let result = positions;
        if (search) {
            const q = search.toLowerCase();
            result = result.filter(pos =>
                (pos.position_name || '').toLowerCase().includes(q) ||
                (pos.department_name || '').toLowerCase().includes(q)
            );
        }
        if (departmentFilter) {
            result = result.filter(pos => String(pos.department_id) === departmentFilter);
        }
        return result;
    }, [positions, search, departmentFilter]);

    const departmentOptions = useMemo(() =>
        departments.map(dept => ({ value: String(dept.id), label: dept.department_name })),
        [departments]
    );

    const columns = [
        { key: 'position_name', label: t("hr.positions.job_title"), style: { fontWeight: 'bold' } },
        {
            key: 'department_name', label: t("hr.positions.department"),
            render: (val) => val ? (
                <span className="badge bg-light text-dark border">{val}</span>
            ) : '-',
        },
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
                        <h1 className="workspace-title">{t("hr.positions.title")}</h1>
                        <p className="workspace-subtitle">{t("hr.positions.subtitle")}</p>
                    </div>
                    <button className="btn btn-primary" onClick={() => setShowModal(true)}>
                        <Plus size={18} className="ms-2" />
                        {t('hr.positions.add')}
                    </button>
                </div>
            </div>

            <SearchFilter
                value={search}
                onChange={setSearch}
                placeholder={t("hr.positions.job_title")}
                filters={[
                    { key: 'department', label: t("hr.positions.department"), options: departmentOptions },
                ]}
                filterValues={{ department: departmentFilter }}
                onFilterChange={(_key, val) => setDepartmentFilter(val)}
            />

            <DataTable
                columns={columns}
                data={filteredData}
                loading={loading}
                emptyIcon="💼"
                emptyTitle={t("hr.positions.no_positions")}
                emptyAction={{ label: t('hr.positions.add'), onClick: () => setShowModal(true) }}
            />

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
