"use client"

import { createContext, useContext, useEffect, useState } from "react"

type User = {
  id: number
  email: string
  full_name: string
  organization_name?: string
  role: string
  org_id?: number
}

type AuthContextType = {
  user: User | null
  token: string | null
  loading: boolean
  isAuthenticated: boolean
  logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const storedToken = localStorage.getItem("token")
    if (storedToken) {
      setToken(storedToken)
      try {
        const payload = JSON.parse(atob(storedToken.split(".")[1]))
        setUser({
          id: payload.sub,
          email: payload.email || "",
          full_name: payload.full_name || "",
          organization_name: payload.org_name || "",
          role: payload.role || "user",
          org_id: payload.org,
        })
      } catch (err) {
        localStorage.removeItem("token")
        setToken(null)
      }
    }
    setLoading(false)
  }, [])

  const logout = () => {
    localStorage.removeItem("token")
    localStorage.removeItem("must_change_password")
    setToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        isAuthenticated: !!token,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider")
  }
  return context
}
