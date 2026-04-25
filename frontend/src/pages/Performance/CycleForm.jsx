import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { hrAdvancedAPI } from '../../utils/api';
import '../../index.css';
import '../../components/ModuleStyles.css';
import DateInput from '../../components/common/DateInput';
import BackButton from '../../components/common/BackButton';

const CycleForm = () => {
    const { t, i18n } = useTranslation();
    const isRTL = i18n.language === 'ar';
    const navigate = useNavigate();
    const [saving, setSaving] = useState(false);
    const [form, setForm] = useState({
        name: '',
        period_start: '',
        period_end: '',
        self_assessment_deadline: '',
        manager_review_deadline: '',
    });

    const handleChange = (field, value) => setForm(f => ({ ...f, [field]: value }));

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!form.name || !form.period_start || !form.period_end) {
            alert(t('common.fill_required'));
            return;
        }
        setSaving(true);
        try {
            const payload = {
                ...form,
                self_assessment_deadline: form.self_assessment_deadline || null,
                manager_review_deadline: form.manager_review_deadline || null,
            };
            await hrAdvancedAPI.createCycle(payload);
            navigate('/hr/performance/cycles');
        } catch (e) {
            alert(e.response?.data?.detail || 'Error');
        }
        setSaving(false);
    };

    return (
        <div className="module-container" dir={isRTL ? 'rtl' : 'ltr'}>
            <BackButton />
            <h1>{t('performance.new_cycle')}</h1>
            <p style={{ color: '#6b7280', marginBottom: 24 }}>{t('performance.cycle_form_subtitle')}</p>

            <form onSubmit={handleSubmit} style={{ maxWidth: 600 }}>
                <div className="form-group">
                    <label>{t('performance.cycle_name')} *</label>
                    <input className="form-control" value={form.name}
                        onChange={e => handleChange('name', e.target.value)}
                        placeholder={t('performance.cycle_name_placeholder')} required />
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                    <div className="form-group">
                        <label>{t('performance.period_start')} *</label>
                        <DateInput value={form.period_start} onChange={v => handleChange('period_start', v)} required />
                    </div>
                    <div className="form-group">
                        <label>{t('performance.period_end')} *</label>
                        <DateInput value={form.period_end} onChange={v => handleChange('period_end', v)} required />
                    </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                    <div className="form-group">
                        <label>{t('performance.self_deadline')}</label>
                        <DateInput value={form.self_assessment_deadline} onChange={v => handleChange('self_assessment_deadline', v)} />
                    </div>
                    <div className="form-group">
                        <label>{t('performance.manager_deadline')}</label>
                        <DateInput value={form.manager_review_deadline} onChange={v => handleChange('manager_review_deadline', v)} />
                    </div>
                </div>

                <div style={{ display: 'flex', gap: 12, marginTop: 24 }}>
                    <button type="submit" className="btn btn-primary" disabled={saving}>
                        {saving ? t('common.saving') : t('performance.create_cycle')}
                    </button>
                    <button type="button" className="btn btn-secondary" onClick={() => navigate('/hr/performance/cycles')}>
                        {t('common.cancel')}
                    </button>
                </div>
            </form>
        </div>
    );
};

export default CycleForm;
