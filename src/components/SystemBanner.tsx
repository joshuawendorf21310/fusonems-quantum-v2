"use client"

import { useEffect, useState } from "react"
import { apiFetch } from "@/lib/api"

interface SystemBannerProps {
  onAccept: () => void
  onError?: (error: string) => void
}

interface BannerData {
  text: string
  version: string
  requires_acceptance: boolean
}

/**
 * System Use Notification Banner Component (FedRAMP AC-8)
 * 
 * Displays the FedRAMP-compliant system use notification banner
 * and requires user acceptance before granting access to the system.
 */
export default function SystemBanner({ onAccept, onError }: SystemBannerProps) {
  const [banner, setBanner] = useState<BannerData | null>(null)
  const [accepted, setAccepted] = useState(false)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Fetch banner from backend
    const fetchBanner = async () => {
      try {
        const data = await apiFetch<BannerData>("/auth/system-banner")
        setBanner(data)
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Failed to load system banner"
        setError(errorMessage)
        onError?.(errorMessage)
      } finally {
        setLoading(false)
      }
    }

    fetchBanner()
  }, [onError])

  const handleAccept = async () => {
    if (!banner || !accepted) {
      return
    }

    setSubmitting(true)
    setError(null)

    try {
      await apiFetch("/auth/accept-banner", {
        method: "POST",
        body: JSON.stringify({
          banner_version: banner.version,
        }),
      })
      onAccept()
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to accept banner"
      setError(errorMessage)
      onError?.(errorMessage)
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm">
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-8 max-w-2xl w-full mx-4">
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500"></div>
            <span className="ml-3 text-white">Loading system notification...</span>
          </div>
        </div>
      </div>
    )
  }

  if (!banner) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm">
        <div className="bg-zinc-900 border border-red-500/30 rounded-xl p-8 max-w-2xl w-full mx-4">
          <div className="text-center">
            <h2 className="text-xl font-semibold text-white mb-2">Error Loading Banner</h2>
            <p className="text-gray-400 mb-4">{error || "Failed to load system use notification"}</p>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-orange-500 hover:bg-orange-600 text-white rounded-lg transition-colors"
            >
              Reload Page
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
      <div className="bg-zinc-900 border border-orange-500/30 rounded-xl shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-zinc-900 border-b border-zinc-800 px-6 py-4">
          <div className="flex items-center space-x-3">
            <div className="flex-shrink-0">
              <svg
                className="w-6 h-6 text-orange-500"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-white">
              System Use Notification
            </h2>
          </div>
        </div>

        {/* Content */}
        <div className="px-6 py-6">
          <div className="bg-zinc-950/50 border border-zinc-800 rounded-lg p-6 mb-6">
            <p className="text-gray-300 leading-relaxed whitespace-pre-line">
              {banner.text}
            </p>
          </div>

          {error && (
            <div className="mb-4 p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
              <p className="text-red-400 text-sm">{error}</p>
            </div>
          )}

          {/* Acceptance Checkbox */}
          <div className="mb-6">
            <label className="flex items-start space-x-3 cursor-pointer group">
              <input
                type="checkbox"
                checked={accepted}
                onChange={(e) => setAccepted(e.target.checked)}
                className="mt-1 w-5 h-5 rounded border-zinc-700 bg-zinc-800 text-orange-500 focus:ring-2 focus:ring-orange-500 focus:ring-offset-2 focus:ring-offset-zinc-900 cursor-pointer"
                required
              />
              <span className="text-gray-300 group-hover:text-white transition-colors">
                I have read and understand the system use notification. I acknowledge that:
                <ul className="mt-2 ml-6 list-disc space-y-1 text-sm text-gray-400">
                  <li>This system is for authorized users only</li>
                  <li>All activities may be monitored and recorded</li>
                  <li>Unauthorized use is prohibited and may result in legal action</li>
                </ul>
              </span>
            </label>
          </div>

          {/* Actions */}
          <div className="flex justify-end space-x-3">
            <button
              onClick={() => {
                // User cannot proceed without accepting
                if (!accepted) {
                  setError("You must accept the system use notification to continue.")
                  return
                }
                handleAccept()
              }}
              disabled={!accepted || submitting}
              className="px-6 py-2.5 bg-orange-500 hover:bg-orange-600 disabled:bg-zinc-700 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors"
            >
              {submitting ? (
                <span className="flex items-center">
                  <svg
                    className="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    ></circle>
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    ></path>
                  </svg>
                  Accepting...
                </span>
              ) : (
                "I Accept and Continue"
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
