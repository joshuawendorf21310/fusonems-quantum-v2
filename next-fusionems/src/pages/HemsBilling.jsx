import { useEffect, useState } from 'react'
import SectionHeader from '../components/SectionHeader.jsx'
import DataTable from '../components/DataTable.jsx'
import { apiFetch } from '../services/api.js'
import { fallbackHemsMissions } from '../data/fallback.js'

const billingColumns = [
  { key: 'mission_id', label: 'Mission' },
  { key: 'transport_type', label: 'Type' },
  { key: 'miles', label: 'Miles' },
  { key: 'time_minutes', label: 'Minutes' },
  { key: 'export_status', label: 'Export' },
]

export default function HemsBilling() {
  const [missions, setMissions] = useState(fallbackHemsMissions)
  const [billingPackets, setBillingPackets] = useState([])
  const [formState, setFormState] = useState({
    mission_id: '',
    transport_type: 'scene',
    miles: 0,
    time_minutes: 0,
    justification: '',
  })

  const loadMissions = async () => {
    try {
      const data = await apiFetch('/api/hems/missions')
      if (Array.isArray(data) && data.length) {
        setMissions(data)
      }
    } catch (error) {
      console.warn('Unable to load missions', error)
    }
  }

  useEffect(() => {
    loadMissions()
  }, [])

  const handleChange = (event) => {
    const { name, value } = event.target
    setFormState((prev) => ({ ...prev, [name]: value }))
  }

  const createPacket = async (event) => {
    event.preventDefault()
    if (!formState.mission_id) return
    try {
      const packet = await apiFetch(`/api/hems/missions/${formState.mission_id}/billing`, {
        method: 'POST',
        body: JSON.stringify({
          transport_type: formState.transport_type,
          miles: Number(formState.miles),
          time_minutes: Number(formState.time_minutes),
          justification: formState.justification,
        }),
      })
      setBillingPackets((prev) => [packet, ...prev])
      setFormState({
        mission_id: '',
        transport_type: 'scene',
        miles: 0,
        time_minutes: 0,
        justification: '',
      })
    } catch (error) {
      console.warn('Unable to create billing packet', error)
    }
  }

  return (
    <div className="page">
      <SectionHeader
        eyebrow="HEMS Billing"
        title="Export Packets + Justification"
        action={<button className="ghost-button">Export 837</button>}
      />

      <div className="section-grid">
        <div className="panel form-panel">
          <form className="form-grid" onSubmit={createPacket}>
            <div>
              <label>Mission</label>
              <select
                name="mission_id"
                value={formState.mission_id}
                onChange={handleChange}
                required
              >
                <option value="">Select mission</option>
                {missions.map((mission) => (
                  <option key={mission.id} value={mission.id}>
                    {mission.id} — {mission.mission_type} ({mission.status})
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label>Transport Type</label>
              <select
                name="transport_type"
                value={formState.transport_type}
                onChange={handleChange}
              >
                <option value="scene">Scene</option>
                <option value="IFT">IFT</option>
                <option value="fixed-wing">Fixed Wing</option>
                <option value="rotor-wing">Rotor Wing</option>
              </select>
            </div>
            <div>
              <label>Miles</label>
              <input
                name="miles"
                type="number"
                value={formState.miles}
                onChange={handleChange}
              />
            </div>
            <div>
              <label>Minutes</label>
              <input
                name="time_minutes"
                type="number"
                value={formState.time_minutes}
                onChange={handleChange}
              />
            </div>
            <div className="full-width">
              <label>Justification</label>
              <textarea
                name="justification"
                value={formState.justification}
                onChange={handleChange}
                placeholder="Medical necessity summary"
              />
            </div>
            <div className="full-width align-end">
              <button className="primary-button" type="submit">
                Create Billing Packet
              </button>
            </div>
          </form>
        </div>
        <div className="panel">
          <SectionHeader eyebrow="Queue" title="Pending Exports" />
          <DataTable
            columns={billingColumns}
            rows={billingPackets}
            emptyState="No billing packets yet."
          />
        </div>
      </div>
    </div>
  )
}
