import React from 'react';

/**
 * Shared Card component — replaces all inline card styles.
 *
 * Variants (via className or props):
 *   default     → .card            (16px radius, 24px pad)
 *   compact     → .card-compact    (12px radius, 16px pad)
 *   flush       → .card-flush      (0 padding — for tables)
 *   section     → .section-card    (matches .card look)
 *   metric      → .metric-card     (smaller, 12px radius)
 */

const Card = ({
    title,
    children,
    className = '',
    flush = false,
    compact = false,
    style = {},
    ...rest
}) => {
    const classes = [
        'card',
        flush && 'card-flush',
        compact && 'card-compact',
        className,
    ].filter(Boolean).join(' ');

    return (
        <div className={classes} style={style} {...rest}>
            {title && (
                <div className="card-header" style={{ margin: '-24px -24px 16px', padding: '14px 24px' }}>
                    <span style={{
                        fontSize: '0.82rem',
                        fontWeight: 600,
                        color: 'var(--text-secondary)',
                        textTransform: 'uppercase',
                        letterSpacing: '0.04em',
                    }}>
                        {title}
                    </span>
                </div>
            )}
            {children}
        </div>
    );
};

export default Card;
