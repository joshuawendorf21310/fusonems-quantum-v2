"use client"
import Link from "next/link"
import dynamic from "next/dynamic"

const ComplianceAgentWidget = dynamic(() => import("./ComplianceAgentWidget"), { ssr: false })

export default function ComplianceLanding() {
  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white">
      <div className="mx-auto max-w-3xl py-16 px-6">
        <h1 className="text-3xl font-bold mb-6">Compliance & Regulatory Center</h1>
        <p className="mb-8 text-white/80">
          This platform is designed to meet and exceed the requirements of CMS, DEA, HIPAA, CJIS, and State EMS regulatory frameworks. All compliance dashboards, audit logs, and agent actions are tracked and available for review. For procurement and regulatory documentation, see the sections below.
        </p>
        <div className="grid gap-6 md:grid-cols-2">
          <Link href="/compliance/cms" className="block rounded-lg border border-white/10 bg-white/5 p-6 hover:bg-white/10 transition">
            <h2 className="text-xl font-semibold mb-2">CMS Compliance</h2>
            <p className="text-white/70">Medicare/Medicaid enrollment, audit logs, and metadata tracking.</p>
          </Link>
          <Link href="/compliance/dea" className="block rounded-lg border border-white/10 bg-white/5 p-6 hover:bg-white/10 transition">
            <h2 className="text-xl font-semibold mb-2">DEA Compliance</h2>
            <p className="text-white/70">Controlled substance registration, expiration, and audit logs.</p>
          </Link>
          <Link href="/compliance/hipaa" className="block rounded-lg border border-white/10 bg-white/5 p-6 hover:bg-white/10 transition">
            <h2 className="text-xl font-semibold mb-2">HIPAA & Privacy</h2>
            <p className="text-white/70">Patient privacy, access controls, and auditability.</p>
          </Link>
          <Link href="/compliance/cjis" className="block rounded-lg border border-white/10 bg-white/5 p-6 hover:bg-white/10 transition">
            <h2 className="text-xl font-semibold mb-2">CJIS & State EMS</h2>
            <p className="text-white/70">Criminal justice and state EMS compliance documentation.</p>
          </Link>
          <Link href="/compliance/baa" className="block rounded-lg border border-white/10 bg-white/5 p-6 hover:bg-white/10 transition">
            <h2 className="text-xl font-semibold mb-2">Business Associate Agreements (BAA)</h2>
            <p className="text-white/70">Vendor BAA tracking and HIPAA breach notification workflow.</p>
          </Link>
        </div>
        <ComplianceAgentWidget />
        <div className="mt-12 text-center">
          <Link href="/" className="text-orange-400 hover:underline">Return to Homepage</Link>
        </div>
      </div>
    </div>
  )
}
