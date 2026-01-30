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

  const loadUserFromToken = (tokenToLoad: string | null) => {
    if (!tokenToLoad) {
      setUser(null)
      setToken(null)
      return
    }
    
    try {
      const payload = JSON.parse(atob(tokenToLoad.split(".")[1]))
      setUser({
        id: payload.sub,
        email: payload.email || "",
        full_name: payload.full_name || "",
        organization_name: payload.org_name || "",
        role: payload.role || "user",
        org_id: payload.org,
      })
      setToken(tokenToLoad)
    } catch (err) {
      localStorage.removeItem("token")
      setUser(null)
      setToken(null)
    }
  }

  useEffect(() => {
    const storedToken = localStorage.getItem("token")
    loadUserFromToken(storedToken)
    setLoading(false)

    // Listen for storage changes (e.g., login from another tab)
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === "token") {
        loadUserFromToken(e.newValue)
      }
    }
    window.addEventListener("storage", handleStorageChange)

    // Poll for token changes (in case login happens in same tab)
    let lastToken = storedToken
    const interval = setInterval(() => {
      const currentToken = localStorage.getItem("token")
      if (currentToken !== lastToken) {
        lastToken = currentToken
        loadUserFromToken(currentToken)
      }
    }, 1000)

    return () => {
      window.removeEventListener("storage", handleStorageChange)
      clearInterval(interval)
    }
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
