"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/lib/auth-context"
import Link from "next/link"

interface PatientProfile {
  id: number
  first_name: string
  last_name: string
  date_of_birth: string
  gender: string
  email: string
  phone: string
  address: string
  city: string
  state: string
  zip_code: string
  emergency_contact_name: string
  emergency_contact_phone: string
  insurance_provider: string
  insurance_policy_number: string
}

export default function ProfilePage() {
  const router = useRouter()
  const { user, logout } = useAuth()
  const [profile, setProfile] = useState<PatientProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isEditing, setIsEditing] = useState(false)
  const [saving, setSaving] = useState(false)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  useEffect(() => {
    fetchProfile()
  }, [])

  const fetchProfile = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await fetch("http://localhost:8000/api/patient-portal/profile", {
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
      })

      if (!response.ok) {
        throw new Error("Failed to fetch profile")
      }

      const data = await response.json()
      setProfile(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred")
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (!profile) return

    try {
      setSaving(true)
      setError(null)
      const response = await fetch("http://localhost:8000/api/patient-portal/profile", {
        method: "PUT",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(profile),
      })

      if (!response.ok) {
        throw new Error("Failed to update profile")
      }

      setSuccessMessage("Profile updated successfully")
      setIsEditing(false)
      setTimeout(() => setSuccessMessage(null), 3000)
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred")
    } finally {
      setSaving(false)
    }
  }

  const handleLogout = () => {
    logout()
    localStorage.removeItem("portal")
    router.push("/")
  }

  const handleChange = (field: keyof PatientProfile, value: string) => {
    if (profile) {
      setProfile({ ...profile, [field]: value })
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    })
  }

  return (
    <div className="min-h-screen bg-zinc-950">
      <div className="bg-zinc-900 border-b border-zinc-800 px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">Patient Portal</h1>
          <p className="text-sm text-zinc-400">FusionEMS Quantum</p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="text-right">
            <p className="text-sm font-semibold text-zinc-100">{user?.full_name || "User"}</p>
            <p className="text-xs text-zinc-400">{user?.organization_name || "Organization"}</p>
          </div>
          <button
            onClick={handleLogout}
            className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-100 rounded-lg transition-colors"
          >
            Sign Out
          </button>
        </div>
      </div>

      <nav className="bg-zinc-900 border-b border-zinc-800 px-6 py-3">
        <div className="flex space-x-6">
          <Link href="/portals/patient/dashboard" className="text-sm text-zinc-400 hover:text-zinc-100 transition-colors">
            Dashboard
          </Link>
          <Link href="/portals/patient/bills" className="text-sm text-zinc-400 hover:text-zinc-100 transition-colors">
            Bills
          </Link>
          <Link href="/portals/patient/payments" className="text-sm text-zinc-400 hover:text-zinc-100 transition-colors">
            Payment History
          </Link>
          <Link href="/portals/patient/profile" className="text-sm text-zinc-100 font-medium border-b-2 border-blue-500 pb-3">
            Profile
          </Link>
        </div>
      </nav>

      <main className="max-w-5xl mx-auto px-6 py-8">
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-zinc-100 mb-2">Your Profile</h2>
          <p className="text-zinc-400">Manage your personal information</p>
        </div>

        {successMessage && (
          <div className="mb-6 bg-green-900/20 border border-green-800 text-green-400 px-4 py-3 rounded-lg">
            <p className="font-medium">{successMessage}</p>
          </div>
        )}

        {error && (
          <div className="mb-6 bg-red-900/20 border border-red-800 text-red-400 px-4 py-3 rounded-lg">
            <p className="font-medium">Error</p>
            <p className="text-sm">{error}</p>
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
          </div>
        ) : profile ? (
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-semibold text-zinc-100">Personal Information</h3>
                {!isEditing && (
                  <button
                    type="button"
                    onClick={() => setIsEditing(true)}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors text-sm font-medium"
                  >
                    Edit Profile
                  </button>
                )}
              </div>

              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-zinc-400 mb-2">First Name</label>
                  {isEditing ? (
                    <input
                      type="text"
                      value={profile.first_name}
                      onChange={(e) => handleChange("first_name", e.target.value)}
                      className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 text-zinc-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  ) : (
                    <p className="text-zinc-100">{profile.first_name}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-zinc-400 mb-2">Last Name</label>
                  {isEditing ? (
                    <input
                      type="text"
                      value={profile.last_name}
                      onChange={(e) => handleChange("last_name", e.target.value)}
                      className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 text-zinc-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  ) : (
                    <p className="text-zinc-100">{profile.last_name}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-zinc-400 mb-2">Date of Birth</label>
                  {isEditing ? (
                    <input
                      type="date"
                      value={profile.date_of_birth}
                      onChange={(e) => handleChange("date_of_birth", e.target.value)}
                      className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 text-zinc-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  ) : (
                    <p className="text-zinc-100">{formatDate(profile.date_of_birth)}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-zinc-400 mb-2">Gender</label>
                  {isEditing ? (
                    <select
                      value={profile.gender}
                      onChange={(e) => handleChange("gender", e.target.value)}
                      className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 text-zinc-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="Male">Male</option>
                      <option value="Female">Female</option>
                      <option value="Other">Other</option>
                    </select>
                  ) : (
                    <p className="text-zinc-100">{profile.gender}</p>
                  )}
                </div>
              </div>
            </div>

            <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-zinc-100 mb-6">Contact Information</h3>

              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-zinc-400 mb-2">Email</label>
                  {isEditing ? (
                    <input
                      type="email"
                      value={profile.email}
                      onChange={(e) => handleChange("email", e.target.value)}
                      className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 text-zinc-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  ) : (
                    <p className="text-zinc-100">{profile.email}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-zinc-400 mb-2">Phone</label>
                  {isEditing ? (
                    <input
                      type="tel"
                      value={profile.phone}
                      onChange={(e) => handleChange("phone", e.target.value)}
                      className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 text-zinc-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  ) : (
                    <p className="text-zinc-100">{profile.phone}</p>
                  )}
                </div>

                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-zinc-400 mb-2">Address</label>
                  {isEditing ? (
                    <input
                      type="text"
                      value={profile.address}
                      onChange={(e) => handleChange("address", e.target.value)}
                      className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 text-zinc-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  ) : (
                    <p className="text-zinc-100">{profile.address}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-zinc-400 mb-2">City</label>
                  {isEditing ? (
                    <input
                      type="text"
                      value={profile.city}
                      onChange={(e) => handleChange("city", e.target.value)}
                      className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 text-zinc-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  ) : (
                    <p className="text-zinc-100">{profile.city}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-zinc-400 mb-2">State</label>
                  {isEditing ? (
                    <input
                      type="text"
                      value={profile.state}
                      onChange={(e) => handleChange("state", e.target.value)}
                      className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 text-zinc-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  ) : (
                    <p className="text-zinc-100">{profile.state}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-zinc-400 mb-2">ZIP Code</label>
                  {isEditing ? (
                    <input
                      type="text"
                      value={profile.zip_code}
                      onChange={(e) => handleChange("zip_code", e.target.value)}
                      className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 text-zinc-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  ) : (
                    <p className="text-zinc-100">{profile.zip_code}</p>
                  )}
                </div>
              </div>
            </div>

            <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-zinc-100 mb-6">Emergency Contact</h3>

              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-zinc-400 mb-2">Emergency Contact Name</label>
                  {isEditing ? (
                    <input
                      type="text"
                      value={profile.emergency_contact_name}
                      onChange={(e) => handleChange("emergency_contact_name", e.target.value)}
                      className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 text-zinc-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  ) : (
                    <p className="text-zinc-100">{profile.emergency_contact_name}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-zinc-400 mb-2">Emergency Contact Phone</label>
                  {isEditing ? (
                    <input
                      type="tel"
                      value={profile.emergency_contact_phone}
                      onChange={(e) => handleChange("emergency_contact_phone", e.target.value)}
                      className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 text-zinc-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  ) : (
                    <p className="text-zinc-100">{profile.emergency_contact_phone}</p>
                  )}
                </div>
              </div>
            </div>

            <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-zinc-100 mb-6">Insurance Information</h3>

              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-zinc-400 mb-2">Insurance Provider</label>
                  {isEditing ? (
                    <input
                      type="text"
                      value={profile.insurance_provider}
                      onChange={(e) => handleChange("insurance_provider", e.target.value)}
                      className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 text-zinc-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  ) : (
                    <p className="text-zinc-100">{profile.insurance_provider}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-zinc-400 mb-2">Policy Number</label>
                  {isEditing ? (
                    <input
                      type="text"
                      value={profile.insurance_policy_number}
                      onChange={(e) => handleChange("insurance_policy_number", e.target.value)}
                      className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 text-zinc-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  ) : (
                    <p className="text-zinc-100">{profile.insurance_policy_number}</p>
                  )}
                </div>
              </div>
            </div>

            {isEditing && (
              <div className="flex space-x-4">
                <button
                  type="submit"
                  disabled={saving}
                  className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-zinc-800 disabled:text-zinc-500 text-white rounded-lg transition-colors font-medium"
                >
                  {saving ? (
                    <span className="flex items-center space-x-2">
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                      <span>Saving...</span>
                    </span>
                  ) : (
                    "Save Changes"
                  )}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setIsEditing(false)
                    fetchProfile()
                  }}
                  className="px-6 py-3 bg-zinc-800 hover:bg-zinc-700 text-zinc-100 rounded-lg transition-colors font-medium"
                >
                  Cancel
                </button>
              </div>
            )}
          </form>
        ) : (
          <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-8 text-center">
            <h3 className="text-xl font-semibold text-zinc-100 mb-2">Profile Not Found</h3>
            <p className="text-zinc-400">Unable to load your profile information.</p>
          </div>
        )}
      </main>
    </div>
  )
}
