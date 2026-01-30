"use client"

import { usePathname } from "next/navigation"
import BillingAIAssistant from "@/components/billing/BillingAIAssistant"

export default function BillingLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const pathname = usePathname() ?? ""
  const pageContext =
    pathname.includes("denials") ? "Denials page" :
    pathname.includes("claims-ready") ? "Claims ready to submit" :
    pathname.includes("dashboard") ? "Billing dashboard" :
    pathname.includes("batch-submit") ? "Batch submit" :
    pathname.includes("denial-workflow") ? "Denial workflow" :
    pathname.includes("review") ? "Claim review" :
    "Billing"

  return (
    <div style={{ display: "flex", flexDirection: "column", minHeight: "100vh" }}>
      {children}
      <div style={{ maxWidth: 900, width: "100%", margin: "0 auto", padding: "0 1.5rem 2rem" }}>
        <BillingAIAssistant pageContext={pageContext} />
      </div>
    </div>
  )
}
