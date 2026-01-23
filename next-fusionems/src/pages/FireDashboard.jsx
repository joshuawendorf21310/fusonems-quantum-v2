import SectionHeader from '../components/SectionHeader.jsx'
import StatCard from '../components/StatCard.jsx'
import ChartPanel from '../components/ChartPanel.jsx'

export default function FireDashboard() {
  return (
    <div className="page">
      <SectionHeader
        eyebrow="Fire Command"
        title="Fire-EMS Readiness & Incident Visibility"
        action={<button className="ghost-button">NFIRS Export</button>}
      />

      <div className="grid-3">
        <StatCard label="Active Incidents" value="4" delta="+2" />
        <StatCard label="Apparatus Ready" value="92%" delta="+3%" />
        <StatCard label="Training Gaps" value="2 crews" delta="-1" />
      </div>

      <div className="section-grid">
        <ChartPanel
          title="Fire vs EMS Volume"
          description="Rolling 14-day comparison for hybrid agencies."
          data={[8, 6, 9, 11, 10, 7, 6, 8]}
        />
        <ChartPanel
          title="Readiness Score"
          description="Station readiness score across the last 8 shifts."
          data={[82, 84, 88, 90, 92, 89, 91, 94]}
        />
      </div>
    </div>
  )
}
