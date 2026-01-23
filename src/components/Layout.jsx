import { useLocation, matchPath } from "react-router-dom"
import PropTypes from "prop-types"
import Sidebar from "./Sidebar.jsx"
import TopBar from "./TopBar.jsx"
import ErrorBanner from "./ErrorBanner.jsx"

const LANDING_ROUTES = ["/", "/landing"]
const AUTH_ROUTES = ["/login", "/register"]

export default function Layout({ children }) {
  const { pathname } = useLocation()

  const isLanding = LANDING_ROUTES.some((route) =>
    matchPath({ path: route, end: true }, pathname)
  )

  const isAuth = AUTH_ROUTES.some((route) =>
    matchPath({ path: route, end: true }, pathname)
  )

  if (isLanding) {
    return (
      <div className="landing-shell">
        <a href="#main-content" className="skip-link">Skip to content</a>
        <main id="main-content">{children}</main>
      </div>
    )
  }

  if (isAuth) {
    return (
      <div className="auth-shell">
        <a href="#main-content" className="skip-link">Skip to content</a>
        <ErrorBanner />
        <main id="main-content" className="auth-content">
          {children}
        </main>
      </div>
    )
  }

  return (
    <div className="app-shell">
      <a href="#main-content" className="skip-link">Skip to content</a>
      <nav aria-label="Primary navigation">
        <Sidebar />
      </nav>
      <div className="app-main">
        <header role="banner">
          <TopBar />
        </header>
        <ErrorBanner />
        <main id="main-content" className="app-content" role="main">
          {children}
        </main>
      </div>
    </div>
  )
}

Layout.propTypes = {
  children: PropTypes.node.isRequired,
}
