"use client"
import { apiFetch } from "@/lib/api"
import EnterpriseLoginShell from "@/components/portal/EnterpriseLoginShell"

export default function FusionCareLogin() {
  const handleLogin = async (email: string, password: string) => {
    const response = await apiFetch<{ access_token: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    })
    localStorage.setItem("token", response.access_token)
    localStorage.setItem("portal", "carefusion")
  }

  return (
    <EnterpriseLoginShell
      portalName="FusionCare"
      portalTagline="Native telehealth and clinical oversight — medical control, specialist escalation, documentation-backed decisions"
      portalGradient="from-cyan-500 via-cyan-600 to-blue-600"
      portalIcon="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
      onSubmit={handleLogin}
      redirectPath="/portals/carefusion/dashboard"
      features={[
        "Clinical decision support and medical control",
        "Live consults and specialist escalation",
        "Integrated documentation for care and billing"
      ]}
    />
  )
}
