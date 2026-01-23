import { useEffect, useState } from 'react'
import SectionHeader from '../components/SectionHeader.jsx'
import DataTable from '../components/DataTable.jsx'
import AdvisoryPanel from '../components/AdvisoryPanel.jsx'
import { apiFetch } from '../services/api.js'

const exportColumns = [
  { key: 'resource', label: 'Resource' },
  { key: 'count', label: 'Count' },
]

export default function DataExports() {
  const [manifest, setManifest] = useState(null)
  const [csvPreview, setCsvPreview] = useState('')
  const [history, setHistory] = useState([])

  const loadHistory = async () => {
    try {
      const data = await apiFetch('/api/export/history')
      if (Array.isArray(data)) {
        setHistory(data)
      }
    } catch (error) {
      console.warn('Export history unavailable', error)
    }
  }

  const runExport = async () => {
    try {
      const data = await apiFetch('/api/export/full', { method: 'POST', body: '{}' })
      setManifest(data.manifest)
      setCsvPreview(data.csv_preview)
      await loadHistory()
    } catch (error) {
      console.warn('Export failed', error)
    }
  }

  useEffect(() => {
    loadHistory()
  }, [])

  const exportRows = manifest
    ? Object.entries(manifest.counts || {}).map(([resource, count]) => ({
        resource,
        count,
      }))
    : []

  const historyRows = history.map((record) => ({
    id: record.id,
    export_hash: record.export_hash,
    created_at: record.created_at,
  }))

  const historyColumns = [
    { key: 'id', label: 'Export ID' },
    { key: 'export_hash', label: 'Hash' },
    { key: 'created_at', label: 'Created' },
  ]

  return (
    <div className="page">
      <SectionHeader
        eyebrow="Data Exit"
        title="Vendor-Neutral Exports"
        action={
          <button className="primary-button" type="button" onClick={runExport}>
            Generate Full Export
          </button>
        }
      />

      <div className="section-grid">
        <div className="panel">
          <SectionHeader eyebrow="Manifest" title="Completeness Snapshot" />
          <DataTable
            columns={exportColumns}
            rows={exportRows}
            emptyState="Generate an export to view the manifest."
          />
        </div>
        <div className="panel">
          <AdvisoryPanel
            title="Chain of Custody"
            model="system"
            version="1.0"
            level="ADVISORY"
            message="Export includes hash + chain-of-custody metadata. PDF bundle generation is queued."
            reason="Legal hold + export manifest policies."
          />
          <div className="note-card">
            <p className="note-title">CSV Preview</p>
            <pre className="code-block">{csvPreview || 'CSV preview will appear here.'}</pre>
          </div>
        </div>
      </div>

      <div className="panel">
        <SectionHeader eyebrow="History" title="Recent Exports" />
        <DataTable
          columns={historyColumns}
          rows={historyRows}
          emptyState="No exports yet. Generate a full export to seed the history."
        />
      </div>
    </div>
  )
}
