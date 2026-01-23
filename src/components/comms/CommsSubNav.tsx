"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"

const navItems = [
  { label: "Overview", href: "/comms" },
  { label: "Email", href: "/comms/email" },
  { label: "SMS", href: "/comms/sms" },
  { label: "Fax", href: "/comms/fax" },
  { label: "Voice", href: "/comms/voice" },
  { label: "Queue", href: "/comms/queue" },
  { label: "Audit", href: "/comms/audit" },
]

export default function CommsSubNav() {
  const pathname = usePathname()

  return (
    <aside className="comms-subnav">
      <div className="comms-subnav-title">
        <p className="eyebrow">Communications</p>
        <h2>Command Hub</h2>
      </div>
      <nav aria-label="Communications sections">
        <ul>
          {navItems.map((item) => (
            <li key={item.href}>
              <Link
                href={item.href}
                className={`comms-subnav-link ${pathname === item.href ? "active" : ""}`}
              >
                {item.label}
              </Link>
            </li>
          ))}
        </ul>
      </nav>
    </aside>
  )
}
