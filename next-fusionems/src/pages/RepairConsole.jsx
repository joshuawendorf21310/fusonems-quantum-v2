import { useState } from 'react'
import SectionHeader from '../components/SectionHeader.jsx'
import DataTable from '../components/DataTable.jsx'
import AdvisoryPanel from '../components/AdvisoryPanel.jsx'
import { apiFetch } from '../services/api.js'

const demoOrphans = [
  {
    orphan_type: 'hems_assignment',
    orphan_id: 12,
    mission_id: 404,
    crew_id: 7,
    aircraft_id: 3,
  },
]

const orphanColumns = [
  { key: 'orphan_type', label: 'Type' },
  { key: 'orphan_id', label: 'Orphan ID' },
  { key: 'mission_id', label: 'Mission' },
  { key: 'crew_id', label: 'Crew' },
  { key: 'aircraft_id', label: 'Aircraft' },
]

export default function RepairConsole() {
  const [orphans, setOrphans] = useState(demoOrphans)
  const [repairState, setRepairState] = useState({
    orphan_type: 'hems_assignment',
    orphan_id: '',
    action: 'relink',
    new_mission_id: '',
  })

  const scanOrphans = async () => {
    try {
      const data = await apiFetch('/api/repair/scan')
      if (Array.isArray(data.orphans)) {
        setOrphans(data.orphans)
      }
    } catch (error) {
      console.warn('Unable to scan orphans', error)
    }
  }

  const handleChange = (event) => {
    const { name, value } = event.target
    setRepairState((prev) => ({ ...prev, [name]: value }))
  }

  const resolveOrphan = async (event) => {
    event.preventDefault()
    try {
      await apiFetch('/api/repair/resolve', {
        method: 'POST',
        body: JSON.stringify({
          ...repairState,
          orphan_id: Number(repairState.orphan_id),
          new_mission_id: repairState.new_mission_id
            ? Number(repairState.new_mission_id)
            : null,
        }),
      })
    } catch (error) {
      console.warn('Unable to resolve orphan', error)
    }
  }

  return (
    <div className="page">
      <SectionHeader
        eyebrow="Repair Tooling"
        title="Orphan Detection + Recovery"
        action={
          <button className="primary-button" type="button" onClick={scanOrphans}>
            Scan Orphans
          </button>
        }
      />

      <div className="section-grid">
        <div className="panel">
          <SectionHeader eyebrow="Detected Orphans" title="Review Queue" />
          <DataTable
            columns={orphanColumns}
            rows={orphans}
            emptyState="No orphans detected."
          />
        </div>
        <div className="panel form-panel">
          <SectionHeader eyebrow="Repair Action" title="Relink or Mark Detached" />
          <form className="form-grid" onSubmit={resolveOrphan}>
            <div>
              <label>Orphan ID</label>
              <input
                name="orphan_id"
                value={repairState.orphan_id}
                onChange={handleChange}
                placeholder="12"
                required
              />
            </div>
            <div>
              <label>Action</label>
              <select name="action" value={repairState.action} onChange={handleChange}>
                <option value="relink">Relink</option>
                <option value="mark_detached">Mark Detached</option>
              </select>
            </div>
            <div>
              <label>New Mission ID</label>
              <input
                name="new_mission_id"
                value={repairState.new_mission_id}
                onChange={handleChange}
                placeholder="221"
              />
            </div>
            <div className="full-width align-end">
              <button className="primary-button" type="submit">
                Resolve
              </button>
            </div>
          </form>
        </div>
      </div>

      <AdvisoryPanel
        title="Integrity Guardrail"
        model="quantum-ai"
        version="1.0"
        level="ADVISORY"
        message="All repairs are audited and replayable. Use relink when the target mission is verified."
        reason="Orphan detection + repair policy checks."
      />
    </div>
  )
}
