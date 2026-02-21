import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { format, startOfWeek, endOfWeek, addDays, eachDayOfInterval } from 'date-fns';
import { ar, enUS } from 'date-fns/locale';
import { ChevronRight, ChevronLeft, Save, Trash2, CheckCircle2 } from 'lucide-react';
import { projectsAPI } from '../../utils/api';
import { toastEmitter } from '../../utils/toastEmitter';
import './Timesheets.css';

export default function Timesheets({ projectId, tasks = [] }) {
    const { t, i18n } = useTranslation();
    const isRTL = i18n.language === 'ar';
    const locale = isRTL ? ar : enUS;

    const [currentWeekStart, setCurrentWeekStart] = useState(startOfWeek(new Date(), { weekStartsOn: 6 })); // Week starts Saturday
    const [timesheets, setTimesheets] = useState([]);
    const [loading, setLoading] = useState(false);
    const [gridData, setGridData] = useState({});
    const [selectedIds, setSelectedIds] = useState([]);
    const [approving, setApproving] = useState(false);

    useEffect(() => {
        fetchTimesheets();
    }, [projectId, currentWeekStart]);

    const fetchTimesheets = async () => {
        setLoading(true);
        try {
            const res = await projectsAPI.listTimesheets(projectId);
            setTimesheets(res.data || []);
            setSelectedIds([]); // Clear selection on reload
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const weekDays = eachDayOfInterval({
        start: currentWeekStart,
        end: addDays(currentWeekStart, 6)
    });

    // Group timesheets by Task + Date
    const getEntry = (taskId, date) => {
        const dateStr = format(date, 'yyyy-MM-dd');
        return timesheets.find(ts => ts.task_id === taskId && ts.date === dateStr);
    };

    const getHours = (taskId, date) => {
        const dateStr = format(date, 'yyyy-MM-dd');
        // Check local state first
        if (gridData[taskId] && gridData[taskId][dateStr] !== undefined) {
            return gridData[taskId][dateStr];
        }
        // Then check fetched data
        const entry = getEntry(taskId, date);
        return entry ? entry.hours : '';
    };

    const handleInputChange = (taskId, date, value) => {
        const entry = getEntry(taskId, date);
        if (entry && entry.status === 'approved') return;

        const dateStr = format(date, 'yyyy-MM-dd');
        setGridData(prev => ({
            ...prev,
            [taskId]: {
                ...(prev[taskId] || {}),
                [dateStr]: value
            }
        }));
    };

    const toggleSelect = (id) => {
        setSelectedIds(prev =>
            prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
        );
    };

    const handleSave = async () => {
        setSubmitting(true);
        try {
            // Process gridData changes
            const promises = [];
            for (const taskId in gridData) {
                for (const dateStr in gridData[taskId]) {
                    const hours = parseFloat(gridData[taskId][dateStr]);
                    if (isNaN(hours) && gridData[taskId][dateStr] !== '') continue;

                    // Find existing entry
                    const existing = timesheets.find(ts => ts.task_id == taskId && ts.date === dateStr);

                    if (existing) {
                        if (gridData[taskId][dateStr] === '' || hours === 0) {
                            // Delete if cleared
                            promises.push(projectsAPI.deleteTimesheet(existing.id));
                        } else if (hours !== existing.hours) {
                            // Update
                            promises.push(projectsAPI.updateTimesheet(existing.id, { hours }));
                        }
                    } else if (hours > 0) {
                        // Create
                        promises.push(projectsAPI.createTimesheet(projectId, {
                            task_id: parseInt(taskId),
                            date: dateStr,
                            hours: hours,
                            description: 'Logged via grid',
                            status: 'draft'
                        }));
                    }
                }
            }

            await Promise.all(promises);
            toastEmitter.emit(t('common.save_success', 'تم الحفظ بنجاح'), 'success');
            setGridData({}); // Clear local changes
            fetchTimesheets(); // Reload
        } catch (err) {
            toastEmitter.emit(t('common.save_error', 'حدث خطأ أثناء الحفظ'), 'error');
        } finally {
            setSubmitting(false);
        }
    };

    const handleApprove = async () => {
        if (selectedIds.length === 0) return;
        setApproving(true);
        try {
            await projectsAPI.approveTimesheets(projectId, { timesheet_ids: selectedIds });
            toastEmitter.emit(t('projects.approve_success', 'تم اعتماد السجلات بنجاح'), 'success');
            fetchTimesheets();
        } catch (err) {
            console.error(err);
        } finally {
            setApproving(false);
        }
    };

    const changeWeek = (direction) => {
        setCurrentWeekStart(prev => addDays(prev, direction * 7));
    };

    return (
        <div className="timesheet-container fade-in">
            {/* Toolbar */}
            <div className="d-flex align-items-center justify-content-between mb-3">
                <div className="d-flex align-items-center gap-3">
                    <div className="btn-group">
                        <button className="btn btn-outline-secondary btn-sm" onClick={() => changeWeek(-1)}>
                            <ChevronRight size={16} />
                        </button>
                        <button className="btn btn-outline-secondary btn-sm" onClick={() => setCurrentWeekStart(startOfWeek(new Date(), { weekStartsOn: 6 }))}>
                            {t('common.today', 'اليوم')}
                        </button>
                        <button className="btn btn-outline-secondary btn-sm" onClick={() => changeWeek(1)}>
                            <ChevronLeft size={16} /> {/* RTL logic: Left is Next in styling usually, but let's assume standard icon direction needs fix if RTL */}
                        </button>
                    </div>
                    <h5 className="mb-0">
                        {format(currentWeekStart, 'd MMM', { locale })} - {format(addDays(currentWeekStart, 6), 'd MMM yyyy', { locale })}
                    </h5>
                </div>
                <div className="d-flex gap-2">
                    {selectedIds.length > 0 && (
                        <button className="btn btn-success" onClick={handleApprove} disabled={approving}>
                            <CheckCircle2 size={16} /> {approving ? t('common.loading') : `${t('common.approve', 'اعتماد')} (${selectedIds.length})`}
                        </button>
                    )}
                    <button className="btn btn-primary" onClick={handleSave} disabled={submitting}>
                        <Save size={16} /> {submitting ? t('common.saving') : t('common.save_changes', 'حفظ التغييرات')}
                    </button>
                </div>
            </div>

            {/* Grid */}
            <div className="table-responsive">
                <table className="table table-bordered timesheet-table">
                    <thead className="table-light">
                        <tr>
                            <th style={{ width: '25%' }}>{t('projects.task', 'المهمة')}</th>
                            {weekDays.map(day => (
                                <th key={day.toISOString()} className="text-center" style={{ width: '10%' }}>
                                    <div className="small text-muted">{format(day, 'EEE', { locale })}</div>
                                    <div>{format(day, 'd')}</div>
                                </th>
                            ))}
                            <th className="text-center" style={{ width: '5%' }}>{t('projects.total', 'المجموع')}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {tasks.map(task => (
                            <tr key={task.id}>
                                <td className="align-middle">
                                    <div className="fw-medium">{task.task_name}</div>
                                    <small className="text-muted">{task.status}</small>
                                </td>
                                {weekDays.map(day => {
                                    const entry = getEntry(task.id, day);
                                    const isApproved = entry?.status === 'approved';
                                    const isSelected = entry && selectedIds.includes(entry.id);

                                    return (
                                        <td key={day.toISOString()} className={`p-1 position-relative ${isApproved ? 'bg-light-success' : ''}`}>
                                            <input
                                                type="number"
                                                className={`form-input form-input-sm text-center border-0 ${isApproved ? 'bg-transparent text-success fw-bold' : ''}`}
                                                value={getHours(task.id, day)}
                                                onChange={(e) => handleInputChange(task.id, day, e.target.value)}
                                                disabled={isApproved}
                                                min="0" max="24" step="0.5"
                                            />
                                            {entry && !isApproved && (
                                                <div className="selection-overlay" onClick={() => toggleSelect(entry.id)}>
                                                    <input type="checkbox" checked={isSelected} readOnly />
                                                </div>
                                            )}
                                            {isApproved && (
                                                <div className="approved-indicator">
                                                    <CheckCircle2 size={10} />
                                                </div>
                                            )}
                                        </td>
                                    );
                                })}
                                <td className="text-center align-middle fw-bold bg-light">
                                    {/* Calculated Total for Row */}
                                    {weekDays.reduce((acc, day) => acc + (parseFloat(getHours(task.id, day)) || 0), 0)}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {tasks.length === 0 && (
                <div className="text-center py-4 text-muted">
                    {t('projects.no_tasks_timesheet', 'يرجى إضافة مهام للمشروع أولاً لتسجيل الوقت.')}
                </div>
            )}
        </div>
    );
}
