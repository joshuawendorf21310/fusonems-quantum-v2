import { useState } from 'react'
import { useAppData } from '../context/useAppData.js'
import SectionHeader from '../components/SectionHeader.jsx'
import DualScreenCAD from '../components/cad/DualScreenCAD.tsx'
import { apiFetch } from '../services/api.js'

export default function CadManagement() {
  const { refreshAll } = useAppData()
  const [formState, setFormState] = useState({
    caller_name: '',
    caller_phone: '',
    location_address: '',
    latitude: '',
    longitude: '',
    priority: 'Routine',
  })

  const handleChange = (event) => {
    const { name, value } = event.target
    setFormState((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    try {
      await apiFetch('/api/cad/calls', {
        method: 'POST',
        body: JSON.stringify({
          ...formState,
          latitude: Number(formState.latitude),
          longitude: Number(formState.longitude),
        }),
      })
      setFormState({
        caller_name: '',
        caller_phone: '',
        location_address: '',
        latitude: '',
        longitude: '',
        priority: 'Routine',
      })
      await refreshAll()
    } catch (error) {
      console.warn('Unable to create call', error)
    }
  }

  return (
    <div className="page">
      <SectionHeader
        eyebrow="CAD Management"
        title="Incoming Call Intake"
        action={<button className="ghost-button">Dispatch Protocols</button>}
      />

      <div className="panel form-panel">
        <form className="form-grid" onSubmit={handleSubmit}>
          <div>
            <label>Caller Name</label>
            <input
              name="caller_name"
              value={formState.caller_name}
              onChange={handleChange}
              placeholder="Patient or bystander"
              required
            />
          </div>
          <div>
            <label>Caller Phone</label>
            <input
              name="caller_phone"
              value={formState.caller_phone}
              onChange={handleChange}
              placeholder="(555) 555-5555"
              required
            />
          </div>
          <div className="full-width">
            <label>Location</label>
            <input
              name="location_address"
              value={formState.location_address}
              onChange={handleChange}
              placeholder="Address or landmark"
              required
            />
          </div>
          <div>
            <label>Latitude</label>
            <input
              name="latitude"
              value={formState.latitude}
              onChange={handleChange}
              placeholder="40.7128"
              required
            />
          </div>
          <div>
            <label>Longitude</label>
            <input
              name="longitude"
              value={formState.longitude}
              onChange={handleChange}
              placeholder="-74.0060"
              required
            />
          </div>
          <div>
            <label>Priority</label>
            <select name="priority" value={formState.priority} onChange={handleChange}>
              <option>Routine</option>
              <option>High</option>
              <option>Critical</option>
            </select>
          </div>
          <div className="full-width align-end">
            <button className="primary-button" type="submit">
              Log Call
            </button>
          </div>
        </form>
      </div>

      <DualScreenCAD />
    </div>
  )
}
