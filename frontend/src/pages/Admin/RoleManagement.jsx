import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import api from '../../utils/api';
import { hasPermission, getUser } from '../../utils/auth';
import { toastEmitter } from '../../utils/toastEmitter';
import './RoleManagement.css';

const RoleManagement = () => {
    const { t, i18n } = useTranslation();
    const isRTL = i18n.language === 'ar';

    const [roles, setRoles] = useState([]);
    const [permissions, setPermissions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [user] = useState(getUser());
    const [companies, setCompanies] = useState([]);
    const [selectedCompany, setSelectedCompany] = useState('');
    const [showModal, setShowModal] = useState(false);
    const [editingRole, setEditingRole] = useState(null);
    const [formData, setFormData] = useState({
        role_name: '',
        role_name_ar: '',
        description: '',
        permissions: []
    });

    useEffect(() => {
        if (user?.role === 'system_admin') {
            fetchCompanies();
        }
    }, []);

    useEffect(() => {
        fetchData();
    }, [selectedCompany]);

    const fetchCompanies = async () => {
        try {
            const res = await api.get('/companies/list');
            setCompanies(res.data.companies || []);
        } catch (error) {
            console.error('Error fetching companies:', error);
        }
    };

    const fetchData = async () => {
        if (!hasPermission('admin.roles')) {
            setLoading(false);
            return;
        }

        // Special case for system admin: they MUST select a company first
        if (user?.role === 'system_admin' && !selectedCompany) {
            setRoles([]);
            setLoading(false);
            return;
        }

        setLoading(true);
        const params = {};
        if (selectedCompany) params.company_id = selectedCompany;

        try {
            const [rolesRes, permsRes] = await Promise.all([
                api.get('/roles/', { params }),
                api.get('/roles/permissions')
            ]);
            setRoles(rolesRes.data);
            setPermissions(permsRes.data);
        } catch (error) {
            console.error('Error fetching roles:', error);
        } finally {
            setLoading(false);
        }
    };

    const openModal = (role = null) => {
        if (role) {
            setEditingRole(role);
            setFormData({
                role_name: role.role_name,
                role_name_ar: role.role_name_ar || '',
                description: role.description || '',
                permissions: role.permissions || []
            });
        } else {
            setEditingRole(null);
            setFormData({
                role_name: '',
                role_name_ar: '',
                description: '',
                permissions: []
            });
        }
        setShowModal(true);
    };

    const closeModal = () => {
        setShowModal(false);
        setEditingRole(null);
    };

    const handleInputChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const togglePermission = (permKey) => {
        const perms = formData.permissions.includes(permKey)
            ? formData.permissions.filter(p => p !== permKey)
            : [...formData.permissions, permKey];
        setFormData({ ...formData, permissions: perms });
    };

    const selectAllPermissions = () => {
        setFormData({ ...formData, permissions: permissions.map(p => p.key) });
    };

    const clearAllPermissions = () => {
        setFormData({ ...formData, permissions: [] });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        const params = {};
        if (selectedCompany) params.company_id = selectedCompany;

        try {
            if (editingRole) {
                await api.put(`/roles/${editingRole.id}`, formData, { params });
            } else {
                await api.post('/roles/', formData, { params });
            }
            closeModal();
            fetchData();
        } catch (error) {
            console.error('Error saving role:', error);
        }
    };

    const handleDelete = async (role) => {
        if (role.is_system_role) {
            toastEmitter.emit('لا يمكن حذف الأدوار الافتراضية للنظام', 'error');
            return;
        }
        if (!window.confirm(t('admin.roles.confirm_delete', { name: role.role_name }))) return;

        const params = {};
        if (selectedCompany) params.company_id = selectedCompany;

        try {
            await api.delete(`/roles/${role.id}`, { params });
            fetchData();
        } catch (error) {
            console.error('Error deleting role:', error);
        }
    };

    // Group permissions by section
    const groupedPermissions = permissions.reduce((acc, perm) => {
        const section = perm.key.split('.')[0];
        if (!acc[section]) acc[section] = [];
        acc[section].push(perm);
        return acc;
    }, {});

    return (
        <div className="role-management-container">
            <div className="role-header">
                <div>
                    <h1>🔐 {t('roles.title') || 'إدارة الأدوار والصلاحيات'}</h1>
                    <p className="subtitle">{t('roles.subtitle') || 'إنشاء وتعديل أدوار المستخدمين وصلاحياتهم'}</p>
                </div>
                <button className="btn-primary" onClick={() => openModal()} disabled={user?.role === 'system_admin' && !selectedCompany}>
                    ➕ {t('roles.addRole') || 'إضافة دور جديد'}
                </button>
            </div>

            {user?.role === 'system_admin' && (
                <div className="company-selector-panel">
                    <label>{t('companies.title') || 'الشركة'}:</label>
                    <select
                        value={selectedCompany}
                        onChange={(e) => setSelectedCompany(e.target.value)}
                        className="company-select"
                    >
                        <option value="">-- {t('audit.select_company') || 'اختر شركة لرؤية أدوارها'} --</option>
                        {Array.isArray(companies) && companies.map(c => (
                            <option key={c.id} value={c.id}>{c.company_name} ({c.id})</option>
                        ))}
                    </select>
                </div>
            )}

            {loading ? (
                <div className="loading">⏳ {t('common.loading') || 'جاري التحميل...'}</div>
            ) : (
                <div className="roles-grid">
                    {roles.length === 0 ? (
                        <div className="no-data">
                            {user?.role === 'system_admin' && !selectedCompany
                                ? (t('roles.selectCompanyToView') || 'يرجى اختيار شركة لعرض أدوارها')
                                : (t('common.no_data') || 'لا توجد بيانات')}
                        </div>
                    ) : (
                        roles.map(role => (
                            <div key={role.id} className={`role-card ${role.is_system_role ? 'system' : ''}`}>
                                <div className="role-card-header">
                                    <div className="role-icon">
                                        {role.is_system_role ? '🛡️' : '👤'}
                                    </div>
                                    <div className="role-info">
                                        <h3>{isRTL ? (role.role_name_ar || role.role_name) : role.role_name}</h3>
                                        {role.description && <p>{role.description}</p>}
                                    </div>
                                    {role.is_system_role && (
                                        <span className="system-badge">{t('roles.systemRole') || 'افتراضي'}</span>
                                    )}
                                </div>
                                <div className="role-permissions">
                                    <span className="perm-count">
                                        {role.permissions?.length || 0} {t('roles.permissions') || 'صلاحية'}
                                    </span>
                                    <div className="perm-preview">
                                        {(role.permissions || []).slice(0, 3).map(p => (
                                            <span key={p} className="perm-tag">{p}</span>
                                        ))}
                                        {(role.permissions?.length || 0) > 3 && (
                                            <span className="perm-more">+{role.permissions.length - 3}</span>
                                        )}
                                    </div>
                                </div>
                                <div className="role-actions">
                                    <button
                                        className="btn-edit"
                                        onClick={() => openModal(role)}
                                        disabled={role.is_system_role}
                                    >
                                        ✏️ {t('common.edit') || 'تعديل'}
                                    </button>
                                    <button
                                        className="btn-delete"
                                        onClick={() => handleDelete(role)}
                                        disabled={role.is_system_role}
                                    >
                                        🗑️ {t('common.delete') || 'حذف'}
                                    </button>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            )}

            {/* Modal */}
            {showModal && (
                <div className="modal-overlay" onClick={closeModal}>
                    <div className="modal-content" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <h2>
                                {editingRole
                                    ? (t('roles.editRole') || 'تعديل الدور')
                                    : (t('roles.addRole') || 'إضافة دور جديد')}
                            </h2>
                            <button className="modal-close" onClick={closeModal}>✕</button>
                        </div>

                        <form onSubmit={handleSubmit}>
                            <div className="form-row">
                                <div className="form-group">
                                    <label>{t('roles.roleName') || 'اسم الدور (إنجليزي)'}</label>
                                    <input
                                        type="text"
                                        name="role_name"
                                        value={formData.role_name}
                                        onChange={handleInputChange}
                                        required
                                        placeholder="e.g. sales_manager"
                                    />
                                </div>
                                <div className="form-group">
                                    <label>{t('roles.roleNameAr') || 'اسم الدور (عربي)'}</label>
                                    <input
                                        type="text"
                                        name="role_name_ar"
                                        value={formData.role_name_ar}
                                        onChange={handleInputChange}
                                        placeholder={t("admin.roles.name_ar_placeholder")}
                                    />
                                </div>
                            </div>

                            <div className="form-group">
                                <label>{t('roles.description') || 'الوصف'}</label>
                                <textarea
                                    name="description"
                                    value={formData.description}
                                    onChange={handleInputChange}
                                    rows={2}
                                />
                            </div>

                            <div className="permissions-section">
                                <div className="permissions-header">
                                    <h3>{t('roles.selectPermissions') || 'اختر الصلاحيات'}</h3>
                                    <div className="perm-actions">
                                        <button type="button" onClick={selectAllPermissions}>
                                            ✓ {t('roles.selectAll') || 'تحديد الكل'}
                                        </button>
                                        <button type="button" onClick={clearAllPermissions}>
                                            ✕ {t('roles.clearAll') || 'إلغاء الكل'}
                                        </button>
                                    </div>
                                </div>

                                <div className="permissions-grid">
                                    {Object.entries(groupedPermissions).map(([section, perms]) => (
                                        <div key={section} className="perm-section">
                                            <h4 className="section-title">{section.toUpperCase()}</h4>
                                            <div className="perm-list">
                                                {perms.map(perm => (
                                                    <label key={perm.key} className="perm-item">
                                                        <input
                                                            type="checkbox"
                                                            checked={formData.permissions.includes(perm.key)}
                                                            onChange={() => togglePermission(perm.key)}
                                                        />
                                                        <span className="perm-label">
                                                            {isRTL ? perm.label_ar : perm.label_en}
                                                        </span>
                                                        <code className="perm-key">{perm.key}</code>
                                                    </label>
                                                ))}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            <div className="modal-footer">
                                <button type="button" className="btn-cancel" onClick={closeModal}>
                                    {t('common.cancel') || 'إلغاء'}
                                </button>
                                <button type="submit" className="btn-save">
                                    {t('common.save') || 'حفظ'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default RoleManagement;
