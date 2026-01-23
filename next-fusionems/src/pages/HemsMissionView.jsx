import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import SectionHeader from '../components/SectionHeader.jsx'
import AdvisoryPanel from '../components/AdvisoryPanel.jsx'
import LegalHoldBanner from '../components/LegalHoldBanner.jsx'
import { apiFetch } from '../services/api.js'

const statusSteps = [
  'accepted',
  'lifted',
  'patient_contact',
  'depart_scene',
  'enroute_dest',
  'landed',
  'complete',
]

export default function HemsMissionView() {
  const { missionId } = useParams()
  const [mission, setMission] = useState(null)
  const [status, setStatus] = useState('accepted')
  const [notes, setNotes] = useState('')

  const loadMission = async () => {
    try {
      const data = await apiFetch(`/api/hems/missions/${missionId}`)
      setMission(data)
      setStatus(data.status || 'accepted')
    } catch (error) {
      console.warn('Unable to load mission', error)
    }
  }

  useEffect(() => {
    if (missionId) {
      loadMission()
    }
  }, [missionId])

  const updateStatus = async () => {
    try {
      await apiFetch(`/api/hems/missions/${missionId}/status`, {
        method: 'POST',
        body: JSON.stringify({ status, notes }),
      })
      setNotes('')
      await loadMission()
    } catch (error) {
      console.warn('Unable to update status', error)
    }
  }

  return (
    <div className="page">
      <SectionHeader
        eyebrow="Mission Command"
        title={`Mission ${mission?.id || missionId}`}
        action={<button className="ghost-button">Open CrewLink</button>}
      />
      <LegalHoldBanner scopeType="hems_mission" scopeId={mission?.id || missionId} />

      <div className="section-grid">
        <div className="panel">
          <SectionHeader eyebrow="Status" title="Timeline Control" />
          <div className="stack">
            <label>Status</label>
            <select value={status} onChange={(event) => setStatus(event.target.value)}>
              {statusSteps.map((step) => (
                <option key={step} value={step}>
                  {step.replace('_', ' ')}
                </option>
              ))}
            </select>
            <label>Notes</label>
            <textarea
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              placeholder="Add flight notes or crew updates"
            />
            <button className="primary-button" type="button" onClick={updateStatus}>
              Update Status
            </button>
          </div>
        </div>
        <div className="panel">
          <SectionHeader eyebrow="Risk + Intelligence" title="Advisory" />
          <AdvisoryPanel
            title="Launch Advisory"
            model="quantum-ai"
            version="1.0"
            level="ADVISORY"
            message="Moderate terrain risk. NVG approved. Crew fatigue within limits."
            reason="HEMS risk model evaluated weather + duty time inputs."
          />
          <div className="note-card">
            <p className="note-title">Mission Summary</p>
            <p className="note-body">
              {mission
                ? `${mission.pickup_location} → ${mission.destination_location}`
                : 'Awaiting live data. Simulator data will populate automatically.'}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
