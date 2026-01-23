import { useEffect, useState } from 'react'
import SectionHeader from '../components/SectionHeader.jsx'
import DataTable from '../components/DataTable.jsx'
import { apiFetch } from '../services/api.js'

const demoHolds = [
  {
    id: 1,
    scope_type: 'hems_mission',
    scope_id: '221',
    status: 'Active',
    reason: 'QA review',
  },
]

const holdColumns = [
  { key: 'scope_type', label: 'Scope' },
  { key: 'scope_id', label: 'ID' },
  { key: 'status', label: 'Status' },
  { key: 'reason', label: 'Reason' },
]

export default function HemsQA() {
  const [holds, setHolds] = useState(demoHolds)
  const [reviews, setReviews] = useState([])
  const [overrideState, setOverrideState] = useState({
    override_type: 'aviation',
    resource_type: 'hems_mission',
    resource_id: '',
    reason_code: '',
    notes: '',
  })

  const loadHolds = async () => {
    try {
      const data = await apiFetch('/api/legal-hold')
      if (Array.isArray(data) && data.length) {
        setHolds(data)
      }
    } catch (error) {
      console.warn('Unable to load legal holds', error)
    }
  }

  const loadReviews = async () => {
    try {
      const data = await apiFetch('/api/hems/qa')
      if (Array.isArray(data)) {
        setReviews(data)
      }
    } catch (error) {
      console.warn('Unable to load HEMS QA', error)
    }
  }

  useEffect(() => {
    loadHolds()
    loadReviews()
  }, [])

  const handleOverrideChange = (event) => {
    const { name, value } = event.target
    setOverrideState((prev) => ({ ...prev, [name]: value }))
  }

  const submitOverride = async (event) => {
    event.preventDefault()
    try {
      await apiFetch('/api/legal-hold/overrides', {
        method: 'POST',
        body: JSON.stringify(overrideState),
      })
      setOverrideState({
        override_type: 'aviation',
        resource_type: 'hems_mission',
        resource_id: '',
        reason_code: '',
        notes: '',
      })
    } catch (error) {
      console.warn('Unable to submit override', error)
    }
  }

  return (
    <div className="page">
      <SectionHeader
        eyebrow="QA + Medical Director"
        title="Compliance Review Queue"
        action={<button className="ghost-button">Export QA Packet</button>}
      />

      <div className="section-grid">
        <div className="panel">
          <SectionHeader eyebrow="Legal Holds" title="Active Holds" />
          <DataTable columns={holdColumns} rows={holds} emptyState="No active legal holds." />
        </div>
        <div className="panel form-panel">
          <SectionHeader eyebrow="Override" title="Structured Override Request" />
          <form className="form-grid" onSubmit={submitOverride}>
            <div>
              <label>Override Type</label>
              <select
                name="override_type"
                value={overrideState.override_type}
                onChange={handleOverrideChange}
              >
                <option value="aviation">Aviation</option>
                <option value="clinical">Clinical</option>
                <option value="billing">Billing</option>
                <option value="access">Access</option>
              </select>
            </div>
            <div>
              <label>Resource Type</label>
              <input
                name="resource_type"
                value={overrideState.resource_type}
                onChange={handleOverrideChange}
              />
            </div>
            <div>
              <label>Resource ID</label>
              <input
                name="resource_id"
                value={overrideState.resource_id}
                onChange={handleOverrideChange}
                placeholder="Mission ID"
                required
              />
            </div>
            <div>
              <label>Reason Code</label>
              <input
                name="reason_code"
                value={overrideState.reason_code}
                onChange={handleOverrideChange}
                placeholder="QA-justification"
                required
              />
            </div>
            <div className="full-width">
              <label>Notes</label>
              <textarea
                name="notes"
                value={overrideState.notes}
                onChange={handleOverrideChange}
                placeholder="Medical director review notes"
              />
            </div>
            <div className="full-width align-end">
              <button className="primary-button" type="submit">
                Submit Override
              </button>
            </div>
          </form>
        </div>
      </div>

      <div className="panel">
        <SectionHeader eyebrow="QA Queue" title="HEMS Quality Reviews" />
        <DataTable
          columns={[
            { key: 'mission_id', label: 'Mission' },
            { key: 'reviewer', label: 'Reviewer' },
            { key: 'status', label: 'Status' },
            { key: 'determination', label: 'Determination' },
          ]}
          rows={reviews}
          emptyState="No HEMS QA reviews yet."
        />
      </div>
    </div>
  )
}
