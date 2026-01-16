import { NavLink } from 'react-router-dom'
import { useAppData } from '../context/useAppData.js'
import { useAuth } from '../context/useAuth.js'
import { canAccessModule } from '../utils/access.js'

const navItems = [
  { to: '/dashboard', label: 'Command Center', hint: 'Overview & KPIs', moduleKey: 'CAD' },
  { to: '/cad', label: 'CAD Management', hint: 'Call intake & dispatch', moduleKey: 'CAD' },
  { to: '/tracking', label: 'Unit Tracking', hint: 'Live GPS & status', moduleKey: 'CAD' },
  { to: '/epcr', label: 'ePCR', hint: 'Patient care reports', moduleKey: 'EPCR' },
  { to: '/scheduling', label: 'Scheduling', hint: 'Coverage & shifts', moduleKey: 'SCHEDULING' },
  { to: '/billing', label: 'Billing Ops', hint: 'Claims & reconciliation', moduleKey: 'BILLING' },
  { to: '/communications', label: 'Communications', hint: 'Telnyx voice/SMS', moduleKey: 'COMMS' },
  { to: '/communications/voice', label: 'Quantum Voice', hint: 'Softphone + logs', moduleKey: 'COMMS' },
  { to: '/email', label: 'Email Inbox', hint: 'Postmark transport', moduleKey: 'EMAIL' },
  { to: '/qa', label: 'Clinical QA', hint: 'Review + remediation', moduleKey: 'QA' },
  { to: '/training-center', label: 'Training Center', hint: 'Credentials & CE', moduleKey: 'TRAINING' },
  { to: '/narcotics', label: 'Narcotics', hint: 'Chain of custody', moduleKey: 'NARCOTICS' },
  { to: '/medication', label: 'Medication', hint: 'Formulary + admin', moduleKey: 'MEDICATION' },
  { to: '/inventory', label: 'Inventory', hint: 'Rig checks + stock', moduleKey: 'INVENTORY' },
  { to: '/fleet', label: 'Fleet', hint: 'Vehicles + maintenance', moduleKey: 'FLEET' },
  { to: '/founder-ops', label: 'Founder Ops', hint: 'Governance + pricing', moduleKey: 'FOUNDER' },
  { to: '/founder/workspace', label: 'Founder Workspace', hint: 'Docs + Voice', moduleKey: 'FOUNDER' },
  { to: '/founder/workspace/documents', label: 'Workspace Docs', hint: 'Vault oversight', moduleKey: 'FOUNDER' },
  { to: '/founder/workspace/voice', label: 'Workspace Voice', hint: 'Voice governance', moduleKey: 'FOUNDER' },
  { to: '/founder/workspace/holds', label: 'Workspace Holds', hint: 'Global holds', moduleKey: 'FOUNDER' },
  { to: '/founder/workspace/exports', label: 'Workspace Exports', hint: 'Discovery packets', moduleKey: 'FOUNDER' },
  { to: '/founder/governance/retention', label: 'Retention', hint: 'Policy controls', moduleKey: 'FOUNDER' },
  { to: '/legal-portal', label: 'Legal Portal', hint: 'Discovery + evidence', moduleKey: 'LEGAL_PORTAL' },
  { to: '/patient-portal', label: 'Patient Portal', hint: 'Statements + inbox', moduleKey: 'BILLING' },
  { to: '/telehealth', label: 'Telehealth', hint: 'CareFusion video visits', moduleKey: 'TELEHEALTH' },
  { to: '/fire', label: 'Fire Dashboard', hint: 'Command visibility', moduleKey: 'FIRE' },
  { to: '/fire/incidents', label: 'Fire Incidents', hint: 'NFIRS / NERIS', moduleKey: 'FIRE' },
  { to: '/fire/apparatus', label: 'Apparatus', hint: 'Fleet & inventory', moduleKey: 'FIRE' },
  { to: '/fire/personnel', label: 'Personnel', hint: 'Roles & certs', moduleKey: 'FIRE' },
  { to: '/fire/training', label: 'Training', hint: 'Drills & readiness', moduleKey: 'FIRE' },
  { to: '/fire/prevention', label: 'Prevention', hint: 'Inspections', moduleKey: 'FIRE' },
  { to: '/hems', label: 'HEMS Command', hint: 'Air medical ops', moduleKey: 'HEMS' },
  { to: '/hems/missions', label: 'HEMS Missions', hint: 'Mission board', moduleKey: 'HEMS' },
  { to: '/hems/aircraft', label: 'HEMS Aircraft', hint: 'Fleet readiness', moduleKey: 'HEMS' },
  { to: '/hems/crew', label: 'HEMS Crew', hint: 'Duty + fatigue', moduleKey: 'HEMS' },
  { to: '/hems/qa', label: 'HEMS QA', hint: 'Review queue', moduleKey: 'HEMS' },
  { to: '/hems/billing', label: 'HEMS Billing', hint: 'Export packets', moduleKey: 'HEMS' },
  { to: '/repair', label: 'Repair Tooling', hint: 'Orphan recovery', moduleKey: 'REPAIR' },
  { to: '/exports', label: 'Data Exports', hint: 'Exit tooling', moduleKey: 'EXPORTS' },
  { to: '/documents', label: 'Quantum Documents', hint: 'Drive + Vault', moduleKey: 'DOCUMENT_STUDIO' },
  { to: '/document-studio', label: 'Document Studio', hint: 'Templates + outputs', moduleKey: 'DOCUMENT_STUDIO' },
  { to: '/documents/holds', label: 'Doc Holds', hint: 'Legal freezes', moduleKey: 'DOCUMENT_STUDIO' },
  { to: '/documents/exports', label: 'Doc Exports', hint: 'Discovery packets', moduleKey: 'DOCUMENT_STUDIO' },
  { to: '/builders', label: 'Builder Registry', hint: 'Rules & workflows', moduleKey: 'BUILDERS' },
  { to: '/builders/validation', label: 'Validation Builder', hint: 'Rule enforcement', moduleKey: 'BUILDERS' },
  { to: '/search', label: 'Search', hint: 'Discovery engine', moduleKey: 'SEARCH' },
  { to: '/jobs', label: 'Jobs Console', hint: 'Queue orchestration', moduleKey: 'JOBS' },
  { to: '/analytics', label: 'Analytics Core', hint: 'Telemetry + forecasts', moduleKey: 'ANALYTICS' },
  { to: '/feature-flags', label: 'Feature Flags', hint: 'Release gates', moduleKey: 'FEATURE_FLAGS' },
  { to: '/automation', label: 'Automation', hint: 'Validation & compliance', moduleKey: 'AUTOMATION' },
  { to: '/ai-console', label: 'AI Console', hint: 'Predictions & guidance', moduleKey: 'AI_CONSOLE' },
  { to: '/reporting', label: 'Reporting', hint: 'Compliance & QA', moduleKey: 'COMPLIANCE' },
  { to: '/founder', label: 'Founder', hint: 'Enterprise controls', moduleKey: 'FOUNDER' },
  { to: '/investor', label: 'Investor', hint: 'Performance snapshot', moduleKey: 'INVESTOR' },
]

export default function Sidebar() {
  const { modules, systemHealth } = useAppData()
  const { userRole } = useAuth()
  const moduleIndex = modules.reduce((acc, module) => {
    acc[module.module_key] = module
    return acc
  }, {})
  const filteredItems = navItems.filter((item) => {
    if (!item.moduleKey) {
      return true
    }
    const module = moduleIndex[item.moduleKey]
    if (module && (!module.enabled || module.kill_switch)) {
      return false
    }
    return canAccessModule(item.moduleKey, userRole)
  })
  const healthLabel = systemHealth?.status === 'online' ? 'System: Online' : 'System: Degraded'
  const healthDetail = systemHealth?.upgrade?.status === 'PASS' ? 'Upgrade checks passing' : 'Upgrade checks failed'

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
        {filteredItems.map((item) => (
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
        <p className="status-pill">{healthLabel}</p>
        <p className="status-sub">{healthDetail}</p>
      </div>
    </aside>
  )
}
