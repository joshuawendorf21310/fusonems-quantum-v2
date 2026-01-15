import SectionHeader from '../components/SectionHeader.jsx'
import ChartPanel from '../components/ChartPanel.jsx'

export default function Reporting() {
  return (
    <div className="page">
      <SectionHeader
        eyebrow="Reporting"
        title="Compliance, QA, and Performance Analytics"
        action={<button className="ghost-button">Export Reports</button>}
      />

      <div className="section-grid">
        <ChartPanel
          title="ePCR Completeness"
          description="Documentation completeness over the last 14 days."
          data={[9, 8, 8, 10, 11, 12, 12, 11]}
        />
        <ChartPanel
          title="Response Time"
          description="Average response time by shift."
          data={[7, 6, 5, 6, 8, 7, 6, 5]}
        />
      </div>

      <div className="panel">
        <SectionHeader eyebrow="Audit" title="Regulatory Readiness" />
        <ul className="checklist">
          <li>HIPAA audit trail maintained for 100% of ePCR submissions.</li>
          <li>Clinical QA review queue: 12 charts pending.</li>
          <li>PCI and SOC2 controls aligned with billing workflows.</li>
        </ul>
      </div>
    </div>
  )
}
