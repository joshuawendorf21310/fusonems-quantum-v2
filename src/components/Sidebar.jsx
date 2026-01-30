import { NavLink } from "react-router-dom"
import PropTypes from "prop-types"
import clsx from "clsx"
import Link from "next/link"
import Logo from "@/components/Logo"
import { useAppData } from "../context/useAppData.js"
import { useAuth } from "../context/useAuth.js"
import { canAccessModule } from "../utils/access.js"

const NAV_ITEMS = [
  { to: "/operations", label: "Operations", moduleKey: "OPS" },
  { to: "/cad", label: "CAD", moduleKey: "CAD" },
  { to: "/tracking", label: "Unit Tracking", moduleKey: "CAD" },
  { to: "/epcr", label: "ePCR", moduleKey: "EPCR" },
  { to: "/scheduling", label: "Scheduling", moduleKey: "SCHEDULING" },
  { to: "/billing", label: "Billing", moduleKey: "BILLING" },
  { to: "/communications", label: "Comms", moduleKey: "COMMS" },
  { to: "/qa", label: "Clinical QA", moduleKey: "QA" },
  { to: "/inventory", label: "Inventory", moduleKey: "INVENTORY" },
  { to: "/fleet", label: "Fleet", moduleKey: "FLEET" },
  { to: "/fire", label: "Fire", moduleKey: "FIRE" },
  { to: "/hems", label: "HEMS", moduleKey: "HEMS" },
  { to: "/hr", label: "HR & Personnel", moduleKey: "HR" },
  { to: "/training", label: "Training Center", moduleKey: "TRAINING" },
  { to: "/documents", label: "Documents", moduleKey: "DOCUMENT_STUDIO" },
  { to: "/ai-console", label: "AI Console", moduleKey: "AI_CONSOLE" },
  { to: "/founder", label: "Founder", moduleKey: "FOUNDER" },
]

export default function Sidebar() {
  const { modules = [], systemHealth } = useAppData()
  const { userRole } = useAuth()

  const moduleIndex = modules.reduce((acc, m) => {
    acc[m.module_key] = m
    return acc
  }, {})

  const visibleItems = NAV_ITEMS.filter((item) => {
    const mod = moduleIndex[item.moduleKey]
    if (mod && (!mod.enabled || mod.kill_switch)) return false
    return canAccessModule(item.moduleKey, userRole)
  })

  const healthLabel =
    systemHealth?.status === "online" ? "Online" : "Degraded"

  return (
    <aside className="sidebar" aria-label="Primary">
      <Link href="/" className="sidebar-brand" aria-label="FusionEMS Quantum home">
        <Logo variant="icon" width={40} height={40} className="sidebar-logo w-10 h-10" />
        <div className="sidebar-brand-text">
          <span className="sidebar-title">FusionEMS</span>
          <span className="sidebar-subtitle">Quantum</span>
        </div>
      </Link>

      <nav className="sidebar-nav">
        <ul role="list">
          {visibleItems.map((item) => (
            <li key={item.to}>
              <NavLink
                to={item.to}
                className={({ isActive }) =>
                  clsx("nav-link", isActive && "active")
                }
                aria-current={({ isActive }) =>
                  isActive ? "page" : undefined
                }
              >
                <span className="nav-label">{item.label}</span>
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      <footer className="sidebar-footer">
        <span className="system-health">
          System: {healthLabel}
        </span>
      </footer>
    </aside>
  )
}

Sidebar.propTypes = {}
