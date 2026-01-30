"use client"

import { apiFetch } from "@/lib/api"
import EnterpriseLoginShell from "@/components/portal/EnterpriseLoginShell"

export default function FusionCarePatientLogin() {
  const handleLogin = async (email: string, password: string) => {
    const response = await apiFetch<{ access_token: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    })
    localStorage.setItem("token", response.access_token)
    localStorage.setItem("portal", "carefusion_patient")
  }

  return (
    <EnterpriseLoginShell
      portalName="FusionCare Patient"
      portalTagline="Access your health records, virtual consultations, and billing"
      portalGradient="from-cyan-500 via-cyan-600 to-blue-600"
      portalIcon="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
      features={[
        "Protected Health Information",
        "Virtual Consultations",
        "Medical Records Access",
        "Easy Billing & Payments",
      ]}
      onSubmit={handleLogin}
      redirectPath="/portals/carefusion/patient/dashboard"
    />
  )
}
