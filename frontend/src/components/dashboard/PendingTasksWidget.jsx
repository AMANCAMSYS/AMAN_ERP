import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import api from '../../utils/api';
import { ClipboardList, FileText, ShoppingBag, Clock, AlertCircle, CalendarOff } from 'lucide-react';

const TASK_ICONS = {
    unpaid_invoices: <FileText size={14} className="text-amber-500" />,
    pending_purchases: <ShoppingBag size={14} className="text-blue-500" />,
    pending_approvals: <Clock size={14} className="text-purple-500" />,
    pending_leaves: <CalendarOff size={14} className="text-teal-500" />,
    overdue_invoices: <AlertCircle size={14} className="text-red-500" />,
};

const PendingTasksWidget = ({ config = {} }) => {
    const { t } = useTranslation();
    const [tasks, setTasks] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        api.get('/dashboard/widgets/pending-tasks', { params: { limit: config.limit || 10 } })
            .then(res => setTasks(res.data?.tasks || []))
            .catch(() => {})
            .finally(() => setLoading(false));
    }, [config.limit]);

    if (loading) return (
        <div className="space-y-2">
            {[1,2,3].map(i => <div key={i} className="h-10 bg-slate-100 animate-pulse rounded" />)}
        </div>
    );

    if (!tasks.length) return (
        <div className="flex flex-col items-center justify-center h-full text-slate-400 py-8">
            <ClipboardList size={32} className="mb-2" />
            <span className="text-sm">{t('dashboard.no_pending_tasks') || 'لا توجد مهام معلقة'}</span>
        </div>
    );

    return (
        <div className="space-y-2 overflow-auto max-h-[280px] custom-scrollbar">
            {tasks.map((task, i) => (
                <a
                    key={i}
                    href={task.link || '#'}
                    className="flex items-center justify-between p-2.5 rounded-lg bg-slate-50 hover:bg-slate-100 transition-colors cursor-pointer text-sm group"
                >
                    <div className="flex items-center gap-2">
                        {TASK_ICONS[task.type] || <ClipboardList size={14} className="text-slate-400" />}
                        <span className="font-medium text-slate-700 group-hover:text-primary transition-colors">{task.label}</span>
                    </div>
                    {task.value && (
                        <span className="text-xs font-bold text-slate-500 bg-white px-2 py-0.5 rounded-full border border-slate-200">
                            {typeof task.value === 'number' ? task.value.toLocaleString() : task.value}
                        </span>
                    )}
                </a>
            ))}
        </div>
    );
};

export default PendingTasksWidget;
