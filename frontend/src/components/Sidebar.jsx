import { NavLink } from 'react-router-dom'

const navItems = [
  { to: '/dashboard', label: 'Command Center', hint: 'Overview & KPIs' },
  { to: '/cad', label: 'CAD Management', hint: 'Call intake & dispatch' },
  { to: '/tracking', label: 'Unit Tracking', hint: 'Live GPS & status' },
  { to: '/epcr', label: 'ePCR', hint: 'Patient care reports' },
  { to: '/scheduling', label: 'Scheduling', hint: 'Coverage & shifts' },
  { to: '/billing', label: 'Billing Ops', hint: 'Claims & reconciliation' },
  { to: '/ai-console', label: 'AI Console', hint: 'Predictions & guidance' },
  { to: '/reporting', label: 'Reporting', hint: 'Compliance & QA' },
  { to: '/founder', label: 'Founder', hint: 'Enterprise controls' },
  { to: '/investor', label: 'Investor', hint: 'Performance snapshot' },
]

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">
          <span className="pulse" />
          <span className="pulse delay" />
        </div>
        <div>
          <p className="brand-title">FusonEMS</p>
          <p className="brand-subtitle">Quantum Platform</p>
        </div>
      </div>
      <nav className="nav">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              isActive ? 'nav-link active' : 'nav-link'
            }
          >
            <div>
              <span className="nav-label">{item.label}</span>
              <span className="nav-hint">{item.hint}</span>
            </div>
          </NavLink>
        ))}
      </nav>
      <div className="sidebar-footer">
        <p className="status-pill">System: Online</p>
        <p className="status-sub">All services healthy</p>
      </div>
    </aside>
  )
}
