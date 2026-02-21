import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

import ar from './locales/ar.json';
import en from './locales/en.json';

i18n
    .use(LanguageDetector)
    .use(initReactI18next)
    .init({
        resources: {
            ar: {
                translation: ar
            },
            en: {
                translation: en
            }
        },
        detection: {
            order: ['localStorage'], // Only rely on localStorage for persistence
            caches: ['localStorage'],
            lookupLocalStorage: 'i18nextLng'
        },
        lng: localStorage.getItem('i18nextLng') || 'ar', // Force Arabic if no stored preference
    });

export default i18n;
