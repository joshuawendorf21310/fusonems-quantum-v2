"use client"
import { apiFetch } from "@/lib/api"
import EnterpriseLoginShell from "@/components/portal/EnterpriseLoginShell"

export default function FirePortalLogin() {
  const handleLogin = async (email: string, password: string) => {
    const response = await apiFetch<{ access_token: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    })
    localStorage.setItem("token", response.access_token)
    localStorage.setItem("portal", "fire")
  }

  return (
    <EnterpriseLoginShell
      portalName="Fire Portal"
      portalTagline="Specialized platform for fire-based EMS operations and reporting"
      portalGradient="from-orange-600 via-red-600 to-red-700"
      portalIcon="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z"
      onSubmit={handleLogin}
      redirectPath="/portals/fire/dashboard"
      features={[
        "Station and battalion management",
        "Fire and EMS incident reporting",
        "Personnel tracking and readiness"
      ]}
    />
  )
}
