/**
 * AMAN ERP - Date Utilities
 * مساعدات التواريخ مع دعم المنطقة الزمنية للشركة
 *
 * Architecture:
 *  - DB stores UTC (TIMESTAMPTZ)
 *  - Backend returns ISO 8601 strings (e.g. "2026-02-21T10:30:00+00:00")
 *  - Frontend converts to company timezone for display
 */

import dayjs from 'dayjs';
import utc from 'dayjs/plugin/utc';
import timezone from 'dayjs/plugin/timezone';
import relativeTime from 'dayjs/plugin/relativeTime';
import localizedFormat from 'dayjs/plugin/localizedFormat';
import 'dayjs/locale/ar';

// تحميل الإضافات
dayjs.extend(utc);
dayjs.extend(timezone);
dayjs.extend(relativeTime);
dayjs.extend(localizedFormat);

// Latin numerals by default
dayjs.locale('en');

/**
 * الحصول على المنطقة الزمنية للشركة من localStorage
 * @returns {string} - e.g. "Europe/Istanbul", "Asia/Damascus"
 */
export const getCompanyTimezone = () => {
    try {
        const user = JSON.parse(localStorage.getItem('user') || '{}');
        return user.timezone || 'UTC';
    } catch {
        return 'UTC';
    }
};

/**
 * تحويل تاريخ UTC إلى المنطقة الزمنية للشركة
 * @param {string|Date} date - تاريخ UTC
 * @param {string} [tz] - المنطقة الزمنية (اختياري، يُستخدم توقيت الشركة افتراضيًا)
 * @returns {dayjs.Dayjs}
 */
const toCompanyTz = (date, tz) => {
    const targetTz = tz || getCompanyTimezone();
    // If the string lacks timezone info (no Z, no +HH:MM), treat it as UTC
    if (typeof date === 'string' && !date.endsWith('Z') && !/[+-]\d{2}:?\d{2}$/.test(date)) {
        return dayjs.utc(date).tz(targetTz);
    }
    return dayjs(date).tz(targetTz);
};

/**
 * تنسيق التاريخ بتوقيت الشركة
 * @param {string|Date} date
 * @param {string} [format]
 * @param {string} [tz]
 * @returns {string}
 */
export const formatDate = (date, format = 'YYYY/MM/DD', tz) => {
    if (!date) return '-';
    return toCompanyTz(date, tz).format(format);
};

/**
 * تنسيق التاريخ والوقت بتوقيت الشركة
 * @param {string|Date} date
 * @param {string} [tz]
 * @returns {string}
 */
export const formatDateTime = (date, tz) => {
    if (!date) return '-';
    return toCompanyTz(date, tz).format('YYYY/MM/DD HH:mm');
};

/**
 * تنسيق الوقت النسبي (منذ...) بتوقيت الشركة
 * @param {string|Date} date
 * @returns {string}
 */
export const formatRelative = (date) => {
    if (!date) return '-';
    return toCompanyTz(date).locale('ar').fromNow();
};

/**
 * تنسيق التاريخ القصير بتوقيت الشركة
 * @param {string|Date} date
 * @param {string} [tz]
 * @returns {string}
 */
export const formatShortDate = (date, tz) => {
    if (!date) return '-';
    return toCompanyTz(date, tz).format('YYYY/MM/DD');
};

/**
 * الحصول على التاريخ للـ input[type=date] — لا يحتاج تحويل منطقة زمنية
 * @param {string|Date} date
 * @returns {string} - YYYY-MM-DD
 */
export const toInputDate = (date) => {
    if (!date) return '';
    return dayjs(date).format('YYYY-MM-DD');
};

/**
 * التحقق من صلاحية التاريخ
 * @param {string|Date} date
 * @returns {boolean}
 */
export const isValidDate = (date) => {
    return date && dayjs(date).isValid();
};

export default dayjs;
