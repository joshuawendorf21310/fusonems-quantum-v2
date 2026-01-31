"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { apiFetch } from "@/lib/api"
import { useAuth } from "@/lib/auth-context"
import { SystemBanner } from "@/components/SystemBanner"

export default function LoginPage() {
  const router = useRouter()
  const { isAuthenticated } = useAuth()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [rememberMe, setRememberMe] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showBanner, setShowBanner] = useState(false)
  const [bannerId, setBannerId] = useState<string | null>(null)

  useEffect(() => {
    const storedEmail = localStorage.getItem("remember_email")
    if (storedEmail) {
      setEmail(storedEmail)
      setRememberMe(true)
    }
  }, [])

  // Only redirect if authenticated and not showing banner
  useEffect(() => {
    if (isAuthenticated && !showBanner) {
      router.push("/dashboard")
    }
  }, [isAuthenticated, showBanner, router])

  const handleBannerAccept = async () => {
    try {
      if (bannerId) {
        await apiFetch(`/auth/banner/${bannerId}/accept`, { method: "POST" })
      }
      setShowBanner(false)
      router.push("/dashboard")
    } catch (err) {
      setError("Failed to accept banner. Please try again.")
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const response = await apiFetch<{ access_token: string; user?: { role?: string; must_change_password?: boolean } }>(
        "/auth/login",
        {
          method: "POST",
          body: JSON.stringify({ email, password }),
        }
      )
      localStorage.setItem("token", response.access_token)
      if (rememberMe) {
        localStorage.setItem("remember_email", email)
      } else {
        localStorage.removeItem("remember_email")
      }
      
      // Check if banner acceptance is required (FedRAMP AC-8)
      // The backend login endpoint checks for banner acceptance and returns 403 if not accepted
      // If login succeeds, BannerAcceptanceGuard will handle showing banner if needed
      // But we can also check here to show banner immediately after login
      try {
        await apiFetch("/auth/me")
        // If we get here, user has accepted banner (or banner check passed)
      } catch (bannerErr: any) {
        // Check if error is about banner acceptance
        const bannerDetail = bannerErr.response?.data?.detail
        if (bannerDetail?.requires_banner_acceptance || bannerDetail?.error === "Banner acceptance required") {
          setShowBanner(true)
          return // Show banner modal, don't navigate yet
        }
        // Other errors - proceed with normal flow
      }
      
      if (response.user?.must_change_password) {
        localStorage.setItem("must_change_password", "true")
        router.push("/change-password")
        return
      }
      const role = response.user?.role
      router.push(role === "founder" ? "/founder" : "/dashboard")
    } catch (err: any) {
      const detail = err.response?.data?.detail
      
      // Check if error is about banner acceptance requirement
      if (detail?.requires_banner_acceptance || detail?.error === "Banner acceptance required") {
        setBannerId(detail?.banner_id || null)
        setShowBanner(true)
        return
      }
      
      const message =
        typeof detail === "string"
          ? detail
          : typeof detail === "object" && detail?.message
            ? detail.message
            : Array.isArray(detail) && detail[0]?.msg
              ? detail.map((d: { msg?: string }) => d.msg).filter(Boolean).join(". ")
              : "Login failed. Please try again."
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  const handleDevAccess = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await apiFetch<{ access_token: string; user?: { must_change_password?: boolean } }>("/auth/dev_seed", {
        method: "POST",
      })
      localStorage.setItem("token", response.access_token)
      if (response.user?.must_change_password) {
        localStorage.setItem("must_change_password", "true")
        router.push("/change-password")
        window.location.reload()
        return
      }
      router.push("/founder")
      window.location.reload()
    } catch (err: any) {
      setError(err.response?.data?.detail || "Dev access failed. Set ENV=development and LOCAL_AUTH_ENABLED=true in the backend.")
    } finally {
      setLoading(false)
    }
  }

  const securityFeatures = [
    {
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
        </svg>
      ),
      title: "Military-Grade Security",
      description: "Bank-level 256-bit AES encryption protecting your data"
    },
    {
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
      ),
      title: "HIPAA Compliant",
      description: "Fully compliant with healthcare security standards"
    },
    {
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      ),
      title: "99.9% Uptime",
      description: "Cloud infrastructure with automatic failover"
    },
    {
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      title: "24/7 Monitoring",
      description: "Real-time threat detection and security monitoring"
    }
  ]

  return (
    <div className="min-h-screen bg-zinc-950 flex">
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-orange-600 to-red-600 relative overflow-hidden">
        <div className="absolute inset-0 bg-black/20"></div>
        <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-10"></div>
        
        <div className="relative z-10 flex flex-col justify-between p-12 text-white w-full">
          <Link href="/" className="flex items-center space-x-3 hover:opacity-80 transition-opacity text-white">
            <div className="w-10 h-10 min-w-[2.5rem] max-w-[2.5rem] min-h-[2.5rem] max-h-[2.5rem] bg-white/20 backdrop-blur-sm rounded-lg flex items-center justify-center shrink-0">
              <svg className="w-6 h-6 shrink-0" width={24} height={24} fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden>
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
            </div>
            <span className="font-semibold">Back to Home</span>
          </Link>

          <div className="space-y-8">
            <div className="space-y-4">
              <div className="inline-flex items-center justify-center w-20 h-20 min-w-[5rem] max-w-[5rem] min-h-[5rem] max-h-[5rem] rounded-2xl bg-white/20 backdrop-blur-sm shrink-0">
                <svg className="w-12 h-12 shrink-0 text-white" width={48} height={48} fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden>
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <h1 className="text-5xl font-bold leading-tight">
                Enterprise EMS Platform
              </h1>
              <p className="text-xl text-white/80 max-w-md">
                The complete solution for emergency medical services, fire departments, and HEMS operations.
              </p>
            </div>

            <div className="grid grid-cols-1 gap-6 max-w-lg">
              {securityFeatures.map((feature, index) => (
                <div key={index} className="flex items-start space-x-4 bg-white/10 backdrop-blur-sm rounded-xl p-4 border border-white/20">
                  <div className="flex-shrink-0 text-white">
                    {feature.icon}
                  </div>
                  <div>
                    <h3 className="font-semibold text-white mb-1">{feature.title}</h3>
                    <p className="text-sm text-white/70">{feature.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="text-sm text-white/60">
            &copy; {new Date().getFullYear()} FusionEMS Quantum. All rights reserved.
          </div>
        </div>
      </div>

      <div className="flex-1 flex items-center justify-center p-8 bg-zinc-950">
        <div className="w-full max-w-md space-y-8">
          <div className="lg:hidden text-center space-y-4 mb-8">
            <Link href="/" className="inline-flex items-center space-x-2 text-gray-400 hover:text-white transition-colors mb-4">
              <svg className="w-5 h-5 shrink-0" width={20} height={20} fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden>
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              <span>Back to Home</span>
            </Link>
            <h1 className="text-3xl font-bold text-white">FusionEMS Quantum</h1>
            <p className="text-gray-400">Enterprise EMS Platform</p>
          </div>

          <div className="hidden lg:block">
            <h2 className="text-3xl font-bold text-white mb-2">Welcome Back</h2>
            <p className="text-gray-400">Sign in to your account to continue</p>
          </div>

          {error && (
            <div
              role="alert"
              aria-live="assertive"
              className="p-4 bg-red-500/10 border border-red-500/30 rounded-xl"
            >
              <div className="flex items-center space-x-3">
                <svg className="w-5 h-5 text-red-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden>
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p className="text-red-400 text-sm">{error}</p>
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-300 mb-2">
                Email Address
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
                className="w-full px-4 py-3 bg-zinc-900/50 border border-zinc-800 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all"
                placeholder="you@example.com"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-300 mb-2">
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete="current-password"
                  className="w-full px-4 py-3 bg-zinc-900/50 border border-zinc-800 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all pr-12"
                  placeholder="Enter your password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  aria-pressed={showPassword}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white transition-colors"
                >
                  {showPassword ? (
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                    </svg>
                  ) : (
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  )}
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <label htmlFor="remember-me" className="flex items-center space-x-2 cursor-pointer group">
                <input
                  id="remember-me"
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="w-4 h-4 bg-zinc-900 border-zinc-700 rounded text-orange-500 focus:ring-2 focus:ring-orange-500 focus:ring-offset-0 cursor-pointer"
                />
                <span className="text-sm text-gray-400 group-hover:text-gray-300 transition-colors">Remember me</span>
              </label>
              <Link href="/password-recovery" className="text-sm text-orange-500 hover:text-orange-400 transition-colors font-medium">
                Forgot password?
              </Link>
            </div>

            <button
              type="submit"
              disabled={loading}
              aria-busy={loading}
              className="w-full py-3 px-4 bg-gradient-to-r from-orange-600 to-red-600 text-white font-semibold rounded-xl hover:shadow-lg hover:shadow-orange-500/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
            >
              {loading ? (
                <>
                  <svg className="animate-spin h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span>Signing in...</span>
                </>
              ) : (
                <span>Sign In</span>
              )}
            </button>
          </form>

          <div className="pt-6 border-t border-zinc-800 space-y-4">
            <p className="text-center text-sm text-gray-400">
              Don't have an account?{" "}
              <Link href="/register" className="text-orange-500 hover:text-orange-400 font-medium transition-colors">
                Create one
              </Link>
            </p>
            {process.env.NODE_ENV === "development" && (
              <div className="text-center">
                <button
                  type="button"
                  onClick={handleDevAccess}
                  disabled={loading}
                  className="text-sm text-amber-400 hover:text-amber-300 font-medium transition-colors disabled:opacity-50"
                >
                  Dev access (founder) — no password
                </button>
                <p className="text-xs text-gray-500 mt-1">Creates dev@local founder user and logs you in</p>
              </div>
            )}
            <p className="text-center text-sm text-gray-500">
              Secure enterprise authentication · FusionEMS Quantum
            </p>
          </div>
        </div>
      </div>
    </>
  )
}
