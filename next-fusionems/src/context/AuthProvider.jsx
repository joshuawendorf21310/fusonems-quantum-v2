import { useEffect, useMemo, useState } from 'react'
import axios from 'axios'
import { pushError } from '../services/errorBus.js'
import { defaultRoleHome } from '../utils/access.js'
import AuthContext from './authContext.js'

const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const oidcEnabled = (import.meta.env.VITE_OIDC_ENABLED || 'false').toLowerCase() === 'true'
const localAuthEnabled = (import.meta.env.VITE_LOCAL_AUTH_ENABLED || 'true').toLowerCase() === 'true'

export function AuthProvider({ children }) {
  const [session, setSession] = useState(() => window.__AUTH_BOOTSTRAP__ || null)
  const [platformConfig, setPlatformConfig] = useState({ smart_mode: false })
  const userRole = session?.role || ''
  const orgId = session?.org_id || null
  const mfaVerified = Boolean(session?.mfa_verified)
  const deviceTrusted = Boolean(session?.device_trusted)
  const onShift = Boolean(session?.on_shift)

  const refreshMe = async () => {
    try {
      const response = await axios.get(`${baseUrl}/api/auth/me`, { withCredentials: true })
      if (response.data?.user) {
        setSession(response.data.user)
      }
      if (response.data?.config) {
        setPlatformConfig(response.data.config)
      }
    } catch (error) {
      setSession(null)
      setPlatformConfig({ smart_mode: false })
    }
  }

  const loginLocal = async ({ email, password }) => {
    try {
      const response = await axios.post(
        `${baseUrl}/api/auth/login`,
        { email, password },
        { withCredentials: true }
      )
      if (response.data?.user) {
        setSession(response.data.user)
      } else {
        await refreshMe()
      }
      if (response.data?.config) {
        setPlatformConfig(response.data.config)
      }
      return defaultRoleHome(response.data?.user?.role)
    } catch (error) {
      pushError('Login failed. Verify credentials and try again.', error?.response?.status)
      throw error
    }
  }

  const registerLocal = async ({ email, password, full_name, organization_name, role }) => {
    try {
      const response = await axios.post(`${baseUrl}/api/auth/register`, {
        email,
        password,
        full_name,
        organization_name,
        role,
      }, { withCredentials: true })
      if (response.data?.user) {
        setSession(response.data.user)
      } else {
        await refreshMe()
      }
      if (response.data?.config) {
        setPlatformConfig(response.data.config)
      }
      return defaultRoleHome(response.data?.user?.role)
    } catch (error) {
      pushError('Registration failed. Check the form and try again.', error?.response?.status)
      throw error
    }
  }

  const loginOIDC = () => {
    window.location.assign(`${baseUrl}/api/auth/oidc/login`)
  }

  const logout = async () => {
    try {
      await axios.post(`${baseUrl}/api/auth/logout`, {}, { withCredentials: true })
    } finally {
      setSession(null)
      setPlatformConfig({ smart_mode: false })
    }
  }

  const value = useMemo(
    () => ({
      isAuthenticated: Boolean(session),
      user: session,
      userRole,
      orgId,
      mfaVerified,
      deviceTrusted,
      onShift,
      smartMode: Boolean(platformConfig?.smart_mode),
      loginLocal,
      loginOIDC,
      registerLocal,
      logout,
      refreshMe,
      oidcEnabled,
      localAuthEnabled,
      platformConfig,
    }),
    [
      session,
      userRole,
      orgId,
      mfaVerified,
      deviceTrusted,
      onShift,
      oidcEnabled,
      localAuthEnabled,
      platformConfig,
    ]
  )

  useEffect(() => {
    if (window.__AUTH_BOOTSTRAP__) {
      return
    }
    refreshMe()
  }, [])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
