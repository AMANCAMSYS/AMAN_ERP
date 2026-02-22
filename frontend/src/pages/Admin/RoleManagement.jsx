import React, { useState, useEffect, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import * as LucideIcons from 'lucide-react';
import api from '../../utils/api';
import { hasPermission, getUser } from '../../utils/auth';
import { toastEmitter } from '../../utils/toastEmitter';
import './RoleManagement.css';

const PERM_AR = {
    '*': 'صلاحيات كاملة',
    'dashboard.view': 'لوحة التحكم',
    'sales.*': 'المبيعات (كامل)', 'sales.view': 'عرض المبيعات', 'sales.create': 'إنشاء مبيعات', 'sales.edit': 'تعديل مبيعات', 'sales.delete': 'حذف مبيعات', 'sales.approve': 'اعتماد مبيعات',
    'buying.*': 'المشتريات (كامل)', 'buying.view': 'عرض المشتريات', 'buying.create': 'إنشاء مشتريات', 'buying.edit': 'تعديل مشتريات', 'buying.delete': 'حذف مشتريات', 'buying.approve': 'اعتماد مشتريات',
    'products.*': 'المنتجات (كامل)', 'products.view': 'عرض المنتجات', 'products.create': 'إنشاء منتجات', 'products.edit': 'تعديل منتجات',
    'stock.*': 'المخزون (كامل)', 'stock.view': 'عرض المخزون', 'stock.create': 'حركات مخزون', 'stock.edit': 'تعديل مخزون',
    'inventory.*': 'الجرد (كامل)', 'inventory.view': 'عرض الجرد', 'inventory.create': 'إنشاء جرد',
    'accounting.*': 'المحاسبة (كامل)', 'accounting.view': 'عرض المحاسبة', 'accounting.edit': 'تعديل المحاسبة', 'accounting.create': 'إنشاء قيود', 'accounting.approve': 'اعتماد قيود', 'accounting.budgets.view': 'الميزانيات', 'accounting.cost_centers.view': 'مراكز التكلفة',
    'treasury.*': 'الخزينة (كامل)', 'treasury.view': 'عرض الخزينة', 'treasury.create': 'إنشاء خزينة', 'treasury.edit': 'تعديل الخزينة', 'treasury.approve': 'اعتماد الخزينة',
    'reconciliation.*': 'التسوية (كامل)', 'reconciliation.view': 'عرض التسوية', 'reconciliation.create': 'إنشاء تسوية',
    'taxes.*': 'الضرائب (كامل)', 'taxes.view': 'عرض الضرائب', 'taxes.create': 'إنشاء ضرائب',
    'currencies.*': 'العملات (كامل)', 'currencies.view': 'عرض العملات',
    'reports.*': 'التقارير (كامل)', 'reports.view': 'عرض التقارير', 'reports.financial': 'التقارير المالية', 'reports.create': 'إنشاء تقارير',
    'hr.*': 'الموارد البشرية (كامل)', 'hr.view': 'عرض الموارد البشرية', 'hr.create': 'إنشاء HR', 'hr.edit': 'تعديل HR', 'hr.reports': 'تقارير HR', 'hr.payroll.view': 'عرض الرواتب', 'hr.payroll.create': 'إنشاء رواتب',
    'assets.*': 'الأصول (كامل)', 'assets.view': 'عرض الأصول', 'assets.create': 'إنشاء أصول', 'assets.edit': 'تعديل أصول',
    'expenses.*': 'المصروفات (كامل)', 'expenses.view': 'عرض المصروفات', 'expenses.create': 'إنشاء مصروفات', 'expenses.approve': 'اعتماد مصروفات',
    'contracts.*': 'العقود (كامل)', 'contracts.view': 'عرض العقود', 'contracts.create': 'إنشاء عقود', 'contracts.edit': 'تعديل عقود',
    'projects.*': 'المشاريع (كامل)', 'projects.view': 'عرض المشاريع', 'projects.create': 'إنشاء مشاريع', 'projects.edit': 'تعديل مشاريع',
    'pos.*': 'نقطة البيع (كامل)', 'pos.view': 'عرض نقطة البيع', 'pos.create': 'إنشاء مبيعات POS', 'pos.manage': 'إدارة نقطة البيع', '*.pos': 'نقطة البيع',
    'manufacturing.*': 'التصنيع (كامل)', 'manufacturing.view': 'عرض التصنيع', 'manufacturing.create': 'إنشاء أوامر تصنيع', 'manufacturing.edit': 'تعديل التصنيع', 'manufacturing.reports': 'تقارير التصنيع',
    'approvals.*': 'الاعتمادات (كامل)', 'approvals.view': 'عرض الاعتمادات', 'approvals.create': 'إنشاء اعتمادات', 'approvals.approve': 'منح الاعتمادات',
    'notifications.view': 'الإشعارات', 'notifications.*': 'الإشعارات (كامل)',
    'security.*': 'الأمان (كامل)', 'security.view': 'عرض الأمان',
    'audit.*': 'سجل المراجعة (كامل)', 'audit.view': 'سجل المراجعة',
    'data_import.*': 'استيراد البيانات (كامل)', 'data_import.view': 'استيراد البيانات',
    'branches.*': 'الفروع (كامل)', 'branches.view': 'عرض الفروع', 'branches.create': 'إنشاء فروع',
    'settings.*': 'الإعدادات (كامل)', 'settings.view': 'عرض الإعدادات', 'settings.edit': 'تعديل الإعدادات',
    'admin.*': 'إدارة النظام (كامل)', 'admin.roles': 'إدارة الأدوار', 'admin.users': 'إدارة المستخدمين', 'admin.companies': 'إدارة الشركات',
    '*.accounting': 'المحاسبة', '*.treasury': 'الخزينة', '*.reconciliation': 'التسوية', '*.sales': 'المبيعات', '*.reports': 'التقارير',
};

const permLabel = (p) => PERM_AR[p] || p;

const DynamicIcon = ({ name, size = 18, ...props }) => {
    const Icon = LucideIcons[name];
    return Icon ? <Icon size={size} {...props} /> : null;
};

const RoleManagement = () => {
    const { t, i18n } = useTranslation();
    const isRTL = i18n.language === 'ar';

    const [roles, setRoles] = useState([]);
    const [permissions, setPermissions] = useState([]);
    const [sections, setSections] = useState({});
    const [loading, setLoading] = useState(true);
    const [initLoading, setInitLoading] = useState(false);
    const [user] = useState(getUser());
    const [companies, setCompanies] = useState([]);
    const [selectedCompany, setSelectedCompany] = useState('');
    const [showModal, setShowModal] = useState(false);
    const [editingRole, setEditingRole] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');
    const [collapsedSections, setCollapsedSections] = useState({});
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

        if (user?.role === 'system_admin' && !selectedCompany) {
            setRoles([]);
            setLoading(false);
            return;
        }

        setLoading(true);
        const params = {};
        if (selectedCompany) params.company_id = selectedCompany;

        try {
            const [rolesRes, permsRes, sectionsRes] = await Promise.all([
                api.get('/roles/', { params }),
                api.get('/roles/permissions'),
                api.get('/roles/permissions/sections')
            ]);
            setRoles(rolesRes.data);
            setPermissions(permsRes.data);
            setSections(sectionsRes.data);
        } catch (error) {
            console.error('Error fetching roles:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleInitDefaults = async () => {
        setInitLoading(true);
        try {
            const params = {};
            if (selectedCompany) params.company_id = selectedCompany;
            const res = await api.post('/roles/init-defaults', null, { params });
            toastEmitter.emit(
                isRTL
                    ? `تم إنشاء ${res.data.created} وتحديث ${res.data.updated} من الأدوار الافتراضية`
                    : `Created ${res.data.created} and updated ${res.data.updated} default roles`,
                'success'
            );
            fetchData();
        } catch (error) {
            toastEmitter.emit(t('admin.roles.init_failed'), 'error');
        } finally {
            setInitLoading(false);
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
        setSearchTerm('');
        setCollapsedSections({});
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

    const toggleSectionPermissions = (sectionKey, perms) => {
        const permKeys = perms.map(p => p.key);
        const allSelected = permKeys.every(k => formData.permissions.includes(k));
        if (allSelected) {
            setFormData({ ...formData, permissions: formData.permissions.filter(p => !permKeys.includes(p)) });
        } else {
            const newPerms = new Set([...formData.permissions, ...permKeys]);
            setFormData({ ...formData, permissions: [...newPerms] });
        }
    };

    const toggleSectionCollapse = (sectionKey) => {
        setCollapsedSections(prev => ({ ...prev, [sectionKey]: !prev[sectionKey] }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        const params = {};
        if (selectedCompany) params.company_id = selectedCompany;

        try {
            if (editingRole) {
                await api.put(`/roles/${editingRole.id}`, formData, { params });
                toastEmitter.emit(t('admin.roles.updated'), 'success');
            } else {
                await api.post('/roles/', formData, { params });
                toastEmitter.emit(t('admin.roles.created'), 'success');
            }
            closeModal();
            fetchData();
        } catch (error) {
            console.error('Error saving role:', error);
            toastEmitter.emit(t('admin.roles.save_error'), 'error');
        }
    };

    const handleDelete = async (role) => {
        if (role.is_system_role) {
            toastEmitter.emit(t('admin.roles.cannot_delete_system'), 'error');
            return;
        }
        if (!window.confirm(t('admin.roles.confirm_delete', { name: isRTL ? (role.role_name_ar || role.role_name) : role.role_name }))) return;

        const params = {};
        if (selectedCompany) params.company_id = selectedCompany;

        try {
            await api.delete(`/roles/${role.id}`, { params });
            toastEmitter.emit(t('admin.roles.deleted'), 'success');
            fetchData();
        } catch (error) {
            console.error('Error deleting role:', error);
        }
    };

    // Group permissions by section field
    const groupedPermissions = useMemo(() => {
        return permissions.reduce((acc, perm) => {
            const section = perm.section || perm.key.split('.')[0];
            if (!acc[section]) acc[section] = [];
            acc[section].push(perm);
            return acc;
        }, {});
    }, [permissions]);

    // Filter permissions by search
    const filteredSections = useMemo(() => {
        if (!searchTerm.trim()) return groupedPermissions;
        const term = searchTerm.toLowerCase();
        const filtered = {};
        for (const [section, perms] of Object.entries(groupedPermissions)) {
            const sectionMeta = sections[section];
            const sectionMatch = sectionMeta && (
                sectionMeta.label_ar?.includes(term) ||
                sectionMeta.label_en?.toLowerCase().includes(term)
            );
            if (sectionMatch) {
                filtered[section] = perms;
            } else {
                const matchingPerms = perms.filter(p =>
                    p.key.toLowerCase().includes(term) ||
                    p.label_ar?.includes(term) ||
                    p.label_en?.toLowerCase().includes(term)
                );
                if (matchingPerms.length > 0) filtered[section] = matchingPerms;
            }
        }
        return filtered;
    }, [groupedPermissions, searchTerm, sections]);

    const totalSelected = formData.permissions.length;
    const totalPerms = permissions.length;

    return (
        <div className="role-management-container">
            <div className="role-header">
                <div>
                    <h1><LucideIcons.Shield size={28} style={{ verticalAlign: 'middle', marginLeft: isRTL ? 8 : 0, marginRight: isRTL ? 0 : 8 }} /> {t('roles.title')}</h1>
                    <p className="subtitle">{t('roles.subtitle')}</p>
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                    <button className="btn-secondary" onClick={handleInitDefaults} disabled={initLoading || (user?.role === 'system_admin' && !selectedCompany)}>
                        <LucideIcons.RefreshCw size={16} className={initLoading ? 'spin' : ''} />
                        {' '}{t('roles.initDefaults')}
                    </button>
                    <button className="btn-primary" onClick={() => openModal()} disabled={user?.role === 'system_admin' && !selectedCompany}>
                        <LucideIcons.Plus size={16} /> {t('roles.addRole')}
                    </button>
                </div>
            </div>

            {user?.role === 'system_admin' && (
                <div className="company-selector-panel">
                    <LucideIcons.Building size={18} />
                    <label>{t('companies.title')}:</label>
                    <select
                        value={selectedCompany}
                        onChange={(e) => setSelectedCompany(e.target.value)}
                        className="company-select"
                    >
                        <option value="">-- {t('audit.select_company')} --</option>
                        {Array.isArray(companies) && companies.map(c => (
                            <option key={c.id} value={c.id}>{c.company_name} ({c.id})</option>
                        ))}
                    </select>
                </div>
            )}

            {loading ? (
                <div className="loading"><LucideIcons.Loader2 className="spin" size={24} /> {t('common.loading')}</div>
            ) : (
                <div className="roles-grid">
                    {roles.length === 0 ? (
                        <div className="no-data">
                            {user?.role === 'system_admin' && !selectedCompany
                                ? t('roles.selectCompanyToView')
                                : t('common.no_data')}
                        </div>
                    ) : (
                        roles.map(role => (
                            <div key={role.id} className={`role-card ${role.is_system_role ? 'system' : ''}`}>
                                {role.is_system_role && (
                                    <div className="system-badge-row">
                                        <span className="system-badge">
                                            <LucideIcons.Lock size={12} /> {t('roles.systemRole')}
                                        </span>
                                    </div>
                                )}
                                <div className="role-card-header">
                                    <div className="role-icon">
                                        {role.is_system_role
                                            ? <LucideIcons.ShieldCheck size={24} color="white" />
                                            : <LucideIcons.User size={24} color="white" />}
                                    </div>
                                    <div className="role-info">
                                        <h3>{isRTL ? (role.role_name_ar || role.role_name) : role.role_name}</h3>
                                        {role.description && <p>{role.description}</p>}
                                        {!isRTL && role.role_name_ar && <p className="role-name-secondary">{role.role_name_ar}</p>}
                                        {isRTL && <p className="role-name-secondary">{role.role_name}</p>}
                                    </div>
                                </div>
                                <div className="role-permissions">
                                    <span className="perm-count">
                                        <LucideIcons.Key size={14} style={{ verticalAlign: 'middle' }} />
                                        {' '}{role.permissions?.includes('*') ? t('roles.fullAccess') : `${role.permissions?.length || 0} ${t('roles.permissions')}`}
                                    </span>
                                    <div className="perm-preview">
                                        {(role.permissions || []).slice(0, 4).map(p => (
                                            <span key={p} className="perm-tag">{permLabel(p)}</span>
                                        ))}
                                        {(role.permissions?.length || 0) > 4 && (
                                            <span className="perm-more">+{role.permissions.length - 4}</span>
                                        )}
                                    </div>
                                </div>
                                <div className="role-actions">
                                    <button
                                        className="btn-edit"
                                        onClick={() => openModal(role)}
                                    >
                                        <LucideIcons.Pencil size={14} /> {t('common.edit')}
                                    </button>
                                    <button
                                        className="btn-delete"
                                        onClick={() => handleDelete(role)}
                                        disabled={role.is_system_role}
                                        title={role.is_system_role ? t('admin.roles.cannot_edit_system_roles') : ''}
                                    >
                                        <LucideIcons.Trash2 size={14} /> {t('common.delete')}
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
                    <div className="modal-content role-modal-wide" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <h2>
                                {editingRole
                                    ? <><LucideIcons.Pencil size={20} /> {t('roles.editRole')}</>
                                    : <><LucideIcons.Plus size={20} /> {t('roles.addRole')}</>}
                            </h2>
                            <button className="modal-close" onClick={closeModal}><LucideIcons.X size={20} /></button>
                        </div>

                        <form onSubmit={handleSubmit}>
                            <div className="form-row">
                                <div className="form-group">
                                    <label>{t('roles.roleName')}</label>
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
                                    <label>{t('roles.roleNameAr')}</label>
                                    <input
                                        type="text"
                                        name="role_name_ar"
                                        value={formData.role_name_ar}
                                        onChange={handleInputChange}
                                        placeholder="مثال: مدير المبيعات"
                                    />
                                </div>
                            </div>

                            <div className="form-group">
                                <label>{t('roles.description')}</label>
                                <textarea
                                    name="description"
                                    value={formData.description}
                                    onChange={handleInputChange}
                                    rows={2}
                                    placeholder={t('admin.roles.brief_description_of_this_role')}
                                />
                            </div>

                            <div className="permissions-section">
                                <div className="permissions-header">
                                    <h3>
                                        <LucideIcons.Key size={18} />
                                        {' '}{t('roles.selectPermissions')}
                                        <span className="perm-counter">{totalSelected}/{totalPerms}</span>
                                    </h3>
                                    <div className="perm-actions">
                                        <div className="perm-search">
                                            <LucideIcons.Search size={14} />
                                            <input
                                                type="text"
                                                value={searchTerm}
                                                onChange={e => setSearchTerm(e.target.value)}
                                                placeholder={t('admin.roles.search_permissions')}
                                            />
                                        </div>
                                        <button type="button" className="btn-select-all" onClick={selectAllPermissions}>
                                            <LucideIcons.CheckSquare size={14} /> {t('roles.selectAll')}
                                        </button>
                                        <button type="button" className="btn-clear-all" onClick={clearAllPermissions}>
                                            <LucideIcons.Square size={14} /> {t('roles.clearAll')}
                                        </button>
                                    </div>
                                </div>

                                <div className="permissions-sections-list">
                                    {Object.entries(filteredSections).map(([sectionKey, perms]) => {
                                        const meta = sections[sectionKey] || {};
                                        const sectionLabel = isRTL ? (meta.label_ar || sectionKey) : (meta.label_en || sectionKey);
                                        const permKeys = perms.map(p => p.key);
                                        const selectedCount = permKeys.filter(k => formData.permissions.includes(k)).length;
                                        const allSelected = selectedCount === permKeys.length;
                                        const someSelected = selectedCount > 0 && !allSelected;
                                        const isCollapsed = collapsedSections[sectionKey];

                                        return (
                                            <div key={sectionKey} className={`perm-section-card ${someSelected ? 'partial' : ''} ${allSelected ? 'all-selected' : ''}`}>
                                                <div className="section-header" onClick={() => toggleSectionCollapse(sectionKey)}>
                                                    <div className="section-header-left">
                                                        <div className="section-icon-wrapper">
                                                            <DynamicIcon name={meta.icon || 'Circle'} size={18} />
                                                        </div>
                                                        <span className="section-label">{sectionLabel}</span>
                                                        <span className="section-count">{selectedCount}/{permKeys.length}</span>
                                                    </div>
                                                    <div className="section-header-right">
                                                        <button
                                                            type="button"
                                                            className={`btn-section-toggle ${allSelected ? 'active' : ''}`}
                                                            onClick={(e) => { e.stopPropagation(); toggleSectionPermissions(sectionKey, perms); }}
                                                        >
                                                            {allSelected
                                                                ? <><LucideIcons.CheckSquare size={14} /> {t('admin.roles.deselect')}</>
                                                                : <><LucideIcons.Square size={14} /> {t('admin.roles.select_all')}</>}
                                                        </button>
                                                        <LucideIcons.ChevronDown size={16} className={`chevron ${isCollapsed ? 'collapsed' : ''}`} />
                                                    </div>
                                                </div>
                                                {!isCollapsed && (
                                                    <div className="perm-list">
                                                        {perms.map(perm => (
                                                            <label key={perm.key} className={`perm-item ${formData.permissions.includes(perm.key) ? 'checked' : ''}`}>
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
                                                )}
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>

                            <div className="modal-footer">
                                <button type="button" className="btn-cancel" onClick={closeModal}>
                                    {t('common.cancel')}
                                </button>
                                <button type="submit" className="btn-save">
                                    <LucideIcons.Save size={16} /> {t('common.save')}
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
