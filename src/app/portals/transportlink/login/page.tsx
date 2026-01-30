"use client"
import { apiFetch } from "@/lib/api"
import EnterpriseLoginShell from "@/components/portal/EnterpriseLoginShell"

export default function TransportLinkPortalLogin() {
  const handleLogin = async (email: string, password: string) => {
    const response = await apiFetch<{ access_token: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    })
    localStorage.setItem("token", response.access_token)
    localStorage.setItem("portal", "transportlink")
  }

  return (
    <EnterpriseLoginShell
      portalName="TransportLink"
      portalTagline="Healthcare facility transport request and coordination platform"
      portalGradient="from-cyan-500 via-teal-600 to-teal-700"
      portalIcon="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
      onSubmit={handleLogin}
      redirectPath="/portals/transportlink/dashboard"
      features={[
        "Submit and manage transport requests",
        "Real-time transport tracking",
        "Secure facility communication"
      ]}
    />
  )
}
