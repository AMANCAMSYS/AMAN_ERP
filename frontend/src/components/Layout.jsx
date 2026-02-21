import { useEffect } from 'react'
import Sidebar from './Sidebar'
import Topbar from './Topbar'
import { authAPI } from '../utils/api'
import { getUser } from '../utils/auth'

function Layout({ children }) {
    useEffect(() => {
        const user = getUser();
        const syncUser = async () => {
            // System admin might have different auth flow or shouldn't sync per-tenant
            try {
                const response = await authAPI.me()
                localStorage.setItem('user', JSON.stringify(response.data))
            } catch (err) {
                console.error("Session sync failed", err)
                // If it's a 403/401, the interceptor will handle it, but we don't want to crash.
            }
        }
        if (user) syncUser();
    }, [])

    return (
        <div className="app-layout">
            <Sidebar />
            <div className="main-container">
                <Topbar />
                <main className="content-area">
                    {children}
                </main>
            </div>
        </div>
    )
}

export default Layout
