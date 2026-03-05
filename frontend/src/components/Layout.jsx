import { useEffect, useState, useCallback } from 'react'
import Sidebar from './Sidebar'
import Topbar from './Topbar'
import { authAPI } from '../utils/api'
import { getUser } from '../utils/auth'

function Layout({ children }) {
    const [sidebarOpen, setSidebarOpen] = useState(false)
    const [isMobile, setIsMobile] = useState(() => window.innerWidth < 1024)

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
            const mobile = window.innerWidth < 1024
            setIsMobile(mobile)
            if (!mobile) setSidebarOpen(false)
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
            <Sidebar isOpen={sidebarOpen} isMobile={isMobile} onClose={closeSidebar} />
            <div className="main-container" style={{ marginRight: isMobile ? 0 : 'var(--sidebar-width)' }}>
                <Topbar onToggleSidebar={toggleSidebar} sidebarOpen={sidebarOpen} />
                <main className="content-area">
                    {children}
                </main>
            </div>
        </div>
    )
}

export default Layout
