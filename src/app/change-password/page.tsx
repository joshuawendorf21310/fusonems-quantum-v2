"use client"

import { useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { apiClient } from "@/lib/api"

export default function ChangePasswordPage() {
  const router = useRouter()
  const [currentPassword, setCurrentPassword] = useState("")
  const [newPassword, setNewPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    if (newPassword !== confirmPassword) {
      setError("New password and confirmation do not match.")
      return
    }
    if (newPassword.length < 8) {
      setError("New password must be at least 8 characters.")
      return
    }
    setLoading(true)
    try {
      await apiClient.post("/auth/change-password", {
        current_password: currentPassword,
        new_password: newPassword,
      })
      localStorage.removeItem("must_change_password")
      const role = JSON.parse(atob((localStorage.getItem("token") || "").split(".")[1] || "{}")).role
      router.push(role === "founder" ? "/founder" : "/dashboard")
      window.location.reload()
    } catch (err: unknown) {
      const message =
        err && typeof err === "object" && "response" in err && err.response && typeof (err.response as { data?: { detail?: string } }).data?.detail === "string"
          ? (err.response as { data: { detail: string } }).data.detail
          : "Failed to change password. Check your current password."
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-zinc-950 flex items-center justify-center p-4">
      <div className="w-full max-w-md space-y-6">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-white">Change your password</h1>
          <p className="text-gray-400 mt-1">You must set a new password before continuing.</p>
        </div>

        {error && (
          <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="current" className="block text-sm font-medium text-gray-300 mb-2">
              Current password
            </label>
            <input
              id="current"
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              required
              autoComplete="current-password"
              className="w-full px-4 py-3 bg-zinc-900/50 border border-zinc-800 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
              placeholder="Enter current password (e.g. Pass1234)"
            />
          </div>
          <div>
            <label htmlFor="new" className="block text-sm font-medium text-gray-300 mb-2">
              New password
            </label>
            <input
              id="new"
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
              minLength={8}
              autoComplete="new-password"
              className="w-full px-4 py-3 bg-zinc-900/50 border border-zinc-800 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
              placeholder="At least 8 characters"
            />
          </div>
          <div>
            <label htmlFor="confirm" className="block text-sm font-medium text-gray-300 mb-2">
              Confirm new password
            </label>
            <input
              id="confirm"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              minLength={8}
              autoComplete="new-password"
              className="w-full px-4 py-3 bg-zinc-900/50 border border-zinc-800 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
              placeholder="Confirm new password"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 px-4 bg-gradient-to-r from-orange-600 to-red-600 text-white font-semibold rounded-xl hover:shadow-lg hover:shadow-orange-500/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? "Updating…" : "Change password"}
          </button>
        </form>

        <p className="text-center text-sm text-gray-500">
          <Link href="/login" className="text-orange-500 hover:text-orange-400">
            Back to login
          </Link>
        </p>
      </div>
    </div>
  )
}
