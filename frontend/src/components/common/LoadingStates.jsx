/**
 * ============================================================
 * Unified Loading & Skeleton Components — SINGLE SOURCE OF TRUTH
 * ============================================================
 * ALL loading/spinner visuals in the app flow through this file.
 * To change the look of the spinner: edit spinnerStyle / pageLoadingStyle here.
 * Changing these objects automatically updates EVERY page.
 *
 * Exports:
 *   PageLoading  — full-page centered spinner  (for page-level loading guards)
 *   Spinner      — inline/button-size spinner   (for submit buttons, inline states)
 *   TableSkeleton, CardSkeleton, DashboardSkeleton — shimmer placeholders
 * ============================================================
 */import { useTranslation } from 'react-i18next'
// ── Design tokens ─────────────────────────────────────────
// Edit HERE to change the spinner across the entire app.
const SIZE = {
    sm: { w: 20, h: 20, shadow: 'none' },
    md: { w: 40, h: 40, shadow: '0 0 8px rgba(37, 99, 235, 0.3)' },
    lg: { w: 58, h: 58, shadow: '0 0 14px rgba(37, 99, 235, 0.45)' },
}

function SpinEl({ w, h, shadow }) {
    return (
        <span
            className="aman-spinner"
            style={{
                display: 'inline-block',
                width: w,
                height: h,
                borderRadius: '50%',
                background: 'conic-gradient(from 0deg, transparent 0deg, var(--primary, #2563eb) 270deg, transparent 360deg)',
                WebkitMask: 'radial-gradient(circle, transparent 58%, #000 60%)',
                mask: 'radial-gradient(circle, transparent 58%, #000 60%)',
                animation: 'aman-spin 0.9s cubic-bezier(0.5, 0.1, 0.5, 0.9) infinite',
                filter: shadow !== 'none' ? `drop-shadow(${shadow})` : undefined,
                flexShrink: 0,
            }}
        />
    )
}

/**
 * Full-page centered spinner.
 * Replaces all of:
 *   <div className="page-center"><span className="loading"></span></div>
 *   <div className="text-center p-5"><div className="spinner-border" /></div>
 *   <div className="loading-spinner">جاري التحميل…</div>
 *   etc.
 *
 * @param {string}  [text]    — optional label shown below the spinner (defaults to translated "loading")
 * @param {number}  [minH]    — min-height of the wrapper (default 300px)
 * @param {boolean} [noText]  — set true to hide the text entirely
 */
export function PageLoading({ text, minH = 300, noText = false }) {
    const { t } = useTranslation()
    const label = noText ? '' : (text ?? t('common.loading', 'Loading...'))
    return (
        <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: minH,
            padding: '40px 20px',
            gap: 14,
            color: 'var(--text-secondary, #64748b)',
            fontSize: '0.95rem',
        }}>
            <SpinEl {...SIZE.md} />
            {label && <p style={{ margin: 0 }}>{label}</p>}
        </div>
    )
}

/**
 * Inline / button spinner.
 * Replaces all of:
 *   <span className="loading loading-spinner loading-sm"></span>
 *   <span className="spinner-border spinner-border-sm"></span>
 *   <Loader2 className="spin" size={16} />
 *
 * @param {'sm'|'md'|'lg'} [size='sm']
 */
export function Spinner({ size = 'sm' }) {
    return <SpinEl {...SIZE[size] ?? SIZE.sm} />
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
