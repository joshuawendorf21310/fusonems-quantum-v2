import { useEffect, useState } from 'react'
import SectionHeader from '../components/SectionHeader.jsx'
import DataTable from '../components/DataTable.jsx'
import AdvisoryPanel from '../components/AdvisoryPanel.jsx'
import { apiFetch } from '../services/api.js'
import {
  fallbackGovernance,
  fallbackIncidents,
  fallbackPwa,
  fallbackPricing,
} from '../data/fallback.js'

const pwaColumns = [
  { key: 'platform', label: 'Platform' },
  { key: 'current_version', label: 'Current' },
  { key: 'pending_version', label: 'Pending' },
  { key: 'status', label: 'Status' },
]

const pricingColumns = [
  { key: 'plan_name', label: 'Plan' },
  { key: 'status', label: 'Status' },
  { key: 'pricing', label: 'Pricing' },
]

const incidentColumns = [
  { key: 'title', label: 'Incident' },
  { key: 'severity', label: 'Severity' },
  { key: 'status', label: 'Status' },
  { key: 'summary', label: 'Summary' },
]

const governanceColumns = [
  { key: 'rule_type', label: 'Rule' },
  { key: 'status', label: 'Status' },
  { key: 'settings', label: 'Settings' },
]

export default function FounderOps() {
  const [pwaRules, setPwaRules] = useState(fallbackPwa)
  const [pricing, setPricing] = useState(fallbackPricing)
  const [incidents, setIncidents] = useState(fallbackIncidents)
  const [governance, setGovernance] = useState(fallbackGovernance)
  const [pwaForm, setPwaForm] = useState({
    platform: 'web',
    current_version: '',
    pending_version: '',
    status: 'enabled',
  })

  const loadFounderData = async () => {
    try {
      const [pwaData, pricingData, incidentData, governanceData] = await Promise.all([
        apiFetch('/api/founder-ops/pwa'),
        apiFetch('/api/founder-ops/pricing'),
        apiFetch('/api/founder-ops/incidents'),
        apiFetch('/api/founder-ops/governance'),
      ])
      if (Array.isArray(pwaData) && pwaData.length > 0) setPwaRules(pwaData)
      if (Array.isArray(pricingData) && pricingData.length > 0) setPricing(pricingData)
      if (Array.isArray(incidentData) && incidentData.length > 0) setIncidents(incidentData)
      if (Array.isArray(governanceData) && governanceData.length > 0) setGovernance(governanceData)
    } catch (error) {
      console.warn('Founder ops unavailable', error)
    }
  }

  useEffect(() => {
    loadFounderData()
  }, [])

  const handlePwaChange = (event) => {
    const { name, value } = event.target
    setPwaForm((prev) => ({ ...prev, [name]: value }))
  }

  const handlePwaSubmit = async (event) => {
    event.preventDefault()
    try {
      const record = await apiFetch('/api/founder-ops/pwa', {
        method: 'POST',
        body: JSON.stringify(pwaForm),
      })
      setPwaRules((prev) => [record, ...prev])
      setPwaForm({ ...pwaForm, current_version: '', pending_version: '' })
    } catch (error) {
      console.warn('Unable to create PWA rule', error)
    }
  }

  return (
    <div className="page">
      <SectionHeader
        eyebrow="Founder Ops"
        title="Distribution, Pricing, Incidents, Governance"
        action={<button className="primary-button">Open Incident</button>}
      />

      <div className="section-grid">
        <div className="panel">
          <SectionHeader eyebrow="PWA" title="Distribution Control" />
          <form className="form-grid" onSubmit={handlePwaSubmit}>
            <label className="field">
              <span>Platform</span>
              <select name="platform" value={pwaForm.platform} onChange={handlePwaChange}>
                <option value="web">Web</option>
                <option value="pwa-ios">PWA (iOS)</option>
                <option value="pwa-android">PWA (Android)</option>
              </select>
            </label>
            <label className="field">
              <span>Current Version</span>
              <input
                name="current_version"
                value={pwaForm.current_version}
                onChange={handlePwaChange}
              />
            </label>
            <label className="field">
              <span>Pending Version</span>
              <input
                name="pending_version"
                value={pwaForm.pending_version}
                onChange={handlePwaChange}
              />
            </label>
            <label className="field">
              <span>Status</span>
              <select name="status" value={pwaForm.status} onChange={handlePwaChange}>
                <option value="enabled">Enabled</option>
                <option value="disabled">Disabled</option>
                <option value="rollback">Rollback</option>
              </select>
            </label>
            <button className="ghost-button" type="submit">
              Save Distribution Rule
            </button>
          </form>
          <DataTable columns={pwaColumns} rows={pwaRules} emptyState="No distribution rules." />
        </div>
        <div className="panel">
          <AdvisoryPanel
            title="Release Gate"
            model="ops-guard"
            version="1.3"
            level="ADVISORY"
            message="Run readiness checks before scheduling a release window."
            reason="Upgrade readiness + compliance status"
          />
          <div className="note-card">
            <p className="note-title">Kill Switch</p>
            <p className="note-body">Emergency mode is available. Enable only during incidents.</p>
          </div>
        </div>
      </div>

      <div className="section-grid">
        <div className="panel">
          <SectionHeader eyebrow="Pricing" title="Plans & Limits" />
          <DataTable columns={pricingColumns} rows={pricing} emptyState="No pricing plans." />
        </div>
        <div className="panel">
          <SectionHeader eyebrow="Incidents" title="Command Center" />
          <DataTable columns={incidentColumns} rows={incidents} emptyState="No incidents." />
        </div>
      </div>

      <div className="panel">
        <SectionHeader eyebrow="Governance" title="Data Governance Rules" />
        <DataTable columns={governanceColumns} rows={governance} emptyState="No rules." />
      </div>
    </div>
  )
}
