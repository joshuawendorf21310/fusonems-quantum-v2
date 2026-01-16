import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/useAuth.js'

const roles = [
  'dispatcher',
  'provider',
  'admin',
  'medical_director',
  'billing',
  'hems_supervisor',
  'flight_nurse',
  'flight_medic',
  'pilot',
  'founder',
  'investor',
]

export default function Register() {
  const navigate = useNavigate()
  const { registerLocal, localAuthEnabled } = useAuth()
  const [form, setForm] = useState({
    full_name: '',
    organization_name: '',
    email: '',
    password: '',
    role: 'dispatcher',
  })
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleChange = (event) => {
    const { name, value } = event.target
    setForm((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setIsSubmitting(true)
    try {
      const destination = await registerLocal(form)
      navigate(destination, { replace: true })
    } finally {
      setIsSubmitting(false)
    }
  }

  if (!localAuthEnabled) {
    return (
      <div className="auth-shell">
        <div className="panel auth-panel">
          <h2>Registration Disabled</h2>
          <p className="list-sub">
            Local registration is disabled. Please sign in through your organization.
          </p>
          <Link className="primary-button" to="/login">
            Back to Sign In
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="auth-shell">
      <div className="panel auth-panel">
        <h2>Activate Your Agency</h2>
        <p className="list-sub">Provision a secure tenant and jump into operational mode.</p>
        <form className="form-grid" onSubmit={handleSubmit}>
          <label className="field">
            <span>Full name</span>
            <input
              name="full_name"
              value={form.full_name}
              onChange={handleChange}
              required
              placeholder="Commander Name"
            />
          </label>
          <label className="field">
            <span>Organization</span>
            <input
              name="organization_name"
              value={form.organization_name}
              onChange={handleChange}
              required
              placeholder="Agency Name"
            />
          </label>
          <label className="field">
            <span>Email</span>
            <input
              type="email"
              name="email"
              value={form.email}
              onChange={handleChange}
              required
              placeholder="you@agency.com"
            />
          </label>
          <label className="field">
            <span>Password</span>
            <input
              type="password"
              name="password"
              value={form.password}
              onChange={handleChange}
              required
              placeholder="Create a secure password"
            />
          </label>
          <label className="field">
            <span>Role</span>
            <select name="role" value={form.role} onChange={handleChange}>
              {roles.map((role) => (
                <option key={role} value={role}>
                  {role.replace('_', ' ')}
                </option>
              ))}
            </select>
          </label>
          <button className="primary-button" type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Provisioning...' : 'Create Account'}
          </button>
        </form>
        <p className="auth-footer">
          Already have access? <Link to="/login">Sign in</Link>
        </p>
      </div>
    </div>
  )
}
