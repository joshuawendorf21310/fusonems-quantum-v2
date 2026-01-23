import { Link } from 'react-router-dom'

export default function Landing() {
  return (
    <div className="landing-shell">
      <main className="landing">
        <section className="command-hero">
          <div className="hero-logo">
            <img src="/brand/fusionems-quantum.png" alt="FusionEMS Quantum" />
          </div>
          <div className="hero-copy">
            <p className="eyebrow">FusionEMS Quantum Platform</p>
            <h1>Command Gate</h1>
            <p className="hero-text">
              FusionEMS Quantum orchestrates mission-ready EMS, Fire-EMS, HEMS, and telehealth
              operations from a decisive access surface. No dashboards, just guarded entry to the
              command layer.
            </p>
            <div className="landing-actions">
              <Link className="primary-button" to="/login">
                Sign In to Command
              </Link>
              <Link className="ghost-button" to="/register">
                Deploy Agency
              </Link>
              <Link className="ghost-button" to="/provider-portal">
                Provider Portal
              </Link>
            </div>
          </div>
        </section>

        <section className="positioning">
          <div>
            <h2>Decisive Command</h2>
            <p>
              Built for mission leadership—dispatch, crew, compliance, and finance converge inside a
              single authority with AI-assisted oversight.
            </p>
          </div>
          <div>
            <h2>For Trusted Operators</h2>
            <p>
              Agencies, fire districts, and hospital-integrated systems rely on FusionEMS Quantum for
              secure orchestration, ironclad auditing, and real-time readiness.
            </p>
          </div>
        </section>

        <section className="authority">
          <div>
            <p className="eyebrow">Authority & Compliance</p>
            <h3>Security & Oversight</h3>
            <p>
              End-to-end encryption, role-aware access, and full audit trails keep every mission
              record court-ready. When the gate opens, every action is documented.
            </p>
          </div>
          <div className="authority-list">
            <div>
              <p>HIPAA / NFIRS / NEMSIS alignment</p>
            </div>
            <div>
              <p>Telnyx + Postmark + Office Ally wired</p>
            </div>
            <div>
              <p>Founder control plane & legal hold vault</p>
            </div>
          </div>
        </section>
      </main>
    </div>
  )
}
