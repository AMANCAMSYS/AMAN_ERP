/**
 * Shared EmptyState component — replaces 20+ inconsistent empty-table/empty-page patterns.
 *
 * Props:
 *   icon        — emoji or React node (default "📋")
 *   title       — heading text (required)
 *   description — optional sub-text
 *   action      — { label, onClick } for CTA button (optional)
 */
export default function EmptyState({ icon = '📋', title, description, action }) {
    return (
        <div style={{ padding: '48px 20px', textAlign: 'center' }}>
            {icon && <div style={{ fontSize: '48px', marginBottom: '16px' }}>{icon}</div>}
            <h3 style={{ fontSize: '18px', marginBottom: '8px', fontWeight: 600 }}>{title}</h3>
            {description && (
                <p style={{ color: 'var(--text-secondary)', marginBottom: action ? '24px' : '0', maxWidth: '400px', margin: '0 auto' }}>
                    {description}
                </p>
            )}
            {action && (
                <button
                    className="btn btn-primary"
                    onClick={action.onClick}
                    style={{ marginTop: '24px' }}
                >
                    {action.label}
                </button>
            )}
        </div>
    );
}
