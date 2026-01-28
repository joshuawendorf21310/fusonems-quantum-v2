"use client"
import { useRouter } from "next/navigation"
import { useAuth } from "@/lib/auth-context"

export default function SchedulingDashboard() {
  const router = useRouter()
  const { user, logout } = useAuth()

  return (
    <div className="min-h-screen bg-gradient-to-br from-violet-50 to-purple-50">
      <div className="bg-gradient-to-r from-violet-600 to-purple-600 shadow-lg px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Scheduling Portal</h1>
          <p className="text-sm text-violet-100">FusionEMS Quantum</p>
        </div>
        <button
          onClick={() => { logout(); localStorage.removeItem("portal"); router.push("/"); }}
          className="px-4 py-2 bg-white/20 hover:bg-white/30 text-white rounded-lg transition-colors"
        >
          Sign Out
        </button>
      </div>
      <main className="max-w-7xl mx-auto px-6 py-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-6">Welcome to Scheduling Portal</h2>
        <p className="text-gray-600">Crew scheduling and shift management</p>
      </main>
    </div>
  )
}
