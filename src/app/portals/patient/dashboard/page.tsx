import Link from 'next/link'

export default function PatientDashboard() {
  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 p-6">
      <header className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-white">Patient Portal</h1>
          <p className="text-zinc-400">Welcome back, John Doe</p>
        </div>
        <div className="flex gap-4">
           <Link href="/portals/patient/profile" className="px-4 py-2 bg-zinc-800 rounded hover:bg-zinc-700 transition">Profile</Link>
           <Link href="/api/auth/logout" className="px-4 py-2 bg-red-900/20 text-red-400 rounded hover:bg-red-900/30 transition">Sign Out</Link>
        </div>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        {/* Balance Card */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
          <h3 className="text-zinc-400 text-sm font-medium uppercase tracking-wider mb-2">Current Balance</h3>
          <div className="text-3xl font-bold text-white mb-4">$450.00</div>
          <p className="text-zinc-500 text-sm mb-6">Due by Feb 15, 2026</p>
          <Link href="/portals/patient/bills" className="block w-full text-center py-2 bg-[#FF6B35] text-white font-bold rounded hover:bg-[#e55a2b] transition">
            Pay Bill Now
          </Link>
        </div>

        {/* Recent Activity */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
          <h3 className="text-zinc-400 text-sm font-medium uppercase tracking-wider mb-2">Recent Activity</h3>
          <ul className="space-y-3">
            <li className="flex justify-between text-sm">
              <span className="text-zinc-300">Transport to General Hospital</span>
              <span className="text-zinc-500">Jan 28</span>
            </li>
            <li className="flex justify-between text-sm">
              <span className="text-zinc-300">Payment Processed</span>
              <span className="text-green-500">-$150.00</span>
            </li>
            <li className="flex justify-between text-sm">
              <span className="text-zinc-300">Statement Generated</span>
              <span className="text-zinc-500">Jan 15</span>
            </li>
          </ul>
        </div>

        {/* Quick Actions */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
          <h3 className="text-zinc-400 text-sm font-medium uppercase tracking-wider mb-2">Quick Actions</h3>
          <div className="space-y-2">
            <Link href="/portals/patient/records" className="block w-full text-left px-4 py-3 bg-zinc-800 rounded hover:bg-zinc-700 transition text-sm">
              Request Medical Records
            </Link>
            <Link href="/portals/patient/insurance" className="block w-full text-left px-4 py-3 bg-zinc-800 rounded hover:bg-zinc-700 transition text-sm">
              Update Insurance Info
            </Link>
            <Link href="/portals/patient/messages" className="block w-full text-left px-4 py-3 bg-zinc-800 rounded hover:bg-zinc-700 transition text-sm">
              Contact Billing Support
            </Link>
          </div>
        </div>
      </div>

      {/* Recent Transports Table */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-lg overflow-hidden">
        <div className="px-6 py-4 border-b border-zinc-800">
          <h3 className="font-bold text-white">Recent Transports</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="bg-zinc-950 text-zinc-400 uppercase">
              <tr>
                <th className="px-6 py-3">Date</th>
                <th className="px-6 py-3">Incident #</th>
                <th className="px-6 py-3">Destination</th>
                <th className="px-6 py-3">Status</th>
                <th className="px-6 py-3">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800">
              <tr className="hover:bg-zinc-800/50">
                <td className="px-6 py-4">Jan 28, 2026</td>
                <td className="px-6 py-4 font-mono">INC-2026-001</td>
                <td className="px-6 py-4">Memorial General</td>
                <td className="px-6 py-4"><span className="px-2 py-1 rounded-full bg-yellow-900/30 text-yellow-400 text-xs">Pending Insurance</span></td>
                <td className="px-6 py-4"><Link href="/portals/patient/transports/1" className="text-[#FF6B35] hover:underline">View Details</Link></td>
              </tr>
              <tr className="hover:bg-zinc-800/50">
                <td className="px-6 py-4">Dec 12, 2025</td>
                <td className="px-6 py-4 font-mono">INC-2025-892</td>
                <td className="px-6 py-4">City Medical Center</td>
                <td className="px-6 py-4"><span className="px-2 py-1 rounded-full bg-green-900/30 text-green-400 text-xs">Paid in Full</span></td>
                <td className="px-6 py-4"><Link href="/portals/patient/transports/2" className="text-[#FF6B35] hover:underline">View Details</Link></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}