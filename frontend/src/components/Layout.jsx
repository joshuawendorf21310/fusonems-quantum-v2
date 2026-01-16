import { useLocation } from 'react-router-dom'
import Sidebar from './Sidebar.jsx'
import TopBar from './TopBar.jsx'
import ErrorBanner from './ErrorBanner.jsx'

export default function Layout({ children }) {
  const location = useLocation()
  const isLanding = location.pathname === '/' || location.pathname === '/landing'
  const isAuth = location.pathname === '/login' || location.pathname === '/register'

  if (isLanding) {
    return <div className="landing-shell">{children}</div>
  }

  if (isAuth) {
    return (
      <div className="auth-shell">
        <ErrorBanner />
        {children}
      </div>
    )
  }

  return (
    <div className="app-shell">
      <Sidebar />
      <div className="app-main">
        <TopBar />
        <ErrorBanner />
        <main className="app-content">{children}</main>
      </div>
    </div>
  )
}
