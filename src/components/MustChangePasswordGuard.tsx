"use client"

import { useEffect } from "react"
import { usePathname, useRouter } from "next/navigation"

const ALLOWED = ["/change-password", "/login", "/register", "/password-recovery"]

export default function MustChangePasswordGuard() {
  const pathname = usePathname()
  const router = useRouter()

  useEffect(() => {
    if (typeof window === "undefined") return
    const token = localStorage.getItem("token")
    const mustChange = localStorage.getItem("must_change_password") === "true"
    const allowed = ALLOWED.some((p) => pathname === p || pathname?.startsWith(p + "/"))
    if (token && mustChange && !allowed) {
      router.replace("/change-password")
    }
  }, [pathname, router])

  return null
}
