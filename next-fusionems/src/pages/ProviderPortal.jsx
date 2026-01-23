import { Link } from 'react-router-dom'

const portals = [
  {
    title: 'Field Provider',
    subtitle: 'EMS / Fire / Transport',
    description: [
      'ePCR Documentation',
      'Unit & Crew Status',
      'Dispatch / Response Updates',
      'Medication & Controlled Substance Logging',
      'Agency Credential Enforcement',
    ],
    cta: 'Continue to Field Provider Login',
    className: 'portal-card orange',
    icon: '🚑',
    link: '/login?portal=field',
  },
  {
    title: 'Clinical Provider',
    subtitle: 'FusionCare',
    description: [
      'Virtual Visits',
      'Clinical Documentation',
      'Scheduling',
      'Prescribing (if enabled)',
      'Patient Panels',
    ],
    cta: 'Continue to FusionCare Provider Login',
    className: 'portal-card blue',
    icon: '🩺',
    link: '/login?portal=clinical',
  },
]

export default function ProviderPortal() {
  return (
    <div className="landing-shell">
      <div className="provider-hero">
        <img src="/brand/fusionems-quantum.png" alt="FusionEMS Quantum" />
        <div>
          <p className="eyebrow">Provider Portal</p>
          <h1>Choose Your Provider Environment</h1>
          <p className="hero-text">
            Access is controlled by your organization and secure credentials. Select the portal that
            matches your role—each stream is audited and governed by your agency policies.
          </p>
        </div>
        <Link className="ghost-button" to="/">
          ← Back to Home
        </Link>
      </div>
      <div className="provider-grid">
        {portals.map((portal) => (
          <article key={portal.title} className={portal.className}>
            <div className="portal-icon">{portal.icon}</div>
            <h3>{portal.title}</h3>
            <p className="portal-sub">{portal.subtitle}</p>
            <ul>
              {portal.description.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
            <Link className="portal-cta" to={portal.link}>
              {portal.cta}
            </Link>
          </article>
        ))}
      </div>
    </div>
  )
}
