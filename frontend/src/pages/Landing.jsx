import { Link } from 'react-router-dom'
import { useEffect, useMemo, useState } from 'react'

const systemEvents = [
  {
    title: 'AI Narrative Generated',
    detail: 'Ventilation decision packet flagged for review.',
    severity: 'orange',
  },
  {
    title: 'Unit Status Updated',
    detail: 'Medic Delta 3 enroute with green lights.',
    severity: 'info',
  },
  {
    title: 'NEMSIS Validation Passed',
    detail: 'Patient encounter 81245 verified, compliance green.',
    severity: 'info',
  },
  {
    title: 'Compliance Check Completed',
    detail: 'Retention holds reconciled for LegalOrg.',
    severity: 'orange',
  },
  {
    title: 'Risk Radar',
    detail: 'Anomalous vitals stream detected; awaiting override.',
    severity: 'red',
  },
  {
    title: 'Camera Feed Synced',
    detail: 'Quad-copter payload 01 integrated with dispatch LOS.',
    severity: 'info',
  },
]

export default function Landing() {
  const [tick, setTick] = useState(0)
  useEffect(() => {
    const interval = setInterval(() => {
      setTick((prev) => (prev + 1) % systemEvents.length)
    }, 3200)
    return () => clearInterval(interval)
  }, [])

  const activeEvents = useMemo(() => {
    return Array.from({ length: 4 }, (_, idx) => {
      return systemEvents[(tick + idx) % systemEvents.length]
    })
  }, [tick])

  return (
    <div className="landing">
      <nav className="landing-nav">
        <div className="nav-brand">
          <img
            src="/brand/fusionems-quantum.png"
            alt="FusionEMS Quantum"
            className="nav-logo"
          />
          <div>
            <p className="nav-title">Quantum Console</p>
            <p className="nav-sub">Operational Command / Restricted</p>
          </div>
        </div>
        <div className="nav-indicators">
          <div className="nav-indicator">
            <span className="nav-dot" />
            <p>Secure Link</p>
            <small>Encrypted</small>
          </div>
          <div className="nav-indicator">
            <span className="nav-dot orange" />
            <p>Command Mesh</p>
            <small>Latency 42ms</small>
          </div>
          <div className="nav-indicator">
            <span className="nav-dot red" />
            <p>Risk Radar</p>
            <small>1 Alert</small>
          </div>
        </div>
        <div className="nav-access">
          <span className="nav-gate">Access System</span>
        </div>
      </nav>

      <section className="landing-hero">
        <div className="hero-left">
          <p className="eyebrow">FusionEMS Quantum Engine</p>
          <h1>Operational AI Command Console</h1>
          <p className="hero-text">
            Authoritative visuals, live telemetry, and compliance guardianship align into a single
            entry surface. This is the state before every mission recruits a human crew.
          </p>
          <p className="hero-sub">
            Unified EMS, Fire-EMS, HEMS, and Compliance Command under one watchful console.
          </p>
          <div className="landing-actions">
            <Link className="primary-button" to="/login">
              Sign In to Command
            </Link>
            <Link className="ghost-button" to="/register">
              Activate Agency
            </Link>
          </div>
        </div>
        <div className="hero-center">
          <div className="signal-grid">
            <div className="grid-layer" />
            <div className="grid-layer secondary" />
          </div>
          <div className="signal-center">
            <p>Pulse</p>
            <span />
          </div>
          <div className="signal-overlay">
            <p>Topology stream</p>
            <p>Procedural watch</p>
          </div>
        </div>
        <div className="hero-right">
          <div className="status-alive">
            <span className="status-pill orange">System Alive</span>
            <p className="status-alive-note">Command mesh locked</p>
          </div>
          <div className="status-header">
            <p>System Status</p>
            <span>Command Console</span>
          </div>
          <div className="status-row">
            <div>
              <p className="status-label">Environment</p>
              <p>EDGE / PRODUCTION</p>
            </div>
            <p className="status-time">14:45:12Z</p>
          </div>
          <div className="status-row">
            <div>
              <p className="status-label">Version</p>
              <p>v3.0.18-quantum</p>
            </div>
            <div className="status-pill orange">Live</div>
          </div>
          <div className="status-row">
            <div>
              <p className="status-label">Audit Clock</p>
              <p>Completed 4m ago</p>
            </div>
            <div className="status-pill red">Risk</div>
          </div>
          <div className="status-row compact">
            <p className="status-label">Guidance</p>
            <p>Signals bridging dispatch, compliance, flight ops.</p>
          </div>
        </div>
      </section>

      <section className="landing-events">
        <div className="events-header">
          <div>
            <p className="eyebrow">Live Activity Stream</p>
            <h3>Pulse of Quantum Operations</h3>
          </div>
          <p className="events-timestamp">Updated — {new Date().toISOString().split('T')[1].split('.')[0]} UTC</p>
        </div>
        <div className="events-list">
          {activeEvents.map((event) => (
            <article key={event.title + event.detail} className={`event-card ${event.severity}`}>
              <div className="event-head">
                <span className="event-dot" />
                <p>{event.title}</p>
              </div>
              <p className="event-detail">{event.detail}</p>
            </article>
          ))}
        </div>
      </section>
    </div>
  )
}
