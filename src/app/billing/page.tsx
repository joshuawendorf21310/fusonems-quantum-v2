"use client"

import { useState } from "react"
import Link from "next/link"
import Logo from "@/components/Logo"
import TrustBadge from "@/components/marketing/TrustBadge"
import { BILLING_EMAIL, BILLING_PHONE } from "@/lib/site-contact"

type PayMode = "self" | "representative"

export default function BillingPage() {
  const [mode, setMode] = useState<PayMode>("self")
  const [formData, setFormData] = useState({
    accountNumber: "",
    zipCode: "",
    amount: "",
    // Authorized representative fields
    patientDob: "",
    patientLastName: "",
    representativeName: "",
    relationship: "",
  })
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState("")

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value })
    setError("")
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    setError("")

    if (!formData.accountNumber || !formData.zipCode) {
      setError("Please enter account number and ZIP code.")
      setIsSubmitting(false)
      return
    }

    if (mode === "representative") {
      if (!formData.patientDob || !formData.patientLastName || !formData.representativeName || !formData.relationship) {
        setError("Please complete all authorized representative fields.")
        setIsSubmitting(false)
        return
      }
    }

    try {
      const body: Record<string, unknown> = {
        accountNumber: formData.accountNumber,
        zipCode: formData.zipCode,
      }
      if (mode === "representative") {
        body.authorizedRep = true
        body.patientDob = formData.patientDob
        body.patientLastName = formData.patientLastName
        body.representativeName = formData.representativeName
        body.relationship = formData.relationship
      }

      const response = await fetch("/api/billing/lookup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      })

      if (response.ok) {
        const data = await response.json()
        console.log("Account found:", data)
        // TODO: redirect to payment flow when implemented
      } else {
        setError("Account not found. Please verify the information.")
      }
    } catch {
      setError("An error occurred. Please try again.")
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#0a0a0b] text-white">
      <header className="fixed top-0 left-0 right-0 z-50 h-16 bg-[#0a0a0b]/95 backdrop-blur-xl border-b border-white/5">
        <div className="max-w-7xl mx-auto h-full px-6 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-3">
            <div className="relative">
              <div aria-hidden="true" className="absolute -inset-2 rounded-2xl bg-gradient-to-r from-orange-500/25 via-red-600/15 to-transparent blur-lg" />
              <div className="relative w-10 h-10 rounded-xl border border-white/10 bg-white/5 backdrop-blur flex items-center justify-center">
                <Logo variant="icon" width={40} height={40} className="w-8 h-8" />
              </div>
            </div>
            <div className="hidden sm:block">
              <div className="text-white font-black text-lg tracking-tight">FusionEMS Quantum</div>
              <div className="text-[10px] text-gray-500 tracking-widest uppercase">Enterprise EMS Platform</div>
            </div>
          </Link>

          <nav className="hidden md:flex items-center gap-8">
            <Link href="/#modules" className="text-sm text-gray-400 hover:text-white transition-colors">Modules</Link>
            <Link href="/portals" className="text-sm text-gray-400 hover:text-white transition-colors">Portals</Link>
            <Link href="/billing" className="text-sm text-orange-500 font-medium">Pay a Bill</Link>
            <Link href="/#contact" className="text-sm text-gray-400 hover:text-white transition-colors">Contact</Link>
          </nav>

          <Link href="/portals/patient/login" className="px-4 py-2 rounded-lg bg-gradient-to-r from-orange-500 to-red-600 text-white text-sm font-semibold hover:opacity-90 transition-opacity">
            Patient Portal
          </Link>
        </div>
      </header>

      <main className="pt-28 pb-24 px-6">
        <div className="max-w-2xl mx-auto">
          <div className="text-center mb-10">
            <span className="inline-block px-3 py-1 rounded-full bg-orange-500/10 border border-orange-500/20 text-orange-400 text-xs font-semibold tracking-wider uppercase mb-4">
              Billing Portal
            </span>
            <h1 className="text-4xl sm:text-5xl font-black text-white mb-3 tracking-tight">
              Pay a Medical Bill
            </h1>
            <p className="text-lg text-gray-400">
              Secure payment for EMS services. Look up by account or pay as an authorized representative.
            </p>
          </div>

          {/* Mode toggle */}
          <div className="flex rounded-xl bg-white/5 border border-white/10 p-1 mb-8">
            <button
              type="button"
              onClick={() => setMode("self")}
              className={`flex-1 rounded-lg py-3 px-4 text-sm font-semibold transition ${
                mode === "self"
                  ? "bg-white/10 text-white"
                  : "text-gray-400 hover:text-white"
              }`}
            >
              Pay your bill
            </button>
            <button
              type="button"
              onClick={() => setMode("representative")}
              className={`flex-1 rounded-lg py-3 px-4 text-sm font-semibold transition ${
                mode === "representative"
                  ? "bg-white/10 text-white"
                  : "text-gray-400 hover:text-white"
              }`}
            >
              Authorized representative
            </button>
          </div>

          <div className="rounded-2xl border border-white/10 bg-zinc-900/80 backdrop-blur-sm p-8">
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label htmlFor="accountNumber" className="block text-sm font-semibold text-gray-300 mb-2">
                  {mode === "representative" ? "Patient account number" : "Account number"} *
                </label>
                <input
                  type="text"
                  id="accountNumber"
                  name="accountNumber"
                  required
                  value={formData.accountNumber}
                  onChange={handleChange}
                  className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-gray-500 focus:border-orange-400 focus:ring-2 focus:ring-orange-500/20 focus:outline-none transition"
                  placeholder={mode === "representative" ? "Patient's account number" : "Enter your account number"}
                />
              </div>

              <div>
                <label htmlFor="zipCode" className="block text-sm font-semibold text-gray-300 mb-2">
                  {mode === "representative" ? "Patient ZIP code" : "ZIP code"} *
                </label>
                <input
                  type="text"
                  id="zipCode"
                  name="zipCode"
                  required
                  value={formData.zipCode}
                  onChange={handleChange}
                  maxLength={5}
                  pattern="[0-9]{5}"
                  className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-gray-500 focus:border-orange-400 focus:ring-2 focus:ring-orange-500/20 focus:outline-none transition"
                  placeholder="12345"
                />
                <p className="text-xs text-gray-500 mt-1.5">
                  {mode === "representative" ? "ZIP code on the patient's account." : "ZIP code associated with the service address."}
                </p>
              </div>

              {mode === "representative" && (
                <>
                  <div className="pt-2 border-t border-white/10">
                    <p className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-4">
                      Verify patient identity
                    </p>
                    <div className="grid sm:grid-cols-2 gap-4">
                      <div>
                        <label htmlFor="patientDob" className="block text-sm font-semibold text-gray-300 mb-2">
                          Patient date of birth *
                        </label>
                        <input
                          type="date"
                          id="patientDob"
                          name="patientDob"
                          required={mode === "representative"}
                          value={formData.patientDob}
                          onChange={handleChange}
                          className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white focus:border-orange-400 focus:ring-2 focus:ring-orange-500/20 focus:outline-none transition"
                        />
                      </div>
                      <div>
                        <label htmlFor="patientLastName" className="block text-sm font-semibold text-gray-300 mb-2">
                          Patient last name *
                        </label>
                        <input
                          type="text"
                          id="patientLastName"
                          name="patientLastName"
                          required={mode === "representative"}
                          value={formData.patientLastName}
                          onChange={handleChange}
                          className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-gray-500 focus:border-orange-400 focus:ring-2 focus:ring-orange-500/20 focus:outline-none transition"
                          placeholder="Last name"
                        />
                      </div>
                    </div>
                  </div>
                  <div className="border-t border-white/10 pt-4">
                    <p className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-4">
                      Your information (authorized representative)
                    </p>
                    <div className="space-y-4">
                      <div>
                        <label htmlFor="representativeName" className="block text-sm font-semibold text-gray-300 mb-2">
                          Your full name *
                        </label>
                        <input
                          type="text"
                          id="representativeName"
                          name="representativeName"
                          required={mode === "representative"}
                          value={formData.representativeName}
                          onChange={handleChange}
                          className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-gray-500 focus:border-orange-400 focus:ring-2 focus:ring-orange-500/20 focus:outline-none transition"
                          placeholder="First and last name"
                        />
                      </div>
                      <div>
                        <label htmlFor="relationship" className="block text-sm font-semibold text-gray-300 mb-2">
                          Relationship to patient *
                        </label>
                        <select
                          id="relationship"
                          name="relationship"
                          required={mode === "representative"}
                          value={formData.relationship}
                          onChange={handleChange}
                          className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white focus:border-orange-400 focus:ring-2 focus:ring-orange-500/20 focus:outline-none transition [color-scheme:dark]"
                        >
                          <option value="">Select relationship</option>
                          <option value="parent">Parent</option>
                          <option value="guardian">Legal guardian</option>
                          <option value="spouse">Spouse</option>
                          <option value="child">Child</option>
                          <option value="power_of_attorney">Power of attorney</option>
                          <option value="other">Other</option>
                        </select>
                      </div>
                    </div>
                  </div>
                </>
              )}

              {error && (
                <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20">
                  <p className="text-sm text-red-400">{error}</p>
                </div>
              )}

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full rounded-xl bg-gradient-to-r from-orange-500 to-red-600 py-4 px-5 text-base font-semibold text-white hover:opacity-95 active:scale-[0.99] transition disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isSubmitting ? "Looking up account…" : "Continue to payment"}
                </button>
              </div>
            </form>

            <div className="mt-8 pt-8 border-t border-white/10">
              <div className="flex flex-wrap justify-center gap-8 mb-6">
                <div className="flex flex-col items-center gap-1">
                  <svg className="w-10 h-10 text-emerald-400/80" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                  <span className="text-xs text-gray-500 font-medium">PCI-DSS compliant</span>
                </div>
                <div className="flex flex-col items-center gap-1">
                  <svg className="w-10 h-10 text-emerald-400/80" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                  <span className="text-xs text-gray-500 font-medium">256-bit SSL</span>
                </div>
                <div className="flex flex-col items-center gap-1">
                  <svg className="w-10 h-10 text-emerald-400/80" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                  </svg>
                  <span className="text-xs text-gray-500 font-medium">Secure gateway</span>
                </div>
              </div>
              <p className="text-center text-sm text-gray-500 mb-4">
                Need help? Contact billing support
              </p>
              <div className="flex justify-center gap-6 text-sm">
                <a href={`tel:${BILLING_PHONE.replace(/\D/g, "")}`} className="text-orange-400 hover:text-orange-300 transition">
                  📞 {BILLING_PHONE}
                </a>
                <a href={`mailto:${BILLING_EMAIL}`} className="text-orange-400 hover:text-orange-300 transition">
                  ✉️ {BILLING_EMAIL}
                </a>
              </div>
            </div>
          </div>

          <div className="mt-12 flex flex-wrap justify-center gap-12">
            <TrustBadge icon="lock" text="HIPAA-compliant" />
            <TrustBadge icon="shield" text="Secure processing" />
            <TrustBadge icon="headset" text="24/7 support" />
          </div>
          <p className="mt-6 text-center text-xs text-gray-500">
            All transactions are encrypted. We do not store full payment details.
          </p>
        </div>
      </main>

      <footer className="border-t border-white/5 py-8">
        <div className="max-w-7xl mx-auto px-6 text-center">
          <p className="text-orange-500/90 font-bold tracking-widest uppercase text-xs">
            Trusted by leading EMS organizations
          </p>
        </div>
      </footer>
    </div>
  )
}
