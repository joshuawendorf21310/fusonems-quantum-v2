import { useEffect, useState } from 'react'
import SectionHeader from '../components/SectionHeader.jsx'
import DataTable from '../components/DataTable.jsx'
import AdvisoryPanel from '../components/AdvisoryPanel.jsx'
import { apiFetch } from '../services/api.js'

const incidentColumns = [
  { key: 'incident_id', label: 'Incident ID' },
  { key: 'incident_type', label: 'Type' },
  { key: 'location', label: 'Location' },
  { key: 'status', label: 'Status' },
  { key: 'priority', label: 'Priority' },
  { key: 'nfirs_status', label: 'NFIRS' },
]

export default function FireIncidents() {
  const [incidents, setIncidents] = useState([])
  const [exportHistory, setExportHistory] = useState([])
  const [formState, setFormState] = useState({
    incident_type: '',
    location: '',
    incident_category: 'Structure',
    priority: 'Routine',
    narrative: '',
  })
  const [selectedIncident, setSelectedIncident] = useState('')
  const [epcrLink, setEpcrLink] = useState('')
  const [aiReview, setAiReview] = useState(null)

  const loadIncidents = async () => {
    try {
      const data = await apiFetch('/api/fire/incidents')
      setIncidents(data)
      if (!selectedIncident && data.length) {
        setSelectedIncident(data[0].incident_id)
      }
    } catch (error) {
      console.warn('Unable to load fire incidents', error)
    }
  }

  const loadExports = async () => {
    try {
      const data = await apiFetch('/api/fire/exports/history')
      if (Array.isArray(data)) {
        setExportHistory(data)
      }
    } catch (error) {
      console.warn('Unable to load fire exports', error)
    }
  }

  useEffect(() => {
    loadIncidents()
    loadExports()
  }, [])

  const handleChange = (event) => {
    const { name, value } = event.target
    setFormState((prev) => ({ ...prev, [name]: value }))
  }

  const createIncident = async (event) => {
    event.preventDefault()
    try {
      await apiFetch('/api/fire/incidents', {
        method: 'POST',
        body: JSON.stringify(formState),
      })
      setFormState({
        incident_type: '',
        location: '',
        incident_category: 'Structure',
        priority: 'Routine',
        narrative: '',
      })
      await loadIncidents()
    } catch (error) {
      console.warn('Unable to create incident', error)
    }
  }

  const linkEpcr = async () => {
    if (!selectedIncident || !epcrLink) return
    try {
      await apiFetch(`/api/fire/incidents/${selectedIncident}/link-epcr`, {
        method: 'POST',
        body: JSON.stringify({ ems_incident_id: epcrLink }),
      })
      setEpcrLink('')
      await loadIncidents()
    } catch (error) {
      console.warn('Unable to link ePCR', error)
    }
  }

  const runAiReview = async () => {
    if (!selectedIncident) return
    try {
      const data = await apiFetch(`/api/fire/incidents/${selectedIncident}/ai-review`)
      setAiReview(data)
    } catch (error) {
      console.warn('Unable to run AI review', error)
    }
  }

  const exportIncident = async (format) => {
    if (!selectedIncident) return
    const endpoint = format === 'NERIS' ? '/api/fire/exports/neris' : '/api/fire/exports/nfirs'
    try {
      await apiFetch(endpoint, {
        method: 'POST',
        body: JSON.stringify({ incident_id: selectedIncident }),
      })
      await loadExports()
    } catch (error) {
      console.warn('Unable to export incident', error)
    }
  }

  return (
    <div className="page">
      <SectionHeader
        eyebrow="Fire Incidents"
        title="NFIRS / NERIS-ready Incident Reporting"
        action={
          <div className="inline-actions">
            <button className="ghost-button" onClick={() => exportIncident('NFIRS')}>
              Export NFIRS
            </button>
            <button className="ghost-button" onClick={() => exportIncident('NERIS')}>
              Export NERIS
            </button>
          </div>
        }
      />

      <div className="section-grid">
        <div className="panel form-panel">
          <form className="form-grid" onSubmit={createIncident}>
            <div>
              <label>Incident Type</label>
              <input
                name="incident_type"
                value={formState.incident_type}
                onChange={handleChange}
                placeholder="Structure / Vehicle / Wildland"
                required
              />
            </div>
            <div>
              <label>Location</label>
              <input
                name="location"
                value={formState.location}
                onChange={handleChange}
                placeholder="123 Oak Street"
                required
              />
            </div>
            <div>
              <label>Category</label>
              <select
                name="incident_category"
                value={formState.incident_category}
                onChange={handleChange}
              >
                <option>Structure</option>
                <option>Vehicle</option>
                <option>Wildland</option>
                <option>Hazmat</option>
                <option>Rescue</option>
                <option>Standby</option>
                <option>Hybrid EMS</option>
              </select>
            </div>
            <div>
              <label>Priority</label>
              <select name="priority" value={formState.priority} onChange={handleChange}>
                <option>Routine</option>
                <option>Priority</option>
                <option>Critical</option>
              </select>
            </div>
            <div className="full-width">
              <label>Narrative</label>
              <textarea
                name="narrative"
                value={formState.narrative}
                onChange={handleChange}
                placeholder="AI-assisted narrative draft"
              />
            </div>
            <div className="full-width align-end">
              <button className="primary-button" type="submit">
                Create Incident
              </button>
            </div>
          </form>
        </div>
        <div className="panel">
          <SectionHeader eyebrow="Hybrid Reporting" title="Fire-EMS Layering" />
          <div className="stack">
            <label>Incident</label>
            <select
              value={selectedIncident}
              onChange={(event) => setSelectedIncident(event.target.value)}
            >
              {incidents.map((incident) => (
                <option key={incident.incident_id} value={incident.incident_id}>
                  {incident.incident_id} - {incident.location}
                </option>
              ))}
            </select>
            <input
              value={epcrLink}
              onChange={(event) => setEpcrLink(event.target.value)}
              placeholder="Link ePCR ID"
            />
            <button className="ghost-button" type="button" onClick={linkEpcr}>
              Link ePCR
            </button>
            <button className="ghost-button" type="button" onClick={runAiReview}>
              Run AI Review
            </button>
            {aiReview ? (
              <AdvisoryPanel
                title="AI Review Summary"
                model="quantum-ai"
                version={aiReview.model_version || '1.0'}
                level={aiReview.advisory_level || 'ADVISORY'}
                message={aiReview.summary}
                reason="Incident completeness + timeline consistency review."
              />
            ) : null}
          </div>
        </div>
      </div>

      <div className="panel">
        <SectionHeader eyebrow="Incident Log" title="Active + Recent Incidents" />
        <DataTable
          columns={incidentColumns}
          rows={incidents}
          emptyState="No incidents logged yet."
        />
      </div>

      <div className="panel">
        <SectionHeader eyebrow="Exports" title="NFIRS / NERIS History" />
        <DataTable
          columns={[
            { key: 'export_type', label: 'Type' },
            { key: 'incident_id', label: 'Incident' },
            { key: 'status', label: 'Status' },
            { key: 'created_at', label: 'Created' },
          ]}
          rows={exportHistory}
          emptyState="No exports generated yet."
        />
      </div>
    </div>
  )
}
