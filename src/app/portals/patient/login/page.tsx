"use client"

import { apiFetch } from "@/lib/api"
import { useState } from "react"
import { useRouter } from "next/navigation"
import Logo from "@/components/Logo"

const heroFeatures = [
  { label: "View visit history and vitals instantly", icon: "M3 12l6 6L21 6" },
  { label: "Pay bills securely from any device", icon: "M3 12l6 6L21 6" },
  { label: "Message the billing team directly", icon: "M3 12l6 6L21 6" },
]

export default function PatientPortalLogin() {
  const router = useRouter()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [rememberMe, setRememberMe] = useState(false)
  const [loginError, setLoginError] = useState<string | null>(null)
  const [loginLoading, setLoginLoading] = useState(false)

  const [step, setStep] = useState<"lookup" | "verify" | "result">("lookup")
  const [lookupId, setLookupId] = useState("")
  const [lookupError, setLookupError] = useState<string | null>(null)
  const [verifyType, setVerifyType] = useState<"patient" | "rep" | null>(null)
  const [verifyFields, setVerifyFields] = useState<{ dob?: string; lastName?: string; relationship?: string }>({})
  const [verifyError, setVerifyError] = useState<string | null>(null)
  const [billData, setBillData] = useState<Record<string, unknown> | null>(null)
  const [loading, setLoading] = useState(false)

  const handleLogin = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (loginLoading) return
    setLoginError(null)
    setLoginLoading(true)
    try {
      const response = await apiFetch<{ access_token: string }>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      })
      localStorage.setItem("token", response.access_token)
      localStorage.setItem("portal", "patient")
      if (rememberMe) {
        localStorage.setItem("remember_email", email)
      }
      router.push("/portals/patient/dashboard")
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Authentication failed. Please check your credentials."
      setLoginError(message)
    } finally {
      setLoginLoading(false)
    }
  }

  const handleLookup = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setLookupError(null)
    if (!lookupId) {
      setLookupError("Please enter a Bill or Transport ID.")
      return
    }
    setStep("verify")
  }

  const handleVerify = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setVerifyError(null)
    setLoading(true)
    try {
      const response = await fetch("/api/transport-bill/verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          id: lookupId,
          type: verifyType,
          ...verifyFields,
        }),
      })
      if (!response.ok) throw new Error("Verification failed")
      const data = await response.json()
      setBillData(data)
      setStep("result")
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Verification failed"
      setVerifyError(message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="relative min-h-screen overflow-hidden bg-slate-950 text-white">
      <div
        aria-hidden="true"
        className="absolute inset-0 -z-10 opacity-80"
      >
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(255,140,0,0.22),_transparent_45%)]" />
        <div className="absolute inset-x-0 top-0 h-1/2 bg-gradient-to-b from-[#0d0d0f] via-transparent to-transparent" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_70%_35%,_rgba(239,68,68,0.16),_rgba(239,68,68,0)_40%)]" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_70%,_rgba(255,140,0,0.12),_transparent_42%)]" />
        <div className="absolute -left-24 top-24 h-[520px] w-[520px] rotate-12 bg-gradient-to-br from-orange-500/18 via-transparent to-red-600/14 blur-3xl" />
        <div className="absolute right-0 top-0 h-[420px] w-[640px] bg-[conic-gradient(from_180deg_at_70%_20%,rgba(255,107,53,0.18),rgba(239,68,68,0.10),rgba(255,179,0,0.10),rgba(255,107,53,0.18))] blur-3xl opacity-70" />
        <div
          className="absolute inset-0 bg-[radial-gradient(circle,_rgba(255,255,255,0.06),_transparent_65%)]"
          style={{
            backgroundSize: "140px 140px",
            backgroundPosition: "0 0",
            backgroundImage:
              "radial-gradient(circle,_rgba(255,255,255,0.08)_1px,_transparent_2px)",
          }}
        />
        <div className="absolute inset-0 opacity-[0.06] [background:repeating-linear-gradient(90deg,rgba(255,255,255,0.8)_0px,rgba(255,255,255,0.8)_1px,transparent_1px,transparent_14px)]" />
        <div className="absolute -top-44 right-8 h-[420px] w-[420px] rounded-full bg-gradient-to-br from-orange-500/26 via-red-600/18 to-transparent blur-3xl" />
        <div className="absolute bottom-10 left-8 h-[320px] w-[320px] rounded-full bg-gradient-to-br from-white/10 via-orange-500/6 to-transparent blur-3xl" />
      </div>
      <div className="flex min-h-screen flex-col gap-10 px-6 py-10 lg:flex-row lg:items-center lg:gap-8 lg:px-12 lg:py-16">
        <section className="hidden lg:flex lg:flex-[0.55] flex-col justify-between rounded-[32px] bg-gradient-to-b from-[#030303] via-[#08080a] to-[#120309] p-10 shadow-[0_40px_120px_rgba(0,0,0,0.8)]">
          <div className="space-y-8">
            <div className="flex items-center gap-4">
              <div className="relative flex h-14 w-14 items-center justify-center rounded-3xl border border-white/10 bg-white/5 backdrop-blur shadow-[0_18px_60px_rgba(0,0,0,0.6)]">
                <div aria-hidden="true" className="absolute -inset-3 rounded-[26px] bg-gradient-to-r from-orange-500/25 via-red-600/16 to-transparent blur-xl" />
                <Logo variant="icon" width={56} height={56} className="relative h-12 w-12" />
              </div>
              <div>
                <p className="text-sm uppercase tracking-[0.4em] text-orange-200/80">FusionEMS Quantum</p>
                <p className="text-xs text-slate-400">Enterprise EMS Operating System</p>
              </div>
            </div>

            <div>
              <h1 className="text-4xl font-black text-white">Patient Portal</h1>
              <p className="mt-2 max-w-xs text-base text-slate-200">
                Securely access billing, records, and communication tools anytime. The portal is HIPAA-ready
                and optimized for mission-critical visibility.
              </p>
            </div>
          </div>

          <div className="space-y-5">
            {heroFeatures.map((feature) => (
              <div key={feature.label} className="flex items-start gap-3">
                <div className="mt-1 h-10 w-10 rounded-xl bg-gradient-to-br from-orange-500 via-[#ff6b40] to-red-500 text-white shadow-lg shadow-orange-600/40">
                  <svg viewBox="0 0 24 24" className="h-full w-full p-2">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" stroke="currentColor" fill="none" d={feature.icon} />
                  </svg>
                </div>
                <p className="text-base leading-relaxed text-slate-100">{feature.label}</p>
              </div>
            ))}
          </div>

          <div className="flex items-center justify-between border-t border-white/10 pt-6 text-xs text-slate-300">
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-emerald-400"></span>
              HIPAA compliant
            </div>
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-cyan-400"></span>
              256-bit encryption
            </div>
          </div>
        </section>

        <section className="flex w-full flex-1 flex-col gap-6 lg:flex-[0.45]">
          <div className="rounded-[32px] border border-orange-500/30 bg-[#030303] p-8 shadow-[0_25px_70px_rgba(255,87,34,0.3)] backdrop-blur">
            <div className="mb-6 space-y-2">
              <p className="text-sm font-semibold uppercase tracking-[0.4em] text-slate-400">Patient Portal</p>
              <h2 className="text-3xl font-black text-white">Sign in to continue</h2>
              <p className="text-sm text-slate-400">Access statements, records, and communicate with our billing team.</p>
            </div>
            {loginError && (
              <div className="mb-4 rounded-2xl border border-red-500/70 bg-red-500/10 p-4 text-sm text-red-300">
                {loginError}
              </div>
            )}
            <form onSubmit={handleLogin} className="space-y-5">
              <label className="text-sm font-semibold text-slate-300">
                Email address
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="mt-2 w-full rounded-2xl border border-orange-500/50 bg-white/5 px-4 py-3 text-base text-white placeholder:text-slate-500 focus:border-orange-400 focus:outline-none focus:ring-2 focus:ring-orange-500/40"
                  placeholder="you@example.com"
                />
              </label>

              <label className="text-sm font-semibold text-slate-300">
                Password
                <div className="relative mt-2">
                  <input
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    className="w-full rounded-2xl border border-orange-500/50 bg-white/5 px-4 py-3 pr-12 text-base text-white placeholder:text-slate-500 focus:border-orange-400 focus:outline-none focus:ring-2 focus:ring-orange-500/40"
                    placeholder="Enter your password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((prev) => !prev)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-sm text-slate-400 transition-colors hover:text-orange-300"
                  >
                    {showPassword ? "Hide" : "Show"}
                  </button>
                </div>
              </label>

              <div className="flex items-center justify-between text-sm text-slate-400">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    className="h-4 w-4 rounded border border-orange-500/40 bg-white/5 text-orange-400 focus:ring-0"
                  />
                  Remember me
                </label>
                <button type="button" className="font-semibold text-cyan-400 hover:text-cyan-300">
                  Forgot password?
                </button>
              </div>

                <button
                  type="submit"
                  disabled={loginLoading}
                  className="w-full rounded-2xl bg-gradient-to-r from-orange-500 to-red-500 px-5 py-3 text-base font-bold text-white shadow-lg shadow-orange-600/40 transition hover:shadow-xl disabled:opacity-60"
                >
                  {loginLoading ? "Authenticating..." : "Sign in securely"}
                </button>
            </form>

            <p className="mt-6 text-center text-xs uppercase tracking-[0.4em] text-slate-500">
              Protected by enterprise-grade security
            </p>
          </div>

          <div className="space-y-6">
            <article className="rounded-3xl border border-orange-500/20 bg-[#050504] p-6 shadow-xl backdrop-blur">
              <h3 className="text-lg font-black text-white">Transport Bill Lookup</h3>
              <p className="mt-2 text-sm text-slate-400">Find your billing or transport record before verifying identity.</p>
                <form onSubmit={handleLookup} className="mt-4 space-y-4">
                <input
                  type="text"
                  value={lookupId}
                  onChange={(e) => setLookupId(e.target.value)}
                  className="w-full rounded-2xl border border-orange-500/40 bg-white/5 px-4 py-3 text-sm text-white placeholder:text-slate-500 focus:border-orange-400 focus:outline-none focus:ring-2 focus:ring-orange-500/30"
                  placeholder="Enter Bill or Transport ID"
                />
                <button
                  type="submit"
                  className="w-full rounded-2xl bg-gradient-to-r from-orange-500 to-red-500 px-4 py-3 text-sm font-semibold text-white transition hover:opacity-90"
                >
                  Look up bill
                </button>
                {lookupError && <p className="text-xs text-red-400">{lookupError}</p>}
              </form>
            </article>

            {step === "verify" && (
              <article className="rounded-3xl border border-white/10 bg-slate-900/70 p-6 shadow-xl backdrop-blur">
                <div className="mb-4 flex gap-2">
                  {["patient", "rep"].map((type) => (
                    <button
                      key={type}
                      type="button"
                      onClick={() => setVerifyType(type as "patient" | "rep")}
                  className={`flex-1 rounded-2xl border px-3 py-2 text-sm font-semibold transition ${
                    verifyType === type
                      ? "border-orange-500 bg-orange-500/10 text-orange-300"
                      : "border-white/10 text-slate-400 hover:border-white/20"
                  }`}
                    >
                      {type === "patient" ? "Patient" : "Authorized Rep"}
                    </button>
                  ))}
                </div>
                {verifyType && (
                  <form onSubmit={handleVerify} className="space-y-3">
                    <div>
                      <label className="text-xs uppercase tracking-[0.4em] text-slate-500">Date of Birth</label>
                      <input
                        type="date"
                        value={verifyFields.dob || ""}
                        onChange={(e) => setVerifyFields((prev) => ({ ...prev, dob: e.target.value }))}
                        required
                        className="mt-2 w-full rounded-2xl border border-white/10 bg-white/5 px-3 py-3 text-sm text-white placeholder:text-slate-500 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/30"
                      />
                    </div>
                    <div>
                      <label className="text-xs uppercase tracking-[0.4em] text-slate-500">Patient Last Name</label>
                      <input
                        type="text"
                        value={verifyFields.lastName || ""}
                        onChange={(e) => setVerifyFields((prev) => ({ ...prev, lastName: e.target.value }))}
                        required
                        className="mt-2 w-full rounded-2xl border border-white/10 bg-white/5 px-3 py-3 text-sm text-white placeholder:text-slate-500 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/30"
                      />
                    </div>
                    {verifyType === "rep" && (
                      <div>
                        <label className="text-xs uppercase tracking-[0.4em] text-slate-500">Relationship to patient</label>
                        <input
                          type="text"
                          value={verifyFields.relationship || ""}
                          onChange={(e) => setVerifyFields((prev) => ({ ...prev, relationship: e.target.value }))}
                          required
                          className="mt-2 w-full rounded-2xl border border-white/10 bg-white/5 px-3 py-3 text-sm text-white placeholder:text-slate-500 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/30"
                        />
                      </div>
                    )}
                    <button
                      type="submit"
                      disabled={loading}
                      className="mt-3 w-full rounded-2xl bg-gradient-to-r from-blue-500 to-cyan-500 px-4 py-3 text-sm font-semibold text-white shadow-lg shadow-cyan-500/40 transition hover:shadow-xl disabled:opacity-60"
                    >
                      {loading ? "Verifying..." : "Verify & view bill"}
                    </button>
                    {verifyError && <p className="text-xs text-red-400">{verifyError}</p>}
                  </form>
                )}
              </article>
            )}

            {step === "result" && billData && (
              <article className="rounded-3xl border border-orange-500/20 bg-[#050504] p-6 shadow-xl backdrop-blur">
                <h3 className="text-lg font-black text-white">Billing details captured</h3>
                <p className="mt-2 text-sm text-slate-400">
                  The latest transport or bill data has been connected to your session. You can now review and pay securely.
                </p>
                <pre className="mt-4 max-h-48 overflow-auto rounded-2xl bg-slate-900/80 p-4 text-xs text-slate-200">
                  {JSON.stringify(billData, null, 2)}
                </pre>
              </article>
            )}
          </div>
        </section>
      </div>
    </main>
  )
}
