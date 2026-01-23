import { useEffect, useState } from 'react'
import SectionHeader from '../components/SectionHeader.jsx'
import StatCard from '../components/StatCard.jsx'
import ChartPanel from '../components/ChartPanel.jsx'
import DataTable from '../components/DataTable.jsx'
import AdvisoryPanel from '../components/AdvisoryPanel.jsx'
import { apiFetch } from '../services/api.js'
import { fallbackHemsMissions } from '../data/fallback.js'

const missionColumns = [
  { key: 'id', label: 'Mission ID' },
  { key: 'mission_type', label: 'Type' },
  { key: 'requesting_party', label: 'Requesting' },
  { key: 'status', label: 'Status' },
]

export default function HemsDashboard() {
  const [dashboard, setDashboard] = useState(null)
  const [missions, setMissions] = useState(fallbackHemsMissions)

  useEffect(() => {
    const load = async () => {
      try {
        const [dashboardData, missionData] = await Promise.all([
          apiFetch('/api/hems/dashboard'),
          apiFetch('/api/hems/missions'),
        ])
        if (dashboardData) setDashboard(dashboardData)
        if (Array.isArray(missionData) && missionData.length) {
          setMissions(missionData)
        }
      } catch (error) {
        console.warn('HEMS dashboard unavailable, using demo data', error)
      }
    }
    load()
  }, [])

  return (
    <div className="page">
      <SectionHeader
        eyebrow="HEMS Command"
        title="Air Medical Mission Readiness"
        action={<button className="ghost-button">Launch Simulator</button>}
      />

      <div className="grid-3">
        <StatCard
          label="Active Missions"
          value={dashboard?.active_missions ?? '2'}
          delta="+1"
        />
        <StatCard
          label="Ready Aircraft"
          value={dashboard?.ready_aircraft ?? '3'}
          delta="+0"
        />
        <StatCard
          label="Crew Ready"
          value={dashboard?.crew_ready ?? '92%'}
          delta="+4%"
        />
      </div>

      <div className="section-grid">
        <ChartPanel
          title="Mission Tempo"
          description="Live load across bases in the last 8 hours."
          data={[3, 5, 4, 6, 7, 5, 4, 6]}
        />
        <AdvisoryPanel
          title="AI Flight Advisory"
          model="quantum-ai"
          version="1.0"
          level="ADVISORY"
          message={
            dashboard?.weather_risk
              ? `Weather impact: ${dashboard.weather_risk}.`
              : 'Moderate weather risk near Base 2. NVG operations recommended.'
          }
          reason="Weather overlays + NVG policy rules."
        />
      </div>

      <div className="panel">
        <SectionHeader eyebrow="Mission Board" title="Active + Recent Missions" />
        <DataTable
          columns={missionColumns}
          rows={missions}
          emptyState="No missions yet. Start a simulation to populate the board."
        />
      </div>
    </div>
  )
}
