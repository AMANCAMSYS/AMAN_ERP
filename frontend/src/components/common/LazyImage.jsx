
import React, { useState, useEffect, useRef } from 'react'

const LazyImage = ({ src, alt, className, style, placeholder, ...props }) => {
    const [isLoaded, setIsLoaded] = useState(false)
    const [isInView, setIsInView] = useState(false)
    const imgRef = useRef()

    useEffect(() => {
        const observer = new IntersectionObserver((entries) => {
            if (entries[0].isIntersecting) {
                setIsInView(true)
                observer.disconnect()
            }
        }, {
            rootMargin: '100px', // Start loading 100px before appearing
        })

        if (imgRef.current) {
            observer.observe(imgRef.current)
        }

        return () => {
            if (observer) observer.disconnect()
        }
    }, [])

    return (
        <div ref={imgRef} className={`lazy-image-container ${className || ''}`} style={{ position: 'relative', overflow: 'hidden', ...style }}>
            {isInView ? (
                <img
                    src={src}
                    alt={alt}
                    {...props}
                    style={{
                        width: '100%',
                        height: '100%',
                        opacity: isLoaded ? 1 : 0,
                        transition: 'opacity 0.3s ease-in-out',
                        objectFit: 'cover',
                        ...(props.style || {})
                    }}
                    onLoad={() => setIsLoaded(true)}
                />
            ) : null}
            {!isLoaded && (
                <div
                    style={{
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        right: 0,
                        bottom: 0,
                        backgroundColor: '#f5f5f5',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        zIndex: 1
                    }}
                >
                    {placeholder || <div className="spinner-small" style={{ width: '24px', height: '24px', border: '2px solid #ddd', borderTopColor: '#3498db', borderRadius: '50%', animation: 'spin 1s linear infinite' }}></div>}
                </div>
            )}
            <style jsx>{`
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
            `}</style>
        </div>
    )
}

export default LazyImage
