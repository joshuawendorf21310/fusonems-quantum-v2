"use client"

import PortalDashboardShell from "@/components/portal/PortalDashboardShell"

export default function DispatchDashboard() {
  const navItems = [
    {
      label: "Dashboard",
      href: "/portals/dispatch/dashboard",
      icon: "M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6",
      active: true
    },
    {
      label: "Active Incidents",
      href: "/portals/dispatch/incidents",
      icon: "M13 10V3L4 14h7v7l9-11h-7z"
    },
    {
      label: "Unit Status",
      href: "/portals/dispatch/units",
      icon: "M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"
    },
    {
      label: "Live Map",
      href: "/portals/dispatch/map",
      icon: "M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"
    },
    {
      label: "Call Log",
      href: "/portals/dispatch/calls",
      icon: "M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"
    },
    {
      label: "Reports",
      href: "/portals/dispatch/reports",
      icon: "M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
    },
    {
      label: "Settings",
      href: "/portals/dispatch/settings",
      icon: "M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z"
    }
  ]

  return (
    <PortalDashboardShell
      portalName="Dispatch Portal"
      portalGradient="from-orange-600 to-amber-600"
      navItems={navItems}
    >
      <div className="space-y-8">
        <div>
          <h2 className="text-4xl font-black text-white mb-2">Dispatch Command Center</h2>
          <p className="text-gray-400 text-lg">Real-time emergency dispatch and resource coordination</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-gray-900/50 border border-gray-800 rounded-2xl p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 bg-red-500/10 border border-red-500/20 rounded-xl flex items-center justify-center">
                <svg className="w-6 h-6 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <span className="px-3 py-1 bg-red-500/10 text-red-500 rounded-lg text-xs font-bold border border-red-500/20">ACTIVE</span>
            </div>
            <p className="text-3xl font-black text-white mb-1">7</p>
            <p className="text-gray-400 text-sm">Active Incidents</p>
          </div>

          <div className="bg-gray-900/50 border border-gray-800 rounded-2xl p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 bg-green-500/10 border border-green-500/20 rounded-xl flex items-center justify-center">
                <svg className="w-6 h-6 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <span className="px-3 py-1 bg-green-500/10 text-green-500 rounded-lg text-xs font-bold border border-green-500/20">AVAILABLE</span>
            </div>
            <p className="text-3xl font-black text-white mb-1">18</p>
            <p className="text-gray-400 text-sm">Units Available</p>
          </div>

          <div className="bg-gray-900/50 border border-gray-800 rounded-2xl p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 bg-blue-500/10 border border-blue-500/20 rounded-xl flex items-center justify-center">
                <svg className="w-6 h-6 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <span className="px-3 py-1 bg-blue-500/10 text-blue-500 rounded-lg text-xs font-bold border border-blue-500/20">AVG</span>
            </div>
            <p className="text-3xl font-black text-white mb-1">3.2m</p>
            <p className="text-gray-400 text-sm">Response Time</p>
          </div>

          <div className="bg-gray-900/50 border border-gray-800 rounded-2xl p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 bg-purple-500/10 border border-purple-500/20 rounded-xl flex items-center justify-center">
                <svg className="w-6 h-6 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                </svg>
              </div>
              <span className="px-3 py-1 bg-purple-500/10 text-purple-500 rounded-lg text-xs font-bold border border-purple-500/20">TODAY</span>
            </div>
            <p className="text-3xl font-black text-white mb-1">52</p>
            <p className="text-gray-400 text-sm">Calls Dispatched</p>
          </div>
        </div>

        <div className="bg-gradient-to-br from-gray-900/80 to-gray-800/50 border border-gray-800 rounded-2xl p-8">
          <h3 className="text-2xl font-black text-white mb-6">Active Incidents</h3>
          <div className="space-y-4">
            <div className="bg-gray-900/50 border border-red-500/20 rounded-xl p-6 flex items-center justify-between hover:border-red-500/40 transition-all">
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 bg-red-500/10 border border-red-500/20 rounded-xl flex items-center justify-center">
                  <span className="text-red-500 font-black">1</span>
                </div>
                <div>
                  <p className="text-white font-bold text-lg">Cardiac Arrest - 123 Main St</p>
                  <p className="text-gray-400 text-sm">Unit M-42 dispatched • 2 minutes ago</p>
                </div>
              </div>
              <span className="px-4 py-2 bg-red-500/10 text-red-500 rounded-xl text-sm font-bold border border-red-500/20">PRIORITY 1</span>
            </div>

            <div className="bg-gray-900/50 border border-orange-500/20 rounded-xl p-6 flex items-center justify-between hover:border-orange-500/40 transition-all">
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 bg-orange-500/10 border border-orange-500/20 rounded-xl flex items-center justify-center">
                  <span className="text-orange-500 font-black">2</span>
                </div>
                <div>
                  <p className="text-white font-bold text-lg">MVA with Injuries - Highway 101</p>
                  <p className="text-gray-400 text-sm">Unit M-15 dispatched • 5 minutes ago</p>
                </div>
              </div>
              <span className="px-4 py-2 bg-orange-500/10 text-orange-500 rounded-xl text-sm font-bold border border-orange-500/20">PRIORITY 2</span>
            </div>

            <div className="bg-gray-900/50 border border-yellow-500/20 rounded-xl p-6 flex items-center justify-between hover:border-yellow-500/40 transition-all">
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 bg-yellow-500/10 border border-yellow-500/20 rounded-xl flex items-center justify-center">
                  <span className="text-yellow-500 font-black">3</span>
                </div>
                <div>
                  <p className="text-white font-bold text-lg">Fall Injury - Senior Center</p>
                  <p className="text-gray-400 text-sm">Unit M-8 dispatched • 8 minutes ago</p>
                </div>
              </div>
              <span className="px-4 py-2 bg-yellow-500/10 text-yellow-500 rounded-xl text-sm font-bold border border-yellow-500/20">PRIORITY 3</span>
            </div>
          </div>
        </div>
      </div>
    </PortalDashboardShell>
  )
}
