import { useEffect, useState } from 'react'
import SectionHeader from '../components/SectionHeader.jsx'
import DataTable from '../components/DataTable.jsx'
import AdvisoryPanel from '../components/AdvisoryPanel.jsx'
import { apiFetch } from '../services/api.js'
import { fallbackDocumentExports } from '../data/fallback.js'

const exportColumns = [
  { key: 'id', label: 'Export' },
  { key: 'export_type', label: 'Type' },
  { key: 'status', label: 'Status' },
  { key: 'created_at', label: 'Created' },
]

export default function DocumentsExports() {
  const [exports, setExports] = useState(fallbackDocumentExports)

  useEffect(() => {
    const load = async () => {
      try {
        const data = await apiFetch('/api/documents/exports/history')
        if (Array.isArray(data) && data.length > 0) {
          setExports(data)
        }
      } catch (error) {
        // fallback remains
      }
    }
    load()
  }, [])

  return (
    <div className="page">
      <SectionHeader eyebrow="Quantum Documents" title="Discovery Export History" />
      <div className="panel">
        <AdvisoryPanel
          title="Export Integrity"
          model="vault-packager"
          version="1.1"
          level="ADVISORY"
          message="Exports include manifest hashes and audit trail summaries."
          reason="Discovery packaging"
        />
      </div>
      <div className="panel">
        <DataTable columns={exportColumns} rows={exports} emptyState="No exports yet." />
      </div>
    </div>
  )
}
