import { useEffect, useState } from 'react'
import SectionHeader from '../components/SectionHeader.jsx'
import DataTable from '../components/DataTable.jsx'
import AdvisoryPanel from '../components/AdvisoryPanel.jsx'
import { apiFetch } from '../services/api.js'
import { fallbackValidationRules } from '../data/fallback.js'

const ruleColumns = [
  { key: 'name', label: 'Rule' },
  { key: 'entity_type', label: 'Entity' },
  { key: 'rule_type', label: 'Type' },
  { key: 'field', label: 'Field' },
  { key: 'severity', label: 'Severity' },
  { key: 'enforcement', label: 'Enforcement' },
  { key: 'status', label: 'Status' },
]

export default function ValidationBuilder() {
  const [rules, setRules] = useState(fallbackValidationRules)
  const [form, setForm] = useState({
    name: '',
    entity_type: 'epcr',
    rule_type: 'required_field',
    field: '',
    severity: 'High',
    enforcement: 'hard_block',
    status: 'active',
  })

  const loadRules = async () => {
    try {
      const data = await apiFetch('/api/validation/rules')
      if (Array.isArray(data) && data.length > 0) {
        setRules(data)
      }
    } catch (error) {
      console.warn('Validation rules unavailable', error)
    }
  }

  useEffect(() => {
    loadRules()
  }, [])

  const handleChange = (event) => {
    const { name, value } = event.target
    setForm((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    const payload = {
      ...form,
      condition: form.rule_type === 'conditional' ? { if_field: 'transport', if_value: true, then_field: form.field } : {},
    }
    try {
      const created = await apiFetch('/api/validation/rules', {
        method: 'POST',
        body: JSON.stringify(payload),
      })
      setRules((prev) => [created, ...prev])
      setForm({ ...form, name: '', field: '' })
    } catch (error) {
      console.warn('Unable to create validation rule', error)
    }
  }

  return (
    <div className="page">
      <SectionHeader
        eyebrow="Validation Builder"
        title="Rule-Based Clinical & Billing Enforcement"
        action={<button className="primary-button">Run Rule Simulation</button>}
      />

      <div className="section-grid">
        <div className="panel">
          <SectionHeader eyebrow="Create Rule" title="New Validation Rule" />
          <form className="form-grid" onSubmit={handleSubmit}>
            <label className="field">
              <span>Name</span>
              <input name="name" value={form.name} onChange={handleChange} required />
            </label>
            <label className="field">
              <span>Entity</span>
              <select name="entity_type" value={form.entity_type} onChange={handleChange}>
                <option value="epcr">ePCR</option>
                <option value="hems">HEMS</option>
                <option value="billing">Billing</option>
                <option value="scheduling">Scheduling</option>
              </select>
            </label>
            <label className="field">
              <span>Rule Type</span>
              <select name="rule_type" value={form.rule_type} onChange={handleChange}>
                <option value="required_field">Required Field</option>
                <option value="conditional">Conditional</option>
              </select>
            </label>
            <label className="field">
              <span>Field</span>
              <input name="field" value={form.field} onChange={handleChange} required />
            </label>
            <label className="field">
              <span>Severity</span>
              <select name="severity" value={form.severity} onChange={handleChange}>
                <option value="High">High</option>
                <option value="Medium">Medium</option>
                <option value="Low">Low</option>
              </select>
            </label>
            <label className="field">
              <span>Enforcement</span>
              <select name="enforcement" value={form.enforcement} onChange={handleChange}>
                <option value="hard_block">Hard Block</option>
                <option value="soft_block">Soft Block</option>
                <option value="advisory">Advisory</option>
              </select>
            </label>
            <button className="primary-button" type="submit">
              Save Rule
            </button>
          </form>
        </div>
        <div className="panel">
          <AdvisoryPanel
            title="Impact Preview"
            model="rule-sim"
            version="2.0"
            level="ADVISORY"
            message="Run a simulation to see how many submissions would be impacted."
            reason="Simulation requires recent run data."
          />
          <div className="note-card">
            <p className="note-title">Versioning</p>
            <p className="note-body">Draft rules remain isolated until explicitly activated.</p>
          </div>
        </div>
      </div>

      <div className="panel">
        <SectionHeader eyebrow="Rules" title="Active Validation Rules" />
        <DataTable columns={ruleColumns} rows={rules} emptyState="No validation rules." />
      </div>
    </div>
  )
}
