"use client"

import { PageShell } from "@/components/PageShell"

export default function DispatchDashboard() {
  return (
    <PageShell title="Dispatch Portal" requireAuth={true}>
      <div className="space-y-8">
        <section className="portal-hero">
          <h2 className="text-4xl font-black tracking-tight text-white mb-2">Dispatch Command Center</h2>
          <p className="text-zinc-400 text-lg">Real-time emergency dispatch and resource coordination</p>
        </section>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <PortalStatCard
            value="7"
            label="Active Incidents"
            badge="ACTIVE"
            badgeVariant="red"
            icon={<svg className="w-6 h-6 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>}
          />
          <PortalStatCard
            value="18"
            label="Units Available"
            badge="AVAILABLE"
            badgeVariant="green"
            icon={<svg className="w-6 h-6 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>}
          />
          <PortalStatCard
            value="3.2m"
            label="Response Time"
            badge="AVG"
            badgeVariant="blue"
            icon={<svg className="w-6 h-6 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>}
          />
          <PortalStatCard
            value="52"
            label="Calls Dispatched"
            badge="TODAY"
            badgeVariant="purple"
            icon={<svg className="w-6 h-6 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" /></svg>}
          />
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
    </PageShell>
  )
}
