import { useEffect, useState } from 'react'
import SectionHeader from '../components/SectionHeader.jsx'
import DataTable from '../components/DataTable.jsx'
import AdvisoryPanel from '../components/AdvisoryPanel.jsx'
import { apiFetch } from '../services/api.js'
import { fallbackFeatureFlags } from '../data/fallback.js'

const flagColumns = [
  { key: 'flag_key', label: 'Flag' },
  { key: 'module_key', label: 'Module' },
  { key: 'scope', label: 'Scope' },
  { key: 'enabled', label: 'Enabled' },
]

export default function FeatureFlags() {
  const [flags, setFlags] = useState(fallbackFeatureFlags)

  const loadFlags = async () => {
    try {
      const data = await apiFetch('/api/feature-flags')
      if (Array.isArray(data) && data.length > 0) {
        setFlags(data)
      }
    } catch (error) {
      console.warn('Feature flags unavailable', error)
    }
  }

  useEffect(() => {
    loadFlags()
  }, [])

  return (
    <div className="page">
      <SectionHeader
        eyebrow="Feature Flags"
        title="Release & Safety Controls"
        action={<button className="primary-button">Stage Flag</button>}
      />

      <div className="section-grid">
        <div className="panel flag-panel">
          <SectionHeader eyebrow="Registry" title="Active Flags" />
          <DataTable columns={flagColumns} rows={flags} emptyState="No feature flags yet." />
        </div>
        <div className="panel">
          <AdvisoryPanel
            title="Safety Gate"
            model="flag-guard"
            version="1.2"
            level="ADVISORY"
            message="PWA upgrades are blocked when compliance drift is detected."
            reason="Foundational safety policy"
          />
          <div className="note-card">
            <p className="note-title">Deployment Ready</p>
            <p className="note-body">Upgrade readiness PASS across core modules. Rollback points stored.</p>
          </div>
        </div>
      </div>
    </div>
  )
}
