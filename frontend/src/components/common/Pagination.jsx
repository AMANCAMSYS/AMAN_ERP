import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { ChevronRight, ChevronLeft, ChevronsRight, ChevronsLeft } from 'lucide-react';

const PAGE_SIZES = [10, 25, 50, 100];

export default function Pagination({ currentPage, totalItems, pageSize, onPageChange, onPageSizeChange }) {
    const { t, i18n } = useTranslation();
    const isRTL = i18n.language === 'ar';
    const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));

    if (totalItems <= 10) return null;

    const startItem = (currentPage - 1) * pageSize + 1;
    const endItem = Math.min(currentPage * pageSize, totalItems);

    const getPageNumbers = () => {
        const pages = [];
        const maxVisible = 5;
        let start = Math.max(1, currentPage - Math.floor(maxVisible / 2));
        let end = Math.min(totalPages, start + maxVisible - 1);
        if (end - start < maxVisible - 1) {
            start = Math.max(1, end - maxVisible + 1);
        }
        for (let i = start; i <= end; i++) pages.push(i);
        return pages;
    };

    const PrevIcon = isRTL ? ChevronRight : ChevronLeft;
    const NextIcon = isRTL ? ChevronLeft : ChevronRight;
    const FirstIcon = isRTL ? ChevronsRight : ChevronsLeft;
    const LastIcon = isRTL ? ChevronsLeft : ChevronsRight;

    return (
        <div className="pagination-container" style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            padding: '12px 16px', borderTop: '1px solid var(--border-color, #e5e7eb)',
            flexWrap: 'wrap', gap: '8px', fontSize: '14px'
        }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-secondary, #6b7280)' }}>
                <span>{t('pagination.showing', 'عرض')} {startItem}-{endItem} {t('pagination.of', 'من')} {totalItems}</span>
                {onPageSizeChange && (
                    <select
                        value={pageSize}
                        onChange={(e) => onPageSizeChange(Number(e.target.value))}
                        style={{
                            padding: '4px 8px', borderRadius: '6px',
                            border: '1px solid var(--border-color, #d1d5db)',
                            background: 'var(--bg-card, #ffffff)', fontSize: '13px',
                            cursor: 'pointer'
                        }}
                    >
                        {PAGE_SIZES.map(size => (
                            <option key={size} value={size}>{size} / {t('pagination.page', 'صفحة')}</option>
                        ))}
                    </select>
                )}
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <button
                    onClick={() => onPageChange(1)}
                    disabled={currentPage === 1}
                    className="pagination-btn"
                    title={t('pagination.first', 'الأولى')}
                    style={btnStyle(currentPage === 1)}
                >
                    <FirstIcon size={16} />
                </button>
                <button
                    onClick={() => onPageChange(currentPage - 1)}
                    disabled={currentPage === 1}
                    className="pagination-btn"
                    title={t('pagination.previous', 'السابقة')}
                    style={btnStyle(currentPage === 1)}
                >
                    <PrevIcon size={16} />
                </button>

                {getPageNumbers().map(page => (
                    <button
                        key={page}
                        onClick={() => onPageChange(page)}
                        className={`pagination-btn ${page === currentPage ? 'active' : ''}`}
                        style={{
                            ...btnStyle(false),
                            minWidth: '32px',
                            ...(page === currentPage ? {
                                background: 'var(--primary-color, #3b82f6)',
                                color: 'var(--text-on-primary, #ffffff)',
                                borderColor: 'var(--primary-color, #3b82f6)'
                            } : {})
                        }}
                    >
                        {page}
                    </button>
                ))}

                <button
                    onClick={() => onPageChange(currentPage + 1)}
                    disabled={currentPage === totalPages}
                    className="pagination-btn"
                    title={t('pagination.next', 'التالية')}
                    style={btnStyle(currentPage === totalPages)}
                >
                    <NextIcon size={16} />
                </button>
                <button
                    onClick={() => onPageChange(totalPages)}
                    disabled={currentPage === totalPages}
                    className="pagination-btn"
                    title={t('pagination.last', 'الأخيرة')}
                    style={btnStyle(currentPage === totalPages)}
                >
                    <LastIcon size={16} />
                </button>
            </div>
        </div>
    );
}

function btnStyle(disabled) {
    return {
        padding: '6px 10px', borderRadius: '6px',
        borderWidth: '1px',
        borderStyle: 'solid',
        borderColor: 'var(--border-color, #d1d5db)',
        background: disabled ? 'var(--bg-hover, #f3f4f6)' : 'var(--bg-card, #ffffff)',
        cursor: disabled ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.5 : 1,
        display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
        color: 'var(--text-main, #374151)', fontSize: '13px',
        transition: 'all 0.15s ease'
    };
}

/** Hook for client-side pagination */
export function usePagination(items, initialPageSize = 25) {
    const [currentPage, setCurrentPage] = useState(1);
    const [pageSize, setPageSize] = useState(initialPageSize);

    const totalItems = items.length;
    const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));

    // Reset to page 1 when items change
    useEffect(() => {
        if (currentPage > totalPages) {
            setCurrentPage(1);
        }
    }, [totalItems, pageSize]);

    const paginatedItems = items.slice(
        (currentPage - 1) * pageSize,
        currentPage * pageSize
    );

    const handlePageChange = (page) => {
        setCurrentPage(Math.max(1, Math.min(page, totalPages)));
    };

    const handlePageSizeChange = (size) => {
        setPageSize(size);
        setCurrentPage(1);
    };

    return {
        currentPage,
        pageSize,
        totalItems,
        paginatedItems,
        onPageChange: handlePageChange,
        onPageSizeChange: handlePageSizeChange
    };
}
