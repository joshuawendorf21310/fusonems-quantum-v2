import { useEffect, useState } from 'react'
import SectionHeader from '../components/SectionHeader.jsx'
import DataTable from '../components/DataTable.jsx'
import { apiFetch } from '../services/api.js'

const preventionColumns = [
  { key: 'occupancy_name', label: 'Occupancy' },
  { key: 'inspection_status', label: 'Status' },
  { key: 'hydrant_map', label: 'Hydrant Map' },
  { key: 'notes', label: 'Notes' },
]

export default function FirePrevention() {
  const [records, setRecords] = useState([])
  const [formState, setFormState] = useState({
    occupancy_name: '',
    inspection_status: 'Scheduled',
    hydrant_map: '',
    notes: '',
  })

  const loadPrevention = async () => {
    try {
      const data = await apiFetch('/api/fire/prevention')
      setRecords(data)
    } catch (error) {
      console.warn('Unable to load prevention records', error)
    }
  }

  useEffect(() => {
    loadPrevention()
  }, [])

  const handleChange = (event) => {
    const { name, value } = event.target
    setFormState((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    try {
      await apiFetch('/api/fire/prevention', {
        method: 'POST',
        body: JSON.stringify(formState),
      })
      setFormState({
        occupancy_name: '',
        inspection_status: 'Scheduled',
        hydrant_map: '',
        notes: '',
      })
      await loadPrevention()
    } catch (error) {
      console.warn('Unable to create prevention record', error)
    }
  }

  return (
    <div className="page">
      <SectionHeader
        eyebrow="Prevention & Inspections"
        title="Pre-Incident Planning and Hydrant Mapping"
        action={<button className="ghost-button">Inspection Calendar</button>}
      />

      <div className="panel form-panel">
        <form className="form-grid" onSubmit={handleSubmit}>
          <div>
            <label>Occupancy Name</label>
            <input
              name="occupancy_name"
              value={formState.occupancy_name}
              onChange={handleChange}
              placeholder="Silver Oaks Mall"
              required
            />
          </div>
          <div>
            <label>Status</label>
            <select
              name="inspection_status"
              value={formState.inspection_status}
              onChange={handleChange}
            >
              <option>Scheduled</option>
              <option>In Progress</option>
              <option>Complete</option>
              <option>Follow-up Required</option>
            </select>
          </div>
          <div>
            <label>Hydrant Map</label>
            <input
              name="hydrant_map"
              value={formState.hydrant_map}
              onChange={handleChange}
              placeholder="Map reference or link"
            />
          </div>
          <div className="full-width">
            <label>Notes</label>
            <input
              name="notes"
              value={formState.notes}
              onChange={handleChange}
              placeholder="Occupancy notes, hazards, access info"
            />
          </div>
          <div className="full-width align-end">
            <button className="primary-button" type="submit">
              Add Record
            </button>
          </div>
        </form>
      </div>

      <div className="panel">
        <SectionHeader eyebrow="Records" title="Inspection History" />
        <DataTable
          columns={preventionColumns}
          rows={records}
          emptyState="No prevention records yet."
        />
      </div>
    </div>
  )
}
