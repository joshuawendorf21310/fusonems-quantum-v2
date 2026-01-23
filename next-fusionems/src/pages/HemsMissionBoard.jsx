import { useEffect, useState } from 'react'
import SectionHeader from '../components/SectionHeader.jsx'
import DataTable from '../components/DataTable.jsx'
import AdvisoryPanel from '../components/AdvisoryPanel.jsx'
import { apiFetch } from '../services/api.js'
import { fallbackHemsMissions } from '../data/fallback.js'

const missionColumns = [
  { key: 'id', label: 'Mission ID' },
  { key: 'mission_type', label: 'Type' },
  { key: 'requesting_party', label: 'Requesting' },
  { key: 'pickup_location', label: 'Pickup' },
  { key: 'destination_location', label: 'Destination' },
  { key: 'status', label: 'Status' },
]

export default function HemsMissionBoard() {
  const [missions, setMissions] = useState(fallbackHemsMissions)
  const [isSimulating, setIsSimulating] = useState(false)
  const [resumeWorkflow, setResumeWorkflow] = useState(null)

  const loadMissions = async () => {
    try {
      const data = await apiFetch('/api/hems/missions')
      if (Array.isArray(data) && data.length) {
        setMissions(data)
      }
    } catch (error) {
      console.warn('Unable to load missions, using demo data', error)
    }
  }

  useEffect(() => {
    loadMissions()
    const loadWorkflows = async () => {
      try {
        const data = await apiFetch('/api/workflows?workflow_key=hems_mission_acceptance')
        if (Array.isArray(data)) {
          const interrupted = data.find((item) => item.status === 'interrupted')
          if (interrupted) {
            setResumeWorkflow(interrupted)
          }
        }
      } catch (error) {
        console.warn('Workflow resume unavailable', error)
      }
    }
    loadWorkflows()
  }, [])

  const simulateMission = async () => {
    setIsSimulating(true)
    try {
      await apiFetch('/api/hems/simulate', { method: 'POST', body: '{}' })
      await loadMissions()
    } catch (error) {
      console.warn('Simulation failed', error)
    } finally {
      setIsSimulating(false)
    }
  }

  return (
    <div className="page">
      <SectionHeader
        eyebrow="HEMS Mission Board"
        title="Live Mission Queue"
        action={
          <button className="primary-button" type="button" onClick={simulateMission}>
            {isSimulating ? 'Simulating...' : 'Simulate Mission'}
          </button>
        }
      />

      <div className="hems-board">
        <div className="panel">
          <SectionHeader eyebrow="Active Missions" title="Queue + Filters" />
          <DataTable
            columns={missionColumns}
            rows={missions}
            emptyState="No missions yet. Run a simulation to see the live queue."
          />
        </div>
        <div className="panel">
          <SectionHeader eyebrow="System Alive" title="Live Telemetry" />
          <div className="stack">
            <div className="list-row">
              <div>
                <p className="list-title">Resume Workflow</p>
                <p className="list-sub">
                  {resumeWorkflow
                    ? `Interrupted at ${resumeWorkflow.last_step || 'unknown step'}`
                    : 'No interrupted workflows detected.'}
                </p>
              </div>
              <span className="badge">{resumeWorkflow ? 'Resume' : 'Stable'}</span>
            </div>
            <div className="list-row">
              <div>
                <p className="list-title">Event Bus</p>
                <p className="list-sub">3 events in the last minute</p>
              </div>
              <span className="badge active">Healthy</span>
            </div>
            <div className="list-row">
              <div>
                <p className="list-title">CrewLink Sync</p>
                <p className="list-sub">2 devices connected</p>
              </div>
              <span className="badge">Live</span>
            </div>
            <AdvisoryPanel
              title="AI Launch Advisory"
              model="quantum-ai"
              version="1.0"
              level="ADVISORY"
              message="Night ops permitted. Weather risk low. Recommend dispatching AW-12."
              reason="Risk assessment computed from weather + crew readiness."
            />
          </div>
        </div>
      </div>
    </div>
  )
}
