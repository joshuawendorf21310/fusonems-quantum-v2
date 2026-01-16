import SectionHeader from '../components/SectionHeader.jsx'
import DataTable from '../components/DataTable.jsx'
import AdvisoryPanel from '../components/AdvisoryPanel.jsx'
import { fallbackLegalCases, fallbackLegalEvidence } from '../data/fallback.js'

const caseColumns = [
  { key: 'case_number', label: 'Case' },
  { key: 'status', label: 'Status' },
  { key: 'summary', label: 'Summary' },
]

const evidenceColumns = [
  { key: 'case_id', label: 'Case' },
  { key: 'evidence_type', label: 'Type' },
  { key: 'status', label: 'Status' },
]

export default function LegalPortal() {
  return (
    <div className="page">
      <SectionHeader
        eyebrow="Legal Portal"
        title="Discovery + Evidence Management"
        action={<button className="primary-button">Create Case</button>}
      />

      <div className="section-grid">
        <div className="panel">
          <SectionHeader eyebrow="Cases" title="Active Legal Cases" />
          <DataTable columns={caseColumns} rows={fallbackLegalCases} emptyState="No cases." />
        </div>
        <div className="panel">
          <AdvisoryPanel
            title="Discovery Readiness"
            model="legal-guard"
            version="1.1"
            level="ADVISORY"
            message="Legal hold enforcement active on 2 incidents."
            reason="Legal hold engine + export locks"
          />
          <div className="note-card">
            <p className="note-title">Evidence Chain</p>
            <p className="note-body">All evidence packets are hash-stamped and immutable.</p>
          </div>
        </div>
      </div>

      <div className="panel">
        <SectionHeader eyebrow="Evidence" title="Case Evidence" />
        <DataTable columns={evidenceColumns} rows={fallbackLegalEvidence} emptyState="No evidence." />
      </div>
    </div>
  )
}
