"use client"

import React, { useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { Stethoscope } from "lucide-react"
import Logo from "@/components/Logo"

const portalName = "FusionCare Provider"
const portalTagline = "Secure access to patient charts, prescriptions, and dispatch-linked missions."
const portalGradient = "from-cyan-600 via-cyan-700 to-blue-600"
const portalIcon = (
  <div className="h-14 w-14 rounded-2xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center text-white shadow-lg">
    <Stethoscope className="h-8 w-8" />
  </div>
)
const features = [
  "View assigned patients and active missions",
  "eRx with formulary and allergy checks",
  "Dispatch-linked visit timelines",
  "Role-based access and audit trails",
]

const EnterpriseLoginShell: React.FC = () => {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const router = useRouter()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError("")

    try {
      // TODO: wire to real auth endpoint
      await new Promise((resolve) => setTimeout(resolve, 400))
      router.push("/portals/carefusion/provider/dashboard")
    } catch (err) {
      setError("Login failed. Please check your credentials.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={`min-h-screen flex items-center justify-center bg-gradient-to-r ${portalGradient}`}>
      <div className="bg-white p-8 rounded-lg shadow-lg max-w-md w-full">
        <div className="flex flex-col items-center text-center mb-8">
          <Link href="/" className="inline-flex items-center space-x-3 mb-6">
            <div className="w-14 h-14 rounded-xl border border-gray-200 bg-gray-50 flex items-center justify-center flex-shrink-0">
              <Logo variant="icon" width={56} height={56} className="w-12 h-12" />
            </div>
            <div className="text-left">
              <div className="text-gray-900 font-black text-2xl tracking-tight">FusionEMS Quantum</div>
              <div className="text-gray-500 text-sm font-medium">Enterprise EMS Operating System</div>
            </div>
          </Link>
          <div className="flex justify-center mb-4">{portalIcon}</div>
          <h1 className="text-2xl font-bold text-center mb-2">{portalName}</h1>
          <p className="text-center text-gray-600">{portalTagline}</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-cyan-500"
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-cyan-500"
          />
          {error && <p className="text-red-500 text-sm">{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-cyan-600 hover:bg-cyan-700 text-white font-semibold py-2 px-4 rounded-md transition"
          >
            {loading ? "Logging in..." : "Login"}
          </button>
        </form>

        <ul className="mt-6 space-y-2 text-sm text-gray-700">
          {features.map((feature, idx) => (
            <li key={idx} className="flex items-start">
              <span className="mr-2 text-cyan-600">✓</span>
              <span>{feature}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}

export default EnterpriseLoginShell
