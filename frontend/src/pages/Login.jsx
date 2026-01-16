import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/useAuth.js'

export default function Login() {
  const navigate = useNavigate()
  const location = useLocation()
  const { loginLocal, loginOIDC, oidcEnabled, localAuthEnabled } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (!email || !password) {
      return
    }
    setIsSubmitting(true)
    try {
      const destination = await loginLocal({ email, password })
      const redirect = location.state?.from || destination
      navigate(redirect, { replace: true })
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="auth-shell">
      <div className="panel auth-panel">
        <h2>Sign in to FusionEMS Quantum</h2>
        <p className="list-sub">Secure access to the command center and role-specific modules.</p>
        {oidcEnabled ? (
          <button className="primary-button" type="button" onClick={loginOIDC}>
            Sign in with Organization
          </button>
        ) : null}
        {localAuthEnabled ? (
          <form className="form-grid" onSubmit={handleSubmit}>
            <label className="field">
              <span>Email</span>
              <input
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                required
                placeholder="you@agency.com"
              />
            </label>
            <label className="field">
              <span>Password</span>
              <input
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                required
                placeholder="••••••••"
              />
            </label>
            <button className="primary-button" type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Signing in...' : 'Sign In'}
            </button>
          </form>
        ) : (
          <p className="list-sub">Local sign-in is disabled. Use organization login.</p>
        )}
        {localAuthEnabled ? (
          <p className="auth-footer">
            New agency? <Link to="/register">Create an account</Link>
          </p>
        ) : null}
      </div>
    </div>
  )
}
