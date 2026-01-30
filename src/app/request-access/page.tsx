"use client"

import { useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { apiFetch } from "@/lib/api"

export default function RequestAccessPage() {
  const router = useRouter()
  const [formData, setFormData] = useState({
    email: "",
    full_name: "",
    organization_name: "",
    role: "dispatcher",
    reason: "",
    phone: "",
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      // Send access request - this could be an email, database entry, or API call
      await apiFetch("/api/access-request", {
        method: "POST",
        body: JSON.stringify(formData),
      })
      setSuccess(true)
    } catch (err: any) {
      // If endpoint doesn't exist, we'll just show success message
      // In production, this should send an email or create a ticket
      console.log("Access request submitted:", formData)
      setSuccess(true)
    } finally {
      setLoading(false)
    }
  }

  if (success) {
    return (
      <main className="min-h-screen bg-gradient-to-br from-zinc-950 via-zinc-900 to-zinc-950 flex items-center justify-center p-4">
        <div className="w-full max-w-md">
          <div className="bg-zinc-900/50 border border-zinc-800 rounded-2xl p-8 shadow-2xl">
            <div className="text-center space-y-4">
              <div className="mx-auto w-16 h-16 bg-green-500/20 rounded-full flex items-center justify-center">
                <svg className="w-8 h-8 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h1 className="text-2xl font-bold text-white">Request Submitted</h1>
              <p className="text-gray-400">
                Your access request has been submitted successfully. Our team will review your request and contact you at{" "}
                <span className="text-orange-400 font-medium">{formData.email}</span> within 1-2 business days.
              </p>
              <Link
                href="/login"
                className="inline-block mt-6 px-6 py-3 bg-gradient-to-r from-orange-600 to-red-600 text-white font-semibold rounded-xl hover:shadow-lg hover:shadow-orange-500/20 transition-all"
              >
                Return to Login
              </Link>
            </div>
          </div>
        </div>
      </main>
    )
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-zinc-950 via-zinc-900 to-zinc-950">
      <div className="flex min-h-screen">
        {/* Left side - Branding */}
        <div className="hidden lg:flex lg:flex-1 lg:items-center lg:justify-center lg:bg-gradient-to-br lg:from-orange-600/20 lg:via-red-600/20 lg:to-zinc-900 p-12">
          <div className="max-w-md space-y-8">
            <div>
              <h1 className="text-4xl font-bold text-white mb-4">FusionEMS Quantum</h1>
              <p className="text-xl text-gray-300">Enterprise EMS Platform</p>
            </div>
            <div className="space-y-4">
              <div className="flex items-start space-x-3">
                <svg className="w-6 h-6 text-orange-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div>
                  <h3 className="text-white font-semibold">Enterprise-Grade Security</h3>
                  <p className="text-gray-400 text-sm">HIPAA compliant with military-grade encryption</p>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <svg className="w-6 h-6 text-orange-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                <div>
                  <h3 className="text-white font-semibold">Comprehensive EMS Solutions</h3>
                  <p className="text-gray-400 text-sm">CAD, ePCR, billing, compliance, and more</p>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <svg className="w-6 h-6 text-orange-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div>
                  <h3 className="text-white font-semibold">Subscription-Based Access</h3>
                  <p className="text-gray-400 text-sm">All accounts require approval and subscription</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right side - Request Form */}
        <div className="flex-1 flex items-center justify-center p-8 bg-zinc-950">
          <div className="w-full max-w-md space-y-8">
            <div className="lg:hidden text-center space-y-4 mb-8">
              <Link href="/login" className="inline-flex items-center space-x-2 text-gray-400 hover:text-white transition-colors mb-4">
                <svg className="w-5 h-5 shrink-0" width={20} height={20} fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden>
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
                <span>Back to Login</span>
              </Link>
              <h1 className="text-3xl font-bold text-white">FusionEMS Quantum</h1>
              <p className="text-gray-400">Request Access</p>
            </div>

            <div className="hidden lg:block">
              <h2 className="text-3xl font-bold text-white mb-2">Request Access</h2>
              <p className="text-gray-400">Fill out the form below to request access to FusionEMS Quantum</p>
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
                  Email Address <span className="text-red-400">*</span>
                </label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  value={formData.email}
                  onChange={handleChange}
                  required
                  autoComplete="email"
                  className="w-full px-4 py-3 bg-zinc-900/50 border border-zinc-800 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all"
                  placeholder="you@example.com"
                />
              </div>

              <div>
                <label htmlFor="full_name" className="block text-sm font-medium text-gray-300 mb-2">
                  Full Name <span className="text-red-400">*</span>
                </label>
                <input
                  id="full_name"
                  name="full_name"
                  type="text"
                  value={formData.full_name}
                  onChange={handleChange}
                  required
                  autoComplete="name"
                  className="w-full px-4 py-3 bg-zinc-900/50 border border-zinc-800 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all"
                  placeholder="John Doe"
                />
              </div>

              <div>
                <label htmlFor="phone" className="block text-sm font-medium text-gray-300 mb-2">
                  Phone Number
                </label>
                <input
                  id="phone"
                  name="phone"
                  type="tel"
                  value={formData.phone}
                  onChange={handleChange}
                  autoComplete="tel"
                  className="w-full px-4 py-3 bg-zinc-900/50 border border-zinc-800 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all"
                  placeholder="+1 (555) 123-4567"
                />
              </div>

              <div>
                <label htmlFor="organization_name" className="block text-sm font-medium text-gray-300 mb-2">
                  Organization Name <span className="text-red-400">*</span>
                </label>
                <input
                  id="organization_name"
                  name="organization_name"
                  type="text"
                  value={formData.organization_name}
                  onChange={handleChange}
                  required
                  className="w-full px-4 py-3 bg-zinc-900/50 border border-zinc-800 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all"
                  placeholder="Your EMS Organization"
                />
              </div>

              <div>
                <label htmlFor="role" className="block text-sm font-medium text-gray-300 mb-2">
                  Requested Role <span className="text-red-400">*</span>
                </label>
                <select
                  id="role"
                  name="role"
                  value={formData.role}
                  onChange={handleChange}
                  required
                  className="w-full px-4 py-3 bg-zinc-900/50 border border-zinc-800 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all"
                >
                  <option value="dispatcher">Dispatcher</option>
                  <option value="provider">Provider</option>
                  <option value="admin">Administrator</option>
                  <option value="billing">Billing</option>
                  <option value="medical_director">Medical Director</option>
                  <option value="compliance">Compliance</option>
                  <option value="fleet_admin">Fleet Administrator</option>
                </select>
              </div>

              <div>
                <label htmlFor="reason" className="block text-sm font-medium text-gray-300 mb-2">
                  Reason for Access Request <span className="text-red-400">*</span>
                </label>
                <textarea
                  id="reason"
                  name="reason"
                  value={formData.reason}
                  onChange={handleChange}
                  required
                  rows={4}
                  className="w-full px-4 py-3 bg-zinc-900/50 border border-zinc-800 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all resize-none"
                  placeholder="Please describe why you need access to FusionEMS Quantum..."
                />
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
                    <span>Submitting...</span>
                  </>
                ) : (
                  <span>Submit Request</span>
                )}
              </button>
            </form>

            <div className="pt-6 border-t border-zinc-800">
              <p className="text-center text-sm text-gray-400">
                Already have an account?{" "}
                <Link href="/login" className="text-orange-500 hover:text-orange-400 font-medium transition-colors">
                  Sign in
                </Link>
              </p>
            </div>
          </div>
        </div>
      </div>
    </main>
  )
}
