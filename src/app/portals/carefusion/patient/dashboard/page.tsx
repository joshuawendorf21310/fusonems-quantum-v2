"use client"

export default function CareFusionPatientDashboard() {
  return (
    <div className="min-h-screen bg-zinc-950 text-white p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-4xl font-bold mb-8 bg-gradient-to-r from-cyan-500 to-blue-500 bg-clip-text text-transparent">
          CareFusion Patient Dashboard
        </h1>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
            <h2 className="text-xl font-semibold mb-4">Virtual Consultations</h2>
            <p className="text-gray-400">Schedule and join telehealth appointments</p>
          </div>
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
            <h2 className="text-xl font-semibold mb-4">Medical Records</h2>
            <p className="text-gray-400">Access your complete health history</p>
          </div>
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
            <h2 className="text-xl font-semibold mb-4">Billing & Payments</h2>
            <p className="text-gray-400">Manage healthcare expenses</p>
          </div>
        </div>
      </div>
    </div>
  )
}
