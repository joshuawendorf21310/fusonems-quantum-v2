import { useEffect, useState } from 'react'
import SectionHeader from '../components/SectionHeader.jsx'
import DataTable from '../components/DataTable.jsx'
import { apiFetch } from '../services/api.js'
import { fallbackHemsAircraft } from '../data/fallback.js'

const aircraftColumns = [
  { key: 'tail_number', label: 'Tail' },
  { key: 'availability', label: 'Availability' },
  { key: 'maintenance_status', label: 'Maintenance' },
]

export default function HemsAircraft() {
  const [aircraft, setAircraft] = useState(fallbackHemsAircraft)
  const [formState, setFormState] = useState({
    tail_number: '',
    availability: 'Available',
    maintenance_status: 'Green',
  })

  const loadAircraft = async () => {
    try {
      const data = await apiFetch('/api/hems/aircraft')
      if (Array.isArray(data) && data.length) {
        setAircraft(data)
      }
    } catch (error) {
      console.warn('Unable to load aircraft', error)
    }
  }

  useEffect(() => {
    loadAircraft()
  }, [])

  const handleChange = (event) => {
    const { name, value } = event.target
    setFormState((prev) => ({ ...prev, [name]: value }))
  }

  const addAircraft = async (event) => {
    event.preventDefault()
    try {
      await apiFetch('/api/hems/aircraft', {
        method: 'POST',
        body: JSON.stringify({
          tail_number: formState.tail_number,
          capability_flags: { nvg: true, winch: false },
          availability: formState.availability,
          maintenance_status: formState.maintenance_status,
        }),
      })
      setFormState({ tail_number: '', availability: 'Available', maintenance_status: 'Green' })
      await loadAircraft()
    } catch (error) {
      console.warn('Unable to add aircraft', error)
    }
  }

  return (
    <div className="page">
      <SectionHeader
        eyebrow="Aircraft Readiness"
        title="Fleet Status + NVG Capability"
        action={<button className="ghost-button">Maintenance Log</button>}
      />

      <div className="section-grid">
        <div className="panel form-panel">
          <form className="form-grid" onSubmit={addAircraft}>
            <div>
              <label>Tail Number</label>
              <input
                name="tail_number"
                value={formState.tail_number}
                onChange={handleChange}
                placeholder="N12QF"
                required
              />
            </div>
            <div>
              <label>Availability</label>
              <select
                name="availability"
                value={formState.availability}
                onChange={handleChange}
              >
                <option>Available</option>
                <option>Standby</option>
                <option>Out of Service</option>
              </select>
            </div>
            <div>
              <label>Maintenance</label>
              <select
                name="maintenance_status"
                value={formState.maintenance_status}
                onChange={handleChange}
              >
                <option>Green</option>
                <option>Yellow</option>
                <option>Red</option>
              </select>
            </div>
            <div className="full-width align-end">
              <button className="primary-button" type="submit">
                Add Aircraft
              </button>
            </div>
          </form>
        </div>
        <div className="panel">
          <SectionHeader eyebrow="Capabilities" title="Configured Loadouts" />
          <div className="stack">
            <div className="list-row">
              <div>
                <p className="list-title">NVG Ready</p>
                <p className="list-sub">2 aircraft</p>
              </div>
              <span className="badge">Active</span>
            </div>
            <div className="list-row">
              <div>
                <p className="list-title">Winch Config</p>
                <p className="list-sub">1 aircraft</p>
              </div>
              <span className="badge">Standby</span>
            </div>
          </div>
        </div>
      </div>

      <div className="panel">
        <SectionHeader eyebrow="Fleet" title="Current Status" />
        <DataTable
          columns={aircraftColumns}
          rows={aircraft}
          emptyState="No aircraft configured."
        />
      </div>
    </div>
  )
}
