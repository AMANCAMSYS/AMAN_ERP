/**
 * AMAN ERP - Global Formatting Utilities
 */

import { getUser } from './auth';

/**
 * Formats a number according to the company's decimal precision setting.
 * @param {number|string} value - The number to format.
 * @param {number} [overridePrecision] - Optional override for precision.
 * @returns {string} Formatted number.
 */
export const formatNumber = (value, overridePrecision = null) => {
    const user = getUser();
    const precision = overridePrecision !== null ? overridePrecision : (user?.decimal_places !== undefined ? user.decimal_places : 2);

    const num = parseFloat(value);
    if (isNaN(num)) return '0';

    return num.toLocaleString(undefined, {
        minimumFractionDigits: precision,
        maximumFractionDigits: precision,
    });
};

/**
 * Formats a currency value with the currency symbol.
 * @param {number|string} value - The amount.
 * @param {string} [currency] - Optional currency code.
 * @returns {string} Formatted currency.
 */
export const formatCurrency = (value, currency = null) => {
    const user = getUser();
    const curr = currency || user?.currency || '';
    return `${formatNumber(value)} ${curr}`;
};

/**
 * Gets the numeric step value for inputs based on decimal precision.
 * @returns {string} Step value (e.g., "0.01", "0.0001").
 */
export const getStep = () => {
    const user = getUser();
    const precision = user?.decimal_places !== undefined ? user.decimal_places : 2;
    if (precision <= 0) return "1";
    return (1 / Math.pow(10, precision)).toFixed(precision);
};
