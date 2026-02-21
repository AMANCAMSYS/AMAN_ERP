import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ArrowRight, Save, FolderKanban, Users, Calendar, DollarSign } from 'lucide-react';
import { projectsAPI, salesAPI, hrAPI } from '../../utils/api';
import { toastEmitter } from '../../utils/toastEmitter';
import '../../components/ModuleStyles.css';

export default function ProjectForm() {
    const { t, i18n } = useTranslation();
    const navigate = useNavigate();
    const { id } = useParams();
    const isEdit = !!id;
    const isRTL = i18n.language === 'ar';

    const [loading, setLoading] = useState(false);
    const [submitting, setSubmitting] = useState(false);
    const [customers, setCustomers] = useState([]);
    const [employees, setEmployees] = useState([]);

    const [formData, setFormData] = useState({
        project_name: '',
        project_name_en: '',
        project_code: '',
        description: '',
        project_type: 'internal',
        customer_id: '',
        manager_id: '',
        start_date: '',
        end_date: '',
        planned_budget: '',
        status: 'planning',
    });

    useEffect(() => {
        fetchDropdowns();
        if (isEdit) fetchProject();
    }, [id]);

    const fetchDropdowns = async () => {
        try {
            const [custRes, empRes] = await Promise.all([
                salesAPI.listCustomers({ limit: 200 }).catch(() => ({ data: { customers: [] } })),
                hrAPI.getEmployees().catch(() => ({ data: [] }))
            ]);
            setCustomers(custRes.data?.customers || custRes.data || []);
            setEmployees(Array.isArray(empRes.data) ? empRes.data : empRes.data?.employees || []);
        } catch (err) {
            console.error('Error loading dropdowns:', err);
        }
    };

    const fetchProject = async () => {
        try {
            setLoading(true);
            const res = await projectsAPI.get(id);
            const p = res.data;
            setFormData({
                project_name: p.project_name || '',
                project_name_en: p.project_name_en || '',
                project_code: p.project_code || '',
                description: p.description || '',
                project_type: p.project_type || 'internal',
                customer_id: p.customer_id || '',
                manager_id: p.manager_id || '',
                start_date: p.start_date || '',
                end_date: p.end_date || '',
                planned_budget: p.planned_budget || '',
                status: p.status || 'planning',
            });
        } catch (err) {
            toastEmitter.emit(t('common.load_error', 'خطأ في تحميل البيانات'), 'error');
            navigate('/projects');
        } finally {
            setLoading(false);
        }
    };

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!formData.project_name.trim()) {
            toastEmitter.emit(t('projects.errors.name_required', 'اسم المشروع مطلوب'), 'error');
            return;
        }

        setSubmitting(true);
        try {
            const payload = {
                ...formData,
                customer_id: formData.customer_id ? parseInt(formData.customer_id) : null,
                manager_id: formData.manager_id ? parseInt(formData.manager_id) : null,
                planned_budget: parseFloat(formData.planned_budget) || 0,
                start_date: formData.start_date || null,
                end_date: formData.end_date || null,
                project_code: formData.project_code || null,
            };

            if (isEdit) {
                await projectsAPI.update(id, payload);
                toastEmitter.emit(t('projects.messages.updated', 'تم تحديث المشروع بنجاح'), 'success');
            } else {
                await projectsAPI.create(payload);
                toastEmitter.emit(t('projects.messages.created', 'تم إنشاء المشروع بنجاح'), 'success');
            }
            navigate('/projects');
        } catch (err) {
            console.error('Save failed:', err);
            toastEmitter.emit(t('common.save_error', 'خطأ في الحفظ'), 'error');
        } finally {
            setSubmitting(false);
        }
    };

    if (loading) {
        return <div className="text-center py-5"><span className="loading"></span></div>;
    }

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <div className="d-flex align-items-center gap-3">
                    <button className="btn btn-icon btn-light" onClick={() => navigate('/projects')}>
                        <ArrowRight size={20} style={{ transform: isRTL ? 'none' : 'scaleX(-1)' }} />
                    </button>
                    <div>
                        <h1 className="workspace-title">
                            {isEdit ? t('projects.edit', 'تعديل المشروع') : t('projects.new', 'مشروع جديد')}
                        </h1>
                        <p className="workspace-subtitle">
                            {isEdit ? t('projects.edit_subtitle', 'تعديل بيانات المشروع') : t('projects.new_subtitle', 'إنشاء مشروع جديد لتتبع التكاليف والإيرادات')}
                        </p>
                    </div>
                </div>
            </div>

            <form onSubmit={handleSubmit}>
                {/* Basic Info Card */}
                <div className="card section-card border-0 shadow-sm mb-4">
                    <div className="card-body">
                        <div className="d-flex align-items-center gap-2 mb-4">
                            <div style={{
                                width: 36, height: 36, borderRadius: 8,
                                background: 'linear-gradient(135deg, #667eea, #764ba2)',
                                display: 'flex', alignItems: 'center', justifyContent: 'center'
                            }}>
                                <FolderKanban size={18} color="white" />
                            </div>
                            <h5 className="section-title mb-0">{t('projects.sections.basic', 'البيانات الأساسية')}</h5>
                        </div>

                        <div className="row g-3">
                            <div className="col-md-6">
                                <label className="form-label">{t('projects.fields.name', 'اسم المشروع')} *</label>
                                <input type="text" className="form-input" name="project_name"
                                    value={formData.project_name} onChange={handleChange} required />
                            </div>
                            <div className="col-md-6">
                                <label className="form-label">{t('projects.fields.name_en', 'الاسم بالإنجليزية')}</label>
                                <input type="text" className="form-input" name="project_name_en"
                                    value={formData.project_name_en} onChange={handleChange} dir="ltr" />
                            </div>
                            <div className="col-md-4">
                                <label className="form-label">{t('projects.fields.code', 'رمز المشروع')}</label>
                                <input type="text" className="form-input" name="project_code"
                                    value={formData.project_code} onChange={handleChange}
                                    placeholder={t('projects.fields.code_auto', 'تلقائي إذا تُرك فارغاً')} dir="ltr" />
                            </div>
                            <div className="col-md-4">
                                <label className="form-label">{t('projects.fields.type', 'نوع المشروع')}</label>
                                <select className="form-input" name="project_type"
                                    value={formData.project_type} onChange={handleChange}>
                                    <option value="internal">{t('projects.types.internal', 'داخلي')}</option>
                                    <option value="external">{t('projects.types.external', 'خارجي (عميل)')}</option>
                                    <option value="consulting">{t('projects.types.consulting', 'استشاري')}</option>
                                </select>
                            </div>
                            <div className="col-md-4">
                                <label className="form-label">{t('projects.fields.status', 'الحالة')}</label>
                                <select className="form-input" name="status"
                                    value={formData.status} onChange={handleChange}>
                                    <option value="planning">{t('projects.status.planning', 'تخطيط')}</option>
                                    <option value="in_progress">{t('projects.status.in_progress', 'قيد التنفيذ')}</option>
                                    <option value="on_hold">{t('projects.status.on_hold', 'متوقف')}</option>
                                    <option value="completed">{t('projects.status.completed', 'مكتمل')}</option>
                                    <option value="cancelled">{t('projects.status.cancelled', 'ملغي')}</option>
                                </select>
                            </div>
                            <div className="col-12">
                                <label className="form-label">{t('projects.fields.description', 'الوصف')}</label>
                                <textarea className="form-input" name="description" rows={3}
                                    value={formData.description} onChange={handleChange} />
                            </div>
                        </div>
                    </div>
                </div>

                {/* People Card */}
                <div className="card section-card border-0 shadow-sm mb-4">
                    <div className="card-body">
                        <div className="d-flex align-items-center gap-2 mb-4">
                            <div style={{
                                width: 36, height: 36, borderRadius: 8,
                                background: 'linear-gradient(135deg, #f093fb, #f5576c)',
                                display: 'flex', alignItems: 'center', justifyContent: 'center'
                            }}>
                                <Users size={18} color="white" />
                            </div>
                            <h5 className="section-title mb-0">{t('projects.sections.people', 'الأطراف')}</h5>
                        </div>

                        <div className="row g-3">
                            <div className="col-md-6">
                                <label className="form-label">{t('projects.fields.customer', 'العميل')}</label>
                                <select className="form-input" name="customer_id"
                                    value={formData.customer_id} onChange={handleChange}>
                                    <option value="">{t('projects.fields.no_customer', 'بدون عميل (مشروع داخلي)')}</option>
                                    {customers.map(c => (
                                        <option key={c.id} value={c.id}>{c.customer_name}</option>
                                    ))}
                                </select>
                            </div>
                            <div className="col-md-6">
                                <label className="form-label">{t('projects.fields.manager', 'مدير المشروع')}</label>
                                <select className="form-input" name="manager_id"
                                    value={formData.manager_id} onChange={handleChange}>
                                    <option value="">{t('common.not_specified', 'غير محدد')}</option>
                                    {employees.map(e => (
                                        <option key={e.id} value={e.id}>{e.first_name} {e.last_name}</option>
                                    ))}
                                </select>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Schedule & Budget Card */}
                <div className="card section-card border-0 shadow-sm mb-4">
                    <div className="card-body">
                        <div className="d-flex align-items-center gap-2 mb-4">
                            <div style={{
                                width: 36, height: 36, borderRadius: 8,
                                background: 'linear-gradient(135deg, #43e97b, #38f9d7)',
                                display: 'flex', alignItems: 'center', justifyContent: 'center'
                            }}>
                                <Calendar size={18} color="white" />
                            </div>
                            <h5 className="section-title mb-0">{t('projects.sections.schedule', 'الجدول الزمني والميزانية')}</h5>
                        </div>

                        <div className="row g-3">
                            <div className="col-md-4">
                                <label className="form-label">{t('projects.fields.start_date', 'تاريخ البدء')}</label>
                                <DateInput className="form-input" name="start_date"
                                    value={formData.start_date} onChange={handleChange} />
                            </div>
                            <div className="col-md-4">
                                <label className="form-label">{t('projects.fields.end_date', 'تاريخ الانتهاء')}</label>
                                <DateInput className="form-input" name="end_date"
                                    value={formData.end_date} onChange={handleChange} />
                            </div>
                            <div className="col-md-4">
                                <label className="form-label">{t('projects.fields.budget', 'الميزانية المخططة')}</label>
                                <input type="number" className="form-input" name="planned_budget"
                                    value={formData.planned_budget} onChange={handleChange}
                                    min="0" step="0.01" placeholder="0.00" dir="ltr" />
                            </div>
                        </div>
                    </div>
                </div>

                {/* Actions */}
                <div className="d-flex justify-content-end gap-3">
                    <button type="button" className="btn btn-light" onClick={() => navigate('/projects')}>
                        {t('common.cancel', 'إلغاء')}
                    </button>
                    <button type="submit" className="btn btn-primary" disabled={submitting}>
                        {submitting ? (
                            <><span className="loading" style={{ width: 16, height: 16 }}></span> {t('common.saving', 'جاري الحفظ...')}</>
                        ) : (
                            <><Save size={18} /> {t('common.save', 'حفظ')}</>
                        )}
                    </button>
                </div>
            </form>
        </div>
    );
}
