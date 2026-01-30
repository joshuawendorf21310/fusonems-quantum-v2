"use client"
import { apiFetch } from "@/lib/api"
import EnterpriseLoginShell from "@/components/portal/EnterpriseLoginShell"

export default function SchedulingPortalLogin() {
  const handleLogin = async (email: string, password: string) => {
    const response = await apiFetch<{ access_token: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    })
    localStorage.setItem("token", response.access_token)
    localStorage.setItem("portal", "scheduling")
  }

  return (
    <EnterpriseLoginShell
      portalName="Scheduling Portal"
      portalTagline="Advanced crew scheduling and shift management system"
      portalGradient="from-violet-500 via-purple-600 to-indigo-600"
      portalIcon="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
      onSubmit={handleLogin}
      redirectPath="/portals/scheduling/dashboard"
      features={[
        "Intelligent shift planning and optimization",
        "Time tracking and attendance",
        "Crew availability management"
      ]}
    />
  )
}
