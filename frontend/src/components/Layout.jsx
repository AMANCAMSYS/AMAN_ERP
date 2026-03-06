import { useEffect, useState, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import Sidebar from './Sidebar'
import Topbar from './Topbar'
import { authAPI } from '../utils/api'
import { getUser } from '../utils/auth'

function Layout({ children }) {
    const { i18n } = useTranslation()
    const [sidebarOpen, setSidebarOpen] = useState(() => window.innerWidth > 1024)
    const [isMobile, setIsMobile] = useState(() => window.innerWidth <= 1024)

    useEffect(() => {
        const user = getUser();
        const syncUser = async () => {
            try {
                const response = await authAPI.me()
                localStorage.setItem('user', JSON.stringify(response.data))
            } catch (err) {
                console.error("Session sync failed", err)
            }
        }
        if (user) syncUser();
    }, [])

    // Track screen size
    useEffect(() => {
        const handleResize = () => {
            const mobile = window.innerWidth <= 1024
            setIsMobile(mobile)
            if (mobile) setSidebarOpen(false)
            else setSidebarOpen(true)
        }
        window.addEventListener('resize', handleResize)
        return () => window.removeEventListener('resize', handleResize)
    }, [])

    const toggleSidebar = useCallback(() => setSidebarOpen(prev => !prev), [])
    const closeSidebar = useCallback(() => setSidebarOpen(false), [])

    return (
        <div className="app-layout">
            {/* Dark overlay — only on mobile when sidebar is open */}
            {isMobile && sidebarOpen && (
                <div
                    className="sidebar-overlay"
                    onClick={closeSidebar}
                    aria-hidden="true"
                    style={{ display: 'block' }}
                />
            )}
            <Sidebar isOpen={sidebarOpen} isMobile={isMobile} onClose={closeSidebar} onToggle={toggleSidebar} />
            <div className={`main-container ${sidebarOpen ? 'sidebar-open' : 'sidebar-closed'}`}>
                <Topbar onToggleSidebar={toggleSidebar} sidebarOpen={sidebarOpen} />
                <main className="content-area" dir={i18n.language === 'ar' ? 'rtl' : 'ltr'}>
                    {children}
                </main>
            </div>
        </div>
    )
}

export default Layout
