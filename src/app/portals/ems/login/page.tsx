"use client"
import { apiFetch } from "@/lib/api"
import EnterpriseLoginShell from "@/components/portal/EnterpriseLoginShell"

export default function EMSPortalLogin() {
  const handleLogin = async (email: string, password: string) => {
    const response = await apiFetch<{ access_token: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    })
    localStorage.setItem("token", response.access_token)
    localStorage.setItem("portal", "ems")
  }

  return (
    <EnterpriseLoginShell
      portalName="EMS Portal"
      portalTagline="Complete crew management, scheduling, and clinical documentation platform"
      portalGradient="from-red-500 via-red-600 to-orange-600"
      portalIcon="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
      onSubmit={handleLogin}
      redirectPath="/portals/ems/dashboard"
      features={[
        "Crew scheduling and shift management",
        "Electronic patient care reports (ePCR)",
        "Unit tracking and resource management"
      ]}
    />
  )
}
