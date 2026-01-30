import Link from "next/link"

export default function CJISCompliance() {
  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white">
      <div className="mx-auto max-w-2xl py-16 px-6">
        <h1 className="text-3xl font-bold mb-6">CJIS & State EMS Compliance</h1>
        <p className="mb-6 text-white/80">This page provides public documentation of CJIS (Criminal Justice Information Services) and State EMS compliance, including criminal justice and state EMS documentation. For internal dashboards and audit logs, see the Founder Portal.</p>
        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-2">Criminal Justice Compliance</h2>
          <p className="text-white/70">All criminal justice data is handled in accordance with CJIS standards. Access is strictly controlled and logged.</p>
        </div>
        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-2">State EMS Compliance</h2>
          <p className="text-white/70">State EMS requirements are met or exceeded, with documentation and audit logs available for review.</p>
        </div>
        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-2">Procurement & Regulatory Documentation</h2>
          <p className="text-white/70">Procurement-safe documentation and compliance attestations are available upon request.</p>
        </div>
        <div className="mt-12 text-center">
          <Link href="/compliance" className="text-[#B86B1E] hover:underline">Back to Compliance Center</Link>
        </div>
      </div>
    </div>
  )
}
