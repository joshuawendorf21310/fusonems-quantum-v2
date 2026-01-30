"use client"
import Link from "next/link"
import dynamic from "next/dynamic"
import { useState } from "react"

const ComplianceAgentWidget = dynamic(() => import("./ComplianceAgentWidget"), { ssr: false })

export default function ComplianceLanding() {
  const [ruleName, setRuleName] = useState("");
  const [ruleType, setRuleType] = useState("");
  const [color, setColor] = useState("#00FF00"); // Default to green

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
        <section className="panel">
          <header>
            <h3>Validation Rule Builder</h3>
          </header>
          <div className="panel-card">
            <label>
              Rule Name:
              <input type="text" value={ruleName} onChange={e => setRuleName(e.target.value)} />
            </label>
            <label>
              Rule Type:
              <input type="text" value={ruleType} onChange={e => setRuleType(e.target.value)} />
            </label>
            <label>
              Rule Color:
              <input type="color" value={color} onChange={e => setColor(e.target.value)} />
              <input type="text" value={color} onChange={e => setColor(e.target.value)} style={{marginLeft:8}} />
            </label>
            <div style={{marginTop:16}}>
              <span style={{background: color, color: '#fff', padding: '8px 16px', borderRadius: 4}}>
                Preview: {ruleName || "Rule"} ({ruleType || "Type"})
              </span>
            </div>
          </div>
        </section>
        <BillingImportWizard />
      </div>
    </div>
  )
}

function BillingImportWizard() {
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<any[]>([])
  const [mapping, setMapping] = useState<Record<string, string>>({})
  const [progress, setProgress] = useState<number>(0)
  const [status, setStatus] = useState<string>("")

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]
    if (f) {
      setFile(f)
      // TODO: Parse file and set preview
      setPreview([])
      setMapping({})
      setStatus("")
    }
  }

  const handleImport = () => {
    setStatus("Importing...")
    // TODO: Send file and mapping to backend, update progress
    setTimeout(() => {
      setProgress(100)
      setStatus("Import complete!")
    }, 2000)
  }

  return (
    <section className="panel">
      <header>
        <h3>Billing Import Wizard</h3>
      </header>
      <div className="panel-card">
        <input type="file" accept=".csv,.xlsx" onChange={handleFileChange} />
        {file && (
          <div style={{marginTop:16}}>
            <strong>Preview:</strong>
            {/* TODO: Render preview table */}
            <div style={{marginTop:8}}>
              <button onClick={handleImport}>Import</button>
              <span style={{marginLeft:16}}>{status}</span>
              {progress > 0 && <progress value={progress} max={100} style={{marginLeft:8}} />}
            </div>
          </div>
        )}
      </div>
    </section>
  )
}
