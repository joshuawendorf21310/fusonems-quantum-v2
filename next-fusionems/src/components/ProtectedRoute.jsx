import { Navigate, useLocation, Link } from 'react-router-dom'
import { useAuth } from '../context/useAuth.js'
import { pushError } from '../services/errorBus.js'

export default function ProtectedRoute({ children, allowedRoles }) {
  const location = useLocation()
  const { isAuthenticated, userRole } = useAuth()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  if (Array.isArray(allowedRoles) && allowedRoles.length > 0) {
    if (!allowedRoles.includes(userRole)) {
      pushError('Access blocked by role policy.', 403)
      return (
        <div className="panel">
          <h3>Access denied</h3>
          <p className="list-sub">
            Your role does not include this module. Request access from an administrator or return
            to the command center.
          </p>
          <Link className="primary-button" to="/dashboard">
            Return to Command Center
          </Link>
        </div>
      )
    }
  }

  return children
}
