import { useEffect, useState } from 'react'
import SectionHeader from '../components/SectionHeader.jsx'
import DataTable from '../components/DataTable.jsx'
import AdvisoryPanel from '../components/AdvisoryPanel.jsx'
import { apiFetch } from '../services/api.js'
import { fallbackBuilderLogs, fallbackBuilders } from '../data/fallback.js'

const builderColumns = [
  { key: 'builder_key', label: 'Builder' },
  { key: 'version', label: 'Version' },
  { key: 'status', label: 'Status' },
  { key: 'description', label: 'Mission' },
]

const logColumns = [
  { key: 'builder_key', label: 'Builder' },
  { key: 'change_summary', label: 'Change' },
  { key: 'created_at', label: 'Timestamp' },
]

export default function BuilderRegistry() {
  const [builders, setBuilders] = useState(fallbackBuilders)
  const [logs, setLogs] = useState(fallbackBuilderLogs)

  const loadBuilders = async () => {
    try {
      const data = await apiFetch('/api/builders/registry')
      if (Array.isArray(data) && data.length > 0) {
        setBuilders(data)
      }
    } catch (error) {
      console.warn('Builder registry unavailable', error)
    }
  }

  const loadLogs = async () => {
    try {
      const data = await apiFetch('/api/builders/logs')
      if (Array.isArray(data) && data.length > 0) {
        setLogs(data)
      }
    } catch (error) {
      console.warn('Builder logs unavailable', error)
    }
  }

  useEffect(() => {
    loadBuilders()
    loadLogs()
  }, [])

  return (
    <div className="page">
      <SectionHeader
        eyebrow="Builder Registry"
        title="Policy, Workflow, Export Builders"
        action={<button className="primary-button">Publish Drafts</button>}
      />

      <div className="section-grid">
        <div className="panel builder-panel">
          <SectionHeader eyebrow="Registry" title="Active Builders" />
          <DataTable columns={builderColumns} rows={builders} emptyState="No builders yet." />
        </div>
        <div className="panel">
          <AdvisoryPanel
            title="Impact Preview"
            model="builder-sim"
            version="1.8"
            level="ADVISORY"
            message="Run a rule impact simulation to see which workflows would be affected."
            reason="Builder impact simulator"
          />
          <div className="note-card">
            <p className="note-title">Rollback Safe State</p>
            <p className="note-body">No rollback staged yet. Publish a draft to enable rollback history.</p>
          </div>
        </div>
      </div>

      <div className="panel">
        <SectionHeader eyebrow="Change Log" title="Recent Builder Changes" />
        <DataTable columns={logColumns} rows={logs} emptyState="No builder changes recorded yet." />
      </div>
    </div>
  )
}
