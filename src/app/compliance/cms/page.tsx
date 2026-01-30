import Link from "next/link"

export default function CMSCompliance() {
  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white">
      <div className="mx-auto max-w-2xl py-16 px-6">
        <h1 className="text-3xl font-bold mb-6">CMS Compliance</h1>
        <p className="mb-6 text-white/80">This page provides public documentation of CMS (Centers for Medicare & Medicaid Services) compliance, including enrollment, audit logging, and metadata tracking. For internal dashboards and audit logs, see the Founder Portal.</p>
        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-2">Medicare/Medicaid Enrollment</h2>
          <p className="text-white/70">All provider enrollments are tracked and verified. Audit logs are maintained for all changes and verifications. For detailed enrollment status, contact compliance@fusionems.com.</p>
        </div>
        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-2">Audit Logging</h2>
          <p className="text-white/70">All actions related to CMS data are logged immutably and reviewed regularly for compliance.</p>
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
