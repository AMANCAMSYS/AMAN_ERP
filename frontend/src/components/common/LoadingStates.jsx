/**
 * Unified Loading & Skeleton Components
 * Drop-in replacements for inconsistent loading patterns across the app.
 */

/**
 * Full-page centered spinner — replaces:
 *   <div className="page-center"><span className="loading"></span></div>
 *   <div className="text-center p-5"><div className="spinner-border" /></div>
 */
export function PageLoading({ text }) {
    return (
        <div className="page-center">
            <div className="spinner"></div>
            {text && <p style={{ marginTop: 4, color: 'var(--text-secondary)' }}>{text}</p>}
        </div>
    )
}

/**
 * Inline/button spinner — replaces:
 *   <span className="loading loading-spinner loading-sm"></span>
 *   <span className="spinner-border spinner-border-sm"></span>
 */
export function Spinner({ size = 'sm' }) {
    const cls = size === 'lg' ? 'spinner spinner-lg'
        : size === 'md' ? 'spinner'
        : 'spinner spinner-sm'
    return <span className={cls}></span>
}

/**
 * Table skeleton — shows shimmering rows while table data loads
 * @param {number} rows - Number of skeleton rows (default: 5)
 * @param {number} cols - Number of columns (default: 4)
 */
export function TableSkeleton({ rows = 5, cols = 4 }) {
    return (
        <div className="skeleton-table">
            <div className="skeleton-table-header">
                {Array.from({ length: cols }, (_, i) => (
                    <div key={i} className="skeleton skeleton-table-cell" />
                ))}
            </div>
            {Array.from({ length: rows }, (_, r) => (
                <div key={r} className="skeleton-table-row">
                    {Array.from({ length: cols }, (_, c) => (
                        <div key={c} className="skeleton skeleton-table-cell" />
                    ))}
                </div>
            ))}
        </div>
    )
}

/**
 * Card skeleton — shows a shimmering card placeholder
 */
export function CardSkeleton({ lines = 3 }) {
    const widths = ['w-75', 'w-100', 'w-50', 'w-25']
    return (
        <div className="skeleton-card">
            {Array.from({ length: lines }, (_, i) => (
                <div key={i} className={`skeleton skeleton-text ${widths[i % widths.length]}`} />
            ))}
        </div>
    )
}

/**
 * Dashboard skeleton — shows placeholder cards for dashboard stats
 * @param {number} cards - Number of stat cards (default: 4)
 */
export function DashboardSkeleton({ cards = 4 }) {
    return (
        <div style={{ display: 'grid', gridTemplateColumns: `repeat(auto-fit, minmax(200px, 1fr))`, gap: '16px', padding: '20px 0' }}>
            {Array.from({ length: cards }, (_, i) => (
                <div key={i} className="skeleton-card">
                    <div className="skeleton skeleton-text w-50" style={{ height: '12px' }} />
                    <div className="skeleton skeleton-text w-75" style={{ height: '24px', marginTop: '12px' }} />
                    <div className="skeleton skeleton-text w-25" style={{ height: '12px', marginTop: '8px' }} />
                </div>
            ))}
        </div>
    )
}
