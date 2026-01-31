/**
 * Page Shell Component - Standard wrapper for all authenticated pages
 * Provides consistent layout, loading states, and authentication
 */

"use client"

import { motion } from "framer-motion"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { useAuth } from "@/lib/auth-context"
import { useEffect, ReactNode } from "react"
import { Bell, LogOut } from "lucide-react"

interface PageShellProps {
  children: ReactNode
  title: string
  subtitle?: string
  requireAuth?: boolean
  allowedRoles?: string[]
  hideHeader?: boolean
}

export function PageShell({
  children,
  title,
  subtitle,
  requireAuth = true,
  allowedRoles,
  hideHeader = false
}: PageShellProps) {
  const router = useRouter()
  const { user, isAuthenticated, loading, logout } = useAuth()

  // Authentication check
  useEffect(() => {
    if (!loading && requireAuth && !isAuthenticated) {
      router.push("/login")
    }
  }, [isAuthenticated, loading, requireAuth, router])

  // Role check
  const hasRequiredRole = !allowedRoles || (user && allowedRoles.includes(user.role))

  // Loading state
  if (loading && requireAuth) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.3 }}
          className="flex flex-col items-center gap-4"
        >
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
            className="w-16 h-16 border-4 border-orange-500/30 border-t-orange-500 rounded-full"
          />
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="text-zinc-400 font-medium"
          >
            Authenticating...
          </motion.p>
        </motion.div>
      </div>
    )
  }

  // Not authenticated
  if (requireAuth && !isAuthenticated) {
    return null
  }

  // No required role
  if (requireAuth && !hasRequiredRole) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center p-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="max-w-md w-full bg-zinc-900 border border-red-500/20 rounded-2xl p-8"
        >
          <div className="flex items-center justify-center w-16 h-16 bg-red-500/10 rounded-full mx-auto mb-6">
            <svg className="w-8 h-8 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          
          <h1 className="text-3xl font-bold text-red-400 text-center mb-4">
            Access Denied
          </h1>
          
          <p className="text-zinc-400 text-center mb-8">
            You don't have permission to access this page.
          </p>

          <div className="space-y-3">
            <button
              onClick={() => router.back()}
              className="w-full py-3 px-4 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 rounded-xl transition-all font-medium border border-zinc-700"
            >
              Go Back
            </button>
            <button
              onClick={() => router.push("/dashboard")}
              className="w-full py-3 px-4 bg-gradient-to-r from-orange-600 to-red-600 text-white font-semibold rounded-xl hover:shadow-lg hover:shadow-orange-500/20 transition-all"
            >
              Go to Dashboard
            </button>
          </div>
        </motion.div>
      </div>
    )
  }

  // Render page
  return (
    <div className="min-h-screen bg-zinc-950">
      {!hideHeader && (
        <div className="bg-gradient-to-r from-zinc-900 via-zinc-800 to-zinc-900 border-b border-zinc-800">
          <div className="max-w-7xl mx-auto px-6 py-6">
            <div className="flex justify-between items-center">
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.5 }}
              >
                <h1 className="text-3xl font-bold bg-gradient-to-r from-orange-400 to-red-400 bg-clip-text text-transparent">
                  {title}
                </h1>
                {subtitle && (
                  <p className="text-zinc-400 mt-1">{subtitle}</p>
                )}
                {user && !subtitle && (
                  <p className="text-zinc-400 mt-1">
                    Welcome back, <span className="text-orange-400 font-medium">{user.full_name || user.email}</span>
                  </p>
                )}
              </motion.div>
              {requireAuth && (
                <div className="flex items-center gap-4">
                  <Link
                    href="/notifications"
                    className="relative p-3 bg-zinc-800 hover:bg-zinc-700 rounded-xl transition-all border border-zinc-700 hover:border-orange-500/50"
                  >
                    <Bell className="w-5 h-5 text-zinc-300" />
                  </Link>
                  <Link
                    href="/dashboard"
                    className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 rounded-xl transition-all font-medium border border-zinc-700"
                  >
                    Dashboard
                  </Link>
                  <button
                    onClick={() => {
                      logout()
                      router.push("/login")
                    }}
                    className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 rounded-xl transition-all font-medium border border-zinc-700 flex items-center gap-2"
                  >
                    <LogOut className="w-4 h-4" />
                    <span>Sign Out</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      <div className="max-w-7xl mx-auto px-6 py-8">
        {children}
      </div>
    </div>
  )
}
