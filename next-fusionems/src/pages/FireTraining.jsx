import { useEffect, useState } from 'react'
import SectionHeader from '../components/SectionHeader.jsx'
import DataTable from '../components/DataTable.jsx'
import { apiFetch } from '../services/api.js'

const trainingColumns = [
  { key: 'training_type', label: 'Training' },
  { key: 'crew', label: 'Crew' },
  { key: 'status', label: 'Status' },
  { key: 'notes', label: 'Notes' },
]

export default function FireTraining() {
  const [records, setRecords] = useState([])
  const [formState, setFormState] = useState({
    training_type: '',
    crew: '',
    status: 'Planned',
    notes: '',
  })

  const loadTraining = async () => {
    try {
      const data = await apiFetch('/api/fire/training')
      setRecords(data)
    } catch (error) {
      console.warn('Unable to load training', error)
    }
  }

  useEffect(() => {
    loadTraining()
  }, [])

  const handleChange = (event) => {
    const { name, value } = event.target
    setFormState((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    try {
      await apiFetch('/api/fire/training', {
        method: 'POST',
        body: JSON.stringify(formState),
      })
      setFormState({
        training_type: '',
        crew: '',
        status: 'Planned',
        notes: '',
      })
      await loadTraining()
    } catch (error) {
      console.warn('Unable to add training', error)
    }
  }

  return (
    <div className="page">
      <SectionHeader
        eyebrow="Training & Drills"
        title="Readiness Exercises and Compliance"
        action={<button className="ghost-button">Readiness Report</button>}
      />

      <div className="panel form-panel">
        <form className="form-grid" onSubmit={handleSubmit}>
          <div>
            <label>Training Type</label>
            <input
              name="training_type"
              value={formState.training_type}
              onChange={handleChange}
              placeholder="Live burn, tabletop, joint Fire-EMS"
              required
            />
          </div>
          <div>
            <label>Crew</label>
            <input
              name="crew"
              value={formState.crew}
              onChange={handleChange}
              placeholder="Station 3 Alpha"
              required
            />
          </div>
          <div>
            <label>Status</label>
            <select name="status" value={formState.status} onChange={handleChange}>
              <option>Planned</option>
              <option>Completed</option>
              <option>Overdue</option>
            </select>
          </div>
          <div className="full-width">
            <label>Notes</label>
            <input
              name="notes"
              value={formState.notes}
              onChange={handleChange}
              placeholder="Objectives, attendance, outcomes"
            />
          </div>
          <div className="full-width align-end">
            <button className="primary-button" type="submit">
              Schedule Training
            </button>
          </div>
        </form>
      </div>

      <div className="panel">
        <SectionHeader eyebrow="Records" title="Training Activity" />
        <DataTable
          columns={trainingColumns}
          rows={records}
          emptyState="No training records yet."
        />
      </div>
    </div>
  )
}
