import Link from "next/link"

export default function HIPAACompliance() {
  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white">
      <div className="mx-auto max-w-2xl py-16 px-6">
        <h1 className="text-3xl font-bold mb-6">HIPAA & Privacy Compliance</h1>
        <p className="mb-6 text-white/80">This page provides public documentation of HIPAA (Health Insurance Portability and Accountability Act) and privacy compliance, including patient privacy, access controls, and auditability. For internal dashboards and audit logs, see the Founder Portal.</p>
        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-2">Patient Privacy</h2>
          <p className="text-white/70">All patient data is protected in accordance with HIPAA and state privacy laws. Access is strictly role-based and logged.</p>
        </div>
        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-2">Access Controls</h2>
          <p className="text-white/70">Role-based access control (RBAC) is enforced across all systems. All access and actions are logged and auditable.</p>
        </div>
        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-2">Auditability</h2>
          <p className="text-white/70">All actions on protected health information (PHI) are logged immutably and reviewed for compliance.</p>
        </div>
        <div className="mt-12 flex flex-wrap gap-4 justify-center">
          <Link href="/compliance/baa" className="text-orange-400 hover:underline">BAA & Vendors</Link>
          <Link href="/compliance" className="text-orange-400 hover:underline">Back to Compliance Center</Link>
        </div>
      </div>
    </div>
  )
}
