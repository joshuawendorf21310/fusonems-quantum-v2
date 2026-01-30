"use client"

import { useState, ReactNode } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/lib/auth-context"
import Link from "next/link"
import Logo from "@/components/Logo"

interface NavItem {
  label: string
  href: string
  icon: string
  active?: boolean
}

interface PortalDashboardShellProps {
  portalName: string
  portalGradient: string
  navItems: NavItem[]
  children: ReactNode
}

export default function PortalDashboardShell({
  portalName,
  portalGradient,
  navItems,
  children
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
    <div className="min-h-screen w-full bg-zinc-950 flex">
      <aside className={`${sidebarOpen ? "w-72" : "w-20"} bg-zinc-900/95 border-r border-white/10 backdrop-blur-sm transition-all duration-300 flex flex-col fixed left-0 top-0 h-screen z-50`}>
        <div className={`bg-gradient-to-r ${portalGradient} px-6 py-6 border-b border-white/10`}>
          {sidebarOpen ? (
            <Link href="/" className="flex items-center gap-3 group" aria-label="FusionEMS Quantum home">
              <div className="w-9 h-9 rounded-lg bg-white/10 border border-white/20 flex items-center justify-center flex-shrink-0">
                <Logo variant="icon" width={36} height={36} className="w-7 h-7" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-white tracking-tight">{portalName}</h2>
                <p className="text-sm text-white/80 mt-0.5">FusionEMS Quantum</p>
              </div>
            </Link>
          ) : (
            <Link href="/" className="w-9 h-9 rounded-lg bg-white/20 flex items-center justify-center flex-shrink-0 mx-auto" aria-label="FusionEMS Quantum home">
              <Logo variant="icon" width={36} height={36} className="w-7 h-7" />
            </Link>
          )}
        </div>

        <nav className="flex-1 px-3 py-5 space-y-1 overflow-y-auto">
          {navItems.map((item, idx) => (
            <Link
              key={idx}
              href={item.href}
              className={`flex items-center space-x-3 px-4 py-3 rounded-xl transition-all ${
                item.active
                  ? `bg-white/10 text-white font-semibold border border-white/15 shadow-sm`
                  : "text-zinc-400 hover:text-white hover:bg-white/5 border border-transparent"
              }`}
            >
              <svg className="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={item.icon} />
              </svg>
              {sidebarOpen && <span className="text-sm font-medium">{item.label}</span>}
            </Link>
          ))}
        </nav>

        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="mx-3 mb-4 px-3 py-2.5 bg-white/5 hover:bg-white/10 border border-white/10 text-zinc-300 hover:text-white rounded-xl transition-colors flex items-center justify-center space-x-2"
        >
          <svg className={`w-5 h-5 transition-transform ${sidebarOpen ? "" : "rotate-180"}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
          </svg>
          {sidebarOpen && <span className="font-medium text-sm">Collapse</span>}
        </button>
      </aside>

      <div className={`flex-1 ${sidebarOpen ? "ml-72" : "ml-20"} transition-all duration-300 min-h-screen flex flex-col`}>
        <header className="relative overflow-hidden bg-zinc-900/95 backdrop-blur-md border-b border-white/10 px-8 py-4 flex items-center justify-between sticky top-0 z-40">
          <div className={`absolute inset-0 bg-gradient-to-r ${portalGradient} opacity-[0.15] pointer-events-none`} aria-hidden />
          <div className="relative z-10 flex items-center justify-between w-full">
            <div className="flex items-center space-x-4">
            <Link href="/" className="w-10 h-10 rounded-xl border border-white/15 bg-white/10 flex items-center justify-center flex-shrink-0" aria-label="FusionEMS Quantum home">
              <Logo variant="icon" width={40} height={40} className="w-8 h-8" />
            </Link>
            <div>
              <h1 className="text-xl font-bold text-white tracking-tight">{portalName}</h1>
              <p className="text-sm text-zinc-400">Enterprise Management Platform</p>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <button className="relative p-2.5 hover:bg-white/10 rounded-xl transition-colors text-white">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
              <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full border-2 border-zinc-900" />
            </button>

            <div className="flex items-center space-x-3 pl-4 border-l border-white/15">
              <div className="text-right hidden sm:block">
                <p className="text-sm font-semibold text-white">{user?.full_name || "User"}</p>
                <p className="text-xs text-zinc-400">{user?.organization_name || "Organization"}</p>
              </div>
              <div className="w-10 h-10 bg-white/15 rounded-xl border border-white/20 flex items-center justify-center">
                <span className="text-white font-semibold text-sm">
                  {(user?.full_name || "U").charAt(0).toUpperCase()}
                </span>
              </div>
            </div>

            <button
              onClick={handleLogout}
              className="px-4 py-2.5 bg-white/10 hover:bg-white/15 text-white rounded-xl transition-all font-medium text-sm border border-white/15 flex items-center space-x-2"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
              <span>Sign Out</span>
            </button>
          </div>
          </div>
        </header>

        <main className="flex-1 p-8 bg-zinc-950">
          <div className="max-w-6xl mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}
