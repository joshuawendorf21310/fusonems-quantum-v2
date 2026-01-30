"use client"

import { useState, FormEvent } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import Logo from "@/components/Logo"

interface EnterpriseLoginShellProps {
  portalName: string
  portalTagline: string
  portalGradient: string
  portalIcon: string
  onSubmit: (email: string, password: string) => Promise<void>
  redirectPath: string
  features: string[]
}

export default function EnterpriseLoginShell({
  portalName,
  portalTagline,
  portalGradient,
  portalIcon,
  onSubmit,
  redirectPath,
  features
}: EnterpriseLoginShellProps) {
  const router = useRouter()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [rememberMe, setRememberMe] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      await onSubmit(email, password)
      if (rememberMe) {
        localStorage.setItem("remember_email", email)
      }
      router.push(redirectPath)
    } catch (err: unknown) {
      const message =
        err instanceof Error
          ? err.message
          : "Authentication failed. Please check your credentials."
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen w-full bg-[#0a0a0b] flex">
      {/* Left — Tech hero */}
      <div className="hidden lg:flex lg:w-1/2 xl:w-3/5 relative overflow-hidden">
        <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:64px_64px]" aria-hidden />
        <div className={`absolute inset-0 bg-gradient-to-br ${portalGradient} opacity-[0.12]`} aria-hidden />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full bg-white/[0.02] blur-3xl" aria-hidden />
        <div className="relative z-10 flex flex-col justify-between w-full max-w-lg mx-auto px-14 py-12">
          <Link href="/" className="inline-flex items-center gap-2.5 text-white/90 hover:text-white transition-colors w-fit">
            <div className="w-9 h-9 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center">
              <Logo variant="icon" width={36} height={36} className="w-7 h-7" />
            </div>
            <span className="font-semibold text-base tracking-tight">FusionEMS Quantum</span>
          </Link>

          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-white/50 mb-4">Portal</p>
            <h1 className="text-4xl xl:text-5xl font-bold text-white tracking-tight leading-[1.1] mb-4">
              {portalName}
            </h1>
            <p className="text-lg text-white/60 max-w-md leading-relaxed mb-8">
              {portalTagline}
            </p>
            <div className="space-y-3">
              {features.map((feature, i) => (
                <div key={i} className="flex items-center gap-3 text-white/70 text-sm font-medium">
                  <span className="w-1 h-1 rounded-full bg-white/50 flex-shrink-0" aria-hidden />
                  {feature}
                </div>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-4 text-xs text-white/40 font-medium">
            <span className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400/80" aria-hidden />
              HIPAA
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-sky-400/80" aria-hidden />
              256-bit
            </span>
          </div>
        </div>
      </div>

      {/* Right — Modern form */}
      <div className="w-full lg:w-1/2 xl:w-2/5 min-h-screen flex items-center justify-center p-6 sm:p-10 bg-[#0a0a0b]">
        <div className="w-full max-w-[400px]">
          {/* Mobile: brand */}
          <div className="lg:hidden mb-10">
            <Link href="/" className="inline-flex items-center gap-2.5 text-white/90 mb-8">
              <Logo variant="icon" width={36} height={36} className="w-9 h-9" />
              <span className="font-semibold text-lg">FusionEMS Quantum</span>
            </Link>
            <h1 className="text-3xl font-bold text-white tracking-tight">{portalName}</h1>
            <p className="text-white/50 text-base mt-1">{portalTagline}</p>
          </div>

          <div className="lg:mb-10">
            <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">Sign in</h2>
            <p className="text-white/50 text-base mt-1">Use your credentials to access the portal.</p>
          </div>

          {error && (
            <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/30 flex items-center gap-3">
              <svg className="w-5 h-5 text-red-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-red-300 text-sm font-medium">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-white/80 mb-2">
                Email
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full px-4 py-3.5 rounded-xl bg-white/5 border border-white/10 text-white placeholder-white/30 text-base focus:outline-none focus:border-white/25 focus:ring-2 focus:ring-white/10 transition-all"
                placeholder="you@company.com"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-white/80 mb-2">
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="w-full px-4 py-3.5 pr-12 rounded-xl bg-white/5 border border-white/10 text-white placeholder-white/30 text-base focus:outline-none focus:border-white/25 focus:ring-2 focus:ring-white/10 transition-all"
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 p-1.5 text-white/40 hover:text-white/70 rounded-lg transition-colors"
                  aria-label={showPassword ? "Hide password" : "Show password"}
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
              <label className="flex items-center gap-2.5 cursor-pointer">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="w-4 h-4 rounded border-white/20 bg-white/5 text-white focus:ring-2 focus:ring-white/20"
                />
                <span className="text-sm text-white/60">Remember me</span>
              </label>
              <Link href="/password-recovery" className="text-sm font-medium text-white/70 hover:text-white transition-colors">
                Forgot password?
              </Link>
            </div>

            <button
              type="submit"
              disabled={loading}
              className={`w-full py-4 px-5 rounded-xl bg-gradient-to-r ${portalGradient} text-white font-semibold text-base transition-all disabled:opacity-50 disabled:cursor-not-allowed hover:opacity-95 active:scale-[0.99] flex items-center justify-center gap-2 shadow-lg`}
            >
              {loading ? (
                <>
                  <svg className="animate-spin h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  <span>Signing in…</span>
                </>
              ) : (
                <>
                  <span>Sign in</span>
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
                  </svg>
                </>
              )}
            </button>
          </form>

          <p className="mt-8 text-center text-xs text-white/40">
            Secure access · <Link href="/security" className="text-white/60 hover:text-white transition-colors">Learn more</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
