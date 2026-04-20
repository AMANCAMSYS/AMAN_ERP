import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { format, differenceInDays, addDays, startOfWeek, endOfWeek, isWithinInterval } from 'date-fns';
import { ar, enUS } from 'date-fns/locale';
import './GanttChart.css';
import { formatDate, formatDateTime } from '../../utils/dateUtils';

export default function GanttChart({ tasks = [] }) {
    const { t, i18n } = useTranslation();
    const isRTL = i18n.language === 'ar';
    const locale = isRTL ? ar : enUS;

    // Filter tasks with dates
    const validTasks = useMemo(() => tasks.filter(t => t.start_date && t.end_date), [tasks]);

    if (validTasks.length === 0) {
        return <div className="text-center py-5 text-muted">{t('projects.gantt.no_tasks')}</div>;
    }

    // Calculate Timeline Range
    const { startDate, endDate, totalDays, dates } = useMemo(() => {
        if (validTasks.length === 0) return { startDate: new Date(), endDate: new Date(), totalDays: 0, dates: [] };

        const starts = validTasks.map(t => new Date(t.start_date));
        const ends = validTasks.map(t => new Date(t.end_date));

        // Buffer of 3 days before and after
        const minDate = addDays(new Date(Math.min(...starts)), -3);
        const maxDate = addDays(new Date(Math.max(...ends)), 7); // Extended buffer

        const days = differenceInDays(maxDate, minDate) + 1;
        const dateArray = Array.from({ length: days }, (_, i) => addDays(minDate, i));

        return { startDate: minDate, endDate: maxDate, totalDays: days, dates: dateArray };
    }, [validTasks]);

    // Grid Configuration
    const colWidth = 40;
    const headerHeight = 50;
    const rowHeight = 40;

    return (
        <div className="gantt-container" style={{ direction: 'ltr' }}> {/* Always LTR for timeline logic simplicity, content aligned via CSS */}
            <div className="gantt-scroll-container">
                <div className="gantt-header" style={{ width: totalDays * colWidth, height: headerHeight }}>
                    {dates.map((date, index) => (
                        <div key={index} className={`gantt-header-cell ${date.getDay() === 0 || date.getDay() === 6 ? 'weekend' : ''}`}
                            style={{ left: index * colWidth, width: colWidth }}>
                            <div className="day-name">{format(date, 'EE', { locale })}</div>
                            <div className="day-number">{format(date, 'd')}</div>
                        </div>
                    ))}
                </div>

                <div className="gantt-body" style={{ width: totalDays * colWidth, height: validTasks.length * rowHeight }}>
                    {/* Background Grid */}
                    {dates.map((_, index) => (
                        <div key={index} className="gantt-grid-column"
                            style={{ left: index * colWidth, width: colWidth, height: '100%' }} />
                    ))}

                    {/* Task Bars */}
                    {validTasks.map((task, index) => {
                        const taskStart = new Date(task.start_date);
                        const taskEnd = new Date(task.end_date);
                        const offsetDays = differenceInDays(taskStart, startDate);
                        const durationDays = differenceInDays(taskEnd, taskStart) + 1;

                        const left = offsetDays * colWidth;
                        const width = durationDays * colWidth;

                        return (
                            <div key={task.id} className="gantt-task-row" style={{ top: index * rowHeight, height: rowHeight }}>
                                <div className="gantt-task-bar"
                                    style={{
                                        left, width,
                                        backgroundColor: task.status === 'completed' ? '#28a745' : '#007bff'
                                    }}
                                    title={`${task.task_name} (${formatDate(task.start_date)} - ${formatDate(task.end_date)})`}>
                                    <span className="gantt-task-label">{task.task_name}</span>
                                    <div className="gantt-task-progress" style={{ width: `${task.progress || 0}%` }}></div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>
            {/* Legend or Task List Sidebar could be added here */}
        </div>
    );
}
