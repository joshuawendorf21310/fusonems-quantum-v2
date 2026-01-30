import Link from 'next/link'

export default function PatientBills() {
  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 p-6">
      <header className="mb-8">
        <Link href="/portals/patient/dashboard" className="text-zinc-400 hover:text-white mb-4 inline-block">← Back to Dashboard</Link>
        <h1 className="text-2xl font-bold text-white">My Bills</h1>
      </header>
      <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-8 text-center">
        <h2 className="text-xl font-bold mb-4">Payment System</h2>
        <p className="text-zinc-400 mb-6">Secure payment processing is being initialized.</p>
        <button className="px-6 py-3 bg-[#FF6B35] text-white font-bold rounded hover:bg-[#e55a2b] transition">
          Make a Payment
        </button>
      </div>
    </div>
  )
}
