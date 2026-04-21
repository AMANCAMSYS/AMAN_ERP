import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { selfServiceAPI } from '../../utils/api';
import { toastEmitter } from '../../utils/toastEmitter';
import BackButton from '../../components/common/BackButton';
import '../../components/ModuleStyles.css';
import DateInput from '../../components/common/DateInput';

const LeaveRequestForm = () => {
    const { t } = useTranslation();
    const navigate = useNavigate();
    const [loading, setLoading] = useState(false);
    const [form, setForm] = useState({
        leave_type: 'annual',
        start_date: '',
        end_date: '',
        reason: '',
    });

    const leaveTypes = [
        { value: 'annual', label: t('self_service.leave_annual') },
        { value: 'sick', label: t('self_service.leave_sick') },
        { value: 'unpaid', label: t('self_service.leave_unpaid') },
        { value: 'emergency', label: t('self_service.leave_emergency') },
    ];

    const handleChange = (e) => {
        setForm(prev => ({ ...prev, [e.target.name]: e.target.value }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!form.start_date || !form.end_date) {
            toastEmitter.emit(t('self_service.dates_required'), 'error');
            return;
        }
        setLoading(true);
        try {
            await selfServiceAPI.submitLeaveRequest(form);
            toastEmitter.emit(t('self_service.leave_submitted'), 'success');
            navigate('/hr/self-service');
        } catch (err) {
            toastEmitter.emit(err.response?.data?.detail || t('common.error'), 'error');
        } finally {
            setLoading(false);
        }
    };

    const days = form.start_date && form.end_date
        ? Math.max(0, Math.ceil((new Date(form.end_date) - new Date(form.start_date)) / 86400000) + 1)
        : 0;

    return (
        <div className="module-container">
            <div className="module-header">
                <BackButton />
                <h1>{t('self_service.new_leave_request')}</h1>
            </div>

            <form className="card" onSubmit={handleSubmit} style={{ maxWidth: 600 }}>
                <div className="form-group">
                    <label>{t('self_service.leave_type')}</label>
                    <select name="leave_type" value={form.leave_type} onChange={handleChange} className="form-control">
                        {leaveTypes.map(lt => (
                            <option key={lt.value} value={lt.value}>{lt.label}</option>
                        ))}
                    </select>
                </div>

                <div className="form-group">
                    <label>{t('self_service.start_date')}</label>
                    <DateInput name="start_date" value={form.start_date} onChange={handleChange} className="form-control" required />
                </div>

                <div className="form-group">
                    <label>{t('self_service.end_date')}</label>
                    <DateInput name="end_date" value={form.end_date} onChange={handleChange} className="form-control" required />
                </div>

                {days > 0 && (
                    <div className="form-group">
                        <span className="text-muted">{t('self_service.total_days')}: <strong>{days}</strong></span>
                    </div>
                )}

                <div className="form-group">
                    <label>{t('self_service.reason')}</label>
                    <textarea name="reason" value={form.reason} onChange={handleChange} className="form-control" rows={3} />
                </div>

                <div style={{ display: 'flex', gap: 12, marginTop: 16 }}>
                    <button type="submit" className="btn btn-primary" disabled={loading}>
                        {loading ? t('common.saving') : t('self_service.submit_request')}
                    </button>
                    <button type="button" className="btn btn-secondary" onClick={() => navigate('/hr/self-service')}>
                        {t('common.cancel')}
                    </button>
                </div>
            </form>
        </div>
    );
};

export default LeaveRequestForm;
