import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { selfServiceAPI } from '../../utils/api';
import { useToast } from '../../context/ToastContext';
import { User, Save } from 'lucide-react';
import BackButton from '../../components/common/BackButton';
import '../../components/ModuleStyles.css';

const ProfileEdit = () => {
    const { t } = useTranslation();
    const navigate = useNavigate();
    const { showToast } = useToast();
    const [profile, setProfile] = useState(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [form, setForm] = useState({ phone: '', email: '' });

    useEffect(() => {
        fetchProfile();
    }, []);

    const fetchProfile = async () => {
        setLoading(true);
        try {
            const res = await selfServiceAPI.getProfile();
            const p = res.data?.data || res.data;
            setProfile(p);
            setForm({ phone: p.phone || '', email: p.email || '' });
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleChange = (e) => {
        setForm(prev => ({ ...prev, [e.target.name]: e.target.value }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSaving(true);
        try {
            await selfServiceAPI.updateProfile(form);
            showToast(t('self_service.profile_updated'), 'success');
            navigate('/hr/self-service');
        } catch (err) {
            showToast(err.response?.data?.detail || t('common.error'), 'error');
        } finally {
            setSaving(false);
        }
    };

    if (loading) return <div className="module-loading"><div className="spinner" /></div>;
    if (!profile) return <div className="module-container"><BackButton /><p>{t('common.error')}</p></div>;

    return (
        <div className="module-container">
            <div className="module-header">
                <BackButton />
                <h1><User size={22} /> {t('self_service.edit_profile')}</h1>
            </div>

            <div className="card" style={{ maxWidth: 600 }}>
                {/* Read-only info */}
                <div style={{ marginBottom: 20, padding: 16, background: 'var(--bg-secondary, #f8fafc)', borderRadius: 8 }}>
                    <div><strong>{t('self_service.name')}:</strong> {profile.first_name} {profile.last_name}</div>
                    <div><strong>{t('self_service.department')}:</strong> {profile.department || '-'}</div>
                    <div><strong>{t('self_service.position')}:</strong> {profile.position || '-'}</div>
                    <div><strong>{t('self_service.hire_date')}:</strong> {profile.hire_date || '-'}</div>
                </div>

                {/* Editable fields */}
                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label>{t('self_service.phone')}</label>
                        <input type="tel" name="phone" value={form.phone} onChange={handleChange} className="form-control" />
                    </div>

                    <div className="form-group">
                        <label>{t('self_service.email')}</label>
                        <input type="email" name="email" value={form.email} onChange={handleChange} className="form-control" />
                    </div>

                    <div style={{ display: 'flex', gap: 12, marginTop: 16 }}>
                        <button type="submit" className="btn btn-primary" disabled={saving}>
                            <Save size={16} /> {saving ? t('common.saving') : t('common.save')}
                        </button>
                        <button type="button" className="btn btn-secondary" onClick={() => navigate('/hr/self-service')}>
                            {t('common.cancel')}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default ProfileEdit;
