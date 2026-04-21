import React from 'react';
import BackButton from './BackButton';

/**
 * PageLayout — unified page shell for every module screen.
 *
 * Usage:
 *   <PageLayout title={t('sales.invoices')} subtitle="..." actions={<button/>}>
 *     ...content...
 *   </PageLayout>
 *
 * - Applies the standard `.module-container` shell (padding, max-width, animation)
 * - Renders a consistent `.module-header` with optional BackButton, title,
 *   subtitle, and right-aligned action slot.
 * - Forwards `dir` so RTL pages get correct ordering.
 */
function PageLayout({
    title,
    subtitle,
    actions,
    showBack = true,
    dir,
    className = '',
    children,
}) {
    return (
        <div className={`module-container ${className}`.trim()} dir={dir}>
            {(title || subtitle || actions || showBack) && (
                <div className="module-header">
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12, flex: 1, minWidth: 0 }}>
                        {showBack && <BackButton />}
                        <div style={{ minWidth: 0 }}>
                            {title && <h1 className="module-title">{title}</h1>}
                            {subtitle && <div className="module-subtitle">{subtitle}</div>}
                        </div>
                    </div>
                    {actions && <div className="module-header-actions">{actions}</div>}
                </div>
            )}
            {children}
        </div>
    );
}

export default PageLayout;
