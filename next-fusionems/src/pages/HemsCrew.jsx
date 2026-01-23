import { useEffect, useState } from 'react'
import SectionHeader from '../components/SectionHeader.jsx'
import DataTable from '../components/DataTable.jsx'
import AdvisoryPanel from '../components/AdvisoryPanel.jsx'
import { apiFetch } from '../services/api.js'
import { fallbackHemsCrew } from '../data/fallback.js'

const crewColumns = [
  { key: 'full_name', label: 'Crew Member' },
  { key: 'role', label: 'Role' },
  { key: 'duty_status', label: 'Duty Status' },
]

export default function HemsCrew() {
  const [crew, setCrew] = useState(fallbackHemsCrew)
  const [formState, setFormState] = useState({
    full_name: '',
    role: 'pilot',
    duty_status: 'Ready',
  })

  const loadCrew = async () => {
    try {
      const data = await apiFetch('/api/hems/crew')
      if (Array.isArray(data) && data.length) {
        setCrew(data)
      }
    } catch (error) {
      console.warn('Unable to load crew', error)
    }
  }

  useEffect(() => {
    loadCrew()
  }, [])

  const handleChange = (event) => {
    const { name, value } = event.target
    setFormState((prev) => ({ ...prev, [name]: value }))
  }

  const addCrew = async (event) => {
    event.preventDefault()
    try {
      await apiFetch('/api/hems/crew', {
        method: 'POST',
        body: JSON.stringify({
          full_name: formState.full_name,
          role: formState.role,
          duty_status: formState.duty_status,
          readiness_flags: { fatigue: 'low', duty_time: 'within' },
        }),
      })
      setFormState({ full_name: '', role: 'pilot', duty_status: 'Ready' })
      await loadCrew()
    } catch (error) {
      console.warn('Unable to add crew', error)
    }
  }

  return (
    <div className="page">
      <SectionHeader
        eyebrow="Crew Readiness"
        title="Duty Time + Certifications"
        action={<button className="ghost-button">Fatigue Report</button>}
      />

      <div className="section-grid">
        <div className="panel form-panel">
          <form className="form-grid" onSubmit={addCrew}>
            <div>
              <label>Name</label>
              <input
                name="full_name"
                value={formState.full_name}
                onChange={handleChange}
                placeholder="Crew member name"
                required
              />
            </div>
            <div>
              <label>Role</label>
              <select name="role" value={formState.role} onChange={handleChange}>
                <option value="pilot">Pilot</option>
                <option value="flight_nurse">Flight Nurse</option>
                <option value="flight_medic">Flight Medic</option>
                <option value="hems_supervisor">Supervisor</option>
              </select>
            </div>
            <div>
              <label>Duty Status</label>
              <select
                name="duty_status"
                value={formState.duty_status}
                onChange={handleChange}
              >
                <option>Ready</option>
                <option>On Duty</option>
                <option>Resting</option>
                <option>Unavailable</option>
              </select>
            </div>
            <div className="full-width align-end">
              <button className="primary-button" type="submit">
                Add Crew
              </button>
            </div>
          </form>
        </div>
        <div className="panel">
          <AdvisoryPanel
            title="Fatigue Advisory"
            model="quantum-ai"
            version="1.0"
            level="ADVISORY"
            message="Crew 2 approaching duty limit. Recommend relief after next mission."
            reason="Duty time + sleep index evaluation."
          />
          <div className="note-card">
            <p className="note-title">Readiness Snapshot</p>
            <p className="note-body">
              92% of crews cleared for immediate launch. 1 crew on rest cycle.
            </p>
          </div>
        </div>
      </div>

      <div className="panel">
        <SectionHeader eyebrow="Roster" title="Active Crew" />
        <DataTable columns={crewColumns} rows={crew} emptyState="No crew added yet." />
      </div>
    </div>
  )
}
