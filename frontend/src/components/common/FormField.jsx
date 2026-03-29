/**
 * Shared FormField component — wraps label + input + error in a consistent layout.
 *
 * Props:
 *   label       — field label text
 *   required    — show asterisk (default false)
 *   error       — error message string (optional)
 *   children    — the input/select/textarea element
 *   hint        — optional help text below the input
 *   className   — additional wrapper class
 *   style       — additional wrapper style
 */
export default function FormField({ label, required, error, children, hint, className = '', style }) {
    return (
        <div className={`form-group ${className}`} style={style}>
            {label && (
                <label className="form-label">
                    {label} {required && <span style={{ color: 'var(--error, #ef4444)' }}>*</span>}
                </label>
            )}
            {children}
            {hint && !error && (
                <small style={{ display: 'block', marginTop: '4px', color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                    {hint}
                </small>
            )}
            {error && (
                <small style={{ display: 'block', marginTop: '4px', color: 'var(--error, #ef4444)', fontSize: '0.8rem' }}>
                    {error}
                </small>
            )}
        </div>
    );
}
