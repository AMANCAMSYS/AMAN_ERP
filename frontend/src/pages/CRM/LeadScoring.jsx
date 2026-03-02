import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { crmAPI } from '../../utils/api'
import BackButton from '../../components/common/BackButton'
import '../../components/ModuleStyles.css'
import { useToast } from '../../context/ToastContext'

function LeadScoring() {
    const { t } = useTranslation()
  const { showToast } = useToast()
    const [tab, setTab] = useState('rules')
    const [rules, setRules] = useState([])
    const [scores, setScores] = useState([])
    const [loading, setLoading] = useState(true)
    const [showForm, setShowForm] = useState(false)
    const [gradeFilter, setGradeFilter] = useState('')
    const [calculating, setCalculating] = useState(false)
    const [form, setForm] = useState({
        rule_name: '', field_name: 'source', operator: 'equals', field_value: '', score: 10
    })

    useEffect(() => { fetchData() }, [tab, gradeFilter])

    const fetchData = async () => {
        try {
            setLoading(true)
            if (tab === 'rules') {
                const res = await crmAPI.listScoringRules()
                setRules(res.data)
            } else {
                const params = gradeFilter ? { grade: gradeFilter } : {}
                const res = await crmAPI.getLeadScores(params)
                setScores(res.data)
            }
        } catch (err) {
            console.error('Failed to fetch lead scoring data', err)
        } finally {
            setLoading(false)
        }
    }

    const handleCreateRule = async (e) => {
        e.preventDefault()
        try {
            await crmAPI.createScoringRule({
                rule_name: form.rule_name,
                field_name: form.field_name,
                operator: form.operator,
                field_value: form.field_value,
                score: parseInt(form.score)
            })
            setShowForm(false)
            setForm({ rule_name: '', field_name: 'source', operator: 'equals', field_value: '', score: 10 })
            fetchData()
        } catch (err) {
            showToast(err.response?.data?.detail || 'Error', 'error')
        }
    }

    const handleDeleteRule = async (id) => {
        if (!confirm(t('common.confirm_delete', 'هل أنت متأكد من الحذف؟'))) return
        try {
            await crmAPI.deleteScoringRule(id)
            fetchData()
        } catch (err) {
            showToast(err.response?.data?.detail || 'Error', 'error')
        }
    }

    const handleCalculate = async () => {
        try {
            setCalculating(true)
            const res = await crmAPI.calculateLeadScore()
            showToast(res.data.message || `تم تسجيل ${res.data.scored} فرصة`, 'success')
            if (tab === 'scores') fetchData()
        } catch (err) {
            showToast(err.response?.data?.detail || 'Error', 'error')
        } finally {
            setCalculating(false)
        }
    }

    const FIELDS = [
        { value: 'source', label: t('crm.field_source', 'المصدر') },
        { value: 'stage', label: t('crm.field_stage', 'المرحلة') },
        { value: 'expected_value', label: t('crm.field_value', 'القيمة المتوقعة') },
        { value: 'probability', label: t('crm.field_probability', 'الاحتمالية') },
        { value: 'contact_email', label: t('crm.field_email', 'البريد') },
        { value: 'contact_phone', label: t('crm.field_phone', 'الهاتف') }
    ]

    const OPERATORS = [
        { value: 'equals', label: t('crm.op_equals', 'يساوي') },
        { value: 'contains', label: t('crm.op_contains', 'يحتوي') },
        { value: 'greater_than', label: t('crm.op_gt', 'أكبر من') },
        { value: 'less_than', label: t('crm.op_lt', 'أقل من') },
        { value: 'exists', label: t('crm.op_exists', 'موجود') }
    ]

    const getGradeColor = (grade) => {
        switch (grade) {
            case 'A': return '#22c55e'
            case 'B': return '#3b82f6'
            case 'C': return '#f97316'
            case 'D': return '#ef4444'
            default: return '#6b7280'
        }
    }

    return (
        <div className="workspace fade-in">
            <div className="workspace-header">
                <BackButton />
                <div>
                    <h1 className="workspace-title">{t('crm.lead_scoring', 'تقييم العملاء المحتملين')}</h1>
                    <p className="workspace-subtitle">{t('crm.lead_scoring_desc', 'إعداد قواعد التقييم وحساب نقاط الفرص تلقائياً')}</p>
                </div>
            </div>

            {/* Tabs + Actions */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <div className="tabs">
                    <button className={`tab ${tab === 'rules' ? 'active' : ''}`} onClick={() => setTab('rules')}>
                        {t('crm.scoring_rules', 'قواعد التقييم')}
                    </button>
                    <button className={`tab ${tab === 'scores' ? 'active' : ''}`} onClick={() => setTab('scores')}>
                        {t('crm.lead_scores', 'نقاط الفرص')}
                    </button>
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                    <button className="btn btn-warning btn-sm" onClick={handleCalculate} disabled={calculating}>
                        {calculating ? t('common.calculating', 'جاري الحساب...') : t('crm.calculate_scores', 'حساب النقاط')}
                    </button>
                    {tab === 'rules' && (
                        <button className="btn btn-primary btn-sm" onClick={() => setShowForm(!showForm)}>
                            {showForm ? t('common.cancel', 'إلغاء') : t('crm.add_rule', '+ قاعدة جديدة')}
                        </button>
                    )}
                </div>
            </div>

            {/* Create Rule Form */}
            {showForm && tab === 'rules' && (
                <div className="section-card" style={{ marginBottom: 16 }}>
                    <h3 className="section-title">{t('crm.new_rule', 'قاعدة تقييم جديدة')}</h3>
                    <form onSubmit={handleCreateRule}>
                        <div className="form-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 12 }}>
                            <div className="form-group">
                                <label className="form-label">{t('crm.rule_name', 'اسم القاعدة')}</label>
                                <input className="form-input" required value={form.rule_name}
                                    onChange={e => setForm({ ...form, rule_name: e.target.value })} />
                            </div>
                            <div className="form-group">
                                <label className="form-label">{t('crm.field', 'الحقل')}</label>
                                <select className="form-input" value={form.field_name}
                                    onChange={e => setForm({ ...form, field_name: e.target.value })}>
                                    {FIELDS.map(f => <option key={f.value} value={f.value}>{f.label}</option>)}
                                </select>
                            </div>
                            <div className="form-group">
                                <label className="form-label">{t('crm.operator', 'المعامل')}</label>
                                <select className="form-input" value={form.operator}
                                    onChange={e => setForm({ ...form, operator: e.target.value })}>
                                    {OPERATORS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                                </select>
                            </div>
                            <div className="form-group">
                                <label className="form-label">{t('crm.field_value', 'القيمة')}</label>
                                <input className="form-input" value={form.field_value}
                                    onChange={e => setForm({ ...form, field_value: e.target.value })} />
                            </div>
                            <div className="form-group">
                                <label className="form-label">{t('crm.score', 'النقاط')}</label>
                                <input className="form-input" type="number" min="1" max="100" value={form.score}
                                    onChange={e => setForm({ ...form, score: e.target.value })} />
                            </div>
                        </div>
                        <div style={{ marginTop: 12 }}>
                            <button type="submit" className="btn btn-primary btn-sm">{t('common.save', 'حفظ')}</button>
                        </div>
                    </form>
                </div>
            )}

            {loading ? (
                <div className="loading-spinner"><div className="spinner"></div></div>
            ) : tab === 'rules' ? (
                /* Rules Table */
                <div className="section-card">
                    <h3 className="section-title">{t('crm.scoring_rules', 'قواعد التقييم')} ({rules.length})</h3>
                    {rules.length === 0 ? (
                        <p style={{ color: '#9ca3af', textAlign: 'center', padding: 24 }}>
                            {t('crm.no_rules', 'لا توجد قواعد بعد. أضف أول قاعدة تقييم.')}
                        </p>
                    ) : (
                        <div className="data-table-container">
                            <table className="data-table">
                                <thead>
                                    <tr>
                                        <th>{t('crm.rule_name', 'اسم القاعدة')}</th>
                                        <th>{t('crm.field', 'الحقل')}</th>
                                        <th>{t('crm.operator', 'المعامل')}</th>
                                        <th>{t('crm.field_value', 'القيمة')}</th>
                                        <th>{t('crm.score', 'النقاط')}</th>
                                        <th>{t('common.status', 'الحالة')}</th>
                                        <th>{t('common.actions', 'إجراءات')}</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {rules.map(r => (
                                        <tr key={r.id}>
                                            <td style={{ fontWeight: 600 }}>{r.rule_name}</td>
                                            <td>{r.field_name}</td>
                                            <td><span className="badge badge-info">{r.operator}</span></td>
                                            <td>{r.field_value || '—'}</td>
                                            <td>
                                                <span className="badge badge-primary" style={{ fontSize: '0.875rem' }}>
                                                    +{r.score}
                                                </span>
                                            </td>
                                            <td>
                                                <span className={`badge ${r.is_active ? 'badge-success' : 'badge-secondary'}`}>
                                                    {r.is_active ? t('common.active', 'نشط') : t('common.inactive', 'غير نشط')}
                                                </span>
                                            </td>
                                            <td>
                                                <button className="btn btn-danger btn-sm" onClick={() => handleDeleteRule(r.id)}>
                                                    {t('common.delete', 'حذف')}
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            ) : (
                /* Scores Table */
                <div className="section-card">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                        <h3 className="section-title" style={{ marginBottom: 0 }}>
                            {t('crm.lead_scores', 'نقاط الفرص')} ({scores.length})
                        </h3>
                        <select className="form-input" style={{ width: 'auto', minWidth: 150 }}
                            value={gradeFilter} onChange={e => setGradeFilter(e.target.value)}>
                            <option value="">{t('crm.all_grades', 'جميع التصنيفات')}</option>
                            <option value="A">A - {t('crm.grade_excellent', 'ممتاز')}</option>
                            <option value="B">B - {t('crm.grade_good', 'جيد')}</option>
                            <option value="C">C - {t('crm.grade_average', 'متوسط')}</option>
                            <option value="D">D - {t('crm.grade_low', 'منخفض')}</option>
                        </select>
                    </div>
                    {scores.length === 0 ? (
                        <p style={{ color: '#9ca3af', textAlign: 'center', padding: 24 }}>
                            {t('crm.no_scores', 'لم يتم حساب النقاط بعد. اضغط "حساب النقاط" أعلاه.')}
                        </p>
                    ) : (
                        <div className="data-table-container">
                            <table className="data-table">
                                <thead>
                                    <tr>
                                        <th>{t('crm.opportunity', 'الفرصة')}</th>
                                        <th>{t('common.customer', 'العميل')}</th>
                                        <th>{t('crm.stage', 'المرحلة')}</th>
                                        <th>{t('crm.total_score', 'النقاط')}</th>
                                        <th>{t('crm.grade', 'التصنيف')}</th>
                                        <th>{t('crm.last_scored', 'آخر تقييم')}</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {scores.map(s => (
                                        <tr key={s.id}>
                                            <td style={{ fontWeight: 600 }}>{s.title}</td>
                                            <td>{s.customer_name || s.contact_name || '—'}</td>
                                            <td>
                                                <span className={`badge ${s.stage === 'won' ? 'badge-success' : s.stage === 'lost' ? 'badge-danger' : 'badge-info'}`}>
                                                    {t(`crm.stage_${s.stage}`, s.stage)}
                                                </span>
                                            </td>
                                            <td>
                                                <span style={{
                                                    fontWeight: 700, fontSize: '1rem',
                                                    color: getGradeColor(s.grade)
                                                }}>
                                                    {s.total_score}
                                                </span>
                                            </td>
                                            <td>
                                                <span style={{
                                                    display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                                                    width: 32, height: 32, borderRadius: '50%',
                                                    backgroundColor: getGradeColor(s.grade) + '20',
                                                    color: getGradeColor(s.grade), fontWeight: 700, fontSize: '0.875rem'
                                                }}>
                                                    {s.grade}
                                                </span>
                                            </td>
                                            <td style={{ color: '#9ca3af', fontSize: '0.875rem' }}>
                                                {s.last_scored_at ? new Date(s.last_scored_at).toLocaleDateString('ar-SA') : '—'}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}

export default LeadScoring
