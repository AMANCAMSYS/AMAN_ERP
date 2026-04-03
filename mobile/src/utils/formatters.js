/**
 * Shared mobile formatters for amount/date display.
 */
import AsyncStorage from '@react-native-async-storage/async-storage';

const DEFAULT_CURRENCY = 'SAR';
const CURRENCY_SYMBOL_MAP = {
  SAR: 'ر.س',
  USD: '$',
  EUR: '€',
  GBP: '£',
  AED: 'د.إ',
  KWD: 'د.ك',
  QAR: 'ر.ق',
  BHD: 'د.ب',
  OMR: 'ر.ع',
};

export function getCurrencySymbol(currencyCode) {
  const code = String(currencyCode || DEFAULT_CURRENCY).toUpperCase();
  return CURRENCY_SYMBOL_MAP[code] || code;
}

export function formatAmount(value, currencyCode) {
  if (value == null || value === '') return '—';

  const num = Number(value);
  const code = String(currencyCode || DEFAULT_CURRENCY).toUpperCase();
  const symbol = getCurrencySymbol(code);

  if (Number.isNaN(num)) {
    return `${value} ${symbol}`;
  }

  const formatted = num.toLocaleString('ar-SA', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });

  return `${formatted} ${symbol}`;
}

export function formatDate(value) {
  if (!value) return '';
  try {
    return new Date(value).toLocaleDateString('ar-SA');
  } catch {
    return String(value);
  }
}

export async function setMobileCurrencyCode(code) {
  if (!code) return;
  await AsyncStorage.setItem('mobile_currency_code', String(code).toUpperCase());
}

export async function getMobileCurrencyCode() {
  return (await AsyncStorage.getItem('mobile_currency_code')) || DEFAULT_CURRENCY;
}
