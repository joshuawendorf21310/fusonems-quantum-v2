"use client"
import { apiFetch } from "@/lib/api"
import EnterpriseLoginShell from "@/components/portal/EnterpriseLoginShell"

export default function DispatchPortalLogin() {
  const handleLogin = async (email: string, password: string) => {
    const response = await apiFetch<{ access_token: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    })
    localStorage.setItem("token", response.access_token)
    localStorage.setItem("portal", "dispatch")
  }

  return (
    <EnterpriseLoginShell
      portalName="Dispatch Portal"
      portalTagline="Real-time computer-aided dispatch and emergency incident management"
      portalGradient="from-amber-500 via-orange-600 to-red-600"
      portalIcon="M8 7v8a2 2 0 002 2h6M8 7V5a2 2 0 012-2h4.586a1 1 0 01.707.293l4.414 4.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-2M8 7H6a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2v-2"
      onSubmit={handleLogin}
      redirectPath="/portals/dispatch/dashboard"
      features={[
        "911 call intake and processing",
        "Real-time unit dispatch and tracking",
        "Incident lifecycle management"
      ]}
    />
  )
}
