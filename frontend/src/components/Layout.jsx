import { useEffect, useState, useCallback } from 'react'
import Sidebar from './Sidebar'
import Topbar from './Topbar'
import { authAPI } from '../utils/api'
import { getUser } from '../utils/auth'

function Layout({ children }) {
    const [sidebarOpen, setSidebarOpen] = useState(false)

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

    // Close sidebar on resize to desktop
    useEffect(() => {
        const handleResize = () => {
            if (window.innerWidth >= 1024) {
                setSidebarOpen(false)
            }
        }
        window.addEventListener('resize', handleResize)
        return () => window.removeEventListener('resize', handleResize)
    }, [])

    const toggleSidebar = useCallback(() => setSidebarOpen(prev => !prev), [])
    const closeSidebar = useCallback(() => setSidebarOpen(false), [])

    return (
        <div className="app-layout">
            {/* Overlay for mobile/tablet */}
            {sidebarOpen && (
                <div
                    className="sidebar-overlay"
                    onClick={closeSidebar}
                    aria-hidden="true"
                />
            )}
            <Sidebar isOpen={sidebarOpen} onClose={closeSidebar} />
            <div className={`main-container${sidebarOpen ? ' sidebar-is-open' : ''}`}>
                <Topbar onToggleSidebar={toggleSidebar} sidebarOpen={sidebarOpen} />
                <main className="content-area">
                    {children}
                </main>
            </div>
        </div>
    )
}

export default Layout
