import { useTranslation } from 'react-i18next';
import Pagination, { usePagination } from './Pagination';
import EmptyState from './EmptyState';
import { PageLoading } from './LoadingStates';

/**
 * Shared DataTable component — replaces duplicated table markup across all list pages.
 *
 * Props:
 *   columns     — [{ key, label, width?, render?, style?, headerStyle? }]
 *   data        — array of row objects
 *   loading     — show loading spinner
 *   emptyIcon   — emoji/icon for empty state (default "📋")
 *   emptyTitle  — heading when no data
 *   emptyDesc   — description when no data
 *   emptyAction — { label, onClick } for CTA button in empty state
 *   onRowClick  — (row) => void
 *   rowKey      — field name for React key (default "id")
 *   paginate    — enable built-in pagination (default true)
 *   pageSize    — initial page size (default 25)
 *   searchValue — controlled search value (optional)
 *   onSearch    — (value) => void (optional)
 *   searchPlaceholder — placeholder for search input
 */
export default function DataTable({
    columns = [],
    data = [],
    loading = false,
    emptyIcon = '📋',
    emptyTitle,
    emptyDesc,
    emptyAction,
    onRowClick,
    rowKey = 'id',
    paginate = true,
    pageSize: initialPageSize = 25,
    searchValue,
    onSearch,
    searchPlaceholder,
}) {
    const { t } = useTranslation();
    const pagination = usePagination(data, initialPageSize);
    const displayData = paginate ? pagination.paginatedItems : data;

    if (loading) return <PageLoading />;

    return (
        <div className="card card-flush" style={{ overflow: 'hidden' }}>
            {onSearch !== undefined && (
                <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--border-color)' }}>
                    <input
                        type="text"
                        className="form-input"
                        placeholder={searchPlaceholder || t('common.search', 'بحث...')}
                        value={searchValue || ''}
                        onChange={(e) => onSearch(e.target.value)}
                        style={{ maxWidth: '320px' }}
                    />
                </div>
            )}
            <table className="data-table">
                <thead>
                    <tr>
                        {columns.map((col) => (
                            <th key={col.key} style={{ width: col.width, ...col.headerStyle }}>
                                {col.label}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {data.length === 0 ? (
                        <tr>
                            <td colSpan={columns.length}>
                                <EmptyState
                                    icon={emptyIcon}
                                    title={emptyTitle || t('common.no_data', 'لا توجد بيانات')}
                                    description={emptyDesc}
                                    action={emptyAction}
                                />
                            </td>
                        </tr>
                    ) : (
                        displayData.map((row) => (
                            <tr
                                key={row[rowKey]}
                                onClick={onRowClick ? () => onRowClick(row) : undefined}
                                style={onRowClick ? { cursor: 'pointer' } : undefined}
                            >
                                {columns.map((col) => (
                                    <td key={col.key} style={col.style}>
                                        {col.render ? col.render(row[col.key], row) : row[col.key]}
                                    </td>
                                ))}
                            </tr>
                        ))
                    )}
                </tbody>
            </table>
            {paginate && data.length > 0 && (
                <Pagination
                    currentPage={pagination.currentPage}
                    totalItems={pagination.totalItems}
                    pageSize={pagination.pageSize}
                    onPageChange={pagination.onPageChange}
                    onPageSizeChange={pagination.onPageSizeChange}
                />
            )}
        </div>
    );
}
