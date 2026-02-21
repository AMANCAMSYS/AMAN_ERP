import React from 'react';
import { useTranslation } from 'react-i18next';
import { Construction } from 'lucide-react';

const ComingSoon = ({ title }) => {
    const { t } = useTranslation();

    return (
        <div className="flex flex-col items-center justify-center py-20 text-center animate-fade-in">
            <div className="bg-primary/10 p-6 rounded-full mb-6">
                <Construction size={64} className="text-primary animate-pulse" />
            </div>
            <h2 className="text-2xl font-bold mb-2">
                {title}
            </h2>
            <p className="text-base-content/60 max-w-md">
                {t('settings.coming_soon_desc')}
            </p>

            <div className="mt-8 flex gap-2">
                <div className="w-2 h-2 rounded-full bg-primary animate-bounce"></div>
                <div className="w-2 h-2 rounded-full bg-primary animate-bounce [animation-delay:-.3s]"></div>
                <div className="w-2 h-2 rounded-full bg-primary animate-bounce [animation-delay:-.5s]"></div>
            </div>
        </div>
    );
};

export default ComingSoon;
