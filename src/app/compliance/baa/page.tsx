import Link from "next/link"

const VENDORS = [
  { vendor: "Stripe", service: "Payment processing", status: "Obtain / Signed", notes: "Payments may touch PHI identifiers; use Stripe BAA." },
  { vendor: "Telnyx", service: "Voice, SMS, fax", status: "Obtain / Signed", notes: "Call/SMS may contain PHI; require BAA." },
  { vendor: "Postmark", service: "Transactional email", status: "Obtain / Signed", notes: "If used for patient-facing email." },
  { vendor: "Metriport", service: "Patient information (FHIR)", status: "Obtain / Signed", notes: "Patient info source; BAA required." },
  { vendor: "DigitalOcean (Spaces)", service: "Object storage", status: "Obtain / Signed", notes: "File storage for PHI; check DO BAA availability." },
  { vendor: "Lob", service: "Mail / print", status: "Obtain / Signed", notes: "If patient statements mailed." },
]

export default function BAACompliance() {
  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white">
      <div className="mx-auto max-w-4xl py-16 px-6">
        <h1 className="text-3xl font-bold mb-6">Business Associate Agreements (BAA)</h1>
        <p className="mb-6 text-white/80">
          Under HIPAA, we maintain signed Business Associate Agreements with vendors that create, receive, maintain, or transmit Protected Health Information (PHI) on our behalf.
        </p>
        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-3">Vendors requiring BAA — status</h2>
          <div className="overflow-x-auto rounded-lg border border-white/10">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-white/10 bg-white/5">
                  <th className="px-4 py-3 text-white/90 font-medium">Vendor</th>
                  <th className="px-4 py-3 text-white/90 font-medium">Service</th>
                  <th className="px-4 py-3 text-white/90 font-medium">BAA status</th>
                  <th className="px-4 py-3 text-white/90 font-medium">Notes</th>
                </tr>
              </thead>
              <tbody>
                {VENDORS.map((row) => (
                  <tr key={row.vendor} className="border-b border-white/5 hover:bg-white/5">
                    <td className="px-4 py-3 text-white/90">{row.vendor}</td>
                    <td className="px-4 py-3 text-white/70">{row.service}</td>
                    <td className="px-4 py-3 text-orange-400">{row.status}</td>
                    <td className="px-4 py-3 text-white/60 text-sm">{row.notes}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-2">Tracking & renewal</h2>
          <p className="text-white/70">
            BAAs are requested before processing PHI, stored securely, and reviewed when adding new integrations. For internal BAA status, renewal dates, and audit logs, see the Founder Compliance dashboard.
          </p>
        </div>
        <div className="mt-12 flex flex-wrap gap-4">
          <Link href="/compliance/hipaa" className="text-orange-400 hover:text-orange-300 transition hover:underline">HIPAA & Privacy</Link>
          <Link href="/compliance" className="text-orange-400 hover:text-orange-300 transition hover:underline">Compliance Center</Link>
          <Link href="/founder" className="text-orange-400 hover:text-orange-300 transition hover:underline">Founder Dashboard</Link>
          <Link href="/" className="text-orange-400 hover:text-orange-300 transition hover:underline">Homepage</Link>
        </div>
      </div>
    </div>
  )
}
