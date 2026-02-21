/**
 * AMAN ERP - Date Utilities
 * مساعدات التواريخ مع دعم اللغة العربية
 */

import dayjs from 'dayjs';
import 'dayjs/locale/ar-sa';
import relativeTime from 'dayjs/plugin/relativeTime';
import localizedFormat from 'dayjs/plugin/localizedFormat';

// تحميل الإضافات
dayjs.extend(relativeTime);
dayjs.extend(localizedFormat);

// تعيين اللغة الافتراضية - السعودية
// Default to 'en' to ensure Latin numerals (1, 2, 3) are used globally
dayjs.locale('en');

/**
 * تنسيق التاريخ
 * @param {string|Date} date - التاريخ
 * @param {string} format - الصيغة (اختياري)
 * @returns {string}
 */
export const formatDate = (date, format = 'YYYY/MM/DD') => {
    if (!date) return '-';
    return dayjs(date).format(format);
};

/**
 * تنسيق التاريخ والوقت
 * @param {string|Date} date - التاريخ
 * @returns {string}
 */
export const formatDateTime = (date) => {
    if (!date) return '-';
    return dayjs(date).format('YYYY/MM/DD HH:mm');
};

/**
 * تنسيق الوقت النسبي (منذ...)
 * @param {string|Date} date - التاريخ
 * @returns {string}
 */
export const formatRelative = (date) => {
    if (!date) return '-';
    // For relative time like "منذ ساعة", we might still want Arabic text but Latin numerals?
    // dayjs handles this via locale. If we want Arabic text, we use 'ar'.
    return dayjs(date).locale('ar').fromNow();
};

/**
 * تنسيق التاريخ القصير
 * @param {string|Date} date - التاريخ
 * @returns {string}
 */
export const formatShortDate = (date) => {
    if (!date) return '-';
    return dayjs(date).format('YYYY/MM/DD');
};

/**
 * الحصول على التاريخ للـ input[type=date]
 * @param {string|Date} date - التاريخ
 * @returns {string} - YYYY-MM-DD
 */
export const toInputDate = (date) => {
    if (!date) return '';
    return dayjs(date).format('YYYY-MM-DD');
};

/**
 * التحقق من صلاحية التاريخ
 * @param {string|Date} date - التاريخ
 * @returns {boolean}
 */
export const isValidDate = (date) => {
    return date && dayjs(date).isValid();
};

export default dayjs;
