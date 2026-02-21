import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import api from '../../utils/api';
import { AlertTriangle, Package } from 'lucide-react';

const LowStockWidget = ({ config = {} }) => {
    const { t } = useTranslation();
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(true);
    const limit = config.limit || 10;

    useEffect(() => {
        api.get('/dashboard/widgets/low-stock', { params: { limit } })
            .then(res => setData(res.data?.items || []))
            .catch(() => {})
            .finally(() => setLoading(false));
    }, [limit]);

    if (loading) return (
        <div className="space-y-2">
            {[1,2,3].map(i => <div key={i} className="h-8 bg-slate-100 animate-pulse rounded" />)}
        </div>
    );

    if (!data.length) return (
        <div className="flex flex-col items-center justify-center h-full text-slate-400 py-8">
            <Package size={32} className="mb-2" />
            <span className="text-sm">{t('dashboard.no_low_stock') || 'لا يوجد منتجات منخفضة'}</span>
        </div>
    );

    return (
        <div className="space-y-1 overflow-auto max-h-[280px] custom-scrollbar">
            {data.map((item, i) => {
                const ratio = item.current_stock / Math.max(item.reorder_level, 1);
                const isZero = item.current_stock <= 0;
                const isCritical = ratio < 0.3;
                return (
                    <div key={i} className={`flex items-center justify-between p-2 rounded-lg text-sm ${isZero ? 'bg-red-50' : isCritical ? 'bg-amber-50' : 'bg-slate-50'}`}>
                        <div className="flex items-center gap-2 min-w-0">
                            <AlertTriangle size={14} className={isZero ? 'text-red-500' : isCritical ? 'text-amber-500' : 'text-slate-400'} />
                            <span className="truncate font-medium text-slate-700">{item.product_name}</span>
                        </div>
                        <div className="flex items-center gap-2 flex-shrink-0">
                            <span className={`font-bold ${isZero ? 'text-red-600' : isCritical ? 'text-amber-600' : 'text-slate-600'}`}>
                                {Math.floor(item.current_stock)}
                            </span>
                            <span className="text-xs text-slate-400">/ {Math.floor(item.reorder_level)}</span>
                        </div>
                    </div>
                );
            })}
        </div>
    );
};

export default LowStockWidget;
