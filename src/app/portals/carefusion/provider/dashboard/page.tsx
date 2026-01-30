import Link from 'next/link'

export default function ProviderDashboard() {
  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 p-6">
      <header className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-white">Provider Dashboard</h1>
          <p className="text-zinc-400">Dr. Sarah Smith, MD • Emergency Medicine</p>
        </div>
        <div className="flex gap-4">
           <div className="flex items-center gap-2 px-3 py-1 bg-green-900/20 border border-green-900 rounded-full">
             <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
             <span className="text-green-400 text-sm">Available</span>
           </div>
           <Link href="/api/auth/logout" className="px-4 py-2 bg-zinc-800 rounded hover:bg-zinc-700 transition">Sign Out</Link>
        </div>
      </header>

      {/* Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-zinc-900 p-4 rounded-lg border border-zinc-800">
          <div className="text-zinc-400 text-xs uppercase mb-1">Appointments Today</div>
          <div className="text-2xl font-bold">8</div>
        </div>
        <div className="bg-zinc-900 p-4 rounded-lg border border-zinc-800">
          <div className="text-zinc-400 text-xs uppercase mb-1">Waiting Room</div>
          <div className="text-2xl font-bold text-[#FF6B35]">2</div>
        </div>
        <div className="bg-zinc-900 p-4 rounded-lg border border-zinc-800">
          <div className="text-zinc-400 text-xs uppercase mb-1">Messages</div>
          <div className="text-2xl font-bold">5</div>
        </div>
        <div className="bg-zinc-900 p-4 rounded-lg border border-zinc-800">
          <div className="text-zinc-400 text-xs uppercase mb-1">Avg. Wait Time</div>
          <div className="text-2xl font-bold text-green-400">4m</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Schedule Column */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-zinc-900 border border-zinc-800 rounded-lg overflow-hidden">
            <div className="px-6 py-4 border-b border-zinc-800 flex justify-between items-center">
              <h3 className="font-bold text-white">Upcoming Appointments</h3>
              <Link href="/portals/carefusion/provider/schedule" className="text-sm text-[#FF6B35] hover:underline">View Calendar</Link>
            </div>
            <div className="divide-y divide-zinc-800">
              {/* Appointment Item */}
              <div className="p-4 hover:bg-zinc-800/30 transition flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="text-center min-w-[60px]">
                    <div className="text-lg font-bold text-white">10:00</div>
                    <div className="text-xs text-zinc-500">AM</div>
                  </div>
                  <div>
                    <div className="font-medium text-white">Michael Johnson</div>
                    <div className="text-sm text-zinc-400">Follow-up • Hypertension</div>
                  </div>
                </div>
                <div className="flex gap-2">
                  <button className="px-3 py-1.5 bg-zinc-800 text-zinc-300 text-sm rounded hover:bg-zinc-700">Chart</button>
                  <button className="px-3 py-1.5 bg-[#FF6B35] text-white text-sm rounded hover:bg-[#e55a2b]">Start Video</button>
                </div>
              </div>
              {/* Appointment Item */}
              <div className="p-4 hover:bg-zinc-800/30 transition flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="text-center min-w-[60px]">
                    <div className="text-lg font-bold text-white">10:30</div>
                    <div className="text-xs text-zinc-500">AM</div>
                  </div>
                  <div>
                    <div className="font-medium text-white">Emily Davis</div>
                    <div className="text-sm text-zinc-400">New Patient • Chest Pain</div>
                  </div>
                </div>
                <div className="flex gap-2">
                  <button className="px-3 py-1.5 bg-zinc-800 text-zinc-300 text-sm rounded hover:bg-zinc-700">Chart</button>
                  <button className="px-3 py-1.5 bg-zinc-700 text-zinc-500 text-sm rounded cursor-not-allowed">Waiting</button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Sidebar Column */}
        <div className="space-y-6">
          {/* Patient Queue */}
          <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
            <h3 className="font-bold text-white mb-4">Patient Queue</h3>
            <div className="space-y-3">
              <div className="p-3 bg-zinc-800/50 rounded border border-zinc-700/50 flex justify-between items-center">
                <div>
                  <div className="text-sm font-medium text-white">James Wilson</div>
                  <div className="text-xs text-zinc-400">Waiting 12m</div>
                </div>
                <span className="w-2 h-2 bg-green-500 rounded-full"></span>
              </div>
              <div className="p-3 bg-zinc-800/50 rounded border border-zinc-700/50 flex justify-between items-center">
                <div>
                  <div className="text-sm font-medium text-white">Linda Martinez</div>
                  <div className="text-xs text-zinc-400">Waiting 5m</div>
                </div>
                <span className="w-2 h-2 bg-green-500 rounded-full"></span>
              </div>
            </div>
          </div>

          {/* Tasks */}
          <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
            <h3 className="font-bold text-white mb-4">Tasks & Alerts</h3>
            <ul className="space-y-3 text-sm">
              <li className="flex gap-2 items-start">
                <span className="text-yellow-500 mt-0.5">⚠</span>
                <span className="text-zinc-300">Lab results pending review (3)</span>
              </li>
              <li className="flex gap-2 items-start">
                <span className="text-blue-500 mt-0.5">ℹ</span>
                <span className="text-zinc-300">Prescription refill requests (2)</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}