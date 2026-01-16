import SectionHeader from '../components/SectionHeader.jsx'
import AdvisoryPanel from '../components/AdvisoryPanel.jsx'
import StatCard from '../components/StatCard.jsx'
import { fallbackDocumentExports, fallbackVoiceNumbers } from '../data/fallback.js'

export default function FounderWorkspace() {
  return (
    <div className="page">
      <SectionHeader eyebrow="Founder Workspace" title="Quantum Documents + Voice" />
      <div className="grid-3">
        <StatCard label="Docs Vault" value="Awaiting telemetry" delta="Connect storage" />
        <StatCard label="Voice Lines" value={`${fallbackVoiceNumbers.length}`} delta="Configured numbers" />
        <StatCard label="Discovery Exports" value={`${fallbackDocumentExports.length}`} delta="Export history" />
      </div>
      <div className="panel">
        <AdvisoryPanel
          title="Workspace Guardrails"
          model="governance-core"
          version="2.1"
          level="ADVISORY"
          message="Retention policies and legal holds are enforced on every export and recording."
          reason="Founder governance"
        />
      </div>
    </div>
  )
}
