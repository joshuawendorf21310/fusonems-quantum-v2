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
  const [error, setError] = useState(location.state?.error ?? '')

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (!email || !password) {
      return
    }
    setError('')
    setIsSubmitting(true)
    try {
      const destination = await loginLocal({ email, password })
      const redirect = location.state?.from || destination
      navigate(redirect, { replace: true })
    } catch (err) {
      setError('Action needed: login failed. Verify credentials or unlock your agency key.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="auth-shell">
      <section className="auth-hero">
        <div className="hero-logo">
          <img src="/brand/fusionems-quantum.png" alt="FusionEMS Quantum" />
        </div>
        <div>
          <p className="eyebrow">Secure Access</p>
          <h1>FusionEMS Quantum Command Gate</h1>
          <p className="hero-text">
            Authoritative entry into FusionEMS Quantum. This surface is the only authorized route
            into the command center—no dashboards, no telemetry, just decisive access.
          </p>
        </div>
      </section>

      <div className="panel auth-panel">
        {error ? (
          <div className="alert alert-danger">
            <p>{error}</p>
            <button type="button" className="alert-dismiss" onClick={() => setError('')}>
              DISMISS
            </button>
          </div>
        ) : null}
        <h2>Sign in to FusionEMS Quantum</h2>
        <p className="list-sub">
          Secure access for dispatchers, clinicians, and leadership to the grounded command gate.
        </p>

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
              {isSubmitting ? 'Signing in...' : 'Sign In to Command'}
            </button>
          </form>
        ) : (
          <p className="list-sub">Local sign-in is disabled. Use organization login.</p>
        )}

        {oidcEnabled ? (
          <button className="ghost-button" type="button" onClick={loginOIDC}>
            Sign in with Organization
          </button>
        ) : null}

        {localAuthEnabled ? (
          <p className="auth-footer">
            New agency? <Link to="/register">Create an account</Link>
          </p>
        ) : null}
      </div>
    </div>
  )
}
