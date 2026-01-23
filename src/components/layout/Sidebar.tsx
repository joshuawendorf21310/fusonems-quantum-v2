"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"

const navItems = [
  { label: "Dashboard", href: "/dashboard", icon: "🛰️" },
  { label: "CareFusion", href: "/carefusion", icon: "⚙️" },
  { label: "CAD", href: "/cad", icon: "📡" },
  { label: "ePCR", href: "/epcr", icon: "🧾" },
  { label: "NEMSIS", href: "/nemsis", icon: "🧭" },
  { label: "NFIRS", href: "/nfirs", icon: "🔥" },
  { label: "Billing", href: "/billing", icon: "🧮" },
  { label: "Patient Portal", href: "/patient", icon: "🩺" },
  { label: "Compliance", href: "/compliance", icon: "🛡️" },
  { label: "Comms Hub", href: "/comms", icon: "📞" },
  { label: "CrewLink", href: "/crewlink", icon: "🚑" },
  { label: "Inventory", href: "/inventory", icon: "📦" },
  { label: "Founders", href: "/founders", icon: "🎛️" },
]

export default function Sidebar() {
  const pathname = usePathname() ?? ""

  return (
    <nav className="platform-sidebar" aria-label="Platform navigation">
      <div className="platform-logo">FusionEMS Quantum</div>
      <ul>
        {navItems.map((item) => {
          const isActive = pathname === item.href
          return (
            <li key={item.href}>
              <Link
                href={item.href}
                className={`sidebar-link ${isActive ? "active" : ""}`}
                aria-current={isActive ? "page" : undefined}
              >
                <span aria-hidden="true">{item.icon}</span>
                <span>{item.label}</span>
              </Link>
            </li>
          )
        })}
      </ul>
    </nav>
  )
}
