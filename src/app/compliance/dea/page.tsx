import Link from "next/link"

export default function DEACompliance() {
  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white">
      <div className="mx-auto max-w-2xl py-16 px-6">
        <h1 className="text-3xl font-bold mb-6">DEA Compliance</h1>
        <p className="mb-6 text-white/80">This page provides public documentation of DEA (Drug Enforcement Administration) compliance, including controlled substance registration, expiration, and audit logging. For internal dashboards and audit logs, see the Founder Portal.</p>
        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-2">Controlled Substance Registration</h2>
          <p className="text-white/70">All DEA registrations are tracked, with expiration and schedule authorizations monitored. Audit logs are maintained for all changes and verifications. For detailed status, contact compliance@fusionems.com.</p>
        </div>
        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-2">Audit Logging</h2>
          <p className="text-white/70">All actions related to DEA data are logged immutably and reviewed regularly for compliance.</p>
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
