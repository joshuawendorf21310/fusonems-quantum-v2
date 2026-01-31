"use client"

import { useEffect, useState } from "react"
import { usePathname } from "next/navigation"
import { useAuth } from "@/lib/auth-context"
import { apiFetch } from "@/lib/api"
import SystemBanner from "./SystemBanner"

const ALLOWED_PATHS = ["/login", "/register", "/password-recovery", "/change-password"]

/**
 * Banner Acceptance Guard (FedRAMP AC-8)
 * 
 * Checks if authenticated users have accepted the system use notification banner.
 * Shows the banner modal if acceptance is required.
 */
export default function BannerAcceptanceGuard() {
  const { isAuthenticated, token } = useAuth()
  const pathname = usePathname()
  const [showBanner, setShowBanner] = useState(false)
  const [checking, setChecking] = useState(true)

  useEffect(() => {
    const checkBannerAcceptance = async () => {
      // Don't check on login/register pages
      if (ALLOWED_PATHS.some((path) => pathname === path || pathname?.startsWith(path + "/"))) {
        setChecking(false)
        return
      }

      // Only check if user is authenticated
      if (!isAuthenticated || !token) {
        setChecking(false)
        return
      }

      try {
        // Try to access a protected endpoint
        // If banner acceptance is required, backend will return 403
        await apiFetch("/auth/me")
        // If we get here, user has accepted banner (or banner check passed)
        setShowBanner(false)
      } catch (err: any) {
        // Check if error is about banner acceptance
        const detail = err.response?.data?.detail
        if (
          detail?.requires_banner_acceptance ||
          detail?.error === "Banner acceptance required" ||
          err.response?.status === 403
        ) {
          // Show banner modal
          setShowBanner(true)
        }
        // Other errors (like 401) - don't show banner
      } finally {
        setChecking(false)
      }
    }

    checkBannerAcceptance()
  }, [isAuthenticated, token, pathname])

  const handleBannerAccept = () => {
    setShowBanner(false)
    // Reload page to refresh auth state
    window.location.reload()
  }

  if (checking) {
    return null
  }

  if (showBanner) {
    return (
      <SystemBanner
        onAccept={handleBannerAccept}
        onError={(err) => {
          console.error("Banner acceptance error:", err)
          // On error, still hide banner to prevent blocking user
          setShowBanner(false)
        }}
      />
    )
  }

  return null
}
