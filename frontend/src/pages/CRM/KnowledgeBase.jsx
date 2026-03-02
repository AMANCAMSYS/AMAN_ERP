import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { crmAPI } from '../../utils/api';
import { formatShortDate } from '../../utils/dateUtils';
import '../../components/ModuleStyles.css';
import BackButton from '../../components/common/BackButton';
import { useToast } from '../../context/ToastContext'

const categoryColors = {
    faq: { bg: '#dbeafe', color: '#1d4ed8' },
    guide: { bg: '#dcfce7', color: '#16a34a' },
    policy: { bg: '#fef3c7', color: '#d97706' },
    general: { bg: '#f3e8ff', color: '#7c3aed' }
};

function KnowledgeBase() {
    const { t } = useTranslation();
  const { showToast } = useToast()
    const [articles, setArticles] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [showView, setShowView] = useState(null);
    const [isEdit, setIsEdit] = useState(false);
    const [editId, setEditId] = useState(null);
    const [filterCategory, setFilterCategory] = useState('');
    const [search, setSearch] = useState('');

    const emptyForm = { title: '', category: 'general', content: '', tags: '', is_published: false };
    const [form, setForm] = useState({ ...emptyForm });

    useEffect(() => { fetchData(); }, [filterCategory, search]);

    const fetchData = async () => {
        setLoading(true);
        try {
            const params = {};
            if (filterCategory) params.category = filterCategory;
            if (search) params.search = search;
            const res = await crmAPI.listArticles(params);
            setArticles(res.data || []);
        } catch (e) { console.error(e); }
        finally { setLoading(false); }
    };

    const openCreate = () => { setForm({ ...emptyForm }); setIsEdit(false); setEditId(null); setShowModal(true); };
    const openEdit = (a) => {
        setForm({ title: a.title, category: a.category, content: a.content, tags: a.tags || '', is_published: a.is_published });
        setIsEdit(true); setEditId(a.id); setShowModal(true);
    };
    const viewArticle = async (id) => {
        try {
            const res = await crmAPI.getArticle(id);
            setShowView(res.data);
        } catch (e) { console.error(e); }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            if (isEdit) await crmAPI.updateArticle(editId, form);
            else await crmAPI.createArticle(form);
            setShowModal(false); fetchData();
        } catch (err) { showToast(err.response?.data?.detail || 'Error', 'error'); }
    };

    const handleDelete = async (id) => {
        if (!window.confirm(t('common.confirm_delete', 'هل أنت متأكد؟'))) return;
        try { await crmAPI.deleteArticle(id); fetchData(); } catch (e) { console.error(e); }
    };

    const catLabel = (v) => t(`crm.kb_category_${v}`, v);

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <div className="header-title">
                    <h1 className="workspace-title">📚 {t('crm.kb_title', 'قاعدة المعرفة')}</h1>
                    <p className="workspace-subtitle">{t('crm.kb_subtitle', 'مقالات مساعدة وأسئلة شائعة وأدلة استخدام')}</p>
                </div>
                <div className="header-actions">
                    <button className="btn btn-primary" onClick={openCreate}>+ {t('crm.kb_new', 'مقالة جديدة')}</button>
                </div>
            </div>

            {/* Filters */}
            <div style={{ display: 'flex', gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
                <input className="form-input" style={{ maxWidth: 300 }} placeholder={t('crm.kb_search', 'بحث في المقالات...')}
                    value={search} onChange={e => setSearch(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && fetchData()} />
                <select className="form-input" style={{ maxWidth: 180 }} value={filterCategory} onChange={e => setFilterCategory(e.target.value)}>
                    <option value="">{t('common.all_categories', 'كل الفئات')}</option>
                    {['faq', 'guide', 'policy', 'general'].map(c => <option key={c} value={c}>{catLabel(c)}</option>)}
                </select>
            </div>

            {/* Articles Grid */}
            {loading ? <div className="empty-state">{t('common.loading')}</div> :
            articles.length === 0 ? <div className="empty-state">{t('crm.kb_no_articles', 'لا توجد مقالات')}</div> : (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 16 }}>
                    {articles.map(a => (
                        <div key={a.id} className="section-card" style={{ cursor: 'pointer', transition: 'box-shadow 0.2s' }}
                            onClick={() => viewArticle(a.id)}
                            onMouseEnter={e => e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)'}
                            onMouseLeave={e => e.currentTarget.style.boxShadow = ''}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
                                <span className="badge" style={categoryColors[a.category] || {}}>{catLabel(a.category)}</span>
                                <div style={{ display: 'flex', gap: 4 }}>
                                    {a.is_published ? <span className="status-badge status-active">{t('crm.kb_published', 'منشور')}</span> : <span className="status-badge status-pending">{t('crm.kb_draft', 'مسودة')}</span>}
                                </div>
                            </div>
                            <h3 style={{ fontSize: 16, margin: '8px 0', color: 'var(--text-primary)' }}>{a.title}</h3>
                            <p style={{ fontSize: 13, color: 'var(--text-secondary)', overflow: 'hidden', textOverflow: 'ellipsis', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}>
                                {a.content?.substring(0, 150)}...
                            </p>
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 12, fontSize: 12, color: 'var(--text-secondary)' }}>
                                <span>👤 {a.author_name || '-'}</span>
                                <span>👁 {a.views || 0} | {a.created_at ? formatShortDate(a.created_at) : ''}</span>
                            </div>
                            <div style={{ display: 'flex', gap: 4, marginTop: 8 }} onClick={e => e.stopPropagation()}>
                                <button className="btn btn-secondary btn-sm" onClick={() => openEdit(a)}>{t('crm.edit', 'تعديل')}</button>
                                <button className="btn btn-danger btn-sm" onClick={() => handleDelete(a.id)}>{t('common.delete', 'حذف')}</button>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* View Article Modal */}
            {showView && (
                <div className="modal-overlay" onClick={() => setShowView(null)}>
                    <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: 700, maxHeight: '80vh', overflow: 'auto' }}>
                        <div className="modal-header">
                            <h3>{showView.title}</h3>
                            <button className="btn btn-secondary btn-sm" onClick={() => setShowView(null)}>✕</button>
                        </div>
                        <div className="modal-body">
                            <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
                                <span className="badge" style={categoryColors[showView.category] || {}}>{catLabel(showView.category)}</span>
                                {showView.tags && showView.tags.split(',').map((tag, i) => <span key={i} className="badge badge-secondary">{tag.trim()}</span>)}
                            </div>
                            <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.8, color: 'var(--text-primary)' }}>{showView.content}</div>
                            <div style={{ marginTop: 16, fontSize: 12, color: 'var(--text-secondary)' }}>
                                {t('crm.kb_author', 'الكاتب')}: {showView.author_name || '-'} | {t('crm.kb_views', 'المشاهدات')}: {showView.views || 0} | {showView.created_at ? formatShortDate(showView.created_at) : ''}
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Create/Edit Modal */}
            {showModal && (
                <div className="modal-overlay" onClick={() => setShowModal(false)}>
                    <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: 700 }}>
                        <div className="modal-header"><h3>{isEdit ? t('crm.kb_edit', 'تعديل المقالة') : t('crm.kb_new', 'مقالة جديدة')}</h3></div>
                        <div className="modal-body">
                            <form id="kb-form" onSubmit={handleSubmit}>
                                <div className="form-section"><div className="form-grid">
                                    <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                                        <label className="form-label">{t('crm.kb_article_title', 'عنوان المقالة')}</label>
                                        <input className="form-input" value={form.title} onChange={e => setForm(p => ({ ...p, title: e.target.value }))} required />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">{t('crm.kb_category', 'التصنيف')}</label>
                                        <select className="form-input" value={form.category} onChange={e => setForm(p => ({ ...p, category: e.target.value }))}>
                                            {['faq', 'guide', 'policy', 'general'].map(c => <option key={c} value={c}>{catLabel(c)}</option>)}
                                        </select>
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">{t('crm.kb_tags', 'الوسوم')}</label>
                                        <input className="form-input" value={form.tags} onChange={e => setForm(p => ({ ...p, tags: e.target.value }))} placeholder={t('crm.kb_tags_placeholder', 'كلمات مفصولة بفاصلة')} />
                                    </div>
                                    <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                                        <label className="form-label">{t('crm.kb_content', 'المحتوى')}</label>
                                        <textarea className="form-input" rows={10} value={form.content} onChange={e => setForm(p => ({ ...p, content: e.target.value }))} required />
                                    </div>
                                    <div className="form-group">
                                        <label style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                            <input type="checkbox" checked={form.is_published} onChange={e => setForm(p => ({ ...p, is_published: e.target.checked }))} />
                                            {t('crm.kb_publish', 'نشر المقالة')}
                                        </label>
                                    </div>
                                </div></div>
                            </form>
                        </div>
                        <div className="modal-footer">
                            <button type="submit" form="kb-form" className="btn btn-primary">{isEdit ? t('common.update', 'تحديث') : t('common.create', 'إنشاء')}</button>
                            <button className="btn btn-secondary" onClick={() => setShowModal(false)}>{t('common.cancel', 'إلغاء')}</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default KnowledgeBase;
