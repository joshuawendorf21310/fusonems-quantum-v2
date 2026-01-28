"use client"

import { ReactNode, useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { useAuth } from "@/lib/auth-context"

interface PortalDashboardShellProps {
  portalName: string
  portalGradient: string
  portalIcon: ReactNode
  children: ReactNode
  navigationItems: Array<{
    name: string
    href: string
    icon: ReactNode
  }>
}

export default function PortalDashboardShell({
  portalName,
  portalGradient,
  portalIcon,
  children,
  navigationItems,
}: PortalDashboardShellProps) {
  const router = useRouter()
  const { user, logout } = useAuth()
  const [sidebarOpen, setSidebarOpen] = useState(true)

  const handleLogout = () => {
    logout()
    localStorage.removeItem("portal")
    router.push("/")
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className={`fixed top-0 left-0 right-0 h-16 bg-gradient-to-r ${portalGradient} shadow-lg z-40 flex items-center justify-between px-6`}>
        <div className="flex items-center space-x-4">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="text-white hover:bg-white/20 rounded-lg p-2 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-white/20 backdrop-blur-xl rounded-lg flex items-center justify-center">
              {portalIcon}
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">{portalName}</h1>
              <p className="text-xs text-white/70">FusionEMS Quantum</p>
            </div>
          </div>
        </div>
        <div className="flex items-center space-x-4">
          <div className="text-right">
            <p className="text-sm font-semibold text-white">{user?.full_name || "User"}</p>
            <p className="text-xs text-white/70">{user?.organization_name || "Organization"}</p>
          </div>
          <button
            onClick={handleLogout}
            className="px-4 py-2 bg-white/20 hover:bg-white/30 text-white rounded-lg transition-colors flex items-center space-x-2"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
            <span>Sign Out</span>
          </button>
        </div>
      </div>

      <div className="flex pt-16">
        <aside className={`${sidebarOpen ? "w-64" : "w-0"} fixed left-0 top-16 bottom-0 bg-white border-r border-gray-200 transition-all duration-300 overflow-hidden shadow-lg`}>
          <nav className="p-4 space-y-2">
            {navigationItems.map((item) => (
              <Link
                key={item.name}
                href={item.href}
                className="flex items-center space-x-3 px-4 py-3 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <div className="w-5 h-5">{item.icon}</div>
                <span className="font-medium">{item.name}</span>
              </Link>
            ))}
          </nav>
        </aside>

        <main className={`${sidebarOpen ? "ml-64" : "ml-0"} flex-1 p-8 transition-all duration-300`}>
          {children}
        </main>
      </div>
    </div>
  )
}
