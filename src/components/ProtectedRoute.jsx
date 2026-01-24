import { Navigate, useLocation, Link } from "react-router-dom"
import PropTypes from "prop-types"
import { useEffect, useRef } from "react"
import { useAuth } from "../context/useAuth.js"
import { pushError } from "../services/errorBus.js"

export default function ProtectedRoute({ children, allowedRoles = [] }) {
  const location = useLocation()
  const { isAuthenticated, userRole } = useAuth()
  const errorPushedRef = useRef(false)

  const roleRestricted =
    Array.isArray(allowedRoles) &&
    allowedRoles.length > 0 &&
    !allowedRoles.includes(userRole)

  // Push error ONCE (never during render)
  useEffect(() => {
    if (roleRestricted && !errorPushedRef.current) {
      pushError("Access blocked by role policy.", 403, {
        source: "ProtectedRoute",
      })
      errorPushedRef.current = true
    }
  }, [roleRestricted])

  // Redirect unauthenticated users
  if (!isAuthenticated) {
    return (
      <Navigate
        to="/login"
        replace
        state={{ from: location.pathname }}
      />
    )
  }

  if (roleRestricted) {
    return (
      <section
        className="panel access-denied"
        role="alert"
        aria-live="assertive"
      >
        <h3>ACCESS DENIED</h3>
        <p className="list-sub">
          Your role does not permit access to this area.
        </p>
        <Link className="primary-button" to="/operations">
          Return to Operations
        </Link>
      </section>
    )
  }

  return <>{children}</>
}

ProtectedRoute.propTypes = {
  children: PropTypes.node.isRequired,
  allowedRoles: PropTypes.arrayOf(PropTypes.string),
}
